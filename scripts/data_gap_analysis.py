#!/usr/bin/env python3
"""
データ欠損リスク分析スクリプト
"""

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


def analyze_data_gaps():
    """データ欠損リスクを分析"""
    print("🔍 データ欠損リスク分析開始")
    print("=" * 60)

    # 1. 各時間足の取得可能期間を確認
    print("📊 各時間足の取得可能期間:")

    timeframes = {
        "5m": {"period": "7d", "interval": "5m", "description": "5分足"},
        "1h": {"period": "30d", "interval": "1h", "description": "1時間足"},
        "4h": {"period": "60d", "interval": "4h", "description": "4時間足"},
        "1d": {"period": "365d", "interval": "1d", "description": "日足"},
    }

    ticker = yf.Ticker("USDJPY=X")
    results = {}

    for timeframe, config in timeframes.items():
        try:
            print(f"\n📈 {timeframe}時間足分析:")

            # 直接取得テスト
            hist = ticker.history(period=config["period"], interval=config["interval"])

            if not hist.empty:
                data_count = len(hist)
                start_date = hist.index[0]
                end_date = hist.index[-1]
                expected_count = _calculate_expected_count(
                    config["period"], config["interval"]
                )

                print(f"   ✅ 直接取得可能: {data_count}件")
                print(f"   📅 期間: {start_date} ～ {end_date}")
                print(f"   📊 期待値: {expected_count}件")
                print(f"   📈 充足率: {(data_count/expected_count)*100:.1f}%")

                # 欠損分析
                gaps = _analyze_gaps(hist, config["interval"])
                print(f"   🔍 欠損箇所: {len(gaps)}箇所")

                results[timeframe] = {
                    "direct_count": data_count,
                    "expected_count": expected_count,
                    "coverage_rate": data_count / expected_count,
                    "gaps": gaps,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            else:
                print(f"   ❌ 直接取得不可")
                results[timeframe] = {"direct_count": 0, "gaps": []}

        except Exception as e:
            print(f"   ❌ エラー: {e}")
            results[timeframe] = {"error": str(e)}

    # 2. 集計補完の可能性分析
    print("\n🔧 集計補完可能性分析:")

    # 5分足から集計可能な期間
    if "5m" in results and results["5m"]["direct_count"] > 0:
        m5_coverage = results["5m"]["coverage_rate"]
        print(f"   5分足充足率: {m5_coverage*100:.1f}%")

        # 各時間足の集計可能性
        aggregation_requirements = {
            "1h": {"min_5m": 12, "description": "1時間足"},
            "4h": {"min_5m": 48, "description": "4時間足"},
            "1d": {"min_5m": 288, "description": "日足"},
        }

        for tf, req in aggregation_requirements.items():
            if tf in results:
                can_aggregate = results["5m"]["direct_count"] >= req["min_5m"]
                print(f"   {req['description']}: {'✅' if can_aggregate else '❌'} 集計可能")

    # 3. 代替集計元の検討
    print("\n🔄 代替集計元の検討:")

    # 1時間足から4時間足への集計
    if "1h" in results and results["1h"]["direct_count"] > 0:
        h1_count = results["1h"]["direct_count"]
        h1_to_4h_possible = h1_count >= 4  # 4時間足は1時間足4件必要
        print(f"   1時間足→4時間足集計: {'✅' if h1_to_4h_possible else '❌'} 可能")

    # 4時間足から日足への集計
    if "4h" in results and results["4h"]["direct_count"] > 0:
        h4_count = results["4h"]["direct_count"]
        h4_to_1d_possible = h4_count >= 6  # 日足は4時間足6件必要
        print(f"   4時間足→日足集計: {'✅' if h4_to_1d_possible else '❌'} 可能")

    # 4. 推奨戦略
    print("\n💡 推奨戦略:")

    # 優先順位を決定
    priorities = _determine_priorities(results)

    for i, (timeframe, priority) in enumerate(priorities, 1):
        print(f"   {i}. {timeframe}: {priority}")

    return results


def _calculate_expected_count(period: str, interval: str) -> int:
    """期待されるデータ件数を計算"""
    # 期間を日数に変換
    period_days = {
        "1d": 1,
        "5d": 5,
        "7d": 7,
        "30d": 30,
        "60d": 60,
        "90d": 90,
        "180d": 180,
        "365d": 365,
        "730d": 730,
    }

    # 間隔を分に変換
    interval_minutes = {
        "1m": 1,
        "2m": 2,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "60m": 60,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }

    days = period_days.get(period, 30)
    minutes = interval_minutes.get(interval, 60)

    # 営業時間を考慮（24時間市場）
    total_minutes = days * 24 * 60
    expected_count = total_minutes // minutes

    return expected_count


def _analyze_gaps(hist: pd.DataFrame, interval: str) -> list:
    """データの欠損箇所を分析"""
    gaps = []

    if len(hist) < 2:
        return gaps

    # 間隔を分に変換
    interval_minutes = {
        "1m": 1,
        "2m": 2,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "60m": 60,
        "1h": 60,
        "4h": 240,
        "1d": 1440,
    }

    expected_interval = interval_minutes.get(interval, 60)

    # タイムスタンプの差分をチェック
    timestamps = hist.index.sort_values()

    for i in range(1, len(timestamps)):
        diff = timestamps[i] - timestamps[i - 1]
        diff_minutes = diff.total_seconds() / 60

        # 期待される間隔の2倍以上なら欠損とみなす
        if diff_minutes > expected_interval * 2:
            gaps.append(
                {
                    "start": timestamps[i - 1],
                    "end": timestamps[i],
                    "gap_minutes": diff_minutes,
                    "expected_minutes": expected_interval,
                }
            )

    return gaps


def _determine_priorities(results: dict) -> list:
    """データ取得の優先順位を決定"""
    priorities = []

    # 充足率が高い順にソート
    sorted_timeframes = sorted(
        [(tf, data) for tf, data in results.items() if "coverage_rate" in data],
        key=lambda x: x[1]["coverage_rate"],
        reverse=True,
    )

    for timeframe, data in sorted_timeframes:
        if data["coverage_rate"] > 0.8:
            priorities.append((timeframe, "直接取得優先"))
        elif data["coverage_rate"] > 0.5:
            priorities.append((timeframe, "直接取得 + 集計補完"))
        else:
            priorities.append((timeframe, "集計補完依存"))

    return priorities


if __name__ == "__main__":
    analyze_data_gaps()
