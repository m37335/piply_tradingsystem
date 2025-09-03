"""
差分検知付きテクニカル指標計算サービス

責任:
- 差分検知と計算の統合
- 効率的な計算実行
- 計算結果の検証
"""

from datetime import datetime
from typing import Any, Dict, Optional

import pytz

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.diff_detection_service import (
    DiffDetectionService,
)
from src.utils.logging_config import get_application_logger

logger = get_application_logger()


class TechnicalIndicatorDiffCalculator:
    """
    差分検知付きテクニカル指標計算サービス

    責任:
    - 差分検知と計算の統合
    - 効率的な計算実行
    - 計算結果の検証
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair = currency_pair
        self.calculator = None
        self.diff_service = None
        self.session = None

    async def initialize(self):
        """初期化処理"""
        try:
            logger.info("🚀 TechnicalIndicatorDiffCalculator初期化開始...")

            # データベースセッションを取得
            self.session = await get_async_session()

            # 差分検知サービスを初期化
            self.diff_service = DiffDetectionService(self.session)

            # テクニカル指標計算器をインポートして初期化
            from scripts.cron.advanced_technical.enhanced_unified_technical_calculator import (
                EnhancedUnifiedTechnicalCalculator,
            )

            self.calculator = EnhancedUnifiedTechnicalCalculator(self.currency_pair)
            await self.calculator.initialize()

            logger.info("✅ TechnicalIndicatorDiffCalculator初期化完了")

        except Exception as e:
            logger.error(f"❌ TechnicalIndicatorDiffCalculator初期化エラー: {e}")
            raise

    async def calculate_differential_indicators(
        self, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        差分検知付きテクニカル指標計算

        Args:
            limit: 各時間足の処理件数制限

        Returns:
            Dict[str, Any]: 計算結果の詳細
        """
        try:
            logger.info("🔄 差分検知付きテクニカル指標計算開始...")
            start_time = datetime.now()

            # Step 1: 差分検知
            differences = await self.diff_service.detect_calculation_differences()

            if not differences:
                logger.warning("⚠️ 差分検知で対象データが見つかりませんでした")
                return {"status": "no_data", "message": "対象データなし"}

            # Step 2: 計算対象の特定
            total_uncalculated = sum(differences.values())
            if total_uncalculated == 0:
                logger.info("✅ 全てのデータが計算済みです")
                return {"status": "already_calculated", "message": "全データ計算済み"}

            logger.info(f"📊 計算対象: {total_uncalculated}件")
            for timeframe, count in differences.items():
                if count > 0:
                    logger.info(f"   📈 {timeframe}: {count}件")

            # Step 3: 各時間足の差分計算実行
            results = {}
            total_processed = 0

            for timeframe, count in differences.items():
                if count > 0:
                    timeframe_limit = limit if limit else None
                    result = await self.calculate_for_timeframe(
                        timeframe, timeframe_limit
                    )
                    results[timeframe] = result
                    total_processed += result.get("processed_count", 0)

            # Step 4: 計算完了フラグ更新
            await self._update_calculation_flags()

            # Step 5: 結果検証
            completeness = await self.validate_calculation_completeness()

            # Step 6: 実行時間計算
            execution_time = (datetime.now() - start_time).total_seconds()

            # Step 7: 結果レポート生成
            report = await self.generate_diff_report()

            final_result = {
                "status": "success",
                "execution_time": execution_time,
                "total_processed": total_processed,
                "differences": differences,
                "results": results,
                "completeness": completeness,
                "report": report,
            }

            logger.info(
                f"✅ 差分計算完了: {total_processed}件処理, "
                f"実行時間: {execution_time:.2f}秒"
            )

            return final_result

        except Exception as e:
            logger.error(f"❌ 差分計算エラー: {e}")
            return {"status": "error", "error": str(e), "execution_time": 0}

    async def calculate_for_timeframe(
        self, timeframe: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        指定時間足の差分計算

        Args:
            timeframe: 時間足
            limit: 処理件数制限

        Returns:
            Dict[str, Any]: 計算結果
        """
        try:
            logger.info(f"🔄 {timeframe}の差分計算開始...")
            start_time = datetime.now()

            # Step 1: 未計算データを取得
            uncalculated_data = await self.diff_service.get_uncalculated_data(
                timeframe, limit
            )

            if not uncalculated_data:
                logger.info(f"ℹ️ {timeframe}: 未計算データがありません")
                return {"status": "no_data", "processed_count": 0, "execution_time": 0}

            # Step 2: テクニカル指標計算
            processed_count = 0

            # 時間足をEnhancedUnifiedTechnicalCalculatorの形式に変換
            timeframe_mapping = {"5m": "M5", "1h": "H1", "4h": "H4", "1d": "D1"}

            calculator_timeframe = timeframe_mapping.get(timeframe, timeframe)

            # 計算実行
            calculation_result = await self.calculator.calculate_timeframe_indicators(
                calculator_timeframe, limit=len(uncalculated_data)
            )
            
            # calculation_resultはint型なので、そのまま使用
            processed_count = (
                calculation_result if isinstance(calculation_result, int) else 0
            )

            # Step 3: 処理したデータのフラグ更新
            if processed_count > 0:
                await self.diff_service.update_calculation_flags(
                    uncalculated_data[:processed_count]
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            result = {
                "status": "success",
                "processed_count": processed_count,
                "total_uncalculated": len(uncalculated_data),
                "execution_time": execution_time,
                "calculation_result": calculation_result,
            }

            logger.info(
                f"✅ {timeframe}差分計算完了: {processed_count}件処理, "
                f"実行時間: {execution_time:.2f}秒"
            )

            return result

        except Exception as e:
            logger.error(f"❌ {timeframe}差分計算エラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processed_count": 0,
                "execution_time": 0,
            }

    async def validate_calculation_completeness(self) -> bool:
        """
        計算完了の検証

        Returns:
            bool: 計算が完了している場合True
        """
        try:
            logger.info("🔍 計算完了検証中...")

            # 計算状況を取得
            status = await self.diff_service.get_calculation_status()

            if not status:
                logger.warning("⚠️ 計算状況の取得に失敗しました")
                return False

            uncalculated_count = status.get("uncalculated_records", 0)
            overall_progress = status.get("overall_progress", 0)

            # 未計算データが0件で、進捗が100%に近い場合に完了とみなす
            is_complete = uncalculated_count == 0 and overall_progress >= 99.9

            logger.info(
                f"📊 計算完了検証: 未計算{uncalculated_count}件, "
                f"進捗{overall_progress:.1f}%, 完了: {is_complete}"
            )

            return is_complete

        except Exception as e:
            logger.error(f"❌ 計算完了検証エラー: {e}")
            return False

    async def generate_diff_report(self) -> Dict[str, Any]:
        """
        差分計算レポートの生成

        Returns:
            Dict[str, Any]: 詳細レポート
        """
        try:
            logger.info("📊 差分計算レポート生成中...")

            # 計算状況を取得
            status = await self.diff_service.get_calculation_status()

            # レポート生成
            report = {
                "generated_at": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
                "currency_pair": self.currency_pair,
                "overall_status": status,
                "summary": {
                    "total_records": status.get("total_records", 0),
                    "calculated_records": status.get("calculated_records", 0),
                    "uncalculated_records": status.get("uncalculated_records", 0),
                    "overall_progress": status.get("overall_progress", 0),
                },
                "timeframe_details": status.get("timeframe_stats", {}),
            }

            logger.info("✅ 差分計算レポート生成完了")
            return report

        except Exception as e:
            logger.error(f"❌ レポート生成エラー: {e}")
            return {"error": str(e)}

    async def _update_calculation_flags(self):
        """計算完了フラグの更新（内部メソッド）"""
        try:
            # このメソッドは各時間足の計算で個別に呼び出されるため、
            # ここでは何もしない（既に個別に更新済み）
            pass

        except Exception as e:
            logger.error(f"❌ フラグ更新エラー: {e}")

    async def cleanup(self):
        """リソースのクリーンアップ"""
        try:
            logger.info("🧹 TechnicalIndicatorDiffCalculatorクリーンアップ開始...")

            if self.calculator:
                await self.calculator.cleanup()

            if self.session:
                await self.session.close()

            logger.info("✅ TechnicalIndicatorDiffCalculatorクリーンアップ完了")

        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")

    async def get_calculation_status(self) -> Dict[str, Any]:
        """
        計算状況の取得（DiffDetectionServiceのラッパー）

        Returns:
            Dict[str, Any]: 計算状況の詳細
        """
        if not self.diff_service:
            logger.error("❌ DiffDetectionServiceが初期化されていません")
            return {}

        return await self.diff_service.get_calculation_status()

    async def reset_calculation_flags(self, timeframe: Optional[str] = None) -> bool:
        """
        計算フラグのリセット（DiffDetectionServiceのラッパー）

        Args:
            timeframe: 特定の時間足のみリセット（Noneの場合は全件）

        Returns:
            bool: リセット成功時True
        """
        if not self.diff_service:
            logger.error("❌ DiffDetectionServiceが初期化されていません")
            return False

        return await self.diff_service.reset_calculation_flags(timeframe)
