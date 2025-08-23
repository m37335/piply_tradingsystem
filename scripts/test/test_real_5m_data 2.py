#!/usr/bin/env python3
"""
実際の5分足データ取得テストスクリプト

責任:
- fetch_real_5m_data()メソッドのテスト
- 実際のデータと人工データの比較
- データ品質の検証
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, "/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class Real5mDataTester:
    """実際の5分足データ取得テスト"""

    def __init__(self):
        self.session = None
        self.data_fetcher = None

    async def initialize(self):
        """初期化"""
        try:
            # SQLite環境を強制設定
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"

            self.session = await get_async_session()
            self.data_fetcher = DataFetcherService(self.session)

            logger.info("Real 5m Data Tester initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    async def test_real_5m_data(self):
        """実際の5分足データ取得をテスト"""
        try:
            logger.info("=== 実際の5分足データ取得テスト開始 ===")

            # 1. 従来の人工データ取得
            logger.info("1. 従来の人工データ取得テスト...")
            artificial_data = await self.data_fetcher.fetch_current_price_data()
            
            if artificial_data:
                logger.info(f"  人工データ取得成功:")
                logger.info(f"    Open: {artificial_data.open_price}")
                logger.info(f"    High: {artificial_data.high_price}")
                logger.info(f"    Low: {artificial_data.low_price}")
                logger.info(f"    Close: {artificial_data.close_price}")
                logger.info(f"    Volume: {artificial_data.volume}")
                logger.info(f"    Timestamp: {artificial_data.timestamp}")
            else:
                logger.warning("  人工データ取得失敗")

            # 2. 新しい実際の5分足データ取得
            logger.info("2. 新しい実際の5分足データ取得テスト...")
            try:
                real_data = await self.data_fetcher.fetch_real_5m_data()
                
                if real_data:
                    logger.info(f"  実際の5分足データ取得成功:")
                    logger.info(f"    Open: {real_data.open_price}")
                    logger.info(f"    High: {real_data.high_price}")
                    logger.info(f"    Low: {real_data.low_price}")
                    logger.info(f"    Close: {real_data.close_price}")
                    logger.info(f"    Volume: {real_data.volume}")
                    logger.info(f"    Timestamp: {real_data.timestamp}")
                    logger.info(f"    Data Source: {real_data.data_source}")
                else:
                    logger.warning("  実際の5分足データ取得失敗")
            except Exception as e:
                logger.error(f"  実際の5分足データ取得エラー: {e}")
                import traceback
                traceback.print_exc()

            # 3. データ比較
            if artificial_data and real_data:
                logger.info("3. データ比較:")
                logger.info(f"   終値差: {abs(real_data.close_price - artificial_data.close_price):.4f}")
                logger.info(f"   高値差: {abs(real_data.high_price - artificial_data.high_price):.4f}")
                logger.info(f"   安値差: {abs(real_data.low_price - artificial_data.low_price):.4f}")
                logger.info(f"   オープン差: {abs(real_data.open_price - artificial_data.open_price):.4f}")
                
                # データ品質評価
                self._evaluate_data_quality(artificial_data, real_data)

            # 4. 最新データの確認
            logger.info("4. 最新データ確認...")
            latest_data = await self.data_fetcher.get_latest_price_data(limit=5)
            
            if latest_data:
                logger.info(f"  最新5件のデータ:")
                for i, data in enumerate(latest_data, 1):
                    logger.info(f"    {i}. {data.timestamp}: O={data.open_price}, H={data.high_price}, L={data.low_price}, C={data.close_price}, V={data.volume}")
            else:
                logger.warning("  最新データ取得失敗")

            logger.info("=== 実際の5分足データ取得テスト完了 ===")

        except Exception as e:
            logger.error(f"Error testing real 5m data: {e}")
            import traceback
            traceback.print_exc()

    def _evaluate_data_quality(self, artificial_data, real_data):
        """データ品質を評価"""
        logger.info("  データ品質評価:")
        
        # 価格範囲の合理性
        artificial_range = artificial_data.high_price - artificial_data.low_price
        real_range = real_data.high_price - real_data.low_price
        
        logger.info(f"   人工データ価格範囲: {artificial_range:.4f}")
        logger.info(f"   実際データ価格範囲: {real_range:.4f}")
        
        # ボリュームの合理性
        artificial_volume = artificial_data.volume
        real_volume = real_data.volume
        
        logger.info(f"   人工データボリューム: {artificial_volume:,}")
        logger.info(f"   実際データボリューム: {real_volume:,}")
        
        # データソースの確認
        logger.info(f"   人工データソース: {getattr(artificial_data, 'data_source', 'Unknown')}")
        logger.info(f"   実際データソース: {real_data.data_source}")

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン関数"""
    logger.info("Starting real 5m data test...")

    tester = Real5mDataTester()

    try:
        await tester.initialize()
        await tester.test_real_5m_data()

    except Exception as e:
        logger.error(f"Real 5m data test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
