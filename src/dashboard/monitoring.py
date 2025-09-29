"""
自己進化型AIポートフォリオ自動売買システム - 監視エンドポイント
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from ..core.database import db_manager
from ..utils.circuit_breaker import circuit_breaker
from ..api.bybit_client import BybitClient
from ..api.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="自己進化型AIポートフォリオ自動売買システム",
    description="監視・管理API",
    version="1.0.0"
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """ヘルスチェックエンドポイント"""
    try:
        # データベース接続チェック
        db_status = "healthy"
        try:
            async with db_manager.get_session() as session:
                await session.execute("SELECT 1")
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Bybit API接続チェック
        broker_status = "healthy"
        try:
            async with BybitClient() as bybit:
                await bybit.get_ticker("BTCUSDT")
        except Exception as e:
            broker_status = f"error: {str(e)}"
        
        # Gemini API接続チェック
        gemini_status = "healthy"
        try:
            gemini = GeminiClient()
            # 簡単なテストリクエスト
        except Exception as e:
            gemini_status = f"error: {str(e)}"
        
        # サーキットブレーカー状態
        circuit_info = circuit_breaker.get_state_info()
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_status,
                "broker": broker_status,
                "gemini": gemini_status,
                "circuit_breaker": {
                    "state": circuit_info["state"],
                    "is_open": circuit_info["is_open"],
                    "fail_count": circuit_info["fail_count"]
                }
            }
        }
        
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        raise HTTPException(status_code=500, detail=f"ヘルスチェック失敗: {str(e)}")


@app.get("/status")
async def system_status() -> Dict[str, Any]:
    """システムステータスエンドポイント"""
    try:
        # サーキットブレーカー詳細情報
        circuit_info = circuit_breaker.get_state_info()
        
        # システム情報
        system_info = {
            "uptime": "N/A",  # TODO: 実装
            "version": "1.0.0",
            "environment": "development",
            "circuit_breaker": circuit_info
        }
        
        return system_info
        
    except Exception as e:
        logger.error(f"ステータス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"ステータス取得失敗: {str(e)}")


@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """メトリクスエンドポイント"""
    try:
        # 基本的なメトリクス
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "circuit_breaker": circuit_breaker.get_state_info(),
            "database": {
                "status": "connected"  # TODO: 詳細なDBメトリクス
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"メトリクス取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"メトリクス取得失敗: {str(e)}")


@app.post("/circuit-breaker/reset")
async def reset_circuit_breaker() -> Dict[str, Any]:
    """サーキットブレーカーをリセット"""
    try:
        circuit_breaker.reset()
        
        return {
            "status": "success",
            "message": "サーキットブレーカーをリセットしました",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"サーキットブレーカーリセットエラー: {e}")
        raise HTTPException(status_code=500, detail=f"リセット失敗: {str(e)}")


@app.get("/logs/recent")
async def get_recent_logs(limit: int = 100) -> Dict[str, Any]:
    """最近のログを取得"""
    try:
        # TODO: ログファイルから最近のログを読み取り
        logs = {
            "message": "ログ機能は実装中です",
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return logs
        
    except Exception as e:
        logger.error(f"ログ取得エラー: {e}")
        raise HTTPException(status_code=500, detail=f"ログ取得失敗: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
