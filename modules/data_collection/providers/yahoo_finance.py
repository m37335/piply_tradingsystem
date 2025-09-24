"""
Yahoo Finance APIプロバイダー

Yahoo Finance APIを使用してデータを取得します。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import yfinance as yf
except ImportError:
    yf = None

from .base_provider import BaseDataProvider, DataCollectionResult, PriceData, TimeFrame

logger = logging.getLogger(__name__)


class YahooFinanceProvider(BaseDataProvider):
    """Yahoo Finance APIプロバイダー"""

    def __init__(self):
        super().__init__("yahoo_finance")
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = None

    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self._session:
            await self._session.close()

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_date: datetime,
        end_date: datetime,
    ) -> DataCollectionResult:
        """履歴データを取得"""
        try:
            # レート制限チェック
            if self._rate_limiter:
                await self._rate_limiter.wait_for_availability()

            # yfinanceを使用してデータを取得
            ticker = yf.Ticker(symbol)

            # 時間軸の変換
            interval = self._convert_timeframe(timeframe)

            # データ取得
            hist = ticker.history(start=start_date, end=end_date, interval=interval)

            if hist.empty:
                return DataCollectionResult(
                    success=False, data=[], error_message=f"No data found for {symbol}"
                )

            # PriceDataオブジェクトに変換
            price_data = []
            for timestamp, row in hist.iterrows():
                data = PriceData(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                    source=self.name,
                    quality_score=self._calculate_quality_score(row),
                )
                price_data.append(data)

            # データの妥当性チェック
            validated_data = self._validate_data(price_data)

            return DataCollectionResult(
                success=True,
                data=validated_data,
                metadata={
                    "total_records": len(validated_data),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "timeframe": timeframe.value if hasattr(timeframe, 'value') else str(timeframe),
                },
            )

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return DataCollectionResult(success=False, data=[], error_message=str(e))

    async def get_latest_data(
        self, symbol: str, timeframe: TimeFrame
    ) -> DataCollectionResult:
        """最新データを取得"""
        try:
            # レート制限チェック
            if self._rate_limiter:
                await self._rate_limiter.wait_for_availability()

            # 最新のデータを取得（過去1日分）
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)

            return await self.get_historical_data(
                symbol, timeframe, start_date, end_date
            )

        except Exception as e:
            logger.error(f"Error fetching latest data for {symbol}: {e}")
            return DataCollectionResult(success=False, data=[], error_message=str(e))

    async def get_available_symbols(self) -> List[str]:
        """利用可能なシンボル一覧を取得"""
        # 主要な通貨ペアとインデックス
        return [
            "USDJPY=X",
            "EURJPY=X",
            "GBPJPY=X",
            "AUDJPY=X",
            "EURUSD=X",
            "GBPUSD=X",
            "AUDUSD=X",
            "NZDUSD=X",
            "USDCHF=X",
            "USDCAD=X",
            "EURGBP=X",
            "EURCHF=X",
            "^N225",
            "^GSPC",
            "^DJI",
            "^IXIC",
            "^VIX",
        ]

    def is_available(self) -> bool:
        """プロバイダーが利用可能かチェック"""
        return self._is_available

    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 簡単なテストリクエスト
            ticker = yf.Ticker("USDJPY=X")
            info = ticker.info

            if info and "symbol" in info:
                self._is_available = True
                return True
            else:
                self._is_available = False
                return False

        except Exception as e:
            logger.error(f"Yahoo Finance health check failed: {e}")
            self._is_available = False
            return False

    def _convert_timeframe(self, timeframe: TimeFrame) -> str:
        """TimeFrameをyfinanceのintervalに変換"""
        # TimeFrameの値（文字列）を使用してマッピング
        mapping = {
            "5m": "5m",   # 5分足（メイン対象）
            "15m": "15m", # 15分足
            "1h": "1h",   # 1時間足
            "4h": "4h",   # 4時間足
            "1d": "1d",   # 日足
        }
        timeframe_value = timeframe.value if hasattr(timeframe, 'value') else str(timeframe)
        return mapping.get(timeframe_value, "5m")  # デフォルトは5分足

    def _calculate_quality_score(self, row) -> float:
        """データ品質スコアを計算"""
        score = 1.0

        # 価格の妥当性チェック
        if not (
            row["Low"] <= row["Open"] <= row["High"]
            and row["Low"] <= row["Close"] <= row["High"]
        ):
            score -= 0.3

        # ボリュームの妥当性チェック
        if row["Volume"] < 0:
            score -= 0.2

        return max(0.0, score)

    def set_rate_limiter(self, rate_limiter):
        """レート制限器を設定"""
        self._rate_limiter = rate_limiter
