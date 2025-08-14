#!/usr/bin/env python3
"""
純粋な集計スクリプト
既存の5分足データから1時間足・4時間足データを集計して欠損部分を埋める
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PureAggregationInitializer:
    """
    純粋な集計初期化クラス

    責任:
    - データベース内の5分足データを確認
    - 1時間足・4時間足の欠損部分を特定
    - 5分足データから集計して欠損部分を埋める
    """

    def __init__(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///data/exchange_analytics.db", echo=False
        )
        self.currency_pair = "USD/JPY"
        self.price_repo = None

    async def initialize_aggregation(self) -> bool:
        """
        純粋な集計方式で初期化を実行

        Returns:
            bool: 成功/失敗
        """
        try:
            logger.info("🚀 純粋な集計初期化開始")

            async with AsyncSession(self.engine) as session:
                self.price_repo = PriceDataRepositoryImpl(session)

                # 1. データベース内のデータ状況を確認
                logger.info("📊 データベース内のデータ状況を確認中...")
                data_status = await self._check_data_status()

                for timeframe, status in data_status.items():
                    logger.info(
                        f"   {timeframe}: {status['latest']} - {status['count']}件"
                    )

                # 2. 5分足データから1時間足データを集計
                logger.info("🔄 5分足から1時間足データを集計中...")
                h1_count = await self._aggregate_1h_from_5m()
                logger.info(f"   ✅ 1時間足集計完了: {h1_count}件")

                # 3. 5分足データから4時間足データを集計
                logger.info("🔄 5分足から4時間足データを集計中...")
                h4_count = await self._aggregate_4h_from_5m()
                logger.info(f"   ✅ 4時間足集計完了: {h4_count}件")

                # 4. 最終データ状況を確認
                logger.info("📋 最終データ状況:")
                final_status = await self._check_data_status()

                for timeframe, status in final_status.items():
                    logger.info(
                        f"   {timeframe}: {status['latest']} - {status['count']}件"
                    )

                # 5. 最終サマリー
                logger.info("🎉 純粋な集計初期化完了")
                logger.info("=" * 50)
                logger.info("📊 最終結果:")
                logger.info(f"   5分足: {final_status['5m']['count']}件")
                logger.info(
                    f"   1時間足: {final_status['1h']['count']}件 (+{h1_count}件)"
                )
                logger.info(
                    f"   4時間足: {final_status['4h']['count']}件 (+{h4_count}件)"
                )

                return True

        except Exception as e:
            logger.error(f"❌ 集計初期化エラー: {e}")
            return False

    async def _check_data_status(self) -> dict:
        """
        各時間足のデータ状況を確認

        Returns:
            dict: データ状況
        """
        status = {}

        for timeframe in ["5m", "1h", "4h"]:
            try:
                # 最新データを取得
                latest_data = await self.price_repo.find_by_date_range_and_timeframe(
                    datetime.now() - timedelta(days=30),
                    datetime.now(),
                    self.currency_pair,
                    timeframe,
                    1,
                )

                if latest_data:
                    latest = latest_data[0]
                    status[timeframe] = {
                        "latest": latest.timestamp,
                        "count": len(
                            await self.price_repo.find_by_date_range_and_timeframe(
                                datetime.now() - timedelta(days=30),
                                datetime.now(),
                                self.currency_pair,
                                timeframe,
                                1000,
                            )
                        ),
                    }
                else:
                    status[timeframe] = {"latest": None, "count": 0}

            except Exception as e:
                logger.error(f"❌ {timeframe}データ状況確認エラー: {e}")
                status[timeframe] = {"latest": None, "count": 0}

        return status

    async def _aggregate_1h_from_5m(self) -> int:
        """
        5分足データから1時間足データを集計

        Returns:
            int: 集計件数
        """
        try:
            # 最新の5分足データの日時を取得
            latest_5m = await self.price_repo.find_by_date_range_and_timeframe(
                datetime.now() - timedelta(days=30),
                datetime.now(),
                self.currency_pair,
                "5m",
                1,
            )

            if not latest_5m:
                logger.warning("⚠️ 5分足データが見つかりません")
                return 0

            latest_timestamp = latest_5m[0].timestamp
            start_date = latest_timestamp - timedelta(days=7)  # 7日分のデータを使用

            # 5分足データを取得
            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date,
                latest_timestamp,
                self.currency_pair,
                "5m",
                10000,
            )

            if len(m5_data) < 12:  # 1時間足には最低12件の5分足が必要
                logger.warning(f"⚠️ 5分足データ不足: {len(m5_data)}件")
                return 0

            # 1時間足に集計
            aggregated_count = 0
            current_hour = None
            hour_data = []

            logger.info(f"   5分足データ件数: {len(m5_data)}件")
            logger.info(f"   期間: {m5_data[0].timestamp} ～ {m5_data[-1].timestamp}")

            for data in sorted(m5_data, key=lambda x: x.timestamp):
                data_hour = data.timestamp.replace(minute=0, second=0, microsecond=0)

                if current_hour is None:
                    current_hour = data_hour
                    hour_data = [data]
                elif data_hour == current_hour:
                    hour_data.append(data)
                else:
                    # 1時間足データを作成
                    if len(hour_data) >= 12:  # 最低12件の5分足が必要
                        logger.info(
                            f"   1時間足作成: {current_hour} ({len(hour_data)}件の5分足)"
                        )
                        h1_data = await self._create_1h_data(hour_data, current_hour)
                        if h1_data:
                            await self.price_repo.save(h1_data)
                            aggregated_count += 1
                            logger.info(f"   ✅ 1時間足保存: {current_hour}")

                    # 新しい時間の開始
                    current_hour = data_hour
                    hour_data = [data]

            # 最後の時間足も処理
            if len(hour_data) >= 12:
                logger.info(
                    f"   最後の1時間足作成: {current_hour} ({len(hour_data)}件の5分足)"
                )
                h1_data = await self._create_1h_data(hour_data, current_hour)
                if h1_data:
                    await self.price_repo.save(h1_data)
                    aggregated_count += 1
                    logger.info(f"   ✅ 最後の1時間足保存: {current_hour}")

            return aggregated_count

        except Exception as e:
            logger.error(f"❌ 1時間足集計エラー: {e}")
            return 0

    async def _aggregate_4h_from_5m(self) -> int:
        """
        5分足データから4時間足データを集計

        Returns:
            int: 集計件数
        """
        try:
            # 最新の5分足データの日時を取得
            latest_5m = await self.price_repo.find_by_date_range_and_timeframe(
                datetime.now() - timedelta(days=30),
                datetime.now(),
                self.currency_pair,
                "5m",
                1,
            )

            if not latest_5m:
                logger.warning("⚠️ 5分足データが見つかりません")
                return 0

            latest_timestamp = latest_5m[0].timestamp
            start_date = latest_timestamp - timedelta(days=30)  # 30日分のデータを使用

            # 5分足データを取得
            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date,
                latest_timestamp,
                self.currency_pair,
                "5m",
                10000,
            )

            if len(m5_data) < 48:  # 4時間足には最低48件の5分足が必要
                logger.warning(f"⚠️ 5分足データ不足: {len(m5_data)}件")
                return 0

            # 4時間足に集計
            aggregated_count = 0
            current_4h = None
            four_hour_data = []

            logger.info(f"   5分足データ件数: {len(m5_data)}件")
            logger.info(f"   期間: {m5_data[0].timestamp} ～ {m5_data[-1].timestamp}")

            for data in sorted(m5_data, key=lambda x: x.timestamp):
                # 4時間の境界を計算（0:00, 4:00, 8:00, 12:00, 16:00, 20:00）
                hour = data.timestamp.hour
                if hour < 4:
                    data_4h = data.timestamp.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                elif hour < 8:
                    data_4h = data.timestamp.replace(
                        hour=4, minute=0, second=0, microsecond=0
                    )
                elif hour < 12:
                    data_4h = data.timestamp.replace(
                        hour=8, minute=0, second=0, microsecond=0
                    )
                elif hour < 16:
                    data_4h = data.timestamp.replace(
                        hour=12, minute=0, second=0, microsecond=0
                    )
                elif hour < 20:
                    data_4h = data.timestamp.replace(
                        hour=16, minute=0, second=0, microsecond=0
                    )
                else:
                    data_4h = data.timestamp.replace(
                        hour=20, minute=0, second=0, microsecond=0
                    )

                if current_4h is None:
                    current_4h = data_4h
                    four_hour_data = [data]
                elif data_4h == current_4h:
                    four_hour_data.append(data)
                else:
                    # 4時間足データを作成
                    if len(four_hour_data) >= 48:  # 最低48件の5分足が必要
                        logger.info(
                            f"   4時間足作成: {current_4h} ({len(four_hour_data)}件の5分足)"
                        )
                        h4_data = await self._create_4h_data(four_hour_data, current_4h)
                        if h4_data:
                            await self.price_repo.save(h4_data)
                            aggregated_count += 1
                            logger.info(f"   ✅ 4時間足保存: {current_4h}")

                    # 新しい4時間の開始
                    current_4h = data_4h
                    four_hour_data = [data]

            # 最後の4時間足も処理
            if len(four_hour_data) >= 48:
                logger.info(
                    f"   最後の4時間足作成: {current_4h} ({len(four_hour_data)}件の5分足)"
                )
                h4_data = await self._create_4h_data(four_hour_data, current_4h)
                if h4_data:
                    await self.price_repo.save(h4_data)
                    aggregated_count += 1
                    logger.info(f"   ✅ 最後の4時間足保存: {current_4h}")

            return aggregated_count

        except Exception as e:
            logger.error(f"❌ 4時間足集計エラー: {e}")
            return 0

    async def _create_1h_data(
        self, hour_data: list, timestamp: datetime
    ) -> PriceDataModel:
        """
        1時間足データを作成

        Args:
            hour_data: 1時間分の5分足データ
            timestamp: 1時間足のタイムスタンプ

        Returns:
            PriceDataModel: 1時間足データ
        """
        try:
            if len(hour_data) < 12:
                return None

            # OHLCVを計算
            open_price = hour_data[0].open_price
            high_price = max(data.high_price for data in hour_data)
            low_price = min(data.low_price for data in hour_data)
            close_price = hour_data[-1].close_price
            volume = sum(data.volume for data in hour_data)

            return PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                data_source="Yahoo Finance (H1) Aggregated from 5m - "
                + datetime.now().strftime("%Y%m%d_%H%M%S"),
                data_timestamp=hour_data[-1].timestamp,
                fetched_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"❌ 1時間足データ作成エラー: {e}")
            return None

    async def _create_4h_data(
        self, four_hour_data: list, timestamp: datetime
    ) -> PriceDataModel:
        """
        4時間足データを作成

        Args:
            four_hour_data: 4時間分の5分足データ
            timestamp: 4時間足のタイムスタンプ

        Returns:
            PriceDataModel: 4時間足データ
        """
        try:
            if len(four_hour_data) < 48:
                return None

            # OHLCVを計算
            open_price = four_hour_data[0].open_price
            high_price = max(data.high_price for data in four_hour_data)
            low_price = min(data.low_price for data in four_hour_data)
            close_price = four_hour_data[-1].close_price
            volume = sum(data.volume for data in four_hour_data)

            return PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
                data_source="Yahoo Finance (H4) Aggregated from 5m - "
                + datetime.now().strftime("%Y%m%d_%H%M%S"),
                data_timestamp=four_hour_data[-1].timestamp,
                fetched_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"❌ 4時間足データ作成エラー: {e}")
            return None

    async def close(self):
        """リソースをクローズ"""
        await self.engine.dispose()


async def main():
    """メイン関数"""
    try:
        initializer = PureAggregationInitializer()
        success = await initializer.initialize_aggregation()
        await initializer.close()

        if success:
            logger.info("✅ 純粋な集計初期化成功")
            sys.exit(0)
        else:
            logger.error("❌ 純粋な集計初期化失敗")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ メイン処理エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
