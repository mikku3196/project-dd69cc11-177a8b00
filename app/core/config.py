import os
import toml
from dotenv import load_dotenv
from typing import List

# .envファイルから環境変数を読み込む
load_dotenv()

class Settings:
    # .envから読み込む設定
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY")
    BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET")
    GEMINI_API_KEYS: List[str] = os.getenv("GEMINI_API_KEYS", "").split(',')
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # config.tomlを読み込む
    def __init__(self, config_path: str = "config.toml"):
        try:
            with open(config_path, "r") as f:
                self.toml_config = toml.load(f)
        except FileNotFoundError:
            print(f"Warning: {config_path} not found. Using default settings.")
            self.toml_config = {}

    @property
    def general(self):
        return self.toml_config.get("general", {})

    @property
    def database(self):
        return self.toml_config.get("database", {})

    @property
    def master_bot(self):
        return self.toml_config.get("master_bot", {})
    
    # ... 他のセクションも同様にプロパティとして定義 ...

# シングルトンインスタンスとして設定をロード
settings = Settings()
