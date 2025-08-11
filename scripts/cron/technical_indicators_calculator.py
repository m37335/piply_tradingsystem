#!/usr/bin/env python3
"""
Technical Indicators Calculator Script
AI分析レポートの方法を参考にしたテクニカル指標計算スクリプト

責任:
- データベースから価格データを取得
- AI分析レポートと同じ方法でテクニカル指標を計算
- 計算結果をデータベースに保存
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.append("/app")

from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.database.connection import get_async_session
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


class TechnicalIndicatorsCalculator:
    """AI分析レポート方式のテクニカル指標計算器"""

    def __init__(self):
        self.session = None
        self.price_repo = None
        self.indicator_repo = None
        self.technical_analyzer = TechnicalIndicatorsAnalyzer()
        self.currency_pair = "USD/JPY"

    async def initialize(self):
        """初期化"""
        try:
            # SQLite環境を強制設定
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

            self.session = await get_async_session()
            self.price_repo = PriceDataRepositoryImpl(self.session)
            self.indicator_repo = TechnicalIndicatorRepositoryImpl(self.session)

            logger.info("Technical Indicators Calculator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            import traceback

            traceback.print_exc()
            raise

    async def calculate_all_indicators(self):
        """全テクニカル指標を計算"""
        try:
            logger.info("=== AI分析レポート方式でテクニカル指標計算開始 ===")

            # 複数期間のデータを取得
            timeframes = {
                "M5": {"days": 7, "description": "5分足"},
                "H1": {"days": 30, "description": "1時間足"},
                "H4": {"days": 60, "description": "4時間足"},
                "D1": {"days": 365, "description": "日足"},
            }

            total_indicators = 0

            for timeframe, config in timeframes.items():
                logger.info(f"📊 {config['description']}テクニカル指標計算中...")

                # 期間設定
                end_date = datetime.now()
                start_date = end_date - timedelta(days=config["days"])

                # 価格データを取得
                price_data = await self.price_repo.find_by_date_range(
                    start_date, end_date, self.currency_pair, 10000
                )

                if len(price_data) < 20:  # 最小データ数チェック
                    logger.warning(f"  ⚠️ {timeframe}データ不足: {len(price_data)}件")
                    continue

                # DataFrameに変換
                df = self._convert_to_dataframe(price_data)
                if df.empty:
                    logger.warning(f"  ⚠️ {timeframe}DataFrame変換失敗")
                    continue

                logger.info(f"  ✅ {timeframe}データ取得: {len(df)}件")

                # 各指標を計算
                timeframe_indicators = 0

                # RSI計算
                rsi_count = await self._calculate_and_save_rsi(df, timeframe)
                timeframe_indicators += rsi_count

                # MACD計算（十分なデータがある場合）
                if len(df) >= 40:
                    macd_count = await self._calculate_and_save_macd(df, timeframe)
                    timeframe_indicators += macd_count

                # ボリンジャーバンド計算
                bb_count = await self._calculate_and_save_bollinger_bands(df, timeframe)
                timeframe_indicators += bb_count

                total_indicators += timeframe_indicators
                logger.info(f"  ✅ {timeframe}完了: {timeframe_indicators}件の指標計算")

            logger.info(f"🎉 全テクニカル指標計算完了: 合計{total_indicators}件")
            return total_indicators

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            import traceback

            traceback.print_exc()
            return 0

    def _convert_to_dataframe(self, price_data):
        """価格データをDataFrameに変換"""
        try:
            import pandas as pd

            data = []
            for item in price_data:
                data.append(
                    {
                        "Open": float(item.open_price),
                        "High": float(item.high_price),
                        "Low": float(item.low_price),
                        "Close": float(item.close_price),
                        "Volume": int(item.volume) if item.volume else 1000000,
                        "timestamp": item.timestamp,
                    }
                )

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            return df

        except Exception as e:
            logger.error(f"Error converting to DataFrame: {e}")
            return pd.DataFrame()

    async def _calculate_and_save_rsi(self, df, timeframe):
        """RSIを計算して保存"""
        try:
            # AI分析レポート方式でRSI計算
            rsi_result = self.technical_analyzer.calculate_rsi(df, timeframe)

            if "error" in rsi_result:
                logger.warning(f"  ⚠️ RSI計算エラー: {rsi_result['error']}")
                return 0

            current_value = rsi_result.get("current_value")
            if current_value is None:
                logger.warning(f"  ⚠️ RSI値が取得できませんでした")
                return 0

            # 最新のタイムスタンプを取得
            latest_timestamp = df.index[-1] if not df.empty else datetime.now()

            # テクニカル指標モデル作成
            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="RSI",
                timeframe=timeframe,
                value=float(current_value),
                parameters={"period": 14},
            )

            if indicator.validate():
                # 重複チェック
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    latest_timestamp, "RSI", timeframe, self.currency_pair
                )

                if not existing:
                    await self.indicator_repo.save(indicator)
                    logger.info(f"  💾 RSI保存: {current_value:.2f}")
                    return 1
                else:
                    logger.debug(f"  ⏭️ RSI重複スキップ")
                    return 0
            else:
                logger.warning(f"  ⚠️ RSIバリデーション失敗")
                return 0

        except Exception as e:
            logger.error(f"  ❌ RSI計算・保存エラー: {e}")
            return 0

    async def _calculate_and_save_macd(self, df, timeframe):
        """MACDを計算して保存"""
        try:
            # AI分析レポート方式でMACD計算
            macd_result = self.technical_analyzer.calculate_macd(df, timeframe)

            if "error" in macd_result:
                logger.warning(f"  ⚠️ MACD計算エラー: {macd_result['error']}")
                return 0

            macd_line = macd_result.get("macd_line")
            signal_line = macd_result.get("signal_line")

            if macd_line is None or signal_line is None:
                logger.warning(f"  ⚠️ MACD値が取得できませんでした")
                return 0

            # 最新のタイムスタンプを取得
            latest_timestamp = df.index[-1] if not df.empty else datetime.now()

            # MACD Lineを保存
            macd_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="MACD",
                timeframe=timeframe,
                value=float(macd_line),
                parameters={"type": "macd_line", "fast": 12, "slow": 26, "signal": 9},
            )

            # Signal Lineを保存
            signal_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="MACD_SIGNAL",
                timeframe=timeframe,
                value=float(signal_line),
                parameters={"type": "signal_line", "fast": 12, "slow": 26, "signal": 9},
            )

            saved_count = 0

            # MACD Line保存
            if macd_indicator.validate():
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    latest_timestamp, "MACD", timeframe, self.currency_pair
                )
                if not existing:
                    await self.indicator_repo.save(macd_indicator)
                    saved_count += 1

            # Signal Line保存
            if signal_indicator.validate():
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    latest_timestamp, "MACD_SIGNAL", timeframe, self.currency_pair
                )
                if not existing:
                    await self.indicator_repo.save(signal_indicator)
                    saved_count += 1

            if saved_count > 0:
                logger.info(f"  💾 MACD保存: {macd_line:.4f}, {signal_line:.4f}")

            return saved_count

        except Exception as e:
            logger.error(f"  ❌ MACD計算・保存エラー: {e}")
            return 0

    async def _calculate_and_save_bollinger_bands(self, df, timeframe):
        """ボリンジャーバンドを計算して保存"""
        try:
            # AI分析レポート方式でボリンジャーバンド計算
            bb_result = self.technical_analyzer.calculate_bollinger_bands(df, timeframe)

            if "error" in bb_result:
                logger.warning(
                    f"  ⚠️ ボリンジャーバンド計算エラー: {bb_result['error']}"
                )
                return 0

            upper_band = bb_result.get("upper_band")
            middle_band = bb_result.get("middle_band")
            lower_band = bb_result.get("lower_band")

            if upper_band is None or middle_band is None or lower_band is None:
                logger.warning(f"  ⚠️ ボリンジャーバンド値が取得できませんでした")
                return 0

            # 最新のタイムスタンプを取得
            latest_timestamp = df.index[-1] if not df.empty else datetime.now()

            saved_count = 0

            # Upper Band保存
            upper_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="BB_UPPER",
                timeframe=timeframe,
                value=float(upper_band),
                parameters={"type": "upper_band", "period": 20, "std_dev": 2},
            )

            # Middle Band保存
            middle_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="BB_MIDDLE",
                timeframe=timeframe,
                value=float(middle_band),
                parameters={"type": "middle_band", "period": 20, "std_dev": 2},
            )

            # Lower Band保存
            lower_indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=latest_timestamp,
                indicator_type="BB_LOWER",
                timeframe=timeframe,
                value=float(lower_band),
                parameters={"type": "lower_band", "period": 20, "std_dev": 2},
            )

            # 各バンドを保存
            for indicator, band_type in [
                (upper_indicator, "Upper"),
                (middle_indicator, "Middle"),
                (lower_indicator, "Lower"),
            ]:
                if indicator.validate():
                    existing = await self.indicator_repo.find_by_timestamp_and_type(
                        latest_timestamp,
                        indicator.indicator_type,
                        timeframe,
                        self.currency_pair,
                    )
                    if not existing:
                        await self.indicator_repo.save(indicator)
                        saved_count += 1

            if saved_count > 0:
                logger.info(
                    f"  💾 ボリンジャーバンド保存: {upper_band:.2f}, {middle_band:.2f}, {lower_band:.2f}"
                )

            return saved_count

        except Exception as e:
            logger.error(f"  ❌ ボリンジャーバンド計算・保存エラー: {e}")
            return 0

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン関数"""
    logger.info("Starting AI analysis report style technical indicators calculation...")

    # 環境変数チェック
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

    calculator = TechnicalIndicatorsCalculator()

    try:
        await calculator.initialize()

        # テクニカル指標計算
        indicator_count = await calculator.calculate_all_indicators()

        if indicator_count > 0:
            logger.info(f"✅ テクニカル指標計算完了: {indicator_count}件")
            logger.info("🎉 AI分析レポート方式のテクニカル指標計算完了！")
        else:
            logger.warning("⚠️ テクニカル指標計算に失敗しました")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Technical indicators calculation error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        await calculator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
