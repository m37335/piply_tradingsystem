#!/usr/bin/env python3
"""
Yahoo Finance Client Test Script
Yahoo Finance クライアントテストスクリプト
"""

import asyncio
import os
import sys
from datetime import datetime

import pytz

# プロジェクトパスを追加
sys.path.append("/app")

from rich.console import Console

from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


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
    console.print(
        f"⏰ テスト時刻: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
    )
    console.print(f"🧪 テストタイプ: {args.test}")
    console.print()

    try:
        if args.test == "connection":
            result = await client.test_connection()
            console.print(f"✅ 接続テスト: {'成功' if result else '失敗'}")

        elif args.test == "rate":
            console.print(f"📊 {args.pair} レート取得テスト...")
            rate_data = await client.get_current_rate(args.pair)
            if rate_data:
                console.print("✅ レート取得成功")
                console.print(f"📊 詳細: {rate_data}")
            else:
                console.print("❌ レート取得失敗")

        elif args.test == "historical":
            console.print(f"📈 {args.pair} 履歴データ取得テスト...")
            hist_data = await client.get_historical_data(
                args.pair, args.period, args.interval
            )
            if hist_data is not None:
                console.print("✅ 履歴データ取得成功")
                console.print(f"📊 データ形状: {hist_data.shape}")
                console.print(f"📈 最新5件:\n{hist_data.tail()}")
            else:
                console.print("❌ 履歴データ取得失敗")

        elif args.test == "multiple":
            console.print("📊 複数通貨ペア取得テスト...")
            pairs = ["USD/JPY", "EUR/USD", "GBP/USD", "AUD/USD", "EUR/JPY"]
            rates_data = await client.get_multiple_rates(pairs)
            client.display_rates_table(rates_data)

    except Exception as e:
        console.print(f"❌ テストエラー: {str(e)}")
        sys.exit(1)

    console.print("\n✅ Yahoo Finance APIテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
