"""
利益確保機能（プロフィット・セービング）モジュール
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class ProfitSaveStatus(Enum):
    """利益確保ステータス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProfitSaveConfig:
    """利益確保設定"""
    enabled: bool
    save_interval: str  # 'daily', 'weekly', 'monthly'
    save_day: str  # 'Monday', 'Tuesday', etc.
    save_hour: int  # 0-23
    save_rate: float  # 0.0-1.0 (確保率)
    min_profit_threshold: float  # 最小利益閾値
    max_save_amount: float  # 最大確保額

@dataclass
class SubBotPerformance:
    """サブボットパフォーマンス"""
    bot_name: str
    current_balance: float
    initial_balance: float
    total_pnl: float
    profit_rate: float
    win_rate: float
    max_drawdown: float
    last_update: datetime

@dataclass
class ProfitSaveResult:
    """利益確保結果"""
    bot_name: str
    profit_amount: float
    save_amount: float
    save_rate: float
    status: ProfitSaveStatus
    executed_at: datetime
    error_message: Optional[str]

class ProfitSaveManager:
    """利益確保管理クラス"""
    
    def __init__(self, config: ProfitSaveConfig):
        self.config = config
        self.last_save_time: Optional[datetime] = None
        self.save_history: List[ProfitSaveResult] = []
        
    def should_execute_save(self) -> bool:
        """利益確保実行判定"""
        if not self.config.enabled:
            return False
        
        now = datetime.now()
        
        # 初回実行
        if self.last_save_time is None:
            return True
        
        # 間隔チェック
        if self.config.save_interval == 'daily':
            return (now - self.last_save_time).days >= 1
        elif self.config.save_interval == 'weekly':
            return (now - self.last_save_time).days >= 7
        elif self.config.save_interval == 'monthly':
            return (now - self.last_save_time).days >= 30
        
        return False
    
    def is_save_time(self) -> bool:
        """保存時間判定"""
        now = datetime.now()
        
        # 曜日チェック
        if self.config.save_interval == 'weekly':
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            if weekdays[now.weekday()] != self.config.save_day:
                return False
        
        # 時間チェック
        if now.hour != self.config.save_hour:
            return False
        
        return True
    
    def calculate_save_amount(self, performance: SubBotPerformance) -> float:
        """確保額計算"""
        if performance.total_pnl <= 0:
            return 0.0
        
        # 最小利益閾値チェック
        if performance.total_pnl < self.config.min_profit_threshold:
            return 0.0
        
        # 確保額計算
        save_amount = performance.total_pnl * self.config.save_rate
        
        # 最大確保額制限
        save_amount = min(save_amount, self.config.max_save_amount)
        
        return save_amount
    
    async def execute_profit_save(
        self,
        performances: List[SubBotPerformance],
        transfer_executor  # 資金移動実行関数
    ) -> List[ProfitSaveResult]:
        """利益確保実行"""
        
        if not self.should_execute_save():
            logger.info("Profit save not due yet")
            return []
        
        if not self.is_save_time():
            logger.info("Not save time yet")
            return []
        
        results = []
        
        for performance in performances:
            try:
                # 確保額計算
                save_amount = self.calculate_save_amount(performance)
                
                if save_amount <= 0:
                    logger.info(f"No profit to save for {performance.bot_name}")
                    continue
                
                # 利益確保実行
                result = await self._execute_single_save(
                    performance, save_amount, transfer_executor
                )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to save profit for {performance.bot_name}: {e}")
                
                result = ProfitSaveResult(
                    bot_name=performance.bot_name,
                    profit_amount=performance.total_pnl,
                    save_amount=0.0,
                    save_rate=0.0,
                    status=ProfitSaveStatus.FAILED,
                    executed_at=datetime.now(),
                    error_message=str(e)
                )
                results.append(result)
        
        # 最終保存時間更新
        self.last_save_time = datetime.now()
        
        # 履歴に追加
        self.save_history.extend(results)
        
        logger.info(f"Profit save completed: {len(results)} bots processed")
        
        return results
    
    async def _execute_single_save(
        self,
        performance: SubBotPerformance,
        save_amount: float,
        transfer_executor
    ) -> ProfitSaveResult:
        """単一ボットの利益確保実行"""
        
        logger.info(f"Executing profit save for {performance.bot_name}: ${save_amount:.2f}")
        
        try:
            # 資金移動実行（実際の実装では取引所APIを使用）
            success = await transfer_executor(
                from_account=performance.bot_name,
                to_account='profit_save_account',
                amount=save_amount
            )
            
            if success:
                status = ProfitSaveStatus.COMPLETED
                error_message = None
                logger.info(f"Profit save successful for {performance.bot_name}")
            else:
                status = ProfitSaveStatus.FAILED
                error_message = "Transfer execution failed"
                logger.error(f"Profit save failed for {performance.bot_name}")
            
        except Exception as e:
            status = ProfitSaveStatus.FAILED
            error_message = str(e)
            logger.error(f"Profit save error for {performance.bot_name}: {e}")
        
        result = ProfitSaveResult(
            bot_name=performance.bot_name,
            profit_amount=performance.total_pnl,
            save_amount=save_amount if status == ProfitSaveStatus.COMPLETED else 0.0,
            save_rate=self.config.save_rate,
            status=status,
            executed_at=datetime.now(),
            error_message=error_message
        )
        
        return result
    
    def get_save_summary(self) -> Dict[str, Any]:
        """利益確保サマリー取得"""
        if not self.save_history:
            return {"message": "No save history available"}
        
        # 統計計算
        total_saves = len(self.save_history)
        successful_saves = len([r for r in self.save_history if r.status == ProfitSaveStatus.COMPLETED])
        total_saved_amount = sum(r.save_amount for r in self.save_history if r.status == ProfitSaveStatus.COMPLETED)
        
        # 最近の保存
        recent_saves = sorted(self.save_history, key=lambda x: x.executed_at, reverse=True)[:5]
        
        return {
            'config': {
                'enabled': self.config.enabled,
                'save_interval': self.config.save_interval,
                'save_day': self.config.save_day,
                'save_hour': self.config.save_hour,
                'save_rate': self.config.save_rate,
                'min_profit_threshold': self.config.min_profit_threshold,
                'max_save_amount': self.config.max_save_amount
            },
            'statistics': {
                'total_saves': total_saves,
                'successful_saves': successful_saves,
                'success_rate': successful_saves / total_saves if total_saves > 0 else 0.0,
                'total_saved_amount': total_saved_amount,
                'last_save_time': self.last_save_time.isoformat() if self.last_save_time else None
            },
            'recent_saves': [
                {
                    'bot_name': r.bot_name,
                    'save_amount': r.save_amount,
                    'status': r.status.value,
                    'executed_at': r.executed_at.isoformat(),
                    'error_message': r.error_message
                }
                for r in recent_saves
            ]
        }
    
    def get_next_save_time(self) -> Optional[datetime]:
        """次回保存予定時間取得"""
        if not self.config.enabled:
            return None
        
        now = datetime.now()
        
        if self.config.save_interval == 'daily':
            next_save = now.replace(hour=self.config.save_hour, minute=0, second=0, microsecond=0)
            if next_save <= now:
                next_save += timedelta(days=1)
        elif self.config.save_interval == 'weekly':
            weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            target_weekday = weekdays.index(self.config.save_day)
            
            days_ahead = target_weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_save = now + timedelta(days=days_ahead)
            next_save = next_save.replace(hour=self.config.save_hour, minute=0, second=0, microsecond=0)
        elif self.config.save_interval == 'monthly':
            # 月次は毎月1日
            next_save = now.replace(day=1, hour=self.config.save_hour, minute=0, second=0, microsecond=0)
            if next_save <= now:
                if now.month == 12:
                    next_save = next_save.replace(year=now.year + 1, month=1)
                else:
                    next_save = next_save.replace(month=now.month + 1)
        else:
            return None
        
        return next_save

# テスト用のメイン関数
async def test_profit_save_manager():
    """利益確保管理テスト"""
    print("Profit Save Manager Test")
    print("=" * 50)
    
    # 設定
    config = ProfitSaveConfig(
        enabled=True,
        save_interval='weekly',
        save_day='Sunday',
        save_hour=0,  # 日曜日 00:00
        save_rate=0.5,  # 利益の50%を確保
        min_profit_threshold=100.0,  # 最小$100の利益
        max_save_amount=10000.0  # 最大$10,000まで
    )
    
    # 利益確保管理クラス初期化
    manager = ProfitSaveManager(config)
    
    # モック資金移動実行関数
    async def mock_transfer_executor(from_account: str, to_account: str, amount: float) -> bool:
        """モック資金移動実行関数"""
        print(f"  Transfer: ${amount:.2f} from {from_account} to {to_account}")
        # シミュレーション：90%の確率で成功
        import random
        return random.random() < 0.9
    
    # モックサブボットパフォーマンス
    performances = [
        SubBotPerformance(
            bot_name='SubBot-A',
            current_balance=15000.0,
            initial_balance=10000.0,
            total_pnl=5000.0,
            profit_rate=0.5,
            win_rate=0.65,
            max_drawdown=0.15,
            last_update=datetime.now()
        ),
        SubBotPerformance(
            bot_name='SubBot-B',
            current_balance=12000.0,
            initial_balance=10000.0,
            total_pnl=2000.0,
            profit_rate=0.2,
            win_rate=0.55,
            max_drawdown=0.08,
            last_update=datetime.now()
        ),
        SubBotPerformance(
            bot_name='SubBot-C',
            current_balance=8000.0,
            initial_balance=10000.0,
            total_pnl=-2000.0,
            profit_rate=-0.2,
            win_rate=0.45,
            max_drawdown=0.25,
            last_update=datetime.now()
        )
    ]
    
    # 利益確保実行
    print("Executing profit save...")
    results = await manager.execute_profit_save(performances, mock_transfer_executor)
    
    print(f"\nProfit Save Results:")
    for result in results:
        print(f"  {result.bot_name}:")
        print(f"    Profit Amount: ${result.profit_amount:.2f}")
        print(f"    Save Amount: ${result.save_amount:.2f}")
        print(f"    Status: {result.status.value}")
        if result.error_message:
            print(f"    Error: {result.error_message}")
    
    # サマリー表示
    summary = manager.get_save_summary()
    print(f"\nSave Summary:")
    print(f"  Total Saves: {summary['statistics']['total_saves']}")
    print(f"  Successful Saves: {summary['statistics']['successful_saves']}")
    print(f"  Success Rate: {summary['statistics']['success_rate']:.2%}")
    print(f"  Total Saved Amount: ${summary['statistics']['total_saved_amount']:.2f}")
    
    # 次回保存時間
    next_save_time = manager.get_next_save_time()
    if next_save_time:
        print(f"  Next Save Time: {next_save_time}")
    
    print("\nProfit Save Manager Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_profit_save_manager())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
