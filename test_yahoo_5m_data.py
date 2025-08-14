#!/usr/bin/env python3
"""
Yahoo Finance 5分足データ直接テスト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


async def test_yahoo_5m_data():
    """Yahoo Financeから5分足データを直接取得してテスト"""

    print("=== Yahoo Finance 5分足データ直接テスト ===")

    try:
        # Yahoo Financeクライアントを初期化
        client = YahooFinanceClient()

        # 5分足データを取得
        print("\n📈 5分足データ取得中...")
        df = await client.get_historical_data("USD/JPY", "1d", "5m")

        if df is None or df.empty:
            print("❌ データが取得できませんでした")
            return

        print(f"\n✅ データ取得成功: {len(df)}件")
        print(f"期間: {df.index[0]} ～ {df.index[-1]}")

        # 最新の5件を表示
        print("\n📊 最新5件のデータ:")
        print("=" * 80)
        print(
            f"{'タイムスタンプ':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<10}"
        )
        print("=" * 80)

        for i in range(min(5, len(df))):
            row = df.iloc[-(i + 1)]  # 最新から表示
            timestamp = row.name.strftime("%Y-%m-%d %H:%M:%S")
            print(
                f"{timestamp:<20} {row['Open']:<10.4f} {row['High']:<10.4f} {row['Low']:<10.4f} {row['Close']:<10.4f} {row['Volume']:<10}"
            )

        # データの統計情報
        print("\n📈 データ統計:")
        print(
            f"Open  - 最小: {df['Open'].min():.4f}, 最大: {df['Open'].max():.4f}, 平均: {df['Open'].mean():.4f}"
        )
        print(
            f"High  - 最小: {df['High'].min():.4f}, 最大: {df['High'].max():.4f}, 平均: {df['High'].mean():.4f}"
        )
        print(
            f"Low   - 最小: {df['Low'].min():.4f}, 最大: {df['Low'].max():.4f}, 平均: {df['Low'].mean():.4f}"
        )
        print(
            f"Close - 最小: {df['Close'].min():.4f}, 最大: {df['Close'].max():.4f}, 平均: {df['Close'].mean():.4f}"
        )

        # 同じ値のデータをチェック
        print("\n🔍 データ品質チェック:")
        same_ohlc_count = 0
        for i, row in df.iterrows():
            if row["Open"] == row["High"] == row["Low"] == row["Close"]:
                same_ohlc_count += 1
                if same_ohlc_count <= 3:  # 最初の3件のみ表示
                    print(
                        f"⚠️  同じOHLC値: {i.strftime('%Y-%m-%d %H:%M:%S')} - {row['Open']:.4f}"
                    )

        if same_ohlc_count > 0:
            print(f"⚠️  同じOHLC値のデータ: {same_ohlc_count}件 / {len(df)}件")
        else:
            print("✅ すべてのデータで異なるOHLC値")

        # 最新データの詳細
        latest = df.iloc[-1]
        print(f"\n🎯 最新データ詳細:")
        print(f"タイムスタンプ: {latest.name}")
        print(f"Open:  {latest['Open']:.4f}")
        print(f"High:  {latest['High']:.4f}")
        print(f"Low:   {latest['Low']:.4f}")
        print(f"Close: {latest['Close']:.4f}")
        print(f"Volume: {latest['Volume']}")

        # 価格変動の確認
        if len(df) > 1:
            prev = df.iloc[-2]
            change = latest["Close"] - prev["Close"]
            change_pct = (change / prev["Close"]) * 100
            print(f"\n📊 価格変動:")
            print(f"前回: {prev['Close']:.4f}")
            print(f"今回: {latest['Close']:.4f}")
            print(f"変動: {change:+.4f} ({change_pct:+.2f}%)")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_yahoo_5m_data())
