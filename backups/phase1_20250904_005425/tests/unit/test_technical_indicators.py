#!/usr/bin/env python3
"""
Technical Indicators Test Script
実トレード用テクニカル指標テストスクリプト
"""

import asyncio
import sys
from datetime import datetime

import pytz

# プロジェクトパスを追加
sys.path.append("/app")

from rich.console import Console

from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Technical Indicators Test")
    parser.add_argument("--pair", default="USD/JPY", help="通貨ペア")
    parser.add_argument(
        "--indicator",
        choices=["rsi", "macd", "bb", "multi", "all"],
        default="all",
        help="テストする指標",
    )
    parser.add_argument(
        "--timeframe", choices=["1d", "4h", "1h", "5m"], default="1d", help="時間軸"
    )

    args = parser.parse_args()

    console = Console()
    console.print("📊 Technical Indicators Test 開始")
    console.print(
        f"⏰ 実行時刻: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
    )
    console.print(f"💱 通貨ペア: {args.pair}")
    console.print(f"📈 指標: {args.indicator}")
    console.print(f"⏰ 時間軸: {args.timeframe}")
    console.print()

    try:
        # Yahoo Finance クライアント初期化
        yahoo_client = YahooFinanceClient()

        # テクニカル指標アナライザー初期化
        analyzer = TechnicalIndicatorsAnalyzer()

        if args.indicator == "multi":
            # マルチタイムフレーム分析テスト
            console.print("🔄 マルチタイムフレームデータ取得中...")

            timeframes = {
                "D1": ("1mo", "1d"),  # 1ヶ月、日足
                "H4": ("5d", "1h"),  # 5日、1時間足
                "H1": ("3d", "1h"),  # 3日、1時間足
                "M5": ("1d", "5m"),  # 1日、5分足
            }

            data_dict = {}
            for tf, (period, interval) in timeframes.items():
                console.print(f"  📊 {tf} データ取得中 ({period}, {interval})...")
                hist_data = await yahoo_client.get_historical_data(
                    args.pair, period, interval
                )
                if hist_data is not None and not hist_data.empty:
                    data_dict[tf] = hist_data
                    console.print(f"  ✅ {tf}: {len(hist_data)}件")
                else:
                    console.print(f"  ❌ {tf}: データ取得失敗")

            if data_dict:
                console.print(f"\n📈 マルチタイムフレーム分析実行...")
                analysis = analyzer.multi_timeframe_analysis(data_dict)

                if "error" not in analysis:
                    analyzer.display_analysis_table(analysis, args.pair)
                else:
                    console.print(f"❌ 分析エラー: {analysis['error']}")
            else:
                console.print("❌ データ取得失敗のため分析をスキップ")

        else:
            # 単一指標テスト
            period_map = {
                "1d": ("1mo", "1d"),
                "4h": ("5d", "1h"),
                "1h": ("3d", "1h"),
                "5m": ("1d", "5m"),
            }

            period, interval = period_map[args.timeframe]
            console.print(f"📊 履歴データ取得中 ({period}, {interval})...")

            hist_data = await yahoo_client.get_historical_data(
                args.pair, period, interval
            )

            if hist_data is None or hist_data.empty:
                console.print("❌ データ取得失敗")
                return

            console.print(f"✅ データ取得成功: {len(hist_data)}件")
            console.print(f"📈 期間: {hist_data.index[0]} ～ {hist_data.index[-1]}")
            console.print()

            if args.indicator in ["rsi", "all"]:
                console.print("📈 RSI分析実行...")
                rsi_result = analyzer.calculate_rsi(hist_data, args.timeframe.upper())
                console.print(f"RSI結果: {rsi_result}")
                console.print()

            if args.indicator in ["macd", "all"]:
                console.print("📊 MACD分析実行...")
                macd_result = analyzer.calculate_macd(hist_data, args.timeframe.upper())
                console.print(f"MACD結果: {macd_result}")
                console.print()

            if args.indicator in ["bb", "all"]:
                console.print("🎯 ボリンジャーバンド分析実行...")
                bb_result = analyzer.calculate_bollinger_bands(
                    hist_data, args.timeframe.upper()
                )
                console.print(f"ボリンジャーバンド結果: {bb_result}")
                console.print()

    except Exception as e:
        console.print(f"❌ テストエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    console.print("✅ Technical Indicators Test 完了")


if __name__ == "__main__":
    asyncio.run(main())
