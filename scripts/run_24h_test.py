"""
24時間稼働テスト用メインスクリプト
テストネット環境での継続稼働と監視
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import signal
import os

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.core.config import config
from src.utils.circuit_breaker import circuit_breaker
from src.dashboard.monitoring import health_check
from scripts.setup_24h_logging import setup_24h_test_logging

logger = logging.getLogger(__name__)

class Testnet24hRunner:
    """24時間稼働テストランナー"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.running = True
        self.test_duration = timedelta(hours=24)
        self.health_check_interval = 60  # 1分間隔
        self.metrics_interval = 300      # 5分間隔
        self.circuit_breaker_check_interval = 30  # 30秒間隔
        
    async def start_24h_test(self):
        """24時間稼働テストを開始"""
        logger.info("=== テストネット24時間稼働テスト開始 ===")
        logger.info(f"開始時刻: {self.start_time}")
        logger.info(f"予定終了時刻: {self.start_time + self.test_duration}")
        
        # 非同期タスクを並行実行
        tasks = [
            asyncio.create_task(self.health_monitor()),
            asyncio.create_task(self.metrics_collector()),
            asyncio.create_task(self.circuit_breaker_monitor()),
            asyncio.create_task(self.timeout_monitor())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("ユーザーによる中断")
        except Exception as e:
            logger.error(f"予期しないエラー: {e}")
        finally:
            await self.cleanup()
    
    async def health_monitor(self):
        """ヘルスチェック監視"""
        logger.info("ヘルスチェック監視開始")
        
        while self.running:
            try:
                health = await health_check()
                logger.info(f"ヘルスチェック: {health['status']}")
                
                # サーキットブレーカーの状態を特別に記録
                cb_status = health['components']['circuit_breaker']
                if cb_status['is_open']:
                    logger.warning(f"サーキットブレーカーOPEN: {cb_status}")
                else:
                    logger.debug(f"サーキットブレーカーCLOSED: {cb_status}")
                    
            except Exception as e:
                logger.error(f"ヘルスチェックエラー: {e}")
            
            await asyncio.sleep(self.health_check_interval)
    
    async def metrics_collector(self):
        """メトリクス収集"""
        logger.info("メトリクス収集開始")
        
        while self.running:
            try:
                # 簡易メトリクス収集
                cb_status = circuit_breaker.get_status()
                logger.info(f"メトリクス収集: Circuit Breaker = {cb_status}")
                
            except Exception as e:
                logger.error(f"メトリクス収集エラー: {e}")
            
            await asyncio.sleep(self.metrics_interval)
    
    async def circuit_breaker_monitor(self):
        """サーキットブレーカー監視"""
        logger.info("サーキットブレーカー監視開始")
        
        while self.running:
            try:
                cb_status = circuit_breaker.get_status()
                
                # 状態変化を記録
                if cb_status['state'] == 'OPEN':
                    logger.warning(f"サーキットブレーカーOPEN状態継続: {cb_status}")
                elif cb_status['state'] == 'HALF_OPEN':
                    logger.info(f"サーキットブレーカーHALF-OPEN状態: {cb_status}")
                else:
                    logger.debug(f"サーキットブレーカーCLOSED状態: {cb_status}")
                
            except Exception as e:
                logger.error(f"サーキットブレーカー監視エラー: {e}")
            
            await asyncio.sleep(self.circuit_breaker_check_interval)
    
    async def timeout_monitor(self):
        """タイムアウト監視（24時間経過で自動終了）"""
        logger.info("タイムアウト監視開始")
        
        while self.running:
            elapsed = datetime.now() - self.start_time
            
            if elapsed >= self.test_duration:
                logger.info(f"24時間経過 - テスト終了: {elapsed}")
                self.running = False
                break
            
            # 残り時間をログ出力（1時間ごと）
            remaining = self.test_duration - elapsed
            if int(remaining.total_seconds()) % 3600 == 0:
                logger.info(f"残り時間: {remaining}")
            
            await asyncio.sleep(60)  # 1分間隔でチェック
    
    async def cleanup(self):
        """クリーンアップ処理"""
        logger.info("=== 24時間稼働テスト終了 ===")
        
        # 最終ステータス取得
        try:
            final_health = await health_check()
            logger.info(f"最終ヘルスチェック: {final_health}")
        except Exception as e:
            logger.error(f"最終ヘルスチェックエラー: {e}")
        
        # テスト結果サマリー
        total_duration = datetime.now() - self.start_time
        logger.info(f"総稼働時間: {total_duration}")
        logger.info(f"サーキットブレーカー最終状態: {circuit_breaker.get_status()}")


def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info(f"シグナル受信: {signum}")
    global runner
    runner.running = False


async def main():
    """メイン関数"""
    # ログ設定
    log_file = setup_24h_test_logging()
    logger.info(f"ログファイル: {log_file}")
    
    # シグナルハンドラー設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # テストランナー開始
    global runner
    runner = Testnet24hRunner()
    await runner.start_24h_test()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        sys.exit(1)
