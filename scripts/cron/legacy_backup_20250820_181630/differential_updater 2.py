"""
Differential Updater
差分データ更新機能

責任:
- 基盤データの最新タイムスタンプ以降の差分データ取得
- 差分期間の計算
- 差分データの保存と検証

設計書参照:
- CLIデータベース初期化システム実装仕様書_2025.md
- CLIデータベース初期化システム実装計画書_Phase3_分析処理_2025.md
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


class DifferentialUpdater:
    """
    差分データ更新クラス

    基盤データの最新タイムスタンプ以降の差分データのみを取得する機能を提供
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair: str = currency_pair
        self.session: Optional[AsyncSession] = None
        self.price_repo: Optional[PriceDataRepositoryImpl] = None
        self.yahoo_client: YahooFinanceClient = YahooFinanceClient()

        # 基盤データの最終更新日時（Phase 2完了時）
        self.base_timestamps: Dict[str, datetime] = {
            "5m": datetime(2025, 8, 14, 9, 15, 0),
            "1h": datetime(2025, 8, 14, 9, 0, 0),
            "4h": datetime(2025, 8, 14, 8, 0, 0),
            "1d": datetime(2025, 8, 14, 8, 0, 0),
        }

    async def update_all_timeframes(self) -> Dict[str, int]:
        """
        全時間足の差分データを更新

        Returns:
            Dict[str, int]: 各時間足の更新件数
        """
        results = {}

        for timeframe in ["5m", "1h", "4h", "1d"]:
            print(f"🔄 {timeframe}時間足の差分更新を開始...")
            count = await self.update_timeframe(timeframe)
            results[timeframe] = count
            print(f"✅ {timeframe}時間足更新完了: {count}件")

        return results

    async def update_timeframe(self, timeframe: str) -> int:
        """
        特定時間足の差分データを更新

        Args:
            timeframe: 時間足（"5m", "1h", "4h", "1d"）

        Returns:
            int: 更新件数
        """
        try:
            # 差分期間の計算
            start_date, end_date = await self._calculate_differential_period(timeframe)

            if not start_date or not end_date:
                print(f"ℹ️ {timeframe}の差分データはありません")
                return 0

            # 差分データの取得
            count = await self._fetch_differential_data(timeframe, start_date, end_date)

            return count

        except Exception as e:
            print(f"❌ {timeframe}差分更新エラー: {e}")
            return 0

    async def _calculate_differential_period(
        self, timeframe: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        差分期間を計算

        Args:
            timeframe: 時間足

        Returns:
            Tuple[Optional[str], Optional[str]]: (開始日, 終了日) または (None, None)
        """
        # データベース内の最新タイムスタンプを取得
        latest_timestamp = await self._get_latest_timestamp(timeframe)

        if not latest_timestamp:
            print(f"⚠️ {timeframe}の既存データが見つかりません")
            return None, None

        # 現在時刻（日本時間）
        import pytz

        jst = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jst)

        # 差分期間の計算（重複を避けるため次のタイムスタンプから）
        if timeframe == "5m":
            start_date = latest_timestamp + timedelta(minutes=5)
        elif timeframe == "1h":
            start_date = latest_timestamp + timedelta(hours=1)
        elif timeframe == "4h":
            start_date = latest_timestamp + timedelta(hours=4)
        else:  # 1d
            start_date = latest_timestamp + timedelta(days=1)

        end_date = current_time

        # デバッグ情報を表示
        print(f"   📅 最新タイムスタンプ: {latest_timestamp}")
        print(f"   📅 計算開始日: {start_date}")
        print(f"   📅 現在時刻: {end_date}")
        print(f"   ⏱️ 差分時間: {end_date - start_date}")

        # 差分が存在するかチェック
        if start_date >= end_date:
            print(f"ℹ️ {timeframe}の差分データはありません")
            return None, None

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    async def _get_latest_timestamp(self, timeframe: str) -> Optional[datetime]:
        """
        データベース内の最新タイムスタンプを取得

        Args:
            timeframe: 時間足

        Returns:
            Optional[datetime]: 最新タイムスタンプ
        """
        try:
            # 特定時間足の最新タイムスタンプを取得
            query = (
                select(PriceDataModel.timestamp)
                .where(PriceDataModel.data_source.like(f"%{timeframe}%"))
                .order_by(PriceDataModel.timestamp.desc())
                .limit(1)
            )

            result = await self.session.execute(query)
            latest = result.scalar_one_or_none()

            # タイムゾーン情報を追加
            if latest:
                import pytz

                jst = pytz.timezone("Asia/Tokyo")
                latest = jst.localize(latest)

            return latest

        except Exception as e:
            print(f"❌ 最新タイムスタンプ取得エラー: {e}")
            return None

    async def _fetch_differential_data(
        self, timeframe: str, start_date: str, end_date: str
    ) -> int:
        """
        差分データを取得して保存

        Args:
            timeframe: 時間足
            start_date: 開始日
            end_date: 終了日

        Returns:
            int: 取得件数
        """
        try:
            print(f"📥 {timeframe}差分データ取得中: {start_date} ～ {end_date}")

            # Yahoo Financeからデータを取得
            # 差分期間を計算して適切な期間を設定
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days_diff = (end_dt - start_dt).days

            # 期間を設定（最大7日分）
            period = f"{min(days_diff + 1, 7)}d"

            df = await self.yahoo_client.get_historical_data(
                currency_pair=self.currency_pair,
                period=period,
                interval=timeframe,
            )

            if df.empty:
                print(f"ℹ️ {timeframe}の差分データは空でした")
                return 0

            # データソース名を設定
            data_source = f"yahoo_finance_{timeframe}_differential"

            # データベースに保存
            count = await self._save_dataframe_to_db(df, data_source)

            print(f"✅ {timeframe}差分データ保存完了: {count}件")
            return count

        except Exception as e:
            print(f"❌ {timeframe}差分データ取得エラー: {e}")
            return 0

    async def _save_dataframe_to_db(self, df: pd.DataFrame, data_source: str) -> int:
        """
        DataFrameをデータベースに保存

        Args:
            df: 保存するDataFrame
            data_source: データソース名

        Returns:
            int: 保存件数
        """
        try:
            if not self.price_repo:
                print("❌ リポジトリが初期化されていません")
                return 0

            saved_count = 0
            errors = []

            # データ保存の進捗を表示
            total_rows = len(df)
            print(f"📊 {data_source}データ保存中... ({total_rows}件)")

            # 重複チェックとデータ保存
            for i, (timestamp, row) in enumerate(df.iterrows()):
                try:
                    # タイムスタンプをdatetimeオブジェクトに変換
                    if hasattr(timestamp, "to_pydatetime"):
                        dt_timestamp = timestamp.to_pydatetime()
                    else:
                        dt_timestamp = timestamp

                    # 取引量の処理
                    volume = int(float(row["Volume"])) if row["Volume"] > 0 else 0

                    # PriceDataModelを作成
                    from src.infrastructure.database.models.price_data_model import (
                        PriceDataModel,
                    )

                    price_data = PriceDataModel(
                        currency_pair=self.currency_pair,
                        timestamp=dt_timestamp,
                        data_timestamp=dt_timestamp,  # データの実際のタイムスタンプ
                        fetched_at=datetime.utcnow(),  # データ取得実行時刻
                        open_price=float(row["Open"]),
                        high_price=float(row["High"]),
                        low_price=float(row["Low"]),
                        close_price=float(row["Close"]),
                        volume=volume,
                        data_source=data_source,
                    )

                    # 保存
                    await self.price_repo.save(price_data)
                    saved_count += 1

                except Exception as e:
                    # セッションロールバックエラーの場合はセッションをリセット
                    if "Session's transaction has been rolled back" in str(e):
                        if self.session:
                            await self.session.rollback()
                            await self.session.begin()
                        continue

                    # Invalid price dataエラーの場合はスキップ（データ品質問題）
                    if "Invalid price data" in str(e):
                        # エラーを記録するが処理は続行
                        error_msg = f"⚠️ データ品質エラー (timestamp: {timestamp}): {e}"
                        errors.append(error_msg)
                        continue

                    # 重複エラー以外のエラーのみ記録
                    if "UNIQUE constraint failed" not in str(e):
                        error_msg = f"⚠️ データ保存エラー (timestamp: {timestamp}): {e}"
                        errors.append(error_msg)

            # エラーがある場合は表示
            if errors:
                print(f"⚠️ {len(errors)}件のエラーが発生しました")
                for error in errors[:5]:  # 最初の5件のみ表示
                    print(f"   {error}")

            return saved_count

        except Exception as e:
            print(f"❌ データ保存エラー: {e}")
            return 0

    async def initialize(self) -> bool:
        """
        初期化処理

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            # セッションの初期化
            self.session = await get_async_session()

            # リポジトリの初期化
            self.price_repo = PriceDataRepositoryImpl(self.session)

            return True

        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
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
    updater = DifferentialUpdater()

    try:
        # 初期化
        if not await updater.initialize():
            print("❌ 初期化に失敗しました")
            return 1

        # 差分更新実行
        results = await updater.update_all_timeframes()

        # 結果表示
        total_count = sum(results.values())
        print("\n📊 差分更新結果:")
        for timeframe, count in results.items():
            print(f"   {timeframe}: {count}件")
        print(f"   合計: {total_count}件")

        if total_count > 0:
            print("🎉 差分更新が正常に完了しました")
        else:
            print("ℹ️ 差分データはありませんでした")

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1
    finally:
        await updater.cleanup()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
