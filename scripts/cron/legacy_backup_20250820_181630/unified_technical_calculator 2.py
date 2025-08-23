"""
Unified Technical Calculator
統合テクニカル指標計算システム

責任:
- TA-Libライブラリを使用した高性能テクニカル指標計算
- 既存システムの統合（TechnicalIndicatorService, TALibTechnicalIndicatorService, MultiTimeframeTechnicalIndicatorService）
- 差分更新システムとの連携
- マルチタイムフレーム対応

設計書参照:
- CLIデータベース初期化システム実装仕様書_2025.md
- CLIデータベース初期化システム実装計画書_Phase3_分析処理_2025.md
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import talib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)


class UnifiedTechnicalCalculator:
    """
    統合テクニカル指標計算クラス

    TA-Libライブラリを使用して高性能なテクニカル指標計算を行う機能を提供
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair: str = currency_pair
        self.session: Optional[AsyncSession] = None
        self.indicator_repo: Optional[TechnicalIndicatorRepositoryImpl] = None

        # TA-Lib設定
        self.indicators_config = {
            "RSI": {"period": 14, "overbought": 70, "oversold": 30},
            "MACD": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "BB": {"period": 20, "std_dev": 2},
            "SMA": {"periods": [5, 10, 20, 50, 100, 200]},
            "EMA": {"periods": [12, 26]},
            "STOCH": {"fastk_period": 14, "slowk_period": 3, "slowd_period": 3},
            "ATR": {"period": 14},
        }

        # 時間足設定
        self.timeframes = {
            "M5": {"description": "5分足", "days": 7},
            "H1": {"description": "1時間足", "days": 30},
            "H4": {"description": "4時間足", "days": 60},
            "D1": {"description": "日足", "days": 365},
        }

    async def calculate_all_indicators(self) -> Dict[str, int]:
        """
        全テクニカル指標を計算

        Returns:
            Dict[str, int]: 各時間足の計算件数
        """
        results = {}

        for timeframe in ["M5", "H1", "H4", "D1"]:
            print(f"📊 {timeframe}時間足のテクニカル指標計算を開始...")
            count = await self.calculate_timeframe_indicators(timeframe)
            results[timeframe] = count
            print(f"✅ {timeframe}時間足指標計算完了: {count}件")

        return results

    async def calculate_timeframe_indicators(self, timeframe: str) -> int:
        """
        特定時間足の指標を計算

        Args:
            timeframe: 時間足

        Returns:
            int: 計算件数
        """
        try:
            # 価格データを取得
            df = await self._get_price_data(timeframe)

            if df.empty:
                print(f"⚠️ {timeframe}の価格データがありません")
                return 0

            print(f"📈 {timeframe}データ取得: {len(df)}件")

            # 各指標を計算
            total_indicators = 0

            # RSI計算
            rsi_count = await self._calculate_and_save_rsi(df, timeframe)
            total_indicators += rsi_count

            # MACD計算（十分なデータがある場合）
            if len(df) >= 40:
                macd_count = await self._calculate_and_save_macd(df, timeframe)
                total_indicators += macd_count

            # ボリンジャーバンド計算
            bb_count = await self._calculate_and_save_bollinger_bands(df, timeframe)
            total_indicators += bb_count

            # 移動平均線計算
            ma_count = await self._calculate_and_save_moving_averages(df, timeframe)
            total_indicators += ma_count

            # ストキャスティクス計算
            stoch_count = await self._calculate_and_save_stochastic(df, timeframe)
            total_indicators += stoch_count

            # ATR計算
            atr_count = await self._calculate_and_save_atr(df, timeframe)
            total_indicators += atr_count

            return total_indicators

        except Exception as e:
            print(f"❌ {timeframe}指標計算エラー: {e}")
            return 0

    async def _get_price_data(self, timeframe: str) -> pd.DataFrame:
        """
        価格データを取得してDataFrameに変換

        Args:
            timeframe: 時間足

        Returns:
            pd.DataFrame: 価格データ
        """
        try:
            # 期間設定
            config = self.timeframes[timeframe]
            end_date = datetime.now()
            start_date = end_date - timedelta(days=config["days"])

            # データベースから価格データを取得
            query = (
                select(PriceDataModel)
                .where(
                    PriceDataModel.currency_pair == self.currency_pair,
                    PriceDataModel.timestamp >= start_date,
                    PriceDataModel.timestamp <= end_date,
                )
                .order_by(PriceDataModel.timestamp.asc())
            )

            result = await self.session.execute(query)
            price_data = result.scalars().all()

            if not price_data:
                return pd.DataFrame()

            # DataFrameに変換
            data = []
            for item in price_data:
                data.append(
                    {
                        "timestamp": item.timestamp,
                        "Open": float(item.open_price),
                        "High": float(item.high_price),
                        "Low": float(item.low_price),
                        "Close": float(item.close_price),
                        "Volume": int(item.volume) if item.volume else 1000000,
                    }
                )

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)

            return df

        except Exception as e:
            print(f"❌ 価格データ取得エラー: {e}")
            return pd.DataFrame()

    async def _calculate_and_save_rsi(self, df: pd.DataFrame, timeframe: str) -> int:
        """
        RSIを計算して保存

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            int: 保存件数
        """
        try:
            config = self.indicators_config["RSI"]

            # TA-LibでRSI計算
            rsi_values = talib.RSI(df["Close"].values, timeperiod=config["period"])

            # 有効な値のみを保存
            saved_count = 0
            for i, (timestamp, rsi_value) in enumerate(zip(df.index, rsi_values)):
                if not np.isnan(rsi_value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="RSI",
                        timeframe=timeframe,
                        value=float(rsi_value),
                        parameters={
                            "period": config["period"],
                            "source": "unified_technical_calculator",
                        },
                    )

                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            print(f"  📊 RSI計算完了: {saved_count}件")
            return saved_count

        except Exception as e:
            print(f"❌ RSI計算エラー: {e}")
            return 0

    async def _calculate_and_save_macd(self, df: pd.DataFrame, timeframe: str) -> int:
        """
        MACDを計算して保存

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            int: 保存件数
        """
        try:
            config = self.indicators_config["MACD"]

            # TA-LibでMACD計算
            macd, macd_signal, macd_hist = talib.MACD(
                df["Close"].values,
                fastperiod=config["fast_period"],
                slowperiod=config["slow_period"],
                signalperiod=config["signal_period"],
            )

            saved_count = 0

            # MACD線
            for i, (timestamp, value) in enumerate(zip(df.index, macd)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="MACD",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "fast": config["fast_period"],
                            "slow": config["slow_period"],
                            "signal": config["signal_period"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            # MACDシグナル線
            for i, (timestamp, value) in enumerate(zip(df.index, macd_signal)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="MACD",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "fast": config["fast_period"],
                            "slow": config["slow_period"],
                            "signal": config["signal_period"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            print(f"  📊 MACD計算完了: {saved_count}件")
            return saved_count

        except Exception as e:
            print(f"❌ MACD計算エラー: {e}")
            return 0

    async def _calculate_and_save_bollinger_bands(
        self, df: pd.DataFrame, timeframe: str
    ) -> int:
        """
        ボリンジャーバンドを計算して保存

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            int: 保存件数
        """
        try:
            config = self.indicators_config["BB"]

            # TA-Libでボリンジャーバンド計算
            upper, middle, lower = talib.BBANDS(
                df["Close"].values,
                timeperiod=config["period"],
                nbdevup=config["std_dev"],
                nbdevdn=config["std_dev"],
            )

            saved_count = 0

            # 上バンド
            for i, (timestamp, value) in enumerate(zip(df.index, upper)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="BB",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "period": config["period"],
                            "std": config["std_dev"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            # 中バンド（移動平均）
            for i, (timestamp, value) in enumerate(zip(df.index, middle)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="BB",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "period": config["period"],
                            "std": config["std_dev"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            # 下バンド
            for i, (timestamp, value) in enumerate(zip(df.index, lower)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="BB",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "period": config["period"],
                            "std": config["std_dev"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            print(f"  📊 ボリンジャーバンド計算完了: {saved_count}件")
            return saved_count

        except Exception as e:
            print(f"❌ ボリンジャーバンド計算エラー: {e}")
            return 0

    async def _calculate_and_save_moving_averages(
        self, df: pd.DataFrame, timeframe: str
    ) -> int:
        """
        移動平均線を計算して保存

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            int: 保存件数
        """
        try:
            sma_config = self.indicators_config["SMA"]
            ema_config = self.indicators_config["EMA"]

            saved_count = 0

            # SMA計算
            for period in sma_config["periods"]:
                sma_values = talib.SMA(df["Close"].values, timeperiod=period)

                for i, (timestamp, value) in enumerate(zip(df.index, sma_values)):
                    if not np.isnan(value):
                        indicator = TechnicalIndicatorModel(
                            currency_pair=self.currency_pair,
                            timestamp=timestamp,
                            indicator_type="SMA",
                            timeframe=timeframe,
                            value=float(value),
                            parameters={
                                "period": period,
                                "source": "unified_technical_calculator",
                            },
                        )
                        await self.indicator_repo.save(indicator)
                        saved_count += 1

            # EMA計算
            for period in ema_config["periods"]:
                ema_values = talib.EMA(df["Close"].values, timeperiod=period)

                for i, (timestamp, value) in enumerate(zip(df.index, ema_values)):
                    if not np.isnan(value):
                        indicator = TechnicalIndicatorModel(
                            currency_pair=self.currency_pair,
                            timestamp=timestamp,
                            indicator_type="EMA",
                            timeframe=timeframe,
                            value=float(value),
                            parameters={
                                "period": period,
                                "source": "unified_technical_calculator",
                            },
                        )
                        await self.indicator_repo.save(indicator)
                        saved_count += 1

            print(f"  📊 移動平均線計算完了: {saved_count}件")
            return saved_count

        except Exception as e:
            print(f"❌ 移動平均線計算エラー: {e}")
            return 0

    async def _calculate_and_save_stochastic(
        self, df: pd.DataFrame, timeframe: str
    ) -> int:
        """
        ストキャスティクスを計算して保存

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            int: 保存件数
        """
        try:
            config = self.indicators_config["STOCH"]

            # TA-Libでストキャスティクス計算
            slowk, slowd = talib.STOCH(
                df["High"].values,
                df["Low"].values,
                df["Close"].values,
                fastk_period=config["fastk_period"],
                slowk_period=config["slowk_period"],
                slowd_period=config["slowd_period"],
            )

            saved_count = 0

            # %K線
            for i, (timestamp, value) in enumerate(zip(df.index, slowk)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="STOCH",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "fastk": config["fastk_period"],
                            "slowk": config["slowk_period"],
                            "slowd": config["slowd_period"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            # %D線
            for i, (timestamp, value) in enumerate(zip(df.index, slowd)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="STOCH",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "fastk": config["fastk_period"],
                            "slowk": config["slowk_period"],
                            "slowd": config["slowd_period"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            print(f"  📊 ストキャスティクス計算完了: {saved_count}件")
            return saved_count

        except Exception as e:
            print(f"❌ ストキャスティクス計算エラー: {e}")
            return 0

    async def _calculate_and_save_atr(self, df: pd.DataFrame, timeframe: str) -> int:
        """
        ATRを計算して保存

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            int: 保存件数
        """
        try:
            config = self.indicators_config["ATR"]

            # TA-LibでATR計算
            atr_values = talib.ATR(
                df["High"].values,
                df["Low"].values,
                df["Close"].values,
                timeperiod=config["period"],
            )

            saved_count = 0

            for i, (timestamp, value) in enumerate(zip(df.index, atr_values)):
                if not np.isnan(value):
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="ATR",
                        timeframe=timeframe,
                        value=float(value),
                        parameters={
                            "period": config["period"],
                            "source": "unified_technical_calculator",
                        },
                    )
                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            print(f"  📊 ATR計算完了: {saved_count}件")
            return saved_count

        except Exception as e:
            print(f"❌ ATR計算エラー: {e}")
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
            self.indicator_repo = TechnicalIndicatorRepositoryImpl(self.session)

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
    calculator = UnifiedTechnicalCalculator()

    try:
        # 初期化
        if not await calculator.initialize():
            print("❌ 初期化に失敗しました")
            return 1

        # テクニカル指標計算実行
        results = await calculator.calculate_all_indicators()

        # 結果表示
        total_count = sum(results.values())
        print("\n📊 統合テクニカル指標計算結果:")
        for timeframe, count in results.items():
            print(f"   {timeframe}: {count}件")
        print(f"   合計: {total_count}件")

        if total_count > 0:
            print("🎉 統合テクニカル指標計算が正常に完了しました")
        else:
            print("ℹ️ 計算対象のデータがありませんでした")

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1
    finally:
        await calculator.cleanup()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
