# 🚀 AI仮想通貨自動取引システム - API・Webhook登録ガイド

## 📋 概要
このシステムで使用する各種APIとWebhookの登録場所と設定方法を説明します。

---

## 🔑 1. Bybit API設定

### **1.1 APIキー取得場所**
- **URL**: https://www.bybit.com/app/user/api-management
- **ログイン**: Bybitアカウントでログイン
- **手順**:
  1. 「Create New Key」をクリック
  2. API名を入力（例: "AI Trading Bot"）
  3. 権限設定:
     - ✅ **Read** (必須)
     - ✅ **Trade** (必須)
     - ✅ **Derivatives** (必須)
     - ❌ **Withdraw** (不要)
  4. IP制限を設定（推奨）
  5. 「Create」をクリック

### **1.2 設定ファイル**
```bash
# 設定ファイル: config/api_config.yaml
bybit:
  api_key: "YOUR_API_KEY_HERE"
  api_secret: "YOUR_API_SECRET_HERE"
  testnet: true  # 本番運用時は false
  base_url: "https://api-testnet.bybit.com"  # 本番: "https://api.bybit.com"
```

---

## 📰 2. ニュースAPI設定

### **2.1 Google News RSS**
- **URL**: https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en
- **設定**: 既に設定済み（変更不要）

### **2.2 Gemini AI API（センチメント分析）**
- **URL**: https://aistudio.google.com/app/apikey
- **手順**:
  1. Google AI Studioにアクセス
  2. 「Create API Key」をクリック
  3. APIキーをコピー
  4. 設定ファイルに追加

```bash
# 設定ファイル: config/api_config.yaml
gemini:
  api_key: "YOUR_GEMINI_API_KEY_HERE"
  model: "gemini-1.5-flash"
  endpoint: "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
```

---

## 🔔 3. Discord Webhook設定

### **3.1 Discord Webhook作成**
- **URL**: https://discord.com/developers/applications
- **手順**:
  1. 「New Application」をクリック
  2. アプリケーション名を入力（例: "AI Trading Bot"）
  3. 「Create」をクリック
  4. 左メニューから「Webhooks」を選択
  5. 「New Webhook」をクリック
  6. チャンネルを選択
  7. Webhook URLをコピー

### **3.2 設定ファイル**
```bash
# 設定ファイル: config/api_config.yaml
discord:
  webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
  enabled: true
  notification_levels:
    - "ERROR"
    - "CRITICAL"
    - "WARNING"
```

---

## 📊 4. データベース設定

### **4.1 SQLite（デフォルト）**
```bash
# 設定ファイル: config/database_config.yaml
database:
  type: "sqlite"
  url: "sqlite:///./data/trading_bot.db"
  echo: false
```

### **4.2 PostgreSQL（本番推奨）**
```bash
# 設定ファイル: config/database_config.yaml
database:
  type: "postgresql"
  url: "postgresql://username:password@localhost:5432/trading_bot"
  echo: false
  pool_size: 10
  max_overflow: 20
```

---

## 🌐 5. Webダッシュボード設定

### **5.1 FastAPI設定**
```bash
# 設定ファイル: config/api_config.yaml
dashboard:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins: ["http://localhost:3000"]
  api_key: "YOUR_DASHBOARD_API_KEY"
```

### **5.2 アクセスURL**
- **開発環境**: http://localhost:8000
- **本番環境**: https://your-domain.com:8000

---

## 🔧 6. 設定ファイルの場所

### **6.1 メイン設定ファイル**
```bash
config/
├── api_config.yaml          # API設定
├── database_config.yaml     # データベース設定
├── trading_config.yaml      # 取引設定
├── notification_config.yaml # 通知設定
└── logging_config.yaml     # ログ設定
```

### **6.2 環境変数ファイル**
```bash
.env                        # 環境変数（.gitignoreに追加済み）
.env.example               # 環境変数の例
```

---

## 🚀 7. 起動前チェックリスト

### **7.1 必須設定**
- [ ] Bybit APIキー設定
- [ ] Discord Webhook設定
- [ ] データベース接続確認
- [ ] ログディレクトリ作成

### **7.2 推奨設定**
- [ ] Gemini AI APIキー設定
- [ ] IP制限設定
- [ ] SSL証明書設定（本番環境）
- [ ] バックアップ設定

---

## 📝 8. 設定例

### **8.1 完全な設定ファイル例**
```yaml
# config/api_config.yaml
bybit:
  api_key: "YOUR_BYBIT_API_KEY"
  api_secret: "YOUR_BYBIT_API_SECRET"
  testnet: true
  base_url: "https://api-testnet.bybit.com"

gemini:
  api_key: "YOUR_GEMINI_API_KEY"
  model: "gemini-1.5-flash"
  endpoint: "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

discord:
  webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"
  enabled: true
  notification_levels:
    - "ERROR"
    - "CRITICAL"
    - "WARNING"

dashboard:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins: ["http://localhost:3000"]
  api_key: "YOUR_DASHBOARD_API_KEY"
```

---

## ⚠️ 9. セキュリティ注意事項

### **9.1 APIキー管理**
- APIキーは絶対に公開しない
- `.env`ファイルを`.gitignore`に追加
- 定期的にAPIキーをローテーション
- IP制限を設定

### **9.2 権限設定**
- 必要最小限の権限のみ付与
- 出金権限は絶対に付与しない
- テストネットで十分にテスト

---

## 🔍 10. トラブルシューティング

### **10.1 よくある問題**
1. **APIキーエラー**: 権限設定を確認
2. **接続エラー**: ネットワーク設定を確認
3. **認証エラー**: APIキーの有効性を確認
4. **レート制限**: リクエスト頻度を調整

### **10.2 ログ確認**
```bash
# ログファイルの場所
logs/
├── trading_bot.log
├── api_errors.log
└── system_monitor.log
```

---

## 📞 11. サポート

### **11.1 公式ドキュメント**
- **Bybit API**: https://bybit-exchange.github.io/docs/
- **Discord API**: https://discord.com/developers/docs
- **Gemini AI**: https://ai.google.dev/docs

### **11.2 緊急連絡**
- システムエラー: Discord通知
- API制限: ログ確認
- 取引エラー: 即座に停止

---

## ✅ 12. 最終確認

設定完了後、以下のコマンドで動作確認:

```bash
# 設定確認
python scripts/check_config.py

# API接続テスト
python scripts/test_api_connections.py

# システム起動
python main.py
```

---

**🎉 設定完了後、システムは本格運用準備完了です！**
