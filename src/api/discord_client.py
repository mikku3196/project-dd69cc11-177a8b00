"""
自己進化型AIポートフォリオ自動売買システム - Discord通知クライアント
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
import aiohttp
import logging
from datetime import datetime

from ..core.config import config
from ..core.exceptions import DiscordNotificationError

logger = logging.getLogger(__name__)


class DiscordClient:
    """Discord通知クライアント"""
    
    def __init__(self):
        self.webhook_url = config.discord.webhook_url
        self.bot_token = config.discord.bot_token
        self.timeout = 30
        
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
    
    async def _send_webhook(self, payload: Dict[str, Any]) -> None:
        """Webhookでメッセージを送信"""
        if not self.webhook_url:
            logger.warning("Discord Webhook URLが設定されていません")
            return
        
        if not self.session:
            raise DiscordNotificationError("セッションが初期化されていません")
        
        try:
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status not in [200, 204]:
                    error_text = await response.text()
                    raise DiscordNotificationError(f"Discord Webhook エラー: {response.status} - {error_text}")
                
                logger.info("Discord通知を送信しました")
                
        except aiohttp.ClientError as e:
            raise DiscordNotificationError(f"ネットワークエラー: {e}")
        except Exception as e:
            raise DiscordNotificationError(f"予期しないエラー: {e}")
    
    async def send_trade_notification(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        bot_name: str,
        confidence: Optional[float] = None,
        reason: Optional[str] = None
    ) -> None:
        """取引通知を送信"""
        
        # アクションに応じて絵文字と色を設定
        if action == "BUY":
            emoji = "🟢"
            color = 0x00ff00  # 緑
        elif action == "SELL":
            emoji = "🔴"
            color = 0xff0000  # 赤
        else:
            emoji = "🟡"
            color = 0xffff00  # 黄
        
        embed = {
            "title": f"{emoji} 取引実行通知",
            "color": color,
            "fields": [
                {
                    "name": "通貨ペア",
                    "value": symbol,
                    "inline": True
                },
                {
                    "name": "アクション",
                    "value": action,
                    "inline": True
                },
                {
                    "name": "数量",
                    "value": f"{quantity:.6f}",
                    "inline": True
                },
                {
                    "name": "価格",
                    "value": f"${price:.2f}",
                    "inline": True
                },
                {
                    "name": "ボット",
                    "value": bot_name,
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "自己進化型AIポートフォリオ自動売買システム"
            }
        }
        
        if confidence is not None:
            embed["fields"].append({
                "name": "信頼度",
                "value": f"{confidence:.2%}",
                "inline": True
            })
        
        if reason:
            embed["fields"].append({
                "name": "判断理由",
                "value": reason[:1024],  # Discordの制限
                "inline": False
            })
        
        payload = {
            "embeds": [embed]
        }
        
        await self._send_webhook(payload)
    
    async def send_performance_report(
        self,
        bot_name: str,
        period: str,
        metrics: Dict[str, Any]
    ) -> None:
        """パフォーマンスレポートを送信"""
        
        # パフォーマンスに応じて色を設定
        total_return = metrics.get('total_return', 0)
        if total_return > 0:
            color = 0x00ff00  # 緑
            emoji = "📈"
        else:
            color = 0xff0000  # 赤
            emoji = "📉"
        
        embed = {
            "title": f"{emoji} {bot_name} - {period}パフォーマンスレポート",
            "color": color,
            "fields": [
                {
                    "name": "総リターン",
                    "value": f"{total_return:.2%}",
                    "inline": True
                },
                {
                    "name": "シャープレシオ",
                    "value": f"{metrics.get('sharpe_ratio', 0):.2f}",
                    "inline": True
                },
                {
                    "name": "最大ドローダウン",
                    "value": f"{metrics.get('max_drawdown', 0):.2%}",
                    "inline": True
                },
                {
                    "name": "勝率",
                    "value": f"{metrics.get('win_rate', 0):.2%}",
                    "inline": True
                },
                {
                    "name": "プロフィットファクター",
                    "value": f"{metrics.get('profit_factor', 0):.2f}",
                    "inline": True
                },
                {
                    "name": "総取引数",
                    "value": str(metrics.get('total_trades', 0)),
                    "inline": True
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "自己進化型AIポートフォリオ自動売買システム"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        await self._send_webhook(payload)
    
    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        module: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """エラー通知を送信"""
        
        embed = {
            "title": "🚨 システムエラー通知",
            "color": 0xff0000,  # 赤
            "fields": [
                {
                    "name": "エラータイプ",
                    "value": error_type,
                    "inline": True
                },
                {
                    "name": "モジュール",
                    "value": module,
                    "inline": True
                },
                {
                    "name": "エラーメッセージ",
                    "value": error_message[:1024],  # Discordの制限
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "自己進化型AIポートフォリオ自動売買システム"
            }
        }
        
        if details:
            embed["fields"].append({
                "name": "詳細情報",
                "value": json.dumps(details, ensure_ascii=False, indent=2)[:1024],
                "inline": False
            })
        
        payload = {
            "embeds": [embed]
        }
        
        await self._send_webhook(payload)
    
    async def send_optimization_notification(
        self,
        bot_name: str,
        old_params: Dict[str, Any],
        new_params: Dict[str, Any],
        improvement: float
    ) -> None:
        """最適化通知を送信"""
        
        embed = {
            "title": "🔧 パラメータ最適化完了",
            "color": 0x0099ff,  # 青
            "fields": [
                {
                    "name": "ボット",
                    "value": bot_name,
                    "inline": True
                },
                {
                    "name": "改善予測",
                    "value": f"{improvement:.2%}",
                    "inline": True
                },
                {
                    "name": "更新されたパラメータ",
                    "value": json.dumps(new_params, ensure_ascii=False, indent=2)[:1024],
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "自己進化型AIポートフォリオ自動売買システム"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        await self._send_webhook(payload)
    
    async def send_system_status(
        self,
        status: str,
        details: Dict[str, Any]
    ) -> None:
        """システムステータス通知を送信"""
        
        # ステータスに応じて色と絵文字を設定
        if status == "STARTED":
            emoji = "🟢"
            color = 0x00ff00
        elif status == "STOPPED":
            emoji = "🔴"
            color = 0xff0000
        elif status == "WARNING":
            emoji = "🟡"
            color = 0xffff00
        else:
            emoji = "ℹ️"
            color = 0x0099ff
        
        embed = {
            "title": f"{emoji} システムステータス: {status}",
            "color": color,
            "fields": [],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "自己進化型AIポートフォリオ自動売買システム"
            }
        }
        
        # 詳細情報をフィールドに追加
        for key, value in details.items():
            embed["fields"].append({
                "name": key,
                "value": str(value)[:1024],
                "inline": True
            })
        
        payload = {
            "embeds": [embed]
        }
        
        await self._send_webhook(payload)
    
    async def send_circuit_breaker_notification(
        self,
        trigger_reason: str,
        actions_taken: List[str],
        recovery_time: Optional[str] = None
    ) -> None:
        """サーキットブレーカー通知を送信"""
        
        embed = {
            "title": "⚡ サーキットブレーカー発動",
            "color": 0xff0000,  # 赤
            "fields": [
                {
                    "name": "発動理由",
                    "value": trigger_reason,
                    "inline": False
                },
                {
                    "name": "実行されたアクション",
                    "value": "\n".join(f"• {action}" for action in actions_taken),
                    "inline": False
                }
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "自己進化型AIポートフォリオ自動売買システム"
            }
        }
        
        if recovery_time:
            embed["fields"].append({
                "name": "予想復旧時間",
                "value": recovery_time,
                "inline": True
            })
        
        payload = {
            "embeds": [embed]
        }
        
        await self._send_webhook(payload)
