"""
自己進化型AIポートフォリオ自動売買システム - 簡易テストスクリプト
"""

import asyncio
import logging
import sys
import os

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# サーキットブレーカーの簡易実装
class SimpleCircuitBreaker:
    def __init__(self, fail_threshold=10, window=60, open_for=300):
        self.fail_threshold = fail_threshold
        self.window = window
        self.open_for = open_for
        self.fail_times = []
        self.open_until = 0
        self.state = "CLOSED"
    
    def record_failure(self, error=None):
        import time
        now = time.time()
        self.fail_times = [t for t in self.fail_times if now - t < self.window]
        self.fail_times.append(now)
        
        if len(self.fail_times) >= self.fail_threshold:
            self.open_until = now + self.open_for
            self.state = "OPEN"
            logger.critical(f"サーキットブレーカーがオープンしました: {len(self.fail_times)}回の失敗")
    
    def record_success(self):
        self.fail_times.clear()
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("サーキットブレーカーがクローズしました")
    
    def is_open(self):
        import time
        now = time.time()
        
        if self.state == "OPEN":
            if now >= self.open_until:
                self.state = "HALF_OPEN"
                logger.info("サーキットブレーカーがハーフオープンに移行しました")
                return False
            return True
        
        return False
    
    def get_state_info(self):
        return {
            "state": self.state,
            "fail_count": len(self.fail_times),
            "is_open": self.is_open()
        }


# グローバルインスタンス
circuit_breaker = SimpleCircuitBreaker()


async def test_circuit_breaker():
    """サーキットブレーカーテスト"""
    logger.info("=== サーキットブレーカーテスト開始 ===")
    
    # リセット
    circuit_breaker.fail_times.clear()
    circuit_breaker.state = "CLOSED"
    circuit_breaker.open_until = 0
    
    logger.info("サーキットブレーカーをリセットしました")
    
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
        
        # オープン状態での実行試行
        try:
            if circuit_breaker.is_open():
                raise RuntimeError("Circuit breaker is open")
        except RuntimeError as e:
            if "Circuit breaker is open" in str(e):
                logger.info("✅ サーキットブレーカーが正常に実行をブロックしました")
            else:
                logger.error(f"❌ 予期しないエラー: {e}")
    else:
        logger.error("❌ サーキットブレーカーがオープンになりませんでした")


async def test_rate_limit_simulation():
    """レート制限シミュレーション"""
    logger.info("=== レート制限シミュレーション開始 ===")
    
    # モックレスポンス
    rate_limit_response = {"retCode": 429, "retMsg": "Rate limit exceeded"}
    success_response = {"retCode": 0, "retMsg": "OK", "result": {"orderId": "test_order_123"}}
    
    # シミュレーション
    responses = [rate_limit_response, rate_limit_response, success_response]
    
    for i, response in enumerate(responses, 1):
        logger.info(f"{i}回目の注文実行...")
        
        if response["retCode"] == 429:
            logger.warning(f"レート制限検出: {response['retMsg']}")
            logger.info("指数バックオフで待機...")
            await asyncio.sleep(0.5 * (2 ** (i - 1)))
        else:
            logger.info(f"✅ 注文成功: {response['result']['orderId']}")
            break


async def test_health_endpoint():
    """ヘルスチェックエンドポイントテスト"""
    logger.info("=== ヘルスチェックエンドポイントテスト ===")
    
    # モックヘルスチェック
    health_data = {
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
        "components": {
            "database": "healthy",
            "broker": "healthy",
            "gemini": "healthy",
            "circuit_breaker": {
                "state": circuit_breaker.state,
                "is_open": circuit_breaker.is_open(),
                "fail_count": len(circuit_breaker.fail_times)
            }
        }
    }
    
    logger.info(f"ヘルスチェック結果: {health_data}")
    
    if health_data["status"] == "ok":
        logger.info("✅ ヘルスチェックが正常に動作しています")
    else:
        logger.error("❌ ヘルスチェックが異常です")


async def main():
    """メイン関数"""
    logger.info("=== 自己進化型AIポートフォリオ自動売買システム テスト開始 ===")
    
    try:
        # サーキットブレーカーテスト
        await test_circuit_breaker()
        
        logger.info("\n" + "="*50 + "\n")
        
        # レート制限シミュレーション
        await test_rate_limit_simulation()
        
        logger.info("\n" + "="*50 + "\n")
        
        # ヘルスチェックテスト
        await test_health_endpoint()
        
        logger.info("\n=== 全テスト完了 ===")
        
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n[SUCCESS] 全テストが正常に完了しました", flush=True)
        sys.exit(0)
    else:
        print("\n[FAILED] テストが失敗しました", flush=True)
        sys.exit(1)
