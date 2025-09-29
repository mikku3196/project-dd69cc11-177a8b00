"""
自己進化型AIポートフォリオ自動売買システム - Gemini API クライアント
"""

import asyncio
import json
import random
from typing import Dict, List, Optional, Any, Tuple
import google.generativeai as genai
import logging

from ..core.config import config
from ..core.exceptions import GeminiAPIError

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini API クライアント"""
    
    def __init__(self):
        self.api_keys = config.gemini.api_keys
        self.model_name = config.gemini.model
        self.temperature = config.gemini.temperature
        self.max_tokens = config.gemini.max_tokens
        self.timeout = config.gemini.timeout
        self.retry_attempts = config.gemini.retry_attempts
        
        self.current_key_index = 0
        self._configure_api()
    
    def _configure_api(self) -> None:
        """API設定を初期化"""
        if not self.api_keys:
            raise GeminiAPIError("Gemini APIキーが設定されていません")
        
        # 最初のAPIキーで初期化
        genai.configure(api_key=self.api_keys[0])
        self.model = genai.GenerativeModel(self.model_name)
    
    def _rotate_api_key(self) -> None:
        """APIキーをローテーション"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            genai.configure(api_key=self.api_keys[self.current_key_index])
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"APIキーをローテーション: キー {self.current_key_index + 1}")
    
    async def _make_request_with_retry(self, prompt: str) -> str:
        """リトライ機能付きでAPIリクエストを実行"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                # APIキーをローテーション（初回以外）
                if attempt > 0:
                    self._rotate_api_key()
                
                # Gemini APIを呼び出し
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens
                    )
                )
                
                if response.text:
                    return response.text.strip()
                else:
                    raise GeminiAPIError("空のレスポンスが返されました")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini API リクエスト失敗 (試行 {attempt + 1}/{self.retry_attempts}): {e}")
                
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数バックオフ
        
        raise GeminiAPIError(f"全てのリトライが失敗しました: {last_error}")
    
    async def analyze_market_data(
        self,
        symbol: str,
        price_data: Dict[str, Any],
        technical_indicators: Dict[str, Any],
        sentiment_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """市場データを分析して取引判断を生成"""
        
        prompt = f"""
あなたは経験豊富な暗号資産トレーダーです。以下の市場データを分析し、取引判断を行ってください。

【市場データ】
- 通貨ペア: {symbol}
- 現在価格: {price_data.get('last_price', 'N/A')}
- 24時間変動率: {price_data.get('price_change_24h', 'N/A')}%
- 24時間高値: {price_data.get('high_24h', 'N/A')}
- 24時間安値: {price_data.get('low_24h', 'N/A')}
- 24時間出来高: {price_data.get('volume_24h', 'N/A')}

【テクニカル指標】
- RSI(14): {technical_indicators.get('rsi', 'N/A')}
- MACD: {technical_indicators.get('macd', 'N/A')}
- MACD Signal: {technical_indicators.get('macd_signal', 'N/A')}
- MACD Histogram: {technical_indicators.get('macd_histogram', 'N/A')}
- Bollinger Bands Upper: {technical_indicators.get('bb_upper', 'N/A')}
- Bollinger Bands Lower: {technical_indicators.get('bb_lower', 'N/A')}
- Moving Average (20): {technical_indicators.get('ma_20', 'N/A')}
- Moving Average (50): {technical_indicators.get('ma_50', 'N/A')}
- ATR(14): {technical_indicators.get('atr', 'N/A')}

【市場センチメント】
- センチメントスコア: {sentiment_score if sentiment_score is not None else 'N/A'}

【分析要求】
以下のJSON形式で回答してください：
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "reason": "判断理由の詳細説明",
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "expected_price_target": "目標価格（数値のみ）",
    "stop_loss_price": "損切り価格（数値のみ）",
    "position_size_recommendation": "SMALL" | "MEDIUM" | "LARGE"
}}

判断基準：
1. テクニカル分析の総合的な評価
2. 市場センチメントの影響
3. リスク管理の観点
4. 現在の市場環境への適応性

必ずJSON形式で回答し、その他の説明は含めないでください。
"""
        
        try:
            response_text = await self._make_request_with_retry(prompt)
            
            # JSONレスポンスをパース
            try:
                decision = json.loads(response_text)
                
                # 必須フィールドの検証
                required_fields = ['action', 'confidence', 'reason']
                for field in required_fields:
                    if field not in decision:
                        raise GeminiAPIError(f"必須フィールド '{field}' がレスポンスに含まれていません")
                
                # アクションの検証
                if decision['action'] not in ['BUY', 'SELL', 'HOLD']:
                    raise GeminiAPIError(f"無効なアクション: {decision['action']}")
                
                # 信頼度の検証
                if not (0.0 <= decision['confidence'] <= 1.0):
                    raise GeminiAPIError(f"信頼度が範囲外です: {decision['confidence']}")
                
                return decision
                
            except json.JSONDecodeError as e:
                raise GeminiAPIError(f"JSONパースエラー: {e}")
                
        except Exception as e:
            logger.error(f"市場データ分析に失敗しました: {e}")
            raise GeminiAPIError(f"市場データ分析エラー: {e}")
    
    async def analyze_news_sentiment(self, news_articles: List[Dict[str, Any]]) -> float:
        """ニュース記事のセンチメントを分析"""
        
        if not news_articles:
            return 0.0
        
        # 記事のタイトルと内容を結合
        combined_text = ""
        for article in news_articles[:5]:  # 最新5記事まで
            combined_text += f"タイトル: {article.get('title', '')}\n"
            combined_text += f"内容: {article.get('content', '')}\n\n"
        
        prompt = f"""
以下の暗号資産関連ニュース記事を分析し、市場への影響を評価してください。

【ニュース記事】
{combined_text}

【分析要求】
このニュースは暗号資産市場に対してどのような影響を与えると考えられますか？

以下の基準で評価してください：
- 非常にポジティブ: +1.0
- ポジティブ: +0.5
- ニュートラル: 0.0
- ネガティブ: -0.5
- 非常にネガティブ: -1.0

回答は数値のみで、-1.0から+1.0の範囲で答えてください。
例: 0.3
"""
        
        try:
            response_text = await self._make_request_with_retry(prompt)
            
            # 数値を抽出
            try:
                sentiment_score = float(response_text.strip())
                
                # 範囲チェック
                if not (-1.0 <= sentiment_score <= 1.0):
                    raise GeminiAPIError(f"センチメントスコアが範囲外です: {sentiment_score}")
                
                return sentiment_score
                
            except ValueError as e:
                raise GeminiAPIError(f"センチメントスコアのパースエラー: {e}")
                
        except Exception as e:
            logger.error(f"ニュースセンチメント分析に失敗しました: {e}")
            raise GeminiAPIError(f"ニュースセンチメント分析エラー: {e}")
    
    async def generate_trading_strategy_insights(
        self,
        performance_data: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """取引戦略の洞察を生成"""
        
        prompt = f"""
あなたは暗号資産取引戦略の専門家です。以下のパフォーマンスデータと市場環境を分析し、戦略の改善提案を行ってください。

【パフォーマンスデータ】
- 総リターン: {performance_data.get('total_return', 'N/A')}%
- シャープレシオ: {performance_data.get('sharpe_ratio', 'N/A')}
- 最大ドローダウン: {performance_data.get('max_drawdown', 'N/A')}%
- 勝率: {performance_data.get('win_rate', 'N/A')}%
- プロフィットファクター: {performance_data.get('profit_factor', 'N/A')}
- 総取引数: {performance_data.get('total_trades', 'N/A')}

【市場環境】
- 現在の市場フェーズ: {market_conditions.get('market_phase', 'N/A')}
- ボラティリティレベル: {market_conditions.get('volatility_level', 'N/A')}
- トレンド強度: {market_conditions.get('trend_strength', 'N/A')}

【分析要求】
以下のJSON形式で回答してください：
{{
    "strategy_assessment": "戦略の総合評価",
    "strengths": ["強み1", "強み2", "強み3"],
    "weaknesses": ["弱み1", "弱み2", "弱み3"],
    "improvement_suggestions": ["改善提案1", "改善提案2", "改善提案3"],
    "risk_recommendations": ["リスク管理提案1", "リスク管理提案2"],
    "market_adaptation": "現在の市場環境への適応提案",
    "confidence_level": 0.0-1.0
}}

必ずJSON形式で回答し、その他の説明は含めないでください。
"""
        
        try:
            response_text = await self._make_request_with_retry(prompt)
            
            # JSONレスポンスをパース
            try:
                insights = json.loads(response_text)
                
                # 必須フィールドの検証
                required_fields = ['strategy_assessment', 'strengths', 'weaknesses', 'improvement_suggestions']
                for field in required_fields:
                    if field not in insights:
                        raise GeminiAPIError(f"必須フィールド '{field}' がレスポンスに含まれていません")
                
                return insights
                
            except json.JSONDecodeError as e:
                raise GeminiAPIError(f"JSONパースエラー: {e}")
                
        except Exception as e:
            logger.error(f"戦略洞察生成に失敗しました: {e}")
            raise GeminiAPIError(f"戦略洞察生成エラー: {e}")
    
    async def optimize_parameters(
        self,
        current_params: Dict[str, Any],
        performance_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """パラメータ最適化の提案を生成"""
        
        prompt = f"""
あなたは暗号資産取引システムの最適化専門家です。以下の現在のパラメータとパフォーマンス履歴を分析し、最適化提案を行ってください。

【現在のパラメータ】
{json.dumps(current_params, indent=2, ensure_ascii=False)}

【パフォーマンス履歴】
{json.dumps(performance_history[-10:], indent=2, ensure_ascii=False)}

【分析要求】
以下のJSON形式で回答してください：
{{
    "parameter_recommendations": {{
        "stop_loss": "推奨値と理由",
        "take_profit": "推奨値と理由",
        "position_size": "推奨値と理由",
        "risk_per_trade": "推奨値と理由"
    }},
    "optimization_rationale": "最適化の根拠",
    "expected_improvement": "期待される改善効果",
    "risk_assessment": "最適化に伴うリスク評価",
    "implementation_priority": "HIGH" | "MEDIUM" | "LOW"
}}

必ずJSON形式で回答し、その他の説明は含めないでください。
"""
        
        try:
            response_text = await self._make_request_with_retry(prompt)
            
            # JSONレスポンスをパース
            try:
                optimization = json.loads(response_text)
                
                # 必須フィールドの検証
                required_fields = ['parameter_recommendations', 'optimization_rationale']
                for field in required_fields:
                    if field not in optimization:
                        raise GeminiAPIError(f"必須フィールド '{field}' がレスポンスに含まれていません")
                
                return optimization
                
            except json.JSONDecodeError as e:
                raise GeminiAPIError(f"JSONパースエラー: {e}")
                
        except Exception as e:
            logger.error(f"パラメータ最適化提案に失敗しました: {e}")
            raise GeminiAPIError(f"パラメータ最適化提案エラー: {e}")
