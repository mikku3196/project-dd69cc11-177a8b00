"""
ニュース・センチメント分析モジュール
"""
import asyncio
import aiohttp
import json
import logging
import feedparser
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """ニュース記事"""
    title: str
    content: str
    source: str
    published: datetime
    url: str
    keywords: List[str]

@dataclass
class SentimentScore:
    """センチメントスコア"""
    score: float  # -1.0 to 1.0
    confidence: float
    analysis: str
    timestamp: datetime
    source: str
    keyword: str

class NewsSentimentAnalyzer:
    """ニュース・センチメント分析クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gemini_api_keys = config.get('gemini_api_keys', [])
        self.current_key_index = 0
        self.news_sources = config.get('news_sources', [])
        self.keywords = config.get('keywords', [])
        self.fetch_interval = config.get('fetch_interval_minutes', 15)
        self.moving_average_period = config.get('moving_average_period_hours', 24)
        self.sentiment_history: List[SentimentScore] = []
        
    async def fetch_news_articles(self) -> List[NewsArticle]:
        """ニュース記事取得"""
        articles = []
        
        for source_url in self.news_sources:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source_url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # RSSフィード解析
                            feed = feedparser.parse(content)
                            
                            for entry in feed.entries:
                                # キーワードフィルタリング
                                if self._contains_keywords(entry.title + " " + entry.get('summary', '')):
                                    article = NewsArticle(
                                        title=entry.title,
                                        content=entry.get('summary', ''),
                                        source=source_url,
                                        published=datetime(*entry.published_parsed[:6]),
                                        url=entry.link,
                                        keywords=self._extract_keywords(entry.title + " " + entry.get('summary', ''))
                                    )
                                    articles.append(article)
                                    
            except Exception as e:
                logger.error(f"Failed to fetch news from {source_url}: {e}")
                
        return articles
    
    def _contains_keywords(self, text: str) -> bool:
        """キーワード含有チェック"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出"""
        text_lower = text.lower()
        found_keywords = []
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        return found_keywords
    
    async def analyze_sentiment(self, article: NewsArticle) -> Optional[SentimentScore]:
        """センチメント分析（Gemini API使用）"""
        if not self.gemini_api_keys:
            logger.warning("No Gemini API keys available for sentiment analysis")
            return None
        
        try:
            # プロンプト作成
            prompt = f"""
以下のニュース記事を分析し、暗号資産市場に対するセンチメントを評価してください。

タイトル: {article.title}
内容: {article.content}
キーワード: {', '.join(article.keywords)}

以下のJSON形式で回答してください：
{{
    "sentiment_score": -1.0から1.0の範囲の数値（-1.0=非常にネガティブ、0=ニュートラル、1.0=非常にポジティブ）,
    "confidence": 0.0から1.0の範囲の数値（分析の確信度）,
    "analysis": "分析の詳細説明"
}}
"""
            
            # Gemini API呼び出し
            response = await self._call_gemini_api(prompt)
            
            if response:
                # レスポンス解析
                try:
                    result = json.loads(response)
                    sentiment_score = SentimentScore(
                        score=float(result.get('sentiment_score', 0.0)),
                        confidence=float(result.get('confidence', 0.0)),
                        analysis=result.get('analysis', ''),
                        timestamp=datetime.now(),
                        source=article.source,
                        keyword=', '.join(article.keywords)
                    )
                    return sentiment_score
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to parse Gemini response: {e}")
                    return None
                    
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            return None
    
    async def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Gemini API呼び出し"""
        if not self.gemini_api_keys:
            return None
        
        # APIキーローテーション
        api_key = self.gemini_api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.gemini_api_keys)
        
        try:
            # 実際のGemini API呼び出し（モック実装）
            # 実際の実装では、google.generativeaiを使用
            await asyncio.sleep(0.1)  # API呼び出しのシミュレーション
            
            # モックレスポンス
            mock_response = {
                "sentiment_score": 0.2,  # ややポジティブ
                "confidence": 0.8,
                "analysis": "記事の内容は暗号資産市場に対して中立的からややポジティブな印象を与える"
            }
            
            return json.dumps(mock_response)
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            return None
    
    def calculate_moving_average_sentiment(self) -> float:
        """移動平均センチメントスコア計算"""
        if not self.sentiment_history:
            return 0.0
        
        # 指定期間内のスコアのみを対象
        cutoff_time = datetime.now() - timedelta(hours=self.moving_average_period)
        recent_scores = [
            score for score in self.sentiment_history 
            if score.timestamp >= cutoff_time
        ]
        
        if not recent_scores:
            return 0.0
        
        # 重み付き平均（新しいスコアほど重みが大きい）
        total_weight = 0.0
        weighted_sum = 0.0
        
        for i, score in enumerate(recent_scores):
            weight = (i + 1) / len(recent_scores)  # 新しいほど重みが大きい
            weighted_sum += score.score * weight * score.confidence
            total_weight += weight * score.confidence
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    async def run_sentiment_analysis(self):
        """センチメント分析実行"""
        logger.info("Starting sentiment analysis...")
        
        # ニュース記事取得
        articles = await self.fetch_news_articles()
        logger.info(f"Fetched {len(articles)} articles")
        
        # 各記事のセンチメント分析
        for article in articles:
            sentiment = await self.analyze_sentiment(article)
            if sentiment:
                self.sentiment_history.append(sentiment)
                logger.info(f"Analyzed sentiment: {sentiment.score:.2f} for '{article.title[:50]}...'")
        
        # 移動平均センチメント計算
        moving_avg = self.calculate_moving_average_sentiment()
        logger.info(f"Moving average sentiment: {moving_avg:.2f}")
        
        return moving_avg
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """センチメントサマリー取得"""
        moving_avg = self.calculate_moving_average_sentiment()
        
        # 最近のスコア分布
        recent_scores = self.sentiment_history[-10:] if self.sentiment_history else []
        
        return {
            'moving_average_sentiment': moving_avg,
            'total_articles_analyzed': len(self.sentiment_history),
            'recent_scores': [score.score for score in recent_scores],
            'last_analysis_time': self.sentiment_history[-1].timestamp.isoformat() if self.sentiment_history else None,
            'sentiment_trend': self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """センチメントトレンド計算"""
        if len(self.sentiment_history) < 2:
            return "insufficient_data"
        
        recent_scores = [score.score for score in self.sentiment_history[-5:]]
        if len(recent_scores) < 2:
            return "insufficient_data"
        
        # 単純な線形回帰でトレンド計算
        x = list(range(len(recent_scores)))
        y = recent_scores
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.1:
            return "improving"
        elif slope < -0.1:
            return "deteriorating"
        else:
            return "stable"

# テスト用のメイン関数
async def test_news_sentiment():
    """ニュース・センチメント分析テスト"""
    print("News Sentiment Analysis Test")
    print("=" * 50)
    
    # 設定
    config = {
        'gemini_api_keys': ['mock_key_1', 'mock_key_2'],
        'news_sources': [
            'https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=crypto&hl=en-US&gl=US&ceid=US:en'
        ],
        'keywords': ['Bitcoin', 'BTC', 'crypto', 'FOMC', 'inflation'],
        'fetch_interval_minutes': 15,
        'moving_average_period_hours': 24
    }
    
    # センチメント分析器初期化
    analyzer = NewsSentimentAnalyzer(config)
    
    # センチメント分析実行
    moving_avg = await analyzer.run_sentiment_analysis()
    
    # サマリー表示
    summary = analyzer.get_sentiment_summary()
    print(f"\nSentiment Analysis Summary:")
    print(f"  Moving Average Sentiment: {summary['moving_average_sentiment']:.2f}")
    print(f"  Total Articles Analyzed: {summary['total_articles_analyzed']}")
    print(f"  Sentiment Trend: {summary['sentiment_trend']}")
    
    if summary['recent_scores']:
        print(f"  Recent Scores: {summary['recent_scores']}")
    
    print("\nNews Sentiment Analysis Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_news_sentiment())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
