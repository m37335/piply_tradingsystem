#!/usr/bin/env python3
"""
シンプルなUSD/JPYデータ取得スクリプト
cron用の軽量版
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

try:
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.efficient_pattern_detection_service import (
        EfficientPatternDetectionService,
    )
    from src.infrastructure.database.services.multi_timeframe_data_fetcher_service import (
        MultiTimeframeDataFetcherService,
    )
    from src.infrastructure.database.services.multi_timeframe_technical_indicator_service import (
        MultiTimeframeTechnicalIndicatorService,
    )
    from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


async def main():
    """メイン実行関数"""
    try:
        logger.info("=== USD/JPY データ取得開始 ===")

        # データベースセッション取得（テスト用SQLite）
        try:
            session = await get_async_session()
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            logger.info("テスト用SQLiteを使用します")
            # テスト用のSQLiteセッションを作成
            from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
            from sqlalchemy.orm import sessionmaker

            engine = create_async_engine("sqlite+aiosqlite:///data/test_app.db")
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            session = async_session()

        # サービス初期化
        data_fetcher = MultiTimeframeDataFetcherService(session)
        indicator_service = MultiTimeframeTechnicalIndicatorService(session)
        pattern_detector = EfficientPatternDetectionService(session)
        discord_sender = DiscordWebhookSender()

        # USD/JPYデータ取得
        logger.info("USD/JPYデータ取得中...")
        try:
            # 全時間軸データ取得
            data = await data_fetcher.fetch_all_timeframes()
            if data:
                logger.info("データ取得成功")

                # テクニカル指標計算
                logger.info("テクニカル指標計算中...")
                await indicator_service.calculate_all_indicators("USD/JPY")

                # パターン検出
                logger.info("パターン検出中...")
                patterns = await pattern_detector.detect_patterns("USD/JPY")

                if patterns:
                    logger.info(f"パターン検出: {len(patterns)}件")
                    # Discord通知
                    await discord_sender.send_pattern_notification(patterns)
                else:
                    logger.info("パターン未検出")
            else:
                logger.error("データ取得失敗")
        except Exception as e:
            logger.error(f"データ取得エラー: {e}")

        logger.info("=== USD/JPY データ取得完了 ===")

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
