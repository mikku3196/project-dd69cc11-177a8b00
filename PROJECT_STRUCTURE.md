# プロジェクト構造
src/
├── core/                    # コア機能
│   ├── __init__.py
│   ├── config.py           # 設定管理
│   ├── database.py         # データベース接続
│   ├── logger.py           # ログ設定
│   └── exceptions.py       # カスタム例外
├── api/                     # API統合
│   ├── __init__.py
│   ├── bybit_client.py     # Bybit API クライアント
│   ├── gemini_client.py    # Gemini API クライアント
│   ├── news_client.py      # ニュースAPI クライアント
│   └── discord_client.py   # Discord通知クライアント
├── models/                  # データモデル
│   ├── __init__.py
│   ├── base.py             # ベースモデル
│   ├── account.py          # アカウント関連
│   ├── trade.py            # 取引関連
│   ├── market_data.py      # 市場データ
│   ├── news.py             # ニュース・センチメント
│   └── performance.py      # パフォーマンス指標
├── strategies/              # 取引戦略
│   ├── __init__.py
│   ├── base_strategy.py    # ベース戦略クラス
│   ├── conservative.py     # 安定志向戦略
│   ├── balanced.py         # バランス重視戦略
│   └── aggressive.py      # 積極果敢戦略
├── bots/                    # ボット実装
│   ├── __init__.py
│   ├── sub_bot.py          # サブボット基底クラス
│   ├── conservative_bot.py # 安定志向ボット
│   ├── balanced_bot.py     # バランス重視ボット
│   ├── aggressive_bot.py  # 積極果敢ボット
│   └── master_bot.py       # マスターボット
├── analysis/                # 分析エンジン
│   ├── __init__.py
│   ├── technical.py        # テクニカル分析
│   ├── sentiment.py        # センチメント分析
│   ├── risk_manager.py     # リスク管理
│   └── portfolio_manager.py # ポートフォリオ管理
├── optimization/            # 最適化エンジン
│   ├── __init__.py
│   ├── backtest.py         # バックテスト
│   ├── parameter_optimizer.py # パラメータ最適化
│   └── performance_analyzer.py # パフォーマンス分析
├── dashboard/               # Webダッシュボード
│   ├── __init__.py
│   ├── main.py             # FastAPI アプリケーション
│   ├── routes/             # API ルート
│   │   ├── __init__.py
│   │   ├── trades.py       # 取引関連API
│   │   ├── portfolio.py    # ポートフォリオAPI
│   │   ├── performance.py  # パフォーマンスAPI
│   │   └── system.py       # システム管理API
│   └── static/              # 静的ファイル
│       ├── css/
│       ├── js/
│       └── templates/
├── utils/                   # ユーティリティ
│   ├── __init__.py
│   ├── helpers.py          # ヘルパー関数
│   ├── validators.py       # バリデーター
│   └── decorators.py       # デコレーター
├── tests/                   # テスト
│   ├── __init__.py
│   ├── conftest.py         # pytest設定
│   ├── test_api/           # APIテスト
│   ├── test_strategies/    # 戦略テスト
│   ├── test_bots/          # ボットテスト
│   └── test_analysis/      # 分析テスト
├── migrations/              # データベースマイグレーション
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── scripts/                 # スクリプト
│   ├── setup.py            # セットアップスクリプト
│   ├── migrate.py          # マイグレーションスクリプト
│   └── maintenance.py      # メンテナンススクリプト
├── main.py                  # メインエントリーポイント
├── alembic.ini             # Alembic設定
└── .gitignore              # Git除外設定

# 設定ファイル
config.json                 # メイン設定ファイル
requirements.txt            # Python依存関係
env.example                 # 環境変数テンプレート
README.md                   # プロジェクト説明
.gitignore                  # Git除外設定
