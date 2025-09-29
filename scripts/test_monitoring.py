"""
自己進化型AIポートフォリオ自動売買システム - 簡易監視サーバー
"""

import asyncio
import logging
from datetime import datetime
import json

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 簡易サーキットブレーカー
class SimpleCircuitBreaker:
    def __init__(self):
        self.state = "CLOSED"
        self.fail_count = 0
        self.is_open_flag = False
    
    def is_open(self):
        return self.is_open_flag
    
    def get_state_info(self):
        return {
            "state": self.state,
            "fail_count": self.fail_count,
            "is_open": self.is_open_flag
        }


# グローバルインスタンス
circuit_breaker = SimpleCircuitBreaker()


async def mock_health_check():
    """モックヘルスチェック"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "healthy",
            "broker": "healthy", 
            "gemini": "healthy",
            "circuit_breaker": circuit_breaker.get_state_info()
        }
    }


async def mock_status():
    """モックステータス"""
    return {
        "uptime": "N/A",
        "version": "1.0.0",
        "environment": "development",
        "circuit_breaker": circuit_breaker.get_state_info()
    }


async def mock_metrics():
    """モックメトリクス"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "circuit_breaker": circuit_breaker.get_state_info(),
        "database": {"status": "connected"}
    }


async def simulate_circuit_breaker_open():
    """サーキットブレーカーをオープン状態にシミュレート"""
    circuit_breaker.state = "OPEN"
    circuit_breaker.fail_count = 10
    circuit_breaker.is_open_flag = True
    logger.info("サーキットブレーカーをオープン状態に設定しました")


async def simulate_circuit_breaker_reset():
    """サーキットブレーカーをリセット"""
    circuit_breaker.state = "CLOSED"
    circuit_breaker.fail_count = 0
    circuit_breaker.is_open_flag = False
    logger.info("サーキットブレーカーをリセットしました")


async def test_endpoints():
    """エンドポイントテスト"""
    logger.info("=== 監視エンドポイントテスト開始 ===")
    
    # ヘルスチェックテスト
    logger.info("1. ヘルスチェックテスト")
    health = await mock_health_check()
    logger.info(f"ヘルスチェック結果: {json.dumps(health, indent=2, ensure_ascii=False)}")
    
    if health["status"] == "ok":
        logger.info("[SUCCESS] ヘルスチェックが正常です")
    else:
        logger.error("[FAILED] ヘルスチェックが異常です")
    
    # ステータステスト
    logger.info("\n2. ステータステスト")
    status = await mock_status()
    logger.info(f"ステータス結果: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    # メトリクステスト
    logger.info("\n3. メトリクステスト")
    metrics = await mock_metrics()
    logger.info(f"メトリクス結果: {json.dumps(metrics, indent=2, ensure_ascii=False)}")
    
    # サーキットブレーカーオープンシミュレーション
    logger.info("\n4. サーキットブレーカーオープンシミュレーション")
    await simulate_circuit_breaker_open()
    
    health_open = await mock_health_check()
    logger.info(f"オープン状態のヘルスチェック: {json.dumps(health_open, indent=2, ensure_ascii=False)}")
    
    if health_open["components"]["circuit_breaker"]["is_open"]:
        logger.info("[SUCCESS] サーキットブレーカーが正常にオープン状態を表示しています")
    else:
        logger.error("[FAILED] サーキットブレーカーのオープン状態が正しく表示されていません")
    
    # サーキットブレーカーリセット
    logger.info("\n5. サーキットブレーカーリセット")
    await simulate_circuit_breaker_reset()
    
    health_reset = await mock_health_check()
    logger.info(f"リセット後のヘルスチェック: {json.dumps(health_reset, indent=2, ensure_ascii=False)}")
    
    if not health_reset["components"]["circuit_breaker"]["is_open"]:
        logger.info("[SUCCESS] サーキットブレーカーが正常にリセットされました")
    else:
        logger.error("[FAILED] サーキットブレーカーのリセットが正しく動作していません")


async def main():
    """メイン関数"""
    try:
        await test_endpoints()
        logger.info("\n=== 監視エンドポイントテスト完了 ===")
        return True
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n[SUCCESS] 監視エンドポイントテストが正常に完了しました")
    else:
        print("\n[FAILED] 監視エンドポイントテストが失敗しました")
