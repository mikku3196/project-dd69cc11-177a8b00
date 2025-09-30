#!/bin/bash
set -e

echo "📦 Installing Paper Trading System Dependencies"
echo "=============================================="

# 色付きログ関数
log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_warn() {
    echo -e "\033[33m[WARN]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

log_success() {
    echo -e "\033[32m[SUCCESS]\033[0m $1"
}

# システムパッケージのインストール
log_info "Installing system packages..."
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-pip python3.11-dev
sudo apt install -y build-essential libssl-dev libffi-dev
log_success "System packages installed"

# 仮想環境作成
if [ ! -d ".venv" ]; then
    log_info "Creating virtual environment..."
    python3.11 -m venv .venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# 仮想環境をアクティベート
source .venv/bin/activate
log_success "Virtual environment activated"

# pip アップグレード
log_info "Upgrading pip..."
pip install --upgrade pip

# 依存関係インストール
log_info "Installing Python dependencies..."

# 基本依存関係
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install aiohttp==3.9.1
pip install pydantic==2.5.0
pip install pydantic-settings==2.1.0
pip install structlog==23.2.0
pip install google-generativeai==0.3.2

# データベース関連
pip install sqlalchemy==2.0.23
pip install alembic==1.13.1

# テスト関連
pip install pytest==7.4.3
pip install pytest-asyncio==0.21.1

# その他
pip install python-dotenv==1.0.0
pip install requests==2.31.0

log_success "Python dependencies installed"

# 設定ファイルの確認
log_info "Checking configuration files..."
if [ ! -f "config.json" ]; then
    log_warn "config.json not found, creating default..."
    cat > config.json << 'EOF'
{
  "bybit": {
    "api_key": "TEST_API_KEY",
    "secret_key": "TEST_SECRET_KEY",
    "testnet": true,
    "rate_limit": 120,
    "timeout": 30
  },
  "gemini": {
    "api_key": "TEST_GEMINI_KEY",
    "model": "gemini-pro",
    "temperature": 0.7
  },
  "discord": {
    "webhook_url": "",
    "enabled": false
  },
  "system": {
    "mode": "testnet",
    "log_level": "INFO",
    "max_position_size": 0.1,
    "risk_tolerance": 0.02
  }
}
EOF
    log_success "Default config.json created"
fi

# 環境変数ファイルの確認
if [ ! -f ".env" ]; then
    log_warn ".env not found, creating template..."
    cat > .env << 'EOF'
# Bybit API Keys
BYBIT_API_KEY=TEST_API_KEY
BYBIT_SECRET_KEY=TEST_SECRET_KEY
BYBIT_TESTNET=true

# Gemini API Key
GEMINI_API_KEY=TEST_GEMINI_KEY

# Discord Webhook
DISCORD_WEBHOOK_URL=

# System Settings
PYTHONUTF8=1
LOG_LEVEL=INFO
EOF
    log_success "Template .env created"
fi

# ログディレクトリ作成
log_info "Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p src/migrations
log_success "Directories created"

# 権限設定
log_info "Setting permissions..."
chmod +x scripts/*.sh
chmod +x scripts/*.py
log_success "Permissions set"

log_success "Installation completed!"
echo ""
echo "🚀 Next steps:"
echo "  1. Edit config.json with your API keys"
echo "  2. Edit .env with your environment variables"
echo "  3. Run: ./scripts/setup_and_run.sh quick"
echo ""
