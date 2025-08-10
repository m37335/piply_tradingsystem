"""
時間軸変換サービス

5分足データから他の時間軸（H1, H4, D1）を生成するサービス
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TimeframeConverter:
    """
    時間軸変換サービス
    
    5分足データから他の時間軸を生成し、
    パターン検出器が期待する形式でデータを提供
    """

    def __init__(self, price_repo: PriceDataRepositoryImpl, indicator_repo: TechnicalIndicatorRepositoryImpl):
        self.price_repo = price_repo
        self.indicator_repo = indicator_repo

    async def create_multi_timeframe_data(
        self, 
        start_date: datetime, 
        end_date: datetime,
        currency_pair: str = "USD/JPY"
    ) -> Dict[str, Dict]:
        """
        マルチタイムフレームデータを作成

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア

        Returns:
            Dict: パターン検出器用のマルチタイムフレームデータ
        """
        try:
            # 5分足データを取得
            m5_price_data = await self.price_repo.find_by_date_range(
                start_date, end_date, currency_pair, 1000
            )
            
            if not m5_price_data:
                logger.warning("No M5 price data found")
                return {}

            # 5分足データをDataFrameに変換
            m5_df = self._convert_to_dataframe(m5_price_data)
            
            # 各時間軸のデータを生成
            multi_timeframe_data = {}
            
            # M5データ
            multi_timeframe_data["M5"] = await self._create_timeframe_data(
                m5_df, "5m", start_date, end_date, currency_pair
            )
            
            # H1データ（5分足から集約）
            h1_df = self._aggregate_timeframe(m5_df, "1H")
            multi_timeframe_data["H1"] = await self._create_timeframe_data(
                h1_df, "1h", start_date, end_date, currency_pair
            )
            
            # H4データ（5分足から集約）
            h4_df = self._aggregate_timeframe(m5_df, "4H")
            multi_timeframe_data["H4"] = await self._create_timeframe_data(
                h4_df, "4h", start_date, end_date, currency_pair
            )
            
            # D1データ（5分足から集約）
            d1_df = self._aggregate_timeframe(m5_df, "1D")
            multi_timeframe_data["D1"] = await self._create_timeframe_data(
                d1_df, "1d", start_date, end_date, currency_pair
            )

            logger.info(f"Created multi-timeframe data with {len(multi_timeframe_data)} timeframes")
            return multi_timeframe_data

        except Exception as e:
            logger.error(f"Error creating multi-timeframe data: {e}")
            return {}

    def _convert_to_dataframe(self, price_data: List) -> pd.DataFrame:
        """
        価格データをDataFrameに変換
        """
        df_data = []
        for data in price_data:
            df_data.append({
                "timestamp": data.timestamp,
                "Open": float(data.open_price) if data.open_price else 0.0,
                "High": float(data.high_price) if data.high_price else 0.0,
                "Low": float(data.low_price) if data.low_price else 0.0,
                "Close": float(data.close_price) if data.close_price else 0.0,
                "Volume": int(data.volume) if data.volume else 0
            })
        
        df = pd.DataFrame(df_data)
        df.set_index("timestamp", inplace=True)
        return df

    def _aggregate_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        時間軸を集約
        """
        if df.empty:
            return df
        
        # リサンプリングルール
        resample_rules = {
            "1H": "1H",
            "4H": "4H", 
            "1D": "1D"
        }
        
        rule = resample_rules.get(timeframe)
        if not rule:
            return df
        
        # OHLCV集約
        aggregated = df.resample(rule).agg({
            "Open": "first",
            "High": "max",
            "Low": "min", 
            "Close": "last",
            "Volume": "sum"
        }).dropna()
        
        return aggregated

    async def _create_timeframe_data(
        self, 
        price_df: pd.DataFrame, 
        db_timeframe: str,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str
    ) -> Dict:
        """
        特定時間軸のデータを作成
        """
        try:
            # 価格データ
            price_data = price_df if not price_df.empty else pd.DataFrame()
            
            # 指標データを取得
            indicators = await self.indicator_repo.find_by_date_range(
                start_date, end_date, None, db_timeframe, currency_pair, 1000
            )
            
            # 最新の指標値を取得
            indicator_dict = {}
            
            # RSI
            latest_rsi = await self.indicator_repo.find_latest_by_type(
                "RSI", db_timeframe, limit=1
            )
            if latest_rsi:
                indicator_dict["rsi"] = {
                    "current_value": float(latest_rsi[0].value)
                }
            
            # MACD
            latest_macd = await self.indicator_repo.find_latest_by_type(
                "MACD", db_timeframe, limit=1
            )
            if latest_macd:
                additional_data = latest_macd[0].additional_data or {}
                indicator_dict["macd"] = {
                    "macd": float(latest_macd[0].value),
                    "signal": additional_data.get("signal_line", 0.0),
                    "histogram": additional_data.get("histogram", 0.0)
                }
            
            # ボリンジャーバンド
            latest_bb = await self.indicator_repo.find_latest_by_type(
                "BB", db_timeframe, limit=1
            )
            if latest_bb:
                additional_data = latest_bb[0].additional_data or {}
                indicator_dict["bollinger_bands"] = {
                    "upper": additional_data.get("upper_band", 0.0),
                    "middle": float(latest_bb[0].value),
                    "lower": additional_data.get("lower_band", 0.0)
                }
            
            return {
                "price_data": price_data,
                "indicators": indicator_dict
            }

        except Exception as e:
            logger.error(f"Error creating timeframe data for {db_timeframe}: {e}")
            return {
                "price_data": pd.DataFrame(),
                "indicators": {}
            }
