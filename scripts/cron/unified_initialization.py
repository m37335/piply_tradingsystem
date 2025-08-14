#!/usr/bin/env python3
"""
Unified Initialization Script
統合初期化スクリプト

責任:
- データベース初期化
- マルチタイムフレーム初回データ取得
- AI分析レポート方式のテクニカル指標計算
- システム全体の初期化を一つのフローで実行
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.append("/app")

from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.database.connection import (
    db_manager,
    get_async_session,
    init_database,
)
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
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class UnifiedInitializer:
    """統合初期化器"""

    def __init__(self):
        self.currency_pair = "USD/JPY"
        self.session = None
        self.yahoo_client = YahooFinanceClient()
        self.price_repo = None
        self.indicator_repo = None
        self.technical_analyzer = TechnicalIndicatorsAnalyzer()

        # タイムフレーム設定（移動平均線200期間に基づく最適化）
        self.timeframes = {
            "M5": {
                "period": "7d",
                "interval": "5m",
                "description": "5分足",
                "days": 7,
            },  # 7日分（200期間×5分=1000分+安全マージン）
            "H1": {
                "period": "30d",
                "interval": "1h",
                "description": "1時間足",
                "days": 30,  # 30日分（200期間×1時間=200時間+安全マージン）
            },
            "H4": {
                "period": "60d",
                "interval": "4h",
                "description": "4時間足",
                "days": 60,  # 60日分（200期間×4時間=800時間+安全マージン）
            },
            "D1": {
                "period": "365d",
                "interval": "1d",
                "description": "日足",
                "days": 365,  # 365日分（200期間×1日=200日+安全マージン）
            },
        }

    async def initialize_database(self):
        """データベース初期化"""
        try:
            logger.info("=== データベース初期化開始 ===")

            # SQLite環境を強制設定
            os.environ["DATABASE_URL"] = (
                "sqlite+aiosqlite:///data/exchange_analytics.db"
            )

            # 既存のデータベースファイルを削除
            db_path = "/app/data/exchange_analytics.db"
            if os.path.exists(db_path):
                os.remove(db_path)
                logger.info("✅ 既存データベースファイル削除完了")

            # データベース初期化
            await init_database("sqlite+aiosqlite:///data/exchange_analytics.db")
            logger.info("✅ データベース接続初期化完了")

            # テーブル作成
            await db_manager.create_tables()
            logger.info("✅ データベーステーブル作成完了")

            # セッション初期化
            self.session = await get_async_session()
            self.price_repo = PriceDataRepositoryImpl(self.session)
            self.indicator_repo = TechnicalIndicatorRepositoryImpl(self.session)

            logger.info("🎉 データベース初期化完了")
            return True

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            return False

    async def load_multi_timeframe_data(self):
        """マルチタイムフレームデータ取得"""
        try:
            logger.info("=== マルチタイムフレーム初回データ取得開始 ===")

            total_saved = 0

            for timeframe, config in self.timeframes.items():
                logger.info(f"📊 {config['description']}データ取得中...")

                saved_count = await self._load_timeframe_data(
                    timeframe, config["period"], config["interval"]
                )

                total_saved += saved_count
                logger.info(f"✅ {config['description']}: {saved_count}件保存")

            logger.info(f"🎉 全タイムフレーム完了: 合計{total_saved}件")
            return total_saved

        except Exception as e:
            logger.error(f"❌ マルチタイムフレームデータ取得エラー: {e}")
            return 0

    async def _load_timeframe_data(
        self, timeframe: str, period: str, interval: str
    ) -> int:
        """特定タイムフレームのデータを読み込み"""
        try:
            logger.info(f"  📈 {self.currency_pair} {timeframe}履歴データ取得中...")
            logger.info(f"    期間: {period}, 間隔: {interval}")

            # Yahoo Financeから履歴データ取得
            df = await self.yahoo_client.get_historical_data(
                self.currency_pair, period, interval
            )

            if df is None or df.empty:
                logger.warning(f"  ❌ {timeframe}データが取得できませんでした")
                return 0

            logger.info(f"  ✅ {timeframe}: {len(df)}件のデータ取得")
            logger.info(f"    期間: {df.index[0]} ～ {df.index[-1]}")
            logger.info(f"    最新価格: {df['Close'].iloc[-1]:.4f}")

            # データベースに保存
            saved_count = 0
            for timestamp, row in df.iterrows():
                try:
                    # タイムスタンプの処理
                    if hasattr(timestamp, "to_pydatetime"):
                        dt = timestamp.to_pydatetime()
                    else:
                        dt = datetime.now()

                    # 価格データモデル作成
                    price_data = PriceDataModel(
                        currency_pair=self.currency_pair,
                        timestamp=dt,
                        open_price=float(row["Open"]),
                        high_price=float(row["High"]),
                        low_price=float(row["Low"]),
                        close_price=float(row["Close"]),
                        volume=int(row["Volume"]) if row["Volume"] > 0 else 1000000,
                        data_source=f"Yahoo Finance ({timeframe})",
                    )

                    # データバリデーション
                    if not price_data.validate():
                        logger.debug(
                            f"    ⚠️ 無効なデータをスキップ: {timestamp} - O:{row['Open']}, H:{row['High']}, L:{row['Low']}, C:{row['Close']}"
                        )
                        continue

                    # 重複チェック
                    existing = await self.price_repo.find_by_timestamp(
                        dt, self.currency_pair
                    )
                    if existing:
                        continue

                    # 保存
                    await self.price_repo.save(price_data)
                    saved_count += 1

                    # 100件ごとにログ出力
                    if saved_count % 100 == 0:
                        logger.info(f"    💾 保存済み: {saved_count}件")

                except Exception as e:
                    logger.warning(f"    ⚠️ 保存エラー (timestamp: {timestamp}): {e}")
                    continue

            logger.info(f"  ✅ {timeframe}完了: {saved_count}件保存")
            return saved_count

        except Exception as e:
            logger.error(f"  ❌ {timeframe}データ取得エラー: {e}")
            return 0

    async def calculate_technical_indicators(self):
        """TA-Lib統合テクニカル指標計算"""
        try:
            logger.info("=== TA-Lib統合テクニカル指標計算開始 ===")

            # TA-Libテクニカル指標計算スクリプトを実行
            import subprocess
            import sys
            from pathlib import Path

            script_path = (
                Path(__file__).parent / "talib_technical_indicators_calculator.py"
            )

            try:
                result = subprocess.run(
                    [sys.executable, str(script_path), "all"],
                    capture_output=True,
                    text=True,
                    cwd="/app",
                )

                if result.returncode == 0:
                    logger.info("✅ TA-Libテクニカル指標計算完了")
                    # 計算された指標数を取得
                    import sqlite3

                    conn = sqlite3.connect("/app/data/exchange_analytics.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM technical_indicators")
                    total_indicators = cursor.fetchone()[0]
                    conn.close()

                    logger.info(
                        f"🎉 TA-Lib統合テクニカル指標計算完了: 合計{total_indicators}件"
                    )
                    return total_indicators
                else:
                    logger.error(f"❌ TA-Libテクニカル指標計算エラー: {result.stderr}")
                    return 0

            except Exception as e:
                logger.error(f"❌ TA-Libスクリプト実行エラー: {e}")
                return 0

        except Exception as e:
            logger.error(f"❌ TA-Lib統合テクニカル指標計算エラー: {e}")
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
            logger.error(f"❌ DataFrame変換エラー: {e}")
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

    async def run_unified_initialization(self):
        """統合初期化を実行"""
        try:
            logger.info("🚀 === 統合初期化開始 ===")
            start_time = datetime.now()

            # 1. データベース初期化
            if not await self.initialize_database():
                logger.error("❌ データベース初期化に失敗しました")
                return False

            # 2. マルチタイムフレームデータ取得
            data_count = await self.load_multi_timeframe_data()
            if data_count == 0:
                logger.error("❌ マルチタイムフレームデータ取得に失敗しました")
                return False

            # 3. テクニカル指標計算
            indicator_count = await self.calculate_technical_indicators()
            if indicator_count == 0:
                logger.warning("⚠️ テクニカル指標計算に失敗しました")

            # 完了時間計算
            end_time = datetime.now()
            duration = end_time - start_time

            logger.info("🎉 === 統合初期化完了 ===")
            logger.info(f"📊 取得データ: {data_count}件")
            logger.info(f"📈 テクニカル指標: {indicator_count}件")
            logger.info(f"⏱️ 実行時間: {duration}")

            return True

        except Exception as e:
            logger.error(f"❌ 統合初期化エラー: {e}")
            return False

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン関数"""
    logger.info("Starting unified initialization...")

    # 環境変数チェック
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"

    initializer = UnifiedInitializer()

    try:
        # 統合初期化実行
        success = await initializer.run_unified_initialization()

        if success:
            logger.info("🎉 統合初期化が正常に完了しました！")
            logger.info("✅ システムが本格稼働の準備が整いました")
        else:
            logger.error("❌ 統合初期化に失敗しました")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Unified initialization error: {e}")
        sys.exit(1)
    finally:
        await initializer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
