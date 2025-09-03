"""
Alpha Vantage API Client
Alpha Vantage APIクライアント

設計書参照:
- インフラ・プラグイン設計_20250809.md

Alpha Vantage APIから為替レートデータを取得するクライアント
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from ...domain.entities.exchange_rate import ExchangeRateEntity
from ...domain.value_objects.currency import CurrencyCode, CurrencyPair, Price
from ...utils.logging_config import get_infrastructure_logger
from .base_client import APIError, BaseAPIClient

logger = get_infrastructure_logger()


class AlphaVantageClient(BaseAPIClient):
    """
    Alpha Vantage APIクライアント

    責任:
    - 為替レートの取得
    - データの正規化
    - エラーハンドリング
    - レート制限の管理

    API仕様:
    - Free tier: 5 API requests per minute, 500 per day
    - Premium: より高い制限
    """

    def __init__(self, api_key: str, **kwargs):
        """
        初期化

        Args:
            api_key: Alpha Vantage APIキー
            **kwargs: BaseAPIClientの引数
        """
        super().__init__(
            base_url="https://www.alphavantage.co",
            api_key=api_key,
            rate_limit_calls=5,  # Free tier制限
            rate_limit_period=60,
            **kwargs,
        )

        logger.info("Initialized Alpha Vantage client")

    def _get_auth_params(self) -> Dict[str, str]:
        """
        認証パラメータを取得

        Returns:
            Dict[str, str]: APIキーパラメータ
        """
        return {"apikey": self.api_key}

    async def get_fx_intraday(
        self,
        from_symbol: str,
        to_symbol: str,
        interval: str = "5min",
        outputsize: str = "compact",
    ) -> List[ExchangeRateEntity]:
        """
        FX Intradayデータを取得

        Args:
            from_symbol: 基軸通貨（例: "USD"）
            to_symbol: 相手通貨（例: "JPY"）
            interval: 時間間隔（1min, 5min, 15min, 30min, 60min）
            outputsize: データサイズ（compact, full）

        Returns:
            List[ExchangeRateEntity]: 為替レートエンティティのリスト
        """
        try:
            params = {
                "function": "FX_INTRADAY",
                "from_symbol": from_symbol.upper(),
                "to_symbol": to_symbol.upper(),
                "interval": interval,
                "outputsize": outputsize,
            }

            logger.debug(f"Fetching FX intraday data: {from_symbol}/{to_symbol}")

            response = await self.get("/query", params=params)

            # エラーチェック
            if "Error Message" in response:
                raise APIError(f"Alpha Vantage error: {response['Error Message']}")

            if "Note" in response:
                raise APIError(f"Alpha Vantage rate limit: {response['Note']}")

            # データの解析
            entities = self._parse_fx_intraday_response(
                response, from_symbol, to_symbol
            )

            logger.info(
                f"Retrieved {len(entities)} FX records for {from_symbol}/{to_symbol}"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to get FX intraday data: {str(e)}")
            raise

    async def get_fx_daily(
        self, from_symbol: str, to_symbol: str, outputsize: str = "compact"
    ) -> List[ExchangeRateEntity]:
        """
        FX Dailyデータを取得

        Args:
            from_symbol: 基軸通貨
            to_symbol: 相手通貨
            outputsize: データサイズ

        Returns:
            List[ExchangeRateEntity]: 為替レートエンティティのリスト
        """
        try:
            params = {
                "function": "FX_DAILY",
                "from_symbol": from_symbol.upper(),
                "to_symbol": to_symbol.upper(),
                "outputsize": outputsize,
            }

            logger.debug(f"Fetching FX daily data: {from_symbol}/{to_symbol}")

            response = await self.get("/query", params=params)

            # エラーチェック
            if "Error Message" in response:
                raise APIError(f"Alpha Vantage error: {response['Error Message']}")

            entities = self._parse_fx_daily_response(response, from_symbol, to_symbol)

            logger.info(
                f"Retrieved {len(entities)} daily FX records for {from_symbol}/{to_symbol}"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to get FX daily data: {str(e)}")
            raise

    async def get_currency_exchange_rate(
        self, from_currency: str, to_currency: str
    ) -> Optional[ExchangeRateEntity]:
        """
        リアルタイム為替レートを取得

        Args:
            from_currency: 基軸通貨
            to_currency: 相手通貨

        Returns:
            Optional[ExchangeRateEntity]: 最新の為替レート
        """
        try:
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_currency.upper(),
                "to_currency": to_currency.upper(),
            }

            logger.debug(f"Fetching real-time rate: {from_currency}/{to_currency}")

            response = await self.get("/query", params=params)

            # エラーチェック
            if "Error Message" in response:
                raise APIError(f"Alpha Vantage error: {response['Error Message']}")

            entity = self._parse_currency_exchange_response(
                response, from_currency, to_currency
            )

            if entity:
                logger.info(
                    f"Retrieved real-time rate: {from_currency}/{to_currency} = {entity.rate}"
                )

            return entity

        except Exception as e:
            logger.error(f"Failed to get currency exchange rate: {str(e)}")
            raise

    def _parse_fx_intraday_response(
        self, response: Dict[str, Any], from_symbol: str, to_symbol: str
    ) -> List[ExchangeRateEntity]:
        """
        FX Intradayレスポンスを解析

        Args:
            response: APIレスポンス
            from_symbol: 基軸通貨
            to_symbol: 相手通貨

        Returns:
            List[ExchangeRateEntity]: パースされたエンティティリスト
        """
        entities = []

        # レスポンス構造: "Time Series (5min)" などのキーを探す
        time_series_key = None
        for key in response.keys():
            if "Time Series" in key:
                time_series_key = key
                break

        if not time_series_key or time_series_key not in response:
            logger.warning("No time series data found in response")
            return entities

        time_series = response[time_series_key]
        currency_pair = CurrencyPair(
            base=CurrencyCode(from_symbol.upper()),
            quote=CurrencyCode(to_symbol.upper()),
        )

        for timestamp_str, ohlc_data in time_series.items():
            try:
                # タイムスタンプをパース
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                # OHLCデータを取得
                open_rate = Decimal(str(ohlc_data.get("1. open", "0")))
                high_rate = Decimal(str(ohlc_data.get("2. high", "0")))
                low_rate = Decimal(str(ohlc_data.get("3. low", "0")))
                close_rate = Decimal(str(ohlc_data.get("4. close", "0")))

                # メインレートは終値を使用
                rate = Price(close_rate)

                entity = ExchangeRateEntity(
                    currency_pair=currency_pair,
                    rate=rate,
                    open_rate=Price(open_rate) if open_rate > 0 else None,
                    high_rate=Price(high_rate) if high_rate > 0 else None,
                    low_rate=Price(low_rate) if low_rate > 0 else None,
                    close_rate=Price(close_rate) if close_rate > 0 else None,
                    source="alpha_vantage",
                    timestamp=timestamp,
                )

                entities.append(entity)

            except Exception as e:
                logger.warning(f"Failed to parse record {timestamp_str}: {str(e)}")
                continue

        # 時系列順にソート（古い順）
        entities.sort(key=lambda x: x.timestamp)

        return entities

    def _parse_fx_daily_response(
        self, response: Dict[str, Any], from_symbol: str, to_symbol: str
    ) -> List[ExchangeRateEntity]:
        """
        FX Dailyレスポンスを解析
        """
        entities = []

        if "Time Series (Daily)" not in response:
            logger.warning("No daily time series data found in response")
            return entities

        time_series = response["Time Series (Daily)"]
        currency_pair = CurrencyPair(
            base=CurrencyCode(from_symbol.upper()),
            quote=CurrencyCode(to_symbol.upper()),
        )

        for date_str, ohlc_data in time_series.items():
            try:
                # 日付をパース（日次データは00:00:00に設定）
                timestamp = datetime.strptime(date_str, "%Y-%m-%d")

                open_rate = Decimal(str(ohlc_data.get("1. open", "0")))
                high_rate = Decimal(str(ohlc_data.get("2. high", "0")))
                low_rate = Decimal(str(ohlc_data.get("3. low", "0")))
                close_rate = Decimal(str(ohlc_data.get("4. close", "0")))

                rate = Price(close_rate)

                entity = ExchangeRateEntity(
                    currency_pair=currency_pair,
                    rate=rate,
                    open_rate=Price(open_rate) if open_rate > 0 else None,
                    high_rate=Price(high_rate) if high_rate > 0 else None,
                    low_rate=Price(low_rate) if low_rate > 0 else None,
                    close_rate=Price(close_rate) if close_rate > 0 else None,
                    source="alpha_vantage",
                    timestamp=timestamp,
                )

                entities.append(entity)

            except Exception as e:
                logger.warning(f"Failed to parse daily record {date_str}: {str(e)}")
                continue

        # 時系列順にソート（古い順）
        entities.sort(key=lambda x: x.timestamp)

        return entities

    def _parse_currency_exchange_response(
        self, response: Dict[str, Any], from_currency: str, to_currency: str
    ) -> Optional[ExchangeRateEntity]:
        """
        リアルタイム為替レートレスポンスを解析
        """
        if "Realtime Currency Exchange Rate" not in response:
            logger.warning("No realtime exchange rate data found in response")
            return None

        rate_data = response["Realtime Currency Exchange Rate"]

        try:
            # データの抽出
            exchange_rate = Decimal(str(rate_data.get("5. Exchange Rate", "0")))
            bid_price = rate_data.get("8. Bid Price")
            ask_price = rate_data.get("9. Ask Price")

            # タイムスタンプ
            last_refreshed = rate_data.get("6. Last Refreshed", "")
            try:
                timestamp = datetime.strptime(last_refreshed, "%Y-%m-%d %H:%M:%S")
            except:
                timestamp = datetime.utcnow()

            currency_pair = CurrencyPair(
                base=CurrencyCode(from_currency.upper()),
                quote=CurrencyCode(to_currency.upper()),
            )

            entity = ExchangeRateEntity(
                currency_pair=currency_pair,
                rate=Price(exchange_rate),
                bid_rate=Price(Decimal(str(bid_price))) if bid_price else None,
                ask_rate=Price(Decimal(str(ask_price))) if ask_price else None,
                source="alpha_vantage",
                timestamp=timestamp,
            )

            # スプレッドを計算
            if entity.bid_rate and entity.ask_rate:
                spread_value = entity.ask_rate.value - entity.bid_rate.value
                entity.spread = Price(spread_value)

            return entity

        except Exception as e:
            logger.error(f"Failed to parse currency exchange response: {str(e)}")
            return None

    async def get_supported_currencies(self) -> List[str]:
        """
        サポートされている通貨のリストを取得

        Returns:
            List[str]: 通貨コードのリスト
        """
        # Alpha Vantageでサポートされている主要通貨
        # 実際のAPIではこれらの通貨が利用可能
        major_currencies = [
            "USD",
            "EUR",
            "JPY",
            "GBP",
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "SEK",
            "NZD",
            "MXN",
            "SGD",
            "HKD",
            "NOK",
            "ZAR",
            "TRY",
            "BRL",
            "INR",
            "KRW",
            "PLN",
            "RUB",
        ]

        logger.debug(f"Returning {len(major_currencies)} supported currencies")
        return major_currencies

    def get_popular_pairs(self) -> List[Tuple[str, str]]:
        """
        人気の通貨ペアを取得

        Returns:
            List[Tuple[str, str]]: 通貨ペアのタプルリスト
        """
        popular_pairs = [
            ("EUR", "USD"),  # EUR/USD
            ("USD", "JPY"),  # USD/JPY
            ("GBP", "USD"),  # GBP/USD
            ("AUD", "USD"),  # AUD/USD
            ("USD", "CAD"),  # USD/CAD
            ("USD", "CHF"),  # USD/CHF
            ("EUR", "JPY"),  # EUR/JPY
            ("EUR", "GBP"),  # EUR/GBP
            ("GBP", "JPY"),  # GBP/JPY
            ("AUD", "JPY"),  # AUD/JPY
        ]

        return popular_pairs

    async def test_connection(self) -> bool:
        """
        API接続をテスト

        Returns:
            bool: 接続成功時True
        """
        try:
            # 簡単なAPI呼び出しでテスト
            await self.get_currency_exchange_rate("USD", "EUR")
            logger.info("Alpha Vantage connection test successful")
            return True
        except Exception as e:
            logger.error(f"Alpha Vantage connection test failed: {str(e)}")
            return False
