"""
段階的エントリー（分割売買）モジュール
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class EntryMethod(Enum):
    """エントリーメソッド"""
    TIME = "time"
    PRICE = "price"

class OrderStatus(Enum):
    """注文ステータス"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

@dataclass
class SplitEntryConfig:
    """分割エントリー設定"""
    enabled: bool
    count: int  # 分割回数
    method: EntryMethod  # 'time' or 'price'
    interval_seconds: int  # 時間間隔（秒）
    price_deviation_pct: float  # 価格乖離率（%）
    max_wait_time_seconds: int  # 最大待機時間

@dataclass
class SplitEntryOrder:
    """分割エントリー注文"""
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    order_type: str  # 'market' or 'limit'
    status: OrderStatus
    created_at: datetime
    filled_at: Optional[datetime]
    filled_price: Optional[float]
    filled_quantity: Optional[float]

@dataclass
class SplitEntryResult:
    """分割エントリー結果"""
    total_quantity: float
    average_price: float
    total_cost: float
    orders: List[SplitEntryOrder]
    execution_time: float
    success_rate: float

class SplitEntryManager:
    """分割エントリー管理クラス"""
    
    def __init__(self, config: SplitEntryConfig):
        self.config = config
        self.active_entries: Dict[str, List[SplitEntryOrder]] = {}
        self.order_counter = 0
        
    def _generate_order_id(self) -> str:
        """注文ID生成"""
        self.order_counter += 1
        return f"SPLIT_{self.order_counter:06d}"
    
    async def execute_split_entry(
        self,
        symbol: str,
        side: str,
        total_quantity: float,
        current_price: float,
        order_executor  # 注文実行関数
    ) -> SplitEntryResult:
        """分割エントリー実行"""
        
        if not self.config.enabled:
            # 分割エントリー無効の場合は通常の注文
            order = SplitEntryOrder(
                order_id=self._generate_order_id(),
                symbol=symbol,
                side=side,
                quantity=total_quantity,
                price=current_price,
                order_type='market',
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                filled_at=None,
                filled_price=None,
                filled_quantity=None
            )
            
            # 注文実行
            await order_executor(order)
            
            return SplitEntryResult(
                total_quantity=total_quantity,
                average_price=order.filled_price or current_price,
                total_cost=total_quantity * (order.filled_price or current_price),
                orders=[order],
                execution_time=0.0,
                success_rate=1.0 if order.status == OrderStatus.FILLED else 0.0
            )
        
        # 分割エントリー実行
        start_time = datetime.now()
        orders = []
        filled_quantity = 0.0
        total_cost = 0.0
        
        # 分割数量計算
        split_quantity = total_quantity / self.config.count
        
        for i in range(self.config.count):
            # 注文価格決定
            if self.config.method == EntryMethod.TIME:
                # 時間ベース：現在価格で成行注文
                order_price = current_price
                order_type = 'market'
            else:
                # 価格ベース：指値注文
                if side == 'buy':
                    # 買い注文：価格を下げる
                    deviation = current_price * (self.config.price_deviation_pct / 100)
                    order_price = current_price - (deviation * (i + 1))
                else:
                    # 売り注文：価格を上げる
                    deviation = current_price * (self.config.price_deviation_pct / 100)
                    order_price = current_price + (deviation * (i + 1))
                order_type = 'limit'
            
            # 注文作成
            order = SplitEntryOrder(
                order_id=self._generate_order_id(),
                symbol=symbol,
                side=side,
                quantity=split_quantity,
                price=order_price,
                order_type=order_type,
                status=OrderStatus.PENDING,
                created_at=datetime.now(),
                filled_at=None,
                filled_price=None,
                filled_quantity=None
            )
            
            # 注文実行
            await order_executor(order)
            orders.append(order)
            
            # 約定チェック
            if order.status == OrderStatus.FILLED:
                filled_quantity += order.filled_quantity or 0.0
                total_cost += (order.filled_quantity or 0.0) * (order.filled_price or order_price)
            
            # 時間間隔待機（最後の注文以外）
            if i < self.config.count - 1:
                await asyncio.sleep(self.config.interval_seconds)
        
        # 結果計算
        execution_time = (datetime.now() - start_time).total_seconds()
        success_rate = len([o for o in orders if o.status == OrderStatus.FILLED]) / len(orders)
        average_price = total_cost / filled_quantity if filled_quantity > 0 else current_price
        
        result = SplitEntryResult(
            total_quantity=filled_quantity,
            average_price=average_price,
            total_cost=total_cost,
            orders=orders,
            execution_time=execution_time,
            success_rate=success_rate
        )
        
        logger.info(f"Split entry completed for {symbol}: {filled_quantity:.6f} @ {average_price:.2f} "
                   f"(Success rate: {success_rate:.2%}, Time: {execution_time:.1f}s)")
        
        return result
    
    async def monitor_partial_orders(self, symbol: str, order_executor):
        """部分約定注文の監視"""
        if symbol not in self.active_entries:
            return
        
        orders = self.active_entries[symbol]
        current_time = datetime.now()
        
        for order in orders:
            if order.status == OrderStatus.PENDING:
                # 最大待機時間チェック
                wait_time = (current_time - order.created_at).total_seconds()
                if wait_time > self.config.max_wait_time_seconds:
                    # 注文キャンセル
                    await self._cancel_order(order, order_executor)
                    logger.info(f"Order {order.order_id} cancelled due to timeout")
    
    async def _cancel_order(self, order: SplitEntryOrder, order_executor):
        """注文キャンセル"""
        try:
            # 実際の実装では、取引所APIで注文キャンセル
            order.status = OrderStatus.CANCELLED
            logger.info(f"Order {order.order_id} cancelled")
        except Exception as e:
            logger.error(f"Failed to cancel order {order.order_id}: {e}")
    
    def get_split_entry_summary(self, symbol: str) -> Dict[str, Any]:
        """分割エントリーサマリー取得"""
        if symbol not in self.active_entries:
            return {"error": f"No active entries for {symbol}"}
        
        orders = self.active_entries[symbol]
        
        filled_orders = [o for o in orders if o.status == OrderStatus.FILLED]
        pending_orders = [o for o in orders if o.status == OrderStatus.PENDING]
        cancelled_orders = [o for o in orders if o.status == OrderStatus.CANCELLED]
        
        total_quantity = sum(o.filled_quantity or 0.0 for o in filled_orders)
        total_cost = sum((o.filled_quantity or 0.0) * (o.filled_price or 0.0) for o in filled_orders)
        average_price = total_cost / total_quantity if total_quantity > 0 else 0.0
        
        return {
            'symbol': symbol,
            'total_orders': len(orders),
            'filled_orders': len(filled_orders),
            'pending_orders': len(pending_orders),
            'cancelled_orders': len(cancelled_orders),
            'total_quantity': total_quantity,
            'average_price': average_price,
            'total_cost': total_cost,
            'success_rate': len(filled_orders) / len(orders) if orders else 0.0,
            'config': {
                'enabled': self.config.enabled,
                'count': self.config.count,
                'method': self.config.method.value,
                'interval_seconds': self.config.interval_seconds
            }
        }

# テスト用のメイン関数
async def test_split_entry():
    """分割エントリーテスト"""
    print("Split Entry Test")
    print("=" * 50)
    
    # 設定
    config = SplitEntryConfig(
        enabled=True,
        count=3,
        method=EntryMethod.TIME,
        interval_seconds=5,
        price_deviation_pct=0.5,
        max_wait_time_seconds=60
    )
    
    # 分割エントリーマネージャー初期化
    manager = SplitEntryManager(config)
    
    # モック注文実行関数
    async def mock_order_executor(order: SplitEntryOrder):
        """モック注文実行関数"""
        # シミュレーション：90%の確率で約定
        import random
        if random.random() < 0.9:
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            order.filled_price = order.price
            order.filled_quantity = order.quantity
            print(f"  Order {order.order_id}: FILLED {order.quantity:.6f} @ {order.price:.2f}")
        else:
            order.status = OrderStatus.CANCELLED
            print(f"  Order {order.order_id}: CANCELLED")
    
    # 分割エントリーテスト
    print("Testing split entry for BTCUSDT...")
    
    result = await manager.execute_split_entry(
        symbol='BTCUSDT',
        side='buy',
        total_quantity=0.003,
        current_price=50000.0,
        order_executor=mock_order_executor
    )
    
    print(f"\nSplit Entry Result:")
    print(f"  Total Quantity: {result.total_quantity:.6f}")
    print(f"  Average Price: {result.average_price:.2f}")
    print(f"  Total Cost: {result.total_cost:.2f}")
    print(f"  Execution Time: {result.execution_time:.1f}s")
    print(f"  Success Rate: {result.success_rate:.2%}")
    print(f"  Orders: {len(result.orders)}")
    
    # サマリー表示
    summary = manager.get_split_entry_summary('BTCUSDT')
    print(f"\nSummary:")
    print(f"  Total Orders: {summary['total_orders']}")
    print(f"  Filled Orders: {summary['filled_orders']}")
    print(f"  Success Rate: {summary['success_rate']:.2%}")
    
    print("\nSplit Entry Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_split_entry())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
