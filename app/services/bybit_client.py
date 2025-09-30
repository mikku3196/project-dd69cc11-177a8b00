import time
import hmac
import hashlib
import json
import requests
from app.core.config import settings

class BybitClient:
    """
    Bybit API v5と通信するためのクライアントクラス。
    認証と基本的なリクエスト機能を担当する。
    """
    def __init__(self):
        self.api_key = settings.BYBIT_API_KEY
        self.api_secret = settings.BYBIT_API_SECRET
        
        # 本番環境かテストネットかを設定ファイルから読み込む
        is_testnet = settings.general.get('environment') == 'testnet'
        self.base_url = "https://api-testnet.bybit.com" if is_testnet else "https://api.bybit.com"
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Bybit API Key and Secret must be set in the .env file.")

    def _generate_signature(self, timestamp: str, recv_window: str, params: str) -> str:
        """
        Bybit API v5用のリクエスト署名を生成する。
        """
        param_str = timestamp + self.api_key + recv_window + params
        hash_obj = hmac.new(bytes(self.api_secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
        signature = hash_obj.hexdigest()
        return signature

    def _send_request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """
        署名付きリクエストをBybit APIに送信する共通メソッド。
        """
        full_url = self.base_url + endpoint
        timestamp = str(int(time.time() * 1000))
        recv_window = "20000"  # 20秒
        
        if params is None:
            params = {}

        if method.upper() == 'GET':
            query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._generate_signature(timestamp, recv_window, query_string)
            
            headers = {
                'X-BAPI-API-KEY': self.api_key,
                'X-BAPI-TIMESTAMP': timestamp,
                'X-BAPI-SIGN': signature,
                'X-BAPI-RECV-WINDOW': recv_window,
                'Content-Type': 'application/json'
            }
            
            try:
                response = requests.get(full_url, params=params, headers=headers)
                response.raise_for_status() # HTTPエラーがあれば例外を発生
                return response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error sending GET request: {e}")
                # 実際の運用では、より詳細なエラーハンドリングとロギングを行う
                return {"retCode": -1, "retMsg": str(e), "result": {}}

        # POSTリクエストの実装は将来のタスクで追加する
        # ...

        return {}

    def get_wallet_balance(self, account_type: str = "UNIFIED") -> dict:
        """
        指定されたアカウントタイプのウォレット残高を取得する。
        """
        endpoint = "/v5/account/wallet-balance"
        params = {
            "accountType": account_type
        }
        return self._send_request("GET", endpoint, params)

# --- 動作確認用のコード ---
if __name__ == '__main__':
    # このファイルが直接実行された場合にのみ、以下のコードが動く
    print("--- Bybit API Client Test ---")
    
    # .envファイルにAPIキーが設定されているか確認
    if not settings.BYBIT_API_KEY or settings.BYBIT_API_KEY == "YOUR_BYBIT_API_KEY":
        print("Error: Please set your Bybit API Key and Secret in the .env file.")
        print("You can get them from your Bybit account.")
        print("For testing, you can use Testnet keys.")
    else:
        client = BybitClient()
        print(f"Connecting to: {client.base_url}")
        
        balance_data = client.get_wallet_balance()
        
        print("\n--- API Response ---")
        print(json.dumps(balance_data, indent=2))
        
        if balance_data.get("retCode") == 0:
            print("\nSuccess! API connection is working.")
            try:
                # 資産リストからUSDTの残高を探して表示
                unified_assets = balance_data["result"]["list"][0]["coin"]
                usdt_balance = next((coin["walletBalance"] for coin in unified_assets if coin["coin"] == "USDT"), "0")
                print(f"Your USDT Wallet Balance: {usdt_balance}")
            except (KeyError, IndexError, TypeError):
                print("Could not parse wallet balance from the response.")
        else:
            print(f"\nError: API returned an error.")
            print(f"Return Code: {balance_data.get('retCode')}")
            print(f"Return Message: {balance_data.get('retMsg')}")
