from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.bybit_client import BybitClient
from app.bots.sub_bot import SubBot
from app.bots.simple_bot import SimpleBot

class MasterBot:
    """
    すべてのサブボットを統括管理し、定期的に実行する司令塔クラス。
    """

    def __init__(self):
        print("Initializing MasterBot...")
        self.db_session = SessionLocal()
        self.bybit_client = BybitClient()
        self.scheduler = BackgroundScheduler()
        self.sub_bots: List[SubBot] = []

        self._load_bots()

    def _load_bots(self):
        """
        config.tomlからサブボットの設定を読み込み、インスタンス化してリストに追加する。
        """
        bot_configs = settings.toml_config.get("sub_bots", [])
        print(f"Found {len(bot_configs)} bot configurations in config.toml.")

        for config in bot_configs:
            bot_name = config.get("name", "Unknown")
            
            # ここで戦略タイプに応じてボットクラスを切り替える（将来的に拡張）
            # 今はすべてのボットをSimpleBotとして読み込む
            try:
                bot_instance = SimpleBot(
                    bot_config=config,
                    bybit_client=self.bybit_client,
                    db_session=self.db_session
                )
                self.sub_bots.append(bot_instance)
            except Exception as e:
                print(f"Failed to initialize bot '{bot_name}': {e}")

    def start_all_bots(self):
        """
        保持しているすべてのサブボットを開始し、スケジューラを起動する。
        """
        if not self.sub_bots:
            print("No sub-bots loaded. MasterBot will not start.")
            return

        print("Starting all enabled sub-bots...")
        for bot in self.sub_bots:
            bot.start()

        # 各ボットのrunメソッドを10秒ごとに実行するジョブを登録
        self.scheduler.add_job(
            self._run_all_bots,
            'interval',
            seconds=10,
            id='run_all_bots_job'
        )
        self.scheduler.start()
        print("Scheduler started. Bots will run every 10 seconds.")

    def stop_all_bots(self):
        """
        すべてのサブボットとスケジューラを安全に停止する。
        """
        print("Stopping scheduler and all sub-bots...")
        if self.scheduler.running:
            self.scheduler.shutdown()
        
        for bot in self.sub_bots:
            bot.stop()
        
        self.db_session.close()
        print("MasterBot has been stopped.")

    def _run_all_bots(self):
        """スケジューラによって定期的に呼び出されるメソッド。"""
        print("\n" + "="*50)
        print("MasterBot: Triggering bot run cycle...")
        for bot in self.sub_bots:
            try:
                bot.run()
            except Exception as e:
                print(f"Error running bot '{bot.name}': {e}")
        print("="*50 + "\n")

# マスターボットの唯一のインスタンス（シングルトン）
master_bot = MasterBot()
