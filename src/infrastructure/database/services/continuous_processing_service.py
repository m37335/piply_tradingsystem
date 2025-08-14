"""
継続処理統合サービス

責任:
- 5分足データ取得後の自動集計処理
- マルチタイムフレームテクニカル指標計算
- パターン検出の統合実行
- エラーハンドリングとリトライ機能

特徴:
- 完全自動化された継続処理パイプライン
- 各ステップの依存関係管理
- 包括的エラーハンドリング
- パフォーマンス監視
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.services.efficient_pattern_detection_service import (
    EfficientPatternDetectionService,
)
from src.infrastructure.database.services.notification_integration_service import (
    NotificationIntegrationService,
)
from src.infrastructure.database.services.talib_technical_indicator_service import (
    TALibTechnicalIndicatorService,
)
from src.infrastructure.database.services.timeframe_aggregator_service import (
    TimeframeAggregatorService,
)

logger = logging.getLogger(__name__)


class ContinuousProcessingService:
    """
    継続処理統合サービス

    責任:
    - 5分足データ取得後の自動集計処理
    - マルチタイムフレームテクニカル指標計算
    - パターン検出の統合実行
    - エラーハンドリングとリトライ機能
    """

    def __init__(self, session: AsyncSession):
        # 依存サービス初期化
        self.session = session
        self.timeframe_aggregator = TimeframeAggregatorService(session)
        self.technical_indicator_service = TALibTechnicalIndicatorService(session)
        self.pattern_detection_service = EfficientPatternDetectionService(session)
        # 通知サービス初期化
        self.notification_service = NotificationIntegrationService(session)

        # 設定
        self.currency_pair = "USD/JPY"
        self.timeframes = [
            "M5",
            "H1", 
            "H4",
            "D1",
        ]  # TALibTechnicalIndicatorServiceの形式に合わせる
        self.retry_attempts = 3
        self.retry_delay = 30  # 秒

        # 処理統計
        self.processing_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "last_processing_time": None,
            "average_processing_time": 0.0,
        }

    async def process_5m_data(self, price_data: PriceDataModel) -> Dict[str, Any]:
        """
        5分足データの継続処理を実行

        Args:
            price_data: 取得された5分足データ

        Returns:
            Dict[str, Any]: 処理結果の統計情報
        """
        start_time = datetime.now()
        self.processing_stats["total_cycles"] += 1

        try:
            logger.info("🔄 継続処理サイクル開始")

            results = {
                "aggregation": {},
                "indicators": {},
                "patterns": {},
                "notifications": {},
                "processing_time": 0,
                "status": "success",
            }

            # 1. 5分足データは既にDataFetcherServiceで保存済み
            logger.info("💾 5分足データは既に保存済み（DataFetcherService経由）")
            saved_data = price_data  # 既に保存されたデータを使用
            results["saved_5m_data"] = saved_data

            # 2. 時間軸集計を実行
            logger.info("📊 時間軸集計実行中...")
            aggregation_results = await self.aggregate_timeframes()
            results["aggregation"] = aggregation_results

            # 3. テクニカル指標を計算
            logger.info("📈 テクニカル指標計算中...")
            indicator_results = await self.calculate_all_indicators()
            results["indicators"] = indicator_results

            # 4. パターン検出を実行
            logger.info("🔍 パターン検出実行中...")
            pattern_results = await self.detect_patterns()
            results["patterns"] = pattern_results

            # 5. 通知処理
            logger.info("📢 通知処理実行中...")
            notification_results = await self.process_notifications()
            results["notifications"] = notification_results

            # 処理時間を記録
            processing_time = (datetime.now() - start_time).total_seconds()
            results["processing_time"] = processing_time
            self.processing_stats["last_processing_time"] = processing_time
            self.processing_stats["successful_cycles"] += 1

            # 平均処理時間を更新
            self._update_average_processing_time(processing_time)

            logger.info(f"✅ 継続処理サイクル完了: {processing_time:.2f}秒")
            return results

        except Exception as e:
            self.processing_stats["failed_cycles"] += 1
            processing_time = (datetime.now() - start_time).total_seconds()

            logger.error(f"❌ 継続処理サイクルエラー: {e}")
            return {
                "error": str(e),
                "processing_time": processing_time,
                "status": "failed",
            }

    async def aggregate_timeframes(self) -> Dict[str, int]:
        """
        時間軸の自動集計を実行

        Returns:
            Dict[str, int]: 各時間軸の集計件数
        """
        try:
            logger.info("📊 時間軸集計開始")

            results = {}

            # 1時間足集計
            h1_data = await self.timeframe_aggregator.aggregate_1h_data()
            results["1h"] = len(h1_data)

            # 4時間足集計
            h4_data = await self.timeframe_aggregator.aggregate_4h_data()
            results["4h"] = len(h4_data)

            # 日足集計
            d1_data = await self.timeframe_aggregator.aggregate_1d_data()
            results["1d"] = len(d1_data)

            logger.info(
                f"✅ 時間軸集計完了: 1h={results['1h']}件, 4h={results['4h']}件, 1d={results['1d']}件"
            )
            return results

        except Exception as e:
            logger.error(f"❌ 時間軸集計エラー: {e}")
            return {"error": str(e)}

    async def calculate_all_indicators(self) -> Dict[str, int]:
        """
        全時間軸のテクニカル指標を計算

        Returns:
            Dict[str, int]: 各時間軸の指標計算件数
        """
        try:
            logger.info("📈 テクニカル指標計算開始")

            results = {}

            # 各時間軸のテクニカル指標を計算（TA-Lib使用）
            for timeframe in self.timeframes:
                indicator_count = await self.technical_indicator_service.calculate_and_save_all_indicators(
                    timeframe
                )
                results[timeframe] = (
                    sum(indicator_count.values())
                    if isinstance(indicator_count, dict)
                    else indicator_count
                )

            logger.info(f"✅ テクニカル指標計算完了: {results}")
            return results

        except Exception as e:
            logger.error(f"❌ テクニカル指標計算エラー: {e}")
            return {"error": str(e)}

    async def detect_patterns(self) -> Dict[str, int]:
        """
        パターン検出を実行

        Returns:
            Dict[str, int]: 検出されたパターン数
        """
        try:
            logger.info("🔍 パターン検出開始")

            results = {}

            # 各時間軸でパターン検出を実行
            for timeframe in self.timeframes:
                pattern_count = (
                    await (
                        self.pattern_detection_service.detect_patterns_for_timeframe(
                            timeframe
                        )
                    )
                )
                results[timeframe] = pattern_count

            logger.info(f"✅ パターン検出完了: {results}")
            return results

        except Exception as e:
            logger.error(f"❌ パターン検出エラー: {e}")
            return {"error": str(e)}

    async def process_notifications(self) -> Dict[str, int]:
        """
        通知処理を実行

        Returns:
            Dict[str, int]: 送信された通知数
        """
        try:
            logger.info("📢 通知処理開始")

            # 未通知のパターンを取得
            unnotified_patterns = await (
                self.pattern_detection_service.get_unnotified_patterns()
            )

            # 通知サービスが初期化されていない場合はスキップ
            if self.notification_service is None:
                logger.warning("⚠️ 通知サービスが初期化されていません")
                return {"sent": 0, "total": len(unnotified_patterns), "skipped": True}

            notification_count = 0
            for pattern in unnotified_patterns:
                # 通知を送信
                success = await self.notification_service.send_pattern_notification(
                    pattern
                )
                if success:
                    # 通知済みフラグを更新
                    await self.pattern_detection_service.mark_notification_sent(
                        pattern.id
                    )
                    notification_count += 1

            logger.info(f"✅ 通知処理完了: {notification_count}件送信")
            return {"sent": notification_count, "total": len(unnotified_patterns)}

        except Exception as e:
            logger.error(f"❌ 通知処理エラー: {e}")
            return {"error": str(e)}

    async def _save_5m_data(self, price_data: PriceDataModel) -> PriceDataModel:
        """
        5分足データを保存

        Args:
            price_data: 保存する5分足データ

        Returns:
            PriceDataModel: 保存されたデータ
        """
        try:
            # デバッグログ: 保存前のデータ内容
            logger.info(
                f"💾 保存前のデータ内容: "
                f"O={price_data.open_price}, H={price_data.high_price}, "
                f"L={price_data.low_price}, C={price_data.close_price}, "
                f"V={price_data.volume}, T={price_data.timestamp}"
            )

            # 重複チェック
            existing = await self.timeframe_aggregator.price_repo.find_by_timestamp(
                price_data.timestamp, self.currency_pair
            )

            if existing:
                logger.info(f"⚠️ 5分足データ重複: {price_data.timestamp}")
                logger.info(
                    f"⚠️ 既存データ内容: "
                    f"O={existing.open_price}, H={existing.high_price}, "
                    f"L={existing.low_price}, C={existing.close_price}, "
                    f"V={existing.volume}"
                )

                # 既存データの内容をログ出力（削除はしない）
                if (
                    existing.open_price
                    == existing.high_price
                    == existing.low_price
                    == existing.close_price
                ):
                    logger.warning(
                        f"⚠️ 既存データが同じOHLC値: {existing.open_price:.4f}"
                    )
                else:
                    logger.info(f"✅ 既存データは正常なOHLC値")

                logger.info(f"✅ 既存データを返します")
                return existing

            # データを保存
            saved_data = await self.timeframe_aggregator.price_repo.save(price_data)
            logger.info(f"💾 5分足データ保存完了: {price_data.timestamp}")
            logger.info(
                f"💾 保存後のデータ内容: "
                f"O={saved_data.open_price}, H={saved_data.high_price}, "
                f"L={saved_data.low_price}, C={saved_data.close_price}, "
                f"V={saved_data.volume}"
            )
            return saved_data

        except Exception as e:
            logger.error(f"❌ 5分足データ保存エラー: {e}")
            raise

    def _update_average_processing_time(self, processing_time: float):
        """
        平均処理時間を更新

        Args:
            processing_time: 今回の処理時間
        """
        if self.processing_stats["successful_cycles"] > 1:
            current_avg = self.processing_stats["average_processing_time"]
            new_avg = (
                current_avg * (self.processing_stats["successful_cycles"] - 1)
                + processing_time
            ) / self.processing_stats["successful_cycles"]
            self.processing_stats["average_processing_time"] = new_avg
        else:
            self.processing_stats["average_processing_time"] = processing_time

    async def get_processing_stats(self) -> Dict[str, Any]:
        """
        処理統計を取得

        Returns:
            Dict[str, Any]: 処理統計情報
        """
        return {
            **self.processing_stats,
            "success_rate": (
                self.processing_stats["successful_cycles"]
                / max(self.processing_stats["total_cycles"], 1)
                * 100
            ),
            "currency_pair": self.currency_pair,
            "timeframes": self.timeframes,
        }

    async def reset_stats(self):
        """
        処理統計をリセット
        """
        self.processing_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "last_processing_time": None,
            "average_processing_time": 0.0,
        }
        logger.info("🔄 処理統計をリセットしました")

    async def process_latest_data(self) -> Dict[str, Any]:
        """
        最新データの継続処理を実行

        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            logger.info("🔄 最新データの継続処理開始")

            # 実際の5分足データを取得
            from src.infrastructure.database.services.data_fetcher_service import (
                DataFetcherService,
            )

            data_fetcher = DataFetcherService(self.session)
            latest_data = await data_fetcher.fetch_real_5m_data()

            if not latest_data:
                logger.warning("⚠️ 実際の5分足データの取得に失敗しました")
                return {
                    "status": "no_data",
                    "message": "実際の5分足データの取得に失敗しました",
                    "processing_time": 0,
                }

            # 継続処理を実行
            result = await self.process_5m_data(latest_data)

            logger.info("✅ 最新データの継続処理完了")
            return result

        except Exception as e:
            logger.error(f"❌ 最新データの継続処理エラー: {e}")
            self.processing_stats["failed_cycles"] += 1
            return {
                "status": "error",
                "error": str(e),
                "processing_time": 0,
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        サービス健全性チェック

        Returns:
            Dict[str, Any]: 健全性情報
        """
        try:
            health_status = {
                "service": "ContinuousProcessingService",
                "status": "healthy",
                "timestamp": datetime.now(),
                "dependencies": {},
            }

            # 依存サービスの健全性チェック
            try:
                await self.timeframe_aggregator.get_aggregation_status()
                health_status["dependencies"]["timeframe_aggregator"] = "healthy"
            except Exception as e:
                health_status["dependencies"][
                    "timeframe_aggregator"
                ] = f"unhealthy: {e}"

            try:
                await self.technical_indicator_service.get_service_status()
                health_status["dependencies"]["technical_indicator_service"] = "healthy"
            except Exception as e:
                health_status["dependencies"][
                    "technical_indicator_service"
                ] = f"unhealthy: {e}"

            try:
                await self.pattern_detection_service.get_service_status()
                health_status["dependencies"]["pattern_detection_service"] = "healthy"
            except Exception as e:
                health_status["dependencies"][
                    "pattern_detection_service"
                ] = f"unhealthy: {e}"

            # 全体の健全性判定
            unhealthy_deps = [
                dep
                for dep in health_status["dependencies"].values()
                if not dep.startswith("healthy")
            ]

            if unhealthy_deps:
                health_status["status"] = "degraded"
                health_status["issues"] = unhealthy_deps

            return health_status

        except Exception as e:
            return {
                "service": "ContinuousProcessingService",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(),
            }
