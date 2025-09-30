"""
自己進化型AIポートフォリオ自動売買システム - サーキットブレーカー
"""

import time
import logging
import functools
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """サーキットブレーカー - 連続失敗時の自動停止機能"""
    
    def __init__(
        self,
        fail_threshold: int = 10,
        window: int = 60,
        open_for: int = 300,
        half_open_max_calls: int = 3
    ):
        self.fail_threshold = fail_threshold  # 失敗閾値
        self.window = window  # 時間窓（秒）
        self.open_for = open_for  # オープン状態の継続時間（秒）
        self.half_open_max_calls = half_open_max_calls  # ハーフオープン時の最大試行回数
        
        self.fail_times: list = []  # 失敗時刻のリスト
        self.open_until: float = 0  # オープン状態の終了時刻
        self.half_open_calls: int = 0  # ハーフオープン時の試行回数
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        
        # 状態
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_failure(self, error: Optional[Exception] = None) -> None:
        """失敗を記録"""
        now = time.time()
        
        # 古い失敗記録を削除
        self.fail_times = [t for t in self.fail_times if now - t < self.window]
        self.fail_times.append(now)
        
        self.last_failure_time = now
        
        # 失敗閾値を超えた場合、サーキットをオープン
        if len(self.fail_times) >= self.fail_threshold:
            self.open_until = now + self.open_for
            self.state = "OPEN"
            logger.critical(f"サーキットブレーカーがオープンしました: {len(self.fail_times)}回の失敗")
            
            if error:
                logger.error(f"サーキットブレーカー発動の原因: {error}")
    
    def record_success(self) -> None:
        """成功を記録"""
        now = time.time()
        self.last_success_time = now
        
        # 成功時は失敗記録をクリア
        self.fail_times.clear()
        
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.half_open_calls = 0
            logger.info("サーキットブレーカーがクローズしました")
    
    def is_open(self) -> bool:
        """サーキットがオープンかどうかを確認"""
        now = time.time()
        
        if self.state == "OPEN":
            if now >= self.open_until:
                # オープン期間が終了した場合、ハーフオープンに移行
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                logger.info("サーキットブレーカーがハーフオープンに移行しました")
                return False
            return True
        
        elif self.state == "HALF_OPEN":
            if self.half_open_calls >= self.half_open_max_calls:
                # ハーフオープン時の最大試行回数を超えた場合、再びオープン
                self.state = "OPEN"
                self.open_until = now + self.open_for
                logger.warning("ハーフオープン時の最大試行回数を超えました。サーキットを再オープンします")
                return True
            return False
        
        else:  # CLOSED
            return False
    
    def can_execute(self) -> bool:
        """実行可能かどうかを確認"""
        if self.is_open():
            return False
        
        if self.state == "HALF_OPEN":
            self.half_open_calls += 1
        
        return True
    
    def get_state_info(self) -> Dict[str, Any]:
        """現在の状態情報を取得"""
        now = time.time()
        
        return {
            "state": self.state,
            "fail_count": len(self.fail_times),
            "fail_threshold": self.fail_threshold,
            "window_seconds": self.window,
            "open_until": self.open_until,
            "time_until_close": max(0, self.open_until - now) if self.state == "OPEN" else 0,
            "half_open_calls": self.half_open_calls,
            "last_failure": self.last_failure_time,
            "last_success": self.last_success_time,
            "is_open": self.is_open()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """監視用の状態情報を取得（get_state_infoのエイリアス）"""
        return self.get_state_info()
    
    def reset(self) -> None:
        """サーキットブレーカーをリセット"""
        self.fail_times.clear()
        self.open_until = 0
        self.half_open_calls = 0
        self.state = "CLOSED"
        self.last_failure_time = None
        self.last_success_time = None
        logger.info("サーキットブレーカーをリセットしました")


# グローバルインスタンス
circuit_breaker = CircuitBreaker()


class CircuitBreakerMiddleware:
    """サーキットブレーカーミドルウェア"""
    
    def __init__(self, circuit_breaker: CircuitBreaker):
        self.circuit_breaker = circuit_breaker
    
    async def execute_with_circuit_breaker(self, func, *args, **kwargs):
        """サーキットブレーカー付きで関数を実行"""
        if not self.circuit_breaker.can_execute():
            raise RuntimeError("Circuit breaker open - abort execution")
        
        try:
            result = await func(*args, **kwargs)
            self.circuit_breaker.record_success()
            return result
        except Exception as e:
            self.circuit_breaker.record_failure(e)
            raise


# デコレーター
def circuit_breaker_protected(cb_instance=None):
    """サーキットブレーカー保護デコレーター"""
    if cb_instance is None:
        cb_instance = circuit_breaker
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if cb_instance.is_open():
                raise RuntimeError("Circuit breaker is open")
            try:
                result = await func(*args, **kwargs)
                cb_instance.record_success()
                return result
            except Exception as e:
                cb_instance.record_failure(e)
                raise
        return wrapper
    return decorator
