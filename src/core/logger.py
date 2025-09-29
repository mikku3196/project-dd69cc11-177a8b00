"""
自己進化型AIポートフォリオ自動売買システム - ログ管理モジュール
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import structlog
from .config import config


def setup_logging() -> None:
    """ログ設定を初期化"""
    
    # ログディレクトリを作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # ログレベルを設定
    log_level = getattr(logging, config.system.log_level.upper(), logging.INFO)
    
    # 基本ログ設定
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                log_dir / "trading_bot.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # 構造化ログの設定
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 特定のモジュールのログレベルを調整
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """構造化ログロガーを取得"""
    return structlog.get_logger(name)


class TradingLogger:
    """取引専用ロガー"""
    
    def __init__(self, name: str = "trading"):
        self.logger = get_logger(name)
        self.log_file = Path("logs") / "trades.log"
        
        # 取引ログ用のハンドラー
        trade_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10
        )
        trade_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        
        trade_logger = logging.getLogger(f"{name}.trades")
        trade_logger.addHandler(trade_handler)
        trade_logger.setLevel(logging.INFO)
        self.trade_logger = trade_logger
    
    def log_trade(self, trade_data: dict) -> None:
        """取引ログを記録"""
        self.trade_logger.info(f"TRADE: {trade_data}")
        self.logger.info("取引を実行しました", **trade_data)
    
    def log_decision(self, decision_data: dict) -> None:
        """意思決定ログを記録"""
        self.logger.info("取引意思決定", **decision_data)
    
    def log_error(self, error_data: dict) -> None:
        """エラーログを記録"""
        self.logger.error("取引エラー", **error_data)


class PerformanceLogger:
    """パフォーマンス専用ロガー"""
    
    def __init__(self, name: str = "performance"):
        self.logger = get_logger(name)
        self.perf_file = Path("logs") / "performance.log"
        
        # パフォーマンスログ用のハンドラー
        perf_handler = logging.handlers.RotatingFileHandler(
            self.perf_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10
        )
        perf_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s')
        )
        
        perf_logger = logging.getLogger(f"{name}.metrics")
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        self.perf_logger = perf_logger
    
    def log_metrics(self, metrics_data: dict) -> None:
        """パフォーマンス指標を記録"""
        self.perf_logger.info(f"METRICS: {metrics_data}")
        self.logger.info("パフォーマンス指標を記録", **metrics_data)
    
    def log_optimization(self, optimization_data: dict) -> None:
        """最適化結果を記録"""
        self.logger.info("パラメータ最適化完了", **optimization_data)


class SystemLogger:
    """システム専用ロガー"""
    
    def __init__(self, name: str = "system"):
        self.logger = get_logger(name)
        self.system_file = Path("logs") / "system.log"
        
        # システムログ用のハンドラー
        system_handler = logging.handlers.RotatingFileHandler(
            self.system_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10
        )
        system_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        system_logger = logging.getLogger(f"{name}.events")
        system_logger.addHandler(system_handler)
        system_logger.setLevel(logging.INFO)
        self.system_logger = system_logger
    
    def log_startup(self, startup_data: dict) -> None:
        """起動ログを記録"""
        self.system_logger.info(f"STARTUP: {startup_data}")
        self.logger.info("システム起動", **startup_data)
    
    def log_shutdown(self, shutdown_data: dict) -> None:
        """シャットダウンログを記録"""
        self.system_logger.info(f"SHUTDOWN: {shutdown_data}")
        self.logger.info("システムシャットダウン", **shutdown_data)
    
    def log_health_check(self, health_data: dict) -> None:
        """ヘルスチェックログを記録"""
        self.system_logger.info(f"HEALTH: {health_data}")
        self.logger.info("ヘルスチェック", **health_data)


# グローバルロガーインスタンス
trading_logger = TradingLogger()
performance_logger = PerformanceLogger()
system_logger = SystemLogger()
