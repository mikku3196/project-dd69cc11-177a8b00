from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.tables import Base # 以前作成したモデル定義をインポート

# 設定ファイルに基づいてデータベースURLを決定
if settings.database.get("db_type") == "postgresql":
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
else:
    # デフォルトはSQLite
    SQLALCHEMY_DATABASE_URL = settings.database.get("db_url_sqlite", "sqlite:///./data/trading_bot.db")

# データベースエンジンを作成
# SQLiteの場合は、複数のスレッドからのアクセスを許可する設定を追加
engine_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_args)

# データベースセッションを作成するためのクラス
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    データベースを初期化し、定義されたテーブルをすべて作成する。
    アプリケーションの起動時に一度だけ呼び出す。
    """
    print("Initializing database...")
    print(f"Database URL: {SQLALCHEMY_DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

def get_db():
    """
    リクエストごとにデータベースセッションを提供する依存性関数。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
