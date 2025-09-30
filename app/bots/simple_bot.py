import random
import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.bybit_client import BybitClient
from app.bots.sub_bot import SubBot

class SimpleBot(SubBot):
    """
    SubBotクラスを継承した、シンプルなテスト用ボット。
    一定の確率で売買判断を行うダミーロジックを持つ。
    """

    def __init__(
        self,
        bot_config: Dict[str, Any],
        bybit_client: BybitClient,
        db_session: Session
    ):
        # 親クラス(SubBot)の初期化処理を呼び出す
        super().__init__(bot_config, bybit_client, db_session)
        
        # このボット固有の状態
        self.decision_count = 0
        print(f"SimpleBot '{self.name}' has been fully initialized.")

    def _make_decision(self):
        """
        SubBotの意思決定メソッドをオーバーライド（上書き）する。
        これがこのボットのコアロジックとなる。
        """
        self.decision_count += 1
        print(f"[{self.name}] Making decision #{self.decision_count}...")

        # 5回に1回の確率で「買い」と判断する
        if self.decision_count % 5 == 0:
            print(f"[{self.name}] Decision: BUY signal generated based on simple logic.")
            
            # config.tomlで設定された基本ロット数を取得
            base_lot = self.bot_config.get("base_lot", 0.001)
            
            # 注文実行メソッドを呼び出す
            # (現時点では注文は実行されず、メッセージが表示されるだけ)
            self._execute_order(side="BUY", qty=base_lot)
        else:
            print(f"[{self.name}] Decision: HOLD. No signal generated.")

# --- 動作確認用のコード ---
if __name__ == '__main__':
    from app.core.config import settings

    print("--- SimpleBot Class Test ---")

    # config.tomlから "SubBot-A (Stable)" の設定を読み込む
    try:
        bot_configs = settings.toml_config.get("sub_bots", [])
        simple_bot_config = next((c for c in bot_configs if c["name"] == "SubBot-A (Stable)"), None)
        
        if not simple_bot_config:
            raise ValueError("Configuration for 'SubBot-A (Stable)' not found in config.toml")

    except Exception as e:
        print(f"Error loading config: {e}")
        # config.tomlがない場合や設定がない場合のためのダミー設定
        simple_bot_config = {
            "name": "FallbackTestBot",
            "enabled": True,
            "symbol": "BTC/USDT",
            "base_lot": 0.001,
            "strategy_params": {}
        }
    
    # ダミーのBybitクライアントとDBセッション
    mock_bybit_client = None
    mock_db_session = None

    # SimpleBotをインスタンス化
    simple_bot = SimpleBot(
        bot_config=simple_bot_config,
        bybit_client=mock_bybit_client,
        db_session=mock_db_session
    )

    # ボットを開始し、複数回実行してロジックをテストする
    simple_bot.start()
    for i in range(10):
        print(f"\n--- Cycle {i+1} ---")
        simple_bot.run()
        time.sleep(0.1) # 実行間隔を模倣

    simple_bot.stop()
