"""
時間軸自動集計サービス

責任:
- 5分足データから1時間足・4時間足への自動集計
- 集計データのデータベース保存
- 重複データの防止
- 集計品質の監視

特徴:
- リアルタイム集計処理
- 効率的なメモリ使用
- データ整合性保証
- 自動クリーンアップ
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)

logger = logging.getLogger(__name__)


class TimeframeAggregatorService:
    """
    時間軸自動集計サービス

    責任:
    - 5分足データから1時間足・4時間足への自動集計
    - 集計データのデータベース保存
    - 重複データの防止
    - 集計品質の監視
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.price_repo = PriceDataRepositoryImpl(session)
        self.currency_pair = "USD/JPY"

        # 集計設定
        self.aggregation_rules = {
            "1h": {"minutes": 60, "description": "1時間足"},
            "4h": {"minutes": 240, "description": "4時間足"},
            "1d": {"minutes": 1440, "description": "日足"},
        }

        # 集計品質設定
        self.quality_thresholds = {
            "min_data_points": {"1h": 12, "4h": 48, "1d": 288},  # 5分足の必要件数
            "max_gap_minutes": {"1h": 15, "4h": 30, "1d": 60},  # 最大ギャップ（分）
        }

    async def aggregate_1h_data(self) -> List[PriceDataModel]:
        """
        5分足から1時間足データを集計（進行中データも更新）

        Returns:
            List[PriceDataModel]: 集計された1時間足データ
        """
        try:
            logger.info("📊 1時間足集計開始")

            # 進行中の1時間足データを更新
            updated_data = await self._update_ongoing_1h_data()
            if updated_data:
                logger.info(f"✅ 進行中1時間足データ更新: {len(updated_data)}件")
                return updated_data

            # 完了した1時間足データを集計
            completed_data = await self._aggregate_completed_1h_data()
            logger.info(f"✅ 1時間足集計完了: {len(completed_data)}件")
            return completed_data

        except Exception as e:
            logger.error(f"1時間足集計エラー: {e}")
            return []

    async def aggregate_4h_data(self) -> List[PriceDataModel]:
        """
        5分足から4時間足データを集計（進行中データも更新）

        Returns:
            List[PriceDataModel]: 集計された4時間足データ
        """
        try:
            logger.info("📊 4時間足集計開始")

            # 進行中の4時間足データを更新
            updated_data = await self._update_ongoing_4h_data()
            if updated_data:
                logger.info(f"✅ 進行中4時間足データ更新: {len(updated_data)}件")
                return updated_data

            # 完了した4時間足データを集計
            completed_data = await self._aggregate_completed_4h_data()
            logger.info(f"✅ 4時間足集計完了: {len(completed_data)}件")
            return completed_data

        except Exception as e:
            logger.error(f"4時間足集計エラー: {e}")
            return []

    async def aggregate_1d_data(self) -> List[PriceDataModel]:
        """
        5分足から日足データを集計（進行中データも更新）

        Returns:
            List[PriceDataModel]: 集計された日足データ
        """
        try:
            logger.info("📊 日足集計開始")

            # 進行中の日足データを更新
            updated_data = await self._update_ongoing_1d_data()
            if updated_data:
                logger.info(f"✅ 進行中日足データ更新: {len(updated_data)}件")
                return updated_data

            # 完了した日足データを集計
            completed_data = await self._aggregate_completed_1d_data()
            logger.info(f"✅ 日足集計完了: {len(completed_data)}件")
            return completed_data

        except Exception as e:
            logger.error(f"日足集計エラー: {e}")
            return []

    async def _update_ongoing_1h_data(self) -> List[PriceDataModel]:
        """
        進行中の1時間足データを更新

        Returns:
            List[PriceDataModel]: 更新されたデータ
        """
        try:
            now = datetime.now()
            # 現在の1時間足の開始時刻を計算（例：16:45 → 16:00）
            current_hour_start = now.replace(minute=0, second=0, microsecond=0)

            # 進行中の1時間足データが存在するかチェック
            existing_data = await self.price_repo.find_by_timestamp_and_source(
                current_hour_start, self.currency_pair, "1h_aggregated_data"
            )

            if existing_data:
                # 既存データを更新
                return await self._update_existing_aggregated_data(
                    existing_data, "1h", current_hour_start, now
                )
            else:
                # 新規データを作成
                return await self._create_ongoing_aggregated_data(
                    "1h", current_hour_start, now
                )

        except Exception as e:
            logger.error(f"進行中1時間足データ更新エラー: {e}")
            return []

    async def _update_ongoing_4h_data(self) -> List[PriceDataModel]:
        """
        進行中の4時間足データを更新

        Returns:
            List[PriceDataModel]: 更新されたデータ
        """
        try:
            now = datetime.now()
            # 現在の4時間足の開始時刻を計算（例：16:45 → 12:00）
            current_4h_start = now.replace(
                hour=(now.hour // 4) * 4, minute=0, second=0, microsecond=0
            )

            # 進行中の4時間足データが存在するかチェック
            existing_data = await self.price_repo.find_by_timestamp_and_source(
                current_4h_start, self.currency_pair, "4h_aggregated_data"
            )

            if existing_data:
                # 既存データを更新
                return await self._update_existing_aggregated_data(
                    existing_data, "4h", current_4h_start, now
                )
            else:
                # 新規データを作成
                return await self._create_ongoing_aggregated_data(
                    "4h", current_4h_start, now
                )

        except Exception as e:
            logger.error(f"進行中4時間足データ更新エラー: {e}")
            return []

    async def _update_ongoing_1d_data(self) -> List[PriceDataModel]:
        """
        進行中の日足データを更新

        Returns:
            List[PriceDataModel]: 更新されたデータ
        """
        try:
            now = datetime.now()
            # 現在の日足の開始時刻を計算（例：16:45 → 00:00）
            current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # 進行中の日足データが存在するかチェック
            existing_data = await self.price_repo.find_by_timestamp_and_source(
                current_day_start, self.currency_pair, "1d_aggregated_data"
            )

            if existing_data:
                # 既存データを更新
                return await self._update_existing_aggregated_data(
                    existing_data, "1d", current_day_start, now
                )
            else:
                # 新規データを作成
                return await self._create_ongoing_aggregated_data(
                    "1d", current_day_start, now
                )

        except Exception as e:
            logger.error(f"進行中日足データ更新エラー: {e}")
            return []

    async def _update_existing_aggregated_data(
        self,
        existing_data: PriceDataModel,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[PriceDataModel]:
        """
        既存の集計データを更新

        Args:
            existing_data: 既存の集計データ
            timeframe: 時間軸（1h, 4h, 1d）
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            List[PriceDataModel]: 更新されたデータ
        """
        try:
            # 期間内の5分足データを取得
            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_time, end_time, self.currency_pair, "5m", 1000
            )

            if not m5_data:
                return []

            # 既存データの始値は固定、その他を更新
            df = self._convert_to_dataframe(m5_data)

            # OHLCVを計算
            open_price = existing_data.open_price  # 始値は固定
            high_price = max(existing_data.high_price, float(df["high"].max()))
            low_price = min(existing_data.low_price, float(df["low"].min()))
            close_price = float(df["close"].iloc[-1])  # 最新の終値
            volume = existing_data.volume + int(df["volume"].sum())

            # データを更新
            existing_data.high_price = high_price
            existing_data.low_price = low_price
            existing_data.close_price = close_price
            existing_data.volume = volume
            existing_data.data_timestamp = end_time

            # データベースに保存
            updated_data = await self.price_repo.save(existing_data)

            logger.info(
                f"🔄 {timeframe}進行中データ更新: "
                f"O={open_price}, H={high_price}, L={low_price}, C={close_price}"
            )

            return [updated_data]

        except Exception as e:
            logger.error(f"既存集計データ更新エラー: {e}")
            return []

    async def _create_ongoing_aggregated_data(
        self, timeframe: str, start_time: datetime, end_time: datetime
    ) -> List[PriceDataModel]:
        """
        進行中の集計データを新規作成

        Args:
            timeframe: 時間軸（1h, 4h, 1d）
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            List[PriceDataModel]: 作成されたデータ
        """
        try:
            # 期間内の5分足データを取得
            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_time, end_time, self.currency_pair, "5m", 1000
            )

            if not m5_data:
                return []

            # DataFrameに変換
            df = self._convert_to_dataframe(m5_data)

            # OHLCVを計算
            open_price = float(df["open"].iloc[0])  # 最初の始値
            high_price = float(df["high"].max())
            low_price = float(df["low"].min())
            close_price = float(df["close"].iloc[-1])  # 最新の終値
            volume = int(df["volume"].sum())

            # 新しい集計データを作成
            aggregated_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=start_time,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                data_source=f"Yahoo Finance {timeframe} Aggregated (Ongoing)",
                data_timestamp=end_time,
                fetched_at=datetime.now(),
            )

            # 既存データをチェック（データソースも含めて）
            existing_data = await self.price_repo.find_by_timestamp_and_source(
                start_time, self.currency_pair, f"{timeframe} Aggregated"
            )

            if existing_data:
                # 既存データを進行中データで更新
                existing_data.open_price = open_price
                existing_data.high_price = high_price
                existing_data.low_price = low_price
                existing_data.close_price = close_price
                existing_data.volume = volume
                existing_data.data_source = (
                    f"Yahoo Finance {timeframe} Aggregated (Ongoing)"
                )
                existing_data.data_timestamp = end_time
                existing_data.fetched_at = datetime.now()

                # 更新されたデータを保存
                saved_data = await self.price_repo.save(existing_data)
                logger.info(f"🔄 {timeframe}既存データを進行中データで更新")
            else:
                # 新規データとして保存
                saved_data = await self.price_repo.save(aggregated_data)
                logger.info(f"🆕 {timeframe}進行中データを新規作成")

            logger.info(
                f"✅ {timeframe}進行中データ作成: "
                f"O={open_price}, H={high_price}, L={low_price}, C={close_price}"
            )

            return [saved_data]

        except Exception as e:
            logger.error(f"進行中集計データ作成エラー: {e}")
            return []

    async def aggregate_all_timeframes(self) -> Dict[str, int]:
        """
        全時間軸の集計を実行

        Returns:
            Dict[str, int]: 各時間軸の集計件数
        """
        try:
            logger.info("🔄 全時間軸集計開始")

            results = {}

            # 1時間足集計
            h1_data = await self.aggregate_1h_data()
            results["1h"] = len(h1_data)

            # 4時間足集計
            h4_data = await self.aggregate_4h_data()
            results["4h"] = len(h4_data)

            # 日足集計
            d1_data = await self.aggregate_1d_data()
            results["1d"] = len(d1_data)

            total_aggregated = sum(results.values())
            logger.info(f"✅ 全時間軸集計完了: {total_aggregated}件")

            return results

        except Exception as e:
            logger.error(f"全時間軸集計エラー: {e}")
            return {"1h": 0, "4h": 0, "1d": 0}

    def _convert_to_dataframe(
        self, price_data_list: List[PriceDataModel]
    ) -> pd.DataFrame:
        """
        価格データリストをDataFrameに変換

        Args:
            price_data_list: 価格データリスト

        Returns:
            pd.DataFrame: 変換されたDataFrame
        """
        try:
            data = []
            for price_data in price_data_list:
                data.append(
                    {
                        "timestamp": price_data.timestamp,
                        "open": float(price_data.open_price),
                        "high": float(price_data.high_price),
                        "low": float(price_data.low_price),
                        "close": float(price_data.close_price),
                        "volume": int(price_data.volume),
                    }
                )

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"DataFrame変換エラー: {e}")
            return pd.DataFrame()

    def _aggregate_timeframe_data(
        self, df: pd.DataFrame, timeframe: str
    ) -> pd.DataFrame:
        """
        指定時間軸にデータを集計

        Args:
            df: 5分足データのDataFrame
            timeframe: 集計時間軸（1H, 4H）

        Returns:
            pd.DataFrame: 集計されたデータ
        """
        try:
            if df.empty:
                return df

            # 時間軸でリサンプリング
            resampled = df.resample(timeframe).agg(
                {
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last",
                    "volume": "sum",
                }
            )

            # NaN値を削除
            resampled = resampled.dropna()

            return resampled

        except Exception as e:
            logger.error(f"時間軸集計エラー: {e}")
            return pd.DataFrame()

    async def _save_aggregated_data(
        self, df: pd.DataFrame, timeframe: str
    ) -> List[PriceDataModel]:
        """
        集計データをデータベースに保存

        Args:
            df: 集計されたDataFrame
            timeframe: 時間軸（1h, 4h）

        Returns:
            List[PriceDataModel]: 保存されたデータ
        """
        try:
            saved_data = []

            for timestamp, row in df.iterrows():
                price_data = PriceDataModel(
                    currency_pair=self.currency_pair,
                    timestamp=timestamp,
                    open_price=float(row["open"]),
                    high_price=float(row["high"]),
                    low_price=float(row["low"]),
                    close_price=float(row["close"]),
                    volume=int(row["volume"]),
                    data_source=f"Yahoo Finance {timeframe} Aggregated",
                )

                # 重複チェック（タイムスタンプと通貨ペアで）
                existing = await self.price_repo.find_by_timestamp(
                    timestamp, self.currency_pair
                )

                if not existing:
                    saved_data.append(await self.price_repo.save(price_data))
                    logger.info(f"✅ {timeframe}集計データ保存: {timestamp}")
                else:
                    logger.info(f"⏭️ {timeframe}集計データ既存: {timestamp}")

            return saved_data

        except Exception as e:
            logger.error(f"集計データ保存エラー: {e}")
            return []

    async def get_aggregation_status(self) -> Dict[str, Any]:
        """
        集計状態を取得

        Returns:
            Dict[str, Any]: 集計状態
        """
        try:
            status = {"last_aggregation": {}, "total_aggregated": 0}

            # 各時間軸の最新集計状況を確認
            for timeframe in ["1h", "4h"]:
                # 最新の集計データを取得
                latest_data = await self.price_repo.find_latest(self.currency_pair, 1)

                if latest_data:
                    status["last_aggregation"][timeframe] = {
                        "timestamp": latest_data[0].timestamp,
                        "data_source": latest_data[0].data_source,
                    }

            # 総集計件数を計算
            total_count = await self.price_repo.count_by_date_range(
                datetime.now() - timedelta(days=7), datetime.now(), self.currency_pair
            )
            status["total_aggregated"] = total_count

            return status

        except Exception as e:
            logger.error(f"集計状態取得エラー: {e}")
            return {"error": str(e)}

    async def _aggregate_completed_1h_data(self) -> List[PriceDataModel]:
        """
        完了した1時間足データを集計

        Returns:
            List[PriceDataModel]: 集計されたデータ
        """
        try:
            now = datetime.now()
            # 完了した1時間足の開始時刻を計算（例：16:45 → 15:00）
            completed_hour_start = now.replace(
                minute=0, second=0, microsecond=0
            ) - timedelta(hours=1)

            # 過去1時間の5分足データを取得
            end_date = completed_hour_start + timedelta(hours=1)
            start_date = completed_hour_start

            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date, end_date, self.currency_pair, "5m", 1000
            )

            if len(m5_data) < self.quality_thresholds["min_data_points"]["1h"]:
                logger.warning(
                    f"1時間足集計に必要な5分足データが不足: {len(m5_data)}/"
                    f"{self.quality_thresholds['min_data_points']['1h']}"
                )
                return []

            # DataFrameに変換
            df = self._convert_to_dataframe(m5_data)

            # 1時間足に集計
            h1_df = self._aggregate_timeframe_data(df, "1H")

            # データベースに保存
            saved_data = await self._save_aggregated_data(h1_df, "1h")

            return saved_data

        except Exception as e:
            logger.error(f"完了1時間足集計エラー: {e}")
            return []

    async def _aggregate_completed_4h_data(self) -> List[PriceDataModel]:
        """
        完了した4時間足データを集計

        Returns:
            List[PriceDataModel]: 集計されたデータ
        """
        try:
            now = datetime.now()
            # 完了した4時間足の開始時刻を計算（例：16:45 → 8:00）
            current_4h_start = now.replace(
                hour=(now.hour // 4) * 4, minute=0, second=0, microsecond=0
            )
            completed_4h_start = current_4h_start - timedelta(hours=4)

            # 過去4時間の5分足データを取得
            end_date = completed_4h_start + timedelta(hours=4)
            start_date = completed_4h_start

            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date, end_date, self.currency_pair, "5m", 1000
            )

            if len(m5_data) < self.quality_thresholds["min_data_points"]["4h"]:
                logger.warning(
                    f"4時間足集計に必要な5分足データが不足: {len(m5_data)}/"
                    f"{self.quality_thresholds['min_data_points']['4h']}"
                )
                return []

            # DataFrameに変換
            df = self._convert_to_dataframe(m5_data)

            # 4時間足に集計
            h4_df = self._aggregate_timeframe_data(df, "4H")

            # データベースに保存
            saved_data = await self._save_aggregated_data(h4_df, "4h")

            return saved_data

        except Exception as e:
            logger.error(f"完了4時間足集計エラー: {e}")
            return []

    async def _aggregate_completed_1d_data(self) -> List[PriceDataModel]:
        """
        完了した日足データを集計

        Returns:
            List[PriceDataModel]: 集計されたデータ
        """
        try:
            now = datetime.now()
            # 完了した日足の開始時刻を計算（例：16:45 → 前日00:00）
            completed_day_start = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=1)

            # 過去24時間の5分足データを取得
            end_date = completed_day_start + timedelta(days=1)
            start_date = completed_day_start

            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date, end_date, self.currency_pair, "5m", 1000
            )

            if len(m5_data) < self.quality_thresholds["min_data_points"]["1d"]:
                logger.warning(
                    f"日足集計に必要な5分足データが不足: {len(m5_data)}/"
                    f"{self.quality_thresholds['min_data_points']['1d']}"
                )
                return []

            # DataFrameに変換
            df = self._convert_to_dataframe(m5_data)

            # 日足に集計
            d1_df = self._aggregate_timeframe_data(df, "1D")

            # データベースに保存
            saved_data = await self._save_aggregated_data(d1_df, "1d")

            return saved_data

        except Exception as e:
            logger.error(f"完了日足集計エラー: {e}")
            return []
