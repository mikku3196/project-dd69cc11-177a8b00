import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services.bybit_client import BybitClient

class SubBot:
    """
    すべての取引戦略サブボットの基盤となる基本クラス。
    共通のプロパティとメソッドの枠組みを定義する。
    """

    def __init__(
        self,
        bot_config: Dict[str, Any],
        bybit_client: BybitClient,
        db_session: Session
    ):
        """
        サブボットを初期化する。

        Args:
            bot_config (Dict[str, Any]): config.tomlから読み込まれたこのボット用の設定。
            bybit_client (BybitClient): Bybit APIと通信するためのクライアントインスタンス。
            db_session (Session): データベースセッション。
        """
        # --- 基本情報 ---
        self.name: str = bot_config.get("name", "UnnamedBot")
        self.enabled: bool = bot_config.get("enabled", False)
        self.symbol: str = bot_config.get("symbol", "BTC/USDT")

        # --- 外部サービスとの連携 ---
        self.bybit_client = bybit_client
        self.db = db_session
        
        # --- 戦略パラメータ ---
        # config.tomlから読み込んだ戦略パラメータを保持
        self.strategy_params: Dict[str, Any] = bot_config.get("strategy_params", {})
        
        # --- 状態管理 ---
        self.last_run_time: float = 0
        self.is_running: bool = False

        print(f"SubBot '{self.name}' for symbol '{self.symbol}' has been initialized.")

    def start(self):
        """ボットの実行を開始する。"""
        if self.enabled:
            self.is_running = True
            print(f"SubBot '{self.name}' has been started.")
        else:
            print(f"SubBot '{self.name}' is disabled and will not start.")

    def stop(self):
        """ボットの実行を停止する。"""
        self.is_running = False
        print(f"SubBot '{self.name}' has been stopped.")

    def run(self):
        """
        ボットのメインループ。定期的に呼び出されることを想定。
        このメソッドをサブクラスでオーバーライドして、具体的な取引ロジックを実装する。
        """
        if not self.is_running or not self.enabled:
            return

        current_time = time.time()
        # 前回の実行から一定時間が経過したかなどをチェックする（将来的に実装）
        # if current_time - self.last_run_time < 60:
        #     return

        print(f"[{self.name}] Running main logic cycle...")
        self._make_decision()
        self.last_run_time = current_time

    def _make_decision(self):
        """
        売買判断を行うコアロジック。
        サブクラスで必ずオーバーライド（上書き）する必要がある。
        """
        # この基本クラスでは具体的な判断は行わない
        print(f"[{self.name}] Making a decision... (To be implemented in subclass)")
        pass

    def _execute_order(self, side: str, qty: float):
        """
        注文を実行するヘルパーメソッド。
        サブクラスから利用する。
        """
        print(f"[{self.name}] Attempting to execute {side} order for {qty} {self.symbol}...")
        # ここに将来的に bybit_client を使った注文実行コードが入る
        pass


# --- 動作確認用のコード ---
if __name__ == '__main__':
    print("--- SubBot Class Test ---")

    # ダミーの設定とオブジェクトを作成
    mock_config = {
        "name": "TestBot",
        "enabled": True,
        "symbol": "BTC/USDT",
        "strategy_params": {"rsi_period": 14}
    }
    mock_bybit_client = None  # テストなのでNone
    mock_db_session = None    # テストなのでNone

    # サブボットをインスタンス化
    bot = SubBot(
        bot_config=mock_config,
        bybit_client=mock_bybit_client,
        db_session=mock_db_session
    )

    # 基本的なメソッドをテスト
    bot.start()
    bot.run()
    bot.stop()

    print(f"\nBot name: {bot.name}")
    print(f"Is enabled: {bot.enabled}")
    print(f"Strategy params: {bot.strategy_params}")
