"""
最適化されたデータベース接続管理
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import asyncpg
import aiosqlite
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ConnectionStats:
    """接続統計"""
    total_connections: int
    active_connections: int
    idle_connections: int
    connection_pool_size: int
    avg_response_time: float
    total_queries: int
    failed_queries: int

class OptimizedDatabaseManager:
    """最適化されたデータベース管理クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_type = config.get('db_type', 'sqlite')
        self.db_url = config.get('db_url', 'sqlite+aiosqlite:///trading_bot.db')
        
        # 接続プール設定
        self.pool_size = config.get('pool_size', 10)
        self.max_overflow = config.get('max_overflow', 20)
        self.pool_timeout = config.get('pool_timeout', 30)
        self.pool_recycle = config.get('pool_recycle', 3600)
        
        # エンジンとセッションファクトリー
        self.engine = None
        self.session_factory = None
        
        # 統計情報
        self.stats = ConnectionStats(
            total_connections=0,
            active_connections=0,
            idle_connections=0,
            connection_pool_size=self.pool_size,
            avg_response_time=0.0,
            total_queries=0,
            failed_queries=0
        )
        
        # レスポンス時間追跡
        self.response_times: List[float] = []
        self.max_response_times = 100  # 最新100件のみ保持
    
    async def initialize(self):
        """データベース初期化"""
        try:
            # エンジン作成（接続プール設定付き）
            self.engine = create_async_engine(
                self.db_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=True,  # 接続の健全性チェック
                echo=False  # 本番ではFalse
            )
            
            # セッションファクトリー作成
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 接続テスト
            await self._test_connection()
            
            logger.info(f"Database initialized successfully: {self.db_type}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _test_connection(self):
        """接続テスト"""
        async with self.get_session() as session:
            await session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
    
    @asynccontextmanager
    async def get_session(self):
        """最適化されたセッション取得"""
        session = None
        start_time = time.time()
        
        try:
            session = self.session_factory()
            self.stats.active_connections += 1
            
            yield session
            
            # 成功時の統計更新
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            self.stats.total_queries += 1
            
        except Exception as e:
            # 失敗時の統計更新
            self.stats.failed_queries += 1
            logger.error(f"Database session error: {e}")
            raise
            
        finally:
            if session:
                await session.close()
                self.stats.active_connections -= 1
    
    def _update_response_time(self, response_time: float):
        """レスポンス時間更新"""
        self.response_times.append(response_time)
        
        # 最大件数を超えた場合は古いものを削除
        if len(self.response_times) > self.max_response_times:
            self.response_times = self.response_times[-self.max_response_times:]
        
        # 平均レスポンス時間更新
        self.stats.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    async def execute_query_optimized(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """最適化されたクエリ実行"""
        async with self.get_session() as session:
            try:
                result = await session.execute(text(query), params or {})
                
                # 結果を辞書形式で返す
                if result.returns_rows:
                    columns = result.keys()
                    rows = result.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return []
                    
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise
    
    async def execute_batch_queries(self, queries: List[tuple]) -> List[List[Dict[str, Any]]]:
        """バッチクエリ実行"""
        results = []
        
        async with self.get_session() as session:
            try:
                for query, params in queries:
                    result = await session.execute(text(query), params or {})
                    
                    if result.returns_rows:
                        columns = result.keys()
                        rows = result.fetchall()
                        results.append([dict(zip(columns, row)) for row in rows])
                    else:
                        results.append([])
                        
            except Exception as e:
                logger.error(f"Batch query execution failed: {e}")
                raise
        
        return results
    
    async def get_connection_stats(self) -> ConnectionStats:
        """接続統計取得"""
        # プール統計を取得
        pool = self.engine.pool
        self.stats.total_connections = pool.size()
        self.stats.idle_connections = pool.checkedin()
        
        return self.stats
    
    async def optimize_queries(self):
        """クエリ最適化"""
        try:
            # SQLiteの場合の最適化
            if self.db_type == 'sqlite':
                async with self.get_session() as session:
                    await session.execute(text("PRAGMA journal_mode=WAL"))
                    await session.execute(text("PRAGMA synchronous=NORMAL"))
                    await session.execute(text("PRAGMA cache_size=10000"))
                    await session.execute(text("PRAGMA temp_store=MEMORY"))
                    await session.commit()
                    
            # PostgreSQLの場合の最適化
            elif self.db_type == 'postgresql':
                async with self.get_session() as session:
                    await session.execute(text("SET random_page_cost = 1.1"))
                    await session.execute(text("SET effective_cache_size = '1GB'"))
                    await session.commit()
                    
            logger.info("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
    
    async def cleanup_old_data(self, table_name: str, retention_days: int = 30):
        """古いデータのクリーンアップ"""
        try:
            async with self.get_session() as session:
                query = f"""
                DELETE FROM {table_name} 
                WHERE timestamp < datetime('now', '-{retention_days} days')
                """
                await session.execute(text(query))
                await session.commit()
                
                logger.info(f"Cleaned up old data from {table_name}")
                
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクス取得"""
        stats = await self.get_connection_stats()
        
        return {
            'connection_stats': {
                'total_connections': stats.total_connections,
                'active_connections': stats.active_connections,
                'idle_connections': stats.idle_connections,
                'pool_size': stats.connection_pool_size
            },
            'query_stats': {
                'total_queries': stats.total_queries,
                'failed_queries': stats.failed_queries,
                'success_rate': (stats.total_queries - stats.failed_queries) / max(stats.total_queries, 1),
                'avg_response_time': stats.avg_response_time
            },
            'performance_metrics': {
                'recent_response_times': self.response_times[-10:],  # 最新10件
                'max_response_time': max(self.response_times) if self.response_times else 0,
                'min_response_time': min(self.response_times) if self.response_times else 0
            }
        }
    
    async def close(self):
        """データベース接続終了"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# テスト用のメイン関数
async def test_optimized_database():
    """最適化されたデータベーステスト"""
    print("Optimized Database Test")
    print("=" * 50)
    
    # 設定
    config = {
        'db_type': 'sqlite',
        'db_url': 'sqlite+aiosqlite:///test_optimized.db',
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 3600
    }
    
    # データベース管理クラス初期化
    db_manager = OptimizedDatabaseManager(config)
    
    try:
        # 初期化
        await db_manager.initialize()
        
        # 最適化実行
        await db_manager.optimize_queries()
        
        # テストクエリ実行
        test_queries = [
            ("SELECT 1 as test_value", {}),
            ("SELECT datetime('now') as current_time", {}),
            ("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'", {})
        ]
        
        results = await db_manager.execute_batch_queries(test_queries)
        
        print(f"\nTest Query Results:")
        for i, result in enumerate(results):
            print(f"  Query {i+1}: {result}")
        
        # パフォーマンスメトリクス取得
        metrics = await db_manager.get_performance_metrics()
        print(f"\nPerformance Metrics:")
        print(f"  Connection Stats: {metrics['connection_stats']}")
        print(f"  Query Stats: {metrics['query_stats']}")
        print(f"  Performance: {metrics['performance_metrics']}")
        
    finally:
        await db_manager.close()
    
    print("\nOptimized Database Test Completed!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        asyncio.run(test_optimized_database())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
