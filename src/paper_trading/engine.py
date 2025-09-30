"""
ペーパー取引エンジン - ダミー資金での取引シミュレーション
"""
import asyncio
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class OrderSide(Enum):
    """注文サイド"""
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    """注文タイプ"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class OrderStatus(Enum):
    """注文ステータス"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class PaperOrder:
    """ペーパー注文"""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    status: OrderStatus
    created_at: datetime
    filled_at: Optional[datetime]
    filled_price: Optional[float]
    filled_quantity: Optional[float]
    commission: float = 0.0
    notes: str = ""

@dataclass
class PaperPosition:
    """ペーパーポジション"""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    created_at: datetime
    updated_at: datetime

@dataclass
class PaperAccount:
    """ペーパーアカウント"""
    balance: float
    equity: float
    margin_used: float
    free_margin: float
    positions: Dict[str, PaperPosition]
    orders: List[PaperOrder]
    trade_history: List[Dict[str, Any]]
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    max_drawdown: float
    created_at: datetime
    updated_at: datetime

class PaperTradingEngine:
    """ペーパー取引エンジン"""
    
    def __init__(self, initial_balance: float = 10000.0, commission_rate: float = 0.001):
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.account = self._create_initial_account()
        self.order_counter = 0
        self.is_running = False
        self.log_file = Path("logs/paper_trading.jsonl")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # 価格データキャッシュ
        self.price_cache: Dict[str, float] = {}
        
    def _create_initial_account(self) -> PaperAccount:
        """初期アカウント作成"""
        now = datetime.now()
        return PaperAccount(
            balance=self.initial_balance,
            equity=self.initial_balance,
            margin_used=0.0,
            free_margin=self.initial_balance,
            positions={},
            orders=[],
            trade_history=[],
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_pnl=0.0,
            max_drawdown=0.0,
            created_at=now,
            updated_at=now
        )
    
    def _generate_order_id(self) -> str:
        """注文ID生成"""
        self.order_counter += 1
        return f"PAPER_{self.order_counter:06d}"
    
    def _get_current_price(self, symbol: str) -> float:
        """現在価格取得（モック実装）"""
        if symbol in self.price_cache:
            return self.price_cache[symbol]
        
        # モック価格生成（実際の実装ではAPIから取得）
        base_prices = {
            "BTCUSDT": 50000.0,
            "ETHUSDT": 3000.0,
            "ADAUSDT": 0.5,
            "DOTUSDT": 20.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        # ランダムな価格変動（±2%）
        variation = np.random.uniform(-0.02, 0.02)
        current_price = base_price * (1 + variation)
        
        self.price_cache[symbol] = current_price
        return current_price
    
    def _calculate_commission(self, quantity: float, price: float) -> float:
        """手数料計算"""
        return quantity * price * self.commission_rate
    
    def _update_account_equity(self):
        """アカウントエクイティ更新"""
        # ポジションの未実現損益を計算
        total_unrealized_pnl = 0.0
        
        for symbol, position in self.account.positions.items():
            current_price = self._get_current_price(symbol)
            position.current_price = current_price
            
            if position.side == OrderSide.BUY:
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            else:  # SELL
                position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
            
            total_unrealized_pnl += position.unrealized_pnl
        
        # エクイティ = 残高 + 未実現損益
        self.account.equity = self.account.balance + total_unrealized_pnl
        
        # 最大ドローダウン更新
        if self.account.equity < self.initial_balance:
            drawdown = (self.initial_balance - self.account.equity) / self.initial_balance
            self.account.max_drawdown = max(self.account.max_drawdown, drawdown)
        
        self.account.updated_at = datetime.now()
    
    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> PaperOrder:
        """注文実行"""
        order_id = self._generate_order_id()
        current_price = self._get_current_price(symbol)
        
        # 注文価格決定
        if order_type == OrderType.MARKET:
            order_price = current_price
        elif order_type == OrderType.LIMIT:
            order_price = price or current_price
        elif order_type == OrderType.STOP:
            order_price = stop_price or current_price
        else:
            order_price = current_price
        
        # 注文作成
        order = PaperOrder(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=order_price,
            stop_price=stop_price,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            filled_at=None,
            filled_price=None,
            filled_quantity=None
        )
        
        # 注文実行
        try:
            self._execute_order(order)
            self.account.orders.append(order)
            self._log_order(order)
            
            logger.info(f"Order placed: {order_id} {side.value} {quantity} {symbol} @ {order_price}")
            
        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.notes = str(e)
            logger.error(f"Order rejected: {order_id}, Error: {e}")
        
        return order
    
    def _execute_order(self, order: PaperOrder):
        """注文実行（内部）"""
        current_price = self._get_current_price(order.symbol)
        
        # 注文タイプ別の実行ロジック
        if order.order_type == OrderType.MARKET:
            # 成行注文は即座に約定
            self._fill_order(order, current_price)
            
        elif order.order_type == OrderType.LIMIT:
            # 指値注文の約定判定
            if order.side == OrderSide.BUY and current_price <= order.price:
                self._fill_order(order, order.price)
            elif order.side == OrderSide.SELL and current_price >= order.price:
                self._fill_order(order, order.price)
            else:
                order.status = OrderStatus.PENDING
                
        elif order.order_type == OrderType.STOP:
            # ストップ注文の約定判定
            if order.side == OrderSide.BUY and current_price >= order.stop_price:
                self._fill_order(order, current_price)
            elif order.side == OrderSide.SELL and current_price <= order.stop_price:
                self._fill_order(order, current_price)
            else:
                order.status = OrderStatus.PENDING
    
    def _fill_order(self, order: PaperOrder, fill_price: float):
        """注文約定処理"""
        # 手数料計算
        commission = self._calculate_commission(order.quantity, fill_price)
        order.commission = commission
        
        # 約定情報設定
        order.status = OrderStatus.FILLED
        order.filled_at = datetime.now()
        order.filled_price = fill_price
        order.filled_quantity = order.quantity
        
        # ポジション更新
        self._update_position(order, fill_price)
        
        # アカウント残高更新
        if order.side == OrderSide.BUY:
            cost = (order.quantity * fill_price) + commission
            self.account.balance -= cost
        else:  # SELL
            proceeds = (order.quantity * fill_price) - commission
            self.account.balance += proceeds
        
        # 取引履歴追加
        trade = {
            'order_id': order.id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'price': fill_price,
            'commission': commission,
            'timestamp': order.filled_at.isoformat(),
            'pnl': 0.0  # ポジションクローズ時に計算
        }
        
        self.account.trade_history.append(trade)
        self.account.total_trades += 1
        
        # アカウントエクイティ更新
        self._update_account_equity()
        
        logger.info(f"Order filled: {order.id} @ {fill_price}")
    
    def _update_position(self, order: PaperOrder, fill_price: float):
        """ポジション更新"""
        symbol = order.symbol
        
        if symbol not in self.account.positions:
            # 新しいポジション作成
            self.account.positions[symbol] = PaperPosition(
                symbol=symbol,
                side=order.side,
                quantity=order.quantity,
                entry_price=fill_price,
                current_price=fill_price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        else:
            # 既存ポジション更新
            position = self.account.positions[symbol]
            
            if position.side == order.side:
                # 同方向のポジション追加
                total_quantity = position.quantity + order.quantity
                total_cost = (position.quantity * position.entry_price) + (order.quantity * fill_price)
                position.entry_price = total_cost / total_quantity
                position.quantity = total_quantity
            else:
                # 反対方向のポジション（クローズ）
                if order.quantity >= position.quantity:
                    # ポジション完全クローズ
                    realized_pnl = self._calculate_realized_pnl(position, fill_price, position.quantity)
                    position.realized_pnl += realized_pnl
                    self.account.total_pnl += realized_pnl
                    
                    # 勝敗カウント
                    if realized_pnl > 0:
                        self.account.winning_trades += 1
                    else:
                        self.account.losing_trades += 1
                    
                    # ポジション削除
                    del self.account.positions[symbol]
                    
                    # 残りの数量で新しいポジション作成
                    remaining_quantity = order.quantity - position.quantity
                    if remaining_quantity > 0:
                        self.account.positions[symbol] = PaperPosition(
                            symbol=symbol,
                            side=order.side,
                            quantity=remaining_quantity,
                            entry_price=fill_price,
                            current_price=fill_price,
                            unrealized_pnl=0.0,
                            realized_pnl=0.0,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                else:
                    # ポジション部分クローズ
                    realized_pnl = self._calculate_realized_pnl(position, fill_price, order.quantity)
                    position.realized_pnl += realized_pnl
                    self.account.total_pnl += realized_pnl
                    
                    # 勝敗カウント
                    if realized_pnl > 0:
                        self.account.winning_trades += 1
                    else:
                        self.account.losing_trades += 1
                    
                    # ポジション数量更新
                    position.quantity -= order.quantity
            
            position.updated_at = datetime.now()
    
    def _calculate_realized_pnl(self, position: PaperPosition, exit_price: float, quantity: float) -> float:
        """実現損益計算"""
        if position.side == OrderSide.BUY:
            return (exit_price - position.entry_price) * quantity
        else:  # SELL
            return (position.entry_price - exit_price) * quantity
    
    def cancel_order(self, order_id: str) -> bool:
        """注文キャンセル"""
        for order in self.account.orders:
            if order.id == order_id and order.status == OrderStatus.PENDING:
                order.status = OrderStatus.CANCELLED
                logger.info(f"Order cancelled: {order_id}")
                return True
        
        return False
    
    def get_account_summary(self) -> Dict[str, Any]:
        """アカウントサマリー取得"""
        self._update_account_equity()
        
        return {
            'balance': self.account.balance,
            'equity': self.account.equity,
            'margin_used': self.account.margin_used,
            'free_margin': self.account.free_margin,
            'total_trades': self.account.total_trades,
            'winning_trades': self.account.winning_trades,
            'losing_trades': self.account.losing_trades,
            'win_rate': self.account.winning_trades / self.account.total_trades if self.account.total_trades > 0 else 0,
            'total_pnl': self.account.total_pnl,
            'max_drawdown': self.account.max_drawdown,
            'return_pct': (self.account.equity - self.initial_balance) / self.initial_balance,
            'positions': {symbol: asdict(pos) for symbol, pos in self.account.positions.items()},
            'open_orders': [asdict(order) for order in self.account.orders if order.status == OrderStatus.PENDING],
            'created_at': self.account.created_at.isoformat(),
            'updated_at': self.account.updated_at.isoformat()
        }
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """取引履歴取得"""
        return self.account.trade_history[-limit:]
    
    def _log_order(self, order: PaperOrder):
        """注文ログ出力"""
        log_entry = {
            'timestamp': order.created_at.isoformat(),
            'order_id': order.id,
            'symbol': order.symbol,
            'side': order.side.value,
            'order_type': order.order_type.value,
            'quantity': order.quantity,
            'price': order.price,
            'status': order.status.value,
            'filled_price': order.filled_price,
            'filled_quantity': order.filled_quantity,
            'commission': order.commission,
            'notes': order.notes
        }
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def start(self):
        """ペーパー取引エンジン開始"""
        self.is_running = True
        logger.info("Paper trading engine started")
    
    def stop(self):
        """ペーパー取引エンジン停止"""
        self.is_running = False
        logger.info("Paper trading engine stopped")

# テスト用のメイン関数
async def test_paper_trading():
    """ペーパー取引テスト"""
    print("Paper Trading Engine Test")
    print("=" * 50)
    
    # ペーパー取引エンジン初期化
    engine = PaperTradingEngine(initial_balance=10000.0)
    engine.start()
    
    # テスト取引実行
    print("Testing paper trading operations...")
    
    # 1. 買い注文
    buy_order = engine.place_order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=0.1
    )
    print(f"Buy order: {buy_order.id} - {buy_order.status.value}")
    
    # 2. 売り注文
    sell_order = engine.place_order(
        symbol="BTCUSDT",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=0.05
    )
    print(f"Sell order: {sell_order.id} - {sell_order.status.value}")
    
    # 3. 指値注文
    limit_order = engine.place_order(
        symbol="ETHUSDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=1.0,
        price=2900.0
    )
    print(f"Limit order: {limit_order.id} - {limit_order.status.value}")
    
    # 4. アカウントサマリー表示
    summary = engine.get_account_summary()
    print(f"\nAccount Summary:")
    print(f"  Balance: ${summary['balance']:.2f}")
    print(f"  Equity: ${summary['equity']:.2f}")
    print(f"  Total Trades: {summary['total_trades']}")
    print(f"  Win Rate: {summary['win_rate']:.2%}")
    print(f"  Total PnL: ${summary['total_pnl']:.2f}")
    print(f"  Return: {summary['return_pct']:.2%}")
    print(f"  Max Drawdown: {summary['max_drawdown']:.2%}")
    
    # 5. ポジション表示
    if summary['positions']:
        print(f"\nPositions:")
        for symbol, position in summary['positions'].items():
            print(f"  {symbol}: {position['quantity']} @ ${position['entry_price']:.2f}")
    
    # 6. 取引履歴表示
    history = engine.get_trade_history(limit=5)
    if history:
        print(f"\nRecent Trades:")
        for trade in history[-3:]:
            print(f"  {trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']:.2f}")
    
    engine.stop()
    print("\nPaper Trading Engine Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_paper_trading())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
