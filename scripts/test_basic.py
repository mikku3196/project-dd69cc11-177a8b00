"""
簡易統合テストスクリプト
"""
import asyncio
import aiohttp
import sys
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

async def test_basic_functionality():
    """基本機能テスト"""
    print("=== 基本機能テスト ===")
    
    # 1. マスターボットテスト
    try:
        from src.bots.master_bot import MasterBot
        
        config = {
            'risk_level': 'safe',
            'rebalance_interval_days': 30,
            'discord_webhook_url': ''
        }
        
        master_bot = MasterBot(config)
        await master_bot._initialize_sub_bots()
        
        status = master_bot.get_status()
        print(f"[SUCCESS] マスターボット: OK")
        print(f"   - 稼働状態: {status.get('is_running')}")
        print(f"   - リスクレベル: {status.get('risk_level')}")
        
        await master_bot.stop()
        
    except Exception as e:
        print(f"[ERROR] マスターボット: {e}")
        return False
    
    # 2. 通知システムテスト
    try:
        from src.notifications.discord import NotificationManager
        
        notification_manager = NotificationManager('')
        await notification_manager.initialize()
        
        print(f"[SUCCESS] 通知システム: OK")
        
        await notification_manager.shutdown()
        
    except Exception as e:
        print(f"[ERROR] 通知システム: {e}")
        return False
    
    # 3. ダッシュボードAPIテスト（サーバー起動時のみ）
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"[SUCCESS] ダッシュボードAPI: OK")
                    print(f"   - ステータス: {data.get('status')}")
                else:
                    print(f"[WARNING] ダッシュボードAPI: HTTP {response.status}")
    except Exception as e:
        print(f"[INFO] ダッシュボードAPI: サーバー未起動 ({e})")
    
    return True

async def main():
    """メイン関数"""
    print("統合テスト開始")
    print("=" * 50)
    
    success = await test_basic_functionality()
    
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] 基本機能テストが成功しました！")
        print("\n[INFO] 次のステップ:")
        print("  1. ダッシュボードサーバー起動: python scripts/start_dashboard.py")
        print("  2. バックテストエンジン実装")
    else:
        print("[ERROR] 基本機能テストが失敗しました。")
    
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
