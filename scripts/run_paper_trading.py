"""
ペーパー取引テスト実行スクリプト
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

def setup_environment():
    """環境設定"""
    # 環境変数設定
    os.environ['PYTHONUTF8'] = '1'
    
    # ログディレクトリ作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # データディレクトリ作成
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

async def run_paper_trading_test():
    """ペーパー取引テストを実行"""
    print("=== ペーパー取引テスト開始 ===")
    print("テスト期間: 30日間")
    print("初期残高: $1,000")
    print("取引間隔: 5分")
    print("ログ保存: CSV + JSON")
    
    try:
        # ペーパー取引テストをインポートして実行
        from scripts.paper_trading_test import PaperTradingTest
        
        test = PaperTradingTest(test_duration_days=30)
        await test.run_test()
        
        print("\n=== ペーパー取引テスト完了 ===")
        print("結果ファイル:")
        print(f"- 取引履歴: {test.trades_csv}")
        print(f"- パフォーマンス: {test.performance_json}")
        
    except ImportError as e:
        print(f"[ERROR] モジュールインポートエラー: {e}")
        print("必要な依存関係をインストールしてください:")
        print("pip install -r requirements_light.txt")
        
    except Exception as e:
        print(f"[ERROR] ペーパー取引テストエラー: {e}")
        return False
    
    return True

async def run_quick_test():
    """クイックテスト（1時間）"""
    print("=== クイックテスト開始（1時間） ===")
    
    try:
        from scripts.paper_trading_test import PaperTradingTest
        
        test = PaperTradingTest(test_duration_days=1)  # 1日 = 24時間
        await test.run_test()
        
        print("\n=== クイックテスト完了 ===")
        
    except Exception as e:
        print(f"[ERROR] クイックテストエラー: {e}")
        return False
    
    return True

def show_help():
    """ヘルプ表示"""
    print("""
ペーパー取引テスト実行スクリプト

使用方法:
  python scripts/run_paper_trading.py [オプション]

オプション:
  --full      30日間のフルテストを実行
  --quick     1時間のクイックテストを実行
  --help      このヘルプを表示

例:
  python scripts/run_paper_trading.py --full
  python scripts/run_paper_trading.py --quick
    """)

async def main():
    """メイン関数"""
    setup_environment()
    
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command == "--full":
        success = await run_paper_trading_test()
    elif command == "--quick":
        success = await run_quick_test()
    elif command == "--help":
        show_help()
        return
    else:
        print(f"[ERROR] 不明なコマンド: {command}")
        show_help()
        return
    
    if success:
        print("\n[SUCCESS] テストが正常に完了しました")
        sys.exit(0)
    else:
        print("\n[FAILED] テストが失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        sys.exit(1)
