"""
自己進化型AIポートフォリオ自動売買システム - サブボット基底クラス
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from ..core.config import config
from ..core.database import db_manager, Account, Trade
from ..api.bybit_client import BybitClient
from ..api.discord_client import DiscordClient
from ..analysis.decision_engine import DecisionEngine
from ..core.exceptions import TradingError, InsufficientFundsError, PositionSizeError

logger = logging.getLogger(__name__)


class SubBot(ABC):
    """サブボット基底クラス"""
    
    def __init__(self, bot_type: str, account_id: int):
        self.bot_type = bot_type
        self.account_id = account_id
        self.is_active = True
        self.is_trading_enabled = True
        
        # 設定を取得
        self.config = config.get_sub_bot_config(bot_type)
        self.position_sizing_config = config.get_position_sizing_config()
        
        # クライアント
        self.bybit_client = BybitClient()
        self.discord_client = DiscordClient()
        self.decision_engine = DecisionEngine()
        
        # 状態管理
        self.current_positions: Dict[str, Dict[str, Any]] = {}
        self.pending_orders: List[Dict[str, Any]] = []
        self.last_trade_time: Optional[datetime] = None
        self.daily_trade_count = 0
        self.daily_pnl = 0.0
        
        # パフォーマンス追跡
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
    
    async def initialize(self) -> None:
        """ボットを初期化"""
        try:
            # アカウント情報を取得
            await self._load_account_info()
            
            # 現在のポジションを取得
            await self._load_current_positions()
            
            logger.info(f"{self.bot_type}ボットを初期化しました (アカウントID: {self.account_id})")
            
        except Exception as e:
            logger.error(f"{self.bot_type}ボットの初期化に失敗しました: {e}")
            raise
    
    async def _load_account_info(self) -> None:
        """アカウント情報を読み込み"""
        try:
            async with db_manager.get_session() as session:
                from sqlalchemy import select
                
                result = await session.execute(
                    select(Account).where(Account.id == self.account_id)
                )
                account = result.scalar_one_or_none()
                
                if not account:
                    raise TradingError(f"アカウントが見つかりません: {self.account_id}")
                
                self.account_name = account.name
                self.balance = account.balance
                self.allocated_balance = account.allocated_balance
                self.peak_balance = self.balance
                
        except Exception as e:
            logger.error(f"アカウント情報の読み込みに失敗しました: {e}")
            raise
    
    async def _load_current_positions(self) -> None:
        """現在のポジションを読み込み"""
        try:
            async with self.bybit_client as bybit:
                positions_data = await bybit.get_positions()
                
                if positions_data and 'list' in positions_data:
                    for position in positions_data['list']:
                        symbol = position.get('symbol')
                        if symbol and float(position.get('size', 0)) > 0:
                            self.current_positions[symbol] = {
                                'size': float(position.get('size', 0)),
                                'side': position.get('side'),
                                'entry_price': float(position.get('avgPrice', 0)),
                                'unrealized_pnl': float(position.get('unrealisedPnl', 0)),
                                'leverage': float(position.get('leverage', 1))
                            }
                
        except Exception as e:
            logger.error(f"ポジション情報の読み込みに失敗しました: {e}")
    
    async def execute_trading_cycle(self, symbols: List[str]) -> None:
        """取引サイクルを実行"""
        if not self.is_active or not self.is_trading_enabled:
            return
        
        try:
            for symbol in symbols:
                await self._analyze_and_trade(symbol)
                await asyncio.sleep(1)  # API制限対策
                
        except Exception as e:
            logger.error(f"{self.bot_type}ボットの取引サイクルでエラー: {e}")
            await self.discord_client.send_error_notification(
                error_type="Trading Cycle Error",
                error_message=str(e),
                module=f"{self.bot_type}_bot"
            )
    
    async def _analyze_and_trade(self, symbol: str) -> None:
        """シンボルを分析して取引を実行"""
        try:
            # 意思決定エンジンで分析
            decision = await self.decision_engine.analyze_and_decide(
                symbol=symbol,
                bot_type=self.bot_type
            )
            
            if not decision or decision['action'] == 'HOLD':
                return
            
            # リスクチェック
            if not await self._check_risk_limits(symbol, decision):
                return
            
            # 取引を実行
            await self._execute_trade(symbol, decision)
            
        except Exception as e:
            logger.error(f"{symbol}の分析・取引でエラー: {e}")
    
    async def _check_risk_limits(self, symbol: str, decision: Dict[str, Any]) -> bool:
        """リスク制限をチェック"""
        try:
            # 日次取引制限
            if self.daily_trade_count >= self.config.get('max_daily_trades', 10):
                logger.warning(f"日次取引制限に達しました: {symbol}")
                return False
            
            # 最大ポジション数制限
            max_positions = self.config.get('max_positions', 5)
            if len(self.current_positions) >= max_positions:
                logger.warning(f"最大ポジション数に達しました: {symbol}")
                return False
            
            # 資金制限
            risk_per_trade = config.trading.risk_per_trade
            max_position_value = self.balance * risk_per_trade
            
            if decision.get('position_size_recommendation') == 'LARGE':
                position_value = max_position_value
            elif decision.get('position_size_recommendation') == 'MEDIUM':
                position_value = max_position_value * 0.7
            else:  # SMALL
                position_value = max_position_value * 0.4
            
            if position_value > self.balance * 0.1:  # 総資産の10%制限
                logger.warning(f"ポジションサイズが制限を超えています: {symbol}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"リスク制限チェックでエラー: {e}")
            return False
    
    async def _execute_trade(self, symbol: str, decision: Dict[str, Any]) -> None:
        """取引を実行"""
        try:
            action = decision['action']
            confidence = decision['confidence']
            
            # ポジションサイズを計算
            position_size = await self._calculate_position_size(symbol, decision)
            
            if position_size <= 0:
                logger.warning(f"ポジションサイズが0以下です: {symbol}")
                return
            
            # 注文を発注
            async with self.bybit_client as bybit:
                if action == 'BUY':
                    order_result = await bybit.place_order(
                        symbol=symbol,
                        side='Buy',
                        order_type='Market',
                        qty=str(position_size),
                        stop_loss=decision.get('stop_loss_price'),
                        take_profit=decision.get('expected_price_target')
                    )
                elif action == 'SELL':
                    order_result = await bybit.place_order(
                        symbol=symbol,
                        side='Sell',
                        order_type='Market',
                        qty=str(position_size),
                        stop_loss=decision.get('stop_loss_price'),
                        take_profit=decision.get('expected_price_target')
                    )
                else:
                    return
                
                # 取引をデータベースに記録
                await self._record_trade(symbol, action, position_size, decision, order_result)
                
                # Discord通知
                await self.discord_client.send_trade_notification(
                    symbol=symbol,
                    action=action,
                    quantity=position_size,
                    price=float(decision.get('expected_price_target', 0)),
                    bot_name=f"{self.bot_type}ボット",
                    confidence=confidence,
                    reason=decision.get('reason')
                )
                
                # 状態を更新
                self.last_trade_time = datetime.utcnow()
                self.daily_trade_count += 1
                self.total_trades += 1
                
                logger.info(f"取引を実行しました: {symbol} {action} {position_size}")
                
        except Exception as e:
            logger.error(f"取引実行でエラー: {e}")
            raise TradingError(f"取引実行エラー: {e}")
    
    async def _calculate_position_size(self, symbol: str, decision: Dict[str, Any]) -> float:
        """ポジションサイズを計算"""
        try:
            # 基本リスク金額
            base_risk = self.balance * config.trading.risk_per_trade
            
            # ボットタイプに応じた調整
            risk_multiplier = {
                'conservative': 0.5,
                'balanced': 1.0,
                'aggressive': 1.5
            }.get(self.bot_type, 1.0)
            
            adjusted_risk = base_risk * risk_multiplier
            
            # 信頼度に応じた調整
            confidence_multiplier = decision['confidence']
            
            # ポジションサイズ推奨に応じた調整
            size_multiplier = {
                'SMALL': 0.5,
                'MEDIUM': 1.0,
                'LARGE': 1.5
            }.get(decision.get('position_size_recommendation', 'MEDIUM'), 1.0)
            
            # 最終的なポジションサイズ
            position_value = adjusted_risk * confidence_multiplier * size_multiplier
            
            # 現在価格で数量に変換
            current_price = await self._get_current_price(symbol)
            position_size = position_value / current_price
            
            # 最小・最大制限
            min_size = 0.001
            max_size = self.balance * config.trading.max_position_size / current_price
            
            position_size = max(min_size, min(position_size, max_size))
            
            return round(position_size, 6)
            
        except Exception as e:
            logger.error(f"ポジションサイズ計算でエラー: {e}")
            return 0.0
    
    async def _get_current_price(self, symbol: str) -> float:
        """現在価格を取得"""
        try:
            async with self.bybit_client as bybit:
                ticker_data = await bybit.get_ticker(symbol)
                if ticker_data and 'list' in ticker_data:
                    return float(ticker_data['list'][0].get('lastPrice', 0))
                return 0.0
        except Exception as e:
            logger.error(f"現在価格取得でエラー: {e}")
            return 0.0
    
    async def _record_trade(
        self,
        symbol: str,
        action: str,
        quantity: float,
        decision: Dict[str, Any],
        order_result: Dict[str, Any]
    ) -> None:
        """取引をデータベースに記録"""
        try:
            async with db_manager.get_session() as session:
                trade = Trade(
                    account_id=self.account_id,
                    symbol=symbol,
                    side=action,
                    quantity=quantity,
                    price=float(decision.get('expected_price_target', 0)),
                    fee=0.0,  # 後で計算
                    strategy=self.bot_type,
                    confidence=decision.get('confidence'),
                    reason=decision.get('reason')
                )
                
                session.add(trade)
                await session.commit()
                
        except Exception as e:
            logger.error(f"取引記録でエラー: {e}")
    
    async def update_performance_metrics(self) -> None:
        """パフォーマンス指標を更新"""
        try:
            # 現在の残高を取得
            await self._load_account_info()
            
            # ドローダウンを計算
            if self.balance > self.peak_balance:
                self.peak_balance = self.balance
            
            current_drawdown = (self.peak_balance - self.balance) / self.peak_balance
            self.max_drawdown = max(self.max_drawdown, current_drawdown)
            
            # 日次リセット
            if self.last_trade_time and datetime.utcnow().date() > self.last_trade_time.date():
                self.daily_trade_count = 0
                self.daily_pnl = 0.0
            
            logger.debug(f"{self.bot_type}ボット パフォーマンス更新: 残高={self.balance:.2f}, ドローダウン={self.max_drawdown:.2%}")
            
        except Exception as e:
            logger.error(f"パフォーマンス指標更新でエラー: {e}")
    
    async def emergency_stop(self) -> None:
        """緊急停止"""
        try:
            self.is_trading_enabled = False
            
            # 全ポジションをクローズ
            async with self.bybit_client as bybit:
                for symbol, position in self.current_positions.items():
                    if position['size'] > 0:
                        await bybit.place_order(
                            symbol=symbol,
                            side='Sell' if position['side'] == 'Buy' else 'Buy',
                            order_type='Market',
                            qty=str(position['size'])
                        )
            
            logger.warning(f"{self.bot_type}ボットを緊急停止しました")
            
        except Exception as e:
            logger.error(f"緊急停止でエラー: {e}")
    
    @abstractmethod
    async def get_trading_symbols(self) -> List[str]:
        """取引対象シンボルを取得（サブクラスで実装）"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """戦略名を取得（サブクラスで実装）"""
        pass
