"""
統合データサービス

USD/JPY特化の統合データ管理サービス
設計書参照: /app/note/basic_data_acquisition_system_improvement_design.md

責任:
- データ取得の統合管理
- テクニカル指標計算の統合
- パターン検出の統合
- データフローの統一
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.database.services.talib_technical_indicator_service import TALibTechnicalIndicatorService
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService
from src.infrastructure.database.services.pattern_detection_service import (
    PatternDetectionService,
)
from src.infrastructure.error_handling.error_handler import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
)
from src.infrastructure.monitoring.performance_monitor import PerformanceMonitor
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class IntegratedDataService:
    """
    統合データサービス

    責任:
    - データ取得・計算・検出の統合管理
    - データフローの統一
    - エラーハンドリングの統合
    - パフォーマンス最適化

    特徴:
    - ワンストップデータ処理
    - 統合エラーハンドリング
    - パフォーマンス監視
    - データ品質保証
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session

        # 各サービスの初期化
        self.data_fetcher = DataFetcherService(session)
        self.pattern_service = PatternDetectionService(session)
        self.technical_analyzer = TechnicalIndicatorsAnalyzer()
        self.talib_indicator_service = TALibTechnicalIndicatorService(session)

        # リポジトリの初期化
        self.price_repo = PriceDataRepositoryImpl(session)
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)

        # パフォーマンス監視の初期化
        self.performance_monitor = PerformanceMonitor(session)

        # 設定
        self.currency_pair = "USD/JPY"
        self.timeframes = {
            "M5": {"days": 7, "description": "5分足"},
            "H1": {"days": 30, "description": "1時間足"},
            "H4": {"days": 60, "description": "4時間足"},
            "D1": {"days": 365, "description": "日足"},
        }

        self.error_handler = ErrorHandler()  # エラーハンドリング追加
        logger.info(
            "Initialized IntegratedDataService with performance monitoring and error handling"
        )

    async def run_complete_data_cycle(self) -> Dict:
        """
        完全なデータサイクルを実行

        Returns:
            Dict: 実行結果の統計情報
        """
        start_time = datetime.now()

        # パフォーマンス監視開始
        performance_metrics = (
            await self.performance_monitor.collect_comprehensive_metrics()
        )

        results = {
            "data_fetch": {"success": False, "records": 0, "error": None},
            "technical_indicators": {"success": False, "indicators": 0, "error": None},
            "pattern_detection": {"success": False, "patterns": 0, "error": None},
            "performance": {
                "cpu_percent": performance_metrics.cpu_percent,
                "memory_percent": performance_metrics.memory_percent,
                "query_time_ms": performance_metrics.query_execution_time_ms,
                "processing_time_ms": performance_metrics.data_processing_time_ms,
            },
            "execution_time": 0,
            "overall_success": False,
        }

        try:
            logger.info("=== 統合データサイクル開始 ===")

            # 1. データ取得
            logger.info("Step 1: 統合データ取得...")
            data_result = await self._fetch_integrated_data()
            results["data_fetch"] = data_result

            # 2. テクニカル指標計算
            logger.info("Step 2: 統合テクニカル指標計算...")
            indicator_result = await self._calculate_integrated_indicators()
            results["technical_indicators"] = indicator_result

            # 3. パターン検出
            logger.info("Step 3: 統合パターン検出...")
            pattern_result = await self._detect_integrated_patterns()
            results["pattern_detection"] = pattern_result

            # 実行時間計算
            execution_time = datetime.now() - start_time
            results["execution_time"] = execution_time.total_seconds()
            results["overall_success"] = all(
                [
                    results["data_fetch"]["success"],
                    results["technical_indicators"]["success"],
                    results["pattern_detection"]["success"],
                ]
            )

            # パフォーマンスアラートをチェック
            alerts = self.performance_monitor.get_alerts()
            if alerts:
                results["alerts"] = alerts
                for alert in alerts:
                    logger.warning(f"Performance alert: {alert['message']}")

            logger.info(
                f"=== 統合データサイクル完了: {execution_time.total_seconds():.2f}秒 ==="
            )
            logger.info(f"データ取得: {results['data_fetch']['records']}件")
            logger.info(
                f"テクニカル指標: {results['technical_indicators']['indicators']}件"
            )
            logger.info(f"パターン検出: {results['pattern_detection']['patterns']}件")
            logger.info(
                f"パフォーマンス: CPU={results['performance']['cpu_percent']:.1f}%, "
                f"メモリ={results['performance']['memory_percent']:.1f}%, "
                f"クエリ時間={results['performance']['query_time_ms']:.2f}ms"
            )

            return results

        except Exception as e:
            # エラーハンドリングでエラーを処理
            error_info = self.error_handler.handle_error(
                error=e,
                category=ErrorCategory.DATA_PROCESSING,
                severity=ErrorSeverity.HIGH,
                context={"method": "run_complete_data_cycle"},
            )

            logger.error(f"統合データサイクルエラー: {e}")
            results["overall_success"] = False
            results["error_info"] = {
                "error_type": error_info.error_type,
                "error_message": error_info.error_message,
                "category": error_info.category.value,
                "severity": error_info.severity.value,
                "resolved": error_info.resolved,
            }
            return results

    async def _fetch_integrated_data(self) -> Dict:
        """
        統合データ取得

        Returns:
            Dict: データ取得結果
        """
        try:
            # 実際の5分足データを取得
            price_data = await self.data_fetcher.fetch_real_5m_data()

            if price_data:
                logger.info(f"統合データ取得成功: {price_data.close_price}")
                return {"success": True, "records": 1, "error": None}
            else:
                logger.warning("統合データ取得失敗")
                return {"success": False, "records": 0, "error": "No data fetched"}

        except Exception as e:
            logger.error(f"統合データ取得エラー: {e}")
            return {"success": False, "records": 0, "error": str(e)}

    async def _calculate_integrated_indicators(self) -> Dict:
        """
        統合テクニカル指標計算（TA-Lib使用）

        Returns:
            Dict: テクニカル指標計算結果
        """
        try:
            logger.info("🔄 TA-Lib統合テクニカル指標計算開始...")

            # TA-Libサービスを使用して全時間軸の指標を計算
            results = await self.talib_indicator_service.calculate_all_timeframe_indicators()

            total_indicators = 0
            for timeframe, timeframe_results in results.items():
                timeframe_count = sum(timeframe_results.values())
                total_indicators += timeframe_count
                logger.info(f"  ✅ {timeframe}: {timeframe_count}件の指標計算")

            logger.info(f"🎉 TA-Lib統合テクニカル指標計算完了: 合計{total_indicators}件")
            return {"success": True, "indicators": total_indicators, "error": None}

        except Exception as e:
            logger.error(f"TA-Lib統合テクニカル指標計算エラー: {e}")
            return {"success": False, "indicators": 0, "error": str(e)}

    async def _detect_integrated_patterns(self) -> Dict:
        """
        統合パターン検出

        Returns:
            Dict: パターン検出結果
        """
        try:
            # 全パターンを検出
            pattern_results = await self.pattern_service.detect_all_patterns()

            total_patterns = sum(len(patterns) for patterns in pattern_results.values())

            logger.info(f"統合パターン検出完了: {total_patterns}件")

            return {"success": True, "patterns": total_patterns, "error": None}

        except Exception as e:
            logger.error(f"統合パターン検出エラー: {e}")
            return {"success": False, "patterns": 0, "error": str(e)}

    def _convert_to_dataframe(self, price_data_list: List) -> pd.DataFrame:
        """
        価格データリストをDataFrameに変換

        Args:
            price_data_list: 価格データリスト

        Returns:
            pd.DataFrame: 変換されたDataFrame
        """
        try:
            if not price_data_list:
                return pd.DataFrame()

            # データを辞書のリストに変換
            data = []
            for price_data in price_data_list:
                data.append(
                    {
                        "timestamp": price_data.timestamp,
                        "Open": price_data.open_price,
                        "High": price_data.high_price,
                        "Low": price_data.low_price,
                        "Close": price_data.close_price,
                        "Volume": price_data.volume,
                    }
                )

            # DataFrameを作成
            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error converting to DataFrame: {e}")
            return pd.DataFrame()

    async def _calculate_and_save_rsi(self, df: pd.DataFrame, timeframe: str) -> int:
        """RSIを計算して保存"""
        try:
            # RSI計算
            rsi_result = self.technical_analyzer.calculate_rsi(df, timeframe)

            if "error" in rsi_result:
                logger.warning(f"    ⚠️ RSI計算エラー: {rsi_result['error']}")
                return 0

            current_value = rsi_result.get("current_value")
            if current_value is None:
                logger.warning(f"    ⚠️ RSI値が取得できませんでした")
                return 0

            # 最新のタイムスタンプを取得
            latest_timestamp = df.index[-1] if not df.empty else datetime.now()

            # テクニカル指標モデル作成
            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="RSI",
                timeframe=timeframe,
                value=float(current_value),
                parameters={"period": 14},
            )

            if indicator.validate():
                # 重複チェック
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    latest_timestamp, "RSI", timeframe, self.currency_pair
                )

                if not existing:
                    await self.indicator_repo.save(indicator)
                    logger.info(f"    💾 RSI保存: {current_value:.2f}")
                    return 1
                else:
                    logger.debug(f"    ⏭️ RSI重複スキップ")
                    return 0
            else:
                logger.warning(f"    ⚠️ RSIバリデーション失敗")
                return 0

        except Exception as e:
            logger.error(f"    ❌ RSI計算・保存エラー: {e}")
            return 0

    async def _calculate_and_save_macd(self, df: pd.DataFrame, timeframe: str) -> int:
        """MACDを計算して保存"""
        try:
            # MACD計算
            macd_result = self.technical_analyzer.calculate_macd(df, timeframe)

            if "error" in macd_result:
                logger.warning(f"    ⚠️ MACD計算エラー: {macd_result['error']}")
                return 0

            macd_line = macd_result.get("macd_line")
            signal_line = macd_result.get("signal_line")

            if macd_line is None or signal_line is None:
                logger.warning(f"    ⚠️ MACD値が取得できませんでした")
                return 0

            # 最新のタイムスタンプを取得
            latest_timestamp = df.index[-1] if not df.empty else datetime.now()

            saved_count = 0

            # MACD Lineを保存
            macd_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="MACD",
                timeframe=timeframe,
                value=float(macd_line),
                parameters={"type": "macd_line", "fast": 12, "slow": 26, "signal": 9},
            )

            # Signal Lineを保存
            signal_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="MACD_SIGNAL",
                timeframe=timeframe,
                value=float(signal_line),
                parameters={"type": "signal_line", "fast": 12, "slow": 26, "signal": 9},
            )

            # MACD Line保存
            if macd_indicator.validate():
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    latest_timestamp, "MACD", timeframe, self.currency_pair
                )
                if not existing:
                    await self.indicator_repo.save(macd_indicator)
                    saved_count += 1

            # Signal Line保存
            if signal_indicator.validate():
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    latest_timestamp, "MACD_SIGNAL", timeframe, self.currency_pair
                )
                if not existing:
                    await self.indicator_repo.save(signal_indicator)
                    saved_count += 1

            if saved_count > 0:
                logger.info(f"    💾 MACD保存: {macd_line:.4f}, {signal_line:.4f}")

            return saved_count

        except Exception as e:
            logger.error(f"    ❌ MACD計算・保存エラー: {e}")
            return 0

    async def _calculate_and_save_bollinger_bands(
        self, df: pd.DataFrame, timeframe: str
    ) -> int:
        """ボリンジャーバンドを計算して保存"""
        try:
            # ボリンジャーバンド計算
            bb_result = self.technical_analyzer.calculate_bollinger_bands(df, timeframe)

            if "error" in bb_result:
                logger.warning(
                    f"    ⚠️ ボリンジャーバンド計算エラー: {bb_result['error']}"
                )
                return 0

            upper_band = bb_result.get("upper_band")
            middle_band = bb_result.get("middle_band")
            lower_band = bb_result.get("lower_band")

            if upper_band is None or middle_band is None or lower_band is None:
                logger.warning(f"    ⚠️ ボリンジャーバンド値が取得できませんでした")
                return 0

            # 最新のタイムスタンプを取得
            latest_timestamp = df.index[-1] if not df.empty else datetime.now()

            saved_count = 0

            # 各バンドを保存
            for indicator, band_type in [
                (
                    TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=latest_timestamp,
                        indicator_type="BB_UPPER",
                        timeframe=timeframe,
                        value=float(upper_band),
                        parameters={"type": "upper_band", "period": 20, "std_dev": 2},
                    ),
                    "Upper",
                ),
                (
                    TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=latest_timestamp,
                        indicator_type="BB_MIDDLE",
                        timeframe=timeframe,
                        value=float(middle_band),
                        parameters={"type": "middle_band", "period": 20, "std_dev": 2},
                    ),
                    "Middle",
                ),
                (
                    TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=latest_timestamp,
                        indicator_type="BB_LOWER",
                        timeframe=timeframe,
                        value=float(lower_band),
                        parameters={"type": "lower_band", "period": 20, "std_dev": 2},
                    ),
                    "Lower",
                ),
            ]:
                if indicator.validate():
                    existing = await self.indicator_repo.find_by_timestamp_and_type(
                        latest_timestamp,
                        indicator.indicator_type,
                        timeframe,
                        self.currency_pair,
                    )
                    if not existing:
                        await self.indicator_repo.save(indicator)
                        saved_count += 1

            if saved_count > 0:
                logger.info(
                    f"    💾 ボリンジャーバンド保存: {upper_band:.2f}, {middle_band:.2f}, {lower_band:.2f}"
                )

            return saved_count

        except Exception as e:
            logger.error(f"    ❌ ボリンジャーバンド計算・保存エラー: {e}")
            return 0

    async def get_system_status(self) -> Dict:
        """
        システム状態を取得

        Returns:
            Dict: システム状態情報
        """
        try:
            # 最新データの確認
            latest_data = await self.data_fetcher.get_latest_price_data(limit=1)
            latest_timestamp = latest_data[0].timestamp if latest_data else None

            # テクニカル指標の確認（最新のRSIを取得）
            latest_indicators = await self.indicator_repo.find_latest_by_type(
                "RSI", "5m", self.currency_pair, limit=10
            )

            # パターン検出の確認
            latest_patterns = await self.pattern_service.get_latest_patterns(limit=5)

            return {
                "currency_pair": self.currency_pair,
                "latest_data_timestamp": (
                    latest_timestamp.isoformat() if latest_timestamp else None
                ),
                "latest_indicators_count": len(latest_indicators),
                "latest_patterns_count": len(latest_patterns),
                "system_health": "healthy" if latest_timestamp else "warning",
                "last_update": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"システム状態取得エラー: {e}")
            return {
                "currency_pair": self.currency_pair,
                "system_health": "error",
                "error": str(e),
                "last_update": datetime.now().isoformat(),
            }
