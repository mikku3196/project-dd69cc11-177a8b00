"""
自己進化型AIポートフォリオ自動売買システム - データベース管理モジュール
"""

import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, Integer, Boolean, Text, JSON
from datetime import datetime
import logging

from .config import config

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """データベースベースクラス"""
    pass


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """データベースを初期化"""
        try:
            # データベースURLを取得
            db_url = config.database.url
            
            # SQLiteの場合、非同期対応のURLに変換
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            
            # エンジンを作成
            self.engine = create_async_engine(
                db_url,
                echo=config.database.echo,
                pool_size=config.database.pool_size,
                max_overflow=config.database.max_overflow,
                future=True
            )
            
            # セッションファクトリーを作成
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # テーブルを作成
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("データベースが正常に初期化されました")
            
        except Exception as e:
            logger.error(f"データベースの初期化に失敗しました: {e}")
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """データベースセッションを取得"""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"データベースセッションエラー: {e}")
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """データベース接続を閉じる"""
        if self.engine:
            await self.engine.dispose()
            logger.info("データベース接続を閉じました")


# グローバルデータベースマネージャー
db_manager = DatabaseManager()


# データベースモデルの定義
class Account(Base):
    """アカウント情報"""
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bot_type: Mapped[str] = mapped_column(String(50), nullable=False)  # conservative, balanced, aggressive
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    allocated_balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Trade(Base):
    """取引履歴"""
    __tablename__ = "trades"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    fee: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class MarketData(Base):
    """市場データ"""
    __tablename__ = "market_data"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    high_price: Mapped[float] = mapped_column(Float, nullable=False)
    low_price: Mapped[float] = mapped_column(Float, nullable=False)
    close_price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    technical_indicators: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class NewsSentiment(Base):
    """ニュース・センチメント"""
    __tablename__ = "news_sentiment"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class PerformanceMetrics(Base):
    """パフォーマンス指標"""
    __tablename__ = "performance_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_return: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    win_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    profit_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class SystemLog(Base):
    """システムログ"""
    __tablename__ = "system_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ParameterOptimization(Base):
    """パラメータ最適化履歴"""
    __tablename__ = "parameter_optimization"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_type: Mapped[str] = mapped_column(String(50), nullable=False)
    optimization_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    old_parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    new_parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    performance_improvement: Mapped[float] = mapped_column(Float, nullable=False)
    backtest_results: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
