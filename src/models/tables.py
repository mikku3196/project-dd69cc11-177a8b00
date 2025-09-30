"""
データベースモデル定義
SQLAlchemyを使用してテーブル構造を定義
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class Trade(Base):
    """取引履歴テーブル"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    sub_bot_name = Column(String(50), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    order_id = Column(String(100), unique=True, nullable=False, index=True)
    side = Column(String(10), nullable=False)  # 'BUY' or 'SELL'
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    fee = Column(Numeric(20, 8), default=0)
    pnl = Column(Numeric(20, 8), default=0)
    entry_reason = Column(Text)  # Geminiの分析結果
    exit_reason = Column(Text)   # 決済理由
    status = Column(String(20), default='OPEN')  # 'OPEN', 'CLOSED', 'CANCELLED'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, side={self.side}, price={self.price})>"

class PortfolioHistory(Base):
    """資産履歴テーブル"""
    __tablename__ = 'portfolio_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    total_balance_usdt = Column(Numeric(20, 8), nullable=False)
    sub_bot_a_balance = Column(Numeric(20, 8), default=0)
    sub_bot_b_balance = Column(Numeric(20, 8), default=0)
    sub_bot_c_balance = Column(Numeric(20, 8), default=0)
    profit_saved_balance = Column(Numeric(20, 8), default=0)
    total_pnl = Column(Numeric(20, 8), default=0)
    daily_pnl = Column(Numeric(20, 8), default=0)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<PortfolioHistory(id={self.id}, total_balance={self.total_balance_usdt}, timestamp={self.timestamp})>"

class SentimentScore(Base):
    """センチメントスコアテーブル"""
    __tablename__ = 'sentiment_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    source = Column(String(500), nullable=False)  # ニュースソースURL
    keyword = Column(String(100), nullable=False, index=True)
    score = Column(Numeric(5, 4), nullable=False)  # -1.0 to 1.0
    headline = Column(Text)
    article_url = Column(String(1000))
    confidence = Column(Numeric(5, 4), default=0.5)  # 信頼度
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SentimentScore(id={self.id}, keyword={self.keyword}, score={self.score})>"

class SystemEvent(Base):
    """システムイベントログテーブル"""
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    event_type = Column(String(50), nullable=False, index=True)  # 'STARTUP', 'SHUTDOWN', 'REBALANCE', 'PARAM_UPDATE'
    message = Column(Text, nullable=False)
    details = Column(JSON)  # 追加情報
    module = Column(String(100))  # 発生モジュール
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SystemEvent(id={self.id}, level={self.level}, event_type={self.event_type})>"

class BotPerformance(Base):
    """ボットパフォーマンステーブル"""
    __tablename__ = 'bot_performance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_name = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    balance = Column(Numeric(20, 8), nullable=False)
    total_pnl = Column(Numeric(20, 8), default=0)
    daily_pnl = Column(Numeric(20, 8), default=0)
    win_rate = Column(Numeric(5, 4), default=0)  # 勝率
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    max_drawdown = Column(Numeric(5, 4), default=0)
    sharpe_ratio = Column(Numeric(10, 6), default=0)
    profit_factor = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<BotPerformance(id={self.id}, bot_name={self.bot_name}, balance={self.balance})>"

class MarketPhase(Base):
    """市場フェーズテーブル"""
    __tablename__ = 'market_phases'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    phase = Column(String(20), nullable=False, index=True)  # 'strong_bull', 'weak_bull', 'ranging', 'weak_bear', 'strong_bear'
    confidence = Column(Numeric(5, 4), nullable=False)  # 信頼度
    trend_strength = Column(Numeric(10, 6), default=0)
    volatility = Column(Numeric(10, 6), default=0)
    indicator_value = Column(Numeric(20, 8))  # 指標値
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<MarketPhase(id={self.id}, phase={self.phase}, confidence={self.confidence})>"

class ParameterOptimization(Base):
    """パラメータ最適化履歴テーブル"""
    __tablename__ = 'parameter_optimizations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    bot_name = Column(String(50), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=False)
    old_value = Column(String(100))
    new_value = Column(String(100), nullable=False)
    improvement_percentage = Column(Numeric(10, 6), default=0)
    backtest_score = Column(Numeric(10, 6), default=0)
    optimization_method = Column(String(50), default='grid_search')
    status = Column(String(20), default='SUCCESS')  # 'SUCCESS', 'FAILED', 'SKIPPED'
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<ParameterOptimization(id={self.id}, bot_name={self.bot_name}, parameter={self.parameter_name})>"

class CircuitBreaker(Base):
    """サーキットブレーカーテーブル"""
    __tablename__ = 'circuit_breakers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    bot_name = Column(String(50), nullable=False, index=True)
    trigger_reason = Column(String(200), nullable=False)
    threshold_value = Column(Numeric(20, 8))
    current_value = Column(Numeric(20, 8))
    status = Column(String(20), default='ACTIVE')  # 'ACTIVE', 'RESOLVED', 'MANUAL_RESET'
    duration_minutes = Column(Integer, default=0)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<CircuitBreaker(id={self.id}, bot_name={self.bot_name}, reason={self.trigger_reason})>"

class NewsArticle(Base):
    """ニュース記事テーブル"""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    title = Column(Text, nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(200), nullable=False)
    published_date = Column(DateTime)
    content = Column(Text)
    sentiment_score = Column(Numeric(5, 4))
    keywords = Column(JSON)  # 関連キーワード
    relevance_score = Column(Numeric(5, 4), default=0)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title={self.title[:50]}...)>"

class Alert(Base):
    """アラートテーブル"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # 'TRADE', 'ERROR', 'PERFORMANCE', 'SYSTEM'
    severity = Column(String(20), nullable=False, index=True)  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    bot_name = Column(String(50), index=True)
    symbol = Column(String(20), index=True)
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity})>"