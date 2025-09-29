"""
自己進化型AIポートフォリオ自動売買システム - メインエントリーポイント
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional
import logging

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from src.core import setup_logging, config, db_manager, system_logger
from src.api import BybitClient, GeminiClient, DiscordClient

logger = logging.getLogger(__name__)


class TradingSystem:
    """取引システムのメインクラス"""
    
    def __init__(self):
        self.is_running = False
        self.tasks: list = []
        
    async def initialize(self) -> None:
        """システムを初期化"""
        try:
            # ログ設定を初期化
            setup_logging()
            logger.info("ログシステムを初期化しました")
            
            # 設定の妥当性を検証
            if not config.validate_config():
                raise Exception("設定の妥当性検証に失敗しました")
            
            # データベースを初期化
            await db_manager.initialize()
            logger.info("データベースを初期化しました")
            
            # システム起動ログ
            system_logger.log_startup({
                "system_name": config.system.name,
                "version": config.system.version,
                "environment": config.system.environment
            })
            
            logger.info("システムの初期化が完了しました")
            
        except Exception as e:
            logger.error(f"システムの初期化に失敗しました: {e}")
            raise
    
    async def start(self) -> None:
        """システムを開始"""
        try:
            await self.initialize()
            
            self.is_running = True
            logger.info("取引システムを開始しました")
            
            # メインループを開始
            await self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("キーボード割り込みを受信しました")
        except Exception as e:
            logger.error(f"システム実行中にエラーが発生しました: {e}")
        finally:
            await self.shutdown()
    
    async def _main_loop(self) -> None:
        """メインループ"""
        while self.is_running:
            try:
                # システムのヘルスチェック
                await self._health_check()
                
                # メインループの処理をここに追加
                # TODO: ボットの実行、監視、最適化などの処理
                
                # 1秒待機
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"メインループでエラーが発生しました: {e}")
                await asyncio.sleep(5)  # エラー時は5秒待機
    
    async def _health_check(self) -> None:
        """ヘルスチェック"""
        try:
            # データベース接続の確認
            async with db_manager.get_session() as session:
                await session.execute("SELECT 1")
            
            # API接続の確認
            async with BybitClient() as bybit:
                await bybit.get_ticker("BTCUSDT")
            
            # ヘルスチェックログ（5分ごと）
            if hasattr(self, '_last_health_log'):
                import time
                if time.time() - self._last_health_log > 300:  # 5分
                    system_logger.log_health_check({
                        "status": "HEALTHY",
                        "database": "CONNECTED",
                        "bybit_api": "CONNECTED"
                    })
                    self._last_health_log = time.time()
            else:
                import time
                self._last_health_log = time.time()
                
        except Exception as e:
            logger.warning(f"ヘルスチェックで問題を検出しました: {e}")
            system_logger.log_health_check({
                "status": "WARNING",
                "error": str(e)
            })
    
    async def shutdown(self) -> None:
        """システムをシャットダウン"""
        try:
            self.is_running = False
            
            # 実行中のタスクをキャンセル
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # データベース接続を閉じる
            await db_manager.close()
            
            # シャットダウンログ
            system_logger.log_shutdown({
                "shutdown_time": "正常終了"
            })
            
            logger.info("システムを正常にシャットダウンしました")
            
        except Exception as e:
            logger.error(f"シャットダウン中にエラーが発生しました: {e}")


def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info(f"シグナル {signum} を受信しました")
    sys.exit(0)


async def main():
    """メイン関数"""
    # シグナルハンドラーを設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 取引システムを開始
    system = TradingSystem()
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nシステムを終了します...")
    except Exception as e:
        print(f"システムエラー: {e}")
        sys.exit(1)
