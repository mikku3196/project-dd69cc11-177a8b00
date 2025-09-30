"""
マスターボット - 統括管理・リスク管理・最適化
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notifications.discord import NotificationManager

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """リスクレベル"""
    SAFE = "safe"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

@dataclass
class BotPerformance:
    """ボットパフォーマンスデータ"""
    bot_name: str
    win_rate: float
    total_return: float
    max_drawdown: float
    consistency: float
    trade_count: int
    last_update: datetime

@dataclass
class RiskMetrics:
    """リスク指標"""
    current_drawdown: float
    daily_loss: float
    concurrent_trades: int
    circuit_breaker_failures: int
    last_reset: datetime

class MasterBot:
    """マスターボット - 統括管理・リスク管理・最適化"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_level = RiskLevel.SAFE
        
        # 初期資金配分
        self.allocation = {
            'stable': 0.4,      # 40% - 安定志向
            'balanced': 0.4,    # 40% - バランス重視
            'aggressive': 0.2   # 20% - 積極果敢
        }
        
        # リスク制御設定
        self.risk_control = self._get_risk_control_config()
        
        # 評価重み付け
        self.evaluation_weights = {
            'win_rate': 0.35,      # 勝率35%
            'return': 0.35,        # リターン35%
            'drawdown': 0.20,      # ドローダウン20%
            'consistency': 0.10    # 一貫性10%
        }
        
        # サブボット管理
        self.sub_bots = {}
        self.performance_data = {}
        self.risk_metrics = RiskMetrics(
            current_drawdown=0.0,
            daily_loss=0.0,
            concurrent_trades=0,
            circuit_breaker_failures=0,
            last_reset=datetime.now()
        )
        
        # 状態管理
        self.is_running = False
        self.last_rebalance = datetime.now()
        self.rebalance_interval = timedelta(days=30)  # 月次再配分
        
        # 通知システム
        webhook_url = config.get('discord_webhook_url', '')
        self.notification_manager = NotificationManager(webhook_url)
        
        logger.info("MasterBot initialized")
    
    def _get_risk_control_config(self) -> Dict[str, Any]:
        """リスク制御設定を取得"""
        risk_configs = {
            RiskLevel.SAFE: {
                'max_drawdown': 0.15,           # 15%
                'max_loss_per_trade': 0.02,     # 2%
                'max_concurrent_trades': 3,     # 3件
                'daily_loss_limit': 0.05,       # 5%
                'circuit_breaker_threshold': 5  # 5回
            },
            RiskLevel.BALANCED: {
                'max_drawdown': 0.20,           # 20%
                'max_loss_per_trade': 0.03,     # 3%
                'max_concurrent_trades': 5,     # 5件
                'daily_loss_limit': 0.08,       # 8%
                'circuit_breaker_threshold': 7  # 7回
            },
            RiskLevel.AGGRESSIVE: {
                'max_drawdown': 0.25,           # 25%
                'max_loss_per_trade': 0.05,     # 5%
                'max_concurrent_trades': 8,     # 8件
                'daily_loss_limit': 0.12,       # 12%
                'circuit_breaker_threshold': 10 # 10回
            }
        }
        return risk_configs[self.risk_level]
    
    async def start(self):
        """マスターボット開始"""
        logger.info("MasterBot starting...")
        self.is_running = True
        
        try:
            # 通知システム初期化
            await self.notification_manager.initialize()
            
            # サブボット初期化
            await self._initialize_sub_bots()
            
            # メインループ開始
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"MasterBot error: {e}")
            await self.notification_manager.notify_error("MasterBot Error", str(e))
            await self.stop()
    
    async def stop(self):
        """マスターボット停止"""
        logger.info("MasterBot stopping...")
        self.is_running = False
        
        # サブボット停止
        for bot_name, bot in self.sub_bots.items():
            try:
                await bot.stop()
            except Exception as e:
                logger.error(f"Error stopping {bot_name}: {e}")
        
        # 通知システム終了
        await self.notification_manager.shutdown()
    
    async def _initialize_sub_bots(self):
        """サブボット初期化"""
        logger.info("Initializing sub-bots...")
        
        # モックサブボット作成（実際の実装では src.bots.sub_bot からインポート）
        self.sub_bots = {
            'stable': MockSubBot('stable', {'max_position_size': 0.1, 'risk_tolerance': 0.01}),
            'balanced': MockSubBot('balanced', {'max_position_size': 0.2, 'risk_tolerance': 0.02}),
            'aggressive': MockSubBot('aggressive', {'max_position_size': 0.3, 'risk_tolerance': 0.03})
        }
        
        # サブボット開始
        for bot_name, bot in self.sub_bots.items():
            await bot.start()
            logger.info(f"Sub-bot {bot_name} started")
    
    async def _main_loop(self):
        """メインループ"""
        logger.info("MasterBot main loop started")
        
        while self.is_running:
            try:
                # リスク監視
                await self._monitor_risk()
                
                # パフォーマンス収集
                await self._collect_performance()
                
                # 資金再配分チェック
                await self._check_rebalance()
                
                # サブボット管理
                await self._manage_sub_bots()
                
                # 次のサイクルまで待機（5分間隔）
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
    
    async def _monitor_risk(self):
        """リスク監視"""
        try:
            # 現在のリスク指標を計算
            current_metrics = await self._calculate_risk_metrics()
            
            # リスク制限チェック
            if await self._check_risk_limits(current_metrics):
                await self._trigger_risk_control()
            
            # リスク指標更新
            self.risk_metrics = current_metrics
            
        except Exception as e:
            logger.error(f"Risk monitoring error: {e}")
    
    async def _calculate_risk_metrics(self) -> RiskMetrics:
        """リスク指標計算"""
        # モック実装（実際の実装では実際のデータを使用）
        return RiskMetrics(
            current_drawdown=0.05,  # 5%
            daily_loss=0.02,        # 2%
            concurrent_trades=2,    # 2件
            circuit_breaker_failures=1,  # 1回
            last_reset=datetime.now()
        )
    
    async def _check_risk_limits(self, metrics: RiskMetrics) -> bool:
        """リスク制限チェック"""
        risk_control = self.risk_control
        
        # ドローダウンチェック
        if metrics.current_drawdown > risk_control['max_drawdown']:
            logger.warning(f"Drawdown limit exceeded: {metrics.current_drawdown:.2%}")
            return True
        
        # 日次損失チェック
        if metrics.daily_loss > risk_control['daily_loss_limit']:
            logger.warning(f"Daily loss limit exceeded: {metrics.daily_loss:.2%}")
            return True
        
        # 同時取引チェック
        if metrics.concurrent_trades > risk_control['max_concurrent_trades']:
            logger.warning(f"Concurrent trades limit exceeded: {metrics.concurrent_trades}")
            return True
        
        # サーキットブレーカーチェック
        if metrics.circuit_breaker_failures > risk_control['circuit_breaker_threshold']:
            logger.warning(f"Circuit breaker threshold exceeded: {metrics.circuit_breaker_failures}")
            return True
        
        return False
    
    async def _trigger_risk_control(self):
        """リスク制御発動"""
        logger.warning("Risk control triggered!")
        
        # 全サブボット停止
        for bot_name, bot in self.sub_bots.items():
            await bot.emergency_stop()
        
        # Discord通知
        await self.notification_manager.notify_circuit_breaker(
            "Risk control triggered", 
            self.risk_metrics.circuit_breaker_failures
        )
    
    async def _collect_performance(self):
        """パフォーマンス収集"""
        try:
            for bot_name, bot in self.sub_bots.items():
                performance = await bot.get_performance()
                self.performance_data[bot_name] = BotPerformance(
                    bot_name=bot_name,
                    win_rate=performance.get('win_rate', 0.0),
                    total_return=performance.get('total_return', 0.0),
                    max_drawdown=performance.get('max_drawdown', 0.0),
                    consistency=performance.get('consistency', 0.0),
                    trade_count=performance.get('trade_count', 0),
                    last_update=datetime.now()
                )
        except Exception as e:
            logger.error(f"Performance collection error: {e}")
    
    async def _check_rebalance(self):
        """資金再配分チェック"""
        now = datetime.now()
        if now - self.last_rebalance >= self.rebalance_interval:
            await self._rebalance_allocation()
            self.last_rebalance = now
    
    async def _rebalance_allocation(self):
        """資金再配分実行"""
        logger.info("Starting allocation rebalance...")
        
        try:
            # 現在の配分を保存
            old_allocation = self.allocation.copy()
            
            # パフォーマンス評価
            scores = self._calculate_bot_scores()
            
            # 新しい配分計算
            new_allocation = self._calculate_new_allocation(scores)
            
            # 配分調整
            await self._adjust_allocation(new_allocation)
            
            logger.info(f"Allocation rebalanced: {new_allocation}")
            
            # Discord通知
            await self.notification_manager.notify_rebalance(old_allocation, new_allocation)
            
        except Exception as e:
            logger.error(f"Rebalance error: {e}")
            await self.notification_manager.notify_error("Rebalance Error", str(e))
    
    def _calculate_bot_scores(self) -> Dict[str, float]:
        """ボットスコア計算"""
        scores = {}
        weights = self.evaluation_weights
        
        for bot_name, performance in self.performance_data.items():
            score = (
                performance.win_rate * weights['win_rate'] +
                performance.total_return * weights['return'] +
                (1 - performance.max_drawdown) * weights['drawdown'] +
                performance.consistency * weights['consistency']
            )
            scores[bot_name] = score
        
        return scores
    
    def _calculate_new_allocation(self, scores: Dict[str, float]) -> Dict[str, float]:
        """新しい配分計算"""
        # スコア正規化
        total_score = sum(scores.values())
        if total_score == 0:
            return self.allocation.copy()
        
        normalized_scores = {k: v / total_score for k, v in scores.items()}
        
        # 配分調整（最大60%、最小10%の制限）
        new_allocation = {}
        for bot_name, score in normalized_scores.items():
            allocation = max(0.1, min(0.6, score))
            new_allocation[bot_name] = allocation
        
        # 合計を1.0に正規化
        total_allocation = sum(new_allocation.values())
        if total_allocation > 0:
            new_allocation = {k: v / total_allocation for k, v in new_allocation.items()}
        
        return new_allocation
    
    async def _adjust_allocation(self, new_allocation: Dict[str, float]):
        """配分調整実行"""
        for bot_name, new_ratio in new_allocation.items():
            if bot_name in self.sub_bots:
                bot = self.sub_bots[bot_name]
                await bot.set_allocation_ratio(new_ratio)
        
        self.allocation = new_allocation
    
    async def _manage_sub_bots(self):
        """サブボット管理"""
        for bot_name, bot in self.sub_bots.items():
            try:
                # ボット状態チェック
                status = await bot.get_status()
                
                # 異常な場合は再起動
                if status.get('status') == 'error':
                    logger.warning(f"Restarting {bot_name} due to error")
                    await bot.restart()
                
            except Exception as e:
                logger.error(f"Sub-bot management error for {bot_name}: {e}")
    
    async def _send_emergency_notification(self):
        """緊急通知送信（廃止予定）"""
        # Discord通知に統合済み
        logger.critical("EMERGENCY: Risk control triggered!")
    
    def get_status(self) -> Dict[str, Any]:
        """マスターボット状態取得"""
        return {
            'is_running': self.is_running,
            'risk_level': self.risk_level.value,
            'allocation': self.allocation,
            'risk_metrics': {
                'current_drawdown': self.risk_metrics.current_drawdown,
                'daily_loss': self.risk_metrics.daily_loss,
                'concurrent_trades': self.risk_metrics.concurrent_trades,
                'circuit_breaker_failures': self.risk_metrics.circuit_breaker_failures
            },
            'performance_data': {
                bot_name: {
                    'win_rate': perf.win_rate,
                    'total_return': perf.total_return,
                    'max_drawdown': perf.max_drawdown,
                    'trade_count': perf.trade_count
                }
                for bot_name, perf in self.performance_data.items()
            },
            'last_rebalance': self.last_rebalance.isoformat()
        }


class MockSubBot:
    """モックサブボット（テスト用）"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_running = False
        self.allocation_ratio = 0.33
        self.performance = {
            'win_rate': 0.6 + (hash(name) % 20) / 100,  # 60-80%
            'total_return': 0.05 + (hash(name) % 10) / 100,  # 5-15%
            'max_drawdown': 0.05 + (hash(name) % 5) / 100,   # 5-10%
            'consistency': 0.7 + (hash(name) % 20) / 100,   # 70-90%
            'trade_count': 10 + (hash(name) % 20)  # 10-30
        }
    
    async def start(self):
        self.is_running = True
        logger.info(f"MockSubBot {self.name} started")
    
    async def stop(self):
        self.is_running = False
        logger.info(f"MockSubBot {self.name} stopped")
    
    async def get_performance(self) -> Dict[str, Any]:
        return self.performance.copy()
    
    async def get_status(self) -> Dict[str, Any]:
        return {
            'status': 'running' if self.is_running else 'stopped',
            'allocation_ratio': self.allocation_ratio,
            'performance': self.performance
        }
    
    async def set_allocation_ratio(self, ratio: float):
        self.allocation_ratio = ratio
        logger.info(f"MockSubBot {self.name} allocation set to {ratio:.2%}")
    
    async def emergency_stop(self):
        self.is_running = False
        logger.warning(f"MockSubBot {self.name} emergency stopped")
    
    async def restart(self):
        await self.stop()
        await asyncio.sleep(1)
        await self.start()


# テスト用のメイン関数
async def main():
    """テスト用メイン関数"""
    config = {
        'risk_level': 'safe',
        'rebalance_interval_days': 30
    }
    
    master_bot = MasterBot(config)
    
    try:
        # マスターボット開始
        await master_bot.start()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        await master_bot.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
