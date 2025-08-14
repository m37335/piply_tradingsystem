"""
データ取得サービス

USD/JPY特化の5分おきデータ取得システム用のデータ取得サービス
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.data_fetch_history_model import (
    DataFetchHistoryModel,
)
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.data_fetch_history_repository_impl import (
    DataFetchHistoryRepositoryImpl,
)
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DataFetcherService:
    """
    USD/JPY特化データ取得サービス

    責任:
    - USD/JPYの5分間隔データ取得
    - データの正規化と保存
    - エラーハンドリングとリトライ
    - 取得履歴の管理

    特徴:
    - USD/JPY特化設計
    - 5分間隔データ取得
    - 重複データ防止
    - 包括的エラーハンドリング
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session
        self.yahoo_client = YahooFinanceClient()

        # リポジトリ初期化
        self.price_repo = PriceDataRepositoryImpl(session)
        self.history_repo = DataFetchHistoryRepositoryImpl(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"
        self.symbol = "USDJPY=X"

        # 取得設定
        self.interval_minutes = 5
        self.max_retries = 3
        self.retry_delay = 2.0

        logger.info(f"Initialized DataFetcherService for {self.currency_pair}")

    async def fetch_real_5m_data(self) -> Optional[PriceDataModel]:
        """
        実際の5分足データを取得（最新数件を処理）

        Returns:
            Optional[PriceDataModel]: 取得された価格データ
        """
        start_time = datetime.now()

        try:
            logger.info("📈 USD/JPY 履歴データ取得中...")

            # 1. Yahoo Financeからデータ取得
            data = await self.yahoo_client.get_historical_data(
                "USDJPY=X", period="1d", interval="5m"
            )

            if data is None or data.empty:
                logger.error("❌ Yahoo Financeからデータ取得失敗")
                return None

            logger.info(f"✅ USD/JPY: {len(data)}件のデータ取得")
            logger.info(f"   期間: {data.index[0]} ～ {data.index[-1]}")
            logger.info(f"   最新価格: {data.iloc[-1]['Close']}")

            # 2. 最新データの品質チェックと適切なデータ選択
            latest_row = data.iloc[-1]
            latest_timestamp = data.index[-1]

            # 最新データが異常かチェック（同じOHLC値）
            is_latest_abnormal = (
                latest_row["Open"]
                == latest_row["High"]
                == latest_row["Low"]
                == latest_row["Close"]
            )

            if is_latest_abnormal:
                logger.warning(f"⚠️ 最新データが異常（同じOHLC値）: {latest_timestamp}")
                logger.warning(f"   異常データ: O=H=L=C={latest_row['Open']}")

                # 一つ前のデータを使用
                if len(data) >= 2:
                    latest_row = data.iloc[-2]
                    latest_timestamp = data.index[-2]
                    logger.info(f"🔄 一つ前のデータを使用: {latest_timestamp}")
                else:
                    logger.error("❌ 代替データが利用できません")
                    return None
            else:
                logger.info(f"✅ 最新データは正常: {latest_timestamp}")

            logger.info(f"🎯 処理対象データ: {latest_timestamp}")
            logger.info(
                f"   生データ: O={latest_row['Open']}, H={latest_row['High']}, "
                f"L={latest_row['Low']}, C={latest_row['Close']}"
            )

            # タイムスタンプ処理
            data_timestamp = latest_timestamp
            if hasattr(data_timestamp, "tz_localize"):
                data_timestamp = data_timestamp.tz_localize(None)

            # 5分間隔のタイムスタンプ（秒以下を切り捨て）
            adjusted_timestamp = data_timestamp.replace(second=0, microsecond=0)
            fetched_at = datetime.now()

            logger.info(f"⏰ 処理中: {adjusted_timestamp}")
            logger.info(
                f"   OHLC: O={latest_row['Open']}, H={latest_row['High']}, "
                f"L={latest_row['Low']}, C={latest_row['Close']}"
            )

            # PriceDataModel作成
            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=adjusted_timestamp,
                data_timestamp=data_timestamp,
                fetched_at=fetched_at,
                open_price=float(latest_row["Open"]),
                high_price=float(latest_row["High"]),
                low_price=float(latest_row["Low"]),
                close_price=float(latest_row["Close"]),
                volume=(
                    int(latest_row["Volume"]) if latest_row["Volume"] > 0 else 1000000
                ),
                data_source="Yahoo Finance 5m Real",
            )

            # デバッグ: PriceDataModel作成後の価格データ
            logger.info(f"🔍 [DataFetcherService] PriceDataModel作成後:")
            logger.info(
                f"   OHLC: O={price_data.open_price}, H={price_data.high_price}, "
                f"L={price_data.low_price}, C={price_data.close_price}"
            )

            # バリデーション
            if not price_data.validate():
                logger.error(f"❌ データバリデーション失敗: {adjusted_timestamp}")
                return None

            # 重複チェック
            existing_data = await self.price_repo.find_by_timestamp(
                price_data.timestamp, self.currency_pair
            )

            if existing_data:
                logger.info(f"⚠️ 既存データ発見: {price_data.timestamp}")
                logger.info(
                    f"   既存: O={existing_data.open_price}, "
                    f"H={existing_data.high_price}, "
                    f"L={existing_data.low_price}, "
                    f"C={existing_data.close_price}"
                )
                logger.info(
                    f"   新規: O={price_data.open_price}, "
                    f"H={price_data.high_price}, "
                    f"L={price_data.low_price}, "
                    f"C={price_data.close_price}"
                )

                # 既存データを削除して新しいデータで上書き
                logger.warning("🔄 既存データを削除して新しいデータで上書き")
                await self.price_repo.delete(existing_data.id)

            # データベースに保存
            saved_data = await self.price_repo.save(price_data)

            # デバッグ: 保存後の価格データ
            logger.info(f"🔍 [DataFetcherService] データベース保存後:")
            logger.info(
                f"   OHLC: O={saved_data.open_price}, H={saved_data.high_price}, "
                f"L={saved_data.low_price}, C={saved_data.close_price}"
            )
            logger.info(f"✅ データ保存完了: {adjusted_timestamp}")

            # 8. 取得履歴を記録
            await self._record_fetch_history("success", datetime.now() - start_time, 1)

            return saved_data

        except Exception as e:
            logger.error(f"❌ 5分足データ取得エラー: {e}")
            await self._record_fetch_history(
                "error", datetime.now() - start_time, 0, str(e)
            )
            return None

    async def get_latest_price_data(self, limit: int = 1) -> List[PriceDataModel]:
        """
        最新の価格データを取得

        Args:
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[PriceDataModel]: 最新の価格データリスト
        """
        try:
            return await self.price_repo.find_latest(self.currency_pair, limit)
        except Exception as e:
            logger.error(f"Error getting latest price data: {e}")
            return []

    async def _record_fetch_history(
        self,
        status: str,
        response_time: timedelta,
        records_fetched: int,
        error_message: Optional[str] = None,
    ) -> Optional[DataFetchHistoryModel]:
        """
        取得履歴を記録

        Args:
            status: ステータス
            response_time: レスポンス時間
            records_fetched: 取得レコード数
            error_message: エラーメッセージ（デフォルト: None）

        Returns:
            Optional[DataFetchHistoryModel]: 記録された履歴
        """
        try:
            fetch_history = DataFetchHistoryModel(
                currency_pair=self.currency_pair,
                fetch_timestamp=datetime.now(),
                data_source="Yahoo Finance",
                fetch_type="price_data",
                success=status == "success",
                response_time_ms=int(response_time.total_seconds() * 1000),
                data_count=records_fetched,
                error_message=error_message,
            )

            return await self.history_repo.save(fetch_history)

        except Exception as e:
            logger.error(f"Error recording fetch history: {e}")
            return None

    async def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功の場合True
        """
        try:
            return await self.yahoo_client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
