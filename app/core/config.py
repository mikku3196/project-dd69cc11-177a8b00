import os
import toml
from dotenv import load_dotenv
from typing import List
from pathlib import Path

# .envファイルから環境変数を読み込む
load_dotenv()

# プロジェクトのルートディレクトリを基準に設定ファイルを読み込む
# このファイル (config.py) の2階層上がプロジェクトルートになる
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT_DIR / "config.toml"


class Settings:
    # .envから読み込む設定
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY")
    BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET")
    GEMINI_API_KEYS: List[str] = os.getenv("GEMINI_API_KEYS", "").split(',')
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # config.tomlを読み込む
    def __init__(self, config_path: Path = CONFIG_PATH):
        try:
            # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
            # 修正点: encoding="utf-8" を追加
            # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
            with open(config_path, "r", encoding="utf-8") as f:
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
    
# シングルトンインスタンスとして設定をロード
settings = Settings()