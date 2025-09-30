"""
監視サーバー起動スクリプト
FastAPI監視エンドポイントを起動
"""
import uvicorn
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.dashboard.monitoring import app

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("監視サーバー起動中...")
    logger.info("エンドポイント:")
    logger.info("  - http://localhost:8000/health")
    logger.info("  - http://localhost:8000/status")
    logger.info("  - http://localhost:8000/metrics")
    logger.info("  - http://localhost:8000/circuit-breaker/reset")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
