"""
監視エンドポイント確認スクリプト
"""
import asyncio
import aiohttp
import json
import time
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

async def check_endpoints():
    """監視エンドポイントを確認"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/health",
        "/status", 
        "/metrics"
    ]
    
    print("=== 監視エンドポイント確認 ===")
    
    async with aiohttp.ClientSession() as session:
        for endpoint in endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n✅ {endpoint}:")
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    else:
                        print(f"\n❌ {endpoint}: HTTP {response.status}")
            except aiohttp.ClientConnectorError:
                print(f"\n[ERROR] {endpoint}: 接続エラー - サーバーが起動していません")
            except Exception as e:
                print(f"\n[ERROR] {endpoint}: エラー - {e}")
            
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(check_endpoints())
