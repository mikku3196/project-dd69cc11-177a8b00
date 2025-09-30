#!/usr/bin/env python3
"""
設定確認スクリプト
API接続とWebhook設定を確認する
"""
import sys
import os
import yaml
import asyncio
import aiohttp
from pathlib import Path

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

def load_config():
    """設定ファイルを読み込む"""
    config_path = Path("config/api_config.yaml")
    if not config_path.exists():
        print("❌ 設定ファイルが見つかりません: config/api_config.yaml")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ 設定ファイルを読み込みました")
        return config
    except Exception as e:
        print(f"❌ 設定ファイルの読み込みエラー: {e}")
        return None

def check_bybit_config(config):
    """Bybit API設定を確認"""
    print("\n🔑 Bybit API設定確認")
    print("=" * 40)
    
    bybit = config.get('bybit', {})
    api_key = bybit.get('api_key', '')
    api_secret = bybit.get('api_secret', '')
    testnet = bybit.get('testnet', True)
    
    if not api_key or not api_secret:
        print("❌ Bybit APIキーが設定されていません")
        print("   設定場所: https://www.bybit.com/app/user/api-management")
        return False
    
    print(f"✅ APIキー: {api_key[:8]}...")
    print(f"✅ テストネット: {testnet}")
    print(f"✅ ベースURL: {bybit.get('base_url', 'N/A')}")
    
    return True

def check_discord_config(config):
    """Discord Webhook設定を確認"""
    print("\n🔔 Discord Webhook設定確認")
    print("=" * 40)
    
    discord = config.get('discord', {})
    webhook_url = discord.get('webhook_url', '')
    enabled = discord.get('enabled', False)
    
    if not webhook_url:
        print("❌ Discord Webhook URLが設定されていません")
        print("   設定場所: https://discord.com/developers/applications")
        return False
    
    if not enabled:
        print("⚠️  Discord通知が無効になっています")
        return False
    
    print(f"✅ Webhook URL: {webhook_url[:50]}...")
    print(f"✅ 通知レベル: {discord.get('notification_levels', [])}")
    
    return True

def check_gemini_config(config):
    """Gemini AI API設定を確認"""
    print("\n🤖 Gemini AI API設定確認")
    print("=" * 40)
    
    gemini = config.get('gemini', {})
    api_key = gemini.get('api_key', '')
    
    if not api_key:
        print("❌ Gemini APIキーが設定されていません")
        print("   設定場所: https://aistudio.google.com/app/apikey")
        return False
    
    print(f"✅ APIキー: {api_key[:8]}...")
    print(f"✅ モデル: {gemini.get('model', 'N/A')}")
    print(f"✅ エンドポイント: {gemini.get('endpoint', 'N/A')}")
    
    return True

def check_dashboard_config(config):
    """ダッシュボード設定を確認"""
    print("\n🌐 ダッシュボード設定確認")
    print("=" * 40)
    
    dashboard = config.get('dashboard', {})
    host = dashboard.get('host', '0.0.0.0')
    port = dashboard.get('port', 8000)
    api_key = dashboard.get('api_key', '')
    
    print(f"✅ ホスト: {host}")
    print(f"✅ ポート: {port}")
    print(f"✅ APIキー: {'設定済み' if api_key else '未設定'}")
    print(f"✅ アクセスURL: http://{host}:{port}")
    
    return True

async def test_discord_webhook(config):
    """Discord Webhook接続テスト"""
    print("\n🧪 Discord Webhook接続テスト")
    print("=" * 40)
    
    discord = config.get('discord', {})
    webhook_url = discord.get('webhook_url', '')
    
    if not webhook_url:
        print("❌ Webhook URLが設定されていません")
        return False
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": "🤖 AI Trading Bot - 設定確認テスト",
                "embeds": [{
                    "title": "システム設定確認",
                    "description": "すべての設定が正常に完了しました",
                    "color": 0x00ff00,
                    "fields": [
                        {"name": "ステータス", "value": "✅ 正常", "inline": True},
                        {"name": "時刻", "value": "2025-09-30 19:45:00", "inline": True}
                    ]
                }]
            }
            
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    print("✅ Discord Webhook接続テスト成功")
                    return True
                else:
                    print(f"❌ Discord Webhook接続テスト失敗: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Discord Webhook接続テストエラー: {e}")
        return False

def check_directories():
    """必要なディレクトリを確認"""
    print("\n📁 ディレクトリ確認")
    print("=" * 40)
    
    required_dirs = [
        "config",
        "logs",
        "data",
        "src",
        "scripts"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (作成が必要)")
            all_exist = False
    
    return all_exist

def main():
    """メイン処理"""
    print("🚀 AI Trading Bot - 設定確認スクリプト")
    print("=" * 50)
    
    # 設定ファイル読み込み
    config = load_config()
    if not config:
        return False
    
    # 各設定確認
    checks = []
    checks.append(check_bybit_config(config))
    checks.append(check_discord_config(config))
    checks.append(check_gemini_config(config))
    checks.append(check_dashboard_config(config))
    checks.append(check_directories())
    
    # Discord Webhook接続テスト
    if config.get('discord', {}).get('enabled', False):
        try:
            webhook_test = asyncio.run(test_discord_webhook(config))
            checks.append(webhook_test)
        except Exception as e:
            print(f"❌ Discord Webhookテストエラー: {e}")
            checks.append(False)
    
    # 結果サマリー
    print("\n📊 設定確認結果")
    print("=" * 50)
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print("🎉 すべての設定が正常です！")
        print("✅ システム起動準備完了")
        return True
    else:
        print(f"⚠️  {passed}/{total} の設定が完了しています")
        print("❌ 未完了の設定を確認してください")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
