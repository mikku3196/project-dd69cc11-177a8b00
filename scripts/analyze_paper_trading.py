"""
ペーパー取引テスト - ログ分析スクリプト
"""
import json
import csv
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# UTF-8エンコーディング設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

class PaperTradingAnalyzer:
    """ペーパー取引テスト分析クラス"""
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
    
    def analyze_trades_csv(self, csv_file: str) -> Dict[str, Any]:
        """取引CSVファイルを分析"""
        csv_path = self.log_directory / csv_file
        
        if not csv_path.exists():
            return {"error": f"ファイルが見つかりません: {csv_path}"}
        
        trades = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                trades = list(reader)
        except Exception as e:
            return {"error": f"CSVファイル読み込みエラー: {e}"}
        
        if not trades:
            return {"error": "取引データがありません"}
        
        # 基本統計
        total_trades = len(trades)
        buy_trades = len([t for t in trades if t.get('action') == 'BUY'])
        sell_trades = len([t for t in trades if t.get('action') == 'SELL'])
        
        # ボット別統計
        bot_stats = {}
        for trade in trades:
            bot = trade.get('bot', 'unknown')
            if bot not in bot_stats:
                bot_stats[bot] = {'trades': 0, 'buy': 0, 'sell': 0}
            bot_stats[bot]['trades'] += 1
            if trade.get('action') == 'BUY':
                bot_stats[bot]['buy'] += 1
            elif trade.get('action') == 'SELL':
                bot_stats[bot]['sell'] += 1
        
        # 損益計算
        total_pnl = 0.0
        for trade in trades:
            try:
                pnl = float(trade.get('pnl', 0))
                total_pnl += pnl
            except (ValueError, TypeError):
                pass
        
        # 勝率計算
        profitable_trades = len([t for t in trades if float(t.get('pnl', 0)) > 0])
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'bot_stats': bot_stats,
            'avg_trade_size': total_pnl / total_trades if total_trades > 0 else 0
        }
    
    def analyze_performance_json(self, json_file: str) -> Dict[str, Any]:
        """パフォーマンスJSONファイルを分析"""
        json_path = self.log_directory / json_file
        
        if not json_path.exists():
            return {"error": f"ファイルが見つかりません: {json_path}"}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            return {"error": f"JSONファイル読み込みエラー: {e}"}
        
        test_summary = data.get('test_summary', {})
        
        return {
            'overall_return': test_summary.get('total_return_pct', 0),
            'initial_balance': test_summary.get('initial_balance', 0),
            'final_balance': test_summary.get('final_balance', 0),
            'total_trades': test_summary.get('total_trades', 0),
            'error_count': test_summary.get('error_count', 0),
            'duration_days': test_summary.get('duration_days', 0),
            'circuit_breaker_status': data.get('circuit_breaker_final_status', {}),
            'system_reliability': max(0, 100 - (test_summary.get('error_count', 0) / max(1, test_summary.get('total_trades', 1)) * 100))
        }
    
    def generate_report(self, trades_analysis: Dict[str, Any], performance_analysis: Dict[str, Any]) -> str:
        """分析結果からレポートを生成"""
        report = f"""
=== ペーパー取引テスト分析レポート ===
生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【総合パフォーマンス】
- 総リターン: {performance_analysis.get('overall_return', 0):.2f}%
- 初期残高: ${performance_analysis.get('initial_balance', 0):.2f}
- 最終残高: ${performance_analysis.get('final_balance', 0):.2f}
- テスト期間: {performance_analysis.get('duration_days', 0)}日

【取引統計】
- 総取引数: {trades_analysis.get('total_trades', 0)}
- 買い注文: {trades_analysis.get('buy_trades', 0)}
- 売り注文: {trades_analysis.get('sell_trades', 0)}
- 勝率: {trades_analysis.get('win_rate', 0):.2f}%
- 総損益: ${trades_analysis.get('total_pnl', 0):.2f}

【ボット別パフォーマンス】
"""
        
        bot_stats = trades_analysis.get('bot_stats', {})
        for bot, stats in bot_stats.items():
            report += f"- {bot}: {stats['trades']}回取引 (買い:{stats['buy']}, 売り:{stats['sell']})\n"
        
        report += f"""
【システム信頼性】
- エラー数: {performance_analysis.get('error_count', 0)}
- システム信頼性: {performance_analysis.get('system_reliability', 0):.2f}%
- サーキットブレーカー状態: {performance_analysis.get('circuit_breaker_status', {}).get('state', 'UNKNOWN')}

【推奨事項】
- 本番運用準備度: {'準備完了' if performance_analysis.get('overall_return', 0) > 0 else '要改善'}
- リスク管理: {'適切' if performance_analysis.get('error_count', 0) < 10 else '要強化'}
- 取引頻度: {'適切' if trades_analysis.get('total_trades', 0) > 10 else '要増加'}
        """
        
        return report
    
    def find_latest_logs(self) -> Dict[str, str]:
        """最新のログファイルを検索"""
        log_files = {}
        
        # 取引CSVファイル検索
        csv_files = list(self.log_directory.glob("trades_*.csv"))
        if csv_files:
            latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
            log_files['trades_csv'] = latest_csv.name
        
        # パフォーマンスJSONファイル検索
        json_files = list(self.log_directory.glob("performance_*.json"))
        if json_files:
            latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
            log_files['performance_json'] = latest_json.name
        
        return log_files

def main():
    """メイン関数"""
    analyzer = PaperTradingAnalyzer()
    
    # 最新のログファイルを検索
    log_files = analyzer.find_latest_logs()
    
    if not log_files:
        print("[ERROR] ログファイルが見つかりません")
        print("ペーパー取引テストを実行してください:")
        print("python scripts/run_paper_trading.py --quick")
        return
    
    print("=== ペーパー取引テスト分析 ===")
    print(f"検出されたログファイル:")
    for log_type, filename in log_files.items():
        print(f"- {log_type}: {filename}")
    
    # 分析実行
    trades_analysis = {}
    performance_analysis = {}
    
    if 'trades_csv' in log_files:
        print("\n取引データを分析中...")
        trades_analysis = analyzer.analyze_trades_csv(log_files['trades_csv'])
        if 'error' in trades_analysis:
            print(f"[ERROR] {trades_analysis['error']}")
        else:
            print(f"[SUCCESS] {trades_analysis['total_trades']}件の取引を分析")
    
    if 'performance_json' in log_files:
        print("パフォーマンスデータを分析中...")
        performance_analysis = analyzer.analyze_performance_json(log_files['performance_json'])
        if 'error' in performance_analysis:
            print(f"[ERROR] {performance_analysis['error']}")
        else:
            print(f"[SUCCESS] パフォーマンス分析完了")
    
    # レポート生成
    if trades_analysis and performance_analysis and 'error' not in trades_analysis and 'error' not in performance_analysis:
        report = analyzer.generate_report(trades_analysis, performance_analysis)
        print(report)
        
        # レポートをファイルに保存
        report_file = analyzer.log_directory / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nレポートを保存しました: {report_file}")
    else:
        print("[ERROR] 分析に失敗しました")

if __name__ == "__main__":
    main()
