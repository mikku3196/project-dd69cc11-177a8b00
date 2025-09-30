"""
ダッシュボード起動確認スクリプト
"""
import asyncio
import aiohttp
import time
import sys
import io
from datetime import datetime

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

class DashboardHealthChecker:
    """ダッシュボードヘルスチェッカー"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.max_retries = 10
        self.retry_interval = 3
    
    async def check_server_health(self) -> bool:
        """サーバーヘルスチェック"""
        print(f"[INFO] サーバーヘルスチェック開始: {self.base_url}")
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/health", timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"[SUCCESS] サーバー応答: {data.get('status')}")
                            return True
                        else:
                            print(f"[WARNING] サーバー応答: HTTP {response.status}")
                            
            except aiohttp.ClientConnectorError:
                print(f"[INFO] 接続試行 {attempt + 1}/{self.max_retries}: サーバー未起動")
            except asyncio.TimeoutError:
                print(f"[WARNING] 接続試行 {attempt + 1}/{self.max_retries}: タイムアウト")
            except Exception as e:
                print(f"[ERROR] 接続試行 {attempt + 1}/{self.max_retries}: {e}")
            
            if attempt < self.max_retries - 1:
                print(f"[INFO] {self.retry_interval}秒後に再試行...")
                await asyncio.sleep(self.retry_interval)
        
        print("[ERROR] サーバーに接続できませんでした")
        return False
    
    async def check_all_endpoints(self) -> bool:
        """全エンドポイントチェック"""
        print("\n[INFO] 全エンドポイントチェック開始")
        
        endpoints = [
            ("/", "ルートエンドポイント"),
            ("/health", "ヘルスチェック"),
            ("/status", "ステータス取得"),
            ("/logs", "ログ取得"),
            ("/docs", "API ドキュメント")
        ]
        
        success_count = 0
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}", timeout=5) as response:
                        if response.status == 200:
                            print(f"[SUCCESS] {description}: OK")
                            success_count += 1
                        else:
                            print(f"[WARNING] {description}: HTTP {response.status}")
                            
                except Exception as e:
                    print(f"[ERROR] {description}: {e}")
        
        print(f"\n[INFO] エンドポイントチェック結果: {success_count}/{len(endpoints)} 成功")
        return success_count >= len(endpoints) * 0.8  # 80%以上成功でOK
    
    async def wait_for_server(self) -> bool:
        """サーバー起動待機"""
        print("🚀 ダッシュボードサーバー起動待機")
        print("=" * 50)
        
        # サーバーヘルスチェック
        if await self.check_server_health():
            # 全エンドポイントチェック
            if await self.check_all_endpoints():
                print("\n🎉 ダッシュボードサーバーが正常に起動しています！")
                print(f"📊 アクセス先: {self.base_url}")
                print(f"📚 API ドキュメント: {self.base_url}/docs")
                return True
            else:
                print("\n⚠️ 一部のエンドポイントに問題があります")
                return False
        else:
            print("\n❌ ダッシュボードサーバーが起動していません")
            print("\n[INFO] サーバー起動方法:")
            print("  python scripts/start_dashboard.py")
            print("  または")
            print("  uvicorn src.dashboard.api:app --host 0.0.0.0 --port 8000 --reload")
            return False


async def main():
    """メイン関数"""
    checker = DashboardHealthChecker()
    success = await checker.wait_for_server()
    
    if success:
        print("\n✅ ダッシュボードテストを実行できます")
        print("   python scripts/test_dashboard.py")
    else:
        print("\n❌ ダッシュボードサーバーを起動してからテストを実行してください")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        sys.exit(1)
