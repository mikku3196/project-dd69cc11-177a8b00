"""
統合テストスクリプト - ダッシュボード + 通知システム
"""
import asyncio
import aiohttp
import json
import time
import sys
import io
from datetime import datetime
from pathlib import Path

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.bots.master_bot import MasterBot
from src.notifications.discord import NotificationManager

class IntegratedTester:
    """統合テストクラス"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = []
        self.master_bot = None
        self.notification_manager = None
    
    async def test_server_startup(self):
        """サーバー起動テスト"""
        print("=== サーバー起動テスト ===")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("[SUCCESS] サーバー起動: OK")
                        print(f"   - ステータス: {data.get('status')}")
                        print(f"   - マスターボット: {data.get('master_bot_running')}")
                        self.test_results.append(("サーバー起動", "PASS", "正常に起動"))
                        return True
                    else:
                        print(f"[ERROR] サーバー起動: HTTP {response.status}")
                        self.test_results.append(("サーバー起動", "FAILED", f"HTTP {response.status}"))
                        return False
        except Exception as e:
            print(f"[ERROR] サーバー起動エラー: {e}")
            self.test_results.append(("サーバー起動", "FAILED", str(e)))
            return False
    
    async def test_master_bot_initialization(self):
        """マスターボット初期化テスト"""
        print("\n=== マスターボット初期化テスト ===")
        
        try:
            config = {
                'risk_level': 'safe',
                'rebalance_interval_days': 30,
                'discord_webhook_url': ''  # テスト用は空文字
            }
            
            self.master_bot = MasterBot(config)
            
            # サブボット初期化
            await self.master_bot._initialize_sub_bots()
            
            # 状態確認
            status = self.master_bot.get_status()
            
            print("[SUCCESS] マスターボット初期化: OK")
            print(f"   - 稼働状態: {status.get('is_running')}")
            print(f"   - リスクレベル: {status.get('risk_level')}")
            print(f"   - 配分: {status.get('allocation')}")
            
            self.test_results.append(("マスターボット初期化", "PASS", "正常に初期化"))
            return True
            
        except Exception as e:
            print(f"[ERROR] マスターボット初期化エラー: {e}")
            self.test_results.append(("マスターボット初期化", "FAILED", str(e)))
            return False
    
    async def test_notification_system(self):
        """通知システムテスト"""
        print("\n=== 通知システムテスト ===")
        
        try:
            # 通知マネージャー初期化（テスト用）
            self.notification_manager = NotificationManager('')
            
            # 初期化テスト
            await self.notification_manager.initialize()
            
            print("[SUCCESS] 通知システム初期化: OK")
            print("   - Discord通知: 無効（テスト用）")
            
            self.test_results.append(("通知システム", "PASS", "正常に初期化"))
            return True
            
        except Exception as e:
            print(f"[ERROR] 通知システムエラー: {e}")
            self.test_results.append(("通知システム", "FAILED", str(e)))
            return False
    
    async def test_dashboard_endpoints(self):
        """ダッシュボードエンドポイントテスト"""
        print("\n=== ダッシュボードエンドポイントテスト ===")
        
        endpoints = [
            ("/status", "ステータス取得"),
            ("/logs", "ログ取得"),
            ("/docs", "API ドキュメント")
        ]
        
        success_count = 0
        
        try:
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
            
            if success_count >= len(endpoints) * 0.8:  # 80%以上成功
                print(f"[SUCCESS] エンドポイントテスト: {success_count}/{len(endpoints)} 成功")
                self.test_results.append(("ダッシュボードエンドポイント", "PASS", f"{success_count}/{len(endpoints)} 成功"))
                return True
            else:
                print(f"[ERROR] エンドポイントテスト: {success_count}/{len(endpoints)} 成功")
                self.test_results.append(("ダッシュボードエンドポイント", "FAILED", f"{success_count}/{len(endpoints)} 成功"))
                return False
                
        except Exception as e:
            print(f"[ERROR] エンドポイントテストエラー: {e}")
            self.test_results.append(("ダッシュボードエンドポイント", "FAILED", str(e)))
            return False
    
    async def test_master_bot_operations(self):
        """マスターボット操作テスト"""
        print("\n=== マスターボット操作テスト ===")
        
        try:
            if not self.master_bot:
                print("[ERROR] マスターボットが初期化されていません")
                self.test_results.append(("マスターボット操作", "FAILED", "初期化されていない"))
                return False
            
            # パフォーマンス収集テスト
            await self.master_bot._collect_performance()
            print("[SUCCESS] パフォーマンス収集: OK")
            
            # リスク監視テスト
            await self.master_bot._monitor_risk()
            print("[SUCCESS] リスク監視: OK")
            
            # ボットスコア計算テスト
            scores = self.master_bot._calculate_bot_scores()
            print(f"[SUCCESS] ボットスコア計算: OK ({len(scores)} ボット)")
            
            # 配分計算テスト
            new_allocation = self.master_bot._calculate_new_allocation(scores)
            print(f"[SUCCESS] 配分計算: OK")
            
            self.test_results.append(("マスターボット操作", "PASS", "すべての操作が正常"))
            return True
            
        except Exception as e:
            print(f"[ERROR] マスターボット操作エラー: {e}")
            self.test_results.append(("マスターボット操作", "FAILED", str(e)))
            return False
    
    async def test_integration_workflow(self):
        """統合ワークフローテスト"""
        print("\n=== 統合ワークフローテスト ===")
        
        try:
            # 1. マスターボット状態取得
            status = self.master_bot.get_status()
            
            # 2. ダッシュボードAPI経由で状態取得
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/status") as response:
                    if response.status == 200:
                        dashboard_status = await response.json()
                        print("[SUCCESS] ダッシュボード状態取得: OK")
                    else:
                        print(f"[ERROR] ダッシュボード状態取得: HTTP {response.status}")
                        return False
            
            # 3. 状態の整合性チェック
            if (status.get('is_running') == dashboard_status.get('is_running') and
                status.get('risk_level') == dashboard_status.get('risk_level')):
                print("[SUCCESS] 状態整合性: OK")
            else:
                print("[WARNING] 状態整合性: 不一致")
            
            # 4. ログ取得テスト
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/logs?limit=5") as response:
                    if response.status == 200:
                        logs = await response.json()
                        print(f"[SUCCESS] ログ取得: OK ({len(logs)} 件)")
                    else:
                        print(f"[ERROR] ログ取得: HTTP {response.status}")
                        return False
            
            self.test_results.append(("統合ワークフロー", "PASS", "すべてのワークフローが正常"))
            return True
            
        except Exception as e:
            print(f"[ERROR] 統合ワークフローエラー: {e}")
            self.test_results.append(("統合ワークフロー", "FAILED", str(e)))
            return False
    
    async def cleanup(self):
        """クリーンアップ"""
        print("\n=== クリーンアップ ===")
        
        try:
            if self.master_bot:
                await self.master_bot.stop()
                print("[SUCCESS] マスターボット停止: OK")
            
            if self.notification_manager:
                await self.notification_manager.shutdown()
                print("[SUCCESS] 通知システム終了: OK")
            
            self.test_results.append(("クリーンアップ", "PASS", "正常に終了"))
            
        except Exception as e:
            print(f"[ERROR] クリーンアップエラー: {e}")
            self.test_results.append(("クリーンアップ", "FAILED", str(e)))
    
    async def run_all_tests(self):
        """全テスト実行"""
        print("[INFO] 統合テスト開始")
        print("=" * 50)
        
        # テスト実行
        tests = [
            self.test_server_startup,
            self.test_master_bot_initialization,
            self.test_notification_system,
            self.test_dashboard_endpoints,
            self.test_master_bot_operations,
            self.test_integration_workflow
        ]
        
        passed_tests = 0
        
        for test in tests:
            try:
                if await test():
                    passed_tests += 1
                await asyncio.sleep(1)  # テスト間隔
            except Exception as e:
                print(f"[ERROR] テスト実行エラー: {e}")
        
        # クリーンアップ
        await self.cleanup()
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("[INFO] 統合テスト結果サマリー")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result, message in self.test_results:
            if result == "PASS":
                status_icon = "[SUCCESS]"
                passed += 1
            else:
                status_icon = "[ERROR]"
                failed += 1
            
            print(f"{status_icon} {test_name}: {result}")
            print(f"   {message}")
        
        print(f"\n[INFO] 結果: {passed}件成功, {failed}件失敗")
        print(f"[INFO] テスト通過率: {passed_tests}/{len(tests)} ({passed_tests/len(tests)*100:.1f}%)")
        
        if failed == 0:
            print("[SUCCESS] すべての統合テストが成功しました！")
            print("\n[SUCCESS] システム統合が正常に動作しています")
            print("[INFO] ダッシュボード: http://localhost:8000")
            print("[INFO] API ドキュメント: http://localhost:8000/docs")
            return True
        else:
            print("[WARNING] 一部のテストが失敗しました。")
            return False


async def main():
    """メイン関数"""
    tester = IntegratedTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n[SUCCESS] 統合システムが正常に動作しています！")
        print("次のステップ: バックテストエンジンの実装")
    else:
        print("\n[ERROR] 統合システムに問題があります。修正が必要です。")
    
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
