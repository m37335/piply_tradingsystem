#!/usr/bin/env python3
"""
Multi-Timeframe Initial Data Load Script
マルチタイムフレーム初回データ取得スクリプト

責任:
- 5分足、1時間足、4時間足、日足の全データを一括取得
- 各タイムフレームでテクニカル指標を計算
- 初回システム構築の基盤データを準備
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.append("/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.services.technical_indicator_service import (
    TechnicalIndicatorService,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class MultiTimeframeInitialLoader:
    """マルチタイムフレーム初回データローダー"""

    def __init__(self):
        self.currency_pair = "USD/JPY"
        self.session = None
        self.yahoo_client = YahooFinanceClient()
        self.price_repo = None

        # タイムフレーム設定
        self.timeframes = {
            "5m": {"period": "7d", "interval": "5m", "description": "5分足"},
            "1h": {"period": "30d", "interval": "1h", "description": "1時間足"},
            "4h": {"period": "60d", "interval": "4h", "description": "4時間足"},
            "1d": {"period": "365d", "interval": "1d", "description": "日足"},
        }

    async def initialize(self):
        """初期化"""
        try:
            # SQLite環境を強制設定
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

            self.session = await get_async_session()
            self.price_repo = PriceDataRepositoryImpl(self.session)

            logger.info("Multi-timeframe initial loader initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    async def load_all_timeframe_data(self):
        """全タイムフレームのデータを読み込み"""
        try:
            logger.info("=== マルチタイムフレーム初回データ取得開始 ===")

            total_saved = 0

            for timeframe, config in self.timeframes.items():
                logger.info(f"📊 {config['description']}データ取得中...")

                saved_count = await self._load_timeframe_data(
                    timeframe, config["period"], config["interval"]
                )

                total_saved += saved_count
                logger.info(f"✅ {config['description']}: {saved_count}件保存")

            logger.info(f"🎉 全タイムフレーム完了: 合計{total_saved}件")
            return total_saved

        except Exception as e:
            logger.error(f"Error loading multi-timeframe data: {e}")
            return 0

    async def _load_timeframe_data(
        self, timeframe: str, period: str, interval: str
    ) -> int:
        """特定タイムフレームのデータを読み込み"""
        try:
            logger.info(f"  📈 {self.currency_pair} {timeframe}履歴データ取得中...")
            logger.info(f"    期間: {period}, 間隔: {interval}")

            # Yahoo Financeから履歴データ取得
            df = await self.yahoo_client.get_historical_data(
                self.currency_pair, period, interval
            )

            if df is None or df.empty:
                logger.warning(f"  ❌ {timeframe}データが取得できませんでした")
                return 0

            logger.info(f"  ✅ {timeframe}: {len(df)}件のデータ取得")
            logger.info(f"    期間: {df.index[0]} ～ {df.index[-1]}")
            logger.info(f"    最新価格: {df['Close'].iloc[-1]:.4f}")

            # データベースに保存
            saved_count = 0
            for timestamp, row in df.iterrows():
                try:
                    # タイムスタンプの処理
                    if hasattr(timestamp, "to_pydatetime"):
                        dt = timestamp.to_pydatetime()
                    else:
                        dt = datetime.now()

                    # 価格データモデル作成
                    price_data = PriceDataModel(
                        currency_pair=self.currency_pair,
                        timestamp=dt,
                        open_price=float(row["Open"]),
                        high_price=float(row["High"]),
                        low_price=float(row["Low"]),
                        close_price=float(row["Close"]),
                        volume=int(row["Volume"]) if row["Volume"] > 0 else 1000000,
                        data_source=f"Yahoo Finance ({timeframe})",
                    )

                    # データバリデーション
                    if not price_data.validate():
                        logger.debug(
                            f"    ⚠️ 無効なデータをスキップ: {timestamp} - O:{row['Open']}, H:{row['High']}, L:{row['Low']}, C:{row['Close']}"
                        )
                        continue

                    # 重複チェック
                    existing = await self.price_repo.find_by_timestamp(
                        dt, self.currency_pair
                    )
                    if existing:
                        continue

                    # 保存
                    await self.price_repo.save(price_data)
                    saved_count += 1

                    # 100件ごとにログ出力
                    if saved_count % 100 == 0:
                        logger.info(f"    💾 保存済み: {saved_count}件")

                except Exception as e:
                    logger.warning(f"    ⚠️ 保存エラー (timestamp: {timestamp}): {e}")
                    continue

            logger.info(f"  ✅ {timeframe}完了: {saved_count}件保存")
            return saved_count

        except Exception as e:
            logger.error(f"  ❌ {timeframe}データ取得エラー: {e}")
            return 0

    async def calculate_all_technical_indicators(self):
        """全タイムフレームのテクニカル指標を計算"""
        try:
            logger.info("=== テクニカル指標計算開始 ===")

            indicator_service = TechnicalIndicatorService(self.session)
            total_indicators = 0

            for timeframe in self.timeframes.keys():
                logger.info(f"📊 {timeframe}テクニカル指標計算中...")

                # 各タイムフレームの期間を設定
                end_date = datetime.now()
                if timeframe == "5m":
                    start_date = end_date - timedelta(days=7)
                elif timeframe == "1h":
                    start_date = end_date - timedelta(days=30)
                elif timeframe == "4h":
                    start_date = end_date - timedelta(days=60)
                else:  # 1d
                    start_date = end_date - timedelta(days=365)

                # テクニカル指標計算
                results = await indicator_service.calculate_all_indicators(
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date,
                )

                timeframe_indicators = sum(
                    len(indicators) for indicators in results.values()
                )
                total_indicators += timeframe_indicators

                logger.info(f"✅ {timeframe}: {timeframe_indicators}件の指標計算完了")

            logger.info(f"🎉 全テクニカル指標計算完了: 合計{total_indicators}件")
            return total_indicators

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return 0

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン関数"""
    logger.info("Starting multi-timeframe initial data load...")

    # 環境変数チェック
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

    loader = MultiTimeframeInitialLoader()

    try:
        await loader.initialize()

        # 1. 全タイムフレームデータ取得
        saved_count = await loader.load_all_timeframe_data()

        if saved_count > 0:
            logger.info(f"✅ データ取得完了: {saved_count}件")

            # 2. テクニカル指標計算
            indicator_count = await loader.calculate_all_technical_indicators()

            if indicator_count > 0:
                logger.info(f"✅ テクニカル指標計算完了: {indicator_count}件")
                logger.info("🎉 マルチタイムフレーム初回データ取得完了！")
            else:
                logger.warning("⚠️ テクニカル指標計算に失敗しました")
                sys.exit(1)
        else:
            logger.error("❌ データ取得に失敗しました")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Multi-timeframe initial data load error: {e}")
        sys.exit(1)
    finally:
        await loader.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
