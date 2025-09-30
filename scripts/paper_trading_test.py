"""
ペーパー取引テスト自動化スクリプト
Bybit Testnet APIを使用した1ヶ月間の継続取引テスト
"""
import asyncio
import logging
import sys
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.core.config import config
from src.api.bybit_client import BybitClient
from src.utils.circuit_breaker import circuit_breaker
from src.analysis.decision_engine import DecisionEngine
from src.bots.sub_bot import SubBot

logger = logging.getLogger(__name__)

class PaperTradingTest:
    """ペーパー取引テストクラス"""
    
    def __init__(self, test_duration_days: int = 30):
        self.test_duration = timedelta(days=test_duration_days)
        self.start_time = datetime.now()
        self.end_time = self.start_time + self.test_duration
        
        # テスト結果記録
        self.trades: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.error_log: List[Dict[str, Any]] = []
        
        # 初期設定
        self.initial_balance = 1000.0  # テスト用初期残高
        self.current_balance = self.initial_balance
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # ログファイル設定
        self.setup_logging()
        
    def setup_logging(self):
        """ログ設定"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # メインログファイル
        log_file = log_dir / f"paper_trading_{timestamp}.log"
        
        # 取引ログファイル（CSV）
        self.trades_csv = log_dir / f"trades_{timestamp}.csv"
        
        # パフォーマンスログファイル（JSON）
        self.performance_json = log_dir / f"performance_{timestamp}.json"
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logger.info(f"ペーパー取引テスト開始 - ログファイル: {log_file}")
        logger.info(f"テスト期間: {self.start_time} ～ {self.end_time}")
        
    async def run_test(self):
        """ペーパー取引テストを実行"""
        logger.info("=== ペーパー取引テスト開始 ===")
        
        try:
            # Bybit Testnet接続テスト
            async with BybitClient() as bybit:
                logger.info("Bybit Testnet接続確認中...")
                balance = await bybit.get_wallet_balance()
                logger.info(f"Testnet残高取得: {balance}")
            
            # 意思決定エンジン初期化
            decision_engine = DecisionEngine()
            
            # サブボット初期化
            sub_bots = {
                'stable': SubBot('stable', {'max_position_size': 0.1, 'risk_tolerance': 0.01}),
                'balanced': SubBot('balanced', {'max_position_size': 0.2, 'risk_tolerance': 0.02}),
                'aggressive': SubBot('aggressive', {'max_position_size': 0.3, 'risk_tolerance': 0.03})
            }
            
            # メインループ
            await self.main_trading_loop(bybit, decision_engine, sub_bots)
            
        except Exception as e:
            logger.error(f"ペーパー取引テストエラー: {e}")
            self.error_log.append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': 'main_loop_error'
            })
        finally:
            await self.finalize_test()
    
    async def main_trading_loop(self, bybit: BybitClient, decision_engine: DecisionEngine, sub_bots: Dict[str, SubBot]):
        """メイン取引ループ"""
        logger.info("メイン取引ループ開始")
        
        while datetime.now() < self.end_time:
            try:
                # 市場データ取得
                market_data = await self.get_market_data(bybit)
                
                # 意思決定エンジンで分析
                analysis = await decision_engine.analyze_market(market_data)
                
                # 各サブボットで取引判断
                for bot_name, bot in sub_bots.items():
                    await self.execute_bot_trading(bot_name, bot, analysis, bybit)
                
                # パフォーマンス記録
                await self.record_performance()
                
                # 次のサイクルまで待機（5分間隔）
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"取引ループエラー: {e}")
                self.error_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'type': 'trading_loop_error'
                })
                await asyncio.sleep(60)  # エラー時は1分待機
    
    async def get_market_data(self, bybit: BybitClient) -> Dict[str, Any]:
        """市場データを取得"""
        try:
            # BTC価格取得
            ticker = await bybit.get_ticker("BTCUSDT")
            
            # オープンポジション取得
            positions = await bybit.get_open_positions()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'btc_price': float(ticker.get('result', {}).get('lastPrice', 0)),
                'positions': positions.get('result', {}).get('list', []),
                'balance': self.current_balance
            }
        except Exception as e:
            logger.error(f"市場データ取得エラー: {e}")
            return {'timestamp': datetime.now().isoformat(), 'error': str(e)}
    
    async def execute_bot_trading(self, bot_name: str, bot: SubBot, analysis: Dict[str, Any], bybit: BybitClient):
        """サブボットの取引実行"""
        try:
            # ボットの取引判断
            decision = await bot.make_decision(analysis)
            
            if decision['action'] == 'BUY':
                await self.execute_buy_order(bot_name, decision, bybit)
            elif decision['action'] == 'SELL':
                await self.execute_sell_order(bot_name, decision, bybit)
            elif decision['action'] == 'HOLD':
                logger.debug(f"{bot_name}: HOLD - {decision['reason']}")
                
        except Exception as e:
            logger.error(f"{bot_name} 取引実行エラー: {e}")
            self.error_log.append({
                'timestamp': datetime.now().isoformat(),
                'bot': bot_name,
                'error': str(e),
                'type': 'bot_trading_error'
            })
    
    async def execute_buy_order(self, bot_name: str, decision: Dict[str, Any], bybit: BybitClient):
        """買い注文実行"""
        try:
            # ペーパー取引なので実際の注文は実行しない
            trade = {
                'timestamp': datetime.now().isoformat(),
                'bot': bot_name,
                'action': 'BUY',
                'symbol': decision.get('symbol', 'BTCUSDT'),
                'quantity': decision.get('quantity', 0),
                'price': decision.get('price', 0),
                'reason': decision.get('reason', ''),
                'balance_before': self.current_balance,
                'balance_after': self.current_balance - (decision.get('quantity', 0) * decision.get('price', 0))
            }
            
            self.trades.append(trade)
            self.current_balance = trade['balance_after']
            
            logger.info(f"{bot_name} BUY: {trade['quantity']} @ {trade['price']} - {trade['reason']}")
            
        except Exception as e:
            logger.error(f"{bot_name} 買い注文エラー: {e}")
    
    async def execute_sell_order(self, bot_name: str, decision: Dict[str, Any], bybit: BybitClient):
        """売り注文実行"""
        try:
            # ペーパー取引なので実際の注文は実行しない
            trade = {
                'timestamp': datetime.now().isoformat(),
                'bot': bot_name,
                'action': 'SELL',
                'symbol': decision.get('symbol', 'BTCUSDT'),
                'quantity': decision.get('quantity', 0),
                'price': decision.get('price', 0),
                'reason': decision.get('reason', ''),
                'balance_before': self.current_balance,
                'balance_after': self.current_balance + (decision.get('quantity', 0) * decision.get('price', 0))
            }
            
            self.trades.append(trade)
            self.current_balance = trade['balance_after']
            
            logger.info(f"{bot_name} SELL: {trade['quantity']} @ {trade['price']} - {trade['reason']}")
            
        except Exception as e:
            logger.error(f"{bot_name} 売り注文エラー: {e}")
    
    async def record_performance(self):
        """パフォーマンス記録"""
        try:
            total_return = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
            
            self.performance_metrics = {
                'timestamp': datetime.now().isoformat(),
                'initial_balance': self.initial_balance,
                'current_balance': self.current_balance,
                'total_return_pct': total_return,
                'total_trades': len(self.trades),
                'circuit_breaker_status': circuit_breaker.get_status(),
                'error_count': len(self.error_log)
            }
            
            logger.info(f"パフォーマンス: 残高={self.current_balance:.2f}, リターン={total_return:.2f}%, 取引数={len(self.trades)}")
            
        except Exception as e:
            logger.error(f"パフォーマンス記録エラー: {e}")
    
    async def finalize_test(self):
        """テスト終了処理"""
        logger.info("=== ペーパー取引テスト終了 ===")
        
        # 最終パフォーマンス計算
        final_return = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        # CSVファイルに取引履歴を保存
        await self.save_trades_to_csv()
        
        # JSONファイルにパフォーマンスを保存
        await self.save_performance_to_json()
        
        # 最終レポート
        logger.info(f"最終残高: {self.current_balance:.2f}")
        logger.info(f"総リターン: {final_return:.2f}%")
        logger.info(f"総取引数: {len(self.trades)}")
        logger.info(f"エラー数: {len(self.error_log)}")
        logger.info(f"サーキットブレーカー最終状態: {circuit_breaker.get_status()}")
    
    async def save_trades_to_csv(self):
        """取引履歴をCSVファイルに保存"""
        try:
            with open(self.trades_csv, 'w', newline='', encoding='utf-8') as csvfile:
                if self.trades:
                    fieldnames = self.trades[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.trades)
            
            logger.info(f"取引履歴をCSVファイルに保存: {self.trades_csv}")
            
        except Exception as e:
            logger.error(f"CSV保存エラー: {e}")
    
    async def save_performance_to_json(self):
        """パフォーマンスをJSONファイルに保存"""
        try:
            performance_data = {
                'test_summary': {
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'duration_days': self.test_duration.days,
                    'initial_balance': self.initial_balance,
                    'final_balance': self.current_balance,
                    'total_return_pct': ((self.current_balance - self.initial_balance) / self.initial_balance) * 100,
                    'total_trades': len(self.trades),
                    'error_count': len(self.error_log)
                },
                'performance_metrics': self.performance_metrics,
                'error_log': self.error_log,
                'circuit_breaker_final_status': circuit_breaker.get_status()
            }
            
            with open(self.performance_json, 'w', encoding='utf-8') as jsonfile:
                json.dump(performance_data, jsonfile, indent=2, ensure_ascii=False)
            
            logger.info(f"パフォーマンスをJSONファイルに保存: {self.performance_json}")
            
        except Exception as e:
            logger.error(f"JSON保存エラー: {e}")


async def main():
    """メイン関数"""
    test = PaperTradingTest(test_duration_days=30)
    await test.run_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        sys.exit(1)
