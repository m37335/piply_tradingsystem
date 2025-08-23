#!/usr/bin/env python3
"""
Base Aggregator - 時間足集計の基底クラス

責任:
- 共通の集計ロジック
- データベース接続管理
- エラーハンドリング
- ログ出力
"""

import logging
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pytz
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/base_aggregator.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class AggregationError(Exception):
    """集計処理エラー"""
    pass


class InsufficientDataError(AggregationError):
    """データ不足エラー"""
    pass


class DatabaseError(AggregationError):
    """データベースエラー"""
    pass


class BaseAggregator(ABC):
    """
    時間足集計の基底クラス

    責任:
    - 共通の集計ロジック
    - データベース接続管理
    - エラーハンドリング
    - ログ出力
    """

    def __init__(self, timeframe: str, data_source: str):
        self.timeframe = timeframe  # "1h", "4h", "1d"
        self.data_source = data_source  # "yahoo_finance_1h_aggregated"
        self.currency_pair = "USD/JPY"
        self.db_url = None
        self.engine = None
        self.session_factory = None
        self.session = None
        self.price_repo = None

    async def initialize_database(self):
        """データベース接続を初期化"""
        try:
            # 環境変数からデータベースURLを取得
            self.db_url = os.getenv("DATABASE_URL")
            if not self.db_url:
                raise ValueError("DATABASE_URL環境変数が設定されていません")

            # データベースエンジンを作成
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # セッションを作成
            self.session = self.session_factory()
            self.price_repo = PriceDataRepositoryImpl(self.session)

            logger.info(f"✅ {self.timeframe}集計用データベース接続を初期化しました")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise DatabaseError(f"データベース初期化エラー: {e}")

    async def cleanup(self):
        """リソースをクリーンアップ"""
        try:
            if self.session:
                await self.session.close()
            if self.engine:
                await self.engine.dispose()
            logger.info(f"✅ {self.timeframe}集計用リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")

    @abstractmethod
    async def get_aggregation_period(self) -> Tuple[datetime, datetime]:
        """集計期間を取得（抽象メソッド）"""
        raise NotImplementedError

    async def get_five_min_data(self, start_time: datetime, end_time: datetime) -> List[PriceDataModel]:
        """
        指定期間の5分足データを取得

        Args:
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            List[PriceDataModel]: 5分足データのリスト
        """
        try:
            # 5分足データを取得（yahoo_finance_5mデータソース）
            five_min_data = await self.price_repo.find_by_date_range(
                start_time, end_time, self.currency_pair
            )
            
            # データソースでフィルタリング（5分足データ）
            five_min_data = [data for data in five_min_data if data.data_source in ["yahoo_finance_5m", "yahoo_finance_5m_differential", "yahoo_finance_5m_continuous"]]
            
            logger.info(f"📊 {len(five_min_data)}件の5分足データを取得しました")
            return five_min_data

        except Exception as e:
            logger.error(f"❌ 5分足データ取得エラー: {e}")
            raise DatabaseError(f"5分足データ取得エラー: {e}")

    async def calculate_ohlcv(self, five_min_data: List[PriceDataModel]) -> PriceDataModel:
        """
        OHLCV計算

        Args:
            five_min_data: 5分足データのリスト

        Returns:
            PriceDataModel: 集計されたOHLCVデータ
        """
        if not five_min_data:
            raise InsufficientDataError("集計対象データがありません")

        # データをタイムスタンプ順にソート
        sorted_data = sorted(five_min_data, key=lambda x: x.timestamp)

        # OHLCV計算
        open_price = sorted_data[0].open_price  # 最初の始値
        high_price = max(d.high_price for d in sorted_data)  # 最高値
        low_price = min(d.low_price for d in sorted_data)    # 最低値
        close_price = sorted_data[-1].close_price  # 最後の終値
        volume = sum(d.volume or 0 for d in sorted_data)     # 取引量合計

        # 集計タイムスタンプ（期間の開始時刻）
        aggregated_timestamp = sorted_data[0].timestamp.replace(
            minute=0, second=0, microsecond=0
        )

        return PriceDataModel(
            currency_pair=self.currency_pair,
            timestamp=aggregated_timestamp,
            data_timestamp=aggregated_timestamp,
            fetched_at=datetime.now(pytz.timezone("Asia/Tokyo")),
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            data_source=self.data_source
        )

    async def check_duplicate(self, timestamp: datetime) -> Optional[PriceDataModel]:
        """
        重複データチェック

        Args:
            timestamp: チェック対象のタイムスタンプ

        Returns:
            Optional[PriceDataModel]: 既存データ（存在する場合）
        """
        try:
            existing = await self.price_repo.find_by_timestamp_and_source(
                timestamp, self.currency_pair, self.data_source
            )
            return existing
        except Exception as e:
            logger.error(f"❌ 重複チェックエラー: {e}")
            return None

    async def save_aggregated_data(self, aggregated_data: PriceDataModel) -> PriceDataModel:
        """
        集計データを保存

        Args:
            aggregated_data: 保存する集計データ

        Returns:
            PriceDataModel: 保存されたデータ
        """
        try:
            # リポジトリのsaveメソッドを使用（重複チェック含む）
            saved_data = await self.price_repo.save(aggregated_data)
            logger.info(f"💾 {self.timeframe}集計データを保存しました: {saved_data.timestamp}")
            return saved_data
        except Exception as e:
            logger.error(f"❌ データ保存エラー: {e}")
            raise DatabaseError(f"データ保存エラー: {e}")

    async def aggregate_and_save(self):
        """
        集計と保存を実行（抽象メソッド）
        """
        raise NotImplementedError
