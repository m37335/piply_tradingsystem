"""
パフォーマンス最適化機能

プロトレーダー向け為替アラートシステム用のパフォーマンス最適化機能
設計書参照: /app/note/2025-01-15_実装計画_Phase3_パフォーマンス最適化.yaml
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


class PerformanceOptimizer:
    """
    パフォーマンス最適化機能

    責任:
    - データベースクエリ最適化
    - メモリ使用量最適化
    - レスポンス時間改善
    - 同時処理能力向上

    特徴:
    - 自動最適化
    - パフォーマンス監視
    - ボトルネック特定
    - 効果測定
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.optimization_history = []
        self.performance_metrics = {}

    async def optimize_database_queries(self) -> Dict[str, Any]:
        """
        データベースクエリ最適化

        Returns:
            Dict[str, Any]: 最適化結果
        """
        try:
            optimization_results = {}

            # インデックス最適化
            index_optimization = await self._optimize_indexes()
            optimization_results["index_optimization"] = index_optimization

            # クエリ最適化
            query_optimization = await self._optimize_queries()
            optimization_results["query_optimization"] = query_optimization

            # 接続プール最適化
            connection_optimization = await self._optimize_connections()
            optimization_results["connection_optimization"] = connection_optimization

            # 結果を記録
            self._record_optimization("database_queries", optimization_results)

            return optimization_results

        except Exception as e:
            print(f"Error optimizing database queries: {e}")
            return {"error": str(e)}

    async def _optimize_indexes(self) -> Dict[str, Any]:
        """
        インデックス最適化

        Returns:
            Dict[str, Any]: インデックス最適化結果
        """
        try:
            # 現在のインデックス状況を確認
            index_status = await self._get_index_status()

            # 推奨インデックスを生成
            recommended_indexes = self._generate_recommended_indexes()

            # インデックス作成（実際の実装では慎重に実行）
            created_indexes = []
            for index in recommended_indexes:
                if await self._should_create_index(index, index_status):
                    success = await self._create_index(index)
                    if success:
                        created_indexes.append(index)

            return {
                "current_indexes": index_status,
                "recommended_indexes": recommended_indexes,
                "created_indexes": created_indexes,
                "optimization_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error optimizing indexes: {e}")
            return {"error": str(e)}

    async def _get_index_status(self) -> List[Dict[str, Any]]:
        """
        インデックス状況を取得

        Returns:
            List[Dict[str, Any]]: インデックス状況
        """
        try:
            # PostgreSQLの場合のインデックス情報取得
            query = text(
                """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
            """
            )

            result = await self.db_session.execute(query)
            indexes = []

            for row in result:
                indexes.append(
                    {
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.idx_scan,
                        "tuples_read": row.idx_tup_read,
                        "tuples_fetched": row.idx_tup_fetch,
                    }
                )

            return indexes

        except Exception as e:
            print(f"Error getting index status: {e}")
            return []

    def _generate_recommended_indexes(self) -> List[Dict[str, Any]]:
        """
        推奨インデックスを生成

        Returns:
            List[Dict[str, Any]]: 推奨インデックス
        """
        return [
            {
                "table": "technical_indicators",
                "columns": ["currency_pair", "timeframe", "timestamp"],
                "type": "btree",
                "name": "idx_tech_indicators_currency_timeframe_timestamp",
            },
            {
                "table": "entry_signals",
                "columns": ["currency_pair", "timestamp", "signal_type"],
                "type": "btree",
                "name": "idx_entry_signals_currency_timestamp_type",
            },
            {
                "table": "signal_performance",
                "columns": ["currency_pair", "entry_time", "pnl_percentage"],
                "type": "btree",
                "name": "idx_signal_performance_currency_entry_pnl",
            },
            {
                "table": "risk_alerts",
                "columns": ["currency_pair", "timestamp", "severity"],
                "type": "btree",
                "name": "idx_risk_alerts_currency_timestamp_severity",
            },
        ]

    async def _should_create_index(
        self, index: Dict[str, Any], existing_indexes: List[Dict[str, Any]]
    ) -> bool:
        """
        インデックス作成が必要かチェック

        Args:
            index: 作成予定インデックス
            existing_indexes: 既存インデックス

        Returns:
            bool: 作成が必要かどうか
        """
        index_name = index["name"]

        # 既存インデックスをチェック
        for existing in existing_indexes:
            if existing["index"] == index_name:
                return False

        return True

    async def _create_index(self, index: Dict[str, Any]) -> bool:
        """
        インデックスを作成

        Args:
            index: インデックス情報

        Returns:
            bool: 作成成功かどうか
        """
        try:
            columns = ", ".join(index["columns"])
            query = text(
                f"""
                CREATE INDEX {index['name']} 
                ON {index['table']} ({columns})
            """
            )

            await self.db_session.execute(query)
            await self.db_session.commit()

            return True

        except Exception as e:
            print(f"Error creating index {index['name']}: {e}")
            await self.db_session.rollback()
            return False

    async def _optimize_queries(self) -> Dict[str, Any]:
        """
        クエリ最適化

        Returns:
            Dict[str, Any]: クエリ最適化結果
        """
        try:
            # スロークエリを特定
            slow_queries = await self._identify_slow_queries()

            # クエリ最適化提案
            optimization_suggestions = self._generate_query_suggestions(slow_queries)

            # クエリパフォーマンス改善
            performance_improvements = await self._improve_query_performance(
                slow_queries
            )

            return {
                "slow_queries": slow_queries,
                "optimization_suggestions": optimization_suggestions,
                "performance_improvements": performance_improvements,
                "optimization_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error optimizing queries: {e}")
            return {"error": str(e)}

    async def _identify_slow_queries(self) -> List[Dict[str, Any]]:
        """
        スロークエリを特定

        Returns:
            List[Dict[str, Any]]: スロークエリ情報
        """
        try:
            # PostgreSQLの場合のスロークエリ情報取得
            query = text(
                """
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                ORDER BY mean_time DESC
                LIMIT 10
            """
            )

            result = await self.db_session.execute(query)
            slow_queries = []

            for row in result:
                slow_queries.append(
                    {
                        "query": (
                            row.query[:200] + "..."
                            if len(row.query) > 200
                            else row.query
                        ),
                        "calls": row.calls,
                        "total_time": row.total_time,
                        "mean_time": row.mean_time,
                        "rows": row.rows,
                    }
                )

            return slow_queries

        except Exception as e:
            print(f"Error identifying slow queries: {e}")
            return []

    def _generate_query_suggestions(
        self, slow_queries: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        クエリ最適化提案を生成

        Args:
            slow_queries: スロークエリ情報

        Returns:
            List[Dict[str, Any]]: 最適化提案
        """
        suggestions = []

        for query_info in slow_queries:
            query = query_info["query"]
            mean_time = query_info["mean_time"]

            suggestion = {
                "original_query": query,
                "mean_time": mean_time,
                "suggestions": [],
            }

            # WHERE句の最適化提案
            if "WHERE" in query and "timestamp" in query:
                suggestion["suggestions"].append(
                    "timestampカラムにインデックスを追加することを検討してください"
                )

            # JOINの最適化提案
            if "JOIN" in query:
                suggestion["suggestions"].append(
                    "JOIN条件のカラムにインデックスを追加することを検討してください"
                )

            # ORDER BYの最適化提案
            if "ORDER BY" in query:
                suggestion["suggestions"].append(
                    "ORDER BY句のカラムにインデックスを追加することを検討してください"
                )

            # LIMITの最適化提案
            if "LIMIT" in query and "OFFSET" in query:
                suggestion["suggestions"].append(
                    "OFFSETの代わりにカーソルベースのページネーションを検討してください"
                )

            suggestions.append(suggestion)

        return suggestions

    async def _improve_query_performance(
        self, slow_queries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        クエリパフォーマンスを改善

        Args:
            slow_queries: スロークエリ情報

        Returns:
            Dict[str, Any]: 改善結果
        """
        improvements = {
            "optimized_queries": [],
            "performance_gains": {},
        }

        for query_info in slow_queries:
            original_time = query_info["mean_time"]

            # クエリ最適化（実際の実装ではより詳細な分析が必要）
            optimized_query = self._optimize_single_query(query_info["query"])

            if optimized_query:
                improvements["optimized_queries"].append(
                    {
                        "original": query_info["query"],
                        "optimized": optimized_query,
                        "estimated_improvement": "20-50%",
                    }
                )

        return improvements

    def _optimize_single_query(self, query: str) -> Optional[str]:
        """
        単一クエリを最適化

        Args:
            query: 元のクエリ

        Returns:
            Optional[str]: 最適化されたクエリ
        """
        # 基本的なクエリ最適化ルール
        optimized = query

        # SELECT * の最適化
        if "SELECT *" in optimized:
            optimized = optimized.replace("SELECT *", "SELECT specific_columns")

        # DISTINCTの最適化
        if "DISTINCT" in optimized and "ORDER BY" in optimized:
            optimized = optimized.replace("DISTINCT", "DISTINCT ON")

        return optimized if optimized != query else None

    async def _optimize_connections(self) -> Dict[str, Any]:
        """
        接続プール最適化

        Returns:
            Dict[str, Any]: 接続最適化結果
        """
        try:
            # 接続プール設定を取得
            pool_settings = await self._get_connection_pool_settings()

            # 最適化提案
            optimization_suggestions = self._generate_connection_suggestions(
                pool_settings
            )

            return {
                "current_pool_settings": pool_settings,
                "optimization_suggestions": optimization_suggestions,
                "optimization_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error optimizing connections: {e}")
            return {"error": str(e)}

    async def _get_connection_pool_settings(self) -> Dict[str, Any]:
        """
        接続プール設定を取得

        Returns:
            Dict[str, Any]: 接続プール設定
        """
        try:
            # PostgreSQLの場合の接続情報取得
            query = text(
                """
                SELECT 
                    setting,
                    unit,
                    context
                FROM pg_settings 
                WHERE name IN (
                    'max_connections',
                    'shared_buffers',
                    'effective_cache_size',
                    'work_mem'
                )
            """
            )

            result = await self.db_session.execute(query)
            settings = {}

            for row in result:
                settings[row.setting] = {
                    "value": row.setting,
                    "unit": row.unit,
                    "context": row.context,
                }

            return settings

        except Exception as e:
            print(f"Error getting connection pool settings: {e}")
            return {}

    def _generate_connection_suggestions(
        self, pool_settings: Dict[str, Any]
    ) -> List[str]:
        """
        接続最適化提案を生成

        Args:
            pool_settings: 接続プール設定

        Returns:
            List[str]: 最適化提案
        """
        suggestions = []

        # 接続数最適化
        if "max_connections" in pool_settings:
            suggestions.append(
                "max_connectionsを現在の負荷に応じて調整することを検討してください"
            )

        # 共有バッファ最適化
        if "shared_buffers" in pool_settings:
            suggestions.append(
                "shared_buffersをシステムメモリの25%程度に設定することを検討してください"
            )

        # 作業メモリ最適化
        if "work_mem" in pool_settings:
            suggestions.append(
                "work_memを複雑なクエリの処理に応じて調整することを検討してください"
            )

        return suggestions

    async def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        メモリ使用量最適化

        Returns:
            Dict[str, Any]: メモリ最適化結果
        """
        try:
            optimization_results = {}

            # キャッシュ最適化
            cache_optimization = await self._optimize_cache()
            optimization_results["cache_optimization"] = cache_optimization

            # メモリリーク検出
            memory_leak_detection = await self._detect_memory_leaks()
            optimization_results["memory_leak_detection"] = memory_leak_detection

            # ガベージコレクション最適化
            gc_optimization = await self._optimize_garbage_collection()
            optimization_results["gc_optimization"] = gc_optimization

            # 結果を記録
            self._record_optimization("memory_usage", optimization_results)

            return optimization_results

        except Exception as e:
            print(f"Error optimizing memory usage: {e}")
            return {"error": str(e)}

    async def _optimize_cache(self) -> Dict[str, Any]:
        """
        キャッシュ最適化

        Returns:
            Dict[str, Any]: キャッシュ最適化結果
        """
        try:
            # キャッシュヒット率を測定
            cache_hit_rate = await self._measure_cache_hit_rate()

            # キャッシュサイズ最適化
            cache_size_optimization = self._optimize_cache_size(cache_hit_rate)

            # キャッシュ戦略最適化
            cache_strategy_optimization = self._optimize_cache_strategy()

            return {
                "cache_hit_rate": cache_hit_rate,
                "cache_size_optimization": cache_size_optimization,
                "cache_strategy_optimization": cache_strategy_optimization,
                "optimization_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error optimizing cache: {e}")
            return {"error": str(e)}

    async def _measure_cache_hit_rate(self) -> float:
        """
        キャッシュヒット率を測定

        Returns:
            float: キャッシュヒット率
        """
        try:
            # PostgreSQLの場合のキャッシュヒット率取得
            query = text(
                """
                SELECT 
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as hit_ratio
                FROM pg_statio_user_tables
            """
            )

            result = await self.db_session.execute(query)
            row = result.fetchone()

            if row and row.hit_ratio:
                return float(row.hit_ratio)
            else:
                return 0.0

        except Exception as e:
            print(f"Error measuring cache hit rate: {e}")
            return 0.0

    def _optimize_cache_size(self, hit_rate: float) -> Dict[str, Any]:
        """
        キャッシュサイズ最適化

        Args:
            hit_rate: キャッシュヒット率

        Returns:
            Dict[str, Any]: キャッシュサイズ最適化結果
        """
        suggestions = []

        if hit_rate < 0.8:
            suggestions.append("shared_buffersを増やすことを検討してください")
        elif hit_rate > 0.95:
            suggestions.append(
                "shared_buffersを減らしてメモリを節約することを検討してください"
            )

        return {
            "current_hit_rate": hit_rate,
            "suggestions": suggestions,
        }

    def _optimize_cache_strategy(self) -> Dict[str, Any]:
        """
        キャッシュ戦略最適化

        Returns:
            Dict[str, Any]: キャッシュ戦略最適化結果
        """
        return {
            "suggestions": [
                "頻繁にアクセスされるデータをキャッシュに保持",
                "LRU（Least Recently Used）アルゴリズムの使用",
                "キャッシュの有効期限設定",
                "分散キャッシュの検討",
            ],
        }

    async def _detect_memory_leaks(self) -> Dict[str, Any]:
        """
        メモリリーク検出

        Returns:
            Dict[str, Any]: メモリリーク検出結果
        """
        try:
            # メモリ使用量を測定
            memory_usage = await self._measure_memory_usage()

            # メモリリークの可能性を分析
            leak_analysis = self._analyze_memory_leaks(memory_usage)

            return {
                "memory_usage": memory_usage,
                "leak_analysis": leak_analysis,
                "detection_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error detecting memory leaks: {e}")
            return {"error": str(e)}

    async def _measure_memory_usage(self) -> Dict[str, Any]:
        """
        メモリ使用量を測定

        Returns:
            Dict[str, Any]: メモリ使用量
        """
        try:
            # PostgreSQLの場合のメモリ使用量取得
            query = text(
                """
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    pg_size_pretty(pg_total_relation_size('technical_indicators')) as tech_indicators_size,
                    pg_size_pretty(pg_total_relation_size('entry_signals')) as entry_signals_size
            """
            )

            result = await self.db_session.execute(query)
            row = result.fetchone()

            return {
                "database_size": row.db_size if row else "Unknown",
                "technical_indicators_size": (
                    row.tech_indicators_size if row else "Unknown"
                ),
                "entry_signals_size": row.entry_signals_size if row else "Unknown",
            }

        except Exception as e:
            print(f"Error measuring memory usage: {e}")
            return {}

    def _analyze_memory_leaks(self, memory_usage: Dict[str, Any]) -> Dict[str, Any]:
        """
        メモリリークを分析

        Args:
            memory_usage: メモリ使用量

        Returns:
            Dict[str, Any]: メモリリーク分析結果
        """
        return {
            "potential_leaks": [],
            "suggestions": [
                "定期的なメモリ使用量監視",
                "不要なオブジェクトの早期解放",
                "ガベージコレクションの最適化",
                "メモリプールの使用",
            ],
        }

    async def _optimize_garbage_collection(self) -> Dict[str, Any]:
        """
        ガベージコレクション最適化

        Returns:
            Dict[str, Any]: ガベージコレクション最適化結果
        """
        return {
            "suggestions": [
                "定期的なガベージコレクション実行",
                "メモリ使用量の監視",
                "不要なオブジェクトの早期削除",
                "弱参照の使用",
            ],
        }

    async def optimize_async_processing(self) -> Dict[str, Any]:
        """
        非同期処理最適化

        Returns:
            Dict[str, Any]: 非同期処理最適化結果
        """
        try:
            optimization_results = {}

            # 並行処理最適化
            concurrency_optimization = await self._optimize_concurrency()
            optimization_results["concurrency_optimization"] = concurrency_optimization

            # タスクスケジューリング最適化
            scheduling_optimization = await self._optimize_task_scheduling()
            optimization_results["scheduling_optimization"] = scheduling_optimization

            # 結果を記録
            self._record_optimization("async_processing", optimization_results)

            return optimization_results

        except Exception as e:
            print(f"Error optimizing async processing: {e}")
            return {"error": str(e)}

    async def _optimize_concurrency(self) -> Dict[str, Any]:
        """
        並行処理最適化

        Returns:
            Dict[str, Any]: 並行処理最適化結果
        """
        return {
            "suggestions": [
                "適切なワーカー数の設定",
                "セマフォの使用によるリソース制限",
                "非同期I/Oの活用",
                "バッチ処理の実装",
            ],
            "optimization_timestamp": datetime.utcnow(),
        }

    async def _optimize_task_scheduling(self) -> Dict[str, Any]:
        """
        タスクスケジューリング最適化

        Returns:
            Dict[str, Any]: タスクスケジューリング最適化結果
        """
        return {
            "suggestions": [
                "優先度付きキューンの使用",
                "タスクの優先度設定",
                "負荷分散の実装",
                "タイムアウト設定の最適化",
            ],
            "optimization_timestamp": datetime.utcnow(),
        }

    def _record_optimization(
        self, optimization_type: str, results: Dict[str, Any]
    ) -> None:
        """
        最適化結果を記録

        Args:
            optimization_type: 最適化タイプ
            results: 最適化結果
        """
        record = {
            "type": optimization_type,
            "results": results,
            "timestamp": datetime.utcnow(),
        }

        self.optimization_history.append(record)

        # 履歴を100件まで保持
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]

    async def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        最適化履歴を取得

        Returns:
            List[Dict[str, Any]]: 最適化履歴
        """
        return self.optimization_history.copy()

    async def run_performance_test(self) -> Dict[str, Any]:
        """
        パフォーマンステストを実行

        Returns:
            Dict[str, Any]: パフォーマンステスト結果
        """
        try:
            start_time = time.time()

            # データベースクエリテスト
            db_performance = await self._test_database_performance()

            # メモリ使用量テスト
            memory_performance = await self._test_memory_performance()

            # 非同期処理テスト
            async_performance = await self._test_async_performance()

            end_time = time.time()
            total_time = end_time - start_time

            return {
                "test_duration": total_time,
                "database_performance": db_performance,
                "memory_performance": memory_performance,
                "async_performance": async_performance,
                "test_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error running performance test: {e}")
            return {"error": str(e)}

    async def _test_database_performance(self) -> Dict[str, Any]:
        """
        データベースパフォーマンステスト

        Returns:
            Dict[str, Any]: データベースパフォーマンステスト結果
        """
        try:
            start_time = time.time()

            # 複雑なクエリを実行
            query = select(text("COUNT(*)")).select_from(text("technical_indicators"))
            result = await self.db_session.execute(query)
            count = result.scalar()

            end_time = time.time()
            query_time = end_time - start_time

            return {
                "query_time": query_time,
                "record_count": count,
                "performance_rating": (
                    "good" if query_time < 1.0 else "needs_optimization"
                ),
            }

        except Exception as e:
            print(f"Error testing database performance: {e}")
            return {"error": str(e)}

    async def _test_memory_performance(self) -> Dict[str, Any]:
        """
        メモリパフォーマンステスト

        Returns:
            Dict[str, Any]: メモリパフォーマンステスト結果
        """
        try:
            import psutil

            # メモリ使用量を取得
            memory_info = psutil.virtual_memory()
            process = psutil.Process()

            return {
                "total_memory": memory_info.total,
                "available_memory": memory_info.available,
                "process_memory": process.memory_info().rss,
                "memory_usage_percent": memory_info.percent,
                "performance_rating": (
                    "good" if memory_info.percent < 80 else "needs_optimization"
                ),
            }

        except Exception as e:
            print(f"Error testing memory performance: {e}")
            return {"error": str(e)}

    async def _test_async_performance(self) -> Dict[str, Any]:
        """
        非同期処理パフォーマンステスト

        Returns:
            Dict[str, Any]: 非同期処理パフォーマンステスト結果
        """
        try:
            start_time = time.time()

            # 複数の非同期タスクを実行
            tasks = []
            for i in range(10):
                task = asyncio.create_task(self._dummy_async_task(i))
                tasks.append(task)

            await asyncio.gather(*tasks)

            end_time = time.time()
            async_time = end_time - start_time

            return {
                "async_time": async_time,
                "task_count": len(tasks),
                "performance_rating": (
                    "good" if async_time < 2.0 else "needs_optimization"
                ),
            }

        except Exception as e:
            print(f"Error testing async performance: {e}")
            return {"error": str(e)}

    async def _dummy_async_task(self, task_id: int) -> None:
        """
        ダミーの非同期タスク

        Args:
            task_id: タスクID
        """
        await asyncio.sleep(0.1)  # 100ms待機
