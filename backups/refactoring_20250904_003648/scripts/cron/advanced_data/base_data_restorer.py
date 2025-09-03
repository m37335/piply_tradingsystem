"""
Base Data Restorer
基盤データ復元機能

責任:
- Phase 2で取得した基盤データバックアップからの復元
- SQLiteからPostgreSQLへのデータ移行
- 復元結果の検証
- エラーハンドリング

設計書参照:
- CLIデータベース初期化システム実装仕様書_2025.md
- CLIデータベース初期化システム実装計画書_Phase3_分析処理_2025.md
"""

import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel


class BaseDataRestorer:
    """
    基盤データ復元クラス

    Phase 2で取得した基盤データバックアップからPostgreSQLに復元する機能を提供
    """

    def __init__(self):
        self.base_backup_path: str = (
            "/app/data/exchange_analytics_phase2_complete_2025-08-14.db"
        )
        self.current_db_path: str = "/app/data/exchange_analytics.db"
        self.session: Optional[AsyncSession] = None

    async def restore_base_data(self) -> bool:
        """
        基盤データを復元（SQLiteからPostgreSQLへ）

        Returns:
            bool: 復元成功時True、失敗時False
        """
        try:
            print("🔄 基盤データの復元を開始...")

            # バックアップファイルの存在確認
            if not os.path.exists(self.base_backup_path):
                print(f"❌ 基盤データバックアップが見つかりません: {self.base_backup_path}")
                return False

            # 現在のデータベースをバックアップ
            await self._backup_current_database()

            # セッションを初期化
            if not await self.initialize_session():
                return False

            # SQLiteからPostgreSQLへのデータ移行
            success = await self._migrate_from_sqlite_to_postgresql()

            if success:
                print("✅ 基盤データの復元が完了しました")
            else:
                print("❌ 基盤データの復元に失敗しました")

            return success

        except Exception as e:
            print(f"❌ 基盤データ復元エラー: {e}")
            return False

    async def _backup_current_database(self) -> None:
        """
        現在のデータベースをバックアップ
        """
        if os.path.exists(self.current_db_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.current_db_path}.backup_{timestamp}"
            shutil.copy2(self.current_db_path, backup_path)
            print(f"📦 現在のデータベースをバックアップ: {backup_path}")

    async def _migrate_from_sqlite_to_postgresql(self) -> bool:
        """
        SQLiteからPostgreSQLへのデータ移行

        Returns:
            bool: 移行成功時True、失敗時False
        """
        try:
            print("📥 SQLiteからPostgreSQLへのデータ移行を開始...")

            # SQLiteからデータを読み込み
            sqlite_conn = sqlite3.connect(self.base_backup_path)
            
            # 全データを取得
            df = pd.read_sql_query("SELECT * FROM price_data", sqlite_conn)
            sqlite_conn.close()

            print(f"📊 SQLiteから読み込み: {len(df):,}件")

            # PostgreSQLにデータを挿入
            migrated_count = 0
            for _, row in df.iterrows():
                try:
                    # PriceDataModelを作成
                    price_data = PriceDataModel(
                        currency_pair=row['currency_pair'],
                        timestamp=pd.to_datetime(row['timestamp']).tz_localize('Asia/Tokyo'),
                        data_timestamp=pd.to_datetime(row['data_timestamp']).tz_localize('Asia/Tokyo') if pd.notna(row['data_timestamp']) else None,
                        fetched_at=pd.to_datetime(row['fetched_at']).tz_localize('Asia/Tokyo') if pd.notna(row['fetched_at']) else None,
                        open_price=float(row['open_price']),
                        high_price=float(row['high_price']),
                        low_price=float(row['low_price']),
                        close_price=float(row['close_price']),
                        volume=int(row['volume']) if pd.notna(row['volume']) else None,
                        data_source=row['data_source'],
                    )

                    # PostgreSQLに保存
                    self.session.add(price_data)
                    migrated_count += 1

                    # バッチ処理（1000件ごとにコミット）
                    if migrated_count % 1000 == 0:
                        await self.session.commit()
                        print(f"   📈 {migrated_count:,}件移行完了")

                except Exception as e:
                    print(f"❌ データ移行エラー (行 {migrated_count}): {e}")
                    continue

            # 最終コミット
            await self.session.commit()
            print(f"✅ PostgreSQL移行完了: {migrated_count:,}件")

            # 移行結果の確認
            success = await self._verify_restoration()
            return success

        except Exception as e:
            print(f"❌ SQLiteからPostgreSQLへの移行エラー: {e}")
            return False

    async def _verify_restoration(self) -> bool:
        """
        復元の確認

        Returns:
            bool: 復元成功時True、失敗時False
        """
        try:
            # PostgreSQLからデータ件数を取得
            result = await self.session.execute(text("SELECT COUNT(*) FROM price_data"))
            count = result.scalar()

            print(f"📊 復元されたデータ件数: {count:,}件")

            # 各時間足の件数確認
            timeframe_counts = await self._get_data_counts()
            for timeframe, timeframe_count in timeframe_counts.items():
                print(f"   {timeframe}: {timeframe_count:,}件")

            return True

        except Exception as e:
            print(f"❌ 復元確認エラー: {e}")
            return False

    async def _get_data_counts(self) -> Dict[str, int]:
        """
        各時間足のデータ件数を取得

        Returns:
            Dict[str, int]: 時間足別のデータ件数
        """
        try:
            # 各時間足の件数を取得
            timeframes = {
                "5m": "yahoo_finance_5m",
                "1h": "yahoo_finance_1h",
                "4h": "yahoo_finance_4h",
                "1d": "yahoo_finance_1d",
            }

            counts = {}
            for timeframe, data_source in timeframes.items():
                result = await self.session.execute(
                    text("SELECT COUNT(*) FROM price_data WHERE data_source = :data_source"),
                    {"data_source": data_source}
                )
                count = result.scalar()
                counts[timeframe] = count

            return counts

        except Exception as e:
            print(f"❌ データ件数取得エラー: {e}")
            return {}

    async def initialize_session(self) -> bool:
        """
        セッションの初期化

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            self.session = await get_async_session()
            return True
        except Exception as e:
            print(f"❌ セッション初期化エラー: {e}")
            return False

    async def cleanup(self) -> None:
        """
        リソースのクリーンアップ
        """
        if self.session:
            await self.session.close()


async def main():
    """
    メイン実行関数
    """
    restorer = BaseDataRestorer()

    try:
        # 基盤データ復元実行
        success = await restorer.restore_base_data()

        if success:
            print("🎉 基盤データ復元が正常に完了しました")
        else:
            print("❌ 基盤データ復元に失敗しました")
            return 1

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1
    finally:
        await restorer.cleanup()

    return 0


if __name__ == "__main__":
    import asyncio

    exit_code = asyncio.run(main())
    exit(exit_code)
