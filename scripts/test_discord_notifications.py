"""
Discord通知システムテストスクリプト
"""
import asyncio
import logging
import sys
import io
from datetime import datetime

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.notifications.discord import DiscordNotifier, NotificationLevel

logger = logging.getLogger(__name__)

class DiscordNotificationTester:
    """Discord通知テストクラス"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.test_results = []
    
    async def test_basic_notification(self):
        """基本通知テスト"""
        print("=== 基本通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                success = await notifier.send_notification(
                    title="テスト通知",
                    message="Discord通知システムのテストです",
                    level=NotificationLevel.INFO
                )
                
                if success:
                    print("[SUCCESS] 基本通知: OK")
                    self.test_results.append(("基本通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] 基本通知: FAILED")
                    self.test_results.append(("基本通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] 基本通知エラー: {e}")
            self.test_results.append(("基本通知", "FAILED", str(e)))
    
    async def test_system_startup(self):
        """システム起動通知テスト"""
        print("\n=== システム起動通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                success = await notifier.send_system_startup()
                
                if success:
                    print("[SUCCESS] システム起動通知: OK")
                    self.test_results.append(("システム起動通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] システム起動通知: FAILED")
                    self.test_results.append(("システム起動通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] システム起動通知エラー: {e}")
            self.test_results.append(("システム起動通知", "FAILED", str(e)))
    
    async def test_circuit_breaker_notification(self):
        """サーキットブレーカー通知テスト"""
        print("\n=== サーキットブレーカー通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                success = await notifier.send_circuit_breaker_triggered(
                    reason="API接続エラー",
                    failure_count=5
                )
                
                if success:
                    print("[SUCCESS] サーキットブレーカー通知: OK")
                    self.test_results.append(("サーキットブレーカー通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] サーキットブレーカー通知: FAILED")
                    self.test_results.append(("サーキットブレーカー通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] サーキットブレーカー通知エラー: {e}")
            self.test_results.append(("サーキットブレーカー通知", "FAILED", str(e)))
    
    async def test_daily_loss_limit_notification(self):
        """日次損失制限通知テスト"""
        print("\n=== 日次損失制限通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                success = await notifier.send_daily_loss_limit_reached(
                    current_loss=0.06,
                    limit=0.05
                )
                
                if success:
                    print("[SUCCESS] 日次損失制限通知: OK")
                    self.test_results.append(("日次損失制限通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] 日次損失制限通知: FAILED")
                    self.test_results.append(("日次損失制限通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] 日次損失制限通知エラー: {e}")
            self.test_results.append(("日次損失制限通知", "FAILED", str(e)))
    
    async def test_rebalance_notification(self):
        """再配分通知テスト"""
        print("\n=== 再配分通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                old_allocation = {"stable": 0.4, "balanced": 0.4, "aggressive": 0.2}
                new_allocation = {"stable": 0.5, "balanced": 0.3, "aggressive": 0.2}
                
                success = await notifier.send_rebalance_executed(old_allocation, new_allocation)
                
                if success:
                    print("[SUCCESS] 再配分通知: OK")
                    self.test_results.append(("再配分通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] 再配分通知: FAILED")
                    self.test_results.append(("再配分通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] 再配分通知エラー: {e}")
            self.test_results.append(("再配分通知", "FAILED", str(e)))
    
    async def test_performance_notification(self):
        """パフォーマンス通知テスト"""
        print("\n=== パフォーマンス通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                performance_data = {
                    "stable": {"win_rate": 0.65, "total_return": 0.08, "trade_count": 15},
                    "balanced": {"win_rate": 0.60, "total_return": 0.12, "trade_count": 20},
                    "aggressive": {"win_rate": 0.55, "total_return": 0.18, "trade_count": 25}
                }
                
                success = await notifier.send_performance_summary(performance_data)
                
                if success:
                    print("[SUCCESS] パフォーマンス通知: OK")
                    self.test_results.append(("パフォーマンス通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] パフォーマンス通知: FAILED")
                    self.test_results.append(("パフォーマンス通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] パフォーマンス通知エラー: {e}")
            self.test_results.append(("パフォーマンス通知", "FAILED", str(e)))
    
    async def test_error_notification(self):
        """エラー通知テスト"""
        print("\n=== エラー通知テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                success = await notifier.send_error_notification(
                    error_type="API接続エラー",
                    error_message="Bybit APIへの接続に失敗しました",
                    context={"retry_count": 3, "last_error": "Connection timeout"}
                )
                
                if success:
                    print("[SUCCESS] エラー通知: OK")
                    self.test_results.append(("エラー通知", "PASS", "正常に送信"))
                else:
                    print("[ERROR] エラー通知: FAILED")
                    self.test_results.append(("エラー通知", "FAILED", "送信失敗"))
                    
        except Exception as e:
            print(f"[ERROR] エラー通知エラー: {e}")
            self.test_results.append(("エラー通知", "FAILED", str(e)))
    
    async def test_notification_history(self):
        """通知履歴テスト"""
        print("\n=== 通知履歴テスト ===")
        
        try:
            async with DiscordNotifier(self.webhook_url) as notifier:
                # テスト通知を送信
                await notifier.send_notification(
                    title="履歴テスト",
                    message="通知履歴のテストです",
                    level=NotificationLevel.INFO
                )
                
                # 履歴取得
                history = notifier.get_notification_history(limit=5)
                
                if history:
                    print("[SUCCESS] 通知履歴: OK")
                    print(f"   - 履歴数: {len(history)}")
                    latest = history[-1]
                    print(f"   - 最新通知: {latest.get('title')}")
                    self.test_results.append(("通知履歴", "PASS", f"{len(history)}件の履歴取得"))
                else:
                    print("[ERROR] 通知履歴: FAILED")
                    self.test_results.append(("通知履歴", "FAILED", "履歴が空"))
                    
        except Exception as e:
            print(f"[ERROR] 通知履歴エラー: {e}")
            self.test_results.append(("通知履歴", "FAILED", str(e)))
    
    async def run_all_tests(self):
        """全テスト実行"""
        print("🚀 Discord通知システムテスト開始")
        print("=" * 50)
        
        if not self.webhook_url or self.webhook_url == "YOUR_WEBHOOK_URL_HERE":
            print("[WARNING] Discord Webhook URLが設定されていません")
            print("   環境変数 DISCORD_WEBHOOK_URL を設定してください")
            print("   または、テスト用のWebhook URLを設定してください")
            return False
        
        # テスト実行
        await self.test_basic_notification()
        await asyncio.sleep(1)  # 通知間隔
        
        await self.test_system_startup()
        await asyncio.sleep(1)
        
        await self.test_circuit_breaker_notification()
        await asyncio.sleep(1)
        
        await self.test_daily_loss_limit_notification()
        await asyncio.sleep(1)
        
        await self.test_rebalance_notification()
        await asyncio.sleep(1)
        
        await self.test_performance_notification()
        await asyncio.sleep(1)
        
        await self.test_error_notification()
        await asyncio.sleep(1)
        
        await self.test_notification_history()
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 テスト結果サマリー")
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
        
        print(f"\n📈 結果: {passed}件成功, {failed}件失敗")
        
        if failed == 0:
            print("🎉 すべてのテストが成功しました！")
            print("\n📱 Discordチャンネルで通知を確認してください")
            return True
        else:
            print("⚠️ 一部のテストが失敗しました。")
            return False


async def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Webhook URL取得（環境変数またはテスト用）
    webhook_url = "YOUR_WEBHOOK_URL_HERE"  # 実際のWebhook URLに置き換えてください
    
    if webhook_url == "YOUR_WEBHOOK_URL_HERE":
        print("[INFO] テスト用Webhook URLが設定されていません")
        print("   実際のDiscord Webhook URLを設定してテストしてください")
        print("   設定方法:")
        print("   1. DiscordサーバーでWebhookを作成")
        print("   2. Webhook URLをコピー")
        print("   3. このスクリプトのwebhook_url変数に設定")
        return False
    
    tester = DiscordNotificationTester(webhook_url)
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 Discord通知システムが正常に動作します！")
        print("次のステップ: マスターボットとの統合テスト")
    else:
        print("\n❌ Discord通知システムに問題があります。修正が必要です。")
    
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
