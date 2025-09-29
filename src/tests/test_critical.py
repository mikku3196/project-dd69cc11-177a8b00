"""
自己進化型AIポートフォリオ自動売買システム - テストケース
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

from src.api.bybit_client import BybitClient
from src.api.gemini_client import GeminiClient
from src.utils.circuit_breaker import CircuitBreaker, circuit_breaker
from src.utils.api_client import KeyRing, RateLimitHandler


class TestOrderFlow:
    """注文フロー・正常系テスト"""
    
    @pytest.mark.asyncio
    async def test_successful_order_flow(self):
        """正常な注文フローのテスト"""
        
        # モックレスポンス
        mock_ticker_response = {
            "result": {
                "list": [{
                    "symbol": "BTCUSDT",
                    "lastPrice": "50000.00",
                    "price24hPcnt": "0.05",
                    "highPrice": "51000.00",
                    "lowPrice": "49000.00",
                    "volume24h": "1000000"
                }]
            }
        }
        
        mock_order_response = {
            "result": {
                "orderId": "test_order_123",
                "orderLinkId": "test_link_123"
            }
        }
        
        # BybitClientをモック
        with patch('src.api.bybit_client.BybitClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # セッションコンテキストマネージャーをモック
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            # APIレスポンスをモック
            mock_client.get_ticker.return_value = mock_ticker_response
            mock_client.place_order.return_value = mock_order_response
            
            # テスト実行
            async with BybitClient() as client:
                # ティッカー取得
                ticker = await client.get_ticker("BTCUSDT")
                assert ticker["result"]["list"][0]["symbol"] == "BTCUSDT"
                
                # 注文発注
                order = await client.place_order(
                    symbol="BTCUSDT",
                    side="Buy",
                    order_type="Market",
                    qty="0.001"
                )
                assert order["result"]["orderId"] == "test_order_123"
    
    @pytest.mark.asyncio
    async def test_order_with_circuit_breaker(self):
        """サーキットブレーカー保護下での注文テスト"""
        
        # サーキットブレーカーをリセット
        circuit_breaker.reset()
        
        # 正常時は実行可能
        assert not circuit_breaker.is_open()
        
        # 連続失敗でサーキットをオープン
        for _ in range(10):
            circuit_breaker.record_failure(Exception("Test failure"))
        
        assert circuit_breaker.is_open()
        
        # オープン時は実行不可
        with pytest.raises(RuntimeError, match="Circuit breaker open"):
            if circuit_breaker.is_open():
                raise RuntimeError("Circuit breaker open - abort order")


class TestRateLimitHandling:
    """レート制限処理テスト"""
    
    @pytest.mark.asyncio
    async def test_429_response_handling(self):
        """429レスポンス処理のテスト"""
        
        # キーリングを作成
        keys = ["key1", "key2", "key3"]
        key_ring = KeyRing(keys)
        
        # レート制限ハンドラー
        rate_handler = RateLimitHandler()
        
        # 429レスポンスをシミュレート
        response_headers = {"Retry-After": "60"}
        
        # 最初のキーを取得
        current_key = key_ring.get_next_key()
        assert current_key == "key1"
        
        # 429エラーを処理
        handled = await rate_handler.handle_rate_limit(
            key_ring, current_key, 429, response_headers
        )
        
        assert handled is True
        assert "key1" in key_ring.blacklist
        
        # 次のキーを取得
        next_key = key_ring.get_next_key()
        assert next_key == "key2"
    
    @pytest.mark.asyncio
    async def test_key_rotation(self):
        """キーローテーションテスト"""
        
        keys = ["key1", "key2", "key3"]
        key_ring = KeyRing(keys)
        
        # ラウンドロビンでキーを取得
        key1 = key_ring.get_next_key()
        key2 = key_ring.get_next_key()
        key3 = key_ring.get_next_key()
        key4 = key_ring.get_next_key()
        
        assert key1 == "key1"
        assert key2 == "key2"
        assert key3 == "key3"
        assert key4 == "key1"  # ラウンドロビン
        
        # キーをブラックリストに追加
        key_ring.blacklist_key("key1", 60)
        
        # ブラックリストされたキーは除外される
        available_keys = [key_ring.get_next_key() for _ in range(5)]
        assert "key1" not in available_keys


class TestCircuitBreaker:
    """サーキットブレーカーテスト"""
    
    def test_circuit_breaker_states(self):
        """サーキットブレーカーの状態遷移テスト"""
        
        cb = CircuitBreaker(fail_threshold=3, window=60, open_for=5)
        
        # 初期状態はCLOSED
        assert cb.state == "CLOSED"
        assert not cb.is_open()
        
        # 失敗を記録
        cb.record_failure(Exception("Test error"))
        cb.record_failure(Exception("Test error"))
        cb.record_failure(Exception("Test error"))
        
        # 閾値を超えてOPEN状態に
        assert cb.state == "OPEN"
        assert cb.is_open()
        
        # 成功を記録してもOPEN状態は維持
        cb.record_success()
        assert cb.state == "OPEN"
    
    def test_circuit_breaker_half_open(self):
        """ハーフオープン状態のテスト"""
        
        cb = CircuitBreaker(fail_threshold=2, window=60, open_for=1)
        
        # 失敗でOPEN状態に
        cb.record_failure(Exception("Test error"))
        cb.record_failure(Exception("Test error"))
        assert cb.state == "OPEN"
        
        # 時間を進めてHALF_OPEN状態に
        cb.open_until = 0  # 強制的に期限切れ
        assert not cb.is_open()
        assert cb.state == "HALF_OPEN"
        
        # HALF_OPEN状態で成功するとCLOSEDに
        cb.record_success()
        assert cb.state == "CLOSED"
    
    def test_circuit_breaker_reset(self):
        """サーキットブレーカーのリセットテスト"""
        
        cb = CircuitBreaker()
        
        # 失敗を記録してOPEN状態に
        for _ in range(10):
            cb.record_failure(Exception("Test error"))
        
        assert cb.state == "OPEN"
        
        # リセット
        cb.reset()
        
        assert cb.state == "CLOSED"
        assert len(cb.fail_times) == 0
        assert cb.open_until == 0


class TestGeminiIntegration:
    """Gemini API統合テスト"""
    
    @pytest.mark.asyncio
    async def test_gemini_market_analysis(self):
        """Gemini市場分析のテスト"""
        
        # モックレスポンス
        mock_response = {
            "action": "BUY",
            "confidence": 0.85,
            "reason": "テクニカル分析とセンチメントが良好",
            "risk_level": "MEDIUM",
            "expected_price_target": "52000",
            "stop_loss_price": "48000",
            "position_size_recommendation": "MEDIUM"
        }
        
        with patch('src.api.gemini_client.genai') as mock_genai:
            # Gemini APIをモック
            mock_model = AsyncMock()
            mock_model.generate_content.return_value = AsyncMock(
                text=json.dumps(mock_response)
            )
            mock_genai.GenerativeModel.return_value = mock_model
            
            # テスト実行
            gemini = GeminiClient()
            
            price_data = {
                "last_price": 50000,
                "price_change_24h": 5.0,
                "high_24h": 51000,
                "low_24h": 49000,
                "volume_24h": 1000000
            }
            
            technical_indicators = {
                "rsi": 65,
                "macd": 100,
                "macd_signal": 95,
                "bb_upper": 52000,
                "bb_lower": 48000
            }
            
            result = await gemini.analyze_market_data(
                symbol="BTCUSDT",
                price_data=price_data,
                technical_indicators=technical_indicators,
                sentiment_score=0.3
            )
            
            assert result["action"] == "BUY"
            assert result["confidence"] == 0.85
            assert result["risk_level"] == "MEDIUM"


# テスト実行用の設定
@pytest.fixture
def event_loop():
    """イベントループのフィクスチャ"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
