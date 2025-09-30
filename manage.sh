#!/bin/bash
set -e

echo "🎯 Paper Trading System Management"
echo "================================="

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

# ヘルプ表示
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup           - Complete system setup (Ubuntu)"
    echo "  install         - Install dependencies only"
    echo "  run-quick       - Run 1-hour quick test"
    echo "  run-full        - Run 30-day full test"
    echo "  analyze         - Analyze existing logs"
    echo "  docker-build    - Build Docker image"
    echo "  docker-run      - Run with Docker"
    echo "  systemd-setup   - Setup as systemd service"
    echo "  systemd-start   - Start systemd service"
    echo "  systemd-stop    - Stop systemd service"
    echo "  systemd-status  - Check systemd service status"
    echo "  systemd-logs    - View systemd service logs"
    echo "  clean           - Clean logs and data"
    echo "  help            - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 setup                    # Complete setup"
    echo "  $0 run-quick                # Quick test"
    echo "  $0 docker-run               # Run with Docker"
    echo "  $0 systemd-setup            # Setup as service"
    echo ""
}

# セットアップ実行
run_setup() {
    log_info "Running complete system setup..."
    chmod +x scripts/*.sh
    ./scripts/install_requirements.sh
    log_success "Setup completed!"
}

# インストール実行
run_install() {
    log_info "Installing dependencies..."
    chmod +x scripts/install_requirements.sh
    ./scripts/install_requirements.sh
    log_success "Installation completed!"
}

# クイックテスト実行
run_quick() {
    log_info "Running quick test..."
    chmod +x scripts/setup_and_run.sh
    ./scripts/setup_and_run.sh quick
    log_success "Quick test completed!"
}

# フルテスト実行
run_full() {
    log_info "Running full test..."
    chmod +x scripts/setup_and_run.sh
    ./scripts/setup_and_run.sh full
    log_success "Full test completed!"
}

# 分析実行
run_analyze() {
    log_info "Analyzing logs..."
    python scripts/analyze_paper_trading.py
    log_success "Analysis completed!"
}

# Dockerビルド
docker_build() {
    log_info "Building Docker image..."
    docker build -t paper-trading-bot .
    log_success "Docker image built!"
}

# Docker実行
docker_run() {
    log_info "Running with Docker..."
    docker-compose up -d paper-trading
    log_success "Docker container started!"
    echo "Check logs with: docker-compose logs -f paper-trading"
}

# systemdセットアップ
systemd_setup() {
    log_info "Setting up systemd service..."
    chmod +x scripts/setup_systemd_service.sh
    ./scripts/setup_systemd_service.sh
    log_success "Systemd service setup completed!"
}

# systemd開始
systemd_start() {
    log_info "Starting systemd service..."
    sudo systemctl start paper-trading-bot
    log_success "Service started!"
}

# systemd停止
systemd_stop() {
    log_info "Stopping systemd service..."
    sudo systemctl stop paper-trading-bot
    log_success "Service stopped!"
}

# systemd状態確認
systemd_status() {
    log_info "Checking systemd service status..."
    sudo systemctl status paper-trading-bot --no-pager
}

# systemdログ表示
systemd_logs() {
    log_info "Showing systemd service logs..."
    sudo journalctl -u paper-trading-bot -f
}

# クリーンアップ
run_clean() {
    log_info "Cleaning logs and data..."
    rm -rf logs/*
    rm -rf data/*
    log_success "Cleanup completed!"
}

# メイン処理
case "${1:-help}" in
    "setup")
        run_setup
        ;;
    "install")
        run_install
        ;;
    "run-quick")
        run_quick
        ;;
    "run-full")
        run_full
        ;;
    "analyze")
        run_analyze
        ;;
    "docker-build")
        docker_build
        ;;
    "docker-run")
        docker_run
        ;;
    "systemd-setup")
        systemd_setup
        ;;
    "systemd-start")
        systemd_start
        ;;
    "systemd-stop")
        systemd_stop
        ;;
    "systemd-status")
        systemd_status
        ;;
    "systemd-logs")
        systemd_logs
        ;;
    "clean")
        run_clean
        ;;
    "help"|*)
        show_help
        ;;
esac
