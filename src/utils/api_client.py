"""
自己進化型AIポートフォリオ自動売買システム - APIキー管理とレート制限対応
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class KeyRing:
    """APIキー管理クラス - 複数キーのローテーションとブラックリスト管理"""
    
    def __init__(self, keys: List[str]):
        self.keys = list(keys)
        self.blacklist: Dict[str, float] = {}  # キー: 解除時刻
        self.current_index = 0
        self.key_stats: Dict[str, Dict[str, Any]] = {}
        
        # 各キーの統計情報を初期化
        for key in self.keys:
            self.key_stats[key] = {
                'success_count': 0,
                'failure_count': 0,
                'last_used': None,
                'rate_limit_hits': 0
            }
    
    def get_next_key(self) -> Optional[str]:
        """次の利用可能なキーを取得"""
        now = asyncio.get_event_loop().time()
        
        # ブラックリストから期限切れのキーを削除
        self.keys = [k for k in self.keys if self.blacklist.get(k, 0) < now]
        
        if not self.keys:
            logger.error("利用可能なAPIキーがありません")
            return None
        
        # ラウンドロビンでキーを選択
        key = self.keys[self.current_index % len(self.keys)]
        self.current_index += 1
        
        # 統計情報を更新
        self.key_stats[key]['last_used'] = now
        
        return key
    
    def blacklist_key(self, key: str, seconds: int) -> None:
        """キーをブラックリストに追加"""
        now = asyncio.get_event_loop().time()
        self.blacklist[key] = now + seconds
        
        logger.warning(f"APIキーをブラックリストに追加: {seconds}秒間隔離")
    
    def record_success(self, key: str) -> None:
        """成功を記録"""
        if key in self.key_stats:
            self.key_stats[key]['success_count'] += 1
    
    def record_failure(self, key: str, error_type: str = "unknown") -> None:
        """失敗を記録"""
        if key in self.key_stats:
            self.key_stats[key]['failure_count'] += 1
            
            if error_type == "rate_limit":
                self.key_stats[key]['rate_limit_hits'] += 1
    
    def get_key_stats(self) -> Dict[str, Dict[str, Any]]:
        """キーの統計情報を取得"""
        return self.key_stats.copy()


class RateLimitHandler:
    """レート制限ハンドラー"""
    
    def __init__(self):
        self.retry_delays = [0.5, 1.0, 2.0, 4.0, 8.0]  # 指数バックオフ
        self.max_retries = len(self.retry_delays)
    
    async def handle_rate_limit(
        self,
        key_ring: KeyRing,
        current_key: str,
        response_status: int,
        response_headers: Dict[str, str]
    ) -> bool:
        """レート制限を処理"""
        
        if response_status == 429:
            # レート制限ヘッダーから待機時間を取得
            retry_after = self._get_retry_after(response_headers)
            
            # 現在のキーをブラックリストに追加
            blacklist_duration = retry_after or 60  # デフォルト60秒
            key_ring.blacklist_key(current_key, blacklist_duration)
            key_ring.record_failure(current_key, "rate_limit")
            
            logger.warning(f"レート制限検出: キーを{blacklist_duration}秒間隔離")
            
            # 次のキーを取得
            next_key = key_ring.get_next_key()
            if next_key:
                logger.info(f"次のキーに切り替え: {next_key[:8]}...")
                return True
            else:
                logger.error("利用可能なキーがありません")
                return False
        
        return False
    
    def _get_retry_after(self, headers: Dict[str, str]) -> Optional[int]:
        """Retry-Afterヘッダーから待機時間を取得"""
        retry_after = headers.get('Retry-After') or headers.get('retry-after')
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return None
    
    async def exponential_backoff(self, attempt: int) -> None:
        """指数バックオフで待機"""
        if attempt < len(self.retry_delays):
            delay = self.retry_delays[attempt]
            logger.info(f"指数バックオフ: {delay}秒待機")
            await asyncio.sleep(delay)


class RobustAPIClient:
    """堅牢なAPIクライアント基底クラス"""
    
    def __init__(self, api_keys: List[str], base_url: str):
        self.key_ring = KeyRing(api_keys)
        self.rate_limit_handler = RateLimitHandler()
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
    
    async def _make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        requires_auth: bool = False
    ) -> Dict[str, Any]:
        """リトライ機能付きでAPIリクエストを実行"""
        
        last_error = None
        
        for attempt in range(self.rate_limit_handler.max_retries):
            try:
                # 利用可能なキーを取得
                api_key = self.key_ring.get_next_key()
                if not api_key:
                    raise Exception("利用可能なAPIキーがありません")
                
                # ヘッダーを準備
                request_headers = headers.copy() if headers else {}
                if requires_auth:
                    request_headers['Authorization'] = f'Bearer {api_key}'
                
                # リクエストを実行
                url = f"{self.base_url}{endpoint}"
                
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=params if method.upper() == 'POST' else None,
                    params=params if method.upper() == 'GET' else None
                ) as response:
                    
                    # レスポンスを処理
                    response_data = await response.json()
                    
                    # レート制限チェック
                    if response.status == 429:
                        handled = await self.rate_limit_handler.handle_rate_limit(
                            self.key_ring, api_key, response.status, dict(response.headers)
                        )
                        if handled:
                            continue  # 次のキーでリトライ
                        else:
                            raise Exception("レート制限: 利用可能なキーがありません")
                    
                    # 成功の場合
                    if response.status == 200:
                        self.key_ring.record_success(api_key)
                        return response_data
                    
                    # その他のエラー
                    error_msg = f"API エラー: {response.status} - {response_data}"
                    self.key_ring.record_failure(api_key, "api_error")
                    raise Exception(error_msg)
                    
            except Exception as e:
                last_error = e
                logger.warning(f"API リクエスト失敗 (試行 {attempt + 1}/{self.rate_limit_handler.max_retries}): {e}")
                
                # 指数バックオフで待機
                if attempt < self.rate_limit_handler.max_retries - 1:
                    await self.rate_limit_handler.exponential_backoff(attempt)
        
        # 全てのリトライが失敗
        raise Exception(f"全てのリトライが失敗しました: {last_error}")
    
    def get_key_statistics(self) -> Dict[str, Any]:
        """キーの統計情報を取得"""
        return {
            'key_stats': self.key_ring.get_key_stats(),
            'blacklisted_keys': len(self.key_ring.blacklist),
            'available_keys': len(self.key_ring.keys)
        }
