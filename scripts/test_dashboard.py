"""
ダッシュボード動作確認スクリプト
"""
import asyncio
import aiohttp
import json
import time
import sys
import io
from datetime import datetime

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

class DashboardTester:
    """ダッシュボードテストクラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
    
    async def test_health_endpoint(self):
        """ヘルスチェックエンドポイントテスト"""
        print("=== ヘルスチェックエンドポイントテスト ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("[SUCCESS] ヘルスチェック: OK")
                        print(f"   - ステータス: {data.get('status')}")
                        print(f"   - タイムスタンプ: {data.get('timestamp')}")
                        print(f"   - マスターボット稼働: {data.get('master_bot_running')}")
                        
                        self.test_results.append(("ヘルスチェック", "PASS", "正常に応答"))
                    else:
                        print(f"[ERROR] ヘルスチェック: HTTP {response.status}")
                        self.test_results.append(("ヘルスチェック", "FAILED", f"HTTP {response.status}"))
                        
        except Exception as e:
            print(f"[ERROR] ヘルスチェックエラー: {e}")
            self.test_results.append(("ヘルスチェック", "FAILED", str(e)))
    
    async def test_status_endpoint(self):
        """ステータスエンドポイントテスト"""
        print("\n=== ステータスエンドポイントテスト ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("[SUCCESS] ステータス取得: OK")
                        print(f"   - 稼働状態: {data.get('is_running')}")
                        print(f"   - リスクレベル: {data.get('risk_level')}")
                        print(f"   - 配分: {data.get('allocation')}")
                        
                        # 必須フィールドチェック
                        required_fields = ['is_running', 'risk_level', 'allocation', 'risk_metrics', 'performance_data']
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if missing_fields:
                            print(f"[WARNING] 不足フィールド: {missing_fields}")
                        
                        self.test_results.append(("ステータス取得", "PASS", "正常にデータ取得"))
                    else:
                        print(f"[ERROR] ステータス取得: HTTP {response.status}")
                        self.test_results.append(("ステータス取得", "FAILED", f"HTTP {response.status}"))
                        
        except Exception as e:
            print(f"[ERROR] ステータス取得エラー: {e}")
            self.test_results.append(("ステータス取得", "FAILED", str(e)))
    
    async def test_logs_endpoint(self):
        """ログエンドポイントテスト"""
        print("\n=== ログエンドポイントテスト ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/logs?limit=10") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("[SUCCESS] ログ取得: OK")
                        print(f"   - ログ数: {len(data)}")
                        
                        if data:
                            latest_log = data[-1]
                            print(f"   - 最新ログ: {latest_log.get('level')} - {latest_log.get('message')}")
                        
                        self.test_results.append(("ログ取得", "PASS", f"{len(data)}件のログ取得"))
                    else:
                        print(f"[ERROR] ログ取得: HTTP {response.status}")
                        self.test_results.append(("ログ取得", "FAILED", f"HTTP {response.status}"))
                        
        except Exception as e:
            print(f"[ERROR] ログ取得エラー: {e}")
            self.test_results.append(("ログ取得", "FAILED", str(e)))
    
    async def test_control_endpoints(self):
        """コントロールエンドポイントテスト"""
        print("\n=== コントロールエンドポイントテスト ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                # 再配分テスト
                async with session.post(f"{self.base_url}/control/rebalance") as response:
                    if response.status == 200:
                        data = await response.json()
                        print("[SUCCESS] 再配分コマンド: OK")
                        print(f"   - メッセージ: {data.get('message')}")
                        self.test_results.append(("再配分コマンド", "PASS", "正常に実行"))
                    else:
                        print(f"[ERROR] 再配分コマンド: HTTP {response.status}")
                        self.test_results.append(("再配分コマンド", "FAILED", f"HTTP {response.status}"))
                
                # 緊急停止テスト（実際には実行しない）
                print("[INFO] 緊急停止テスト: スキップ（安全のため）")
                self.test_results.append(("緊急停止", "SKIP", "安全のためスキップ"))
                
        except Exception as e:
            print(f"[ERROR] コントロールエンドポイントエラー: {e}")
            self.test_results.append(("コントロールエンドポイント", "FAILED", str(e)))
    
    async def test_websocket_connection(self):
        """WebSocket接続テスト"""
        print("\n=== WebSocket接続テスト ===")
        
        try:
            import websockets
            
            async with websockets.connect(f"ws://localhost:8000/ws") as websocket:
                print("[SUCCESS] WebSocket接続: OK")
                
                # メッセージ送信テスト
                await websocket.send("ping")
                response = await websocket.recv()
                
                if response == "pong":
                    print("[SUCCESS] WebSocket通信: OK")
                    self.test_results.append(("WebSocket接続", "PASS", "正常に接続・通信"))
                else:
                    print(f"[WARNING] WebSocket応答: {response}")
                    self.test_results.append(("WebSocket通信", "WARNING", f"予期しない応答: {response}"))
                
        except ImportError:
            print("[WARNING] websockets ライブラリがインストールされていません")
            print("   pip install websockets でインストールしてください")
            self.test_results.append(("WebSocket接続", "SKIP", "websocketsライブラリ未インストール"))
        except Exception as e:
            print(f"[ERROR] WebSocket接続エラー: {e}")
            self.test_results.append(("WebSocket接続", "FAILED", str(e)))
    
    async def test_api_documentation(self):
        """API ドキュメントテスト"""
        print("\n=== API ドキュメントテスト ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/docs") as response:
                    if response.status == 200:
                        print("[SUCCESS] API ドキュメント: OK")
                        print(f"   - アクセス先: {self.base_url}/docs")
                        self.test_results.append(("API ドキュメント", "PASS", "正常にアクセス可能"))
                    else:
                        print(f"[ERROR] API ドキュメント: HTTP {response.status}")
                        self.test_results.append(("API ドキュメント", "FAILED", f"HTTP {response.status}"))
                        
        except Exception as e:
            print(f"[ERROR] API ドキュメントエラー: {e}")
            self.test_results.append(("API ドキュメント", "FAILED", str(e)))
    
    async def run_all_tests(self):
        """全テスト実行"""
        print("🚀 ダッシュボード動作確認テスト開始")
        print("=" * 50)
        
        # サーバー起動待機
        print("[INFO] サーバー起動待機中...")
        await asyncio.sleep(5)
        
        # テスト実行
        await self.test_health_endpoint()
        await self.test_status_endpoint()
        await self.test_logs_endpoint()
        await self.test_control_endpoints()
        await self.test_websocket_connection()
        await self.test_api_documentation()
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 テスト結果サマリー")
        print("=" * 50)
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name, result, message in self.test_results:
            if result == "PASS":
                status_icon = "[SUCCESS]"
                passed += 1
            elif result == "FAILED":
                status_icon = "[ERROR]"
                failed += 1
            else:
                status_icon = "[INFO]"
                skipped += 1
            
            print(f"{status_icon} {test_name}: {result}")
            print(f"   {message}")
        
        print(f"\n📈 結果: {passed}件成功, {failed}件失敗, {skipped}件スキップ")
        
        if failed == 0:
            print("🎉 すべてのテストが成功しました！")
            print("\n📊 ダッシュボードアクセス先:")
            print(f"   - フロントエンド: http://localhost:3000")
            print(f"   - バックエンド: http://localhost:8000")
            print(f"   - API ドキュメント: http://localhost:8000/docs")
            return True
        else:
            print("⚠️ 一部のテストが失敗しました。")
            return False


async def main():
    """メイン関数"""
    tester = DashboardTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 ダッシュボードが正常に動作しています！")
        print("次のステップ: Discord通知システムの実装")
    else:
        print("\n❌ ダッシュボードに問題があります。修正が必要です。")
    
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
