#!/usr/bin/env python3
"""
データベース接続テストスクリプト
Phase 1: データ準備とシステム確認

データベース接続とテーブル確認を行うテストスクリプト
"""

import argparse
import asyncio
import logging
import sys
from typing import Dict

import yaml

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.database.models.notification_history_model import (
    NotificationHistoryModel,
)
from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseConnectionTester:
    """データベース接続テストクラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.test_results = {}

    async def test_database_connection(self) -> Dict:
        """データベース接続テスト実行"""
        logger.info("=== データベース接続テスト開始 ===")

        try:
            # 1. データベース接続テスト
            connection_test = await self._test_connection()
            self.test_results["connection"] = connection_test

            if not connection_test["success"]:
                logger.error("データベース接続に失敗しました")
                return self.test_results

            # 2. テーブル存在確認テスト
            table_test = await self._test_table_existence()
            self.test_results["table_existence"] = table_test

            # 3. テーブル構造確認テスト
            if table_test["success"]:
                structure_test = await self._test_table_structure()
                self.test_results["table_structure"] = structure_test

            # 4. 基本的なCRUD操作テスト
            if table_test["success"]:
                crud_test = await self._test_crud_operations()
                self.test_results["crud_operations"] = crud_test

            # 5. 結果サマリー
            self._generate_summary()

            return self.test_results

        except Exception as e:
            logger.error(f"データベース接続テストでエラーが発生しました: {e}")
            self.test_results["error"] = str(e)
            return self.test_results

    async def _test_connection(self) -> Dict:
        """データベース接続テスト"""
        logger.info("データベース接続テスト開始...")

        try:
            # データベース接続の確認
            engine = self.db_manager.get_engine()

            if engine is None:
                return {
                    "success": False,
                    "error": "データベースエンジンが作成できませんでした",
                }

            # 接続テスト
            async with engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                test_value = result.scalar()

                if test_value == 1:
                    logger.info("✅ データベース接続テスト成功")
                    return {
                        "success": True,
                        "message": "データベース接続が正常です",
                        "engine_type": str(type(engine)),
                    }
                else:
                    return {"success": False, "error": "接続テストクエリが失敗しました"}

        except Exception as e:
            logger.error(f"データベース接続テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_table_existence(self) -> Dict:
        """テーブル存在確認テスト"""
        logger.info("テーブル存在確認テスト開始...")

        try:
            engine = self.db_manager.get_engine()
            required_tables = [
                "pattern_detections",
                "technical_indicators",
                "price_data",
                "notification_history",
            ]

            table_results = {}
            async with engine.begin() as conn:
                for table_name in required_tables:
                    try:
                        # テーブル存在確認クエリ
                        result = await conn.execute(
                            f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')"
                        )
                        exists = result.scalar()

                        table_results[table_name] = {
                            "exists": exists,
                            "status": "存在" if exists else "不存在",
                        }

                    except Exception as e:
                        table_results[table_name] = {"exists": False, "error": str(e)}

            # 成功数の計算
            existing_tables = sum(
                1 for result in table_results.values() if result.get("exists", False)
            )
            total_tables = len(required_tables)

            logger.info(f"✅ テーブル存在確認テスト完了")
            logger.info(f"  存在テーブル: {existing_tables}/{total_tables}")

            return {
                "success": existing_tables == total_tables,
                "total_tables": total_tables,
                "existing_tables": existing_tables,
                "table_results": table_results,
            }

        except Exception as e:
            logger.error(f"テーブル存在確認テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_table_structure(self) -> Dict:
        """テーブル構造確認テスト"""
        logger.info("テーブル構造確認テスト開始...")

        try:
            engine = self.db_manager.get_engine()

            # 各テーブルの構造確認
            table_structures = {}

            async with engine.begin() as conn:
                # pattern_detectionsテーブル
                try:
                    result = await conn.execute(
                        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'pattern_detections'"
                    )
                    columns = [dict(row) for row in result]
                    table_structures["pattern_detections"] = {
                        "success": True,
                        "columns": columns,
                    }
                except Exception as e:
                    table_structures["pattern_detections"] = {
                        "success": False,
                        "error": str(e),
                    }

                # technical_indicatorsテーブル
                try:
                    result = await conn.execute(
                        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'technical_indicators'"
                    )
                    columns = [dict(row) for row in result]
                    table_structures["technical_indicators"] = {
                        "success": True,
                        "columns": columns,
                    }
                except Exception as e:
                    table_structures["technical_indicators"] = {
                        "success": False,
                        "error": str(e),
                    }

                # price_dataテーブル
                try:
                    result = await conn.execute(
                        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'price_data'"
                    )
                    columns = [dict(row) for row in result]
                    table_structures["price_data"] = {
                        "success": True,
                        "columns": columns,
                    }
                except Exception as e:
                    table_structures["price_data"] = {"success": False, "error": str(e)}

                # notification_historyテーブル
                try:
                    result = await conn.execute(
                        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'notification_history'"
                    )
                    columns = [dict(row) for row in result]
                    table_structures["notification_history"] = {
                        "success": True,
                        "columns": columns,
                    }
                except Exception as e:
                    table_structures["notification_history"] = {
                        "success": False,
                        "error": str(e),
                    }

            # 成功数の計算
            successful_checks = sum(
                1
                for result in table_structures.values()
                if result.get("success", False)
            )
            total_checks = len(table_structures)

            logger.info(f"✅ テーブル構造確認テスト完了")
            logger.info(f"  成功: {successful_checks}/{total_checks}")

            return {
                "success": successful_checks == total_checks,
                "total_checks": total_checks,
                "successful_checks": successful_checks,
                "table_structures": table_structures,
            }

        except Exception as e:
            logger.error(f"テーブル構造確認テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_crud_operations(self) -> Dict:
        """基本的なCRUD操作テスト"""
        logger.info("CRUD操作テスト開始...")

        try:
            # テスト用のデータ
            test_data = {
                "pattern_number": 1,
                "currency_pair": "USD/JPY",
                "confidence_score": 0.85,
                "direction": "BUY",
                "timeframe": "5m",
            }

            # 1. Create (作成) テスト
            create_result = await self._test_create_operation(test_data)

            # 2. Read (読み取り) テスト
            read_result = await self._test_read_operation(test_data["pattern_number"])

            # 3. Update (更新) テスト
            update_result = await self._test_update_operation(
                test_data["pattern_number"]
            )

            # 4. Delete (削除) テスト
            delete_result = await self._test_delete_operation(
                test_data["pattern_number"]
            )

            # 結果の集計
            crud_results = {
                "create": create_result,
                "read": read_result,
                "update": update_result,
                "delete": delete_result,
            }

            successful_operations = sum(
                1 for result in crud_results.values() if result.get("success", False)
            )
            total_operations = len(crud_results)

            logger.info(f"✅ CRUD操作テスト完了")
            logger.info(f"  成功: {successful_operations}/{total_operations}")

            return {
                "success": successful_operations == total_operations,
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "crud_results": crud_results,
            }

        except Exception as e:
            logger.error(f"CRUD操作テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_create_operation(self, test_data: Dict) -> Dict:
        """作成操作テスト"""
        try:
            # テスト用のパターン検出データを作成
            pattern_detection = PatternDetectionModel(
                pattern_number=test_data["pattern_number"],
                currency_pair=test_data["currency_pair"],
                confidence_score=test_data["confidence_score"],
                direction=test_data["direction"],
                timeframe=test_data["timeframe"],
            )

            # データベースに保存
            async with self.db_manager.get_session() as session:
                session.add(pattern_detection)
                await session.commit()

            return {"success": True, "message": "データの作成に成功しました"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_read_operation(self, pattern_number: int) -> Dict:
        """読み取り操作テスト"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    "SELECT * FROM pattern_detections WHERE pattern_number = :pattern_number",
                    {"pattern_number": pattern_number},
                )
                row = result.fetchone()

                if row:
                    return {
                        "success": True,
                        "message": "データの読み取りに成功しました",
                        "data_found": True,
                    }
                else:
                    return {"success": False, "error": "データが見つかりませんでした"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_update_operation(self, pattern_number: int) -> Dict:
        """更新操作テスト"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    "UPDATE pattern_detections SET confidence_score = 0.90 WHERE pattern_number = :pattern_number",
                    {"pattern_number": pattern_number},
                )
                await session.commit()

                return {"success": True, "message": "データの更新に成功しました"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _test_delete_operation(self, pattern_number: int) -> Dict:
        """削除操作テスト"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(
                    "DELETE FROM pattern_detections WHERE pattern_number = :pattern_number",
                    {"pattern_number": pattern_number},
                )
                await session.commit()

                return {"success": True, "message": "データの削除に成功しました"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_summary(self):
        """テスト結果サマリー生成"""
        logger.info("=== データベース接続テスト結果サマリー ===")

        total_tests = len(self.test_results)
        passed_tests = sum(
            1
            for result in self.test_results.values()
            if isinstance(result, dict) and result.get("success", False)
        )

        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {passed_tests}")
        logger.info(f"失敗: {total_tests - passed_tests}")

        # 各テストの詳細結果
        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ 成功" if result.get("success", False) else "❌ 失敗"
                logger.info(f"{test_name}: {status}")

                if not result.get("success", False) and "error" in result:
                    logger.error(f"  エラー: {result['error']}")


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="データベース接続テストスクリプト")
    parser.add_argument("--output", help="結果出力ファイル")

    args = parser.parse_args()

    # テスト実行
    tester = DatabaseConnectionTester()
    results = await tester.test_database_connection()

    # 結果出力
    if args.output:
        with open(args.output, "w") as f:
            yaml.dump(results, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"結果を {args.output} に保存しました")

    # 終了コード
    success_count = sum(
        1
        for result in results.values()
        if isinstance(result, dict) and result.get("success", False)
    )
    total_tests = len([r for r in results.values() if isinstance(r, dict)])

    if success_count == total_tests:
        logger.info("🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        logger.error(f"❌ {total_tests - success_count}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
