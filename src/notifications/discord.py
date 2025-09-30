"""
Discord通知システム
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

logger = logging.getLogger(__name__)

class NotificationLevel(Enum):
    """通知レベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class DiscordNotifier:
    """Discord通知クラス"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.notification_history: List[Dict[str, Any]] = []
        
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()
    
    def _get_color(self, level: NotificationLevel) -> int:
        """通知レベルに応じた色を取得"""
        colors = {
            NotificationLevel.INFO: 0x00ff00,      # 緑
            NotificationLevel.WARNING: 0xffaa00,   # オレンジ
            NotificationLevel.ERROR: 0xff0000,     # 赤
            NotificationLevel.CRITICAL: 0x8b0000   # ダークレッド
        }
        return colors.get(level, 0x808080)  # デフォルトはグレー
    
    def _get_emoji(self, level: NotificationLevel) -> str:
        """通知レベルに応じた絵文字を取得"""
        emojis = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨"
        }
        return emojis.get(level, "📢")
    
    async def send_notification(
        self, 
        title: str, 
        message: str, 
        level: NotificationLevel = NotificationLevel.INFO,
        fields: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """Discord通知を送信"""
        if not self.session:
            logger.error("Discord session not initialized")
            return False
        
        try:
            # タイムスタンプ設定
            if timestamp is None:
                timestamp = datetime.now()
            
            # 通知履歴に記録
            notification = {
                "timestamp": timestamp.isoformat(),
                "level": level.value,
                "title": title,
                "message": message,
                "fields": fields or []
            }
            self.notification_history.append(notification)
            
            # 履歴制限（最新100件）
            if len(self.notification_history) > 100:
                self.notification_history.pop(0)
            
            # Discord Webhook用のペイロード作成
            embed = {
                "title": f"{self._get_emoji(level)} {title}",
                "description": message,
                "color": self._get_color(level),
                "timestamp": timestamp.isoformat(),
                "footer": {
                    "text": "AI Trading Bot"
                }
            }
            
            # フィールド追加
            if fields:
                embed["fields"] = fields
            
            payload = {
                "embeds": [embed],
                "username": "Trading Bot",
                "avatar_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            }
            
            # Discord Webhook送信
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 204:
                    logger.info(f"Discord通知送信成功: {title}")
                    return True
                else:
                    logger.error(f"Discord通知送信失敗: HTTP {response.status}")
                    response_text = await response.text()
                    logger.error(f"Response: {response_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Discord通知送信エラー: {e}")
            return False
    
    async def send_system_startup(self) -> bool:
        """システム起動通知"""
        return await self.send_notification(
            title="システム起動",
            message="AI Trading Bot が起動しました",
            level=NotificationLevel.INFO,
            fields=[
                {"name": "起動時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                {"name": "ステータス", "value": "稼働中", "inline": True}
            ]
        )
    
    async def send_system_shutdown(self) -> bool:
        """システム停止通知"""
        return await self.send_notification(
            title="システム停止",
            message="AI Trading Bot が停止しました",
            level=NotificationLevel.WARNING,
            fields=[
                {"name": "停止時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                {"name": "ステータス", "value": "停止", "inline": True}
            ]
        )
    
    async def send_circuit_breaker_triggered(self, reason: str, failure_count: int) -> bool:
        """サーキットブレーカー発動通知"""
        return await self.send_notification(
            title="サーキットブレーカー発動",
            message=f"連続失敗によりサーキットブレーカーが発動しました",
            level=NotificationLevel.CRITICAL,
            fields=[
                {"name": "理由", "value": reason, "inline": False},
                {"name": "失敗回数", "value": str(failure_count), "inline": True},
                {"name": "発動時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
            ]
        )
    
    async def send_daily_loss_limit_reached(self, current_loss: float, limit: float) -> bool:
        """日次損失制限到達通知"""
        return await self.send_notification(
            title="日次損失制限到達",
            message=f"日次損失が制限値に達しました",
            level=NotificationLevel.CRITICAL,
            fields=[
                {"name": "現在の損失", "value": f"{current_loss:.2%}", "inline": True},
                {"name": "制限値", "value": f"{limit:.2%}", "inline": True},
                {"name": "到達時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
            ]
        )
    
    async def send_rebalance_executed(self, old_allocation: Dict[str, float], new_allocation: Dict[str, float]) -> bool:
        """再配分実行通知"""
        # 配分変更の詳細を作成
        allocation_changes = []
        for bot_name in old_allocation.keys():
            old_ratio = old_allocation.get(bot_name, 0)
            new_ratio = new_allocation.get(bot_name, 0)
            change = new_ratio - old_ratio
            
            if abs(change) > 0.01:  # 1%以上の変更のみ表示
                allocation_changes.append(f"{bot_name}: {old_ratio:.1%} → {new_ratio:.1%} ({change:+.1%})")
        
        return await self.send_notification(
            title="資金再配分実行",
            message="マスターボットによる資金再配分が実行されました",
            level=NotificationLevel.INFO,
            fields=[
                {"name": "配分変更", "value": "\n".join(allocation_changes) if allocation_changes else "変更なし", "inline": False},
                {"name": "実行時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
            ]
        )
    
    async def send_performance_summary(self, performance_data: Dict[str, Any]) -> bool:
        """パフォーマンスサマリー通知"""
        fields = []
        
        for bot_name, data in performance_data.items():
            fields.append({
                "name": f"{bot_name.title()} Bot",
                "value": f"勝率: {data.get('win_rate', 0):.1%}\nリターン: {data.get('total_return', 0):.1%}\n取引数: {data.get('trade_count', 0)}",
                "inline": True
            })
        
        return await self.send_notification(
            title="パフォーマンスサマリー",
            message="ボット別パフォーマンスの更新",
            level=NotificationLevel.INFO,
            fields=fields
        )
    
    async def send_error_notification(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """エラー通知"""
        fields = [
            {"name": "エラータイプ", "value": error_type, "inline": True},
            {"name": "発生時刻", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True}
        ]
        
        if context:
            for key, value in context.items():
                fields.append({"name": key, "value": str(value), "inline": True})
        
        return await self.send_notification(
            title="システムエラー",
            message=error_message,
            level=NotificationLevel.ERROR,
            fields=fields
        )
    
    def get_notification_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """通知履歴取得"""
        return self.notification_history[-limit:] if self.notification_history else []


class NotificationManager:
    """通知管理クラス"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.notifier: Optional[DiscordNotifier] = None
        self.is_enabled = bool(webhook_url)
        
    async def initialize(self):
        """通知システム初期化"""
        if self.is_enabled:
            self.notifier = DiscordNotifier(self.webhook_url)
            await self.notifier.__aenter__()
            
            # 起動通知
            await self.notifier.send_system_startup()
            logger.info("Discord通知システム初期化完了")
        else:
            logger.info("Discord通知システム無効（Webhook URL未設定）")
    
    async def shutdown(self):
        """通知システム終了"""
        if self.notifier:
            # 停止通知
            await self.notifier.send_system_shutdown()
            await self.notifier.__aexit__(None, None, None)
            logger.info("Discord通知システム終了")
    
    async def notify_circuit_breaker(self, reason: str, failure_count: int):
        """サーキットブレーカー通知"""
        if self.notifier:
            await self.notifier.send_circuit_breaker_triggered(reason, failure_count)
    
    async def notify_daily_loss_limit(self, current_loss: float, limit: float):
        """日次損失制限通知"""
        if self.notifier:
            await self.notifier.send_daily_loss_limit_reached(current_loss, limit)
    
    async def notify_rebalance(self, old_allocation: Dict[str, float], new_allocation: Dict[str, float]):
        """再配分通知"""
        if self.notifier:
            await self.notifier.send_rebalance_executed(old_allocation, new_allocation)
    
    async def notify_performance(self, performance_data: Dict[str, Any]):
        """パフォーマンス通知"""
        if self.notifier:
            await self.notifier.send_performance_summary(performance_data)
    
    async def notify_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """エラー通知"""
        if self.notifier:
            await self.notifier.send_error_notification(error_type, error_message, context)


# テスト用のメイン関数
async def test_discord_notifications():
    """Discord通知テスト"""
    print("🚀 Discord通知システムテスト開始")
    print("=" * 50)
    
    # テスト用Webhook URL（実際のURLに置き換えてください）
    test_webhook_url = "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"
    
    if test_webhook_url == "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE":
        print("[WARNING] テスト用Webhook URLが設定されていません")
        print("   Discord通知のテストをスキップします")
        return False
    
    try:
        async with DiscordNotifier(test_webhook_url) as notifier:
            # 各種通知テスト
            print("[INFO] システム起動通知テスト...")
            await notifier.send_system_startup()
            await asyncio.sleep(1)
            
            print("[INFO] サーキットブレーカー通知テスト...")
            await notifier.send_circuit_breaker_triggered("API接続エラー", 5)
            await asyncio.sleep(1)
            
            print("[INFO] 日次損失制限通知テスト...")
            await notifier.send_daily_loss_limit_reached(0.06, 0.05)
            await asyncio.sleep(1)
            
            print("[INFO] 再配分通知テスト...")
            old_allocation = {"stable": 0.4, "balanced": 0.4, "aggressive": 0.2}
            new_allocation = {"stable": 0.5, "balanced": 0.3, "aggressive": 0.2}
            await notifier.send_rebalance_executed(old_allocation, new_allocation)
            await asyncio.sleep(1)
            
            print("[INFO] パフォーマンス通知テスト...")
            performance_data = {
                "stable": {"win_rate": 0.65, "total_return": 0.08, "trade_count": 15},
                "balanced": {"win_rate": 0.60, "total_return": 0.12, "trade_count": 20},
                "aggressive": {"win_rate": 0.55, "total_return": 0.18, "trade_count": 25}
            }
            await notifier.send_performance_summary(performance_data)
            await asyncio.sleep(1)
            
            print("[INFO] エラー通知テスト...")
            await notifier.send_error_notification(
                "API接続エラー",
                "Bybit APIへの接続に失敗しました",
                {"retry_count": 3, "last_error": "Connection timeout"}
            )
            
            print("\n[SUCCESS] すべての通知テストが完了しました")
            print("Discordチャンネルで通知を確認してください")
            
    except Exception as e:
        print(f"[ERROR] Discord通知テストエラー: {e}")
        return False
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        success = asyncio.run(test_discord_notifications())
        if success:
            print("\n🎉 Discord通知システムが正常に動作します！")
        else:
            print("\n❌ Discord通知システムに問題があります。")
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
