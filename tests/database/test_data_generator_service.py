"""
パターン検出テスト用データ生成サービス

パターン検出器が期待する条件を満たすテストデータを生成する
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TestDataGeneratorService:
    """
    パターン検出テスト用データ生成サービス

    特徴:
    - パターン検出器が期待する条件を満たすデータを生成
    - 各時間軸（5m, 1h, 4h, 1d）のデータを生成
    - テクニカル指標も条件に合わせて生成
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session
        self.price_repo = PriceDataRepositoryImpl(session)
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)
        self.currency_pair = "USD/JPY"

    async def generate_pattern_1_test_data(self) -> bool:
        """
        パターン1（トレンド転換）用のテストデータを生成

        条件:
        - D1: RSI > 70, MACDデッドクロス
        - H4: RSI > 65, ボリンジャーバンド上端タッチ
        - H1: RSI > 60, モメンタム下降
        - M5: RSI > 55, 価格下落
        """
        try:
            logger.info("Generating Pattern 1 test data...")

            # 基準価格（USD/JPYの一般的な範囲）
            base_price = 150.0

            # 各時間軸のデータを生成
            await self._generate_5m_pattern_1_data(base_price)
            await self._generate_1h_pattern_1_data(base_price)
            await self._generate_4h_pattern_1_data(base_price)
            await self._generate_1d_pattern_1_data(base_price)

            # テクニカル指標を生成
            await self._generate_pattern_1_indicators()

            logger.info("Pattern 1 test data generated successfully")
            return True

        except Exception as e:
            logger.error(f"Error generating Pattern 1 test data: {e}")
            return False

    async def generate_pattern_2_test_data(self) -> bool:
        """
        パターン2（押し目・戻り売り）用のテストデータを生成

        条件:
        - D1: RSI 30-50, 上昇トレンド
        - H4: RSI 35-55, 押し目形成
        - H1: RSI 40-60, 戻り売り機会
        - M5: RSI 45-65, 短期調整
        """
        try:
            logger.info("Generating Pattern 2 test data...")

            base_price = 148.0

            await self._generate_5m_pattern_2_data(base_price)
            await self._generate_1h_pattern_2_data(base_price)
            await self._generate_4h_pattern_2_data(base_price)
            await self._generate_1d_pattern_2_data(base_price)

            await self._generate_pattern_2_indicators()

            logger.info("Pattern 2 test data generated successfully")
            return True

        except Exception as e:
            logger.error(f"Error generating Pattern 2 test data: {e}")
            return False

    async def _generate_5m_pattern_1_data(self, base_price: float):
        """5分足パターン1データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=6)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            # パターン1用の価格パターン（下降トレンド）
            price_change = random.uniform(-0.1, -0.05)  # 下降
            current_price += price_change

            # ボリンジャーバンド上端にタッチするように調整
            if current_time > end_time - timedelta(minutes=30):  # 最後の30分間
                current_price = 150.5  # ボリンジャーバンド上端

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.05),
                low_price=current_price - random.uniform(0, 0.05),
                close_price=current_price,
                volume=random.randint(1000, 5000),
                data_source="Test Pattern 1",
            )

            # 最後のデータポイントを確実にボリンジャーバンド上端に設定
            if current_time == end_time:
                price_data.close_price = 150.5
                price_data.high_price = 150.5
                price_data.low_price = 150.4
                price_data.open_price = 150.4

            await self.price_repo.save(price_data)
            current_time += timedelta(minutes=5)

    async def _generate_1h_pattern_1_data(self, base_price: float):
        """1時間足パターン1データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            price_change = random.uniform(-0.2, -0.1)
            current_price += price_change

            # ボリンジャーバンド上端にタッチするように調整
            if current_time > end_time - timedelta(hours=2):  # 最後の2時間
                current_price = 150.0  # H1のボリンジャーバンド上端

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.1),
                low_price=current_price - random.uniform(0, 0.1),
                close_price=current_price,
                volume=random.randint(5000, 15000),
                data_source="Test Pattern 1",
            )

            # 最後のデータポイントを確実にボリンジャーバンド上端に設定
            if current_time == end_time:
                price_data.close_price = 150.0
                price_data.high_price = 150.0
                price_data.low_price = 149.9
                price_data.open_price = 149.9

            await self.price_repo.save(price_data)
            current_time += timedelta(hours=1)

    async def _generate_4h_pattern_1_data(self, base_price: float):
        """4時間足パターン1データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            price_change = random.uniform(-0.5, -0.2)
            current_price += price_change

            # ボリンジャーバンド上端にタッチするように調整
            if current_time > end_time - timedelta(hours=8):  # 最後の8時間
                current_price = 149.5  # H4のボリンジャーバンド上端

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.2),
                low_price=current_price - random.uniform(0, 0.2),
                close_price=current_price,
                volume=random.randint(15000, 30000),
                data_source="Test Pattern 1",
            )

            # 最後のデータポイントを確実にボリンジャーバンド上端に設定
            if current_time == end_time:
                price_data.close_price = 149.5
                price_data.high_price = 149.5
                price_data.low_price = 149.4
                price_data.open_price = 149.4

            await self.price_repo.save(price_data)
            current_time += timedelta(hours=4)

    async def _generate_1d_pattern_1_data(self, base_price: float):
        """日足パターン1データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            price_change = random.uniform(-1.0, -0.5)
            current_price += price_change

            # ボリンジャーバンド上端にタッチするように調整
            if current_time > end_time - timedelta(days=1):  # 最後の1日
                current_price = 149.0  # D1のボリンジャーバンド上端

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.5),
                low_price=current_price - random.uniform(0, 0.5),
                close_price=current_price,
                volume=random.randint(50000, 100000),
                data_source="Test Pattern 1",
            )

            # 最後のデータポイントを確実にボリンジャーバンド上端に設定
            if current_time == end_time:
                price_data.close_price = 149.0
                price_data.high_price = 149.0
                price_data.low_price = 148.9
                price_data.open_price = 148.9

            await self.price_repo.save(price_data)
            current_time += timedelta(days=1)

    async def _generate_pattern_1_indicators(self):
        """パターン1用のテクニカル指標を生成"""
        current_time = datetime.now()

        # 5分足指標（パターン検出条件を満たすように調整）
        await self._save_indicator(
            "RSI", "M5", 75.0, current_time, {"current_value": 75.0}
        )
        # MACDデッドクロス（MACD < Signal）
        await self._save_indicator(
            "MACD",
            "M5",
            -0.1,
            current_time,
            {"macd": [-0.1] * 20, "signal": [0.05] * 20, "histogram": [-0.15] * 20},
        )
        # ボリンジャーバンド（価格が上端にタッチするように）
        await self._save_indicator(
            "BB",
            "M5",
            149.5,
            current_time,
            {"upper": [150.5] * 20, "middle": [149.5] * 20, "lower": [148.5] * 20},
        )

        # 1時間足指標（条件を満たすように調整）
        await self._save_indicator(
            "RSI", "H1", 71.0, current_time, {"current_value": 71.0}  # 70を超えるように
        )
        await self._save_indicator(
            "MACD",
            "H1",
            -0.2,
            current_time,
            {"macd": [-0.2] * 20, "signal": [0.1] * 20, "histogram": [-0.3] * 20},
        )
        await self._save_indicator(
            "BB",
            "H1",
            149.0,
            current_time,
            {"upper": [150.0] * 20, "middle": [149.0] * 20, "lower": [148.0] * 20},
        )

        # 4時間足指標（条件を満たすように調整）
        await self._save_indicator(
            "RSI", "H4", 71.0, current_time, {"current_value": 71.0}  # 70を超えるように
        )
        await self._save_indicator(
            "MACD",
            "H4",
            -0.3,
            current_time,
            {"macd": [-0.3] * 20, "signal": [0.15] * 20, "histogram": [-0.45] * 20},
        )
        await self._save_indicator(
            "BB",
            "H4",
            148.5,
            current_time,
            {"upper": [149.5] * 20, "middle": [148.5] * 20, "lower": [147.5] * 20},
        )

        # 日足指標
        await self._save_indicator(
            "RSI", "D1", 72.0, current_time, {"current_value": 72.0}
        )
        await self._save_indicator(
            "MACD",
            "D1",
            -0.5,
            current_time,
            {"macd": [-0.5] * 20, "signal": [0.2] * 20, "histogram": [-0.7] * 20},
        )
        await self._save_indicator(
            "BB",
            "D1",
            148.0,
            current_time,
            {"upper": [149.0] * 20, "middle": [148.0] * 20, "lower": [147.0] * 20},
        )

    async def _generate_5m_pattern_2_data(self, base_price: float):
        """5分足パターン2データ生成（押し目・戻り売り）"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=6)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            # パターン2用の価格パターン（上昇トレンド中の調整）
            if random.random() < 0.7:  # 70%の確率で上昇
                price_change = random.uniform(0.05, 0.1)
            else:  # 30%の確率で調整
                price_change = random.uniform(-0.05, 0)

            current_price += price_change

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.05),
                low_price=current_price - random.uniform(0, 0.05),
                close_price=current_price,
                volume=random.randint(1000, 5000),
                data_source="Test Pattern 2",
            )

            await self.price_repo.save(price_data)
            current_time += timedelta(minutes=5)

    async def _generate_1h_pattern_2_data(self, base_price: float):
        """1時間足パターン2データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            if random.random() < 0.6:
                price_change = random.uniform(0.1, 0.2)
            else:
                price_change = random.uniform(-0.1, 0.05)

            current_price += price_change

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.1),
                low_price=current_price - random.uniform(0, 0.1),
                close_price=current_price,
                volume=random.randint(5000, 15000),
                data_source="Test Pattern 2",
            )

            await self.price_repo.save(price_data)
            current_time += timedelta(hours=1)

    async def _generate_4h_pattern_2_data(self, base_price: float):
        """4時間足パターン2データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            if random.random() < 0.5:
                price_change = random.uniform(0.2, 0.5)
            else:
                price_change = random.uniform(-0.2, 0.1)

            current_price += price_change

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.2),
                low_price=current_price - random.uniform(0, 0.2),
                close_price=current_price,
                volume=random.randint(15000, 30000),
                data_source="Test Pattern 2",
            )

            await self.price_repo.save(price_data)
            current_time += timedelta(hours=4)

    async def _generate_1d_pattern_2_data(self, base_price: float):
        """日足パターン2データ生成"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)

        current_time = start_time
        current_price = base_price

        while current_time <= end_time:
            if random.random() < 0.4:
                price_change = random.uniform(0.5, 1.0)
            else:
                price_change = random.uniform(-0.5, 0.2)

            current_price += price_change

            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=current_time,
                open_price=current_price,
                high_price=current_price + random.uniform(0, 0.5),
                low_price=current_price - random.uniform(0, 0.5),
                close_price=current_price,
                volume=random.randint(50000, 100000),
                data_source="Test Pattern 2",
            )

            await self.price_repo.save(price_data)
            current_time += timedelta(days=1)

    async def _generate_pattern_2_indicators(self):
        """パターン2用のテクニカル指標を生成"""
        current_time = datetime.now()

        # 5分足指標（調整中）
        await self._save_indicator(
            "RSI", "M5", 45.0, current_time, {"current_value": 45.0}
        )
        await self._save_indicator(
            "MACD",
            "M5",
            0.05,
            current_time,
            {"macd": [0.05] * 20, "signal": [0.08] * 20, "histogram": [-0.03] * 20},
        )
        await self._save_indicator(
            "BB",
            "M5",
            148.5,
            current_time,
            {"upper": [149.0] * 20, "middle": [148.5] * 20, "lower": [148.0] * 20},
        )

        # 1時間足指標（戻り売り機会）
        await self._save_indicator(
            "RSI", "H1", 55.0, current_time, {"current_value": 55.0}
        )
        await self._save_indicator(
            "MACD",
            "H1",
            0.1,
            current_time,
            {"macd": [0.1] * 20, "signal": [0.12] * 20, "histogram": [-0.02] * 20},
        )
        await self._save_indicator(
            "BB",
            "H1",
            148.8,
            current_time,
            {"upper": [149.3] * 20, "middle": [148.8] * 20, "lower": [148.3] * 20},
        )

        # 4時間足指標（押し目形成）
        await self._save_indicator(
            "RSI", "H4", 40.0, current_time, {"current_value": 40.0}
        )
        await self._save_indicator(
            "MACD",
            "H4",
            0.15,
            current_time,
            {"macd": [0.15] * 20, "signal": [0.18] * 20, "histogram": [-0.03] * 20},
        )
        await self._save_indicator(
            "BB",
            "H4",
            148.2,
            current_time,
            {"upper": [148.7] * 20, "middle": [148.2] * 20, "lower": [147.7] * 20},
        )

        # 日足指標（上昇トレンド）
        await self._save_indicator(
            "RSI", "D1", 35.0, current_time, {"current_value": 35.0}
        )
        await self._save_indicator(
            "MACD",
            "D1",
            0.2,
            current_time,
            {"macd": [0.2] * 20, "signal": [0.25] * 20, "histogram": [-0.05] * 20},
        )
        await self._save_indicator(
            "BB",
            "D1",
            147.5,
            current_time,
            {"upper": [148.0] * 20, "middle": [147.5] * 20, "lower": [147.0] * 20},
        )

    async def _save_indicator(
        self,
        indicator_type: str,
        timeframe: str,
        value: float,
        timestamp: datetime,
        additional_data: Dict,
    ):
        """テクニカル指標を保存"""
        indicator = TechnicalIndicatorModel(
            currency_pair=self.currency_pair,
            indicator_type=indicator_type,
            timeframe=timeframe,
            value=value,
            timestamp=timestamp,
            additional_data=additional_data,
        )

        await self.indicator_repo.save(indicator)

    async def cleanup_test_data(self) -> bool:
        """
        テストデータをクリーンアップ

        Returns:
            bool: クリーンアップ成功時True
        """
        try:
            logger.info("Cleaning up test data...")

            # テストデータを削除
            await self.price_repo.delete_by_data_source("Test Pattern 1")
            await self.price_repo.delete_by_data_source("Test Pattern 2")

            logger.info("Test data cleanup completed")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up test data: {e}")
            return False
