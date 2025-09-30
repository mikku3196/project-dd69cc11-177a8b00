from fastapi import FastAPI
from app.core.config import settings
from app.core.database import init_db

# ----------------------------------------------------
# アプリケーションの初期化処理
# ----------------------------------------------------
def initialize_app():
    """アプリケーション起動時に実行される初期化処理をまとめた関数。"""
    # データベースの初期化（テーブル作成）
    init_db()
    # 他にも初期化処理があればここに追加する
    # (例: マスターボットの起動、スケジューラの開始など)

# FastAPIアプリケーションインスタンスを作成
app = FastAPI(
    title="Self-Evolving AI Trading System",
    description="A fully autonomous asset management ecosystem.",
    version="1.0.0"
)

# ----------------------------------------------------
# イベントハンドラ
# ----------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """FastAPIアプリケーション起動時に一度だけ実行されるイベント。"""
    print("Application startup...")
    initialize_app()
    print("Application has been initialized and is ready.")

@app.on_event("shutdown")
async def shutdown_event():
    """FastAPIアプリケーション終了時に一度だけ実行されるイベント。"""
    print("Application shutdown...")


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
    # `reload=True` を設定すると、コード変更時にサーバーが自動で再起動して便利です
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)