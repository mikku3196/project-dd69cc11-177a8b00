"""
自己進化型AIポートフォリオ自動売買システム - カスタム例外クラス
"""


class TradingBotException(Exception):
    """取引ボット基底例外クラス"""
    pass


class ConfigurationError(TradingBotException):
    """設定エラー"""
    pass


class APIError(TradingBotException):
    """API通信エラー"""
    pass


class BybitAPIError(APIError):
    """Bybit APIエラー"""
    pass


class GeminiAPIError(APIError):
    """Gemini APIエラー"""
    pass


class DatabaseError(TradingBotException):
    """データベースエラー"""
    pass


class TradingError(TradingBotException):
    """取引エラー"""
    pass


class InsufficientFundsError(TradingError):
    """資金不足エラー"""
    pass


class PositionSizeError(TradingError):
    """ポジションサイズエラー"""
    pass


class RiskManagementError(TradingBotException):
    """リスク管理エラー"""
    pass


class CircuitBreakerError(RiskManagementError):
    """サーキットブレーカーエラー"""
    pass


class StrategyError(TradingBotException):
    """戦略エラー"""
    pass


class OptimizationError(TradingBotException):
    """最適化エラー"""
    pass


class BacktestError(OptimizationError):
    """バックテストエラー"""
    pass


class NotificationError(TradingBotException):
    """通知エラー"""
    pass


class DiscordNotificationError(NotificationError):
    """Discord通知エラー"""
    pass
