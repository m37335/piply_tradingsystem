#!/usr/bin/env python3
"""
統合データサービステストスクリプト

責任:
- IntegratedDataServiceのテスト
- 完全なデータサイクルのテスト
- パフォーマンス測定
- エラーハンドリングテスト
"""

import asyncio
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, "/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.integrated_data_service import (
    IntegratedDataService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class IntegratedDataServiceTester:
    """統合データサービステスト"""

    def __init__(self):
        self.session = None
        self.integrated_service = None

    async def initialize(self):
        """初期化"""
        try:
            # SQLite環境を強制設定
            os.environ[
                "DATABASE_URL"
            ] = "sqlite+aiosqlite:///data/exchange_analytics.db"

            self.session = await get_async_session()
            self.integrated_service = IntegratedDataService(self.session)

            logger.info("Integrated Data Service Tester initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    async def test_complete_data_cycle(self):
        """完全なデータサイクルをテスト"""
        try:
            logger.info("=== 統合データサービス完全サイクルテスト開始 ===")

            # 完全なデータサイクルを実行
            results = await self.integrated_service.run_complete_data_cycle()

            # 結果の詳細表示
            logger.info("📊 実行結果:")
            logger.info(f"  全体成功: {results['overall_success']}")
            logger.info(f"  実行時間: {results['execution_time']:.2f}秒")

            # データ取得結果
            data_fetch = results["data_fetch"]
            logger.info(f"  データ取得: {'✅' if data_fetch['success'] else '❌'}")
            logger.info(f"    レコード数: {data_fetch['records']}")
            if data_fetch["error"]:
                logger.error(f"    エラー: {data_fetch['error']}")

            # テクニカル指標結果
            technical_indicators = results["technical_indicators"]
            logger.info(f"  テクニカル指標: {'✅' if technical_indicators['success'] else '❌'}")
            logger.info(f"    指標数: {technical_indicators['indicators']}")
            if technical_indicators["error"]:
                logger.error(f"    エラー: {technical_indicators['error']}")

            # パターン検出結果
            pattern_detection = results["pattern_detection"]
            logger.info(f"  パターン検出: {'✅' if pattern_detection['success'] else '❌'}")
            logger.info(f"    パターン数: {pattern_detection['patterns']}")
            if pattern_detection["error"]:
                logger.error(f"    エラー: {pattern_detection['error']}")

            logger.info("=== 統合データサービス完全サイクルテスト完了 ===")

            return results

        except Exception as e:
            logger.error(f"統合データサービステストエラー: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def test_system_status(self):
        """システム状態をテスト"""
        try:
            logger.info("=== システム状態テスト開始 ===")

            status = await self.integrated_service.get_system_status()

            logger.info("📊 システム状態:")
            logger.info(f"  通貨ペア: {status['currency_pair']}")
            logger.info(f"  システム健全性: {status['system_health']}")
            logger.info(f"  最新データタイムスタンプ: {status['latest_data_timestamp']}")
            logger.info(f"  最新指標数: {status['latest_indicators_count']}")
            logger.info(f"  最新パターン数: {status['latest_patterns_count']}")
            logger.info(f"  最終更新: {status['last_update']}")

            if "error" in status:
                logger.error(f"  エラー: {status['error']}")

            logger.info("=== システム状態テスト完了 ===")

            return status

        except Exception as e:
            logger.error(f"システム状態テストエラー: {e}")
            import traceback

            traceback.print_exc()
            return None

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン関数"""
    logger.info("Starting Integrated Data Service Test...")

    tester = IntegratedDataServiceTester()

    try:
        await tester.initialize()

        # 1. システム状態テスト
        await tester.test_system_status()

        # 2. 完全なデータサイクルテスト
        await tester.test_complete_data_cycle()

        logger.info("🎉 統合データサービステスト完了！")

    except Exception as e:
        logger.error(f"Integrated Data Service Test error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
