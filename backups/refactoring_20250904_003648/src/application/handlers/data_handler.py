"""
Data Handler
データ取得処理ハンドラー

設計書参照:
- アプリケーション層設計_20250809.md

為替レートデータの取得と管理を行うハンドラー
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...domain.entities.exchange_rate import ExchangeRateEntity
from ...domain.repositories.exchange_rate_repository import ExchangeRateRepository
from ...utils.logging_config import get_application_logger
from ..commands.fetch_rates_command import FetchRatesCommand
from ..queries.get_rates_query import GetRatesQuery
from .base import BaseCommandHandler, BaseQueryHandler

logger = get_application_logger()


class FetchRatesCommandHandler(BaseCommandHandler[FetchRatesCommand, Dict[str, Any]]):
    """
    為替レート取得コマンドハンドラー

    責任:
    - 外部APIからの為替レートデータ取得
    - データベースへの保存
    - データ品質チェック
    """

    def __init__(
        self,
        exchange_rate_repository: ExchangeRateRepository,
        data_fetcher_interface: Any,  # 外部APIインターフェース（後で実装）
    ):
        super().__init__()
        self._repository = exchange_rate_repository
        self._data_fetcher = data_fetcher_interface

    async def _handle_command(self, command: FetchRatesCommand) -> Dict[str, Any]:
        """
        為替レート取得コマンドの処理

        Args:
            command: 為替レート取得コマンド

        Returns:
            Dict[str, Any]: 取得結果サマリー
        """
        logger.info(
            f"Fetching rates for {len(command.currency_pairs)} pairs from {command.source.value}"
        )

        result = {
            "command_id": command.command_id,
            "currency_pairs": command.get_normalized_currency_pairs(),
            "source": command.source.value,
            "interval": command.interval.value,
            "fetched_records": 0,
            "saved_records": 0,
            "skipped_records": 0,
            "errors": [],
            "processing_time": 0.0,
        }

        start_time = datetime.utcnow()

        try:
            # 各通貨ペアに対してデータ取得
            for pair in command.get_normalized_currency_pairs():
                try:
                    pair_result = await self._fetch_pair_data(command, pair)
                    result["fetched_records"] += pair_result["fetched"]
                    result["saved_records"] += pair_result["saved"]
                    result["skipped_records"] += pair_result["skipped"]

                except Exception as e:
                    error_msg = f"Failed to fetch data for {pair}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)

            result["processing_time"] = (datetime.utcnow() - start_time).total_seconds()

            logger.info(
                f"Fetch completed: {result['saved_records']} records saved, "
                f"{result['skipped_records']} skipped, {len(result['errors'])} errors"
            )

            return result

        except Exception as e:
            logger.error(f"Fetch rates command failed: {str(e)}")
            result["errors"].append(str(e))
            result["processing_time"] = (datetime.utcnow() - start_time).total_seconds()
            raise

    async def _fetch_pair_data(
        self, command: FetchRatesCommand, currency_pair: str
    ) -> Dict[str, int]:
        """
        単一通貨ペアのデータ取得

        Args:
            command: 取得コマンド
            currency_pair: 通貨ペア

        Returns:
            Dict[str, int]: 取得結果
        """
        # データソースに応じた取得処理
        if command.source.value == "mock":
            # モックデータの生成（開発・テスト用）
            return await self._fetch_mock_data(command, currency_pair)
        else:
            # 実際の外部API呼び出し（後で実装）
            return await self._fetch_external_data(command, currency_pair)

    async def _fetch_mock_data(
        self, command: FetchRatesCommand, currency_pair: str
    ) -> Dict[str, int]:
        """
        モックデータの生成と保存

        Args:
            command: 取得コマンド
            currency_pair: 通貨ペア

        Returns:
            Dict[str, int]: 処理結果
        """
        import random
        from decimal import Decimal

        from ...domain.value_objects.currency import CurrencyCode, CurrencyPair, Price

        # 通貨ペアを解析
        base_code, quote_code = currency_pair.split("/")
        pair = CurrencyPair(
            base=CurrencyCode(base_code), quote=CurrencyCode(quote_code)
        )

        # 時間範囲の設定
        end_time = command.end_time or datetime.utcnow()
        start_time = command.start_time or (
            end_time - timedelta(hours=command.get_lookback_hours())
        )

        # インターバルに応じたデータ生成
        interval_minutes = self._get_interval_minutes(command.interval.value)
        current_time = start_time

        # 基準価格（通貨ペアに応じて設定）
        base_rates = {
            "USD/JPY": 150.0,
            "EUR/USD": 1.10,
            "GBP/USD": 1.25,
            "USD/CHF": 0.90,
            "AUD/USD": 0.65,
        }
        base_rate = base_rates.get(currency_pair, 1.0)

        entities = []
        current_rate = base_rate

        while current_time <= end_time and len(entities) < command.max_records:
            # ランダムウォークで価格生成
            change_percent = random.gauss(0, 0.001)  # 0.1%の標準偏差
            current_rate *= 1 + change_percent

            # スプレッドをランダム生成
            spread = Price(Decimal(str(random.uniform(0.0001, 0.001))))

            entity = ExchangeRateEntity(
                currency_pair=pair,
                rate=Price(Decimal(str(round(current_rate, 5)))),
                spread=spread,
                source="mock",
                timestamp=current_time,
                volume=random.randint(1000, 10000),
            )

            entities.append(entity)
            current_time += timedelta(minutes=interval_minutes)

        # データベースに保存
        saved_count = 0
        skipped_count = 0

        for entity in entities:
            try:
                # 重複チェック（同じ時刻のデータが既に存在するかチェック）
                existing = await self._check_existing_rate(entity)
                if existing and not command.force_refresh:
                    skipped_count += 1
                    continue

                await self._repository.save(entity)
                saved_count += 1

            except Exception as e:
                logger.warning(f"Failed to save rate data: {str(e)}")
                skipped_count += 1

        return {
            "fetched": len(entities),
            "saved": saved_count,
            "skipped": skipped_count,
        }

    async def _fetch_external_data(
        self, command: FetchRatesCommand, currency_pair: str
    ) -> Dict[str, int]:
        """
        外部APIからのデータ取得

        Args:
            command: 取得コマンド
            currency_pair: 通貨ペア

        Returns:
            Dict[str, int]: 処理結果
        """
        # 外部APIインターフェースを使用してデータ取得
        # 実装は Infrastructure Layer で行う
        logger.info(
            f"External API fetch for {currency_pair} from {command.source.value}"
        )

        # 現在はプレースホルダー
        return {"fetched": 0, "saved": 0, "skipped": 0}

    def _get_interval_minutes(self, interval: str) -> int:
        """
        インターバル文字列を分数に変換

        Args:
            interval: インターバル文字列

        Returns:
            int: 分数
        """
        interval_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }
        return interval_map.get(interval, 1)

    async def _check_existing_rate(self, entity: ExchangeRateEntity) -> bool:
        """
        既存のレートデータをチェック

        Args:
            entity: チェックするエンティティ

        Returns:
            bool: 既存データが存在する場合True
        """
        try:
            # 同じ通貨ペア・時刻のデータが存在するかチェック
            # 簡易実装：時刻の1分以内のデータを検索
            start_check = entity.timestamp - timedelta(minutes=1)
            end_check = entity.timestamp + timedelta(minutes=1)

            existing_rates = await self._repository.find_by_time_range(
                entity.currency_pair, start_check, end_check
            )

            return len(existing_rates) > 0

        except Exception:
            # エラーの場合は存在しないものとして扱う
            return False


class GetRatesQueryHandler(BaseQueryHandler[GetRatesQuery, List[ExchangeRateEntity]]):
    """
    為替レート取得クエリハンドラー

    責任:
    - 為替レートデータの検索・取得
    - フィルタリング・ソート・ページング
    - キャッシュ管理
    """

    def __init__(self, exchange_rate_repository: ExchangeRateRepository):
        super().__init__()
        self._repository = exchange_rate_repository
        # キャッシュは5分間有効
        self.set_cache_config(enabled=True, ttl=300)

    async def _handle_query(self, query: GetRatesQuery) -> List[ExchangeRateEntity]:
        """
        為替レート取得クエリの処理

        Args:
            query: 為替レート取得クエリ

        Returns:
            List[ExchangeRateEntity]: 取得された為替レート一覧
        """
        logger.debug(f"Getting rates with query: {query}")

        # フィルタ条件に基づくデータ取得
        if query.currency_pairs and len(query.currency_pairs) == 1:
            # 単一通貨ペアの場合
            currency_pair_str = query.get_normalized_currency_pairs()[0]
            currency_pair = self._parse_currency_pair(currency_pair_str)

            if query.start_time and query.end_time:
                # 時間範囲指定
                rates = await self._repository.find_by_time_range(
                    currency_pair, query.start_time, query.end_time
                )
            else:
                # 最新データ取得
                rates = await self._repository.find_by_currency_pair(
                    currency_pair, limit=query.limit
                )
        else:
            # 複数通貨ペアまたは全件取得
            rates = await self._repository.find_by_criteria(
                query.get_filter_conditions()
            )

        # 追加フィルタリング
        filtered_rates = await self._apply_additional_filters(rates, query)

        # ソート
        sorted_rates = await self._apply_sorting(filtered_rates, query)

        # ページング
        paginated_rates = await self._apply_pagination(sorted_rates, query)

        logger.debug(f"Retrieved {len(paginated_rates)} rates")
        return paginated_rates

    def _parse_currency_pair(self, pair_str: str):
        """
        通貨ペア文字列をドメインオブジェクトに変換

        Args:
            pair_str: 通貨ペア文字列

        Returns:
            CurrencyPair: 通貨ペアオブジェクト
        """
        from ...domain.value_objects.currency import CurrencyCode, CurrencyPair

        base_code, quote_code = pair_str.split("/")
        return CurrencyPair(
            base=CurrencyCode(base_code), quote=CurrencyCode(quote_code)
        )

    async def _apply_additional_filters(
        self, rates: List[ExchangeRateEntity], query: GetRatesQuery
    ) -> List[ExchangeRateEntity]:
        """
        追加フィルタリングを適用

        Args:
            rates: フィルタ対象のレートリスト
            query: クエリ

        Returns:
            List[ExchangeRateEntity]: フィルタリング後のレートリスト
        """
        filtered = rates

        # レート範囲フィルタ
        if query.min_rate is not None:
            filtered = [r for r in filtered if float(r.rate) >= query.min_rate]

        if query.max_rate is not None:
            filtered = [r for r in filtered if float(r.rate) <= query.max_rate]

        # ソースフィルタ
        if query.sources:
            filtered = [r for r in filtered if r.source in query.sources]

        # 古いデータの除外
        if not query.include_stale:
            filtered = [r for r in filtered if not r.is_stale(query.max_age_minutes)]

        return filtered

    async def _apply_sorting(
        self, rates: List[ExchangeRateEntity], query: GetRatesQuery
    ) -> List[ExchangeRateEntity]:
        """
        ソートを適用

        Args:
            rates: ソート対象のレートリスト
            query: クエリ

        Returns:
            List[ExchangeRateEntity]: ソート後のレートリスト
        """
        from ..queries.get_rates_query import SortField, SortOrder

        reverse = query.sort_order == SortOrder.DESC

        if query.sort_field == SortField.TIMESTAMP:
            return sorted(
                rates, key=lambda r: r.timestamp or datetime.min, reverse=reverse
            )
        elif query.sort_field == SortField.RATE:
            return sorted(rates, key=lambda r: r.rate.value, reverse=reverse)
        elif query.sort_field == SortField.VOLUME:
            return sorted(rates, key=lambda r: r.volume or 0, reverse=reverse)
        elif query.sort_field == SortField.CREATED_AT:
            return sorted(
                rates, key=lambda r: r.created_at or datetime.min, reverse=reverse
            )

        return rates

    async def _apply_pagination(
        self, rates: List[ExchangeRateEntity], query: GetRatesQuery
    ) -> List[ExchangeRateEntity]:
        """
        ページングを適用

        Args:
            rates: ページング対象のレートリスト
            query: クエリ

        Returns:
            List[ExchangeRateEntity]: ページング後のレートリスト
        """
        start_index = query.offset
        end_index = start_index + query.limit

        return rates[start_index:end_index]
