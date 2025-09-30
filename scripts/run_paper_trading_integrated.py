"""
ペーパー取引統合スクリプト - 1ヶ月間の継続動作検証
"""
import asyncio
import json
import logging
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.paper_trading.engine import PaperTradingEngine, OrderSide, OrderType
from src.bots.master_bot import MasterBot
from src.notifications.discord import NotificationManager

logger = logging.getLogger(__name__)

class PaperTradingManager:
    """ペーパー取引管理クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.paper_engine = PaperTradingEngine(
            initial_balance=config.get('initial_balance', 10000.0),
            commission_rate=config.get('commission_rate', 0.001)
        )
        self.master_bot = None
        self.notification_manager = None
        self.is_running = False
        self.start_time = None
        self.end_time = None
        
        # ログ設定
        self.log_dir = Path("logs/paper_trading")
        self.log_dir.mkdir(exist_ok=True)
        
        # 設定ログ
        self._log_config()
    
    def _log_config(self):
        """設定ログ出力"""
        config_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'config',
            'config': self.config
        }
        
        config_file = self.log_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_log, f, indent=2, ensure_ascii=False)
    
    async def initialize(self):
        """初期化"""
        print("[INFO] ペーパー取引システム初期化中...")
        
        # マスターボット初期化
        self.master_bot = MasterBot(self.config)
        await self.master_bot._initialize_sub_bots()
        
        # 通知システム初期化
        webhook_url = self.config.get('discord_webhook_url', '')
        self.notification_manager = NotificationManager(webhook_url)
        await self.notification_manager.initialize()
        
        # ペーパー取引エンジン開始
        self.paper_engine.start()
        
        print("[SUCCESS] ペーパー取引システム初期化完了")
    
    async def run_paper_trading(self, duration_days: int = 30):
        """ペーパー取引実行"""
        print(f"[INFO] ペーパー取引開始: {duration_days}日間")
        
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(days=duration_days)
        self.is_running = True
        
        # 開始通知
        await self.notification_manager.notify_performance({
            'paper_trading': {
                'status': 'started',
                'duration_days': duration_days,
                'initial_balance': self.paper_engine.initial_balance
            }
        })
        
        try:
            # メインループ
            while self.is_running and datetime.now() < self.end_time:
                await self._trading_cycle()
                await asyncio.sleep(60)  # 1分間隔
                
        except KeyboardInterrupt:
            print("[INFO] ユーザーによる中断")
        except Exception as e:
            print(f"[ERROR] ペーパー取引エラー: {e}")
            await self.notification_manager.notify_error("Paper Trading Error", str(e))
        finally:
            await self._cleanup()
    
    async def _trading_cycle(self):
        """取引サイクル"""
        try:
            # マスターボットの取引指示取得
            trading_signals = await self._get_trading_signals()
            
            # ペーパー取引実行
            for signal in trading_signals:
                await self._execute_paper_trade(signal)
            
            # アカウント状態更新
            self._update_account_status()
            
            # 定期的な通知（1時間ごと）
            if datetime.now().minute == 0:
                await self._send_hourly_report()
            
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
    
    async def _get_trading_signals(self) -> List[Dict[str, Any]]:
        """取引シグナル取得（モック実装）"""
        # 実際の実装では、マスターボットからシグナルを取得
        # ここではモックシグナルを生成
        
        signals = []
        
        # ランダムな取引シグナル生成（テスト用）
        import random
        
        if random.random() < 0.1:  # 10%の確率で取引
            signal = {
                'symbol': random.choice(['BTCUSDT', 'ETHUSDT', 'ADAUSDT']),
                'side': random.choice(['buy', 'sell']),
                'quantity': random.uniform(0.01, 0.1),
                'order_type': 'market',
                'confidence': random.uniform(0.6, 0.9)
            }
            signals.append(signal)
        
        return signals
    
    async def _execute_paper_trade(self, signal: Dict[str, Any]):
        """ペーパー取引実行"""
        try:
            side = OrderSide.BUY if signal['side'] == 'buy' else OrderSide.SELL
            order_type = OrderType.MARKET if signal['order_type'] == 'market' else OrderType.LIMIT
            
            order = self.paper_engine.place_order(
                symbol=signal['symbol'],
                side=side,
                order_type=order_type,
                quantity=signal['quantity']
            )
            
            # 取引ログ
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'signal': signal,
                'order_id': order.id,
                'status': order.status.value,
                'filled_price': order.filled_price
            }
            
            self._log_trade(trade_log)
            
        except Exception as e:
            logger.error(f"Paper trade execution error: {e}")
    
    def _update_account_status(self):
        """アカウント状態更新"""
        summary = self.paper_engine.get_account_summary()
        
        # 状態ログ
        status_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'status',
            'summary': summary
        }
        
        self._log_status(status_log)
    
    async def _send_hourly_report(self):
        """時間レポート送信"""
        summary = self.paper_engine.get_account_summary()
        
        # パフォーマンス通知
        performance_data = {
            'paper_trading': {
                'balance': summary['balance'],
                'equity': summary['equity'],
                'total_trades': summary['total_trades'],
                'win_rate': summary['win_rate'],
                'total_pnl': summary['total_pnl'],
                'return_pct': summary['return_pct'],
                'max_drawdown': summary['max_drawdown']
            }
        }
        
        await self.notification_manager.notify_performance(performance_data)
    
    def _log_trade(self, trade_log: Dict[str, Any]):
        """取引ログ出力"""
        trade_file = self.log_dir / "trades.jsonl"
        with open(trade_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trade_log, ensure_ascii=False) + '\n')
    
    def _log_status(self, status_log: Dict[str, Any]):
        """状態ログ出力"""
        status_file = self.log_dir / "status.jsonl"
        with open(status_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(status_log, ensure_ascii=False) + '\n')
    
    async def _cleanup(self):
        """クリーンアップ"""
        print("[INFO] ペーパー取引システム終了中...")
        
        self.is_running = False
        
        # 最終レポート生成
        await self._generate_final_report()
        
        # システム停止
        if self.master_bot:
            await self.master_bot.stop()
        
        if self.notification_manager:
            await self.notification_manager.shutdown()
        
        self.paper_engine.stop()
        
        print("[SUCCESS] ペーパー取引システム終了完了")
    
    async def _generate_final_report(self):
        """最終レポート生成"""
        summary = self.paper_engine.get_account_summary()
        
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'type': 'final_report',
            'duration': {
                'start': self.start_time.isoformat() if self.start_time else None,
                'end': datetime.now().isoformat(),
                'days': (datetime.now() - self.start_time).days if self.start_time else 0
            },
            'performance': summary,
            'trades': self.paper_engine.get_trade_history()
        }
        
        # レポートファイル出力
        report_file = self.log_dir / "final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        # 通知送信
        await self.notification_manager.notify_performance({
            'paper_trading_final': {
                'duration_days': final_report['duration']['days'],
                'final_balance': summary['balance'],
                'total_return': summary['return_pct'],
                'total_trades': summary['total_trades'],
                'win_rate': summary['win_rate'],
                'max_drawdown': summary['max_drawdown']
            }
        })
        
        print(f"[SUCCESS] 最終レポート生成完了: {report_file}")

async def main():
    """メイン関数"""
    print("ペーパー取引統合システム")
    print("=" * 50)
    
    # 設定
    config = {
        'initial_balance': 10000.0,
        'commission_rate': 0.001,
        'risk_level': 'safe',
        'rebalance_interval_days': 30,
        'discord_webhook_url': ''  # テスト用は空文字
    }
    
    # ペーパー取引管理クラス初期化
    manager = PaperTradingManager(config)
    
    try:
        # 初期化
        await manager.initialize()
        
        # ペーパー取引実行（1日間のテスト）
        await manager.run_paper_trading(duration_days=1)
        
    except Exception as e:
        print(f"[ERROR] ペーパー取引システムエラー: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n[SUCCESS] ペーパー取引システムが正常に完了しました！")
        else:
            print("\n[ERROR] ペーパー取引システムに問題がありました。")
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
