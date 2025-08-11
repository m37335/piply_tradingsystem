"""
初回データ取得サービス

責任:
- 全時間軸（5分足、1時間足、4時間足、日足）の履歴データ一括取得
- 初回テクニカル指標計算
- 初回パターン検出実行
- システム初期化の完了確認

特徴:
- API制限を考慮した段階的データ取得
- 重複データの防止
- 包括的エラーハンドリング
- 初期化進捗の監視
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.services.efficient_pattern_detection_service import (
    EfficientPatternDetectionService,
)
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.services.multi_timeframe_technical_indicator_service import (
    MultiTimeframeTechnicalIndicatorService,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class InitialDataLoaderService:
    """
    初回データ取得サービス

    責任:
    - 全時間軸（5分足、1時間足、4時間足、日足）の履歴データ一括取得
    - 初回テクニカル指標計算
    - 初回パターン検出実行
    - システム初期化の完了確認
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.yahoo_client = YahooFinanceClient()
        self.price_repo = PriceDataRepositoryImpl(session)
        self.indicator_service = MultiTimeframeTechnicalIndicatorService(session)
        self.pattern_service = EfficientPatternDetectionService(session)

        # 初回取得設定（期間延長）
        self.initial_load_config = {
            "5m": {"period": "30d", "interval": "5m", "description": "5分足"},      # 7d → 30d
            "1h": {"period": "90d", "interval": "1h", "description": "1時間足"},   # 30d → 90d
            "4h": {"period": "180d", "interval": "4h", "description": "4時間足"},  # 60d → 180d
            "1d": {"period": "730d", "interval": "1d", "description": "日足"},     # 365d → 730d（2年分）
        }

        self.currency_pair = "USD/JPY"
        self.max_retries = 3
        self.retry_delay = 5  # 秒

    async def load_all_initial_data(self) -> Dict[str, Any]:
        """
        全時間軸の初回データを取得

        Returns:
            Dict[str, Any]: 各時間軸の取得結果
        """
        start_time = datetime.now()
        results = {
            "data_counts": {},
            "indicator_counts": {},
            "pattern_counts": {},
            "processing_time": 0,
            "is_initialized": False,
        }

        try:
            logger.info("=== 初回データ取得開始 ===")

            # 1. 各時間軸のデータを順次取得（API制限対応）
            for timeframe, config in self.initial_load_config.items():
                logger.info(f"📊 {config['description']}データ取得中...")

                data_count = await self.load_timeframe_data(timeframe)
                results["data_counts"][timeframe] = data_count

                logger.info(f"✅ {config['description']}完了: {data_count}件")

                # API制限を考慮した待機
                if timeframe != "1d":  # 最後の時間軸以外で待機
                    await asyncio.sleep(self.retry_delay)

            # 2. 初回テクニカル指標計算
            logger.info("📈 初回テクニカル指標計算中...")
            indicator_results = await self.calculate_initial_indicators()
            results["indicator_counts"] = indicator_results

            # 3. 初回パターン検出
            logger.info("🔍 初回パターン検出中...")
            pattern_results = await self.detect_initial_patterns()
            results["pattern_counts"] = pattern_results

            # 4. 初期化完了確認
            is_initialized = await self.verify_initialization()

            results["processing_time"] = (datetime.now() - start_time).total_seconds()
            results["is_initialized"] = is_initialized

            logger.info("🎉 初回データ取得完了")
            return results

        except Exception as e:
            logger.error(f"初回データ取得エラー: {e}")
            raise

    async def load_timeframe_data(self, timeframe: str) -> int:
        """
        特定時間軸の初回データを取得

        Args:
            timeframe: 時間軸（5m, 1h, 4h, 1d）

        Returns:
            int: 取得したデータ件数
        """
        try:
            config = self.initial_load_config[timeframe]

            # 既存データチェック（期間延長に対応）
            # 各時間軸の期間に応じてチェック期間を調整
            if timeframe == "5m":
                check_days = 30  # 30日分
            elif timeframe == "1h":
                check_days = 90  # 90日分
            elif timeframe == "4h":
                check_days = 180  # 180日分
            elif timeframe == "1d":
                check_days = 730  # 730日分（2年分）
            else:
                check_days = 30

            existing_count = await self.price_repo.count_by_date_range(
                datetime.now() - timedelta(days=check_days), datetime.now(), self.currency_pair
            )

            # 期間に応じた閾値設定
            threshold = check_days * 10  # 1日あたり10件を基準

            if existing_count > threshold:  # 期間に応じた閾値でチェック
                logger.info(
                    f"  ⚠️ {config['description']}データは既に存在: {existing_count}件（閾値: {threshold}件）"
                )
                return existing_count

            # Yahoo Financeから履歴データ取得
            hist_data = await self.yahoo_client.get_historical_data(
                self.currency_pair, config["period"], config["interval"]
            )

            if hist_data is None or hist_data.empty:
                logger.warning(f"  ❌ {config['description']}データ取得失敗")
                return 0

            # データベースに保存
            saved_count = 0
            for timestamp, row in hist_data.iterrows():
                price_data = PriceDataModel(
                    currency_pair=self.currency_pair,
                    timestamp=timestamp,
                    open_price=float(row["Open"]),
                    high_price=float(row["High"]),
                    low_price=float(row["Low"]),
                    close_price=float(row["Close"]),
                    volume=int(row["Volume"]) if "Volume" in row else 1000000,
                    data_source="Yahoo Finance Initial Load",
                )

                # 重複チェック
                existing = await self.price_repo.find_by_timestamp(
                    timestamp, self.currency_pair
                )
                if not existing:
                    await self.price_repo.save(price_data)
                    saved_count += 1

            logger.info(f"  ✅ {config['description']}保存完了: {saved_count}件")
            return saved_count

        except Exception as e:
            logger.error(f"  ❌ {timeframe}データ取得エラー: {e}")
            return 0

    async def calculate_initial_indicators(self) -> Dict[str, int]:
        """
        初回テクニカル指標を計算

        Returns:
            Dict[str, int]: 各時間軸の指標計算件数
        """
        try:
            logger.info("📈 初回テクニカル指標計算開始")

            # 各時間軸でテクニカル指標を計算
            timeframes = ["5m", "1h", "4h", "1d"]
            indicator_counts = {}

            for timeframe in timeframes:
                logger.info(f"  📊 {timeframe}時間軸の指標計算中...")

                # 指標を計算
                indicators = await self.indicator_service.calculate_timeframe_indicators(
                    timeframe
                )
                
                # データベースに保存
                if indicators:
                    saved = await self.indicator_service.save_timeframe_indicators(
                        timeframe, indicators
                    )
                    if saved:
                        indicator_counts[timeframe] = len(indicators)
                        logger.info(f"  ✅ {timeframe}指標計算完了: {len(indicators)}件")
                    else:
                        logger.warning(f"  ⚠️ {timeframe}指標保存失敗")
                else:
                    indicator_counts[timeframe] = 0
                    logger.warning(f"  ⚠️ {timeframe}指標計算結果が空")

            logger.info("📈 初回テクニカル指標計算完了")
            return indicator_counts

        except Exception as e:
            logger.error(f"初回テクニカル指標計算エラー: {e}")
            return {}

    async def detect_initial_patterns(self) -> Dict[str, int]:
        """
        初回パターン検出を実行

        Returns:
            Dict[str, int]: 検出されたパターン数
        """
        try:
            logger.info("🔍 初回パターン検出開始")

            # 各時間軸でパターン検出を実行
            timeframes = ["5m", "1h", "4h", "1d"]
            pattern_counts = {}

            for timeframe in timeframes:
                logger.info(f"  🔍 {timeframe}時間軸のパターン検出中...")

                count = await self.pattern_service.detect_all_patterns_for_timeframe(
                    timeframe
                )
                pattern_counts[timeframe] = count

                logger.info(f"  ✅ {timeframe}パターン検出完了: {count}件")

            logger.info("🔍 初回パターン検出完了")
            return pattern_counts

        except Exception as e:
            logger.error(f"初回パターン検出エラー: {e}")
            return {}

    async def verify_initialization(self) -> bool:
        """
        初期化の完了を確認

        Returns:
            bool: 初期化完了フラグ
        """
        try:
            logger.info("🔍 初期化完了確認中...")

            # 各時間軸のデータ存在確認
            timeframes = ["5m", "1h", "4h", "1d"]
            min_data_counts = {"5m": 100, "1h": 50, "4h": 30, "1d": 30}

            for timeframe in timeframes:
                data_count = await self.price_repo.count_by_date_range(
                    datetime.now() - timedelta(days=7),
                    datetime.now(),
                    self.currency_pair,
                )

                if data_count < min_data_counts[timeframe]:
                    logger.warning(
                        f"初期化未完了: {timeframe}データ不足 ({data_count}/{min_data_counts[timeframe]})"
                    )
                    return False

            # テクニカル指標の存在確認
            indicator_count = await self.indicator_service.count_latest_indicators()
            if indicator_count < 50:
                logger.warning(
                    f"初期化未完了: テクニカル指標不足 ({indicator_count}/50)"
                )
                return False

            logger.info("✅ 初期化完了確認済み")
            return True

        except Exception as e:
            logger.error(f"初期化完了確認エラー: {e}")
            return False

    async def get_initialization_status(self) -> Dict[str, Any]:
        """
        初期化状態の詳細情報を取得

        Returns:
            Dict[str, Any]: 初期化状態の詳細
        """
        try:
            status = {
                "is_initialized": False,
                "data_counts": {},
                "indicator_counts": {},
                "pattern_counts": {},
                "missing_components": [],
            }

            # 各時間軸のデータ件数を確認
            timeframes = ["5m", "1h", "4h", "1d"]
            min_data_counts = {"5m": 100, "1h": 50, "4h": 30, "1d": 30}

            for timeframe in timeframes:
                data_count = await self.price_repo.count_by_date_range(
                    datetime.now() - timedelta(days=7),
                    datetime.now(),
                    self.currency_pair,
                )
                status["data_counts"][timeframe] = data_count

                if data_count < min_data_counts[timeframe]:
                    status["missing_components"].append(f"{timeframe}データ不足")

            # テクニカル指標件数を確認
            indicator_count = await self.indicator_service.count_latest_indicators()
            status["indicator_counts"]["total"] = indicator_count

            if indicator_count < 50:
                status["missing_components"].append("テクニカル指標不足")

            # パターン検出件数を確認
            pattern_count = await self.pattern_service.count_latest_patterns()
            status["pattern_counts"]["total"] = pattern_count

            # 初期化完了判定
            status["is_initialized"] = len(status["missing_components"]) == 0

            return status

        except Exception as e:
            logger.error(f"初期化状態取得エラー: {e}")
            return {"is_initialized": False, "error": str(e)}
