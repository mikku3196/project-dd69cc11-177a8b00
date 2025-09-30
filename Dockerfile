# Docker化用Dockerfile
FROM python:3.11-slim

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements_production.txt .

# Python依存関係のインストール
RUN pip install --no-cache-dir -r requirements_production.txt

# アプリケーションコードをコピー
COPY . .

# ログディレクトリ作成
RUN mkdir -p logs data

# 権限設定
RUN chmod +x scripts/*.sh scripts/*.py

# 環境変数設定
ENV PYTHONUTF8=1
ENV PYTHONPATH=/app

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# デフォルトコマンド
CMD ["./scripts/setup_and_run.sh", "quick"]
