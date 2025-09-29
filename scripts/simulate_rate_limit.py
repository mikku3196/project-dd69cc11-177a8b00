"""
自己進化型AIポートフォリオ自動売買システム - レート制限シミュレーター
"""

import asyncio
import logging
from unittest.mock import AsyncMock, patch
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.bybit_client import BybitClient
from src.utils.circuit_breaker import circuit_breaker

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def simulate_rate_limit():
    """レート制限シミュレーション"""
    
    logger.info("レート制限シミュレーション開始")
    
    # サーキットブレーカーをリセット
    circuit_breaker.reset()
    logger.info("サーキットブレーカーをリセットしました")
    
    # モックレスポンス（レート制限）
    rate_limit_response = {
        "retCode": 429,
        "retMsg": "Rate limit exceeded",
        "result": {}
    }
    
    success_response = {
        "retCode": 0,
        "retMsg": "OK",
        "result": {
            "orderId": "test_order_123"
        }
    }
    
    with patch('src.api.bybit_client.BybitClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # セッションコンテキストマネージャーをモック
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # 最初の2回はレート制限、3回目は成功
        mock_client._make_request.side_effect = [
            rate_limit_response,
            rate_limit_response,
            success_response
        ]
        
        # テスト実行
        async with BybitClient() as client:
            try:
                # 最初の注文（レート制限で失敗）
                logger.info("1回目の注文実行...")
                result1 = await client.place_order(
                    symbol="BTCUSDT",
                    side="Buy",
                    order_type="Market",
                    qty="0.001"
                )
                logger.info(f"1回目結果: {result1}")
                
            except Exception as e:
                logger.warning(f"1回目エラー（予想通り）: {e}")
            
            try:
                # 2回目の注文（レート制限で失敗）
                logger.info("2回目の注文実行...")
                result2 = await client.place_order(
                    symbol="BTCUSDT",
                    side="Buy",
                    order_type="Market",
                    qty="0.001"
                )
                logger.info(f"2回目結果: {result2}")
                
            except Exception as e:
                logger.warning(f"2回目エラー（予想通り）: {e}")
            
            try:
                # 3回目の注文（成功）
                logger.info("3回目の注文実行...")
                result3 = await client.place_order(
                    symbol="BTCUSDT",
                    side="Buy",
                    order_type="Market",
                    qty="0.001"
                )
                logger.info(f"3回目結果: {result3}")
                
            except Exception as e:
                logger.error(f"3回目エラー: {e}")
    
    # サーキットブレーカーの状態を確認
    state_info = circuit_breaker.get_state_info()
    logger.info(f"サーキットブレーカー状態: {state_info}")


async def simulate_circuit_breaker():
    """サーキットブレーカーシミュレーション"""
    
    logger.info("サーキットブレーカーシミュレーション開始")
    
    # サーキットブレーカーをリセット
    circuit_breaker.reset()
    
    # 連続失敗でサーキットをオープン
    logger.info("連続失敗をシミュレート...")
    for i in range(10):
        circuit_breaker.record_failure(Exception(f"Test failure {i+1}"))
        logger.info(f"失敗 {i+1}/10 記録")
    
    # サーキットがオープンになったか確認
    state_info = circuit_breaker.get_state_info()
    logger.info(f"サーキットブレーカー状態: {state_info}")
    
    if circuit_breaker.is_open():
        logger.info("✅ サーキットブレーカーが正常にオープンしました")
        
        # オープン状態での注文試行
        try:
            with patch('src.api.bybit_client.BybitClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value = mock_client
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)
                
                async with BybitClient() as client:
                    await client.place_order(
                        symbol="BTCUSDT",
                        side="Buy",
                        order_type="Market",
                        qty="0.001"
                    )
        except RuntimeError as e:
            if "Circuit breaker is open" in str(e):
                logger.info("✅ サーキットブレーカーが正常に注文をブロックしました")
            else:
                logger.error(f"❌ 予期しないエラー: {e}")
        except Exception as e:
            logger.error(f"❌ 予期しないエラー: {e}")
    else:
        logger.error("❌ サーキットブレーカーがオープンになりませんでした")


async def main():
    """メイン関数"""
    logger.info("=== レート制限・サーキットブレーカーテスト開始 ===")
    
    # レート制限シミュレーション
    await simulate_rate_limit()
    
    logger.info("\n" + "="*50 + "\n")
    
    # サーキットブレーカーシミュレーション
    await simulate_circuit_breaker()
    
    logger.info("=== テスト完了 ===")


if __name__ == "__main__":
    asyncio.run(main())
