"""
動的パラメータ自動チューニングモジュール
"""
import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import itertools

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class OptimizationMetric(Enum):
    """最適化指標"""
    PROFIT = "profit"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"

@dataclass
class ParameterRange:
    """パラメータ範囲"""
    start: float
    end: float
    step: float
    param_type: str = "float"  # "float", "int", "bool"

@dataclass
class OptimizationConfig:
    """最適化設定"""
    enabled: bool
    schedule: str  # cron形式
    backtest_period_months: int
    target_metric: OptimizationMetric
    param_ranges: Dict[str, ParameterRange]
    max_iterations: int = 1000
    parallel_workers: int = 4
    min_improvement_threshold: float = 0.05  # 5%以上の改善が必要

@dataclass
class OptimizationResult:
    """最適化結果"""
    best_params: Dict[str, Any]
    best_score: float
    improvement: float
    total_iterations: int
    execution_time: float
    backtest_results: Dict[str, Any]
    optimization_date: datetime

@dataclass
class ParameterSet:
    """パラメータセット"""
    params: Dict[str, Any]
    score: float = 0.0
    backtest_result: Optional[Dict[str, Any]] = None

class DynamicParameterOptimizer:
    """動的パラメータ最適化クラス"""
    
    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.optimization_history: List[OptimizationResult] = []
        self.current_params: Dict[str, Any] = {}
        
    def generate_parameter_combinations(self) -> List[Dict[str, Any]]:
        """パラメータ組み合わせ生成"""
        param_names = list(self.config.param_ranges.keys())
        param_ranges = list(self.config.param_ranges.values())
        
        # 各パラメータの値を生成
        param_values = []
        for param_range in param_ranges:
            if param_range.param_type == "int":
                values = list(range(int(param_range.start), int(param_range.end) + 1, int(param_range.step)))
            elif param_range.param_type == "bool":
                values = [True, False]
            else:  # float
                values = np.arange(param_range.start, param_range.end + param_range.step, param_range.step)
            
            param_values.append(values)
        
        # 全組み合わせ生成
        combinations = list(itertools.product(*param_values))
        
        # 辞書形式に変換
        param_combinations = []
        for combo in combinations:
            param_dict = {}
            for i, param_name in enumerate(param_names):
                param_dict[param_name] = combo[i]
            param_combinations.append(param_dict)
        
        # 最大反復回数で制限
        if len(param_combinations) > self.config.max_iterations:
            # ランダムサンプリング
            import random
            param_combinations = random.sample(param_combinations, self.config.max_iterations)
        
        logger.info(f"Generated {len(param_combinations)} parameter combinations")
        return param_combinations
    
    async def run_backtest_for_params(
        self, 
        params: Dict[str, Any], 
        backtest_executor  # バックテスト実行関数
    ) -> Dict[str, Any]:
        """パラメータセットでのバックテスト実行"""
        try:
            # 実際の実装では、バックテストエンジンを呼び出し
            result = await backtest_executor(params)
            return result
        except Exception as e:
            logger.error(f"Backtest failed for params {params}: {e}")
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 1.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'error': str(e)
            }
    
    def calculate_score(self, backtest_result: Dict[str, Any]) -> float:
        """スコア計算"""
        metric = self.config.target_metric
        
        if metric == OptimizationMetric.PROFIT:
            return backtest_result.get('total_return', 0.0)
        elif metric == OptimizationMetric.SHARPE_RATIO:
            return backtest_result.get('sharpe_ratio', 0.0)
        elif metric == OptimizationMetric.MAX_DRAWDOWN:
            # ドローダウンは小さい方が良いので負の値を返す
            return -backtest_result.get('max_drawdown', 1.0)
        elif metric == OptimizationMetric.WIN_RATE:
            return backtest_result.get('win_rate', 0.0)
        elif metric == OptimizationMetric.PROFIT_FACTOR:
            return backtest_result.get('profit_factor', 0.0)
        else:
            return 0.0
    
    async def optimize_parameters(
        self, 
        current_params: Dict[str, Any],
        backtest_executor
    ) -> OptimizationResult:
        """パラメータ最適化実行"""
        
        logger.info("Starting parameter optimization...")
        start_time = datetime.now()
        
        # パラメータ組み合わせ生成
        param_combinations = self.generate_parameter_combinations()
        
        # 現在のパラメータでのバックテスト
        current_backtest = await self.run_backtest_for_params(current_params, backtest_executor)
        current_score = self.calculate_score(current_backtest)
        
        logger.info(f"Current parameters score: {current_score:.4f}")
        
        # 最適化実行
        best_params = current_params.copy()
        best_score = current_score
        best_backtest = current_backtest
        
        # 並列実行でバックテスト
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            # 非同期タスク作成
            tasks = []
            for params in param_combinations:
                task = asyncio.create_task(
                    self.run_backtest_for_params(params, backtest_executor)
                )
                tasks.append((params, task))
            
            # 結果収集
            for params, task in tasks:
                try:
                    backtest_result = await task
                    score = self.calculate_score(backtest_result)
                    
                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
                        best_backtest = backtest_result
                        logger.info(f"New best score: {best_score:.4f} with params: {params}")
                    
                except Exception as e:
                    logger.error(f"Failed to process params {params}: {e}")
        
        # 改善度計算
        improvement = (best_score - current_score) / abs(current_score) if current_score != 0 else 0.0
        
        # 実行時間
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 結果作成
        result = OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            improvement=improvement,
            total_iterations=len(param_combinations),
            execution_time=execution_time,
            backtest_results=best_backtest,
            optimization_date=datetime.now()
        )
        
        logger.info(f"Optimization completed: {len(param_combinations)} iterations, "
                   f"best score: {best_score:.4f}, improvement: {improvement:.2%}")
        
        return result
    
    def should_update_parameters(self, result: OptimizationResult) -> bool:
        """パラメータ更新判定"""
        if not self.config.enabled:
            return False
        
        # 改善閾値チェック
        if result.improvement < self.config.min_improvement_threshold:
            logger.info(f"Improvement {result.improvement:.2%} below threshold "
                       f"{self.config.min_improvement_threshold:.2%}")
            return False
        
        return True
    
    async def update_parameters(self, result: OptimizationResult) -> bool:
        """パラメータ更新実行"""
        try:
            # 設定ファイル更新（実際の実装では設定ファイルを書き換え）
            logger.info(f"Updating parameters: {result.best_params}")
            
            # 現在のパラメータを更新
            self.current_params.update(result.best_params)
            
            # 履歴に追加
            self.optimization_history.append(result)
            
            logger.info("Parameters updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update parameters: {e}")
            return False
    
    async def run_optimization_cycle(
        self, 
        current_params: Dict[str, Any],
        backtest_executor,
        notification_sender=None
    ) -> bool:
        """最適化サイクル実行"""
        
        try:
            # 最適化実行
            result = await self.optimize_parameters(current_params, backtest_executor)
            
            # 更新判定
            if self.should_update_parameters(result):
                # パラメータ更新
                success = await self.update_parameters(result)
                
                if success:
                    # 通知送信
                    if notification_sender:
                        await self._send_optimization_notification(result, notification_sender)
                    
                    return True
                else:
                    logger.error("Parameter update failed")
                    return False
            else:
                logger.info("No parameter update needed")
                return False
                
        except Exception as e:
            logger.error(f"Optimization cycle failed: {e}")
            return False
    
    async def _send_optimization_notification(self, result: OptimizationResult, notification_sender):
        """最適化結果通知"""
        try:
            message = {
                'optimization_completed': {
                    'best_score': result.best_score,
                    'improvement': result.improvement,
                    'total_iterations': result.total_iterations,
                    'execution_time': result.execution_time,
                    'best_params': result.best_params,
                    'optimization_date': result.optimization_date.isoformat()
                }
            }
            
            await notification_sender(message)
            
        except Exception as e:
            logger.error(f"Failed to send optimization notification: {e}")
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """最適化サマリー取得"""
        if not self.optimization_history:
            return {"message": "No optimization history available"}
        
        # 統計計算
        total_optimizations = len(self.optimization_history)
        successful_updates = len([r for r in self.optimization_history if r.improvement > 0])
        
        # 最新の最適化結果
        latest_result = self.optimization_history[-1]
        
        # 改善履歴
        improvements = [r.improvement for r in self.optimization_history]
        
        return {
            'config': {
                'enabled': self.config.enabled,
                'target_metric': self.config.target_metric.value,
                'backtest_period_months': self.config.backtest_period_months,
                'max_iterations': self.config.max_iterations,
                'min_improvement_threshold': self.config.min_improvement_threshold
            },
            'statistics': {
                'total_optimizations': total_optimizations,
                'successful_updates': successful_updates,
                'success_rate': successful_updates / total_optimizations if total_optimizations > 0 else 0.0,
                'average_improvement': np.mean(improvements) if improvements else 0.0,
                'max_improvement': max(improvements) if improvements else 0.0,
                'last_optimization_date': latest_result.optimization_date.isoformat()
            },
            'current_params': self.current_params,
            'latest_result': {
                'best_score': latest_result.best_score,
                'improvement': latest_result.improvement,
                'total_iterations': latest_result.total_iterations,
                'execution_time': latest_result.execution_time
            }
        }
    
    def get_next_optimization_time(self) -> Optional[datetime]:
        """次回最適化予定時間取得"""
        if not self.config.enabled:
            return None
        
        # 簡易的なcron解析（実際の実装ではcroniterを使用）
        # "0 1 1 * *" = 毎月1日 AM1:00
        now = datetime.now()
        
        if self.config.schedule == "0 1 1 * *":  # 毎月1日
            next_month = now.replace(day=1, hour=1, minute=0, second=0, microsecond=0)
            if next_month <= now:
                if now.month == 12:
                    next_month = next_month.replace(year=now.year + 1, month=1)
                else:
                    next_month = next_month.replace(month=now.month + 1)
            return next_month
        
        return None

# テスト用のメイン関数
async def test_dynamic_parameter_optimizer():
    """動的パラメータ最適化テスト"""
    print("Dynamic Parameter Optimizer Test")
    print("=" * 50)
    
    # 設定
    config = OptimizationConfig(
        enabled=True,
        schedule="0 1 1 * *",  # 毎月1日 AM1:00
        backtest_period_months=6,
        target_metric=OptimizationMetric.SHARPE_RATIO,
        param_ranges={
            'sl_ratio': ParameterRange(start=0.5, end=2.0, step=0.1),
            'tp_ratio': ParameterRange(start=1.0, end=3.0, step=0.2),
            'atr_period': ParameterRange(start=10, end=30, step=2, param_type='int'),
            'volatility_threshold': ParameterRange(start=100.0, end=500.0, step=50.0)
        },
        max_iterations=50,  # テスト用に制限
        parallel_workers=2,
        min_improvement_threshold=0.05
    )
    
    # 動的パラメータ最適化クラス初期化
    optimizer = DynamicParameterOptimizer(config)
    
    # 現在のパラメータ
    current_params = {
        'sl_ratio': 1.0,
        'tp_ratio': 1.5,
        'atr_period': 14,
        'volatility_threshold': 300.0
    }
    
    # モックバックテスト実行関数
    async def mock_backtest_executor(params: Dict[str, Any]) -> Dict[str, Any]:
        """モックバックテスト実行関数"""
        # シミュレーション：パラメータに基づいてランダムな結果生成
        import random
        
        # パラメータの影響をシミュレーション
        sl_ratio = params.get('sl_ratio', 1.0)
        tp_ratio = params.get('tp_ratio', 1.5)
        atr_period = params.get('atr_period', 14)
        volatility_threshold = params.get('volatility_threshold', 300.0)
        
        # パラメータの組み合わせによるスコア計算
        base_score = 0.5
        sl_factor = 1.0 - abs(sl_ratio - 1.0) * 0.1  # 1.0に近いほど良い
        tp_factor = 1.0 + (tp_ratio - 1.0) * 0.05  # 高いほど良い
        atr_factor = 1.0 - abs(atr_period - 20) * 0.01  # 20に近いほど良い
        vol_factor = 1.0 - abs(volatility_threshold - 300) * 0.0001  # 300に近いほど良い
        
        score = base_score * sl_factor * tp_factor * atr_factor * vol_factor
        
        # ランダム要素追加
        score += random.uniform(-0.1, 0.1)
        
        return {
            'total_return': score * 100,
            'sharpe_ratio': score,
            'max_drawdown': max(0.1, 1.0 - score),
            'win_rate': min(0.9, score + 0.3),
            'profit_factor': max(0.5, score + 0.5),
            'total_trades': random.randint(50, 200)
        }
    
    # モック通知送信関数
    async def mock_notification_sender(message):
        """モック通知送信関数"""
        print(f"  Notification: {message}")
    
    # 最適化サイクル実行
    print("Running optimization cycle...")
    success = await optimizer.run_optimization_cycle(
        current_params, 
        mock_backtest_executor,
        mock_notification_sender
    )
    
    print(f"\nOptimization Result:")
    print(f"  Success: {success}")
    
    # サマリー表示
    summary = optimizer.get_optimization_summary()
    print(f"\nOptimization Summary:")
    print(f"  Total Optimizations: {summary['statistics']['total_optimizations']}")
    print(f"  Successful Updates: {summary['statistics']['successful_updates']}")
    print(f"  Success Rate: {summary['statistics']['success_rate']:.2%}")
    print(f"  Average Improvement: {summary['statistics']['average_improvement']:.2%}")
    print(f"  Max Improvement: {summary['statistics']['max_improvement']:.2%}")
    
    if 'latest_result' in summary:
        latest = summary['latest_result']
        print(f"  Latest Best Score: {latest['best_score']:.4f}")
        print(f"  Latest Improvement: {latest['improvement']:.2%}")
        print(f"  Latest Iterations: {latest['total_iterations']}")
        print(f"  Latest Execution Time: {latest['execution_time']:.1f}s")
    
    # 次回最適化時間
    next_time = optimizer.get_next_optimization_time()
    if next_time:
        print(f"  Next Optimization: {next_time}")
    
    print("\nDynamic Parameter Optimizer Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_dynamic_parameter_optimizer())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
