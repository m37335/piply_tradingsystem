"""
マルチタイムフレームテクニカル指標計算サービス

各時間軸のテクニカル指標を計算し、保存するシステム
"""

from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.infrastructure.database.services.timeframe_data_service import (
    TimeframeDataService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class MultiTimeframeTechnicalIndicatorService:
    """
    マルチタイムフレームテクニカル指標計算サービス

    責任:
    - 各時間軸のテクニカル指標計算
    - 計算結果のデータベース保存
    - 最新指標値の取得
    - 指標データの管理

    特徴:
    - 複数時間軸対応（5m, 1h, 4h, 1d）
    - 3つの主要指標（RSI, MACD, BB）
    - 効率的な計算と保存
    - 重複防止
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)
        self.timeframe_service = TimeframeDataService(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"

        # 時間軸設定
        self.timeframes = {
            "5m": {
                "description": "5分足",
                "periods": {"rsi": 14, "macd": 12, "bb": 20},
            },
            "1h": {
                "description": "1時間足",
                "periods": {"rsi": 14, "macd": 12, "bb": 20},
            },
            "4h": {
                "description": "4時間足",
                "periods": {"rsi": 14, "macd": 12, "bb": 20},
            },
            "1d": {"description": "日足", "periods": {"rsi": 14, "macd": 12, "bb": 20}},
        }

        # 指標計算器の初期化
        self.technical_analyzer = TechnicalIndicatorsAnalyzer()

        logger.info(
            f"Initialized MultiTimeframeTechnicalIndicatorService for {self.currency_pair}"
        )

    async def calculate_all_timeframe_indicators(self) -> Dict[str, Dict]:
        """
        全時間軸のテクニカル指標を計算

        Returns:
            Dict[str, Dict]: 各時間軸の指標計算結果
        """
        try:
            logger.info("Calculating all timeframe indicators...")

            results = {}

            for timeframe, config in self.timeframes.items():
                logger.info(f"Calculating {config['description']} indicators...")

                timeframe_indicators = await self.calculate_timeframe_indicators(
                    timeframe
                )
                if timeframe_indicators:
                    results[timeframe] = timeframe_indicators
                    logger.info(
                        f"Successfully calculated {config['description']} indicators"
                    )
                else:
                    logger.warning(
                        f"Failed to calculate {config['description']} indicators"
                    )

            logger.info(
                f"Completed calculating indicators for {len(results)} timeframes"
            )
            return results

        except Exception as e:
            logger.error(f"Error calculating all timeframe indicators: {e}")
            return {}

    async def calculate_timeframe_indicators(self, timeframe: str) -> Dict:
        """
        特定時間軸のテクニカル指標を計算

        Args:
            timeframe: 時間軸（5m, 1h, 4h, 1d）

        Returns:
            Dict: 計算された指標データ
        """
        try:
            if timeframe not in self.timeframes:
                logger.error(f"Invalid timeframe: {timeframe}")
                return {}

            config = self.timeframes[timeframe]
            logger.info(f"Calculating {config['description']} indicators...")

            # 価格データを取得
            price_data = await self.timeframe_service.get_latest_data_by_timeframe(
                timeframe, limit=1000
            )

            if not price_data:
                logger.warning(f"No price data available for {timeframe}")
                return {}

            # DataFrameに変換
            df = self._convert_to_dataframe(price_data)
            if df.empty:
                logger.warning(f"Empty DataFrame for {timeframe}")
                return {}

            # 各指標を計算
            indicators = {}

            # RSI計算
            rsi_result = await self._calculate_rsi(
                df, timeframe, config["periods"]["rsi"]
            )
            if rsi_result:
                indicators["rsi"] = rsi_result

            # MACD計算
            macd_result = await self._calculate_macd(
                df, timeframe, config["periods"]["macd"]
            )
            if macd_result:
                indicators["macd"] = macd_result

            # ボリンジャーバンド計算
            bb_result = await self._calculate_bollinger_bands(
                df, timeframe, config["periods"]["bb"]
            )
            if bb_result:
                indicators["bb"] = bb_result

            logger.info(f"Calculated {len(indicators)} indicators for {timeframe}")
            return indicators

        except Exception as e:
            logger.error(f"Error calculating {timeframe} indicators: {e}")
            return {}

    async def save_timeframe_indicators(self, timeframe: str, indicators: Dict) -> bool:
        """
        特定時間軸の指標データを保存

        Args:
            timeframe: 時間軸
            indicators: 指標データ

        Returns:
            bool: 保存成功の場合True
        """
        try:
            logger.info(f"Saving {timeframe} indicators...")

            saved_count = 0

            for indicator_type, indicator_data in indicators.items():
                if indicator_type == "rsi":
                    saved = await self._save_rsi_indicator(timeframe, indicator_data)
                    if saved:
                        saved_count += 1

                elif indicator_type == "macd":
                    saved = await self._save_macd_indicator(timeframe, indicator_data)
                    if saved:
                        saved_count += 1

                elif indicator_type == "bb":
                    saved = await self._save_bollinger_bands_indicator(
                        timeframe, indicator_data
                    )
                    if saved:
                        saved_count += 1

            logger.info(f"Saved {saved_count} indicators for {timeframe}")
            return saved_count > 0

        except Exception as e:
            logger.error(f"Error saving {timeframe} indicators: {e}")
            return False

    async def get_latest_indicators_by_timeframe(self, timeframe: str) -> Dict:
        """
        特定時間軸の最新指標値を取得

        Args:
            timeframe: 時間軸

        Returns:
            Dict: 最新の指標値
        """
        try:
            logger.info(f"Getting latest {timeframe} indicators...")

            latest_indicators = {}

            # タイムフレーム形式を変換（1h -> H1）
            db_timeframe = self._convert_timeframe_format(timeframe)

            # RSI
            latest_rsi = await self.indicator_repo.find_latest_by_type(
                "RSI", db_timeframe, limit=1
            )
            if latest_rsi:
                latest_indicators["rsi"] = {
                    "value": float(latest_rsi[0].value),
                    "timestamp": latest_rsi[0].timestamp,
                }

            # MACD
            latest_macd = await self.indicator_repo.find_latest_by_type(
                "MACD", db_timeframe, limit=1
            )
            if latest_macd:
                # additional_dataがJSON文字列の場合があるため、パースを試行
                additional_data = latest_macd[0].additional_data or {}
                if isinstance(additional_data, str):
                    try:
                        import json

                        additional_data = json.loads(additional_data)
                    except (json.JSONDecodeError, TypeError):
                        additional_data = {}

                latest_indicators["macd"] = {
                    "value": float(latest_macd[0].value),
                    "signal": additional_data.get("signal_line", 0.0),
                    "histogram": additional_data.get("histogram", 0.0),
                    "timestamp": latest_macd[0].timestamp,
                }

            # ボリンジャーバンド
            latest_bb = await self.indicator_repo.find_latest_by_type(
                "BB", db_timeframe, limit=1
            )
            if latest_bb:
                # additional_dataがJSON文字列の場合があるため、パースを試行
                additional_data = latest_bb[0].additional_data or {}
                if isinstance(additional_data, str):
                    try:
                        import json

                        additional_data = json.loads(additional_data)
                    except (json.JSONDecodeError, TypeError):
                        additional_data = {}

                latest_indicators["bb"] = {
                    "value": float(latest_bb[0].value),
                    "upper": additional_data.get("upper_band", 0.0),
                    "lower": additional_data.get("lower_band", 0.0),
                    "timestamp": latest_bb[0].timestamp,
                }

            logger.info(
                f"Retrieved {len(latest_indicators)} latest indicators for {timeframe}"
            )
            return latest_indicators

        except Exception as e:
            logger.error(f"Error getting latest {timeframe} indicators: {e}")
            return {}

    async def _calculate_rsi(
        self, df: pd.DataFrame, timeframe: str, period: int
    ) -> Optional[Dict]:
        """
        RSIを計算
        """
        try:
            if len(df) < period + 1:
                logger.warning(
                    f"Insufficient data for RSI calculation: {len(df)} < {period + 1}"
                )
                return None

            # RSI計算
            rsi_result = self.technical_analyzer.calculate_rsi(df, timeframe)

            if "error" in rsi_result:
                logger.warning(f"RSI calculation error: {rsi_result['error']}")
                return None

            # 最新値を取得
            latest_rsi = rsi_result["current_value"]

            return {
                "value": float(latest_rsi),
                "timestamp": df.index[-1],
                "all_values": rsi_result,
            }

        except Exception as e:
            logger.error(f"Error calculating RSI for {timeframe}: {e}")
            return None

    async def _calculate_macd(
        self, df: pd.DataFrame, timeframe: str, period: int
    ) -> Optional[Dict]:
        """
        MACDを計算
        """
        try:
            if len(df) < period * 2:
                logger.warning(
                    f"Insufficient data for MACD calculation: {len(df)} < {period * 2}"
                )
                return None

            # MACD計算
            macd_result = self.technical_analyzer.calculate_macd(df, timeframe)

            if "error" in macd_result:
                logger.warning(f"MACD calculation error: {macd_result['error']}")
                return None

            # 最新値を取得
            latest_macd = macd_result["macd_line"]
            latest_signal = macd_result["signal_line"]
            latest_histogram = macd_result["histogram"]

            return {
                "value": float(latest_macd),
                "signal_line": float(latest_signal),
                "histogram": float(latest_histogram),
                "timestamp": df.index[-1],
                "all_values": macd_result,
            }

        except Exception as e:
            logger.error(f"Error calculating MACD for {timeframe}: {e}")
            return None

    async def _calculate_bollinger_bands(
        self, df: pd.DataFrame, timeframe: str, period: int
    ) -> Optional[Dict]:
        """
        ボリンジャーバンドを計算
        """
        try:
            if len(df) < period:
                logger.warning(
                    f"Insufficient data for BB calculation: {len(df)} < {period}"
                )
                return None

            # ボリンジャーバンド計算
            bb_result = self.technical_analyzer.calculate_bollinger_bands(df, timeframe)

            if "error" in bb_result:
                logger.warning(f"BB calculation error: {bb_result['error']}")
                return None

            # 最新値を取得
            latest_middle = bb_result["middle_band"]
            latest_upper = bb_result["upper_band"]
            latest_lower = bb_result["lower_band"]

            return {
                "value": float(latest_middle),
                "upper_band": float(latest_upper),
                "lower_band": float(latest_lower),
                "timestamp": df.index[-1],
                "all_values": bb_result,
            }

        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands for {timeframe}: {e}")
            return None

    async def _save_rsi_indicator(self, timeframe: str, rsi_data: Dict) -> bool:
        """
        RSI指標を保存
        """
        try:
            # タイムフレーム形式を変換（5m -> M5）
            db_timeframe = self._convert_timeframe_format(timeframe)

            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                indicator_type="RSI",
                timeframe=db_timeframe,
                value=rsi_data["value"],
                timestamp=rsi_data["timestamp"],
                additional_data={},
            )

            await self.indicator_repo.save(indicator)
            logger.info(f"Saved RSI indicator for {timeframe}: {rsi_data['value']:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error saving RSI indicator for {timeframe}: {e}")
            return False

    async def _save_macd_indicator(self, timeframe: str, macd_data: Dict) -> bool:
        """
        MACD指標を保存
        """
        try:
            # タイムフレーム形式を変換（5m -> M5）
            db_timeframe = self._convert_timeframe_format(timeframe)

            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                indicator_type="MACD",
                timeframe=db_timeframe,
                value=macd_data["value"],
                timestamp=macd_data["timestamp"],
                additional_data={
                    "signal_line": macd_data["signal_line"],
                    "histogram": macd_data["histogram"],
                },
            )

            await self.indicator_repo.save(indicator)
            logger.info(
                f"Saved MACD indicator for {timeframe}: {macd_data['value']:.4f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error saving MACD indicator for {timeframe}: {e}")
            return False

    async def _save_bollinger_bands_indicator(
        self, timeframe: str, bb_data: Dict
    ) -> bool:
        """
        ボリンジャーバンド指標を保存
        """
        try:
            # タイムフレーム形式を変換（5m -> M5）
            db_timeframe = self._convert_timeframe_format(timeframe)

            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                indicator_type="BB",
                timeframe=db_timeframe,
                value=bb_data["value"],
                timestamp=bb_data["timestamp"],
                additional_data={
                    "upper_band": bb_data["upper_band"],
                    "lower_band": bb_data["lower_band"],
                },
            )

            await self.indicator_repo.save(indicator)
            logger.info(f"Saved BB indicator for {timeframe}: {bb_data['value']:.2f}")
            return True

        except Exception as e:
            logger.error(f"Error saving BB indicator for {timeframe}: {e}")
            return False

    def _convert_to_dataframe(self, price_data: List) -> pd.DataFrame:
        """
        価格データをDataFrameに変換
        """
        if not price_data:
            return pd.DataFrame()

        df_data = []
        for data in price_data:
            df_data.append(
                {
                    "timestamp": data.timestamp,
                    "Open": float(data.open_price) if data.open_price else 0.0,
                    "High": float(data.high_price) if data.high_price else 0.0,
                    "Low": float(data.low_price) if data.low_price else 0.0,
                    "Close": float(data.close_price) if data.close_price else 0.0,
                    "Volume": int(data.volume) if data.volume else 0,
                }
            )

        df = pd.DataFrame(df_data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)
        return df

    def _convert_timeframe_format(self, timeframe: str) -> str:
        """
        タイムフレーム形式を変換（5m -> M5）

        Args:
            timeframe: 元のタイムフレーム形式

        Returns:
            str: データベース用のタイムフレーム形式
        """
        timeframe_mapping = {"5m": "M5", "1h": "H1", "4h": "H4", "1d": "D1"}
        return timeframe_mapping.get(timeframe, timeframe)

    async def count_latest_indicators(self) -> int:
        """
        最新のテクニカル指標数を取得

        Returns:
            int: 最新の指標数
        """
        try:
            # 過去30日間の指標数をカウント
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            # 直接SQLで検索（文字列比較の問題を回避）
            from sqlalchemy import text

            query = text(
                """
                SELECT COUNT(*) FROM technical_indicators
                WHERE timestamp >= :start_date AND timestamp <= :end_date
            """
            )

            result = await self.session.execute(
                query,
                {
                    "start_date": start_date,  # datetimeオブジェクトを直接渡す
                    "end_date": end_date,      # datetimeオブジェクトを直接渡す
                },
            )
            total_count = result.scalar()

            logger.info(f"総指標数: {total_count}件 ({start_date} から {end_date})")

            return total_count

        except Exception as e:
            logger.error(f"最新指標数取得エラー: {e}")
            return 0

    async def calculate_indicators_for_timeframe(
        self, timeframe: str
    ) -> Dict[str, int]:
        """
        指定時間軸のテクニカル指標を計算

        Args:
            timeframe: 時間軸（5m, 1h, 4h, 1d）

        Returns:
            Dict[str, int]: 計算された指標数
        """
        try:
            logger.info(f"📈 {timeframe}時間軸のテクニカル指標計算開始")

            # 既存のcalculate_timeframe_indicatorsメソッドを使用
            indicators = await self.calculate_timeframe_indicators(timeframe)

            if indicators:
                # データベースに保存
                await self.save_timeframe_indicators(timeframe, indicators)
                logger.info(f"✅ {timeframe}時間軸のテクニカル指標計算完了: {len(indicators)}件")
                return {"calculated": len(indicators)}
            else:
                logger.warning(f"⚠️ {timeframe}時間軸のテクニカル指標計算完了: 0件")
                return {"calculated": 0}

        except Exception as e:
            logger.error(f"❌ {timeframe}時間軸のテクニカル指標計算エラー: {e}")
            return {"error": str(e)}

    async def get_service_status(self) -> Dict:
        """
        サービスの状態を取得

        Returns:
            Dict: サービス状態
        """
        try:
            from datetime import datetime

            return {
                "service": "MultiTimeframeTechnicalIndicatorService",
                "status": "healthy",
                "currency_pair": self.currency_pair,
                "timeframes": list(self.timeframes.keys()),
                "timestamp": datetime.now(),
            }
        except Exception as e:
            return {
                "service": "MultiTimeframeTechnicalIndicatorService",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(),
            }
