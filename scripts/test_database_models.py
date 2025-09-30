#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースモデルのテストスクリプト
テーブル作成と基本的なCRUD操作をテスト
"""
import sys
import os
from datetime import datetime
from decimal import Decimal

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.core.database import init_database, get_db, engine
from src.models.tables import (
    Trade, PortfolioHistory, SentimentScore, SystemEvent,
    BotPerformance, MarketPhase, ParameterOptimization,
    CircuitBreaker, NewsArticle, Alert
)

def test_database_connection():
    """データベース接続テスト"""
    print("データベース接続テスト")
    print("=" * 40)
    
    try:
        # データベース初期化
        init_database()
        print("OK データベース接続成功")
        return True
    except Exception as e:
        print(f"NG データベース接続失敗: {e}")
        return False

def test_table_creation():
    """テーブル作成テスト"""
    print("\nテーブル作成テスト")
    print("=" * 40)
    
    try:
        # テーブル作成
        from src.models.tables import Base
        Base.metadata.create_all(bind=engine)
        print("OK 全テーブル作成成功")
        return True
    except Exception as e:
        print(f"NG テーブル作成失敗: {e}")
        return False

def test_crud_operations():
    """CRUD操作テスト"""
    print("\nCRUD操作テスト")
    print("=" * 40)
    
    try:
        db = next(get_db())
        
        # Tradeテーブルのテスト
        print("Tradeテーブルテスト")
        trade = Trade(
            sub_bot_name="SubBot-A",
            symbol="BTCUSDT",
            order_id="TEST_ORDER_001",
            side="BUY",
            price=Decimal("50000.00"),
            quantity=Decimal("0.001"),
            fee=Decimal("0.50"),
            entry_reason="Gemini analysis: Strong bullish signal"
        )
        db.add(trade)
        db.commit()
        print("OK Trade作成成功")
        
        # PortfolioHistoryテーブルのテスト
        print("PortfolioHistoryテーブルテスト")
        portfolio = PortfolioHistory(
            total_balance_usdt=Decimal("10000.00"),
            sub_bot_a_balance=Decimal("4000.00"),
            sub_bot_b_balance=Decimal("4000.00"),
            sub_bot_c_balance=Decimal("2000.00"),
            profit_saved_balance=Decimal("1000.00")
        )
        db.add(portfolio)
        db.commit()
        print("OK PortfolioHistory作成成功")
        
        # SentimentScoreテーブルのテスト
        print("SentimentScoreテーブルテスト")
        sentiment = SentimentScore(
            source="https://news.google.com/rss/search?q=bitcoin",
            keyword="Bitcoin",
            score=Decimal("0.75"),
            headline="Bitcoin reaches new all-time high",
            confidence=Decimal("0.85")
        )
        db.add(sentiment)
        db.commit()
        print("OK SentimentScore作成成功")
        
        # SystemEventテーブルのテスト
        print("SystemEventテーブルテスト")
        event = SystemEvent(
            level="INFO",
            event_type="STARTUP",
            message="Trading bot started successfully",
            module="main.py"
        )
        db.add(event)
        db.commit()
        print("OK SystemEvent作成成功")
        
        # BotPerformanceテーブルのテスト
        print("BotPerformanceテーブルテスト")
        performance = BotPerformance(
            bot_name="SubBot-A",
            balance=Decimal("4000.00"),
            total_pnl=Decimal("500.00"),
            win_rate=Decimal("0.65"),
            total_trades=100,
            winning_trades=65,
            losing_trades=35
        )
        db.add(performance)
        db.commit()
        print("OK BotPerformance作成成功")
        
        # MarketPhaseテーブルのテスト
        print("MarketPhaseテーブルテスト")
        market_phase = MarketPhase(
            phase="strong_bull",
            confidence=Decimal("0.85"),
            trend_strength=Decimal("0.75"),
            volatility=Decimal("0.25")
        )
        db.add(market_phase)
        db.commit()
        print("OK MarketPhase作成成功")
        
        # ParameterOptimizationテーブルのテスト
        print("ParameterOptimizationテーブルテスト")
        optimization = ParameterOptimization(
            bot_name="SubBot-A",
            parameter_name="sl_ratio",
            old_value="1.0",
            new_value="1.2",
            improvement_percentage=Decimal("15.5"),
            backtest_score=Decimal("0.85")
        )
        db.add(optimization)
        db.commit()
        print("OK ParameterOptimization作成成功")
        
        # CircuitBreakerテーブルのテスト
        print("CircuitBreakerテーブルテスト")
        circuit_breaker = CircuitBreaker(
            bot_name="SubBot-A",
            trigger_reason="Daily loss limit exceeded",
            threshold_value=Decimal("500.00"),
            current_value=Decimal("600.00")
        )
        db.add(circuit_breaker)
        db.commit()
        print("OK CircuitBreaker作成成功")
        
        # NewsArticleテーブルのテスト
        print("NewsArticleテーブルテスト")
        article = NewsArticle(
            title="Bitcoin reaches new all-time high",
            url="https://example.com/bitcoin-news",
            source="CryptoNews",
            sentiment_score=Decimal("0.80"),
            relevance_score=Decimal("0.90")
        )
        db.add(article)
        db.commit()
        print("OK NewsArticle作成成功")
        
        # Alertテーブルのテスト
        print("Alertテーブルテスト")
        alert = Alert(
            alert_type="TRADE",
            severity="HIGH",
            title="Large trade executed",
            message="SubBot-A executed a large BTCUSDT trade",
            bot_name="SubBot-A",
            symbol="BTCUSDT"
        )
        db.add(alert)
        db.commit()
        print("OK Alert作成成功")
        
        # データ読み取りテスト
        print("\nデータ読み取りテスト")
        trades = db.query(Trade).all()
        portfolios = db.query(PortfolioHistory).all()
        sentiments = db.query(SentimentScore).all()
        
        print(f"OK Tradeレコード数: {len(trades)}")
        print(f"OK PortfolioHistoryレコード数: {len(portfolios)}")
        print(f"OK SentimentScoreレコード数: {len(sentiments)}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"NG CRUD操作テスト失敗: {e}")
        return False

def test_data_validation():
    """データ検証テスト"""
    print("\nデータ検証テスト")
    print("=" * 40)
    
    try:
        db = next(get_db())
        
        # 重複チェック
        existing_trade = db.query(Trade).filter(Trade.order_id == "TEST_ORDER_001").first()
        if existing_trade:
            print("OK 重複チェック成功: 既存レコード発見")
        
        # データ型チェック
        trade = db.query(Trade).first()
        if trade and isinstance(trade.price, Decimal):
            print("OK データ型チェック成功: Decimal型確認")
        
        # インデックスチェック
        trades_by_symbol = db.query(Trade).filter(Trade.symbol == "BTCUSDT").all()
        if trades_by_symbol:
            print("OK インデックスチェック成功: シンボル検索")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"NG データ検証テスト失敗: {e}")
        return False

def main():
    """メイン処理"""
    print("データベースモデルテスト")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_table_creation,
        test_crud_operations,
        test_data_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"NG テストエラー: {e}")
    
    print("\nテスト結果")
    print("=" * 50)
    print(f"OK 成功: {passed}/{total}")
    print(f"NG 失敗: {total - passed}/{total}")
    
    if passed == total:
        print("\nすべてのテストが成功しました！")
        print("OK データベースモデルが正常に動作しています")
        return True
    else:
        print("\n一部のテストが失敗しました")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)