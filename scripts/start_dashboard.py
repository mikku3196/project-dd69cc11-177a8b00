"""
ダッシュボード起動スクリプト
"""
import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def check_dependencies():
    """依存関係チェック"""
    print("[INFO] 依存関係をチェック中...")
    
    # Python依存関係
    try:
        import fastapi
        import uvicorn
        print("[SUCCESS] FastAPI: OK")
    except ImportError:
        print("[ERROR] FastAPI not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"], check=True)
    
    # Node.js依存関係
    dashboard_dir = Path("dashboard")
    if not dashboard_dir.exists():
        print("[ERROR] Dashboard directory not found. Run create_dashboard.py first.")
        return False
    
    node_modules = dashboard_dir / "node_modules"
    if not node_modules.exists():
        print("[INFO] Installing Node.js dependencies...")
        try:
            subprocess.run(["npm", "install"], cwd=dashboard_dir, check=True)
            print("[SUCCESS] Node.js dependencies installed")
        except subprocess.CalledProcessError:
            print("[ERROR] Failed to install Node.js dependencies")
            return False
    
    return True

def start_backend():
    """バックエンド起動"""
    print("[INFO] FastAPI バックエンドを起動中...")
    
    try:
        # バックエンド起動
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.dashboard.api:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
        print("[SUCCESS] バックエンド起動完了 (http://localhost:8000)")
        return process
        
    except Exception as e:
        print(f"[ERROR] バックエンド起動エラー: {e}")
        return None

def start_frontend():
    """フロントエンド起動"""
    print("[INFO] React フロントエンドを起動中...")
    
    dashboard_dir = Path("dashboard")
    
    try:
        # フロントエンド起動
        process = subprocess.Popen([
            "npm", "start"
        ], cwd=dashboard_dir)
        
        print("[SUCCESS] フロントエンド起動完了 (http://localhost:3000)")
        return process
        
    except Exception as e:
        print(f"[ERROR] フロントエンド起動エラー: {e}")
        return None

def main():
    """メイン関数"""
    print("🚀 Trading Bot Dashboard 起動")
    print("=" * 50)
    
    # 依存関係チェック
    if not check_dependencies():
        print("[ERROR] 依存関係の準備に失敗しました")
        return False
    
    # バックエンド起動
    backend_process = start_backend()
    if not backend_process:
        return False
    
    # バックエンド起動待機
    print("[INFO] バックエンド起動待機中...")
    time.sleep(3)
    
    # フロントエンド起動
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ダッシュボード起動完了!")
    print("=" * 50)
    print("📊 バックエンド: http://localhost:8000")
    print("🖥️ フロントエンド: http://localhost:3000")
    print("📚 API ドキュメント: http://localhost:8000/docs")
    print("\n[INFO] 終了するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        # プロセス監視
        while True:
            if backend_process.poll() is not None:
                print("[ERROR] バックエンドが停止しました")
                break
            if frontend_process.poll() is not None:
                print("[ERROR] フロントエンドが停止しました")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] シャットダウン中...")
        
        # プロセス終了
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        
        print("[SUCCESS] ダッシュボードを停止しました")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        sys.exit(1)