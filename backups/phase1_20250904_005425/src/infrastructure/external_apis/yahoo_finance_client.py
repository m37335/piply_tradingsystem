"""
Yahoo Finance Client
Yahoo Finance APIクライアント - 無料データソース

設計書参照:
- インフラ・プラグイン設計_20250809.md

機能:
- リアルタイム為替レート取得
- 履歴データ取得 (テクニカル指標用)
- 複数通貨ペア対応
- エラーハンドリング
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pytz
import yfinance as yf
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...domain.entities.exchange_rate import ExchangeRateEntity
from ...domain.value_objects.currency import CurrencyCode, CurrencyPair, Price
from ...utils.logging_config import get_infrastructure_logger
from .base_client import APIError, BaseAPIClient

logger = get_infrastructure_logger()


class YahooFinanceClient(BaseAPIClient):
    """
    Yahoo Finance APIクライアント

    責任:
    - 為替レートの取得
    - 履歴データの取得
    - データの正規化
    - エラーハンドリング

    利点:
    - 無料・無制限
    - 豊富な履歴データ
    - テクニカル指標計算対応
    """

    def __init__(self, **kwargs):
        """
        初期化

        Args:
            **kwargs: BaseAPIClientの引数
        """
        super().__init__(
            base_url="https://query1.finance.yahoo.com",
            api_key="",  # Yahoo Finance は API キー不要
            rate_limit_calls=100,  # 制限は緩い
            rate_limit_period=60,
            **kwargs,
        )

        self.console = Console()
        self.jst = pytz.timezone("Asia/Tokyo")

        # リトライ設定
        self.max_retries = 3
        self.retry_delay = 2.0  # 秒
        self.rate_limit_delay = 5.0  # レート制限時の待機時間

        # 通貨マッピング初期化
        self._init_currency_mapping()

        logger.info("Initialized Yahoo Finance client")

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """リトライ機構付きでAPIコールを実行"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return (
                    await func(*args, **kwargs)
                    if asyncio.iscoroutinefunction(func)
                    else func(*args, **kwargs)
                )
            except Exception as e:
                last_exception = e
                error_msg = str(e).lower()

                # レート制限エラーの場合
                if "429" in error_msg or "too many requests" in error_msg:
                    if attempt < self.max_retries:
                        wait_time = self.rate_limit_delay * (
                            2**attempt
                        )  # 指数バックオフ
                        logger.warning(
                            f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{self.max_retries}"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                # その他のエラーの場合
                elif attempt < self.max_retries:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"API error, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue

                # 最後の試行でも失敗
                break

        # 全ての試行が失敗
        logger.error(f"All retry attempts failed: {str(last_exception)}")
        raise last_exception

    def _init_currency_mapping(self):
        """為替ペアのマッピング初期化"""
        self.fx_mapping = {
            "USD/JPY": "USDJPY=X",
            "EUR/USD": "EURUSD=X",
            "GBP/USD": "GBPUSD=X",
            "USD/CHF": "USDCHF=X",
            "AUD/USD": "AUDUSD=X",
            "USD/CAD": "USDCAD=X",
            "EUR/JPY": "EURJPY=X",
            "GBP/JPY": "GBPJPY=X",
            "CHF/JPY": "CHFJPY=X",
            "AUD/JPY": "AUDJPY=X",
            "CAD/JPY": "CADJPY=X",
            "EUR/GBP": "EURGBP=X",
            "EUR/CHF": "EURCHF=X",
            "GBP/CHF": "GBPCHF=X",
        }

    def _get_auth_params(self) -> Dict[str, str]:
        """
        認証パラメータを取得
        Yahoo Finance は認証不要のため空辞書を返す

        Returns:
            Dict[str, str]: 空の辞書
        """
        return {}

    def get_yahoo_symbol(self, currency_pair: str) -> str:
        """通貨ペアをYahoo Finance形式に変換"""
        return self.fx_mapping.get(currency_pair, currency_pair)

    async def test_connection(self) -> bool:
        """Yahoo Finance接続テスト"""
        try:
            self.console.print("🧪 Yahoo Finance接続テスト...")

            # テスト用にUSD/JPYのデータを取得
            ticker = yf.Ticker("USDJPY=X")
            info = ticker.info

            if info and "regularMarketPrice" in info:
                self.console.print("✅ Yahoo Finance接続成功")
                self.console.print(
                    f"📊 USD/JPY: {info.get('regularMarketPrice', 'N/A')}"
                )
                return True
            else:
                self.console.print("❌ Yahoo Finance接続失敗: データなし")
                return False

        except Exception as e:
            self.console.print(f"❌ Yahoo Finance接続エラー: {str(e)}")
            return False

    async def get_current_rate(self, currency_pair: str) -> Optional[Dict[str, Any]]:
        """リアルタイム為替レート取得"""
        try:
            symbol = self.get_yahoo_symbol(currency_pair)
            self.console.print(f"📊 {currency_pair} ({symbol}) レート取得中...")

            # リトライ機構付きでyfinanceを呼び出し
            def _get_ticker_info():
                ticker = yf.Ticker(symbol)
                return ticker.info

            info = await self._retry_with_backoff(_get_ticker_info)

            if not info or "regularMarketPrice" not in info:
                self.console.print(f"❌ {currency_pair}: データなし")
                return None

            current_time = datetime.now(self.jst)

            rate_data = {
                "currency_pair": currency_pair,
                "rate": info.get("regularMarketPrice"),
                "bid": info.get("bid"),
                "ask": info.get("ask"),
                "previous_close": info.get("previousClose"),
                "day_high": info.get("dayHigh"),
                "day_low": info.get("dayLow"),
                "market_change": info.get("regularMarketChange"),
                "market_change_percent": info.get("regularMarketChangePercent"),
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S JST"),
                "data_source": "Yahoo Finance",
                "symbol": symbol,
            }

            self.console.print(f"✅ {currency_pair}: {rate_data['rate']}")
            return rate_data

        except Exception as e:
            self.console.print(f"❌ {currency_pair} レート取得エラー: {str(e)}")
            return None

    async def get_historical_data(
        self, currency_pair: str, period: str = "1mo", interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """履歴データ取得 (テクニカル指標用)"""
        try:
            symbol = self.get_yahoo_symbol(currency_pair)
            self.console.print(f"📈 {currency_pair} 履歴データ取得中...")
            self.console.print(f"   期間: {period}, 間隔: {interval}")

            # リトライ機構付きで履歴データを取得
            def _get_ticker_history():
                ticker = yf.Ticker(symbol)
                return ticker.history(period=period, interval=interval)

            hist = await self._retry_with_backoff(_get_ticker_history)

            if hist.empty:
                self.console.print(f"❌ {currency_pair}: 履歴データなし")
                return None

            # データを日本時間に変換（データベース保存用）
            if hist.index.tz is not None:
                hist.index = hist.index.tz_convert(self.jst)
            else:
                # タイムゾーン情報がない場合は日本時間として扱う
                hist.index = hist.index.tz_localize(self.jst)

            # 基本統計表示
            self.console.print(f"✅ {currency_pair}: {len(hist)}件のデータ取得")
            self.console.print(f"   期間: {hist.index[0]} ～ {hist.index[-1]}")
            self.console.print(f"   最新価格: {hist['Close'].iloc[-1]:.4f}")

            return hist

        except Exception as e:
            self.console.print(f"❌ {currency_pair} 履歴データエラー: {str(e)}")
            return None

    async def get_multiple_rates(self, currency_pairs: List[str]) -> Dict[str, Any]:
        """複数通貨ペアのレート一括取得"""
        self.console.print(f"📊 {len(currency_pairs)}通貨ペアのレート取得開始...")

        results = {}
        successful = 0
        failed = 0

        for i, pair in enumerate(currency_pairs):
            try:
                rate_data = await self.get_current_rate(pair)
                if rate_data:
                    results[pair] = rate_data
                    successful += 1
                    self.console.print(f"✅ {pair}: レート取得成功")
                else:
                    failed += 1
                    self.console.print(f"❌ {pair}: データなし")

                # レート制限対応 - 複数リクエスト間の間隔を長めに
                if i < len(currency_pairs) - 1:  # 最後以外
                    await asyncio.sleep(2.0)  # 2秒間隔

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    self.console.print(f"⚠️ {pair}: レート制限エラー - 少し待機します")
                    await asyncio.sleep(10.0)  # レート制限時は10秒待機
                else:
                    self.console.print(f"❌ {pair}: {error_msg}")
                failed += 1

        # 結果サマリー
        self.console.print(f"\n📊 取得結果: 成功 {successful}件, 失敗 {failed}件")

        return {
            "rates": results,
            "summary": {
                "successful": successful,
                "failed": failed,
                "total": len(currency_pairs),
            },
            "timestamp": datetime.now(self.jst).strftime("%Y-%m-%d %H:%M:%S JST"),
            "data_source": "Yahoo Finance",
        }

    def display_rates_table(self, rates_data: Dict[str, Any]) -> None:
        """為替レートをテーブル表示"""
        if not rates_data.get("rates"):
            self.console.print("❌ 表示するデータがありません")
            return

        table = Table(title="💱 Yahoo Finance 為替レート")
        table.add_column("通貨ペア", style="cyan")
        table.add_column("レート", style="green")
        table.add_column("変動", style="yellow")
        table.add_column("変動%", style="yellow")
        table.add_column("高値", style="blue")
        table.add_column("安値", style="blue")

        for pair, data in rates_data["rates"].items():
            change = data.get("market_change", 0) or 0
            change_pct = data.get("market_change_percent", 0) or 0
            change_color = "green" if change >= 0 else "red"

            table.add_row(
                pair,
                f"{data.get('rate', 'N/A'):.4f}" if data.get("rate") else "N/A",
                f"[{change_color}]{change:+.4f}[/{change_color}]" if change else "N/A",
                (
                    f"[{change_color}]{change_pct:+.2f}%[/{change_color}]"
                    if change_pct
                    else "N/A"
                ),
                f"{data.get('day_high', 'N/A'):.4f}" if data.get("day_high") else "N/A",
                f"{data.get('day_low', 'N/A'):.4f}" if data.get("day_low") else "N/A",
            )

        self.console.print(table)

        # サマリー情報
        summary = rates_data.get("summary", {})
        panel_content = f"""
📊 取得結果: {summary.get('successful', 0)}/{summary.get('total', 0)} 成功
⏰ 取得時刻: {rates_data.get('timestamp', 'N/A')}
🌐 データソース: {rates_data.get('data_source', 'Yahoo Finance')}
        """
        self.console.print(Panel.fit(panel_content, title="📈 取得統計"))


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Yahoo Finance Client Test")
    parser.add_argument(
        "--test",
        choices=["connection", "rate", "historical", "multiple"],
        default="connection",
    )
    parser.add_argument("--pair", default="USD/JPY", help="通貨ペア")
    parser.add_argument("--period", default="1mo", help="履歴データ期間")
    parser.add_argument("--interval", default="1d", help="履歴データ間隔")

    args = parser.parse_args()

    client = YahooFinanceClient()

    console = Console()
    console.print("🌐 Yahoo Finance API テスト開始")
    console.print(f"🧪 テストタイプ: {args.test}")
    console.print()

    if args.test == "connection":
        await client.test_connection()

    elif args.test == "rate":
        rate_data = await client.get_current_rate(args.pair)
        if rate_data:
            console.print("✅ レート取得成功")
            console.print(f"📊 詳細: {rate_data}")

    elif args.test == "historical":
        hist_data = await client.get_historical_data(
            args.pair, args.period, args.interval
        )
        if hist_data is not None:
            console.print("✅ 履歴データ取得成功")
            console.print(f"📊 データ形状: {hist_data.shape}")
            console.print(f"📈 最新5件:\n{hist_data.tail()}")

    elif args.test == "multiple":
        pairs = ["USD/JPY", "EUR/USD", "GBP/USD", "AUD/USD", "EUR/JPY"]
        rates_data = await client.get_multiple_rates(pairs)
        client.display_rates_table(rates_data)

    console.print("\n✅ Yahoo Finance APIテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
