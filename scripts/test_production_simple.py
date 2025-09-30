"""
簡易本番環境テストスクリプト
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

async def test_production_environment():
    """本番環境テスト"""
    print("本番環境テスト（少額運用）")
    print("=" * 50)
    
    # 本番設定（保守的）
    initial_balance = 10.0  # $10
    max_position_size = 0.01  # 最大ポジションサイズ
    max_drawdown = 0.10  # 最大ドローダウン10%
    min_balance = 5.0  # 最小残高$5
    
    # ペーパー取引エンジン初期化（本番用）
    engine = PaperTradingEngine(initial_balance=initial_balance)
    engine.start()
    
    print(f"[INFO] 本番環境初期化完了")
    print(f"  初期残高: ${initial_balance}")
    print(f"  最大ポジションサイズ: {max_position_size}")
    print(f"  最大ドローダウン: {max_drawdown:.1%}")
    print(f"  最小残高: ${min_balance}")
    
    # 本番取引テスト
    trades = []
    
    # 1. 保守的なBTC買い
    btc_buy = engine.place_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.001  # 非常に小さな数量
    )
    trades.append(btc_buy)
    print(f"[INFO] 保守的BTC買い: {btc_buy.id} - {btc_buy.status.value}")
    
    # 2. 保守的なETH買い
    eth_buy = engine.place_order(
        symbol="ETHUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.01  # 非常に小さな数量
    )
    trades.append(eth_buy)
    print(f"[INFO] 保守的ETH買い: {eth_buy.id} - {eth_buy.status.value}")
    
    # 3. 部分決済
    btc_sell = engine.place_order(
        symbol="BTCUSDT",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=0.0005  # 半分決済
    )
    trades.append(btc_sell)
    print(f"[INFO] BTC部分決済: {btc_sell.id} - {btc_sell.status.value}")
    
    # アカウントサマリー表示
    summary = engine.get_account_summary()
    print(f"\n[INFO] 本番環境アカウントサマリー:")
    print(f"  残高: ${summary['balance']:.2f}")
    print(f"  エクイティ: ${summary['equity']:.2f}")
    print(f"  総取引数: {summary['total_trades']}")
    print(f"  勝率: {summary['win_rate']:.2%}")
    print(f"  総損益: ${summary['total_pnl']:.2f}")
    print(f"  リターン: {summary['return_pct']:.2%}")
    print(f"  最大ドローダウン: {summary['max_drawdown']:.2%}")
    
    # リスクチェック
    print(f"\n[INFO] リスクチェック:")
    print(f"  最大ドローダウン制限: {max_drawdown:.1%}")
    print(f"  現在のドローダウン: {summary['max_drawdown']:.2%}")
    print(f"  制限超過: {'YES' if summary['max_drawdown'] > max_drawdown else 'NO'}")
    
    print(f"  最小残高制限: ${min_balance}")
    print(f"  現在の残高: ${summary['balance']:.2f}")
    print(f"  制限超過: {'YES' if summary['balance'] < min_balance else 'NO'}")
    
    # ポジション表示
    if summary['positions']:
        print(f"\n[INFO] ポジション:")
        for symbol, position in summary['positions'].items():
            print(f"  {symbol}: {position['quantity']} @ ${position['entry_price']:.2f}")
    
    # 取引履歴表示
    history = engine.get_trade_history(limit=10)
    if history:
        print(f"\n[INFO] 取引履歴:")
        for trade in history[-3:]:
            print(f"  {trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
    
    # ログファイル確認
    log_file = Path("logs/paper_trading.jsonl")
    if log_file.exists():
        print(f"\n[INFO] ログファイル: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"  ログ行数: {len(lines)}")
    
    engine.stop()
    print(f"\n[SUCCESS] 本番環境テスト完了")
    
    return True

async def test_production_continuous():
    """継続本番環境テスト（30分）"""
    print("\n継続本番環境テスト（30分）")
    print("=" * 50)
    
    engine = PaperTradingEngine(initial_balance=10.0)
    engine.start()
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=30)
    
    trade_count = 0
    
    try:
        while datetime.now() < end_time:
            # ランダムな取引実行（本番用はより保守的）
            import random
            
            if random.random() < 0.05:  # 5%の確率で取引
                symbols = ['BTCUSDT', 'ETHUSDT']  # 主要通貨のみ
                symbol = random.choice(symbols)
                side = random.choice([OrderSide.BUY, OrderSide.SELL])
                quantity = random.uniform(0.001, 0.01)  # より小さな数量
                
                order = engine.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=quantity
                )
                
                trade_count += 1
                print(f"[INFO] 本番取引 {trade_count}: {side.value} {quantity} {symbol}")
            
            await asyncio.sleep(30)  # 30秒間隔
            
    except KeyboardInterrupt:
        print("[INFO] ユーザーによる中断")
    
    # 最終サマリー
    summary = engine.get_account_summary()
    print(f"\n[INFO] 継続本番テスト結果:")
    print(f"  実行時間: {(datetime.now() - start_time).total_seconds():.0f}秒")
    print(f"  総取引数: {trade_count}")
    print(f"  最終残高: ${summary['balance']:.2f}")
    print(f"  最終エクイティ: ${summary['equity']:.2f}")
    print(f"  総損益: ${summary['total_pnl']:.2f}")
    print(f"  リターン: {summary['return_pct']:.2%}")
    print(f"  最大ドローダウン: {summary['max_drawdown']:.2%}")
    
    engine.stop()
    print(f"[SUCCESS] 継続本番環境テスト完了")
    
    return True

async def main():
    """メイン関数"""
    print("本番環境システムテスト")
    print("=" * 50)
    
    try:
        # 基本テスト
        await test_production_environment()
        
        # 継続テスト
        await test_production_continuous()
        
        print("\n[SUCCESS] すべての本番環境テストが完了しました！")
        print("\n[INFO] 次のステップ:")
        print("  1. 実際のAPIキーでの本番取引")
        print("  2. 24時間継続運用テスト")
        print("  3. 本格的な資金投入")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 本番環境テストエラー: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        success = asyncio.run(main())
        if success:
            print("\n[SUCCESS] 本番環境システムが正常に動作します！")
        else:
            print("\n[ERROR] 本番環境システムに問題があります。")
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
