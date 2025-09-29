"""
自己進化型AIポートフォリオ自動売買システム - 意思決定エンジン
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from ..core.config import config
from ..core.database import db_manager, MarketData, NewsSentiment
from ..api.gemini_client import GeminiClient
from ..api.bybit_client import BybitClient
from ..core.exceptions import GeminiAPIError, TradingError

logger = logging.getLogger(__name__)


class DecisionEngine:
    """意思決定エンジン - Gemini APIを活用した取引判断生成"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.bybit_client = BybitClient()
        self.last_analysis_time: Dict[str, datetime] = {}
        self.analysis_interval = 300  # 5分間隔で分析
    
    async def analyze_and_decide(
        self,
        symbol: str,
        bot_type: str,
        force_analysis: bool = False
    ) -> Optional[Dict[str, Any]]:
        """市場データを分析して取引判断を生成"""
        
        try:
            # 分析間隔チェック
            if not force_analysis:
                last_time = self.last_analysis_time.get(symbol)
                if last_time and datetime.utcnow() - last_time < timedelta(seconds=self.analysis_interval):
                    logger.debug(f"{symbol} の分析をスキップ（間隔制限）")
                    return None
            
            # 市場データを取得
            price_data = await self._get_price_data(symbol)
            technical_indicators = await self._calculate_technical_indicators(symbol)
            sentiment_score = await self._get_sentiment_score(symbol)
            
            # Gemini APIで分析
            decision = await self.gemini_client.analyze_market_data(
                symbol=symbol,
                price_data=price_data,
                technical_indicators=technical_indicators,
                sentiment_score=sentiment_score
            )
            
            # ボットタイプに応じて判断を調整
            adjusted_decision = self._adjust_decision_for_bot_type(decision, bot_type)
            
            # 分析時間を更新
            self.last_analysis_time[symbol] = datetime.utcnow()
            
            logger.info(f"{symbol} の分析完了: {adjusted_decision['action']} (信頼度: {adjusted_decision['confidence']:.2%})")
            
            return adjusted_decision
            
        except GeminiAPIError as e:
            logger.error(f"Gemini API分析エラー ({symbol}): {e}")
            return None
        except Exception as e:
            logger.error(f"意思決定エンジンエラー ({symbol}): {e}")
            return None
    
    async def _get_price_data(self, symbol: str) -> Dict[str, Any]:
        """価格データを取得"""
        try:
            async with self.bybit_client as bybit:
                ticker_data = await bybit.get_ticker(symbol)
                
                if ticker_data and 'list' in ticker_data:
                    ticker = ticker_data['list'][0]
                    return {
                        'last_price': float(ticker.get('lastPrice', 0)),
                        'price_change_24h': float(ticker.get('price24hPcnt', 0)) * 100,
                        'high_24h': float(ticker.get('highPrice', 0)),
                        'low_24h': float(ticker.get('lowPrice', 0)),
                        'volume_24h': float(ticker.get('volume24h', 0)),
                        'bid_price': float(ticker.get('bid1Price', 0)),
                        'ask_price': float(ticker.get('ask1Price', 0))
                    }
                else:
                    raise TradingError(f"ティッカーデータの取得に失敗: {symbol}")
                    
        except Exception as e:
            logger.error(f"価格データ取得エラー ({symbol}): {e}")
            raise TradingError(f"価格データ取得エラー: {e}")
    
    async def _calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """テクニカル指標を計算"""
        try:
            async with self.bybit_client as bybit:
                # K線データを取得（200本）
                kline_data = await bybit.get_kline_data(
                    symbol=symbol,
                    interval='1h',
                    limit=200
                )
                
                if not kline_data or 'list' not in kline_data:
                    raise TradingError(f"K線データの取得に失敗: {symbol}")
                
                # 価格データを抽出
                closes = []
                highs = []
                lows = []
                volumes = []
                
                for kline in reversed(kline_data['list']):  # 時系列順に並び替え
                    closes.append(float(kline[4]))  # close price
                    highs.append(float(kline[2]))    # high price
                    lows.append(float(kline[3]))    # low price
                    volumes.append(float(kline[5]))  # volume
                
                # テクニカル指標を計算
                indicators = self._calculate_indicators(closes, highs, lows, volumes)
                
                return indicators
                
        except Exception as e:
            logger.error(f"テクニカル指標計算エラー ({symbol}): {e}")
            return {}
    
    def _calculate_indicators(
        self,
        closes: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float]
    ) -> Dict[str, Any]:
        """テクニカル指標を計算"""
        try:
            import numpy as np
            
            closes_array = np.array(closes)
            highs_array = np.array(highs)
            lows_array = np.array(lows)
            
            indicators = {}
            
            # RSI (14期間)
            if len(closes) >= 14:
                indicators['rsi'] = self._calculate_rsi(closes_array, 14)
            
            # MACD
            if len(closes) >= 26:
                macd_line, signal_line, histogram = self._calculate_macd(closes_array)
                indicators['macd'] = macd_line
                indicators['macd_signal'] = signal_line
                indicators['macd_histogram'] = histogram
            
            # ボリンジャーバンド (20期間)
            if len(closes) >= 20:
                bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes_array, 20)
                indicators['bb_upper'] = bb_upper
                indicators['bb_middle'] = bb_middle
                indicators['bb_lower'] = bb_lower
            
            # 移動平均線
            if len(closes) >= 20:
                indicators['ma_20'] = np.mean(closes_array[-20:])
            if len(closes) >= 50:
                indicators['ma_50'] = np.mean(closes_array[-50:])
            
            # ATR (14期間)
            if len(closes) >= 14:
                indicators['atr'] = self._calculate_atr(highs_array, lows_array, closes_array, 14)
            
            return indicators
            
        except Exception as e:
            logger.error(f"テクニカル指標計算エラー: {e}")
            return {}
    
    def _calculate_rsi(self, prices: 'np.ndarray', period: int) -> float:
        """RSIを計算"""
        import numpy as np
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = np.mean(gains[-period:])
        avg_losses = np.mean(losses[-period:])
        
        if avg_losses == 0:
            return 100.0
        
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def _calculate_macd(self, prices: 'np.ndarray') -> Tuple[float, float, float]:
        """MACDを計算"""
        import numpy as np
        
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        
        macd_line = ema_12 - ema_26
        
        # シグナルライン（MACDの9期間EMA）
        macd_values = []
        for i in range(len(prices)):
            if i >= 25:  # 26期間目からMACDを計算
                macd_values.append(macd_line)
        
        if len(macd_values) >= 9:
            signal_line = self._calculate_ema(np.array(macd_values), 9)
            histogram = macd_line - signal_line
        else:
            signal_line = macd_line
            histogram = 0
        
        return round(macd_line, 4), round(signal_line, 4), round(histogram, 4)
    
    def _calculate_ema(self, prices: 'np.ndarray', period: int) -> float:
        """指数移動平均を計算"""
        import numpy as np
        
        if len(prices) < period:
            return float(prices[-1])
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return round(ema, 4)
    
    def _calculate_bollinger_bands(self, prices: 'np.ndarray', period: int) -> Tuple[float, float, float]:
        """ボリンジャーバンドを計算"""
        import numpy as np
        
        if len(prices) < period:
            return float(prices[-1]), float(prices[-1]), float(prices[-1])
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (2 * std)
        lower = sma - (2 * std)
        
        return round(upper, 4), round(sma, 4), round(lower, 4)
    
    def _calculate_atr(self, highs: 'np.ndarray', lows: 'np.ndarray', closes: 'np.ndarray', period: int) -> float:
        """ATRを計算"""
        import numpy as np
        
        if len(highs) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        atr = np.mean(true_ranges[-period:])
        return round(atr, 4)
    
    async def _get_sentiment_score(self, symbol: str) -> Optional[float]:
        """センチメントスコアを取得"""
        try:
            async with db_manager.get_session() as session:
                # 直近24時間のセンチメントデータを取得
                from sqlalchemy import select, and_
                from datetime import datetime, timedelta
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                result = await session.execute(
                    select(NewsSentiment.sentiment_score)
                    .where(NewsSentiment.analyzed_at >= cutoff_time)
                    .order_by(NewsSentiment.analyzed_at.desc())
                    .limit(50)
                )
                
                scores = [row[0] for row in result.fetchall()]
                
                if scores:
                    # 移動平均を計算
                    avg_sentiment = sum(scores) / len(scores)
                    return round(avg_sentiment, 3)
                else:
                    return 0.0
                    
        except Exception as e:
            logger.error(f"センチメントスコア取得エラー: {e}")
            return 0.0
    
    def _adjust_decision_for_bot_type(self, decision: Dict[str, Any], bot_type: str) -> Dict[str, Any]:
        """ボットタイプに応じて判断を調整"""
        
        # 信頼度の閾値設定
        confidence_thresholds = {
            'conservative': 0.8,  # 高い信頼度が必要
            'balanced': 0.6,      # 中程度の信頼度
            'aggressive': 0.4     # 低い信頼度でも実行
        }
        
        threshold = confidence_thresholds.get(bot_type, 0.6)
        
        # 信頼度が閾値を下回る場合はHOLDに変更
        if decision['confidence'] < threshold:
            decision['action'] = 'HOLD'
            decision['reason'] = f"信頼度が{bot_type}ボットの閾値({threshold:.1%})を下回るため"
        
        # リスクレベルに応じた調整
        if bot_type == 'conservative' and decision.get('risk_level') == 'HIGH':
            decision['action'] = 'HOLD'
            decision['reason'] = "保守的ボットのため高リスク取引を回避"
        
        return decision
    
    async def get_market_phase(self, symbol: str = "BTCUSDT") -> str:
        """市場フェーズを判定"""
        try:
            # BTCの長期トレンドを分析
            async with self.bybit_client as bybit:
                # 日足データを取得
                daily_data = await bybit.get_kline_data(
                    symbol=symbol,
                    interval='1d',
                    limit=50
                )
                
                if not daily_data or 'list' not in daily_data:
                    return 'range'
                
                # 価格データを抽出
                closes = []
                for kline in reversed(daily_data['list']):
                    closes.append(float(kline[4]))
                
                if len(closes) < 20:
                    return 'range'
                
                # 移動平均線の位置関係を分析
                ma_20 = sum(closes[-20:]) / 20
                ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
                current_price = closes[-1]
                
                # トレンド強度を計算
                price_change_20d = (current_price - closes[-20]) / closes[-20]
                ma_slope = (ma_20 - ma_50) / ma_50
                
                # 市場フェーズを判定
                if price_change_20d > 0.1 and ma_slope > 0.05:
                    return 'strong_bull'
                elif price_change_20d > 0.05 and ma_slope > 0.02:
                    return 'weak_bull'
                elif price_change_20d < -0.1 and ma_slope < -0.05:
                    return 'strong_bear'
                elif price_change_20d < -0.05 and ma_slope < -0.02:
                    return 'weak_bear'
                else:
                    return 'range'
                    
        except Exception as e:
            logger.error(f"市場フェーズ判定エラー: {e}")
            return 'range'
