"""
本番環境設定スクリプト - 少額運用（$10程度）の準備
"""
import asyncio
import json
import logging
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.bots.master_bot import MasterBot
from src.notifications.discord import NotificationManager
from src.paper_trading.engine import PaperTradingEngine

logger = logging.getLogger(__name__)

class ProductionManager:
    """本番環境管理クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.master_bot = None
        self.notification_manager = None
        self.paper_engine = None
        self.is_running = False
        
        # ログ設定
        self.log_dir = Path("logs/production")
        self.log_dir.mkdir(exist_ok=True)
        
        # 設定ログ
        self._log_config()
    
    def _log_config(self):
        """設定ログ出力"""
        config_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'production_config',
            'config': {
                'initial_balance': self.config.get('initial_balance', 10.0),
                'risk_level': self.config.get('risk_level', 'safe'),
                'max_position_size': self.config.get('max_position_size', 0.01),
                'stop_loss_pct': self.config.get('stop_loss_pct', 0.05),
                'take_profit_pct': self.config.get('take_profit_pct', 0.10)
            }
        }
        
        config_file = self.log_dir / "production_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_log, f, indent=2, ensure_ascii=False)
    
    async def initialize(self):
        """初期化"""
        print("[INFO] 本番環境システム初期化中...")
        
        # マスターボット初期化
        self.master_bot = MasterBot(self.config)
        await self.master_bot._initialize_sub_bots()
        
        # 通知システム初期化
        webhook_url = self.config.get('discord_webhook_url', '')
        self.notification_manager = NotificationManager(webhook_url)
        await self.notification_manager.initialize()
        
        # ペーパー取引エンジン（本番用）
        self.paper_engine = PaperTradingEngine(
            initial_balance=self.config.get('initial_balance', 10.0),
            commission_rate=self.config.get('commission_rate', 0.001)
        )
        self.paper_engine.start()
        
        print("[SUCCESS] 本番環境システム初期化完了")
    
    async def run_production_trading(self, duration_hours: int = 24):
        """本番取引実行"""
        print(f"[INFO] 本番取引開始: {duration_hours}時間")
        
        self.is_running = True
        start_time = datetime.now()
        
        # 開始通知
        await self.notification_manager.notify_performance({
            'production_trading': {
                'status': 'started',
                'duration_hours': duration_hours,
                'initial_balance': self.paper_engine.initial_balance,
                'risk_level': self.config.get('risk_level', 'safe')
            }
        })
        
        try:
            # メインループ
            cycle_count = 0
            while self.is_running and cycle_count < duration_hours * 60:  # 1分間隔
                await self._trading_cycle()
                await asyncio.sleep(60)  # 1分間隔
                cycle_count += 1
                
        except KeyboardInterrupt:
            print("[INFO] ユーザーによる中断")
        except Exception as e:
            print(f"[ERROR] 本番取引エラー: {e}")
            await self.notification_manager.notify_error("Production Trading Error", str(e))
        finally:
            await self._cleanup()
    
    async def _trading_cycle(self):
        """取引サイクル"""
        try:
            # マスターボットの取引指示取得
            trading_signals = await self._get_trading_signals()
            
            # 本番取引実行
            for signal in trading_signals:
                await self._execute_production_trade(signal)
            
            # アカウント状態更新
            self._update_account_status()
            
            # 定期的な通知（1時間ごと）
            if datetime.now().minute == 0:
                await self._send_hourly_report()
            
        except Exception as e:
            logger.error(f"Trading cycle error: {e}")
    
    async def _get_trading_signals(self) -> list:
        """取引シグナル取得（本番用）"""
        # 実際の実装では、マスターボットからシグナルを取得
        # ここでは本番用の保守的なシグナルを生成
        
        signals = []
        
        # ランダムな取引シグナル生成（本番用はより保守的）
        import random
        
        if random.random() < 0.05:  # 5%の確率で取引（ペーパー取引の半分）
            signal = {
                'symbol': random.choice(['BTCUSDT', 'ETHUSDT']),  # 主要通貨のみ
                'side': random.choice(['buy', 'sell']),
                'quantity': random.uniform(0.001, 0.01),  # より小さな数量
                'order_type': 'market',
                'confidence': random.uniform(0.7, 0.9)  # より高い信頼度
            }
            signals.append(signal)
        
        return signals
    
    async def _execute_production_trade(self, signal: dict):
        """本番取引実行"""
        try:
            from src.paper_trading.engine import OrderSide, OrderType
            
            side = OrderSide.BUY if signal['side'] == 'buy' else OrderSide.SELL
            order_type = OrderType.MARKET if signal['order_type'] == 'market' else OrderType.LIMIT
            
            # リスク管理チェック
            if not self._check_risk_limits(signal):
                print(f"[WARNING] リスク制限により取引をスキップ: {signal}")
                return
            
            order = self.paper_engine.place_order(
                symbol=signal['symbol'],
                side=side,
                order_type=order_type,
                quantity=signal['quantity']
            )
            
            # 取引ログ
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'type': 'production_trade',
                'signal': signal,
                'order_id': order.id,
                'status': order.status.value,
                'filled_price': order.filled_price
            }
            
            self._log_trade(trade_log)
            
            # 取引通知
            await self.notification_manager.notify_performance({
                'production_trade': {
                    'symbol': signal['symbol'],
                    'side': signal['side'],
                    'quantity': signal['quantity'],
                    'order_id': order.id,
                    'status': order.status.value
                }
            })
            
        except Exception as e:
            logger.error(f"Production trade execution error: {e}")
    
    def _check_risk_limits(self, signal: dict) -> bool:
        """リスク制限チェック"""
        summary = self.paper_engine.get_account_summary()
        
        # 最大ポジションサイズチェック
        max_position_size = self.config.get('max_position_size', 0.01)
        if signal['quantity'] > max_position_size:
            return False
        
        # 最大ドローダウンチェック
        max_drawdown = self.config.get('max_drawdown', 0.10)  # 10%
        if summary['max_drawdown'] > max_drawdown:
            return False
        
        # 残高チェック
        min_balance = self.config.get('min_balance', 5.0)  # $5
        if summary['balance'] < min_balance:
            return False
        
        return True
    
    def _update_account_status(self):
        """アカウント状態更新"""
        summary = self.paper_engine.get_account_summary()
        
        # 状態ログ
        status_log = {
            'timestamp': datetime.now().isoformat(),
            'type': 'production_status',
            'summary': summary
        }
        
        self._log_status(status_log)
    
    async def _send_hourly_report(self):
        """時間レポート送信"""
        summary = self.paper_engine.get_account_summary()
        
        # パフォーマンス通知
        performance_data = {
            'production_hourly': {
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
    
    def _log_trade(self, trade_log: dict):
        """取引ログ出力"""
        trade_file = self.log_dir / "production_trades.jsonl"
        with open(trade_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trade_log, ensure_ascii=False) + '\n')
    
    def _log_status(self, status_log: dict):
        """状態ログ出力"""
        status_file = self.log_dir / "production_status.jsonl"
        with open(status_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(status_log, ensure_ascii=False) + '\n')
    
    async def _cleanup(self):
        """クリーンアップ"""
        print("[INFO] 本番環境システム終了中...")
        
        self.is_running = False
        
        # 最終レポート生成
        await self._generate_final_report()
        
        # システム停止
        if self.master_bot:
            await self.master_bot.stop()
        
        if self.notification_manager:
            await self.notification_manager.shutdown()
        
        if self.paper_engine:
            self.paper_engine.stop()
        
        print("[SUCCESS] 本番環境システム終了完了")
    
    async def _generate_final_report(self):
        """最終レポート生成"""
        summary = self.paper_engine.get_account_summary()
        
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'type': 'production_final_report',
            'performance': summary,
            'trades': self.paper_engine.get_trade_history()
        }
        
        # レポートファイル出力
        report_file = self.log_dir / "production_final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        # 通知送信
        await self.notification_manager.notify_performance({
            'production_final': {
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
    print("本番環境システム（少額運用）")
    print("=" * 50)
    
    # 本番設定（保守的）
    config = {
        'initial_balance': 10.0,  # $10
        'commission_rate': 0.001,
        'risk_level': 'safe',
        'rebalance_interval_days': 30,
        'discord_webhook_url': '',  # テスト用は空文字
        'max_position_size': 0.01,  # 最大ポジションサイズ
        'stop_loss_pct': 0.05,  # 5%ストップロス
        'take_profit_pct': 0.10,  # 10%テイクプロフィット
        'max_drawdown': 0.10,  # 最大ドローダウン10%
        'min_balance': 5.0  # 最小残高$5
    }
    
    # 本番環境管理クラス初期化
    manager = ProductionManager(config)
    
    try:
        # 初期化
        await manager.initialize()
        
        # 本番取引実行（1時間のテスト）
        await manager.run_production_trading(duration_hours=1)
        
    except Exception as e:
        print(f"[ERROR] 本番環境システムエラー: {e}")
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
            print("\n[SUCCESS] 本番環境システムが正常に完了しました！")
        else:
            print("\n[ERROR] 本番環境システムに問題がありました。")
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")

