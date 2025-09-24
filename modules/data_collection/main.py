"""
データ収集モジュールのメインスクリプト

Yahoo Finance APIからデータを収集し、データベースに保存します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.config.settings import DataCollectionSettings
from modules.data_collection.core.data_collection_service import DataCollectionService

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """メイン関数"""
    service = None
    try:
        # 設定を読み込み
        settings = DataCollectionSettings.from_env()
        logger.info(f"Starting data collection with settings: {settings.to_dict()}")

        # サービスを作成して開始
        service = DataCollectionService(settings)
        await service.start()

    except KeyboardInterrupt:
        logger.info("Data collection interrupted by user")
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        sys.exit(1)
    finally:
        if service:
            await service.stop()


async def health_check():
    """ヘルスチェック"""
    try:
        settings = DataCollectionSettings.from_env()
        service = DataCollectionService(settings)
        health = await service.health_check()
        print(f"Health check result: {health}")
        return health
    except Exception as e:
        print(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
