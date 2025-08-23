#!/usr/bin/env python3
"""
Simple Data Fetcher - シンプルな継続的データ取得スクリプト

責任:
- 5分間隔で最新の為替データを取得（5分データのみ）
- 重複データのチェックと回避
- PostgreSQLデータベースへの保存
- シンプルなログ出力

特徴:
- 複雑な依存関係なし
- 確実なデータ取得
- エラーハンドリング
- 軽量で高速
- API制限対応（5分データのみ）
- テストモード（データベース保存なし）
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytz
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/simple_data_fetcher.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class SimpleDataFetcher:
    """
    シンプルなデータ取得クラス
    """

    def __init__(self, test_mode: bool = False):
        self.currency_pair = "USD/JPY"
        self.test_mode = test_mode
        self.db_url = None
        self.engine = None
        self.session_factory = None
        self.session = None
        self.price_repo = None
        self.yahoo_client = YahooFinanceClient()

    async def initialize_database(self):
        """
        データベース接続を初期化
        """
        try:
            # テストモードの場合はデータベース接続をスキップ
            if self.test_mode:
                logger.info("🧪 テストモード: データベース接続をスキップ")
                return

            # 環境変数からデータベースURLを取得
            self.db_url = os.getenv("DATABASE_URL")
            if not self.db_url:
                raise ValueError("DATABASE_URL環境変数が設定されていません")

            # データベースエンジンを作成
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # セッションを作成
            self.session = self.session_factory()
            self.price_repo = PriceDataRepositoryImpl(self.session)

            logger.info("✅ データベース接続を初期化しました")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise

    async def get_latest_timestamp(self, timeframe: str) -> datetime:
        """
        指定時間足の最新タイムスタンプを取得

        Args:
            timeframe: 時間足（"5m", "1h", "4h", "1d"）

        Returns:
            datetime: 最新タイムスタンプ
        """
        try:
            # テストモードの場合は1日前を返す
            if self.test_mode:
                default_time = datetime.now() - timedelta(days=1)
                logger.info(
                    f"�� テストモード: {timeframe}デフォルト時刻: {default_time}"
                )
                return default_time

            # データベースから最新のタイムスタンプを取得
            latest_data = await self.price_repo.get_latest_by_timeframe(
                self.currency_pair, timeframe
            )

            if latest_data:
                logger.info(
                    f"📅 {timeframe}最新タイムスタンプ: {latest_data.timestamp}"
                )
                return latest_data.timestamp
            else:
                # データがない場合は1日前から開始
                default_time = datetime.now() - timedelta(days=1)
                logger.info(f"📅 {timeframe}データなし、デフォルト時刻: {default_time}")
                return default_time

        except Exception as e:
            logger.error(f"❌ {timeframe}最新タイムスタンプ取得エラー: {e}")
            # エラーの場合は1日前から開始
            return datetime.now() - timedelta(days=1)

    async def fetch_and_save_data(self, timeframe: str) -> int:
        """
        指定時間足のデータを取得して保存

        Args:
            timeframe: 時間足（"5m", "1h", "4h", "1d"）

        Returns:
            int: 保存件数
        """
        try:
            logger.info(f"🔄 {timeframe}データ取得開始")

            # 最新タイムスタンプを取得
            latest_timestamp = await self.get_latest_timestamp(timeframe)
            start_date = latest_timestamp + timedelta(
                minutes=1
            )  # 重複を避けるため1分後から
            
            # タイムゾーン情報を統一
            jst = pytz.timezone("Asia/Tokyo")
            end_date = datetime.now(jst)

            # 開始日が現在時刻より後の場合はスキップ
            if start_date >= end_date:
                logger.info(f"ℹ️ {timeframe}新しいデータはありません")
                return 0

            # Yahoo Financeからデータを取得
            # timeframeをYahoo Financeのintervalに変換
            interval_mapping = {"5m": "5m", "1h": "1h", "4h": "4h", "1d": "1d"}
            interval = interval_mapping.get(timeframe, "1d")

            # 継続的データ取得用：最新の数件のみ取得
            # 5分間隔で実行するため、最新の1日分程度で十分
            period = "1d"  # 最新1日分

            data = await self.yahoo_client.get_historical_data(
                self.currency_pair, period, interval
            )

            if data is None or data.empty:
                logger.info(f"ℹ️ {timeframe}取得データなし")
                return 0

            # テストモードの場合はデータを表示してスキップ
            if self.test_mode:
                logger.info(f"🧪 テストモード: {timeframe}取得データ（保存なし）")
                logger.info(f"🧪 データ件数: {len(data)}")
                logger.info(f"🧪 データ範囲: {data.index[0]} ～ {data.index[-1]}")
                logger.info(f"🧪 最新データ: {data.iloc[-1].to_dict()}")
                return len(data)  # 取得件数を返す

            # データを保存
            saved_count = 0
            for _, row in data.iterrows():
                try:
                    # 重複チェック（タイムスタンプとデータソースで判定）
                    existing = await self.price_repo.find_by_timestamp_and_source(
                        row.name, self.currency_pair, "yahoo_finance_5m_continuous"
                    )

                    if existing:
                        logger.debug(f"⏭️ 重複データをスキップ: {row.name}")
                        continue

                    # 日本時間での保存
                    jst = pytz.timezone("Asia/Tokyo")
                    current_time = datetime.now(jst)

                    # 新しいデータを保存
                    price_data = PriceDataModel(
                        currency_pair=self.currency_pair,
                        timestamp=row.name,
                        data_timestamp=row.name,  # データの実際のタイムスタンプ
                        fetched_at=current_time,  # 日本時間での取得時刻
                        open_price=float(row["Open"]),
                        high_price=float(row["High"]),
                        low_price=float(row["Low"]),
                        close_price=float(row["Close"]),
                        volume=(
                            int(row["Volume"])
                            if "Volume" in row and not pd.isna(row["Volume"])
                            else 0
                        ),
                        data_source="yahoo_finance_5m_continuous",  # 継続的データ取得用
                    )

                    await self.price_repo.save(price_data)
                    saved_count += 1

                except Exception as e:
                    logger.error(f"❌ データ保存エラー: {e}")
                    continue

            logger.info(f"✅ {timeframe}データ保存完了: {saved_count}件")
            return saved_count

        except Exception as e:
            logger.error(f"❌ {timeframe}データ取得・保存エラー: {e}")
            return 0

    async def run_fetch_cycle(self) -> dict:
        """
        データ取得サイクルを実行

        Returns:
            dict: 実行結果
        """
        try:
            mode_text = "🧪 テストモード" if self.test_mode else "🚀 本番モード"
            logger.info(f"{mode_text} シンプルデータ取得サイクル開始")

            start_time = datetime.now()
            total_saved = 0
            results = {}

            # 5分データのみ取得（API制限対応）
            timeframe = "5m"
            try:
                saved_count = await self.fetch_and_save_data(timeframe)
                results[timeframe] = saved_count
                total_saved += saved_count
            except Exception as e:
                logger.error(f"❌ {timeframe}処理エラー: {e}")
                results[timeframe] = 0

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            action_text = "取得" if self.test_mode else "保存"
            result = {
                "status": "success",
                "mode": "test" if self.test_mode else "production",
                f"total_{action_text}": total_saved,
                "results": results,
                "processing_time": processing_time,
                "timestamp": end_time,
            }

            logger.info(
                f"🎉 データ取得サイクル完了: {total_saved}件{action_text}、{processing_time:.2f}秒"
            )
            return result

        except Exception as e:
            logger.error(f"❌ データ取得サイクルエラー: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        # テストモードの場合はスキップ
        if self.test_mode:
            logger.info("🧪 テストモード: クリーンアップをスキップ")
            return

        try:
            if self.session:
                await self.session.close()
        except Exception as e:
            logger.error(f"❌ セッションクリーンアップエラー: {e}")

        try:
            if self.engine:
                await self.engine.dispose()
        except Exception as e:
            logger.error(f"❌ エンジンクリーンアップエラー: {e}")

        logger.info("✅ リソースをクリーンアップしました")


async def main():
    """
    メイン関数
    """
    import argparse

    parser = argparse.ArgumentParser(description="シンプルデータ取得スクリプト")
    parser.add_argument(
        "--timeframe",
        choices=["5m", "1h", "4h", "1d", "all"],
        default="all",
        help="取得する時間足",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="テストモード（データベース保存なし、詳細ログ出力）",
    )

    args = parser.parse_args()

    # テストモードの場合はログレベルを変更
    if args.test:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🧪 テストモードで実行（データベース保存なし）")

    fetcher = SimpleDataFetcher(test_mode=args.test)

    try:
        # データベースを初期化
        await fetcher.initialize_database()

        if args.timeframe == "all":
            # 全時間足を取得
            result = await fetcher.run_fetch_cycle()
        else:
            # 特定の時間足のみ取得
            saved_count = await fetcher.fetch_and_save_data(args.timeframe)
            action_text = "取得" if args.test else "保存"
            result = {
                "status": "success",
                "mode": "test" if args.test else "production",
                f"total_{action_text}": saved_count,
                "results": {args.timeframe: saved_count},
                "timestamp": datetime.now(),
            }

        print(f"Result: {result}")

    except Exception as e:
        logger.error(f"❌ メイン実行エラー: {e}")
        sys.exit(1)

    finally:
        await fetcher.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
