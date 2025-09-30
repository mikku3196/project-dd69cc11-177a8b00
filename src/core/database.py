"""
データベース接続設定
SQLAlchemyエンジンとセッション管理
"""
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

logger = logging.getLogger(__name__)

# データベースURL設定
DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    'sqlite:///./data/trading_bot.db'
)

# SQLAlchemyエンジン作成
def create_database_engine():
    """データベースエンジンを作成"""
    try:
        if DATABASE_URL.startswith('sqlite'):
            # SQLite用設定
            engine = create_engine(
                DATABASE_URL,
                echo=False,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 30
                }
            )
        else:
            # PostgreSQL用設定
            engine = create_engine(
                DATABASE_URL,
                echo=False,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
        
        logger.info(f"Database engine created: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise

# エンジン作成
engine = create_database_engine()

# セッションメーカー作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Baseクラス
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """データベースセッションを取得（依存性注入用）"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """テーブルを作成"""
    try:
        # テーブル作成
        from src.models.tables import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # 作成されたテーブル一覧をログ出力
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise

def drop_tables():
    """テーブルを削除（開発・テスト用）"""
    try:
        from src.models.tables import Base
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise

def check_database_connection():
    """データベース接続を確認"""
    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            result = connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

# データベース初期化
def init_database():
    """データベースを初期化"""
    try:
        # 接続確認
        if not check_database_connection():
            raise Exception("Database connection failed")
        
        # テーブル作成
        create_tables()
        
        logger.info("Database initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    # テスト実行
    init_database()