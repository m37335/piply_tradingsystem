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
from typing import Dict, List, Optional, Any
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import PriceDataRepositoryImpl

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
            "4h": {"minutes": 240, "description": "4時間足"}
        }

        # 集計品質設定
        self.quality_thresholds = {
            "min_data_points": {"1h": 12, "4h": 48},  # 5分足の必要件数
            "max_gap_minutes": {"1h": 15, "4h": 30}   # 最大ギャップ（分）
        }

    async def aggregate_1h_data(self) -> List[PriceDataModel]:
        """
        5分足から1時間足データを集計

        Returns:
            List[PriceDataModel]: 集計された1時間足データ
        """
        try:
            logger.info("📊 1時間足集計開始")

            # 過去1時間の5分足データを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=1)

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

            logger.info(f"✅ 1時間足集計完了: {len(saved_data)}件")
            return saved_data

        except Exception as e:
            logger.error(f"1時間足集計エラー: {e}")
            return []

    async def aggregate_4h_data(self) -> List[PriceDataModel]:
        """
        5分足から4時間足データを集計

        Returns:
            List[PriceDataModel]: 集計された4時間足データ
        """
        try:
            logger.info("📊 4時間足集計開始")

            # 過去4時間の5分足データを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=4)

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

            logger.info(f"✅ 4時間足集計完了: {len(saved_data)}件")
            return saved_data

        except Exception as e:
            logger.error(f"4時間足集計エラー: {e}")
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

            total_aggregated = sum(results.values())
            logger.info(f"✅ 全時間軸集計完了: {total_aggregated}件")

            return results

        except Exception as e:
            logger.error(f"全時間軸集計エラー: {e}")
            return {"1h": 0, "4h": 0}

    def _convert_to_dataframe(self, price_data_list: List[PriceDataModel]) -> pd.DataFrame:
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
                data.append({
                    "timestamp": price_data.timestamp,
                    "open": float(price_data.open_price),
                    "high": float(price_data.high_price),
                    "low": float(price_data.low_price),
                    "close": float(price_data.close_price),
                    "volume": int(price_data.volume)
                })

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"DataFrame変換エラー: {e}")
            return pd.DataFrame()

    def _aggregate_timeframe_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
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
            resampled = df.resample(timeframe).agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            })

            # NaN値を削除
            resampled = resampled.dropna()

            return resampled

        except Exception as e:
            logger.error(f"時間軸集計エラー: {e}")
            return pd.DataFrame()

    async def _save_aggregated_data(
        self, 
        df: pd.DataFrame, 
        timeframe: str
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
                    data_source=f"Aggregated from 5m to {timeframe}"
                )

                # 重複チェック
                existing = await self.price_repo.find_by_timestamp(
                    timestamp, self.currency_pair
                )
                if not existing:
                    saved_data.append(await self.price_repo.save(price_data))

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
            status = {
                "last_aggregation": {},
                "total_aggregated": 0
            }

            # 各時間軸の最新集計状況を確認
            for timeframe in ["1h", "4h"]:
                # 最新の集計データを取得
                latest_data = await self.price_repo.find_latest(
                    self.currency_pair, 1
                )

                if latest_data:
                    status["last_aggregation"][timeframe] = {
                        "timestamp": latest_data[0].timestamp,
                        "data_source": latest_data[0].data_source
                    }

            # 総集計件数を計算
            total_count = await self.price_repo.count_by_date_range(
                datetime.now() - timedelta(days=7),
                datetime.now(),
                self.currency_pair
            )
            status["total_aggregated"] = total_count

            return status

        except Exception as e:
            logger.error(f"集計状態取得エラー: {e}")
            return {"error": str(e)}
