#!/usr/bin/env python3
"""
パターン検出テスト用データセットアップスクリプト
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PatternTestDataSetup:
    """
    パターン検出テスト用データセットアップクラス
    """

    def __init__(self):
        self.database_url = "sqlite+aiosqlite:///./test_app.db"
        self.session = None

    async def setup_pattern_test_data(self):
        """
        パターン検出テスト用データをセットアップ
        """
        try:
            logger.info("Setting up pattern detection test data...")

            # エンジンを作成
            engine = create_async_engine(
                self.database_url, echo=False, connect_args={"check_same_thread": False}
            )

            async with engine.begin() as conn:
                # 1. パターン検出に必要な価格データを追加
                await self._add_pattern_price_data(conn)

                # 2. パターン検出に必要なテクニカル指標を追加
                await self._add_pattern_indicators(conn)

                # 3. パターン検出履歴を追加
                await self._add_pattern_detection_history(conn)

            logger.info("Pattern detection test data setup completed")

        except Exception as e:
            logger.error(f"Pattern test data setup failed: {e}")
            raise

    async def _add_pattern_price_data(self, conn):
        """
        パターン検出用の価格データを追加
        """
        logger.info("Adding pattern detection price data...")

        # トレンド転換パターン用の価格データ
        base_time = datetime.now() - timedelta(hours=24)
        base_price = 150.0

        # 上昇トレンド → 下降トレンドの転換パターン
        for i in range(50):
            timestamp = base_time + timedelta(minutes=5 * i)

            if i < 30:  # 上昇トレンド
                price_change = i * 0.01
            else:  # 下降トレンド
                price_change = 30 * 0.01 - (i - 30) * 0.02

            await conn.execute(
                text(
                    """
                    INSERT INTO price_data
                    (id, currency_pair, timestamp, open_price, high_price, low_price, close_price, volume, data_source, created_at, updated_at, uuid, version)
                    VALUES
                    (:id, :currency_pair, :timestamp, :open_price, :high_price, :low_price, :close_price, :volume, :data_source, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                """
                ),
                {
                    "id": 1000 + i,
                    "currency_pair": "USD/JPY",
                    "timestamp": timestamp,
                    "open_price": base_price + price_change,
                    "high_price": base_price + price_change + 0.005,
                    "low_price": base_price + price_change - 0.005,
                    "close_price": base_price + price_change + 0.002,
                    "volume": 1000000 + (i * 1000),
                    "data_source": "Pattern Test",
                    "uuid": f"pattern-price-{i}",
                    "version": 1,
                },
            )

    async def _add_pattern_indicators(self, conn):
        """
        パターン検出用のテクニカル指標を追加
        """
        logger.info("Adding pattern detection indicators...")

        base_time = datetime.now() - timedelta(hours=24)

        # RSIの極値パターン（オーバーブought/オーバーソールド）
        for i in range(50):
            timestamp = base_time + timedelta(minutes=5 * i)

            if i < 25:  # オーバーブought
                rsi_value = 70 + (i * 0.5)
            else:  # オーバーソールド
                rsi_value = 70 - ((i - 25) * 1.5)

            # パターン検出用の極値データを追加
            if i == 20:  # オーバーブought条件
                rsi_value = 75.5
            elif i == 45:  # オーバーソールド条件
                rsi_value = 25.3

            # RSI指標
            await conn.execute(
                text(
                    """
                    INSERT INTO technical_indicators
                    (id, currency_pair, timestamp, indicator_type, timeframe, value, additional_data, parameters, created_at, updated_at, uuid, version)
                    VALUES
                    (:id, :currency_pair, :timestamp, :indicator_type, :timeframe, :value, :additional_data, :parameters, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                """
                ),
                {
                    "id": 2000 + i,
                    "currency_pair": "USD/JPY",
                    "timestamp": timestamp,
                    "indicator_type": "RSI",
                    "timeframe": "5m",
                    "value": rsi_value,
                    "additional_data": json.dumps({"period": 14}),
                    "parameters": json.dumps({"period": 14}),
                    "uuid": f"pattern-rsi-{i}",
                    "version": 1,
                },
            )

            # MACD指標（トレンド転換シグナル）
            if i < 25:
                macd_value = 0.001 + (i * 0.0001)
            else:
                macd_value = 0.0035 - ((i - 25) * 0.0001)

            await conn.execute(
                text(
                    """
                    INSERT INTO technical_indicators
                    (id, currency_pair, timestamp, indicator_type, timeframe, value, additional_data, parameters, created_at, updated_at, uuid, version)
                    VALUES
                    (:id, :currency_pair, :timestamp, :indicator_type, :timeframe, :value, :additional_data, :parameters, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                """
                ),
                {
                    "id": 2050 + i,
                    "currency_pair": "USD/JPY",
                    "timestamp": timestamp,
                    "indicator_type": "MACD",
                    "timeframe": "5m",
                    "value": macd_value,
                    "additional_data": json.dumps(
                        {
                            "macd_line": macd_value,
                            "signal_line": macd_value * 0.8,
                            "histogram": macd_value * 0.2,
                        }
                    ),
                    "parameters": json.dumps(
                        {"fast_period": 12, "slow_period": 26, "signal_period": 9}
                    ),
                    "uuid": f"pattern-macd-{i}",
                    "version": 1,
                },
            )

    async def _add_pattern_detection_history(self, conn):
        """
        パターン検出履歴を追加
        """
        logger.info("Adding pattern detection history...")

        base_time = datetime.now() - timedelta(hours=6)

        # 過去のパターン検出履歴
        for i in range(10):
            timestamp = base_time + timedelta(minutes=30 * i)

            await conn.execute(
                text(
                    """
                    INSERT INTO pattern_detections
                    (id, currency_pair, timestamp, pattern_type, pattern_name, confidence_score, direction, detection_data, indicator_data, notification_sent, notification_sent_at, notification_message, created_at, updated_at, uuid, version)
                    VALUES
                    (:id, :currency_pair, :timestamp, :pattern_type, :pattern_name, :confidence_score, :direction, :detection_data, :indicator_data, :notification_sent, :notification_sent_at, :notification_message, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                    """
                ),
                {
                    "id": 3000 + i,
                    "currency_pair": "USD/JPY",
                    "timestamp": timestamp,
                    "pattern_type": f"Pattern_{i % 6 + 1}",
                    "pattern_name": f"Pattern {i + 1}",
                    "confidence_score": 0.7 + (i * 0.02),
                    "direction": "BUY" if i % 2 == 0 else "SELL",
                    "detection_data": json.dumps(
                        {"condition1": True, "condition2": False}
                    ),
                    "indicator_data": json.dumps({"rsi": 65, "macd": 0.001}),
                    "notification_sent": False,
                    "notification_sent_at": None,
                    "notification_message": f"Pattern {i + 1} detected with confidence {0.7 + (i * 0.02):.2f}",
                    "uuid": f"pattern-detection-{i}",
                    "version": 1,
                },
            )


async def main():
    """
    メイン関数
    """
    logger.info("Starting pattern detection test data setup...")

    # 環境変数の設定
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

    setup = PatternTestDataSetup()

    try:
        await setup.setup_pattern_test_data()
        logger.info("Pattern detection test data setup completed successfully!")

    except Exception as e:
        logger.error(f"Pattern detection test data setup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
