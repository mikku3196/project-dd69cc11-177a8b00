"""
マスターボットテストスクリプト
"""
import asyncio
import logging
import sys
import json
from datetime import datetime
import io

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# プロジェクトルートをパスに追加
sys.path.append('.')

from src.bots.master_bot import MasterBot, RiskLevel

logger = logging.getLogger(__name__)

class MasterBotTester:
    """マスターボットテストクラス"""
    
    def __init__(self):
        self.master_bot = None
        self.test_results = []
    
    async def test_initialization(self):
        """初期化テスト"""
        print("=== マスターボット初期化テスト ===")
        
        try:
            config = {
                'risk_level': 'safe',
                'rebalance_interval_days': 30
            }
            
            self.master_bot = MasterBot(config)
            
            # 初期設定確認
            assert self.master_bot.allocation['stable'] == 0.4
            assert self.master_bot.allocation['balanced'] == 0.4
            assert self.master_bot.allocation['aggressive'] == 0.2
            
            print("✅ 初期配分設定: OK")
            print(f"   - stable: {self.master_bot.allocation['stable']:.1%}")
            print(f"   - balanced: {self.master_bot.allocation['balanced']:.1%}")
            print(f"   - aggressive: {self.master_bot.allocation['aggressive']:.1%}")
            
            # リスク制御設定確認
            risk_control = self.master_bot.risk_control
            assert risk_control['max_drawdown'] == 0.15
            assert risk_control['max_loss_per_trade'] == 0.02
            
            print("✅ リスク制御設定: OK")
            print(f"   - 最大ドローダウン: {risk_control['max_drawdown']:.1%}")
            print(f"   - 1トレード最大損失: {risk_control['max_loss_per_trade']:.1%}")
            print(f"   - 同時取引上限: {risk_control['max_concurrent_trades']}件")
            
            # 評価重み付け確認
            weights = self.master_bot.evaluation_weights
            assert weights['win_rate'] == 0.35
            assert weights['return'] == 0.35
            
            print("✅ 評価重み付け: OK")
            print(f"   - 勝率: {weights['win_rate']:.1%}")
            print(f"   - リターン: {weights['return']:.1%}")
            print(f"   - ドローダウン: {weights['drawdown']:.1%}")
            print(f"   - 一貫性: {weights['consistency']:.1%}")
            
            self.test_results.append(("初期化テスト", "PASS", "すべての設定が正しく初期化されました"))
            
        except Exception as e:
            print(f"❌ 初期化テスト: FAILED - {e}")
            self.test_results.append(("初期化テスト", "FAILED", str(e)))
    
    async def test_sub_bot_management(self):
        """サブボット管理テスト"""
        print("\n=== サブボット管理テスト ===")
        
        try:
            # サブボット初期化
            await self.master_bot._initialize_sub_bots()
            
            # サブボット数確認
            assert len(self.master_bot.sub_bots) == 3
            assert 'stable' in self.master_bot.sub_bots
            assert 'balanced' in self.master_bot.sub_bots
            assert 'aggressive' in self.master_bot.sub_bots
            
            print("✅ サブボット初期化: OK")
            print(f"   - サブボット数: {len(self.master_bot.sub_bots)}")
            
            # サブボット状態確認
            for bot_name, bot in self.master_bot.sub_bots.items():
                status = await bot.get_status()
                assert status['status'] == 'running'
                print(f"   - {bot_name}: {status['status']}")
            
            print("✅ サブボット状態: OK")
            
            self.test_results.append(("サブボット管理テスト", "PASS", "すべてのサブボットが正常に初期化されました"))
            
        except Exception as e:
            print(f"❌ サブボット管理テスト: FAILED - {e}")
            self.test_results.append(("サブボット管理テスト", "FAILED", str(e)))
    
    async def test_performance_collection(self):
        """パフォーマンス収集テスト"""
        print("\n=== パフォーマンス収集テスト ===")
        
        try:
            # パフォーマンス収集
            await self.master_bot._collect_performance()
            
            # パフォーマンスデータ確認
            assert len(self.master_bot.performance_data) == 3
            
            for bot_name, performance in self.master_bot.performance_data.items():
                assert performance.win_rate > 0
                assert performance.total_return > 0
                assert performance.max_drawdown > 0
                assert performance.trade_count > 0
                
                print(f"✅ {bot_name} パフォーマンス:")
                print(f"   - 勝率: {performance.win_rate:.1%}")
                print(f"   - リターン: {performance.total_return:.1%}")
                print(f"   - ドローダウン: {performance.max_drawdown:.1%}")
                print(f"   - 取引数: {performance.trade_count}")
            
            self.test_results.append(("パフォーマンス収集テスト", "PASS", "すべてのサブボットのパフォーマンスが正常に収集されました"))
            
        except Exception as e:
            print(f"❌ パフォーマンス収集テスト: FAILED - {e}")
            self.test_results.append(("パフォーマンス収集テスト", "FAILED", str(e)))
    
    async def test_rebalance_logic(self):
        """再配分ロジックテスト"""
        print("\n=== 再配分ロジックテスト ===")
        
        try:
            # ボットスコア計算
            scores = self.master_bot._calculate_bot_scores()
            
            assert len(scores) == 3
            assert all(score > 0 for score in scores.values())
            
            print("✅ ボットスコア計算: OK")
            for bot_name, score in scores.items():
                print(f"   - {bot_name}: {score:.3f}")
            
            # 新しい配分計算
            new_allocation = self.master_bot._calculate_new_allocation(scores)
            
            # 配分合計確認
            total_allocation = sum(new_allocation.values())
            assert abs(total_allocation - 1.0) < 0.01
            
            # 配分制限確認
            for bot_name, allocation in new_allocation.items():
                assert 0.1 <= allocation <= 0.6
            
            print("✅ 配分計算: OK")
            print(f"   - 合計配分: {total_allocation:.3f}")
            for bot_name, allocation in new_allocation.items():
                print(f"   - {bot_name}: {allocation:.1%}")
            
            self.test_results.append(("再配分ロジックテスト", "PASS", "再配分ロジックが正常に動作しました"))
            
        except Exception as e:
            print(f"❌ 再配分ロジックテスト: FAILED - {e}")
            self.test_results.append(("再配分ロジックテスト", "FAILED", str(e)))
    
    async def test_risk_monitoring(self):
        """リスク監視テスト"""
        print("\n=== リスク監視テスト ===")
        
        try:
            # リスク指標計算
            risk_metrics = await self.master_bot._calculate_risk_metrics()
            
            assert risk_metrics.current_drawdown >= 0
            assert risk_metrics.daily_loss >= 0
            assert risk_metrics.concurrent_trades >= 0
            
            print("✅ リスク指標計算: OK")
            print(f"   - 現在のドローダウン: {risk_metrics.current_drawdown:.1%}")
            print(f"   - 日次損失: {risk_metrics.daily_loss:.1%}")
            print(f"   - 同時取引数: {risk_metrics.concurrent_trades}")
            
            # リスク制限チェック
            risk_check = await self.master_bot._check_risk_limits(risk_metrics)
            
            print(f"✅ リスク制限チェック: OK (制限超過: {risk_check})")
            
            self.test_results.append(("リスク監視テスト", "PASS", "リスク監視が正常に動作しました"))
            
        except Exception as e:
            print(f"❌ リスク監視テスト: FAILED - {e}")
            self.test_results.append(("リスク監視テスト", "FAILED", str(e)))
    
    async def test_status_reporting(self):
        """状態レポートテスト"""
        print("\n=== 状態レポートテスト ===")
        
        try:
            # 状態取得
            status = self.master_bot.get_status()
            
            # 必須フィールド確認
            required_fields = ['is_running', 'risk_level', 'allocation', 'risk_metrics', 'performance_data']
            for field in required_fields:
                assert field in status
            
            print("✅ 状態レポート: OK")
            print(f"   - 稼働状態: {status['is_running']}")
            print(f"   - リスクレベル: {status['risk_level']}")
            print(f"   - 配分: {status['allocation']}")
            
            # JSON出力テスト
            json_output = json.dumps(status, indent=2, ensure_ascii=False)
            assert len(json_output) > 100
            
            print("✅ JSON出力: OK")
            
            self.test_results.append(("状態レポートテスト", "PASS", "状態レポートが正常に生成されました"))
            
        except Exception as e:
            print(f"❌ 状態レポートテスト: FAILED - {e}")
            self.test_results.append(("状態レポートテスト", "FAILED", str(e)))
    
    async def run_all_tests(self):
        """全テスト実行"""
        print("🚀 マスターボットテスト開始")
        print("=" * 50)
        
        # テスト実行
        await self.test_initialization()
        await self.test_sub_bot_management()
        await self.test_performance_collection()
        await self.test_rebalance_logic()
        await self.test_risk_monitoring()
        await self.test_status_reporting()
        
        # 結果サマリー
        print("\n" + "=" * 50)
        print("📊 テスト結果サマリー")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, result, message in self.test_results:
            status_icon = "✅" if result == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result}")
            print(f"   {message}")
            
            if result == "PASS":
                passed += 1
            else:
                failed += 1
        
        print(f"\n📈 結果: {passed}件成功, {failed}件失敗")
        
        if failed == 0:
            print("🎉 すべてのテストが成功しました！")
            return True
        else:
            print("⚠️ 一部のテストが失敗しました。")
            return False


async def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    tester = MasterBotTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🚀 マスターボットのコアロジックが正常に動作します！")
        print("次のステップ: Webダッシュボードの実装")
    else:
        print("\n❌ マスターボットに問題があります。修正が必要です。")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] ユーザーによる中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 予期しないエラー: {e}")
        sys.exit(1)
