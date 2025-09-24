#!/usr/bin/env python3
"""
重複データクリーンアップスクリプト

データベース内の重複データを検出・削除します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_persistence.config.settings import DataPersistenceSettings
from modules.data_persistence.core.database.connection_manager import (
    DatabaseConnectionManager,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DuplicateCleanupService:
    """重複データクリーンアップサービス"""

    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager

    async def analyze_duplicates(self) -> Dict[str, Any]:
        """重複データを分析"""
        try:
            # 重複データの件数を確認
            query = """
                SELECT 
                    symbol,
                    timeframe,
                    COUNT(*) as total_records,
                    COUNT(DISTINCT timestamp) as unique_timestamps,
                    COUNT(*) - COUNT(DISTINCT timestamp) as duplicate_count
                FROM price_data 
                GROUP BY symbol, timeframe
                HAVING COUNT(*) > COUNT(DISTINCT timestamp)
                ORDER BY duplicate_count DESC
            """

            result = await self.connection_manager.execute_query(query)

            analysis = {
                "duplicate_groups": [],
                "total_duplicates": 0,
                "affected_symbols": set(),
                "affected_timeframes": set(),
            }

            for row in result:
                group_info = {
                    "symbol": row["symbol"],
                    "timeframe": row["timeframe"],
                    "total_records": row["total_records"],
                    "unique_timestamps": row["unique_timestamps"],
                    "duplicate_count": row["duplicate_count"],
                }
                analysis["duplicate_groups"].append(group_info)
                analysis["total_duplicates"] += row["duplicate_count"]
                analysis["affected_symbols"].add(row["symbol"])
                analysis["affected_timeframes"].add(row["timeframe"])

            analysis["affected_symbols"] = list(analysis["affected_symbols"])
            analysis["affected_timeframes"] = list(analysis["affected_timeframes"])

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze duplicates: {e}")
            raise

    async def cleanup_duplicates(self, dry_run: bool = True) -> Dict[str, Any]:
        """重複データをクリーンアップ"""
        try:
            # 重複データの詳細を取得
            query = """
                SELECT 
                    symbol,
                    timeframe,
                    timestamp,
                    COUNT(*) as count,
                    MIN(id) as min_id,
                    MAX(id) as max_id,
                    ARRAY_AGG(id ORDER BY id) as all_ids
                FROM price_data 
                GROUP BY symbol, timeframe, timestamp
                HAVING COUNT(*) > 1
                ORDER BY symbol, timeframe, timestamp
            """

            result = await self.connection_manager.execute_query(query)

            cleanup_stats = {
                "total_duplicate_groups": len(result),
                "total_records_to_delete": 0,
                "records_to_keep": 0,
                "cleanup_details": [],
            }

            if dry_run:
                logger.info("🔍 DRY RUN MODE - 実際の削除は行いません")

            for row in result:
                symbol = row["symbol"]
                timeframe = row["timeframe"]
                timestamp = row["timestamp"]
                count = row["count"]
                all_ids = row["all_ids"]

                # 最新のIDを残す（最大ID）
                ids_to_delete = all_ids[:-1]  # 最後のID以外を削除
                id_to_keep = all_ids[-1]  # 最新のIDを保持

                cleanup_detail = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": timestamp,
                    "duplicate_count": count,
                    "ids_to_delete": ids_to_delete,
                    "id_to_keep": id_to_keep,
                }
                cleanup_stats["cleanup_details"].append(cleanup_detail)
                cleanup_stats["total_records_to_delete"] += len(ids_to_delete)
                cleanup_stats["records_to_keep"] += 1

                if not dry_run:
                    # 実際に削除を実行
                    delete_query = """
                        DELETE FROM price_data 
                        WHERE id = ANY($1)
                    """
                    await self.connection_manager.execute_command(
                        delete_query, ids_to_delete
                    )
                    logger.info(
                        f"Deleted {len(ids_to_delete)} duplicate records for {symbol} {timeframe} at {timestamp}"
                    )

            if not dry_run:
                logger.info(
                    f"✅ Cleanup completed: {cleanup_stats['total_records_to_delete']} records deleted"
                )
            else:
                logger.info(
                    f"🔍 DRY RUN: Would delete {cleanup_stats['total_records_to_delete']} records"
                )

            return cleanup_stats

        except Exception as e:
            logger.error(f"Failed to cleanup duplicates: {e}")
            raise

    async def verify_cleanup(self) -> Dict[str, Any]:
        """クリーンアップ後の検証"""
        try:
            # 重複データが残っていないかチェック
            query = """
                SELECT 
                    symbol,
                    timeframe,
                    timestamp,
                    COUNT(*) as count
                FROM price_data 
                GROUP BY symbol, timeframe, timestamp
                HAVING COUNT(*) > 1
            """

            result = await self.connection_manager.execute_query(query)

            if len(result) == 0:
                logger.info("✅ 重複データは完全に削除されました")
                return {"status": "clean", "remaining_duplicates": 0}
            else:
                logger.warning(f"⚠️ {len(result)}個の重複グループが残っています")
                return {"status": "dirty", "remaining_duplicates": len(result)}

        except Exception as e:
            logger.error(f"Failed to verify cleanup: {e}")
            raise

    async def get_data_quality_report(self) -> Dict[str, Any]:
        """データ品質レポートを生成"""
        try:
            # 全体の統計
            total_query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    COUNT(DISTINCT timeframe) as unique_timeframes,
                    MIN(timestamp) as earliest_data,
                    MAX(timestamp) as latest_data
                FROM price_data
            """

            total_result = await self.connection_manager.execute_query(total_query)
            total_stats = dict(total_result[0]) if total_result else {}

            # 時間足別の統計
            timeframe_query = """
                SELECT 
                    timeframe,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT symbol) as symbol_count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM price_data
                GROUP BY timeframe
                ORDER BY timeframe
            """

            timeframe_result = await self.connection_manager.execute_query(
                timeframe_query
            )
            timeframe_stats = [dict(row) for row in timeframe_result]

            # シンボル別の統計
            symbol_query = """
                SELECT 
                    symbol,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT timeframe) as timeframe_count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM price_data
                GROUP BY symbol
                ORDER BY symbol
            """

            symbol_result = await self.connection_manager.execute_query(symbol_query)
            symbol_stats = [dict(row) for row in symbol_result]

            return {
                "total_stats": total_stats,
                "timeframe_stats": timeframe_stats,
                "symbol_stats": symbol_stats,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate data quality report: {e}")
            raise


async def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="重複データクリーンアップスクリプト")
    parser.add_argument(
        "--action",
        choices=["analyze", "cleanup", "verify", "report"],
        default="analyze",
        help="実行するアクション",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際の削除を行わずにシミュレーションのみ実行",
    )
    parser.add_argument("--force", action="store_true", help="確認なしで削除を実行")

    args = parser.parse_args()

    try:
        # 設定を読み込み
        settings = DataPersistenceSettings.from_env()
        logger.info(f"Connecting to database: {settings.database.database}")

        # 接続管理を初期化
        connection_manager = DatabaseConnectionManager(
            connection_string=settings.database.connection_string,
            min_connections=settings.database.min_connections,
            max_connections=settings.database.max_connections,
        )

        await connection_manager.initialize()

        # クリーンアップサービスを初期化
        cleanup_service = DuplicateCleanupService(connection_manager)

        if args.action == "analyze":
            logger.info("🔍 重複データを分析しています...")
            analysis = await cleanup_service.analyze_duplicates()

            if analysis["total_duplicates"] == 0:
                logger.info("✅ 重複データは見つかりませんでした")
            else:
                logger.info(
                    f"⚠️ {analysis['total_duplicates']}件の重複データが見つかりました"
                )
                logger.info(
                    f"影響を受けるシンボル: {', '.join(analysis['affected_symbols'])}"
                )
                logger.info(
                    f"影響を受ける時間足: {', '.join(analysis['affected_timeframes'])}"
                )

                for group in analysis["duplicate_groups"]:
                    logger.info(
                        f"  {group['symbol']} {group['timeframe']}: "
                        f"{group['duplicate_count']}件の重複"
                    )

        elif args.action == "cleanup":
            dry_run = args.dry_run or not args.force

            if not dry_run:
                logger.warning("⚠️ 実際の削除を実行します。この操作は元に戻せません。")
                if not args.force:
                    response = input("続行しますか？ (yes/no): ")
                    if response.lower() != "yes":
                        logger.info("操作をキャンセルしました")
                        return

            logger.info("🧹 重複データをクリーンアップしています...")
            cleanup_stats = await cleanup_service.cleanup_duplicates(dry_run=dry_run)

            logger.info(f"クリーンアップ完了:")
            logger.info(
                f"  削除対象グループ: {cleanup_stats['total_duplicate_groups']}"
            )
            logger.info(f"  削除レコード数: {cleanup_stats['total_records_to_delete']}")
            logger.info(f"  保持レコード数: {cleanup_stats['records_to_keep']}")

        elif args.action == "verify":
            logger.info("🔍 クリーンアップ結果を検証しています...")
            verification = await cleanup_service.verify_cleanup()

            if verification["status"] == "clean":
                logger.info("✅ 重複データは完全に削除されました")
            else:
                logger.warning(
                    f"⚠️ {verification['remaining_duplicates']}個の重複グループが残っています"
                )

        elif args.action == "report":
            logger.info("📊 データ品質レポートを生成しています...")
            report = await cleanup_service.get_data_quality_report()

            logger.info("📈 データ品質レポート:")
            logger.info(f"  総レコード数: {report['total_stats']['total_records']:,}")
            logger.info(f"  シンボル数: {report['total_stats']['unique_symbols']}")
            logger.info(f"  時間足数: {report['total_stats']['unique_timeframes']}")
            logger.info(
                f"  データ期間: {report['total_stats']['earliest_data']} - {report['total_stats']['latest_data']}"
            )

            logger.info("\n時間足別統計:")
            for tf_stat in report["timeframe_stats"]:
                logger.info(
                    f"  {tf_stat['timeframe']}: {tf_stat['record_count']:,}レコード"
                )

            logger.info("\nシンボル別統計:")
            for symbol_stat in report["symbol_stats"]:
                logger.info(
                    f"  {symbol_stat['symbol']}: {symbol_stat['record_count']:,}レコード"
                )

        logger.info("✅ 操作が完了しました")

    except Exception as e:
        logger.error(f"操作が失敗しました: {e}")
        sys.exit(1)

    finally:
        # 接続を閉じる
        if "connection_manager" in locals():
            await connection_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
