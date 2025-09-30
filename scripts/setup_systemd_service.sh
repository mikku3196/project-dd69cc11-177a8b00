#!/bin/bash
set -e

echo "🔧 Setting up Paper Trading System as systemd service"
echo "=================================================="

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

# 現在のディレクトリを取得
CURRENT_DIR=$(pwd)
SERVICE_NAME="paper-trading-bot"
USER_NAME=$(whoami)

log_info "Current directory: $CURRENT_DIR"
log_info "Service name: $SERVICE_NAME"
log_info "User: $USER_NAME"

# systemdサービスファイル作成
log_info "Creating systemd service file..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Paper Trading Bot
After=network.target
Wants=network.target

[Service]
Type=simple
User=${USER_NAME}
Group=${USER_NAME}
WorkingDirectory=${CURRENT_DIR}
Environment=PYTHONUTF8=1
Environment=LOG_LEVEL=INFO
Environment=BYBIT_TESTNET=true
ExecStart=${CURRENT_DIR}/.venv/bin/python ${CURRENT_DIR}/scripts/run_paper_trading.py --full
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# セキュリティ設定
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${CURRENT_DIR}/logs ${CURRENT_DIR}/data

[Install]
WantedBy=multi-user.target
EOF

log_success "Systemd service file created"

# systemdデーモンリロード
log_info "Reloading systemd daemon..."
sudo systemctl daemon-reload

# サービス有効化
log_info "Enabling service..."
sudo systemctl enable ${SERVICE_NAME}

log_success "Service enabled"

# サービス状態確認
log_info "Checking service status..."
sudo systemctl status ${SERVICE_NAME} --no-pager

echo ""
echo "🎯 Service Management Commands:"
echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
echo "  Restart: sudo systemctl restart ${SERVICE_NAME}"
echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "📊 Monitoring Commands:"
echo "  Real-time logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Service status: sudo systemctl status ${SERVICE_NAME}"
echo "  Service logs:   sudo journalctl -u ${SERVICE_NAME} --since today"
echo ""

# サービス開始の確認
read -p "Do you want to start the service now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Starting service..."
    sudo systemctl start ${SERVICE_NAME}
    sleep 2
    sudo systemctl status ${SERVICE_NAME} --no-pager
    log_success "Service started!"
else
    log_info "Service ready to start. Use 'sudo systemctl start ${SERVICE_NAME}' to start it."
fi

log_success "Systemd service setup completed!"
