"""
動的ポジションサイジングモジュール
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class VolatilityLevel(Enum):
    """ボラティリティレベル"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class PositionSizeConfig:
    """ポジションサイズ設定"""
    base_lot: float
    volatility_indicator: str  # 'ATR', 'BB', 'VOL'
    indicator_period: int
    volatility_thresholds: Dict[str, float]
    sizing_multipliers: Dict[str, float]
    max_position_size: float
    min_position_size: float

@dataclass
class PositionSizeResult:
    """ポジションサイズ結果"""
    final_size: float
    volatility_level: VolatilityLevel
    volatility_value: float
    multiplier: float
    base_size: float
    reason: str

class DynamicPositionSizer:
    """動的ポジションサイジングクラス"""
    
    def __init__(self, config: PositionSizeConfig):
        self.config = config
        self.price_history: Dict[str, pd.DataFrame] = {}
        
    def update_price_data(self, symbol: str, price_data: pd.DataFrame):
        """価格データ更新"""
        self.price_history[symbol] = price_data.copy()
        
    def calculate_atr(self, symbol: str, period: int = None) -> float:
        """ATR（Average True Range）計算"""
        if symbol not in self.price_history:
            logger.warning(f"No price data for {symbol}")
            return 0.0
        
        period = period or self.config.indicator_period
        df = self.price_history[symbol]
        
        if len(df) < period + 1:
            logger.warning(f"Insufficient data for ATR calculation: {len(df)} < {period + 1}")
            return 0.0
        
        # True Range計算
        df['prev_close'] = df['close'].shift(1)
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['prev_close'])
        df['low_close'] = abs(df['low'] - df['prev_close'])
        
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # ATR計算
        atr = df['true_range'].rolling(window=period).mean().iloc[-1]
        
        return float(atr) if not pd.isna(atr) else 0.0
    
    def calculate_bollinger_bands_width(self, symbol: str, period: int = None) -> float:
        """ボリンジャーバンド幅計算"""
        if symbol not in self.price_history:
            logger.warning(f"No price data for {symbol}")
            return 0.0
        
        period = period or self.config.indicator_period
        df = self.price_history[symbol]
        
        if len(df) < period:
            logger.warning(f"Insufficient data for Bollinger Bands: {len(df)} < {period}")
            return 0.0
        
        # 移動平均と標準偏差計算
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        # ボリンジャーバンド
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        
        # バンド幅（正規化）
        band_width = (upper_band - lower_band) / sma
        
        return float(band_width.iloc[-1]) if not pd.isna(band_width.iloc[-1]) else 0.0
    
    def calculate_volume_volatility(self, symbol: str, period: int = None) -> float:
        """出来高ボラティリティ計算"""
        if symbol not in self.price_history:
            logger.warning(f"No price data for {symbol}")
            return 0.0
        
        period = period or self.config.indicator_period
        df = self.price_history[symbol]
        
        if len(df) < period:
            logger.warning(f"Insufficient data for volume volatility: {len(df)} < {period}")
            return 0.0
        
        # 出来高の移動平均
        volume_sma = df['volume'].rolling(window=period).mean()
        
        # 出来高の変動係数
        volume_cv = df['volume'].rolling(window=period).std() / volume_sma
        
        return float(volume_cv.iloc[-1]) if not pd.isna(volume_cv.iloc[-1]) else 0.0
    
    def determine_volatility_level(self, symbol: str) -> Tuple[VolatilityLevel, float]:
        """ボラティリティレベル判定"""
        volatility_value = 0.0
        
        if self.config.volatility_indicator == 'ATR':
            volatility_value = self.calculate_atr(symbol)
        elif self.config.volatility_indicator == 'BB':
            volatility_value = self.calculate_bollinger_bands_width(symbol)
        elif self.config.volatility_indicator == 'VOL':
            volatility_value = self.calculate_volume_volatility(symbol)
        else:
            logger.error(f"Unknown volatility indicator: {self.config.volatility_indicator}")
            return VolatilityLevel.MEDIUM, 0.0
        
        # 閾値によるレベル判定
        thresholds = self.config.volatility_thresholds
        
        if volatility_value <= thresholds.get('low', 0.0):
            return VolatilityLevel.LOW, volatility_value
        elif volatility_value <= thresholds.get('medium', 0.0):
            return VolatilityLevel.MEDIUM, volatility_value
        else:
            return VolatilityLevel.HIGH, volatility_value
    
    def calculate_position_size(
        self, 
        symbol: str, 
        account_balance: float,
        risk_per_trade: float = 0.02,
        stop_loss_pct: float = 0.05
    ) -> PositionSizeResult:
        """動的ポジションサイズ計算"""
        
        # ボラティリティレベル判定
        volatility_level, volatility_value = self.determine_volatility_level(symbol)
        
        # 基本ポジションサイズ計算
        risk_amount = account_balance * risk_per_trade
        base_size = risk_amount / (self.price_history[symbol]['close'].iloc[-1] * stop_loss_pct)
        
        # ボラティリティに応じた倍率適用
        multiplier = self.config.sizing_multipliers.get(volatility_level.value, 1.0)
        adjusted_size = base_size * multiplier
        
        # サイズ制限適用
        final_size = max(
            self.config.min_position_size,
            min(adjusted_size, self.config.max_position_size)
        )
        
        # 理由生成
        reason = f"Volatility: {volatility_level.value} ({volatility_value:.4f}), Multiplier: {multiplier:.2f}"
        
        result = PositionSizeResult(
            final_size=final_size,
            volatility_level=volatility_level,
            volatility_value=volatility_value,
            multiplier=multiplier,
            base_size=base_size,
            reason=reason
        )
        
        logger.info(f"Position size calculated for {symbol}: {final_size:.6f} ({reason})")
        
        return result
    
    def get_volatility_summary(self, symbol: str) -> Dict[str, Any]:
        """ボラティリティサマリー取得"""
        if symbol not in self.price_history:
            return {"error": f"No data for {symbol}"}
        
        volatility_level, volatility_value = self.determine_volatility_level(symbol)
        
        return {
            'symbol': symbol,
            'volatility_level': volatility_level.value,
            'volatility_value': volatility_value,
            'indicator': self.config.volatility_indicator,
            'period': self.config.indicator_period,
            'thresholds': self.config.volatility_thresholds,
            'multipliers': self.config.sizing_multipliers,
            'data_points': len(self.price_history[symbol])
        }

# テスト用のメイン関数
def test_dynamic_position_sizing():
    """動的ポジションサイジングテスト"""
    print("Dynamic Position Sizing Test")
    print("=" * 50)
    
    # 設定
    config = PositionSizeConfig(
        base_lot=0.001,
        volatility_indicator='ATR',
        indicator_period=14,
        volatility_thresholds={
            'low': 100.0,
            'medium': 300.0
        },
        sizing_multipliers={
            'low': 1.0,
            'medium': 0.75,
            'high': 0.5
        },
        max_position_size=0.01,
        min_position_size=0.0001
    )
    
    # 動的ポジションサイザー初期化
    sizer = DynamicPositionSizer(config)
    
    # モック価格データ生成
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # ボラティリティの異なる3つのシナリオ
    scenarios = [
        {'name': 'Low Volatility', 'volatility': 0.01},
        {'name': 'Medium Volatility', 'volatility': 0.02},
        {'name': 'High Volatility', 'volatility': 0.05}
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        # 価格データ生成
        base_price = 50000.0
        returns = np.random.normal(0, scenario['volatility'], len(dates))
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
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
        sizer.update_price_data('BTCUSDT', df)
        
        # ポジションサイズ計算
        result = sizer.calculate_position_size(
            symbol='BTCUSDT',
            account_balance=10000.0,
            risk_per_trade=0.02,
            stop_loss_pct=0.05
        )
        
        print(f"  Volatility Level: {result.volatility_level.value}")
        print(f"  Volatility Value: {result.volatility_value:.2f}")
        print(f"  Multiplier: {result.multiplier:.2f}")
        print(f"  Base Size: {result.base_size:.6f}")
        print(f"  Final Size: {result.final_size:.6f}")
        print(f"  Reason: {result.reason}")
        
        # ボラティリティサマリー
        summary = sizer.get_volatility_summary('BTCUSDT')
        print(f"  Data Points: {summary['data_points']}")
    
    print("\nDynamic Position Sizing Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        test_dynamic_position_sizing()
    except Exception as e:
        print(f"\nTest failed: {e}")
