"""
市場フェーズ適応型ポートフォリオモジュール
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class MarketPhase(Enum):
    """市場フェーズ"""
    STRONG_BULL = "strong_bull"      # 強い上昇トレンド
    WEAK_BULL = "weak_bull"          # 弱い上昇トレンド
    RANGING = "ranging"              # レンジ相場
    WEAK_BEAR = "weak_bear"          # 弱い下降トレンド
    STRONG_BEAR = "strong_bear"      # 強い下降トレンド

@dataclass
class MarketPhaseConfig:
    """市場フェーズ設定"""
    indicator: str  # 'EMA_Cross', 'ADX', 'RSI'
    short_period: int
    long_period: int
    thresholds: Dict[str, float]
    allocations: Dict[str, Dict[str, float]]  # フェーズ別資金配分

@dataclass
class MarketPhaseResult:
    """市場フェーズ分析結果"""
    phase: MarketPhase
    confidence: float
    indicator_value: float
    trend_strength: float
    volatility: float
    analysis: str

@dataclass
class PortfolioAllocation:
    """ポートフォリオ配分"""
    sub_bot_a: float  # 安定志向
    sub_bot_b: float  # バランス重視
    sub_bot_c: float  # 積極果敢
    total: float

class MarketPhaseAnalyzer:
    """市場フェーズ分析クラス"""
    
    def __init__(self, config: MarketPhaseConfig):
        self.config = config
        self.price_history: Dict[str, pd.DataFrame] = {}
        
    def update_price_data(self, symbol: str, price_data: pd.DataFrame):
        """価格データ更新"""
        self.price_history[symbol] = price_data.copy()
        
    def calculate_ema_cross(self, symbol: str) -> Tuple[float, float, float]:
        """EMAクロス分析"""
        if symbol not in self.price_history:
            return 0.0, 0.0, 0.0
        
        df = self.price_history[symbol]
        
        if len(df) < self.config.long_period:
            return 0.0, 0.0, 0.0
        
        # EMA計算
        ema_short = df['close'].ewm(span=self.config.short_period).mean()
        ema_long = df['close'].ewm(span=self.config.long_period).mean()
        
        # 現在の値
        current_short = ema_short.iloc[-1]
        current_long = ema_long.iloc[-1]
        
        # 前の値
        prev_short = ema_short.iloc[-2]
        prev_long = ema_long.iloc[-2]
        
        # クロス判定
        current_cross = current_short - current_long
        prev_cross = prev_short - prev_long
        
        # トレンド強度
        trend_strength = abs(current_cross) / current_long if current_long > 0 else 0.0
        
        return current_cross, prev_cross, trend_strength
    
    def calculate_adx(self, symbol: str, period: int = 14) -> Tuple[float, float, float]:
        """ADX（Average Directional Index）計算"""
        if symbol not in self.price_history:
            return 0.0, 0.0, 0.0
        
        df = self.price_history[symbol]
        
        if len(df) < period + 1:
            return 0.0, 0.0, 0.0
        
        # True Range計算
        df['prev_close'] = df['close'].shift(1)
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['prev_close'])
        df['low_close'] = abs(df['low'] - df['prev_close'])
        
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # Directional Movement計算
        df['high_diff'] = df['high'].diff()
        df['low_diff'] = df['low'].diff()
        
        df['plus_dm'] = np.where(
            (df['high_diff'] > df['low_diff']) & (df['high_diff'] > 0),
            df['high_diff'], 0
        )
        df['minus_dm'] = np.where(
            (df['low_diff'] > df['high_diff']) & (df['low_diff'] > 0),
            df['low_diff'], 0
        )
        
        # 平滑化
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / 
                               df['true_range'].rolling(window=period).mean())
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / 
                                df['true_range'].rolling(window=period).mean())
        
        # ADX計算
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(window=period).mean()
        
        # 現在の値
        current_adx = df['adx'].iloc[-1]
        current_plus_di = df['plus_di'].iloc[-1]
        current_minus_di = df['minus_di'].iloc[-1]
        
        return current_adx, current_plus_di, current_minus_di
    
    def calculate_rsi(self, symbol: str, period: int = 14) -> float:
        """RSI（Relative Strength Index）計算"""
        if symbol not in self.price_history:
            return 50.0
        
        df = self.price_history[symbol]
        
        if len(df) < period + 1:
            return 50.0
        
        # 価格変化
        df['price_change'] = df['close'].diff()
        
        # 利益と損失
        df['gain'] = np.where(df['price_change'] > 0, df['price_change'], 0)
        df['loss'] = np.where(df['price_change'] < 0, -df['price_change'], 0)
        
        # 平均利益と平均損失
        avg_gain = df['gain'].rolling(window=period).mean()
        avg_loss = df['loss'].rolling(window=period).mean()
        
        # RSI計算
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def analyze_market_phase(self, symbol: str) -> MarketPhaseResult:
        """市場フェーズ分析"""
        
        if self.config.indicator == 'EMA_Cross':
            cross_diff, prev_cross, trend_strength = self.calculate_ema_cross(symbol)
            
            if cross_diff > 0 and prev_cross <= 0:
                # ゴールデンクロス（上昇トレンド開始）
                if trend_strength > self.config.thresholds.get('strong_trend', 0.05):
                    phase = MarketPhase.STRONG_BULL
                    confidence = min(trend_strength * 2, 1.0)
                else:
                    phase = MarketPhase.WEAK_BULL
                    confidence = trend_strength
            elif cross_diff < 0 and prev_cross >= 0:
                # デッドクロス（下降トレンド開始）
                if trend_strength > self.config.thresholds.get('strong_trend', 0.05):
                    phase = MarketPhase.STRONG_BEAR
                    confidence = min(trend_strength * 2, 1.0)
                else:
                    phase = MarketPhase.WEAK_BEAR
                    confidence = trend_strength
            else:
                # レンジ相場
                phase = MarketPhase.RANGING
                confidence = 1.0 - trend_strength
            
            analysis = f"EMA Cross: {cross_diff:.4f}, Trend Strength: {trend_strength:.3f}"
            
        elif self.config.indicator == 'ADX':
            adx, plus_di, minus_di = self.calculate_adx(symbol)
            
            if adx > self.config.thresholds.get('strong_trend', 25):
                if plus_di > minus_di:
                    phase = MarketPhase.STRONG_BULL if adx > 40 else MarketPhase.WEAK_BULL
                else:
                    phase = MarketPhase.STRONG_BEAR if adx > 40 else MarketPhase.WEAK_BEAR
                confidence = min(adx / 50, 1.0)
            else:
                phase = MarketPhase.RANGING
                confidence = 1.0 - (adx / 50)
            
            analysis = f"ADX: {adx:.2f}, +DI: {plus_di:.2f}, -DI: {minus_di:.2f}"
            
        elif self.config.indicator == 'RSI':
            rsi = self.calculate_rsi(symbol)
            
            if rsi > 70:
                phase = MarketPhase.STRONG_BULL
                confidence = (rsi - 70) / 30
            elif rsi > 55:
                phase = MarketPhase.WEAK_BULL
                confidence = (rsi - 55) / 15
            elif rsi < 30:
                phase = MarketPhase.STRONG_BEAR
                confidence = (30 - rsi) / 30
            elif rsi < 45:
                phase = MarketPhase.WEAK_BEAR
                confidence = (45 - rsi) / 15
            else:
                phase = MarketPhase.RANGING
                confidence = 1.0 - abs(rsi - 50) / 50
            
            analysis = f"RSI: {rsi:.2f}"
            
        else:
            # デフォルト：レンジ相場
            phase = MarketPhase.RANGING
            confidence = 0.5
            analysis = "Unknown indicator"
        
        # ボラティリティ計算
        if symbol in self.price_history:
            df = self.price_history[symbol]
            if len(df) >= 20:
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # 年率換算
            else:
                volatility = 0.0
        else:
            volatility = 0.0
        
        result = MarketPhaseResult(
            phase=phase,
            confidence=confidence,
            indicator_value=cross_diff if self.config.indicator == 'EMA_Cross' else adx if self.config.indicator == 'ADX' else rsi,
            trend_strength=trend_strength if self.config.indicator == 'EMA_Cross' else adx if self.config.indicator == 'ADX' else abs(rsi - 50),
            volatility=volatility,
            analysis=analysis
        )
        
        logger.info(f"Market phase analysis for {symbol}: {phase.value} (confidence: {confidence:.2f})")
        
        return result
    
    def get_portfolio_allocation(self, market_phase: MarketPhase) -> PortfolioAllocation:
        """市場フェーズに応じたポートフォリオ配分取得"""
        
        phase_key = market_phase.value
        allocations = self.config.allocations.get(phase_key, {
            'sub_bot_a': 0.4,
            'sub_bot_b': 0.4,
            'sub_bot_c': 0.2
        })
        
        allocation = PortfolioAllocation(
            sub_bot_a=allocations.get('sub_bot_a', 0.4),
            sub_bot_b=allocations.get('sub_bot_b', 0.4),
            sub_bot_c=allocations.get('sub_bot_c', 0.2),
            total=1.0
        )
        
        logger.info(f"Portfolio allocation for {phase_key}: A={allocation.sub_bot_a:.1%}, "
                   f"B={allocation.sub_bot_b:.1%}, C={allocation.sub_bot_c:.1%}")
        
        return allocation
    
    def get_market_summary(self, symbol: str) -> Dict[str, Any]:
        """市場サマリー取得"""
        if symbol not in self.price_history:
            return {"error": f"No data for {symbol}"}
        
        result = self.analyze_market_phase(symbol)
        allocation = self.get_portfolio_allocation(result.phase)
        
        return {
            'symbol': symbol,
            'market_phase': result.phase.value,
            'confidence': result.confidence,
            'indicator_value': result.indicator_value,
            'trend_strength': result.trend_strength,
            'volatility': result.volatility,
            'analysis': result.analysis,
            'allocation': {
                'sub_bot_a': allocation.sub_bot_a,
                'sub_bot_b': allocation.sub_bot_b,
                'sub_bot_c': allocation.sub_bot_c
            },
            'data_points': len(self.price_history[symbol])
        }

# テスト用のメイン関数
def test_market_phase_analyzer():
    """市場フェーズ分析テスト"""
    print("Market Phase Analyzer Test")
    print("=" * 50)
    
    # 設定
    config = MarketPhaseConfig(
        indicator='EMA_Cross',
        short_period=50,
        long_period=200,
        thresholds={
            'strong_trend': 0.05
        },
        allocations={
            'strong_bull': {'sub_bot_a': 0.2, 'sub_bot_b': 0.3, 'sub_bot_c': 0.5},
            'weak_bull': {'sub_bot_a': 0.3, 'sub_bot_b': 0.4, 'sub_bot_c': 0.3},
            'ranging': {'sub_bot_a': 0.5, 'sub_bot_b': 0.3, 'sub_bot_c': 0.2},
            'weak_bear': {'sub_bot_a': 0.3, 'sub_bot_b': 0.4, 'sub_bot_c': 0.3},
            'strong_bear': {'sub_bot_a': 0.2, 'sub_bot_b': 0.3, 'sub_bot_c': 0.5}
        }
    )
    
    # 市場フェーズ分析器初期化
    analyzer = MarketPhaseAnalyzer(config)
    
    # モック価格データ生成
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=300, freq='1h')
    
    # 3つの異なる市場シナリオ
    scenarios = [
        {'name': 'Bull Market', 'trend': 0.001, 'volatility': 0.02},
        {'name': 'Bear Market', 'trend': -0.001, 'volatility': 0.03},
        {'name': 'Ranging Market', 'trend': 0.0001, 'volatility': 0.015}
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        # 価格データ生成
        base_price = 50000.0
        prices = [base_price]
        
        for i in range(1, len(dates)):
            # トレンド + ランダム変動
            trend_component = scenario['trend']
            random_component = np.random.normal(0, scenario['volatility'])
            price_change = trend_component + random_component
            
            new_price = prices[-1] * (1 + price_change)
            prices.append(new_price)
        
        # OHLCVデータ作成
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price * (1 + abs(np.random.normal(0, 0.005)))
            low = price * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': date,
                'open': prices[i-1] if i > 0 else price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # 価格データ更新
        analyzer.update_price_data('BTCUSDT', df)
        
        # 市場フェーズ分析
        result = analyzer.analyze_market_phase('BTCUSDT')
        
        print(f"  Market Phase: {result.phase.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Trend Strength: {result.trend_strength:.3f}")
        print(f"  Volatility: {result.volatility:.2%}")
        print(f"  Analysis: {result.analysis}")
        
        # ポートフォリオ配分
        allocation = analyzer.get_portfolio_allocation(result.phase)
        print(f"  Allocation: A={allocation.sub_bot_a:.1%}, B={allocation.sub_bot_b:.1%}, C={allocation.sub_bot_c:.1%}")
        
        # サマリー
        summary = analyzer.get_market_summary('BTCUSDT')
        print(f"  Data Points: {summary['data_points']}")
    
    print("\nMarket Phase Analyzer Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        test_market_phase_analyzer()
    except Exception as e:
        print(f"\nTest failed: {e}")
