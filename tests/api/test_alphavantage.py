#!/usr/bin/env python3
"""
Alpha Vantage API 実データ取得テスト
Exchange Analytics System の実際のマーケットデータ取得機能

機能:
- 為替レート取得
- 株価データ取得
- APIキー検証
- レート制限処理
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class AlphaVantageClient:
    """Alpha Vantage APIクライアント"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.console = Console()

    async def test_connection(self) -> bool:
        """API接続テスト"""
        self.console.print("🔍 Alpha Vantage API接続テスト...")

        try:
            # シンプルな為替レート取得でテスト
            data = await self.get_fx_rate("USD", "JPY")

            if data and "Realtime Currency Exchange Rate" in data:
                self.console.print("✅ Alpha Vantage API接続成功！")
                return True
            else:
                self.console.print("❌ Alpha Vantage API接続失敗")
                self.console.print(f"Response: {data}")
                return False

        except Exception as e:
            self.console.print(f"❌ Alpha Vantage API接続エラー: {str(e)}")
            return False

    async def get_fx_rate(
        self, from_currency: str, to_currency: str
    ) -> Optional[Dict[str, Any]]:
        """為替レート取得"""
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)

                if response.status_code == 200:
                    return response.json()
                else:
                    self.console.print(
                        f"❌ FX rate request failed: HTTP {response.status_code}"
                    )
                    return None

        except Exception as e:
            self.console.print(f"❌ FX rate request error: {str(e)}")
            return None

    async def get_fx_daily(
        self, from_currency: str, to_currency: str
    ) -> Optional[Dict[str, Any]]:
        """日次為替データ取得"""
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)

                if response.status_code == 200:
                    return response.json()
                else:
                    self.console.print(
                        f"❌ FX daily request failed: HTTP {response.status_code}"
                    )
                    return None

        except Exception as e:
            self.console.print(f"❌ FX daily request error: {str(e)}")
            return None

    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """株価クォート取得"""
        params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)

                if response.status_code == 200:
                    return response.json()
                else:
                    self.console.print(
                        f"❌ Stock quote request failed: HTTP {response.status_code}"
                    )
                    return None

        except Exception as e:
            self.console.print(f"❌ Stock quote request error: {str(e)}")
            return None

    def display_fx_rate(
        self, data: Dict[str, Any], from_currency: str, to_currency: str
    ):
        """為替レート表示"""
        if "Realtime Currency Exchange Rate" in data:
            fx_data = data["Realtime Currency Exchange Rate"]

            table = Table(title=f"💱 {from_currency}/{to_currency} Exchange Rate")
            table.add_column("項目", style="cyan")
            table.add_column("値", style="bold green")

            table.add_row("From Currency", fx_data.get("1. From_Currency Code", "N/A"))
            table.add_row("To Currency", fx_data.get("3. To_Currency Code", "N/A"))
            table.add_row("Exchange Rate", fx_data.get("5. Exchange Rate", "N/A"))
            table.add_row("Last Update", fx_data.get("6. Last Refreshed", "N/A"))
            table.add_row("Time Zone", fx_data.get("7. Time Zone", "N/A"))
            table.add_row("Bid Price", fx_data.get("8. Bid Price", "N/A"))
            table.add_row("Ask Price", fx_data.get("9. Ask Price", "N/A"))

            self.console.print(table)
        else:
            self.console.print("❌ 為替レートデータが見つかりません")

    def display_fx_daily(
        self, data: Dict[str, Any], from_currency: str, to_currency: str, limit: int = 5
    ):
        """日次為替データ表示"""
        if "Time Series FX (Daily)" in data:
            fx_series = data["Time Series FX (Daily)"]

            table = Table(title=f"📊 {from_currency}/{to_currency} Daily FX Data")
            table.add_column("Date", style="cyan")
            table.add_column("Open", style="green")
            table.add_column("High", style="bright_green")
            table.add_column("Low", style="red")
            table.add_column("Close", style="bold blue")

            # 最新のデータから制限数表示
            for i, (date, values) in enumerate(list(fx_series.items())[:limit]):
                table.add_row(
                    date,
                    values.get("1. open", "N/A"),
                    values.get("2. high", "N/A"),
                    values.get("3. low", "N/A"),
                    values.get("4. close", "N/A"),
                )

            self.console.print(table)
        else:
            self.console.print("❌ 日次為替データが見つかりません")

    def display_stock_quote(self, data: Dict[str, Any], symbol: str):
        """株価クォート表示"""
        if "Global Quote" in data:
            quote_data = data["Global Quote"]

            table = Table(title=f"📈 {symbol} Stock Quote")
            table.add_column("項目", style="cyan")
            table.add_column("値", style="bold green")

            table.add_row("Symbol", quote_data.get("01. symbol", "N/A"))
            table.add_row("Open", quote_data.get("02. open", "N/A"))
            table.add_row("High", quote_data.get("03. high", "N/A"))
            table.add_row("Low", quote_data.get("04. low", "N/A"))
            table.add_row("Price", quote_data.get("05. price", "N/A"))
            table.add_row("Volume", quote_data.get("06. volume", "N/A"))
            table.add_row(
                "Latest Trading Day", quote_data.get("07. latest trading day", "N/A")
            )
            table.add_row("Previous Close", quote_data.get("08. previous close", "N/A"))
            table.add_row("Change", quote_data.get("09. change", "N/A"))
            table.add_row("Change Percent", quote_data.get("10. change percent", "N/A"))

            self.console.print(table)
        else:
            self.console.print("❌ 株価データが見つかりません")


async def test_multiple_currencies(client: AlphaVantageClient):
    """複数通貨ペアテスト"""
    console = Console()

    currency_pairs = [
        ("USD", "JPY"),
        ("EUR", "USD"),
        ("GBP", "USD"),
        ("USD", "CHF"),
        ("AUD", "USD"),
    ]

    console.print("💱 複数通貨ペア為替レートテスト...")

    for from_curr, to_curr in currency_pairs:
        console.print(f"\n🔍 {from_curr}/{to_curr} レート取得中...")

        fx_data = await client.get_fx_rate(from_curr, to_curr)
        if fx_data:
            client.display_fx_rate(fx_data, from_curr, to_curr)

        # API制限を考慮した間隔
        await asyncio.sleep(15)  # 1分間に5回制限対応


async def test_daily_fx_data(client: AlphaVantageClient):
    """日次為替データテスト"""
    console = Console()

    console.print("📊 日次為替データテスト...")

    daily_data = await client.get_fx_daily("USD", "JPY")
    if daily_data:
        client.display_fx_daily(daily_data, "USD", "JPY")
    else:
        console.print("❌ 日次データ取得失敗")


async def test_stock_data(client: AlphaVantageClient):
    """株価データテスト"""
    console = Console()

    stocks = ["AAPL", "GOOGL", "MSFT", "TSLA"]

    console.print("📈 株価データテスト...")

    for symbol in stocks:
        console.print(f"\n🔍 {symbol} 株価取得中...")

        stock_data = await client.get_stock_quote(symbol)
        if stock_data:
            client.display_stock_quote(stock_data, symbol)

        # API制限を考慮した間隔
        await asyncio.sleep(15)


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Alpha Vantage API Test")
    parser.add_argument(
        "--test",
        choices=["connection", "fx", "daily", "stocks", "all"],
        default="connection",
        help="Test type to run",
    )
    parser.add_argument("--api-key", help="Alpha Vantage API key (or use env var)")

    args = parser.parse_args()

    # APIキー取得
    api_key = args.api_key or os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key or api_key == "demo_key_replace_with_your_key":
        console = Console()
        console.print("❌ Alpha Vantage APIキーが設定されていません")
        console.print("🔧 .envファイルのALPHA_VANTAGE_API_KEYを設定してください")
        console.print("📋 取得方法: https://www.alphavantage.co/support/#api-key")
        sys.exit(1)

    client = AlphaVantageClient(api_key)

    console = Console()
    console.print("🚀 Alpha Vantage API テスト開始")
    console.print(f"🔑 APIキー: {api_key[:8]}{'*' * 8}")
    console.print(f"🧪 テストタイプ: {args.test}")
    console.print()

    if args.test == "connection":
        await client.test_connection()

    elif args.test == "fx":
        fx_data = await client.get_fx_rate("USD", "JPY")
        if fx_data:
            client.display_fx_rate(fx_data, "USD", "JPY")

    elif args.test == "daily":
        await test_daily_fx_data(client)

    elif args.test == "stocks":
        await test_stock_data(client)

    elif args.test == "all":
        # 接続テスト
        success = await client.test_connection()
        if not success:
            console.print("❌ 接続テスト失敗。API設定を確認してください。")
            return

        # 基本為替レート
        console.print("\n" + "=" * 50)
        fx_data = await client.get_fx_rate("USD", "JPY")
        if fx_data:
            client.display_fx_rate(fx_data, "USD", "JPY")

        # 日次データ（API制限を考慮してスキップ）
        console.print("\n📝 日次データと株価データはAPI制限のためスキップしました")
        console.print("🔧 個別テスト: python test_alphavantage.py --test daily")
        console.print("🔧 株価テスト: python test_alphavantage.py --test stocks")

    console.print("\n✅ Alpha Vantage APIテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
