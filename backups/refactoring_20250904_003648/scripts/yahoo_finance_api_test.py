#!/usr/bin/env python3
"""
Yahoo Finance API仕様調査スクリプト
"""

from datetime import datetime

import pandas as pd
import yfinance as yf


def test_yahoo_finance_api():
    """Yahoo Finance APIの詳細な仕様を調査"""
    try:
        print("🔍 Yahoo Finance API仕様調査開始")
        print("=" * 60)

        # 1. 基本情報
        print("📊 基本情報:")
        ticker = yf.Ticker("USDJPY=X")
        info = ticker.info

        print(f"   - シンボル: USDJPY=X")
        print(f"   - 現在価格: {info.get('regularMarketPrice', 'N/A')}")
        print(f"   - 前日終値: {info.get('previousClose', 'N/A')}")
        print(f"   - 日次高値: {info.get('dayHigh', 'N/A')}")
        print(f"   - 日次安値: {info.get('dayLow', 'N/A')}")
        print(f"   - 出来高: {info.get('volume', 'N/A')}")

        # 2. 利用可能な間隔をテスト
        print("\n📈 利用可能な間隔テスト:")
        intervals = [
            "1m",
            "2m",
            "5m",
            "15m",
            "30m",
            "60m",
            "90m",
            "1h",
            "1d",
            "5d",
            "1wk",
            "1mo",
            "3mo",
        ]
        periods = [
            "1d",
            "5d",
            "1mo",
            "3mo",
            "6mo",
            "1y",
            "2y",
            "5y",
            "10y",
            "ytd",
            "max",
        ]

        for interval in intervals:
            try:
                hist = ticker.history(period="1d", interval=interval)
                if not hist.empty:
                    print(f"   ✅ {interval}: {len(hist)}件取得可能")
                else:
                    print(f"   ❌ {interval}: データなし")
            except Exception as e:
                print(f"   ❌ {interval}: エラー - {str(e)[:50]}")

        # 3. 期間テスト
        print("\n📅 期間テスト (1時間足):")
        for period in periods:
            try:
                hist = ticker.history(period=period, interval="1h")
                if not hist.empty:
                    print(f"   ✅ {period}: {len(hist)}件取得可能")
                else:
                    print(f"   ❌ {period}: データなし")
            except Exception as e:
                print(f"   ❌ {period}: エラー - {str(e)[:50]}")

        # 4. データ品質テスト
        print("\n🔍 データ品質テスト:")

        # 5分足
        hist_5m = ticker.history(period="1d", interval="5m")
        if not hist_5m.empty:
            print(f"   5分足: {len(hist_5m)}件")
            print(f"   最新: {hist_5m.index[-1]} - {hist_5m['Close'].iloc[-1]:.4f}")
            print(
                f"   最新OHLC: O={hist_5m['Open'].iloc[-1]:.4f}, H={hist_5m['High'].iloc[-1]:.4f}, L={hist_5m['Low'].iloc[-1]:.4f}, C={hist_5m['Close'].iloc[-1]:.4f}"
            )

        # 1時間足
        hist_1h = ticker.history(period="7d", interval="1h")
        if not hist_1h.empty:
            print(f"   1時間足: {len(hist_1h)}件")
            print(f"   最新: {hist_1h.index[-1]} - {hist_1h['Close'].iloc[-1]:.4f}")

        # 4時間足
        hist_4h = ticker.history(period="30d", interval="4h")
        if not hist_4h.empty:
            print(f"   4時間足: {len(hist_4h)}件")
            print(f"   最新: {hist_4h.index[-1]} - {hist_4h['Close'].iloc[-1]:.4f}")

        # 日足
        hist_1d = ticker.history(period="1y", interval="1d")
        if not hist_1d.empty:
            print(f"   日足: {len(hist_1d)}件")
            print(f"   最新: {hist_1d.index[-1]} - {hist_1d['Close'].iloc[-1]:.4f}")

        # 5. レート制限テスト
        print("\n⚡ レート制限テスト:")
        print("   複数回の連続取得をテスト...")

        for i in range(5):
            try:
                hist = ticker.history(period="1d", interval="1h")
                print(f"   取得 {i+1}: {len(hist)}件成功")
            except Exception as e:
                print(f"   取得 {i+1}: エラー - {str(e)[:50]}")

        print("\n✅ Yahoo Finance API仕様調査完了")

    except Exception as e:
        print(f"❌ エラー: {e}")


if __name__ == "__main__":
    test_yahoo_finance_api()
