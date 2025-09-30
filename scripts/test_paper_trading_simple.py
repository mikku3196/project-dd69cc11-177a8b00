"""
簡易ペーパー取引テストスクリプト
"""
import asyncio
import json
import logging
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.paper_trading.engine import PaperTradingEngine, OrderSide, OrderType

logger = logging.getLogger(__name__)

async def test_paper_trading_simple():
    """簡易ペーパー取引テスト"""
    print("簡易ペーパー取引テスト")
    print("=" * 50)
    
    # ペーパー取引エンジン初期化
    engine = PaperTradingEngine(initial_balance=10000.0)
    engine.start()
    
    print("[INFO] ペーパー取引エンジン開始")
    
    # テスト取引実行
    trades = []
    
    # 1. BTC買い
    btc_buy = engine.place_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1
    )
    trades.append(btc_buy)
    print(f"[INFO] BTC買い注文: {btc_buy.id} - {btc_buy.status.value}")
    
    # 2. ETH買い
    eth_buy = engine.place_order(
        symbol="ETHUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0
    )
    trades.append(eth_buy)
    print(f"[INFO] ETH買い注文: {eth_buy.id} - {eth_buy.status.value}")
    
    # 3. BTC売り（部分決済）
    btc_sell = engine.place_order(
        symbol="BTCUSDT",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=0.05
    )
    trades.append(btc_sell)
    print(f"[INFO] BTC売り注文: {btc_sell.id} - {btc_sell.status.value}")
    
    # 4. 指値注文
    limit_order = engine.place_order(
        symbol="ADAUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=100.0,
        price=0.45
    )
    trades.append(limit_order)
    print(f"[INFO] ADA指値注文: {limit_order.id} - {limit_order.status.value}")
    
    # アカウントサマリー表示
    summary = engine.get_account_summary()
    print(f"\n[INFO] アカウントサマリー:")
    print(f"  残高: ${summary['balance']:.2f}")
    print(f"  エクイティ: ${summary['equity']:.2f}")
    print(f"  総取引数: {summary['total_trades']}")
    print(f"  勝率: {summary['win_rate']:.2%}")
    print(f"  総損益: ${summary['total_pnl']:.2f}")
    print(f"  リターン: {summary['return_pct']:.2%}")
    print(f"  最大ドローダウン: {summary['max_drawdown']:.2%}")
    
    # ポジション表示
    if summary['positions']:
        print(f"\n[INFO] ポジション:")
        for symbol, position in summary['positions'].items():
            print(f"  {symbol}: {position['quantity']} @ ${position['entry_price']:.2f}")
    
    # 取引履歴表示
    history = engine.get_trade_history(limit=10)
    if history:
        print(f"\n[INFO] 取引履歴:")
        for trade in history[-5:]:
            print(f"  {trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
    
    # ログファイル確認
    log_file = Path("logs/paper_trading.jsonl")
    if log_file.exists():
        print(f"\n[INFO] ログファイル: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"  ログ行数: {len(lines)}")
    
    engine.stop()
    print(f"\n[SUCCESS] ペーパー取引テスト完了")
    
    return True

async def test_paper_trading_continuous():
    """継続ペーパー取引テスト（1時間）"""
    print("\n継続ペーパー取引テスト（1時間）")
    print("=" * 50)
    
    engine = PaperTradingEngine(initial_balance=10000.0)
    engine.start()
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)
    
    trade_count = 0
    
    try:
        while datetime.now() < end_time:
            # ランダムな取引実行
            import random
            
            if random.random() < 0.1:  # 10%の確率で取引
                symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']
                symbol = random.choice(symbols)
                side = random.choice([OrderSide.BUY, OrderSide.SELL])
                quantity = random.uniform(0.01, 0.1)
                
                order = engine.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=quantity
                )
                
                trade_count += 1
                print(f"[INFO] 取引 {trade_count}: {side.value} {quantity} {symbol}")
            
            await asyncio.sleep(10)  # 10秒間隔
            
    except KeyboardInterrupt:
        print("[INFO] ユーザーによる中断")
    
    # 最終サマリー
    summary = engine.get_account_summary()
    print(f"\n[INFO] 継続テスト結果:")
    print(f"  実行時間: {(datetime.now() - start_time).total_seconds():.0f}秒")
    print(f"  総取引数: {trade_count}")
    print(f"  最終残高: ${summary['balance']:.2f}")
    print(f"  最終エクイティ: ${summary['equity']:.2f}")
    print(f"  総損益: ${summary['total_pnl']:.2f}")
    print(f"  リターン: {summary['return_pct']:.2%}")
    
    engine.stop()
    print(f"[SUCCESS] 継続ペーパー取引テスト完了")
    
    return True

async def main():
    """メイン関数"""
    print("ペーパー取引システムテスト")
    print("=" * 50)
    
    try:
        # 基本テスト
        await test_paper_trading_simple()
        
        # 継続テスト
        await test_paper_trading_continuous()
        
        print("\n[SUCCESS] すべてのペーパー取引テストが完了しました！")
        print("\n[INFO] 次のステップ:")
        print("  1. 1ヶ月間の継続ペーパー取引テスト")
        print("  2. 本番少額運用（$10程度）")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] ペーパー取引テストエラー: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n[SUCCESS] ペーパー取引システムが正常に動作します！")
        else:
            print("\n[ERROR] ペーパー取引システムに問題があります。")
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
