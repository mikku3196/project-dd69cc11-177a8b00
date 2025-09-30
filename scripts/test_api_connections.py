#!/usr/bin/env python3
"""
API接続テストスクリプト
各種APIの接続性をテストする
"""
import sys
import os
import asyncio
import aiohttp
import yaml
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
        return config
    except Exception as e:
        print(f"❌ 設定ファイルの読み込みエラー: {e}")
        return None

async def test_bybit_api(config):
    """Bybit API接続テスト"""
    print("\n🔑 Bybit API接続テスト")
    print("=" * 40)
    
    bybit = config.get('bybit', {})
    api_key = bybit.get('api_key', '')
    api_secret = bybit.get('api_secret', '')
    base_url = bybit.get('base_url', '')
    
    if not all([api_key, api_secret, base_url]):
        print("❌ Bybit API設定が不完全です")
        return False
    
    try:
        # 簡単なAPI呼び出し（サーバー時間取得）
        url = f"{base_url}/v5/market/time"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Bybit API接続成功")
                    print(f"   サーバー時間: {data.get('result', {}).get('timeSecond', 'N/A')}")
                    return True
                else:
                    print(f"❌ Bybit API接続失敗: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Bybit API接続エラー: {e}")
        return False

async def test_gemini_api(config):
    """Gemini AI API接続テスト"""
    print("\n🤖 Gemini AI API接続テスト")
    print("=" * 40)
    
    gemini = config.get('gemini', {})
    api_key = gemini.get('api_key', '')
    endpoint = gemini.get('endpoint', '')
    
    if not all([api_key, endpoint]):
        print("❌ Gemini API設定が不完全です")
        return False
    
    try:
        url = f"{endpoint}?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Hello, this is a test message."
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Gemini AI API接続成功")
                    print("   テストメッセージ送信完了")
                    return True
                else:
                    print(f"❌ Gemini AI API接続失敗: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Gemini AI API接続エラー: {e}")
        return False

async def test_discord_webhook(config):
    """Discord Webhook接続テスト"""
    print("\n🔔 Discord Webhook接続テスト")
    print("=" * 40)
    
    discord = config.get('discord', {})
    webhook_url = discord.get('webhook_url', '')
    
    if not webhook_url:
        print("❌ Discord Webhook URLが設定されていません")
        return False
    
    try:
        payload = {
            "content": "🧪 API接続テスト - Discord Webhook",
            "embeds": [{
                "title": "API接続テスト結果",
                "description": "Discord Webhook接続テストが成功しました",
                "color": 0x00ff00,
                "fields": [
                    {"name": "ステータス", "value": "✅ 成功", "inline": True},
                    {"name": "テスト時刻", "value": "2025-09-30 19:45:00", "inline": True}
                ]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    print("✅ Discord Webhook接続成功")
                    print("   テストメッセージ送信完了")
                    return True
                else:
                    print(f"❌ Discord Webhook接続失敗: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Discord Webhook接続エラー: {e}")
        return False

async def test_news_api():
    """ニュースAPI接続テスト"""
    print("\n📰 ニュースAPI接続テスト")
    print("=" * 40)
    
    try:
        url = "https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    if "bitcoin" in text.lower():
                        print("✅ ニュースAPI接続成功")
                        print("   Bitcoin関連ニュース取得完了")
                        return True
                    else:
                        print("❌ ニュースAPI接続失敗: データ形式エラー")
                        return False
                else:
                    print(f"❌ ニュースAPI接続失敗: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ ニュースAPI接続エラー: {e}")
        return False

async def test_dashboard_api(config):
    """ダッシュボードAPI接続テスト"""
    print("\n🌐 ダッシュボードAPI接続テスト")
    print("=" * 40)
    
    dashboard = config.get('dashboard', {})
    host = dashboard.get('host', '0.0.0.0')
    port = dashboard.get('port', 8000)
    
    try:
        url = f"http://{host}:{port}/health"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    print("✅ ダッシュボードAPI接続成功")
                    print(f"   アクセスURL: http://{host}:{port}")
                    return True
                else:
                    print(f"❌ ダッシュボードAPI接続失敗: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ ダッシュボードAPI接続エラー: {e}")
        print("   ダッシュボードが起動していない可能性があります")
        return False

async def main():
    """メイン処理"""
    print("🚀 AI Trading Bot - API接続テスト")
    print("=" * 50)
    
    # 設定ファイル読み込み
    config = load_config()
    if not config:
        return False
    
    # 各API接続テスト
    tests = []
    
    # Bybit APIテスト
    if config.get('bybit', {}).get('api_key'):
        tests.append(await test_bybit_api(config))
    
    # Gemini AI APIテスト
    if config.get('gemini', {}).get('api_key'):
        tests.append(await test_gemini_api(config))
    
    # Discord Webhookテスト
    if config.get('discord', {}).get('webhook_url'):
        tests.append(await test_discord_webhook(config))
    
    # ニュースAPIテスト
    tests.append(await test_news_api())
    
    # ダッシュボードAPIテスト
    tests.append(await test_dashboard_api(config))
    
    # 結果サマリー
    print("\n📊 API接続テスト結果")
    print("=" * 50)
    
    passed = sum(tests)
    total = len(tests)
    
    if passed == total:
        print("🎉 すべてのAPI接続テストが成功しました！")
        print("✅ システム運用準備完了")
        return True
    else:
        print(f"⚠️  {passed}/{total} のAPI接続テストが成功しました")
        print("❌ 失敗したAPI接続を確認してください")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
