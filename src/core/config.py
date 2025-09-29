"""
自己進化型AIポートフォリオ自動売買システム - コア設定管理モジュール
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseSettings, Field
import logging

logger = logging.getLogger(__name__)


class SystemConfig(BaseSettings):
    """システム基本設定"""
    name: str = "自己進化型AIポートフォリオ自動売買システム"
    version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"


class BybitConfig(BaseSettings):
    """Bybit API設定"""
    api_key: str = Field(..., env="BYBIT_API_KEY")
    secret_key: str = Field(..., env="BYBIT_SECRET_KEY")
    testnet: bool = Field(True, env="BYBIT_TESTNET")
    rate_limit: int = 120
    timeout: int = 30
    
    class Config:
        env_file = ".env"


class GeminiConfig(BaseSettings):
    """Gemini API設定"""
    api_keys: List[str] = Field(default_factory=list)
    model: str = "gemini-pro"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    retry_attempts: int = 3
    
    class Config:
        env_file = ".env"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 環境変数からAPIキーを読み込み
        api_keys_str = os.getenv("GEMINI_API_KEYS", "")
        if api_keys_str:
            self.api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]


class DiscordConfig(BaseSettings):
    """Discord通知設定"""
    webhook_url: str = Field("", env="DISCORD_WEBHOOK_URL")
    bot_token: str = Field("", env="DISCORD_BOT_TOKEN")
    
    class Config:
        env_file = ".env"


class DatabaseConfig(BaseSettings):
    """データベース設定"""
    url: str = Field("sqlite:///./trading_bot.db", env="DATABASE_URL")
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    
    class Config:
        env_file = ".env"


class TradingConfig(BaseSettings):
    """取引設定"""
    default_balance: float = Field(1000, env="DEFAULT_ACCOUNT_BALANCE")
    max_position_size: float = Field(0.1, env="MAX_POSITION_SIZE")
    risk_per_trade: float = Field(0.02, env="RISK_PER_TRADE")
    max_daily_loss: float = 0.05
    
    class Config:
        env_file = ".env"


class ConfigManager:
    """設定管理クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config_data: Dict[str, Any] = {}
        self._load_config()
        
        # Pydantic設定オブジェクト
        self.system = SystemConfig()
        self.bybit = BybitConfig()
        self.gemini = GeminiConfig()
        self.discord = DiscordConfig()
        self.database = DatabaseConfig()
        self.trading = TradingConfig()
    
    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
                logger.info(f"設定ファイルを読み込みました: {self.config_path}")
            else:
                logger.warning(f"設定ファイルが見つかりません: {self.config_path}")
                self._config_data = {}
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            self._config_data = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """設定値を設定"""
        keys = key.split('.')
        config = self._config_data
        
        # ネストした辞書を作成
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self) -> None:
        """設定をファイルに保存"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            logger.info(f"設定ファイルを保存しました: {self.config_path}")
        except Exception as e:
            logger.error(f"設定ファイルの保存に失敗しました: {e}")
    
    def get_sub_bot_config(self, bot_name: str) -> Dict[str, Any]:
        """サブボット設定を取得"""
        return self.get(f"sub_bots.{bot_name}", {})
    
    def get_market_phase_config(self, phase: str) -> Dict[str, Any]:
        """市場フェーズ設定を取得"""
        return self.get(f"market_phases.{phase}", {})
    
    def get_position_sizing_config(self) -> Dict[str, Any]:
        """ポジションサイジング設定を取得"""
        return self.get("position_sizing", {})
    
    def get_optimization_config(self) -> Dict[str, Any]:
        """最適化設定を取得"""
        return self.get("optimization", {})
    
    def validate_config(self) -> bool:
        """設定の妥当性を検証"""
        try:
            # 必須設定の確認
            required_settings = [
                "api.bybit.api_key",
                "api.bybit.secret_key",
                "api.gemini.api_keys"
            ]
            
            for setting in required_settings:
                if not self.get(setting):
                    logger.error(f"必須設定が不足しています: {setting}")
                    return False
            
            # APIキーの確認
            if not self.gemini.api_keys:
                logger.error("Gemini APIキーが設定されていません")
                return False
            
            logger.info("設定の妥当性検証が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"設定の妥当性検証に失敗しました: {e}")
            return False


# グローバル設定インスタンス
config = ConfigManager()
