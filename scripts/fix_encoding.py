#!/usr/bin/env python3
"""
UTF-8エンコーディング修正スクリプト
Windows環境での文字化け問題を解決する
"""
import sys
import io
import os

def fix_encoding():
    """UTF-8エンコーディングを強制的に設定"""
    # 標準出力をUTF-8に設定
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    
    # 環境変数を設定
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    
    print("✅ UTF-8エンコーディングが設定されました")
    print(f"現在のエンコーディング: {sys.stdout.encoding}")
    print(f"Pythonバージョン: {sys.version}")
    
    return True

if __name__ == "__main__":
    fix_encoding()
