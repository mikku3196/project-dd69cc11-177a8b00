#!/bin/bash
set -e

echo "🚀 Paper Trading System Setup & Run (Ubuntu)"
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

# 1. Python & pip チェック
log_info "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    log_error "Python3 not found. Please install Python3.11+"
    echo "Install with: sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
log_info "Python version: $PYTHON_VERSION"

# 2. 仮想環境作成
if [ ! -d ".venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv .venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# 仮想環境をアクティベート
source .venv/bin/activate
log_success "Virtual environment activated"

# 3. pip アップグレード
log_info "Upgrading pip..."
pip install --upgrade pip

# 4. 依存関係インストール
log_info "Installing dependencies..."
if [ -f "requirements_production.txt" ]; then
    pip install -r requirements_production.txt
elif [ -f "requirements_light.txt" ]; then
    pip install -r requirements_light.txt
else
    log_warn "No requirements file found, installing minimal dependencies..."
    pip install fastapi uvicorn aiohttp pydantic pydantic-settings structlog google-generativeai
fi

log_success "Dependencies installed"

# 5. ログディレクトリ作成
log_info "Creating log directories..."
mkdir -p logs
mkdir -p data
log_success "Directories created"

# 6. 引数によるモード切替
MODE=${1:-quick}

log_info "Running paper trading in mode: $MODE"

# 7. ペーパー取引テスト実行
if [ "$MODE" == "full" ]; then
    log_info "Starting 30-day full test..."
    python scripts/run_paper_trading.py --full
elif [ "$MODE" == "quick" ]; then
    log_info "Starting 1-hour quick test..."
    python scripts/run_paper_trading.py --quick
else
    log_error "Invalid mode: $MODE. Use 'quick' or 'full'"
    exit 1
fi

# 8. 分析実行
log_info "Analyzing logs..."
python scripts/analyze_paper_trading.py

# 9. 結果表示
log_success "Paper trading test completed!"
echo ""
echo "📊 Results saved in:"
echo "  - Logs: ./logs/"
echo "  - Data: ./data/"
echo ""
echo "📈 To view results:"
echo "  - Check logs directory for CSV and JSON files"
echo "  - Run: python scripts/analyze_paper_trading.py"
echo ""
echo "🔄 To run again:"
echo "  - Quick test: ./scripts/setup_and_run.sh quick"
echo "  - Full test: ./scripts/setup_and_run.sh full"
echo ""

log_success "Setup & Run completed successfully!"
