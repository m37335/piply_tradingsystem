#!/usr/bin/env python3
"""
シンプルデータ取得cronスクリプト

責任:
- 手動実行と同じ流れでfetch_real_5m_dataを直接実行
- 複雑な中間層を経由せずに直接データ取得
- 詳細なログ出力で問題を特定

特徴:
- 手動実行と同じフロー
- シンプルな構造
- 詳細なデバッグログ
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.connection import DatabaseManager
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/simple_data_fetch_cron.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class SimpleDataFetchCron:
    """
    シンプルデータ取得cronクラス
    """

    def __init__(self):
        self.db_manager = None
        self.session = None
        self.data_fetcher = None

    async def initialize_database(self):
        """
        データベース接続を初期化
        """
        try:
            logger.info("🔧 データベース初期化開始...")

            # DatabaseManagerを使用（手動実行と同じ）
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize(
                "sqlite+aiosqlite:///data/exchange_analytics.db"
            )

            # セッションを取得
            self.session = await self.db_manager.get_session().__aenter__()

            # DataFetcherServiceを初期化
            self.data_fetcher = DataFetcherService(self.session)

            logger.info("✅ データベース初期化完了")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            logger.error(traceback.format_exc())
            raise

    async def fetch_data(self):
        """
        データ取得を実行（手動実行と同じ流れ）
        """
        try:
            logger.info("🔄 データ取得開始...")

            # 手動実行と同じ流れでfetch_real_5m_dataを呼び出し
            data = await self.data_fetcher.fetch_real_5m_data()

            if data:
                logger.info("✅ データ取得成功:")
                logger.info(f"   ID: {data.id}")
                logger.info(f"   タイムスタンプ: {data.timestamp}")
                logger.info(f"   データタイムスタンプ: {data.data_timestamp}")
                logger.info(f"   取得実行時刻: {data.fetched_at}")
                logger.info(f"   Open: {data.open_price}")
                logger.info(f"   High: {data.high_price}")
                logger.info(f"   Low: {data.low_price}")
                logger.info(f"   Close: {data.close_price}")
                logger.info(f"   Volume: {data.volume}")
                logger.info(f"   データソース: {data.data_source}")

                # データベースから直接確認
                from sqlalchemy import text

                result = await self.session.execute(
                    text(
                        "SELECT open_price, high_price, low_price, close_price FROM price_data WHERE id = :id"
                    ),
                    {"id": data.id},
                )
                row = result.fetchone()
                if row:
                    logger.info("🗄️ データベース直接確認:")
                    logger.info(f"   Open: {row[0]} (type: {type(row[0])})")
                    logger.info(f"   High: {row[1]} (type: {type(row[1])})")
                    logger.info(f"   Low: {row[2]} (type: {type(row[2])})")
                    logger.info(f"   Close: {row[3]} (type: {type(row[3])})")

                return {"status": "success", "data": data}
            else:
                logger.error("❌ データ取得失敗: Noneが返されました")
                return {"status": "error", "message": "Data fetch returned None"}

        except Exception as e:
            logger.error(f"❌ データ取得エラー: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            if self.db_manager:
                await self.db_manager.close()
            logger.info("✅ リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")

    async def run(self):
        """
        メイン実行メソッド
        """
        try:
            logger.info("🚀 シンプルデータ取得cron開始")

            # データベースを初期化
            await self.initialize_database()

            # データ取得を実行
            result = await self.fetch_data()

            logger.info(f"🎉 シンプルデータ取得cron完了: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ シンプルデータ取得cronエラー: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

        finally:
            await self.cleanup()


async def main():
    """
    メイン関数
    """
    cron = SimpleDataFetchCron()
    result = await cron.run()

    if result.get("status") == "success":
        logger.info("✅ cron実行成功")
        sys.exit(0)
    else:
        logger.error("❌ cron実行失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
