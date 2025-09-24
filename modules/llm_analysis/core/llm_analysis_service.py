"""
LLM分析サービス

LLM分析の統合サービスを提供します。
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ...data_persistence.core.database.connection_manager import (
    DatabaseConnectionManager,
)
from ..config.settings import AnalysisFrequency, AnalysisType, LLMAnalysisSettings
from ..core.analysis_engine.analysis_engine import AnalysisEngine
from ..core.data_preparator import LLMDataPreparator
from ..core.llm_client.llm_client import LLMClient
from ..core.quality_control.quality_controller import QualityController

logger = logging.getLogger(__name__)


class LLMAnalysisService:
    """LLM分析サービス"""

    def __init__(self, settings: LLMAnalysisSettings):
        self.settings = settings
        self.data_preparator = LLMDataPreparator()
        self.llm_client = LLMClient(settings.llm)
        self.analysis_engine = AnalysisEngine(settings.analysis)
        self.quality_controller = QualityController(settings.quality_control)

        # データベース接続（LLMDataPreparatorが管理するため削除）
        # self.database_manager = DatabaseConnectionManager(...)

        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """サービスを開始"""
        if self._running:
            logger.warning("LLM analysis service is already running")
            return

        try:
            # データ準備器を初期化
            await self.data_preparator.initialize()

            # LLMクライアントを初期化
            await self.llm_client.initialize()

            # サービスを開始
            self._running = True

            # 分析タスクを開始
            if self.settings.analysis.frequency != AnalysisFrequency.ON_DEMAND:
                await self._start_analysis_tasks()

            logger.info("LLM analysis service started successfully")

        except Exception as e:
            logger.error(f"Failed to start LLM analysis service: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """サービスを停止"""
        if not self._running:
            return

        self._running = False

        # 実行中のタスクをキャンセル
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # タスクの完了を待機
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # データ準備器の接続を閉じる
        await self.data_preparator.connection_manager.close()

        logger.info("LLM analysis service stopped")

    async def _start_analysis_tasks(self) -> None:
        """分析タスクを開始"""
        logger.info("Starting LLM analysis tasks")

        # 各シンボルとタイムフレームの組み合わせでタスクを作成
        for symbol in self.settings.analysis.symbols:
            for timeframe in self.settings.analysis.timeframes:
                for analysis_type in self.settings.analysis.analysis_types:
                    task_name = (
                        f"llm_analysis_{symbol}_{timeframe}_{analysis_type.value}"
                    )

                    # 分析頻度に応じてタスクを作成
                    if self.settings.analysis.frequency == AnalysisFrequency.HOURLY:
                        interval_seconds = 3600
                    elif self.settings.analysis.frequency == AnalysisFrequency.DAILY:
                        interval_seconds = 86400
                    elif self.settings.analysis.frequency == AnalysisFrequency.WEEKLY:
                        interval_seconds = 604800
                    else:
                        interval_seconds = 300  # 5分間隔（デフォルト）

                    task = asyncio.create_task(
                        self._analysis_worker(
                            symbol, timeframe, analysis_type, interval_seconds
                        )
                    )
                    self._tasks.append(task)

        logger.info(f"Started {len(self._tasks)} LLM analysis tasks")

    async def _analysis_worker(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: AnalysisType,
        interval_seconds: int,
    ) -> None:
        """分析ワーカー"""
        logger.info(
            f"Starting analysis worker for {symbol} {timeframe} {analysis_type.value}"
        )

        while self._running:
            try:
                # 分析を実行
                await self._perform_analysis(symbol, timeframe, analysis_type)

                # 次の分析まで待機
                await asyncio.sleep(interval_seconds)

            except asyncio.CancelledError:
                logger.info(
                    f"Analysis worker cancelled for {symbol} {timeframe} {analysis_type.value}"
                )
                break
            except Exception as e:
                logger.error(
                    f"Analysis worker error for {symbol} {timeframe} {analysis_type.value}: {e}"
                )
                # エラー時は少し長めに待機
                await asyncio.sleep(interval_seconds * 2)

    async def _perform_analysis(
        self, symbol: str, timeframe: str, analysis_type: AnalysisType
    ) -> None:
        """分析を実行"""
        try:
            logger.info(
                f"Performing {analysis_type.value} analysis for {symbol} {timeframe}"
            )

            # 1. データを準備
            prepared_data = await self._prepare_analysis_data(symbol, timeframe)

            if not prepared_data:
                logger.warning(f"No data available for analysis: {symbol} {timeframe}")
                return

            # 2. 分析を実行
            analysis_result = await self._execute_analysis(
                symbol, timeframe, analysis_type, prepared_data
            )

            if not analysis_result:
                logger.warning(
                    f"Analysis failed: {symbol} {timeframe} {analysis_type.value}"
                )
                return

            # 3. 品質チェック
            quality_score = await self._check_analysis_quality(analysis_result)

            # 4. 結果をデータベースに保存
            await self._save_analysis_result(
                symbol, timeframe, analysis_type, analysis_result, quality_score
            )

            logger.info(
                f"Analysis completed for {symbol} {timeframe} {analysis_type.value}"
            )

        except Exception as e:
            logger.error(
                f"Analysis failed for {symbol} {timeframe} {analysis_type.value}: {e}"
            )
            raise

    async def _prepare_analysis_data(
        self, symbol: str, timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """分析データを準備"""
        try:
            # データベースから価格データを取得
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM price_data
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp DESC
                LIMIT $3
            """

            result = await self.database_manager.execute_query(
                query, symbol, timeframe, self.settings.analysis.lookback_periods
            )

            if not result:
                return None

            # データを準備
            prepared_data = await self.data_preparator.prepare_data(result)

            return prepared_data

        except Exception as e:
            logger.error(
                f"Failed to prepare analysis data for {symbol} {timeframe}: {e}"
            )
            return None

    async def _execute_analysis(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: AnalysisType,
        prepared_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """分析を実行"""
        try:
            # 分析エンジンで分析を実行
            analysis_result = await self.analysis_engine.analyze(
                symbol=symbol,
                timeframe=timeframe,
                analysis_type=analysis_type,
                data=prepared_data,
                llm_client=self.llm_client,
            )

            return analysis_result

        except Exception as e:
            logger.error(
                f"Failed to execute analysis for {symbol} {timeframe} {analysis_type.value}: {e}"
            )
            return None

    async def _check_analysis_quality(self, analysis_result: Dict[str, Any]) -> float:
        """分析品質をチェック"""
        try:
            if not self.settings.quality_control.enable_quality_scoring:
                return 1.0

            quality_score = await self.quality_controller.score_analysis(
                analysis_result
            )
            return quality_score

        except Exception as e:
            logger.error(f"Failed to check analysis quality: {e}")
            return 0.5  # デフォルトスコア

    async def _save_analysis_result(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: AnalysisType,
        analysis_result: Dict[str, Any],
        quality_score: float,
    ) -> None:
        """分析結果をデータベースに保存"""
        try:
            # 入力データのハッシュを生成
            input_data_hash = hashlib.sha256(
                json.dumps(
                    analysis_result.get("input_data", {}), sort_keys=True
                ).encode()
            ).hexdigest()

            # 分析結果を保存
            insert_query = """
                INSERT INTO llm_analysis_results (
                    symbol, timeframe, analysis_type, analysis_timestamp,
                    input_data_hash, model_name, model_version,
                    analysis_result, confidence_score, processing_time_seconds
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """

            await self.database_manager.execute_command(
                insert_query,
                symbol,
                timeframe,
                analysis_type.value,
                datetime.now(),
                input_data_hash,
                self.settings.llm.model_name,
                "1.0",  # モデルバージョン
                json.dumps(analysis_result),
                analysis_result.get("confidence_score", 0.0),
                analysis_result.get("processing_time_seconds", 0.0),
            )

            # 入力データも保存
            await self._save_input_data(
                symbol, timeframe, input_data_hash, analysis_result
            )

            # 品質スコアも保存
            if self.settings.quality_control.enable_quality_scoring:
                await self._save_quality_metrics(
                    input_data_hash, quality_score, analysis_result
                )

            logger.info(
                f"Analysis result saved for {symbol} {timeframe} {analysis_type.value}"
            )

        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            raise

    async def _save_input_data(
        self,
        symbol: str,
        timeframe: str,
        input_data_hash: str,
        analysis_result: Dict[str, Any],
    ) -> None:
        """入力データを保存"""
        try:
            input_data = analysis_result.get("input_data", {})

            insert_query = """
                INSERT INTO llm_analysis_input_data (
                    data_hash, symbol, timeframe, data_start_time, data_end_time,
                    data_points, technical_indicators, market_context
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (data_hash) DO NOTHING
            """

            await self.database_manager.execute_command(
                insert_query,
                input_data_hash,
                symbol,
                timeframe,
                input_data.get("start_time"),
                input_data.get("end_time"),
                json.dumps(input_data.get("data_points", [])),
                json.dumps(input_data.get("technical_indicators", {})),
                json.dumps(input_data.get("market_context", {})),
            )

        except Exception as e:
            logger.error(f"Failed to save input data: {e}")

    async def _save_quality_metrics(
        self,
        input_data_hash: str,
        quality_score: float,
        analysis_result: Dict[str, Any],
    ) -> None:
        """品質メトリクスを保存"""
        try:
            # 分析結果IDを取得
            result_query = """
                SELECT id FROM llm_analysis_results
                WHERE input_data_hash = $1
                ORDER BY created_at DESC
                LIMIT 1
            """

            result = await self.database_manager.execute_query(
                result_query, input_data_hash
            )

            if not result:
                return

            analysis_result_id = result[0]["id"]

            # 品質メトリクスを保存
            insert_query = """
                INSERT INTO llm_analysis_quality (
                    analysis_result_id, quality_metrics, accuracy_score,
                    relevance_score, consistency_score
                ) VALUES ($1, $2, $3, $4, $5)
            """

            quality_metrics = {
                "overall_score": quality_score,
                "timestamp": datetime.now().isoformat(),
            }

            await self.database_manager.execute_command(
                insert_query,
                analysis_result_id,
                json.dumps(quality_metrics),
                quality_score,
                quality_score,
                quality_score,
            )

        except Exception as e:
            logger.error(f"Failed to save quality metrics: {e}")

    async def analyze_on_demand(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: AnalysisType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """オンデマンド分析を実行"""
        try:
            logger.info(
                f"Performing on-demand analysis for {symbol} {timeframe} {analysis_type.value}"
            )

            # データを準備
            if start_date and end_date:
                # 指定期間のデータを取得
                query = """
                    SELECT timestamp, open, high, low, close, volume
                    FROM price_data
                    WHERE symbol = $1 AND timeframe = $2
                    AND timestamp BETWEEN $3 AND $4
                    ORDER BY timestamp DESC
                """

                result = await self.database_manager.execute_query(
                    query, symbol, timeframe, start_date, end_date
                )
            else:
                # 最新のデータを取得
                result = await self.database_manager.execute_query(
                    """
                        SELECT timestamp, open, high, low, close, volume
                        FROM price_data
                        WHERE symbol = $1 AND timeframe = $2
                        ORDER BY timestamp DESC
                        LIMIT $3
                    """,
                    symbol,
                    timeframe,
                    self.settings.analysis.lookback_periods,
                )

            if not result:
                return {"success": False, "error": "No data available for analysis"}

            # データを準備
            prepared_data = await self.data_preparator.prepare_data(result)

            # 分析を実行
            analysis_result = await self.analysis_engine.analyze(
                symbol=symbol,
                timeframe=timeframe,
                analysis_type=analysis_type,
                data=prepared_data,
                llm_client=self.llm_client,
            )

            if not analysis_result:
                return {"success": False, "error": "Analysis failed"}

            # 品質チェック
            quality_score = await self._check_analysis_quality(analysis_result)

            # 結果をデータベースに保存
            await self._save_analysis_result(
                symbol, timeframe, analysis_type, analysis_result, quality_score
            )

            return {
                "success": True,
                "analysis_result": analysis_result,
                "quality_score": quality_score,
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_type": analysis_type.value,
            }

        except Exception as e:
            logger.error(f"On-demand analysis failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_analysis_history(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: Optional[AnalysisType] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """分析履歴を取得"""
        try:
            query = """
                SELECT r.*, q.quality_metrics, q.accuracy_score
                FROM llm_analysis_results r
                LEFT JOIN llm_analysis_quality q ON r.id = q.analysis_result_id
                WHERE r.symbol = $1 AND r.timeframe = $2
            """

            params = [symbol, timeframe]

            if analysis_type:
                query += " AND r.analysis_type = $3"
                params.append(analysis_type.value)
                query += " ORDER BY r.analysis_timestamp DESC LIMIT $4"
                params.append(limit)
            else:
                query += " ORDER BY r.analysis_timestamp DESC LIMIT $3"
                params.append(limit)

            result = await self.database_manager.execute_query(query, *params)

            return [dict(row) for row in result]

        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []

    async def get_analysis_summary(self) -> Dict[str, Any]:
        """分析サマリーを取得"""
        try:
            # 分析統計を取得
            stats_query = """
                SELECT 
                    COUNT(*) as total_analyses,
                    COUNT(DISTINCT symbol) as symbols_analyzed,
                    COUNT(DISTINCT analysis_type) as analysis_types_used,
                    AVG(confidence_score) as avg_confidence,
                    AVG(processing_time_seconds) as avg_processing_time
                FROM llm_analysis_results
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """

            stats_result = await self.database_manager.execute_query(stats_query)
            stats = dict(stats_result[0]) if stats_result else {}

            # 品質統計を取得
            quality_query = """
                SELECT 
                    AVG(accuracy_score) as avg_accuracy,
                    AVG(relevance_score) as avg_relevance,
                    AVG(consistency_score) as avg_consistency
                FROM llm_analysis_quality
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """

            quality_result = await self.database_manager.execute_query(quality_query)
            quality_stats = dict(quality_result[0]) if quality_result else {}

            return {
                "analysis_stats": stats,
                "quality_stats": quality_stats,
                "service_running": self._running,
                "active_tasks": len(self._tasks),
                "settings": self.settings.to_dict(),
            }

        except Exception as e:
            logger.error(f"Failed to get analysis summary: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # データベースのヘルスチェック
            db_health = await self.database_manager.health_check()

            # LLMクライアントのヘルスチェック
            llm_health = await self.llm_client.health_check()

            # 全体のヘルス状態を決定
            overall_health = "healthy"
            if db_health["status"] != "healthy":
                overall_health = "unhealthy"
            elif llm_health.get("status") != "healthy":
                overall_health = "degraded"

            return {
                "status": overall_health,
                "service_running": self._running,
                "database": db_health,
                "llm_client": llm_health,
                "active_tasks": len(self._tasks),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
