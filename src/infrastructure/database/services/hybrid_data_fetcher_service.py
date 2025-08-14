#!/usr/bin/env python3
"""
ハイブリッドデータ取得サービス
各時間足を直接取得 + 不足分を集計で補完
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from ....utils.logging_config import get_infrastructure_logger
from ...database.models.price_data_model import PriceDataModel
from ...database.repositories.price_data_repository_impl import PriceDataRepositoryImpl
from ...database.services.timeframe_aggregator_service import TimeframeAggregatorService
from ...external_apis.yahoo_finance_client import YahooFinanceClient

logger = get_infrastructure_logger()


class HybridDataFetcherService:
    """
    ハイブリッドデータ取得サービス

    責任:
    - 各時間足の直接取得
    - 不足分の集計補完
    - データの統合と保存
    """

    def __init__(self, session: AsyncSession, currency_pair: str = "USD/JPY"):
        self.session = session
        self.currency_pair = currency_pair
        self.yahoo_client = YahooFinanceClient()
        self.price_repo = PriceDataRepositoryImpl(session)
        self.aggregator = TimeframeAggregatorService(session)

        # 時間足設定
        self.timeframes = {
            "5m": {"period": "7d", "interval": "5m", "description": "5分足"},
            "1h": {"period": "30d", "interval": "1h", "description": "1時間足"},
            "4h": {"period": "60d", "interval": "4h", "description": "4時間足"},
            "1d": {"period": "365d", "interval": "1d", "description": "日足"},
        }

        # 集計補完設定
        self.aggregation_fill_config = {
            "1h": {
                "from_5m": True,
                "min_data_points": 12,
            },  # 1時間足は5分足から12件必要
            "4h": {
                "from_5m": True,
                "min_data_points": 48,
            },  # 4時間足は5分足から48件必要
            "1d": {"from_5m": True, "min_data_points": 288},  # 日足は5分足から288件必要
        }

        logger.info(f"Initialized HybridDataFetcherService for {currency_pair}")

    async def fetch_all_timeframes_hybrid(self) -> Dict[str, int]:
        """
        全時間足をハイブリッド方式で取得

        Returns:
            Dict[str, int]: 各時間足の取得件数
        """
        results = {}

        try:
            logger.info("🚀 ハイブリッド方式で全時間足データ取得開始")

            # 1. 5分足を最初に取得（他の時間足の集計元として使用）
            logger.info("📊 5分足データ取得中...")
            m5_count = await self._fetch_direct_timeframe("5m")
            results["5m"] = m5_count

            # 2. 各時間足を並行で直接取得
            tasks = []
            for timeframe in ["1h", "4h", "1d"]:
                task = self._fetch_timeframe_hybrid(timeframe)
                tasks.append(task)

            # 並行実行
            timeframe_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 結果を統合
            for i, timeframe in enumerate(["1h", "4h", "1d"]):
                if isinstance(timeframe_results[i], Exception):
                    logger.error(f"❌ {timeframe}取得エラー: {timeframe_results[i]}")
                    results[timeframe] = 0
                else:
                    results[timeframe] = timeframe_results[i]

            logger.info(f"✅ ハイブリッド取得完了: {results}")
            return results

        except Exception as e:
            logger.error(f"❌ ハイブリッド取得エラー: {e}")
            return results

    async def _fetch_timeframe_hybrid(self, timeframe: str) -> int:
        """
        特定時間足をハイブリッド方式で取得

        Args:
            timeframe: 時間足 (1h, 4h, 1d)

        Returns:
            int: 取得件数
        """
        try:
            logger.info(f"🔄 {timeframe}時間足ハイブリッド取得開始")

            # 1. 直接取得を試行
            direct_count = await self._fetch_direct_timeframe(timeframe)
            logger.info(f"   📥 直接取得: {direct_count}件")

            # 2. 集計補完を実行
            aggregated_count = await self._fill_with_aggregation(timeframe)
            logger.info(f"   🔧 集計補完: {aggregated_count}件")

            total_count = direct_count + aggregated_count
            logger.info(f"   ✅ {timeframe}合計: {total_count}件")

            return total_count

        except Exception as e:
            logger.error(f"❌ {timeframe}ハイブリッド取得エラー: {e}")
            return 0

    async def _fetch_direct_timeframe(self, timeframe: str) -> int:
        """
        時間足を直接取得

        Args:
            timeframe: 時間足

        Returns:
            int: 取得件数
        """
        try:
            config = self.timeframes[timeframe]

            # Yahoo Financeから直接取得
            data = await self.yahoo_client.get_historical_data(
                self.currency_pair, period=config["period"], interval=config["interval"]
            )

            if data is None or data.empty:
                logger.warning(f"⚠️ {timeframe}直接取得データなし")
                return 0

            # データを保存
            saved_count = 0
            for _, row in data.iterrows():
                price_data = self._create_price_data_model(row, timeframe, "direct")

                # 重複チェック（タイムスタンプのみ）
                existing = await self.price_repo.find_by_timestamp_and_source(
                    price_data.timestamp, self.currency_pair, price_data.data_source
                )

                if existing:
                    # 既存データがある場合は削除して新しいデータを保存
                    await self.price_repo.delete(existing.id)
                    logger.info(f"🔄 既存データを更新: {price_data.timestamp}")

                await self.price_repo.save(price_data)
                saved_count += 1

            logger.info(f"✅ {timeframe}直接取得完了: {saved_count}件保存")
            return saved_count

        except Exception as e:
            logger.error(f"❌ {timeframe}直接取得エラー: {e}")
            return 0

    async def _fill_with_aggregation(self, timeframe: str) -> int:
        """
        集計で不足分を補完

        Args:
            timeframe: 時間足

        Returns:
            int: 補完件数
        """
        try:
            config = self.aggregation_fill_config.get(timeframe)
            if not config:
                logger.warning(f"⚠️ {timeframe}集計補完設定なし")
                return 0

            # 5分足データを取得
            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                datetime.now() - timedelta(days=7),
                datetime.now(),
                self.currency_pair,
                "5m",
                1000,
            )

            if len(m5_data) < config["min_data_points"]:
                logger.warning(f"⚠️ {timeframe}集計用5分足データ不足: {len(m5_data)}件")
                return 0

            # 集計実行（引数なしで呼び出し）
            if timeframe == "1h":
                aggregated_data = await self.aggregator.aggregate_1h_data()
            elif timeframe == "4h":
                aggregated_data = await self.aggregator.aggregate_4h_data()
            elif timeframe == "1d":
                aggregated_data = await self.aggregator.aggregate_1d_data()
            else:
                logger.warning(f"⚠️ 未対応時間足: {timeframe}")
                return 0

            if aggregated_data:
                # 集計データを保存
                saved_count = 0
                for data in aggregated_data:
                    # 重複チェック
                    existing = await self.price_repo.find_by_timestamp_and_source(
                        data.timestamp, self.currency_pair, data.data_source
                    )

                    if existing:
                        # 既存データがある場合は削除して新しいデータを保存
                        await self.price_repo.delete(existing.id)
                        logger.info(f"🔄 集計データを更新: {data.timestamp}")

                    await self.price_repo.save(data)
                    saved_count += 1

                logger.info(f"✅ {timeframe}集計補完完了: {saved_count}件保存")
                return saved_count

            return 0

        except Exception as e:
            logger.error(f"❌ {timeframe}集計補完エラー: {e}")
            return 0

    def _create_price_data_model(
        self, row: pd.Series, timeframe: str, source_type: str
    ) -> PriceDataModel:
        """
        価格データモデルを作成

         Args:
             row: DataFrame行
             timeframe: 時間足
             source_type: データソース種別

         Returns:
             PriceDataModel: 価格データモデル
        """
        return PriceDataModel(
            currency_pair=self.currency_pair,
            timestamp=row.name,
            open_price=row["Open"],
            high_price=row["High"],
            low_price=row["Low"],
            close_price=row["Close"],
            volume=row.get("Volume", 1000000),
            data_source=f"Yahoo Finance ({timeframe.upper()}) {source_type.title()}",
            data_timestamp=row.name,
            fetched_at=datetime.now(),
        )

    async def get_data_summary(self) -> Dict[str, Dict]:
        """
        各時間足のデータ状況を取得

        Returns:
            Dict[str, Dict]: データ状況サマリー
        """
        summary = {}

        for timeframe in ["5m", "1h", "4h", "1d"]:
            try:
                # 最新データを取得
                latest_data = await self.price_repo.find_by_date_range_and_timeframe(
                    datetime.now() - timedelta(days=1),
                    datetime.now(),
                    self.currency_pair,
                    timeframe,
                    1,
                )

                if latest_data:
                    latest = latest_data[0]
                    summary[timeframe] = {
                        "latest_timestamp": latest.timestamp,
                        "latest_price": latest.close_price,
                        "data_source": latest.data_source,
                        "count_today": len(latest_data),
                    }
                else:
                    summary[timeframe] = {
                        "latest_timestamp": None,
                        "latest_price": None,
                        "data_source": None,
                        "count_today": 0,
                    }

            except Exception as e:
                logger.error(f"❌ {timeframe}サマリー取得エラー: {e}")
                summary[timeframe] = {"error": str(e)}

        return summary
