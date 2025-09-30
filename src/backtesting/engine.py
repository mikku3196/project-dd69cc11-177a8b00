"""
バックテストエンジン - 過去データでのアルゴリズム検証
"""
import asyncio
import pandas as pd
import numpy as np
import json
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

class BacktestResult:
    """バックテスト結果"""
    def __init__(self):
        self.total_return: float = 0.0
        self.max_drawdown: float = 0.0
        self.sharpe_ratio: float = 0.0
        self.win_rate: float = 0.0
        self.total_trades: int = 0
        self.profitable_trades: int = 0
        self.losing_trades: int = 0
        self.avg_win: float = 0.0
        self.avg_loss: float = 0.0
        self.profit_factor: float = 0.0
        self.volatility: float = 0.0
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []

class MarketDataProvider:
    """市場データプロバイダー"""
    
    def __init__(self):
        self.data_cache: Dict[str, pd.DataFrame] = {}
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str = "1h"
    ) -> pd.DataFrame:
        """ヒストリカルデータ取得"""
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"
        
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # モックデータ生成（実際の実装ではBybit APIから取得）
        data = await self._generate_mock_data(symbol, start_date, end_date, interval)
        
        self.data_cache[cache_key] = data
        return data
    
    async def _generate_mock_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """モックデータ生成"""
        # 時間間隔設定
        if interval == "1h":
            freq = "H"
        elif interval == "4h":
            freq = "4H"
        elif interval == "1d":
            freq = "D"
        else:
            freq = "H"
        
        # 時間範囲生成
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # モック価格データ生成
        np.random.seed(42)  # 再現性のため
        
        # ベース価格（BTC/USDT想定）
        base_price = 50000.0
        
        # ランダムウォーク + トレンド
        returns = np.random.normal(0.0001, 0.02, len(date_range))  # 0.01%平均リターン、2%ボラティリティ
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # OHLCVデータ生成
        data = []
        for i, (timestamp, price) in enumerate(zip(date_range, prices)):
            # 高値・安値・始値・終値
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            
            # 出来高
            volume = np.random.uniform(100, 1000)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df

class TechnicalIndicators:
    """テクニカル指標計算"""
    
    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """単純移動平均"""
        return data.rolling(window=period).mean()
    
    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """指数移動平均"""
        return data.ewm(span=period).mean()
    
    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD"""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """ボリンジャーバンド"""
        sma = TechnicalIndicators.sma(data, period)
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower

class TradingStrategy:
    """取引戦略ベースクラス"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """シグナル生成（サブクラスで実装）"""
        raise NotImplementedError
    
    def calculate_position_size(self, signal: float, current_price: float, account_balance: float) -> float:
        """ポジションサイズ計算"""
        # 基本的なポジションサイジング（リスク管理）
        risk_per_trade = self.params.get('risk_per_trade', 0.02)  # 2%
        stop_loss_pct = self.params.get('stop_loss_pct', 0.05)  # 5%
        
        if signal == 0:
            return 0
        
        # リスクベースのポジションサイズ
        risk_amount = account_balance * risk_per_trade
        position_size = risk_amount / (current_price * stop_loss_pct)
        
        # 最大ポジションサイズ制限
        max_position_pct = self.params.get('max_position_pct', 0.1)  # 10%
        max_position_size = account_balance * max_position_pct / current_price
        
        return min(position_size, max_position_size)

class MovingAverageStrategy(TradingStrategy):
    """移動平均戦略"""
    
    def __init__(self, params: Dict[str, Any]):
        super().__init__("MovingAverage", params)
        self.fast_period = params.get('fast_period', 10)
        self.slow_period = params.get('slow_period', 20)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """シグナル生成"""
        df = data.copy()
        
        # 移動平均計算
        df['sma_fast'] = TechnicalIndicators.sma(df['close'], self.fast_period)
        df['sma_slow'] = TechnicalIndicators.sma(df['close'], self.slow_period)
        
        # シグナル生成
        df['signal'] = 0
        df.loc[df['sma_fast'] > df['sma_slow'], 'signal'] = 1  # 買い
        df.loc[df['sma_fast'] < df['sma_slow'], 'signal'] = -1  # 売り
        
        # ポジション変更のみシグナル
        df['position'] = df['signal'].diff()
        
        return df

class RSIStrategy(TradingStrategy):
    """RSI戦略"""
    
    def __init__(self, params: Dict[str, Any]):
        super().__init__("RSI", params)
        self.rsi_period = params.get('rsi_period', 14)
        self.oversold = params.get('oversold', 30)
        self.overbought = params.get('overbought', 70)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """シグナル生成"""
        df = data.copy()
        
        # RSI計算
        df['rsi'] = TechnicalIndicators.rsi(df['close'], self.rsi_period)
        
        # シグナル生成
        df['signal'] = 0
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1  # 買い
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1  # 売り
        
        # ポジション変更のみシグナル
        df['position'] = df['signal'].diff()
        
        return df

class BacktestEngine:
    """バックテストエンジン"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.data_provider = MarketDataProvider()
    
    async def run_backtest(
        self,
        strategy: TradingStrategy,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1h"
    ) -> BacktestResult:
        """バックテスト実行"""
        logger.info(f"Backtest started: {strategy.name} on {symbol}")
        
        # データ取得
        data = await self.data_provider.get_historical_data(symbol, start_date, end_date, interval)
        
        if data.empty:
            raise ValueError("No data available for backtest")
        
        # シグナル生成
        data_with_signals = strategy.generate_signals(data)
        
        # バックテスト実行
        result = self._execute_backtest(data_with_signals, strategy)
        
        logger.info(f"Backtest completed: Return={result.total_return:.2%}, Trades={result.total_trades}")
        
        return result
    
    def _execute_backtest(self, data: pd.DataFrame, strategy: TradingStrategy) -> BacktestResult:
        """バックテスト実行（内部）"""
        result = BacktestResult()
        result.start_date = data.index[0]
        result.end_date = data.index[-1]
        
        # 初期設定
        balance = self.initial_balance
        position = 0.0
        position_value = 0.0
        equity_curve = [balance]
        trades = []
        
        # バックテスト実行
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close']
            
            # 現在のポジション価値計算
            if position != 0:
                position_value = position * current_price
            
            # 現在の資産価値
            current_equity = balance + position_value
            equity_curve.append(current_equity)
            
            # シグナル処理
            signal = row.get('position', 0)
            
            if signal != 0:
                # ポジションサイズ計算
                position_size = strategy.calculate_position_size(signal, current_price, balance)
                
                if signal > 0:  # 買いシグナル
                    if position < 0:  # ショートポジションクローズ
                        trade_pnl = -position * current_price
                        balance += trade_pnl
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'close_short',
                            'price': current_price,
                            'size': abs(position),
                            'pnl': trade_pnl,
                            'balance': balance
                        })
                        position = 0
                    
                    # ロングポジションオープン
                    if position_size > 0:
                        cost = position_size * current_price
                        if cost <= balance:
                            balance -= cost
                            position = position_size
                            trades.append({
                                'timestamp': timestamp,
                                'type': 'open_long',
                                'price': current_price,
                                'size': position_size,
                                'cost': cost,
                                'balance': balance
                            })
                
                elif signal < 0:  # 売りシグナル
                    if position > 0:  # ロングポジションクローズ
                        trade_pnl = position * current_price
                        balance += trade_pnl
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'close_long',
                            'price': current_price,
                            'size': position,
                            'pnl': trade_pnl,
                            'balance': balance
                        })
                        position = 0
                    
                    # ショートポジションオープン
                    if position_size > 0:
                        proceeds = position_size * current_price
                        balance += proceeds
                        position = -position_size
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'open_short',
                            'price': current_price,
                            'size': position_size,
                            'proceeds': proceeds,
                            'balance': balance
                        })
        
        # 最終ポジションクローズ
        if position != 0:
            final_price = data['close'].iloc[-1]
            if position > 0:  # ロングポジション
                final_pnl = position * final_price
                balance += final_pnl
                trades.append({
                    'timestamp': data.index[-1],
                    'type': 'close_long',
                    'price': final_price,
                    'size': position,
                    'pnl': final_pnl,
                    'balance': balance
                })
            else:  # ショートポジション
                final_pnl = -position * final_price
                balance += final_pnl
                trades.append({
                    'timestamp': data.index[-1],
                    'type': 'close_short',
                    'price': final_price,
                    'size': abs(position),
                    'pnl': final_pnl,
                    'balance': balance
                })
        
        # 結果計算
        result.trades = trades
        result.equity_curve = equity_curve
        result.total_return = (balance - self.initial_balance) / self.initial_balance
        
        # 取引統計
        result.total_trades = len(trades)
        profitable_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        result.profitable_trades = len(profitable_trades)
        result.losing_trades = len(losing_trades)
        result.win_rate = result.profitable_trades / result.total_trades if result.total_trades > 0 else 0
        
        # 平均損益
        if profitable_trades:
            result.avg_win = np.mean([t['pnl'] for t in profitable_trades])
        if losing_trades:
            result.avg_loss = np.mean([t['pnl'] for t in losing_trades])
        
        # プロフィットファクター
        total_profit = sum([t['pnl'] for t in profitable_trades]) if profitable_trades else 0
        total_loss = abs(sum([t['pnl'] for t in losing_trades])) if losing_trades else 0
        result.profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 最大ドローダウン
        equity_array = np.array(equity_curve)
        peak = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - peak) / peak
        result.max_drawdown = np.min(drawdown)
        
        # シャープレシオ
        returns = np.diff(equity_array) / equity_array[:-1]
        result.volatility = np.std(returns)
        result.sharpe_ratio = np.mean(returns) / result.volatility if result.volatility > 0 else 0
        
        return result
    
    async def optimize_parameters(
        self,
        strategy_class,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        param_ranges: Dict[str, List[Any]],
        interval: str = "1h"
    ) -> Dict[str, Any]:
        """パラメータ最適化"""
        logger.info(f"Parameter optimization started for {strategy_class.__name__}")
        
        best_params = None
        best_result = None
        best_score = -float('inf')
        
        # グリッドサーチ
        import itertools
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        for param_combination in itertools.product(*param_values):
            params = dict(zip(param_names, param_combination))
            
            try:
                strategy = strategy_class(params)
                result = await self.run_backtest(strategy, symbol, start_date, end_date, interval)
                
                # スコア計算（シャープレシオ + 勝率）
                score = result.sharpe_ratio + result.win_rate
                
                if score > best_score:
                    best_score = score
                    best_params = params
                    best_result = result
                    
            except Exception as e:
                logger.warning(f"Parameter combination failed: {params}, Error: {e}")
                continue
        
        logger.info(f"Optimization completed. Best score: {best_score:.4f}")
        
        return {
            'best_params': best_params,
            'best_result': best_result,
            'best_score': best_score
        }

# テスト用のメイン関数
async def test_backtest_engine():
    """バックテストエンジンテスト"""
    print("Backtest Engine Test")
    print("=" * 50)
    
    # バックテストエンジン初期化
    engine = BacktestEngine(initial_balance=10000.0)
    
    # テスト期間設定
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()
    
    # 移動平均戦略テスト
    print("Testing Moving Average Strategy...")
    ma_params = {
        'fast_period': 10,
        'slow_period': 20,
        'risk_per_trade': 0.02,
        'stop_loss_pct': 0.05,
        'max_position_pct': 0.1
    }
    
    ma_strategy = MovingAverageStrategy(ma_params)
    ma_result = await engine.run_backtest(ma_strategy, "BTCUSDT", start_date, end_date)
    
    print(f"MA Strategy Results:")
    print(f"  Total Return: {ma_result.total_return:.2%}")
    print(f"  Max Drawdown: {ma_result.max_drawdown:.2%}")
    print(f"  Sharpe Ratio: {ma_result.sharpe_ratio:.4f}")
    print(f"  Win Rate: {ma_result.win_rate:.2%}")
    print(f"  Total Trades: {ma_result.total_trades}")
    
    # RSI戦略テスト
    print("\nTesting RSI Strategy...")
    rsi_params = {
        'rsi_period': 14,
        'oversold': 30,
        'overbought': 70,
        'risk_per_trade': 0.02,
        'stop_loss_pct': 0.05,
        'max_position_pct': 0.1
    }
    
    rsi_strategy = RSIStrategy(rsi_params)
    rsi_result = await engine.run_backtest(rsi_strategy, "BTCUSDT", start_date, end_date)
    
    print(f"RSI Strategy Results:")
    print(f"  Total Return: {rsi_result.total_return:.2%}")
    print(f"  Max Drawdown: {rsi_result.max_drawdown:.2%}")
    print(f"  Sharpe Ratio: {rsi_result.sharpe_ratio:.4f}")
    print(f"  Win Rate: {rsi_result.win_rate:.2%}")
    print(f"  Total Trades: {rsi_result.total_trades}")
    
    # パラメータ最適化テスト
    print("\nTesting Parameter Optimization...")
    param_ranges = {
        'fast_period': [5, 10, 15],
        'slow_period': [20, 30, 40],
        'risk_per_trade': [0.01, 0.02, 0.03]
    }
    
    optimization_result = await engine.optimize_parameters(
        MovingAverageStrategy,
        "BTCUSDT",
        start_date,
        end_date,
        param_ranges
    )
    
    print(f"Optimization Results:")
    print(f"  Best Params: {optimization_result['best_params']}")
    print(f"  Best Score: {optimization_result['best_score']:.4f}")
    
    print("\nBacktest Engine Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_backtest_engine())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
