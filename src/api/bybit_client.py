"""
自己進化型AIポートフォリオ自動売買システム - Bybit API クライアント
"""

import asyncio
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode
import aiohttp
import logging

from ..core.config import config
from ..core.exceptions import BybitAPIError

logger = logging.getLogger(__name__)


class BybitClient:
    """Bybit API クライアント"""
    
    def __init__(self):
        self.api_key = config.bybit.api_key
        self.secret_key = config.bybit.secret_key
        self.testnet = config.bybit.testnet
        self.timeout = config.bybit.timeout
        
        # API エンドポイント
        if self.testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """API署名を生成"""
        timestamp = str(int(time.time() * 1000))
        params['timestamp'] = timestamp
        
        # パラメータをソートしてクエリ文字列を作成
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        
        # HMAC-SHA256で署名を生成
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature, timestamp
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        requires_auth: bool = False
    ) -> Dict[str, Any]:
        """APIリクエストを実行"""
        if not self.session:
            raise BybitAPIError("セッションが初期化されていません")
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'X-BAPI-API-KEY': self.api_key
        }
        
        if requires_auth:
            if not params:
                params = {}
            signature, timestamp = self._generate_signature(params)
            headers.update({
                'X-BAPI-SIGN': signature,
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-RECV-WINDOW': '5000'
            })
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=params if method.upper() == 'POST' else None,
                params=params if method.upper() == 'GET' else None
            ) as response:
                data = await response.json()
                
                if response.status != 200:
                    raise BybitAPIError(f"API エラー: {response.status} - {data}")
                
                if data.get('retCode') != 0:
                    raise BybitAPIError(f"Bybit API エラー: {data.get('retMsg', 'Unknown error')}")
                
                return data.get('result', data)
                
        except aiohttp.ClientError as e:
            raise BybitAPIError(f"ネットワークエラー: {e}")
        except Exception as e:
            raise BybitAPIError(f"予期しないエラー: {e}")
    
    async def get_account_balance(self) -> Dict[str, Any]:
        """アカウント残高を取得"""
        return await self._make_request(
            'GET',
            '/v5/account/wallet-balance',
            {'accountType': 'UNIFIED'},
            requires_auth=True
        )
    
    async def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """ポジション情報を取得"""
        params = {'category': 'linear'}
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request(
            'GET',
            '/v5/position/list',
            params,
            requires_auth=True
        )
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: str,
        price: Optional[str] = None,
        stop_loss: Optional[str] = None,
        take_profit: Optional[str] = None
    ) -> Dict[str, Any]:
        """注文を発注"""
        params = {
            'category': 'linear',
            'symbol': symbol,
            'side': side,
            'orderType': order_type,
            'qty': qty,
            'timeInForce': 'GTC'
        }
        
        if price:
            params['price'] = price
        
        if stop_loss:
            params['stopLoss'] = stop_loss
        
        if take_profit:
            params['takeProfit'] = take_profit
        
        return await self._make_request(
            'POST',
            '/v5/order/create',
            params,
            requires_auth=True
        )
    
    async def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """注文をキャンセル"""
        params = {
            'category': 'linear',
            'symbol': symbol,
            'orderId': order_id
        }
        
        return await self._make_request(
            'POST',
            '/v5/order/cancel',
            params,
            requires_auth=True
        )
    
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """注文履歴を取得"""
        params = {
            'category': 'linear',
            'limit': limit
        }
        
        if symbol:
            params['symbol'] = symbol
        
        return await self._make_request(
            'GET',
            '/v5/order/history',
            params,
            requires_auth=True
        )
    
    async def get_trading_fees(self, symbol: str) -> Dict[str, Any]:
        """取引手数料を取得"""
        params = {
            'category': 'linear',
            'symbol': symbol
        }
        
        return await self._make_request(
            'GET',
            '/v5/account/fee-rate',
            params,
            requires_auth=True
        )
    
    async def get_kline_data(
        self,
        symbol: str,
        interval: str,
        limit: int = 200,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """K線データを取得"""
        params = {
            'category': 'linear',
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['start'] = start_time
        
        if end_time:
            params['end'] = end_time
        
        return await self._make_request(
            'GET',
            '/v5/market/kline',
            params
        )
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """ティッカー情報を取得"""
        params = {
            'category': 'linear',
            'symbol': symbol
        }
        
        return await self._make_request(
            'GET',
            '/v5/market/tickers',
            params
        )
    
    async def get_orderbook(self, symbol: str, limit: int = 25) -> Dict[str, Any]:
        """オーダーブックを取得"""
        params = {
            'category': 'linear',
            'symbol': symbol,
            'limit': limit
        }
        
        return await self._make_request(
            'GET',
            '/v5/market/orderbook',
            params
        )
    
    async def transfer_funds(
        self,
        from_account_type: str,
        to_account_type: str,
        coin: str,
        amount: str
    ) -> Dict[str, Any]:
        """資金移動"""
        params = {
            'fromAccountType': from_account_type,
            'toAccountType': to_account_type,
            'coin': coin,
            'amount': amount
        }
        
        return await self._make_request(
            'POST',
            '/v5/asset/transfer/inter-transfer',
            params,
            requires_auth=True
        )
