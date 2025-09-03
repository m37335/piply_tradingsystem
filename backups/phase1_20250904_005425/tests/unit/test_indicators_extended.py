#!/usr/bin/env python3
"""
Technical Indicators Extended Test Script
MACD計算対応のため長期データ使用版
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

    parser = argparse.ArgumentParser(description="Technical Indicators Extended Test")
    parser.add_argument("--pair", default="USD/JPY", help="通貨ペア")
    parser.add_argument(
        "--indicator",
        choices=["rsi", "macd", "bb", "multi", "all"],
        default="multi",
        help="テストする指標",
    )

    args = parser.parse_args()

    console = Console()
    console.print("📊 Technical Indicators Extended Test 開始")
    console.print(
        f"⏰ 実行時刻: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
    )
    console.print(f"💱 通貨ペア: {args.pair}")
    console.print(f"📈 指標: {args.indicator}")
    console.print()

    try:
        # Yahoo Finance クライアント初期化
        yahoo_client = YahooFinanceClient()

        # テクニカル指標アナライザー初期化
        analyzer = TechnicalIndicatorsAnalyzer()

        if args.indicator == "multi":
            # マルチタイムフレーム分析テスト（長期データ版）
            console.print("🔄 マルチタイムフレームデータ取得中（長期データ版）...")

            timeframes = {
                "D1": ("6mo", "1d"),  # 6ヶ月、日足（MACD対応）
                "H4": ("1mo", "1h"),  # 1ヶ月、1時間足
                "H1": ("1wk", "1h"),  # 1週間、1時間足
                "M5": ("2d", "5m"),  # 2日、5分足
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
                console.print(f"\n📈 マルチタイムフレーム分析実行（長期データ版）...")
                analysis = analyzer.multi_timeframe_analysis(data_dict)

                if "error" not in analysis:
                    analyzer.display_analysis_table(analysis, args.pair)

                    # MACD計算成功の確認
                    if "D1" in analysis.get("timeframes", {}):
                        d1_macd = analysis["timeframes"]["D1"].get("MACD", {})
                        if "error" not in d1_macd:
                            console.print("\n✅ MACD計算成功！")
                            console.print(
                                f"   MACD値: {d1_macd.get('macd_line', 'N/A')}"
                            )
                            console.print(
                                f"   シグナル: {d1_macd.get('signal_line', 'N/A')}"
                            )
                            console.print(
                                f"   クロス: {d1_macd.get('cross_signal', 'N/A')}"
                            )
                        else:
                            console.print(
                                f"\n⚠️ MACD計算失敗: {d1_macd.get('error', 'Unknown')}"
                            )
                            console.print(
                                f"   推奨: {d1_macd.get('recommendation', 'N/A')}"
                            )
                else:
                    console.print(f"❌ 分析エラー: {analysis['error']}")
            else:
                console.print("❌ データ取得失敗のため分析をスキップ")

        elif args.indicator == "macd":
            # MACD特別テスト（長期データ）
            console.print("📊 MACD長期データテスト...")

            periods = ["3mo", "6mo", "1y"]
            for period in periods:
                console.print(f"\n📈 {period} データでMACDテスト...")
                hist_data = await yahoo_client.get_historical_data(
                    args.pair, period, "1d"
                )

                if hist_data is not None and not hist_data.empty:
                    console.print(f"✅ データ取得: {len(hist_data)}件")
                    macd_result = analyzer.calculate_macd(hist_data, "D1")

                    if "error" not in macd_result:
                        console.print(f"✅ MACD計算成功:")
                        console.print(f"   MACD: {macd_result.get('macd_line', 'N/A')}")
                        console.print(
                            f"   Signal: {macd_result.get('signal_line', 'N/A')}"
                        )
                        console.print(
                            f"   Histogram: {macd_result.get('histogram', 'N/A')}"
                        )
                        console.print(
                            f"   Cross: {macd_result.get('cross_signal', 'N/A')}"
                        )
                        break  # 成功したら終了
                    else:
                        console.print(
                            f"❌ MACD計算失敗: {macd_result.get('error', 'Unknown')}"
                        )
                else:
                    console.print(f"❌ データ取得失敗")

        elif args.indicator in ["rsi", "bb", "all"]:
            # 既存のテスト
            period, interval = ("1mo", "1d")
            console.print(f"📊 履歴データ取得中 ({period}, {interval})...")

            hist_data = await yahoo_client.get_historical_data(
                args.pair, period, interval
            )

            if hist_data is None or hist_data.empty:
                console.print("❌ データ取得失敗")
                return

            console.print(f"✅ データ取得成功: {len(hist_data)}件")

            if args.indicator in ["rsi", "all"]:
                console.print("📈 RSI分析実行...")
                rsi_result = analyzer.calculate_rsi(hist_data, "D1")
                console.print(f"RSI結果: {rsi_result}")

            if args.indicator in ["bb", "all"]:
                console.print("🎯 ボリンジャーバンド分析実行...")
                bb_result = analyzer.calculate_bollinger_bands(hist_data, "D1")
                console.print(f"ボリンジャーバンド結果: {bb_result}")

    except Exception as e:
        console.print(f"❌ テストエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    console.print("✅ Technical Indicators Extended Test 完了")


if __name__ == "__main__":
    asyncio.run(main())
