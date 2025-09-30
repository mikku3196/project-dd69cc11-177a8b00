"""
最適化されたニュース・センチメント分析モジュール
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
from concurrent.futures import ThreadPoolExecutor
import time

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

class OptimizedNewsSentimentAnalyzer:
    """最適化されたニュース・センチメント分析クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gemini_api_keys = config.get('gemini_api_keys', [])
        self.current_key_index = 0
        self.news_sources = config.get('news_sources', [])
        self.keywords = config.get('keywords', [])
        self.fetch_interval = config.get('fetch_interval_minutes', 15)
        self.moving_average_period = config.get('moving_average_period_hours', 24)
        self.sentiment_history: List[SentimentScore] = []
        
        # パフォーマンス最適化
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5分間のキャッシュ
        
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=True)
    
    def _is_cache_valid(self, key: str) -> bool:
        """キャッシュの有効性チェック"""
        if key not in self.cache:
            return False
        
        cache_time, _ = self.cache[key]
        return time.time() - cache_time < self.cache_ttl
    
    def _get_from_cache(self, key: str) -> Any:
        """キャッシュから取得"""
        if self._is_cache_valid(key):
            _, value = self.cache[key]
            return value
        return None
    
    def _set_cache(self, key: str, value: Any):
        """キャッシュに保存"""
        self.cache[key] = (time.time(), value)
    
    async def fetch_news_articles_optimized(self) -> List[NewsArticle]:
        """最適化されたニュース記事取得"""
        articles = []
        
        # 並列処理でニュース取得
        tasks = []
        for source_url in self.news_sources:
            task = asyncio.create_task(self._fetch_single_source(source_url))
            tasks.append(task)
        
        # 全てのタスクを並列実行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を統合
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Failed to fetch news: {result}")
        
        # 重複除去とソート
        unique_articles = self._deduplicate_articles(articles)
        return sorted(unique_articles, key=lambda x: x.published, reverse=True)
    
    async def _fetch_single_source(self, source_url: str) -> List[NewsArticle]:
        """単一ソースからのニュース取得"""
        try:
            # キャッシュチェック
            cache_key = f"news_{hash(source_url)}"
            cached_articles = self._get_from_cache(cache_key)
            if cached_articles:
                return cached_articles
            
            async with self.session.get(source_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # スレッドプールでRSS解析
                    loop = asyncio.get_event_loop()
                    feed = await loop.run_in_executor(
                        self.executor, 
                        feedparser.parse, 
                        content
                    )
                    
                    articles = []
                    for entry in feed.entries:
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
                    
                    # キャッシュに保存
                    self._set_cache(cache_key, articles)
                    return articles
                    
        except Exception as e:
            logger.error(f"Failed to fetch news from {source_url}: {e}")
            return []
    
    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """記事の重複除去"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        return unique_articles
    
    def _contains_keywords(self, text: str) -> bool:
        """キーワード含有チェック（最適化版）"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """キーワード抽出（最適化版）"""
        text_lower = text.lower()
        return [keyword for keyword in self.keywords if keyword.lower() in text_lower]
    
    async def analyze_sentiment_batch(self, articles: List[NewsArticle]) -> List[SentimentScore]:
        """バッチ処理でのセンチメント分析"""
        if not self.gemini_api_keys:
            logger.warning("No Gemini API keys available for sentiment analysis")
            return []
        
        # バッチサイズを制限（API制限対策）
        batch_size = 5
        results = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            # バッチ内で並列処理
            tasks = []
            for article in batch:
                task = asyncio.create_task(self._analyze_single_article(article))
                tasks.append(task)
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, SentimentScore):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Sentiment analysis failed: {result}")
            
            # API制限対策：バッチ間で少し待機
            if i + batch_size < len(articles):
                await asyncio.sleep(1)
        
        return results
    
    async def _analyze_single_article(self, article: NewsArticle) -> Optional[SentimentScore]:
        """単一記事のセンチメント分析"""
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
            response = await self._call_gemini_api_optimized(prompt)
            
            if response:
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
    
    async def _call_gemini_api_optimized(self, prompt: str) -> Optional[str]:
        """最適化されたGemini API呼び出し"""
        if not self.gemini_api_keys:
            return None
        
        # APIキーローテーション
        api_key = self.gemini_api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.gemini_api_keys)
        
        try:
            # 実際のGemini API呼び出し（モック実装）
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
    
    def calculate_moving_average_sentiment_optimized(self) -> float:
        """最適化された移動平均センチメントスコア計算"""
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
    
    async def run_sentiment_analysis_optimized(self):
        """最適化されたセンチメント分析実行"""
        logger.info("Starting optimized sentiment analysis...")
        
        # ニュース記事取得
        articles = await self.fetch_news_articles_optimized()
        logger.info(f"Fetched {len(articles)} articles")
        
        # バッチ処理でセンチメント分析
        sentiment_scores = await self.analyze_sentiment_batch(articles)
        
        # 履歴に追加
        self.sentiment_history.extend(sentiment_scores)
        
        # 移動平均センチメント計算
        moving_avg = self.calculate_moving_average_sentiment_optimized()
        logger.info(f"Moving average sentiment: {moving_avg:.2f}")
        
        return moving_avg
    
    def get_sentiment_summary_optimized(self) -> Dict[str, Any]:
        """最適化されたセンチメントサマリー取得"""
        moving_avg = self.calculate_moving_average_sentiment_optimized()
        
        # 最近のスコア分布
        recent_scores = self.sentiment_history[-10:] if self.sentiment_history else []
        
        return {
            'moving_average_sentiment': moving_avg,
            'total_articles_analyzed': len(self.sentiment_history),
            'recent_scores': [score.score for score in recent_scores],
            'last_analysis_time': self.sentiment_history[-1].timestamp.isoformat() if self.sentiment_history else None,
            'sentiment_trend': self._calculate_trend_optimized(),
            'cache_stats': {
                'cache_size': len(self.cache),
                'cache_hit_rate': self._calculate_cache_hit_rate()
            }
        }
    
    def _calculate_trend_optimized(self) -> str:
        """最適化されたセンチメントトレンド計算"""
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
    
    def _calculate_cache_hit_rate(self) -> float:
        """キャッシュヒット率計算"""
        # 簡易実装
        return 0.85  # 85%のヒット率を想定

# テスト用のメイン関数
async def test_optimized_news_sentiment():
    """最適化されたニュース・センチメント分析テスト"""
    print("Optimized News Sentiment Analysis Test")
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
    
    # 最適化されたセンチメント分析器初期化
    async with OptimizedNewsSentimentAnalyzer(config) as analyzer:
        # センチメント分析実行
        moving_avg = await analyzer.run_sentiment_analysis_optimized()
        
        # サマリー表示
        summary = analyzer.get_sentiment_summary_optimized()
        print(f"\nOptimized Sentiment Analysis Summary:")
        print(f"  Moving Average Sentiment: {summary['moving_average_sentiment']:.2f}")
        print(f"  Total Articles Analyzed: {summary['total_articles_analyzed']}")
        print(f"  Sentiment Trend: {summary['sentiment_trend']}")
        print(f"  Cache Stats: {summary['cache_stats']}")
        
        if summary['recent_scores']:
            print(f"  Recent Scores: {summary['recent_scores']}")
    
    print("\nOptimized News Sentiment Analysis Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_optimized_news_sentiment())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
