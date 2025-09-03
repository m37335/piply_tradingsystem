#!/usr/bin/env python3
"""
データベース最適化システム
"""

import asyncio
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.infrastructure.monitoring.log_manager import LogManager
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


@dataclass
class DatabaseMetrics:
    """データベースメトリクス"""

    timestamp: str
    table_sizes: Dict[str, int]
    index_sizes: Dict[str, int]
    query_performance: Dict[str, float]
    connection_count: int
    active_queries: int
    slow_queries: int
    cache_hit_ratio: float
    fragmentation_ratio: float


@dataclass
class OptimizationResult:
    """最適化結果"""

    operation: str
    table_name: str
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    improvement: float
    duration: float
    timestamp: str


class DatabaseOptimizer:
    """
    データベース最適化システム
    """

    def __init__(self, config_manager: SystemConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.optimization_history: List[OptimizationResult] = []
        self.optimization_thresholds = self._load_optimization_thresholds()
        self.optimization_active = False

    def _load_optimization_thresholds(self) -> Dict[str, float]:
        """最適化閾値を読み込み"""
        return {
            "table_size_threshold": self.config_manager.get(
                "performance.table_size_threshold", 1000000
            ),
            "fragmentation_threshold": self.config_manager.get(
                "performance.fragmentation_threshold", 30.0
            ),
            "cache_hit_threshold": self.config_manager.get(
                "performance.cache_hit_threshold", 80.0
            ),
            "slow_query_threshold": self.config_manager.get(
                "performance.slow_query_threshold", 5.0
            ),
        }

    async def analyze_database_performance(
        self, session: AsyncSession
    ) -> DatabaseMetrics:
        """データベースパフォーマンスを分析"""
        try:
            # テーブルサイズを取得
            table_sizes = await self._get_table_sizes(session)

            # インデックスサイズを取得
            index_sizes = await self._get_index_sizes(session)

            # クエリパフォーマンスを取得
            query_performance = await self._get_query_performance(session)

            # 接続数を取得
            connection_count = await self._get_connection_count(session)

            # アクティブクエリ数を取得
            active_queries = await self._get_active_queries(session)

            # スロークエリ数を取得
            slow_queries = await self._get_slow_queries(session)

            # キャッシュヒット率を取得
            cache_hit_ratio = await self._get_cache_hit_ratio(session)

            # フラグメンテーション率を取得
            fragmentation_ratio = await self._get_fragmentation_ratio(session)

            metrics = DatabaseMetrics(
                timestamp=datetime.now().isoformat(),
                table_sizes=table_sizes,
                index_sizes=index_sizes,
                query_performance=query_performance,
                connection_count=connection_count,
                active_queries=active_queries,
                slow_queries=slow_queries,
                cache_hit_ratio=cache_hit_ratio,
                fragmentation_ratio=fragmentation_ratio,
            )

            return metrics

        except Exception as e:
            logger.error(f"データベースパフォーマンス分析中にエラー: {e}")
            return DatabaseMetrics(
                timestamp=datetime.now().isoformat(),
                table_sizes={},
                index_sizes={},
                query_performance={},
                connection_count=0,
                active_queries=0,
                slow_queries=0,
                cache_hit_ratio=0.0,
                fragmentation_ratio=0.0,
            )

    async def _get_table_sizes(self, session: AsyncSession) -> Dict[str, int]:
        """テーブルサイズを取得"""
        try:
            # SQLiteの場合
            result = await session.execute(
                text(
                    """
                SELECT name, sql FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """
                )
            )
            tables = result.fetchall()

            table_sizes = {}
            for table_name, _ in tables:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                )
                count = result.scalar()
                table_sizes[table_name] = count or 0

            return table_sizes

        except Exception as e:
            logger.error(f"テーブルサイズ取得中にエラー: {e}")
            return {}

    async def _get_index_sizes(self, session: AsyncSession) -> Dict[str, int]:
        """インデックスサイズを取得"""
        try:
            # SQLiteの場合
            result = await session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """
                )
            )
            indexes = result.fetchall()

            index_sizes = {}
            for (index_name,) in indexes:
                # インデックスのサイズを推定
                index_sizes[index_name] = 1000  # 推定値

            return index_sizes

        except Exception as e:
            logger.error(f"インデックスサイズ取得中にエラー: {e}")
            return {}

    async def _get_query_performance(self, session: AsyncSession) -> Dict[str, float]:
        """クエリパフォーマンスを取得"""
        try:
            # 実際の実装では、クエリログから統計を取得
            # 現在は推定値を使用
            return {
                "data_fetch": 0.5,
                "pattern_detection": 1.2,
                "indicator_calculation": 0.8,
            }

        except Exception as e:
            logger.error(f"クエリパフォーマンス取得中にエラー: {e}")
            return {}

    async def _get_connection_count(self, session: AsyncSession) -> int:
        """接続数を取得"""
        try:
            # 実際の実装では、接続プールから取得
            return 1  # 現在のセッション数

        except Exception as e:
            logger.error(f"接続数取得中にエラー: {e}")
            return 0

    async def _get_active_queries(self, session: AsyncSession) -> int:
        """アクティブクエリ数を取得"""
        try:
            # 実際の実装では、アクティブクエリを監視
            return 0

        except Exception as e:
            logger.error(f"アクティブクエリ数取得中にエラー: {e}")
            return 0

    async def _get_slow_queries(self, session: AsyncSession) -> int:
        """スロークエリ数を取得"""
        try:
            # 実際の実装では、スロークエリログから取得
            return 0

        except Exception as e:
            logger.error(f"スロークエリ数取得中にエラー: {e}")
            return 0

    async def _get_cache_hit_ratio(self, session: AsyncSession) -> float:
        """キャッシュヒット率を取得"""
        try:
            # 実際の実装では、キャッシュ統計から取得
            return 85.0  # 推定値

        except Exception as e:
            logger.error(f"キャッシュヒット率取得中にエラー: {e}")
            return 0.0

    async def _get_fragmentation_ratio(self, session: AsyncSession) -> float:
        """フラグメンテーション率を取得"""
        try:
            # 実際の実装では、テーブル統計から取得
            return 15.0  # 推定値

        except Exception as e:
            logger.error(f"フラグメンテーション率取得中にエラー: {e}")
            return 0.0

    async def optimize_database(
        self, session: AsyncSession
    ) -> List[OptimizationResult]:
        """データベースを最適化"""
        try:
            logger.info("データベース最適化を開始")

            # 最適化前のメトリクスを取得
            before_metrics = await self.analyze_database_performance(session)

            optimization_results = []

            # インデックス最適化
            index_result = await self._optimize_indexes(session, before_metrics)
            if index_result:
                optimization_results.append(index_result)

            # テーブル最適化
            table_result = await self._optimize_tables(session, before_metrics)
            if table_result:
                optimization_results.append(table_result)

            # クエリ最適化
            query_result = await self._optimize_queries(session, before_metrics)
            if query_result:
                optimization_results.append(query_result)

            # 最適化後のメトリクスを取得
            after_metrics = await self.analyze_database_performance(session)

            # 最適化結果を記録
            for result in optimization_results:
                self.optimization_history.append(result)

            # 最適化レポートをDiscordに送信
            await self._send_optimization_report_to_discord(
                before_metrics, after_metrics, optimization_results
            )

            logger.info(f"データベース最適化完了: {len(optimization_results)}件の最適化を実行")
            return optimization_results

        except Exception as e:
            logger.error(f"データベース最適化中にエラー: {e}")
            return []

    async def _optimize_indexes(
        self, session: AsyncSession, metrics: DatabaseMetrics
    ) -> Optional[OptimizationResult]:
        """インデックスを最適化"""
        try:
            start_time = time.time()

            # 最適化が必要なインデックスを特定
            optimization_needed = []

            for table_name, size in metrics.table_sizes.items():
                if size > self.optimization_thresholds["table_size_threshold"]:
                    # 大きなテーブルにはインデックスが必要
                    optimization_needed.append(table_name)

            if not optimization_needed:
                return None

            # インデックスを作成
            for table_name in optimization_needed:
                # 既存のインデックスをチェック
                result = await session.execute(
                    text(
                        f"""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND tbl_name='{table_name}'
                """
                    )
                )
                existing_indexes = [row[0] for row in result.fetchall()]

                # 必要なインデックスを作成
                if f"idx_{table_name}_timestamp" not in existing_indexes:
                    await session.execute(
                        text(
                            f"""
                        CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp
                        ON {table_name} (timestamp)
                    """
                        )
                    )

                if f"idx_{table_name}_created_at" not in existing_indexes:
                    await session.execute(
                        text(
                            f"""
                        CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at
                        ON {table_name} (created_at)
                    """
                        )
                    )

            await session.commit()

            duration = time.time() - start_time

            # 最適化後のメトリクスを取得
            after_metrics = await self.analyze_database_performance(session)

            # 改善度を計算
            improvement = self._calculate_improvement(
                metrics.query_performance, after_metrics.query_performance
            )

            return OptimizationResult(
                operation="index_optimization",
                table_name="all_tables",
                before_metrics=asdict(metrics),
                after_metrics=asdict(after_metrics),
                improvement=improvement,
                duration=duration,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            logger.error(f"インデックス最適化中にエラー: {e}")
            return None

    async def _optimize_tables(
        self, session: AsyncSession, metrics: DatabaseMetrics
    ) -> Optional[OptimizationResult]:
        """テーブルを最適化"""
        try:
            start_time = time.time()

            # フラグメンテーションが高いテーブルを最適化
            if (
                metrics.fragmentation_ratio
                > self.optimization_thresholds["fragmentation_threshold"]
            ):
                # VACUUMを実行（SQLiteの場合）
                await session.execute(text("VACUUM"))
                await session.commit()

                duration = time.time() - start_time

                # 最適化後のメトリクスを取得
                after_metrics = await self.analyze_database_performance(session)

                # 改善度を計算
                improvement = (
                    metrics.fragmentation_ratio - after_metrics.fragmentation_ratio
                )

                return OptimizationResult(
                    operation="table_optimization",
                    table_name="all_tables",
                    before_metrics=asdict(metrics),
                    after_metrics=asdict(after_metrics),
                    improvement=improvement,
                    duration=duration,
                    timestamp=datetime.now().isoformat(),
                )

            return None

        except Exception as e:
            logger.error(f"テーブル最適化中にエラー: {e}")
            return None

    async def _optimize_queries(
        self, session: AsyncSession, metrics: DatabaseMetrics
    ) -> Optional[OptimizationResult]:
        """クエリを最適化"""
        try:
            start_time = time.time()

            # スロークエリが存在する場合の最適化
            if metrics.slow_queries > 0:
                # クエリキャッシュをクリア
                await session.execute(text("PRAGMA optimize"))
                await session.commit()

                duration = time.time() - start_time

                # 最適化後のメトリクスを取得
                after_metrics = await self.analyze_database_performance(session)

                # 改善度を計算
                improvement = metrics.slow_queries - after_metrics.slow_queries

                return OptimizationResult(
                    operation="query_optimization",
                    table_name="all_tables",
                    before_metrics=asdict(metrics),
                    after_metrics=asdict(after_metrics),
                    improvement=improvement,
                    duration=duration,
                    timestamp=datetime.now().isoformat(),
                )

            return None

        except Exception as e:
            logger.error(f"クエリ最適化中にエラー: {e}")
            return None

    def _calculate_improvement(
        self, before: Dict[str, float], after: Dict[str, float]
    ) -> float:
        """改善度を計算"""
        try:
            if not before or not after:
                return 0.0

            total_before = sum(before.values())
            total_after = sum(after.values())

            if total_before == 0:
                return 0.0

            return ((total_before - total_after) / total_before) * 100

        except Exception:
            return 0.0

    async def _send_optimization_report_to_discord(
        self,
        before_metrics: DatabaseMetrics,
        after_metrics: DatabaseMetrics,
        results: List[OptimizationResult],
    ):
        """最適化レポートをDiscordに送信"""
        try:
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )

            if webhook_url and results:
                async with DiscordWebhookSender(webhook_url) as sender:
                    # 改善度を計算
                    total_improvement = sum(result.improvement for result in results)
                    total_duration = sum(result.duration for result in results)

                    embed = {
                        "title": "🔧 データベース最適化完了",
                        "description": f"最適化件数: {len(results)}件\n"
                        f"総改善度: {total_improvement:.1f}%\n"
                        f"実行時間: {total_duration:.2f}秒",
                        "color": 0x00FF00,
                        "timestamp": datetime.now().isoformat(),
                        "fields": [],
                    }

                    # 各最適化結果を追加
                    for result in results:
                        embed["fields"].append(
                            {
                                "name": f"最適化: {result.operation}",
                                "value": f"改善度: {result.improvement:.1f}%\n"
                                f"実行時間: {result.duration:.2f}秒",
                                "inline": True,
                            }
                        )

                    # メトリクス比較
                    embed["fields"].append(
                        {
                            "name": "最適化前後比較",
                            "value": f"スロークエリ: {before_metrics.slow_queries} → {after_metrics.slow_queries}\n"
                            f"フラグメンテーション: {before_metrics.fragmentation_ratio:.1f}% → {after_metrics.fragmentation_ratio:.1f}%",
                            "inline": False,
                        }
                    )

                    await sender.send_embed(embed)
                    logger.info("データベース最適化レポートをDiscordに送信")

        except Exception as e:
            logger.error(f"最適化レポートのDiscord送信に失敗: {e}")

    async def get_optimization_history(self, days: int = 7) -> List[OptimizationResult]:
        """最適化履歴を取得"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)

            recent_results = [
                result
                for result in self.optimization_history
                if datetime.fromisoformat(result.timestamp) > cutoff_time
            ]

            return recent_results

        except Exception as e:
            logger.error(f"最適化履歴取得中にエラー: {e}")
            return []

    async def schedule_optimization(
        self, session: AsyncSession, interval_hours: int = 24
    ):
        """定期的な最適化をスケジュール"""
        try:
            while True:
                logger.info(f"定期的なデータベース最適化を実行 (間隔: {interval_hours}時間)")

                await self.optimize_database(session)

                # 指定された間隔で待機
                await asyncio.sleep(interval_hours * 3600)

        except Exception as e:
            logger.error(f"定期的な最適化中にエラー: {e}")

    def clear_optimization_history(self):
        """最適化履歴をクリア"""
        self.optimization_history.clear()
        logger.info("最適化履歴をクリアしました")
