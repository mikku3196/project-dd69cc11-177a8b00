import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Trade(Base):
    """
    取引履歴を格納するテーブルモデル。
    """
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    sub_bot_name = Column(String, nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    order_id = Column(String, unique=True, nullable=False)
    side = Column(String, nullable=False)  # 'BUY' or 'SELL'
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    entry_reason = Column(String)  # Geminiの分析結果など

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol='{self.symbol}', side='{self.side}', price={self.price})>"


class PortfolioHistory(Base):
    """
    ポートフォリオ全体の資産推移を定期的に記録するテーブルモデル。
    """
    __tablename__ = 'portfolio_history'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    total_balance_usdt = Column(Float, nullable=False)
    sub_bot_A_balance = Column(Float, default=0.0)
    sub_bot_B_balance = Column(Float, default=0.0)
    sub_bot_C_balance = Column(Float, default=0.0)
    profit_saved_balance = Column(Float, default=0.0)

    def __repr__(self):
        return f"<PortfolioHistory(id={self.id}, timestamp='{self.timestamp}', total_balance={self.total_balance_usdt})>"

class SystemEvent(Base):
    """
    システムの重要なイベント（起動、停止、パラメータ更新など）を記録するテーブルモデル。
    """
    __tablename__ = 'system_events'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    level = Column(String, nullable=False) # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    event_type = Column(String, nullable=False, index=True) # 'STARTUP', 'SHUTDOWN', 'REBALANCE', etc.
    message = Column(String, nullable=False)
    details = Column(JSON) # JSON形式で詳細情報を格納

    def __repr__(self):
        return f"<SystemEvent(id={self.id}, level='{self.level}', event_type='{self.event_type}')>"

# ブループリントにはありませんでしたが、センチメントスコアもDBに保存するのが合理的です。
class SentimentScore(Base):
    """
    ニュースセンチメント分析の結果を保存するテーブルモデル。
    """
    __tablename__ = 'sentiment_scores'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    source = Column(String)
    keyword = Column(String, index=True)
    score = Column(Float, nullable=False)
    headline = Column(String)

    def __repr__(self):
        return f"<SentimentScore(id={self.id}, keyword='{self.keyword}', score={self.score})>"
