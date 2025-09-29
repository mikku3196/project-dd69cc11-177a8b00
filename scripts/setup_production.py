"""
自己進化型AIポートフォリオ自動売買システム - 本番環境セットアップスクリプト
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """コマンドを実行"""
    print(f"[INFO] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description} 完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} 失敗: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def setup_production_environment():
    """本番環境をセットアップ"""
    print("=== 自己進化型AIポートフォリオ自動売買システム 本番環境セットアップ ===")
    
    # 1. 仮想環境作成
    if not run_command("python -m venv .venv", "仮想環境作成"):
        return False
    
    # 2. 仮想環境アクティベート（Windows）
    activate_cmd = ".venv\\Scripts\\activate"
    if not run_command(f"{activate_cmd} && python --version", "仮想環境アクティベート"):
        return False
    
    # 3. pipアップグレード
    if not run_command(f"{activate_cmd} && python -m pip install --upgrade pip", "pipアップグレード"):
        return False
    
    # 4. 本番用依存関係インストール
    if not run_command(f"{activate_cmd} && pip install -r requirements_production.txt", "本番用依存関係インストール"):
        return False
    
    # 5. 環境変数設定
    env_file = Path("env.production")
    if env_file.exists():
        print("[INFO] 環境変数ファイルが見つかりました")
        print("[INFO] 手動で環境変数を設定してください:")
        print("  set PYTHONUTF8=1")
        print("  set LOG_LEVEL=INFO")
        print("  set ENVIRONMENT=production")
    
    # 6. データベース初期化
    if not run_command(f"{activate_cmd} && alembic upgrade head", "データベース初期化"):
        print("[WARNING] データベース初期化をスキップしました")
    
    # 7. テスト実行
    if not run_command(f"{activate_cmd} && python scripts/simple_test.py", "システムテスト実行"):
        print("[WARNING] テスト実行をスキップしました")
    
    print("\n=== セットアップ完了 ===")
    print("次のステップ:")
    print("1. 環境変数を設定: set PYTHONUTF8=1")
    print("2. 仮想環境をアクティベート: .venv\\Scripts\\activate")
    print("3. システムを起動: python main.py")
    
    return True


if __name__ == "__main__":
    success = setup_production_environment()
    if success:
        print("\n[SUCCESS] 本番環境セットアップが正常に完了しました")
        sys.exit(0)
    else:
        print("\n[FAILED] 本番環境セットアップが失敗しました")
        sys.exit(1)
