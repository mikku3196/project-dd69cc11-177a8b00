"""
Webダッシュボード - FastAPI バックエンド
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# プロジェクトルートをパスに追加
import sys
sys.path.append('.')

from src.bots.master_bot import MasterBot

logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="Trading Bot Dashboard",
    description="AI Trading Bot Management Dashboard",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# マスターボットインスタンス
master_bot: Optional[MasterBot] = None
websocket_connections: List[WebSocket] = []

# Pydanticモデル
class BotStatus(BaseModel):
    is_running: bool
    risk_level: str
    allocation: Dict[str, float]
    risk_metrics: Dict[str, Any]
    performance_data: Dict[str, Any]
    last_rebalance: str

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    source: str

class ControlCommand(BaseModel):
    action: str
    parameters: Optional[Dict[str, Any]] = None

# ログストレージ（簡易実装）
log_storage: List[LogEntry] = []

@app.on_event("startup")
async def startup_event():
    """アプリケーション開始時のイベント"""
    global master_bot
    
    logger.info("Dashboard starting up...")
    
    # マスターボット初期化
    config = {
        'risk_level': 'safe',
        'rebalance_interval_days': 30
    }
    
    master_bot = MasterBot(config)
    
    # サブボット初期化
    await master_bot._initialize_sub_bots()
    
    # バックグラウンドタスク開始
    asyncio.create_task(background_status_updater())
    
    logger.info("Dashboard started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時のイベント"""
    global master_bot
    
    logger.info("Dashboard shutting down...")
    
    if master_bot:
        await master_bot.stop()
    
    logger.info("Dashboard shutdown complete")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "Trading Bot Dashboard API", "status": "running"}

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "master_bot_running": master_bot.is_running if master_bot else False
    }

@app.get("/status", response_model=BotStatus)
async def get_status():
    """マスターボットの状態取得"""
    if not master_bot:
        raise HTTPException(status_code=503, detail="Master bot not initialized")
    
    try:
        status = master_bot.get_status()
        return BotStatus(**status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs", response_model=List[LogEntry])
async def get_logs(limit: int = 50):
    """最新のログ取得"""
    return log_storage[-limit:] if log_storage else []

@app.post("/control/stop")
async def emergency_stop():
    """緊急停止"""
    if not master_bot:
        raise HTTPException(status_code=503, detail="Master bot not initialized")
    
    try:
        await master_bot.stop()
        
        # ログ記録
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="CRITICAL",
            message="Emergency stop triggered",
            source="dashboard"
        )
        log_storage.append(log_entry)
        
        return {"message": "Emergency stop executed", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error during emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control/start")
async def start_bot():
    """ボット開始"""
    if not master_bot:
        raise HTTPException(status_code=503, detail="Master bot not initialized")
    
    try:
        if not master_bot.is_running:
            asyncio.create_task(master_bot.start())
            
            # ログ記録
            log_entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level="INFO",
                message="Bot started",
                source="dashboard"
            )
            log_storage.append(log_entry)
            
            return {"message": "Bot started", "timestamp": datetime.now().isoformat()}
        else:
            return {"message": "Bot already running", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/control/rebalance")
async def trigger_rebalance():
    """手動再配分実行"""
    if not master_bot:
        raise HTTPException(status_code=503, detail="Master bot not initialized")
    
    try:
        await master_bot._rebalance_allocation()
        
        # ログ記録
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level="INFO",
            message="Manual rebalance triggered",
            source="dashboard"
        )
        log_storage.append(log_entry)
        
        return {"message": "Rebalance executed", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error during rebalance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket接続"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    logger.info(f"WebSocket connected. Total connections: {len(websocket_connections)}")
    
    try:
        while True:
            # クライアントからのメッセージ待機
            data = await websocket.receive_text()
            
            # メッセージ処理（必要に応じて）
            if data == "ping":
                await websocket.send_text("pong")
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(websocket_connections)}")

async def background_status_updater():
    """バックグラウンド状態更新タスク"""
    while True:
        try:
            if master_bot and websocket_connections:
                # マスターボット状態取得
                status = master_bot.get_status()
                
                # WebSocket接続に状態送信
                for websocket in websocket_connections.copy():
                    try:
                        await websocket.send_text(json.dumps(status, ensure_ascii=False))
                    except Exception as e:
                        logger.error(f"Error sending WebSocket message: {e}")
                        websocket_connections.remove(websocket)
            
            # 5秒間隔で更新
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in background status updater: {e}")
            await asyncio.sleep(10)

# ログハンドラー設定
def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ログをストレージに記録
    class DashboardLogHandler(logging.Handler):
        def emit(self, record):
            log_entry = LogEntry(
                timestamp=datetime.now().isoformat(),
                level=record.levelname,
                message=record.getMessage(),
                source=record.name
            )
            log_storage.append(log_entry)
            
            # ログ数制限（最新1000件）
            if len(log_storage) > 1000:
                log_storage.pop(0)
    
    # ハンドラー追加
    dashboard_handler = DashboardLogHandler()
    logger.addHandler(dashboard_handler)

if __name__ == "__main__":
    setup_logging()
    
    logger.info("Starting Trading Bot Dashboard...")
    
    uvicorn.run(
        "src.dashboard.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )