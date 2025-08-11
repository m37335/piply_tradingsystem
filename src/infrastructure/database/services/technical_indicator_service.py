"""
テクニカル指標計算サービス

USD/JPY特化の5分おきデータ取得システム用のテクニカル指標計算サービス
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
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


class TechnicalIndicatorService:
    """
    テクニカル指標計算サービス

    責任:
    - テクニカル指標の計算
    - 計算結果の保存
    - 複数タイムフレーム対応
    - 指標パラメータ管理

    特徴:
    - USD/JPY特化設計
    - 複数タイムフレーム対応
    - 高精度計算
    - 包括的エラーハンドリング
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session

        # リポジトリ初期化
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)
        self.price_repo = PriceDataRepositoryImpl(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"

        # デフォルトパラメータ
        self.default_params = {
            "RSI": {"period": 14},
            "MACD": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "BB": {"period": 20, "std_dev": 2},
            "SMA": {"period": 20},
            "EMA": {"period": 20},
        }

        logger.info(f"Initialized TechnicalIndicatorService for {self.currency_pair}")

    async def calculate_rsi(
        self,
        timeframe: str = "5m",
        period: int = 14,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        RSI（相対力指数）を計算

        Args:
            timeframe: タイムフレーム（デフォルト: 5m）
            period: 期間（デフォルト: 14）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: 計算されたRSI指標リスト
        """
        try:
            logger.info(f"Calculating RSI for {self.currency_pair} (period={period})")

            # 価格データを取得
            price_data = await self._get_price_data_for_calculation(
                start_date, end_date, period + 10
            )

            if len(price_data) < period + 1:
                logger.warning(
                    f"Insufficient price data for RSI calculation: {len(price_data)}"
                )
                return []

            # RSI計算
            rsi_values = self._calculate_rsi_values(price_data, period)

            # 指標モデルを作成
            indicators = []
            for i, (timestamp, rsi_value) in enumerate(rsi_values):
                if rsi_value is not None:
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="RSI",
                        timeframe=timeframe,
                        value=rsi_value,
                        parameters={"period": period},
                    )

                    if indicator.validate():
                        indicators.append(indicator)

            # 重複チェックと保存
            saved_indicators = await self._save_indicators_with_duplicate_check(
                indicators
            )

            logger.info(
                f"Successfully calculated and saved {len(saved_indicators)} RSI values"
            )
            return saved_indicators

        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return []

    async def calculate_macd(
        self,
        timeframe: str = "5m",
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        MACDを計算

        Args:
            timeframe: タイムフレーム（デフォルト: 5m）
            fast_period: 短期EMA期間（デフォルト: 12）
            slow_period: 長期EMA期間（デフォルト: 26）
            signal_period: シグナル期間（デフォルト: 9）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: 計算されたMACD指標リスト
        """
        try:
            logger.info(
                f"Calculating MACD for {self.currency_pair} "
                f"(fast={fast_period}, slow={slow_period}, signal={signal_period})"
            )

            # 価格データを取得
            price_data = await self._get_price_data_for_calculation(
                start_date, end_date, slow_period + signal_period + 10
            )

            if len(price_data) < slow_period + signal_period:
                logger.warning(
                    f"Insufficient price data for MACD calculation: {len(price_data)}"
                )
                return []

            # MACD計算
            macd_values = self._calculate_macd_values(
                price_data, fast_period, slow_period, signal_period
            )

            # 指標モデルを作成
            indicators = []
            for timestamp, macd_line, signal_line, histogram in macd_values:
                if macd_line is not None:
                    # MACD Line
                    macd_indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="MACD",
                        timeframe=timeframe,
                        value=macd_line,
                        parameters={
                            "fast_period": fast_period,
                            "slow_period": slow_period,
                            "signal_period": signal_period,
                            "type": "macd_line",
                        },
                    )

                    if macd_indicator.validate():
                        indicators.append(macd_indicator)

                    # Signal Line
                    signal_indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="MACD_SIGNAL",
                        timeframe=timeframe,
                        value=signal_line,
                        parameters={
                            "fast_period": fast_period,
                            "slow_period": slow_period,
                            "signal_period": signal_period,
                            "type": "signal_line",
                        },
                    )

                    if signal_indicator.validate():
                        indicators.append(signal_indicator)

                    # Histogram
                    histogram_indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="MACD_HISTOGRAM",
                        timeframe=timeframe,
                        value=histogram,
                        parameters={
                            "fast_period": fast_period,
                            "slow_period": slow_period,
                            "signal_period": signal_period,
                            "type": "histogram",
                        },
                    )

                    if histogram_indicator.validate():
                        indicators.append(histogram_indicator)

            # 重複チェックと保存
            saved_indicators = await self._save_indicators_with_duplicate_check(
                indicators
            )

            logger.info(
                f"Successfully calculated and saved {len(saved_indicators)} MACD values"
            )
            return saved_indicators

        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return []

    async def calculate_bollinger_bands(
        self,
        timeframe: str = "5m",
        period: int = 20,
        std_dev: float = 2.0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        ボリンジャーバンドを計算

        Args:
            timeframe: タイムフレーム（デフォルト: 5m）
            period: 期間（デフォルト: 20）
            std_dev: 標準偏差（デフォルト: 2.0）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: 計算されたボリンジャーバンド指標リスト
        """
        try:
            logger.info(
                f"Calculating Bollinger Bands for {self.currency_pair} "
                f"(period={period}, std_dev={std_dev})"
            )

            # 価格データを取得
            price_data = await self._get_price_data_for_calculation(
                start_date, end_date, period + 10
            )

            if len(price_data) < period:
                logger.warning(
                    f"Insufficient price data for BB calculation: {len(price_data)}"
                )
                return []

            # ボリンジャーバンド計算
            bb_values = self._calculate_bollinger_bands_values(
                price_data, period, std_dev
            )

            # 指標モデルを作成
            indicators = []
            for timestamp, upper, middle, lower in bb_values:
                if upper is not None:
                    # Upper Band
                    upper_indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="BB_UPPER",
                        timeframe=timeframe,
                        value=upper,
                        parameters={"period": period, "std_dev": std_dev},
                    )

                    if upper_indicator.validate():
                        indicators.append(upper_indicator)

                    # Middle Band (SMA)
                    middle_indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="BB_MIDDLE",
                        timeframe=timeframe,
                        value=middle,
                        parameters={"period": period, "std_dev": std_dev},
                    )

                    if middle_indicator.validate():
                        indicators.append(middle_indicator)

                    # Lower Band
                    lower_indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="BB_LOWER",
                        timeframe=timeframe,
                        value=lower,
                        parameters={"period": period, "std_dev": std_dev},
                    )

                    if lower_indicator.validate():
                        indicators.append(lower_indicator)

            # 重複チェックと保存
            saved_indicators = await self._save_indicators_with_duplicate_check(
                indicators
            )

            logger.info(
                f"Successfully calculated and saved {len(saved_indicators)} BB values"
            )
            return saved_indicators

        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return []

    async def calculate_moving_averages(
        self,
        timeframe: str = "5m",
        period: int = 20,
        ma_type: str = "SMA",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        移動平均を計算

        Args:
            timeframe: タイムフレーム（デフォルト: 5m）
            period: 期間（デフォルト: 20）
            ma_type: 移動平均タイプ（SMA/EMA）（デフォルト: SMA）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: 計算された移動平均指標リスト
        """
        try:
            logger.info(
                f"Calculating {ma_type} for {self.currency_pair} (period={period})"
            )

            # 価格データを取得
            price_data = await self._get_price_data_for_calculation(
                start_date, end_date, period + 10
            )

            if len(price_data) < period:
                logger.warning(
                    f"Insufficient price data for MA calculation: {len(price_data)}"
                )
                return []

            # 移動平均計算
            if ma_type.upper() == "SMA":
                ma_values = self._calculate_sma_values(price_data, period)
            elif ma_type.upper() == "EMA":
                ma_values = self._calculate_ema_values(price_data, period)
            else:
                raise ValueError(f"Unsupported moving average type: {ma_type}")

            # 指標モデルを作成
            indicators = []
            for timestamp, ma_value in ma_values:
                if ma_value is not None:
                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type=ma_type.upper(),
                        timeframe=timeframe,
                        value=ma_value,
                        parameters={"period": period},
                    )

                    if indicator.validate():
                        indicators.append(indicator)

            # 重複チェックと保存
            saved_indicators = await self._save_indicators_with_duplicate_check(
                indicators
            )

            logger.info(
                f"Successfully calculated and saved {len(saved_indicators)} {ma_type} values"
            )
            return saved_indicators

        except Exception as e:
            logger.error(f"Error calculating {ma_type}: {e}")
            return []

    async def calculate_all_indicators(
        self,
        timeframe: str = "5m",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, List[TechnicalIndicatorModel]]:
        """
        全テクニカル指標を計算

        Args:
            timeframe: タイムフレーム（デフォルト: 5m）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            Dict[str, List[TechnicalIndicatorModel]]: 計算された指標の辞書
        """
        try:
            logger.info(f"Calculating all indicators for {self.currency_pair}")

            results = {}

            # RSI計算
            rsi_results = await self.calculate_rsi(
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
            )
            results["RSI"] = rsi_results

            # MACD計算
            macd_results = await self.calculate_macd(
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
            )
            results["MACD"] = macd_results

            # ボリンジャーバンド計算
            bb_results = await self.calculate_bollinger_bands(
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
            )
            results["Bollinger_Bands"] = bb_results

            # 移動平均計算
            sma_results = await self.calculate_moving_averages(
                timeframe=timeframe,
                ma_type="SMA",
                start_date=start_date,
                end_date=end_date,
            )
            results["SMA"] = sma_results

            ema_results = await self.calculate_moving_averages(
                timeframe=timeframe,
                ma_type="EMA",
                start_date=start_date,
                end_date=end_date,
            )
            results["EMA"] = ema_results

            total_indicators = sum(len(indicators) for indicators in results.values())
            logger.info(f"Successfully calculated {total_indicators} total indicators")

            return results

        except Exception as e:
            logger.error(f"Error calculating all indicators: {e}")
            return {}

    async def get_latest_indicators(
        self,
        indicator_type: str,
        timeframe: str = "5m",
        limit: int = 1,
    ) -> List[TechnicalIndicatorModel]:
        """
        最新の指標値を取得

        Args:
            indicator_type: 指標タイプ
            timeframe: タイムフレーム（デフォルト: 5m）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[TechnicalIndicatorModel]: 最新の指標値リスト
        """
        try:
            return await self.indicator_repo.find_latest_by_type(
                indicator_type, timeframe, self.currency_pair, limit
            )
        except Exception as e:
            logger.error(f"Error getting latest indicators: {e}")
            return []

    async def get_indicators_by_range(
        self,
        indicator_type: str,
        timeframe: str = "5m",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        期間指定で指標値を取得

        Args:
            indicator_type: 指標タイプ
            timeframe: タイムフレーム（デフォルト: 5m）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: 指標値リスト
        """
        try:
            return await self.indicator_repo.find_by_date_range(
                start_date,
                end_date,
                indicator_type,
                timeframe,
                self.currency_pair,
                limit,
            )
        except Exception as e:
            logger.error(f"Error getting indicators by range: {e}")
            return []

    async def _get_price_data_for_calculation(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        min_periods: int,
    ) -> List[PriceDataModel]:
        """
        計算用の価格データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            min_periods: 最小期間数

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        try:
            # デフォルト期間設定
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)  # 30日分

            # 価格データを取得（十分なデータを取得するため制限を緩和）
            price_data = await self.price_repo.find_by_date_range(
                start_date, end_date, self.currency_pair, 10000  # 十分なデータを取得
            )

            # タイムスタンプ順にソート
            price_data.sort(key=lambda x: x.timestamp)

            return price_data

        except Exception as e:
            logger.error(f"Error getting price data for calculation: {e}")
            return []

    async def _save_indicators_with_duplicate_check(
        self, indicators: List[TechnicalIndicatorModel]
    ) -> List[TechnicalIndicatorModel]:
        """
        重複チェック付きで指標を保存

        Args:
            indicators: 保存する指標リスト

        Returns:
            List[TechnicalIndicatorModel]: 保存された指標リスト
        """
        try:
            saved_indicators = []

            for indicator in indicators:
                # 重複チェック
                existing = await self.indicator_repo.find_by_timestamp_and_type(
                    indicator.timestamp,
                    indicator.indicator_type,
                    indicator.timeframe,
                    indicator.currency_pair,
                )

                if not existing:
                    saved_indicator = await self.indicator_repo.save(indicator)
                    saved_indicators.append(saved_indicator)

            return saved_indicators

        except Exception as e:
            logger.error(f"Error saving indicators: {e}")
            return []

    def _calculate_rsi_values(
        self, price_data: List[PriceDataModel], period: int
    ) -> List[Tuple[datetime, float]]:
        """
        RSI値を計算

        Args:
            price_data: 価格データリスト
            period: 期間

        Returns:
            List[Tuple[datetime, float]]: (タイムスタンプ, RSI値)のリスト
        """
        try:
            if len(price_data) < period + 1:
                return []

            # 終値のリストを作成
            closes = [data.close_price for data in price_data]
            timestamps = [data.timestamp for data in price_data]

            # 価格変化を計算
            deltas = np.diff(closes)

            # 上昇・下降を分離
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            # 移動平均を計算
            avg_gains = pd.Series(gains).rolling(window=period).mean().values
            avg_losses = pd.Series(losses).rolling(window=period).mean().values

            # RSI計算
            rsi_values = []
            for i in range(period, len(closes)):
                if avg_losses[i - 1] == 0:
                    rsi = 100
                else:
                    rs = avg_gains[i - 1] / avg_losses[i - 1]
                    rsi = 100 - (100 / (1 + rs))

                rsi_values.append((timestamps[i], rsi))

            return rsi_values

        except Exception as e:
            logger.error(f"Error calculating RSI values: {e}")
            return []

    def _calculate_macd_values(
        self,
        price_data: List[PriceDataModel],
        fast_period: int,
        slow_period: int,
        signal_period: int,
    ) -> List[Tuple[datetime, float, float, float]]:
        """
        MACD値を計算

        Args:
            price_data: 価格データリスト
            fast_period: 短期EMA期間
            slow_period: 長期EMA期間
            signal_period: シグナル期間

        Returns:
            List[Tuple[datetime, float, float, float]]: (タイムスタンプ, MACD, シグナル, ヒストグラム)のリスト
        """
        try:
            if len(price_data) < slow_period + signal_period:
                return []

            # 終値のリストを作成
            closes = [data.close_price for data in price_data]
            timestamps = [data.timestamp for data in price_data]

            # EMA計算
            ema_fast = pd.Series(closes).ewm(span=fast_period).mean().values
            ema_slow = pd.Series(closes).ewm(span=slow_period).mean().values

            # MACD Line
            macd_line = ema_fast - ema_slow

            # Signal Line
            signal_line = pd.Series(macd_line).ewm(span=signal_period).mean().values

            # Histogram
            histogram = macd_line - signal_line

            # 結果を作成
            macd_values = []
            for i in range(slow_period, len(closes)):
                macd_values.append(
                    (timestamps[i], macd_line[i], signal_line[i], histogram[i])
                )

            return macd_values

        except Exception as e:
            logger.error(f"Error calculating MACD values: {e}")
            return []

    def _calculate_bollinger_bands_values(
        self, price_data: List[PriceDataModel], period: int, std_dev: float
    ) -> List[Tuple[datetime, float, float, float]]:
        """
        ボリンジャーバンド値を計算

        Args:
            price_data: 価格データリスト
            period: 期間
            std_dev: 標準偏差

        Returns:
            List[Tuple[datetime, float, float, float]]: (タイムスタンプ, 上限, 中線, 下限)のリスト
        """
        try:
            if len(price_data) < period:
                return []

            # 終値のリストを作成
            closes = [data.close_price for data in price_data]
            timestamps = [data.timestamp for data in price_data]

            # 移動平均と標準偏差を計算
            sma = pd.Series(closes).rolling(window=period).mean().values
            std = pd.Series(closes).rolling(window=period).std().values

            # ボリンジャーバンド計算
            bb_values = []
            for i in range(period - 1, len(closes)):
                upper = sma[i] + (std[i] * std_dev)
                middle = sma[i]
                lower = sma[i] - (std[i] * std_dev)

                bb_values.append((timestamps[i], upper, middle, lower))

            return bb_values

        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands values: {e}")
            return []

    def _calculate_sma_values(
        self, price_data: List[PriceDataModel], period: int
    ) -> List[Tuple[datetime, float]]:
        """
        SMA値を計算

        Args:
            price_data: 価格データリスト
            period: 期間

        Returns:
            List[Tuple[datetime, float]]: (タイムスタンプ, SMA値)のリスト
        """
        try:
            if len(price_data) < period:
                return []

            # 終値のリストを作成
            closes = [data.close_price for data in price_data]
            timestamps = [data.timestamp for data in price_data]

            # SMA計算
            sma = pd.Series(closes).rolling(window=period).mean().values

            # 結果を作成
            sma_values = []
            for i in range(period - 1, len(closes)):
                sma_values.append((timestamps[i], sma[i]))

            return sma_values

        except Exception as e:
            logger.error(f"Error calculating SMA values: {e}")
            return []

    def _calculate_ema_values(
        self, price_data: List[PriceDataModel], period: int
    ) -> List[Tuple[datetime, float]]:
        """
        EMA値を計算

        Args:
            price_data: 価格データリスト
            period: 期間

        Returns:
            List[Tuple[datetime, float]]: (タイムスタンプ, EMA値)のリスト
        """
        try:
            if len(price_data) < period:
                return []

            # 終値のリストを作成
            closes = [data.close_price for data in price_data]
            timestamps = [data.timestamp for data in price_data]

            # EMA計算
            ema = pd.Series(closes).ewm(span=period).mean().values

            # 結果を作成
            ema_values = []
            for i in range(len(closes)):
                ema_values.append((timestamps[i], ema[i]))

            return ema_values

        except Exception as e:
            logger.error(f"Error calculating EMA values: {e}")
            return []
