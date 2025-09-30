from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db

# ----------------------------------------------------
# アプリケーションのライフサイクル管理 (Lifespan)
# ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時に実行される処理
    print("Application startup...")
    print("Initializing application...")
    # データベースの初期化（テーブル作成）
    init_db()
    # 他の初期化処理 (例: ボットの起動) はここに追加
    print("Application has been initialized and is ready.")
    
    yield  # ここでアプリケーションが稼働状態になる
    
    # アプリケーション終了時に実行される処理
    print("Application shutdown...")


# FastAPIアプリケーションインスタンスを作成
app = FastAPI(
    title="Self-Evolving AI Trading System",
    description="A fully autonomous asset management ecosystem.",
    version="1.0.0",
    lifespan=lifespan  # 新しいlifespanイベントハンドラを登録
)


# ----------------------------------------------------
# APIエンドポイント
# ----------------------------------------------------
@app.get("/")
async def root():
    """システムのルートエンドポイント。動作確認用。"""
    return {
        "message": "AI Trading System is running.",
        "environment": settings.general.get('environment'),
        "database_type": settings.database.get('db_type'),
        "system_status": "OK"
    }

# このファイルが直接実行された場合のサーバー起動処理
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)