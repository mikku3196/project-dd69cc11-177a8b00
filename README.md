# 自己進化型AIポートフォリオ自動売買システム

## プロジェクト概要
Bybit APIとGoogle Gemini APIを核とし、複数の取引戦略を自己最適化させながら並行稼働させる完全自律型の資産運用システム。

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    外部API統合レイヤー                        │
│  Bybit API  │  Gemini API  │  News API  │  Discord API     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    マスターボット (Master Bot)                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ ポートフォリオ │ │ リスク管理   │ │ 最適化エンジン │ │ 監視・通知   │ │
│  │ 管理        │ │ サーキット   │ │ バックテスト │ │ Discord     │ │
│  │ リバランス   │ │ ブレーカー   │ │ パラメータ   │ │ ログ管理     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ サブボットA   │ │ サブボットB   │ │ サブボットC   │
│ 安定志向     │ │ バランス重視   │ │ 積極果敢     │
│ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │
│ │意思決定  │ │ │ │意思決定  │ │ │ │意思決定  │ │
│ │ポジション│ │ │ │ポジション│ │ │ │ポジション│ │
│ │リスク計算│ │ │ │リスク計算│ │ │ │リスク計算│ │
│ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │
└─────────────┘ └─────────────┘ └─────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    データ・ユーティリティレイヤー              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ データベース   │ │ データ収集   │ │ APIクライアント│ │ Webダッシュ  │ │
│  │ SQLAlchemy  │ │ 価格・ニュース│ │ Bybit/Gemini│ │ ボード      │ │
│  │ Alembic     │ │ センチメント │ │ 非同期通信   │ │ FastAPI     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 主要機能

### 1. 意思決定エンジン (Gemini統合)
- 複数APIキーのローテーション
- 構造化されたプロンプト生成
- JSON形式での判断結果
- エラーハンドリングとリトライ機能

### 2. ニュース・センチメント分析
- 複数ニュースソースからの自動収集
- Gemini APIによる感情分析
- 移動平均センチメントスコア計算
- リアルタイム市場心理の定量化

### 3. 動的ポジションサイジング
- ATRベースのボラティリティ適応
- 段階的エントリー（分割売買）
- リスク均等化による資金管理

### 4. 市場フェーズ適応型ポートフォリオ
- 5段階の市場フェーズ判定
- 動的資金配分とリバランス
- 利益確保機能（プロフィット・セービング）

### 5. 学習・最適化エンジン
- 高速バックテスト機能
- グリッドサーチによるパラメータ最適化
- 月次自動チューニング
- 自己進化メカニズム

## 技術スタック

- **言語**: Python 3.10+
- **Web Framework**: FastAPI
- **データベース**: SQLAlchemy + PostgreSQL/SQLite
- **タスクスケジューリング**: APScheduler
- **API通信**: aiohttp, httpx
- **データ分析**: Pandas, NumPy, TA-Lib
- **監視・通知**: Discord.py
- **バージョン管理**: Git

## 開発フェーズ

1. **フェーズ1**: 開発と単体テスト
2. **フェーズ2**: 機械的テスト (Testnet環境)
3. **フェーズ3**: 戦略的フォワードテスト (Paper Trading)
4. **フェーズ4**: 本番稼働 (Mainnet環境)

## 🚀 クイックスタート (Ubuntu)

### ワンクリックセットアップ
```bash
# 1. リポジトリクローン
git clone <repository-url>
cd 仮想通貨自動取引bot

# 2. ワンクリックセットアップ & 実行
chmod +x manage.sh
./manage.sh setup
```

### 個別コマンド
```bash
# 依存関係インストール
./manage.sh install

# クイックテスト (1時間)
./manage.sh run-quick

# フルテスト (30日間)
./manage.sh run-full

# ログ分析
./manage.sh analyze
```

## 🐳 Docker使用

### Docker Compose
```bash
# クイックテスト
docker-compose up paper-trading

# フルテスト
docker-compose up paper-trading-full

# 監視サーバー
docker-compose up monitoring
```

### 個別Docker
```bash
# イメージビルド
./manage.sh docker-build

# コンテナ実行
./manage.sh docker-run
```

## 🔧 systemdサービス化

### サービスセットアップ
```bash
# systemdサービスとして設定
./manage.sh systemd-setup

# サービス開始
./manage.sh systemd-start

# サービス状態確認
./manage.sh systemd-status

# ログ確認
./manage.sh systemd-logs
```

## 📊 監視・分析

### 自動分析
```bash
# ログ分析実行
./manage.sh analyze
```

### 手動分析
```bash
# 取引履歴CSV分析
python scripts/analyze_paper_trading.py

# 監視エンドポイント確認
python scripts/check_endpoints.py
```

## 🔧 設定

### 環境変数 (.env)
```bash
# Bybit API Keys
BYBIT_API_KEY=your_api_key
BYBIT_SECRET_KEY=your_secret_key
BYBIT_TESTNET=true

# Gemini API Key
GEMINI_API_KEY=your_gemini_key

# Discord Webhook
DISCORD_WEBHOOK_URL=your_webhook_url
```

### 設定ファイル (config.json)
```json
{
  "bybit": {
    "testnet": true,
    "rate_limit": 120,
    "timeout": 30
  },
  "gemini": {
    "model": "gemini-pro",
    "temperature": 0.7
  },
  "system": {
    "mode": "testnet",
    "log_level": "INFO",
    "max_position_size": 0.1,
    "risk_tolerance": 0.02
  }
}
```

## 🛡️ 安全機能

### サーキットブレーカー
- 連続失敗時の自動停止
- 自動復旧機能
- 状態監視

### レート制限対応
- 指数バックオフ
- APIキーローテーション
- 429エラー自動処理

### テスト環境
- Bybit Testnet対応
- ペーパー取引モード
- 安全なテスト実行

## 📊 監視

### 監視エンドポイント
- `/health` - ヘルスチェック
- `/status` - システム状態
- `/metrics` - パフォーマンス指標
- `/circuit-breaker/reset` - サーキットブレーカーリセット

### ログファイル
- `trades_*.csv` - 取引履歴
- `performance_*.json` - パフォーマンス統計
- `system_*.log` - システムログ

## ⚠️ 注意事項

### 投資リスク
- 仮想通貨投資にはリスクが伴います
- 損失の可能性があります
- 投資判断は自己責任で行ってください

### テスト推奨
- 本番運用前に十分なテストを行ってください
- テストネットでの動作確認を推奨します
- 少額からの運用開始を推奨します

### セキュリティ
- APIキーは適切に管理してください
- 定期的なセキュリティ更新を行ってください
- ログファイルの適切な管理を行ってください

## 🤝 サポート

### トラブルシューティング
```bash
# ログ確認
./manage.sh systemd-logs

# サービス状態確認
./manage.sh systemd-status

# 依存関係再インストール
./manage.sh install
```

### よくある問題
1. **依存関係エラー**: `./manage.sh install` で再インストール
2. **権限エラー**: `chmod +x scripts/*.sh` で権限設定
3. **API接続エラー**: 設定ファイルとAPIキーを確認

## ライセンス
MIT License
