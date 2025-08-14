"""
Data Loader Module
データ取得処理機能

責任:
- Yahoo Finance APIからの個別データ取得
- マルチタイムフレーム対応
- データ品質検証
- データベースへの保存
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class DataLoader:
    """データ取得処理クラス"""

    def __init__(self):
        self.currency_pair: str = "USD/JPY"
        self.session: Optional[AsyncSession] = None
        self.engine = None
        self.yahoo_client: YahooFinanceClient = YahooFinanceClient()
        self.price_repo: Optional[PriceDataRepositoryImpl] = None

        # 個別取得設定（Yahoo Finance API制限に基づく）
        # 時間足設定
        self.timeframe_configs = {
            "5m": {
                "period": "60d",  # 60日分（API制限）
                "interval": "5m",
                "description": "5分足",
                "max_records": 10000,
            },
            "1h": {
                "period": "60d",  # 60日分（API制限）
                "interval": "1h",
                "description": "1時間足",
                "max_records": 10000,
            },
            "4h": {
                "period": "365d",  # 365日分（API制限）
                "interval": "4h",
                "description": "4時間足",
                "max_records": 10000,
            },
            "1d": {
                "period": "365d",  # 365日分（API制限）
                "interval": "1d",
                "description": "日足",
                "max_records": 10000,
            },
        }

    async def load_multi_timeframe_data(self) -> int:
        """
        全時間足のデータを個別に取得

        Returns:
            int: 取得したデータ総数
        """
        try:
            # ヘッダーセクション
            print("\n" + "=" * 80)
            print("🚀 マルチタイムフレームデータ取得を開始します")
            print("=" * 80)

            if not await self.initialize():
                print("❌ 初期化に失敗しました")
                return 0

            total_records = 0
            all_errors = []

            # 各時間足を個別に取得
            for timeframe, config in self.timeframe_configs.items():
                # 時間足開始時のセクション区切り
                print(f"\n{'─'*60}")
                print(f"📈 {config['description']}データ取得開始")
                print(f"{'─'*60}")

                records, errors = await self._fetch_and_save_timeframe(
                    timeframe, config
                )
                total_records += records
                all_errors.extend(errors)

                # 時間足完了時のプログレスバー表示
                with tqdm(
                    total=1,
                    desc=f"✅ {config['description']}完了 ({records}件)",
                    unit="件",
                    ncols=80,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} "
                    "[{elapsed}<{remaining}, {rate_fmt}]",
                ) as pbar:
                    pbar.update(1)

            # 結果表示セクション
            print(f"\n{'='*80}")
            print("🎉 全時間足データ取得完了")
            print(f"{'='*80}")

            # 統計情報
            print(f"📊 取得データ総数: {total_records:,}件")

            # エラーがある場合はまとめて表示
            if all_errors:
                print(f"\n⚠️ エラー情報 ({len(all_errors)}件)")
                print(f"{'─'*40}")
                for i, error in enumerate(all_errors[:5], 1):  # 最初の5件のみ表示
                    print(f"{i:2d}. {error}")
                if len(all_errors) > 5:
                    print(f"    ... 他{len(all_errors) - 5}件")
                print(f"{'─'*40}")
            else:
                print("✅ エラーなし")

            return total_records

        except Exception as e:
            print(f"\n{'!'*80}")
            print("❌ マルチタイムフレームデータ取得中にエラーが発生しました")
            print(f"{'!'*80}")
            print(f"エラー詳細: {e}")
            return 0

        finally:
            print(f"\n{'─'*60}")
            print("🧹 リソースクリーンアップ中...")
            await self.cleanup()
            print("✅ クリーンアップ完了")
            print(f"{'─'*60}")

    async def verify_data_quality(self, timeframe: str) -> bool:
        """
        データ品質の確認

        Args:
            timeframe: 時間足

        Returns:
            bool: 品質確認結果
        """
        try:
            if not self.price_repo:
                print("❌ リポジトリが初期化されていません")
                return False

            # 最新のデータを取得して確認
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)  # 1日分を確認

            data = await self.price_repo.find_by_date_range(
                start_date, end_date, self.currency_pair
            )

            if not data:
                print(f"⚠️ {timeframe}: データが存在しません")
                return False

            print(f"✅ {timeframe}: {len(data)}件のデータを確認")
            return True

        except Exception as e:
            print(f"❌ データ品質確認中にエラーが発生しました: {e}")
            return False

    async def _fetch_and_save_timeframe(
        self, timeframe: str, config: dict, pbar=None
    ) -> tuple[int, list[str]]:
        """
        特定時間足のデータを取得して保存

        Args:
            timeframe: 時間足
            config: 設定情報

        Returns:
            tuple[int, list[str]]: (保存したデータ数, エラーリスト)
        """
        try:
            # Yahoo Finance APIからのデータ取得
            print("📡 Yahoo Finance APIからデータを取得中...")
            print(f"   通貨ペア: {self.currency_pair}")
            print(f"   期間: {config['period']}, 間隔: {config['interval']}")

            df = await self.yahoo_client.get_historical_data(
                self.currency_pair, config["period"], config["interval"]
            )

            if df is None or df.empty:
                error_msg = f"❌ {timeframe}: データが取得できませんでした"
                return 0, [error_msg]

            # データ取得結果の表示
            print(f"✅ データ取得完了: {len(df):,}件")
            if len(df) > 0:
                start_date = df.index[0].strftime("%Y-%m-%d %H:%M:%S")
                end_date = df.index[-1].strftime("%Y-%m-%d %H:%M:%S")
                latest_price = df.iloc[-1]["Close"]
                print(f"   期間: {start_date} ～ {end_date}")
                print(f"   最新価格: {latest_price:.4f}")

            # データの検証
            print("🔍 データ検証中...")
            if not await self._validate_timeframe_data(df, timeframe):
                error_msg = f"❌ {timeframe}: データ検証に失敗しました"
                return 0, [error_msg]
            print("✅ データ検証完了")

            # データベースへの保存
            print("💾 データベースに保存中...")
            saved_count, errors = await self._save_dataframe_to_db(
                df, timeframe, config["description"]
            )

            return saved_count, errors

        except Exception as e:
            error_msg = f"❌ {timeframe}データ処理中にエラーが発生しました: {e}"
            return 0, [error_msg]

    async def _validate_timeframe_data(
        self, data: pd.DataFrame, timeframe: str
    ) -> bool:
        """
        時間足データの検証

        Args:
            data: 検証するデータ
            timeframe: 時間足

        Returns:
            bool: 検証結果
        """
        try:
            # DataFrame形式の検証
            if not isinstance(data, pd.DataFrame):
                return False

            # 必須カラムの確認
            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            missing_columns = [
                col for col in required_columns if col not in data.columns
            ]
            if missing_columns:
                return False

            # データ型の検証
            for col in required_columns:
                numeric_check = pd.api.types.is_numeric_dtype(data[col])
                if not numeric_check:
                    return False

            # 欠損値の確認
            null_counts = data[required_columns].isnull().sum()
            if null_counts.sum() > 0:
                # 欠損値があっても処理を続行（警告のみ）
                pass

            # データ件数の確認
            if len(data) == 0:
                return False

            return True

        except Exception:
            return False

    async def _save_dataframe_to_db(
        self, df: pd.DataFrame, timeframe: str, description: str
    ) -> tuple[int, list[str]]:
        """
        DataFrameをデータベースに保存

        Args:
            df: 保存するデータ
            timeframe: 時間足

        Returns:
            tuple[int, list[str]]: (保存したデータ数, エラーリスト)
        """
        try:
            if not self.price_repo:
                error_msg = "❌ リポジトリが初期化されていません"
                return 0, [error_msg]

            saved_count = 0
            errors = []

            # データ保存の進捗を表示
            total_rows = len(df)

            # プログレスバーでデータ保存を表示
            with tqdm(
                total=total_rows,
                desc=f"📊 {description}データ保存中...",
                unit="件",
                ncols=80,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            ) as pbar:

                # 重複チェックとデータ保存
                for i, (timestamp, row) in enumerate(df.iterrows()):
                    try:
                        # タイムスタンプをdatetimeオブジェクトに変換
                        if hasattr(timestamp, "to_pydatetime"):
                            dt_timestamp = timestamp.to_pydatetime()
                        else:
                            dt_timestamp = timestamp

                        # 重複チェックはリポジトリのsaveメソッドで行うため、ここではスキップ
                        # 既存データがある場合はリポジトリ側で適切に処理される

                        # 取引量の処理
                        volume = int(float(row["Volume"])) if row["Volume"] > 0 else 0

                        # 日足のみ土日を除外（営業日のみ）
                        if timeframe == "1d":
                            weekday = dt_timestamp.weekday()
                            if weekday >= 5:  # 5=土曜日, 6=日曜日
                                continue

                        # PriceDataModelを作成
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
                            data_source=f"yahoo_finance_{timeframe}",
                        )

                        # 保存
                        await self.price_repo.save(price_data)
                        saved_count += 1

                        # プログレスバーを更新
                        pbar.update(1)

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
                            error_msg = (
                                f"⚠️ データ品質エラー (timestamp: {timestamp}): {e}"
                            )
                            errors.append(error_msg)
                            continue

                        # 重複エラー以外のエラーのみ記録
                        if "UNIQUE constraint failed" not in str(e):
                            error_msg = (
                                f"⚠️ データ保存エラー (timestamp: {timestamp}): {e}"
                            )
                            errors.append(error_msg)

                # プログレスバーは自動的に100%で完了

            return saved_count, errors

        except Exception as e:
            error_msg = f"❌ データベース保存中にエラーが発生しました: {e}"
            return 0, [error_msg]

    async def initialize(self) -> bool:
        """
        初期化

        Returns:
            bool: 成功/失敗
        """
        try:
            print("🔌 データローダーを初期化しています")
            print("─" * 40)

            # ログレベルを一時的に変更してリポジトリのログ出力を抑制
            repo_logger = logging.getLogger(
                "src.infrastructure.database.repositories.price_data_repository_impl"
            )
            repo_logger.setLevel(logging.ERROR)  # WARNINGも抑制

            # 他の関連ロガーも抑制
            logging.getLogger("exchange_analytics.infrastructure").setLevel(
                logging.ERROR
            )
            logging.getLogger("src.infrastructure").setLevel(logging.ERROR)

            # データベース接続の初期化
            default_url = "sqlite+aiosqlite:///data/exchange_analytics.db"
            database_url = os.getenv("DATABASE_URL", default_url)

            self.engine = create_async_engine(
                database_url, echo=False, pool_pre_ping=True
            )

            async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            self.session = async_session()

            # リポジトリの初期化
            self.price_repo = PriceDataRepositoryImpl(self.session)

            print("✅ データローダーの初期化が完了しました")
            return True

        except Exception as e:
            print(f"❌ 初期化中にエラーが発生しました: {e}")
            return False

    async def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self.session:
                await self.session.close()
                print("🔒 セッションをクローズしました")

            if self.engine:
                await self.engine.dispose()
                print("🗑️ エンジンを破棄しました")

        except Exception as e:
            print(f"❌ リソースクリーンアップ中にエラーが発生しました: {e}")


async def main():
    """メイン実行関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    loader = DataLoader()

    try:
        # マルチタイムフレームデータ取得を実行
        total_records = await loader.load_multi_timeframe_data()

        if total_records > 0:
            print(f"✅ データ取得が完了しました: 合計{total_records}件")
            return 0
        else:
            print("❌ データ取得に失敗しました")
            return 1

    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
