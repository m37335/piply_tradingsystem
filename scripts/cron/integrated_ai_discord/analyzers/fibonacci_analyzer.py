#!/usr/bin/env python3
"""
Fibonacci Analyzer Module
フィボナッチリトレースメント分析クラス（期間別階層アプローチ）
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


class FibonacciAnalyzer:
    """フィボナッチリトレースメント分析クラス（期間別階層アプローチ）"""

    def __init__(self):
        self.fibonacci_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        self.timeframe_periods = {
            "D1": 90,  # 3ヶ月間（過去3ヶ月の高値・安値）
            "H4": 42,  # 7日間（過去7日間の高値・安値）
            "H1": 168,  # 7日間（過去7日間の高値・安値）
            "M5": 576,  # 2日間（過去2日間の高値・安値、指標発表時考慮）
        }

    def calculate_fibonacci_analysis(
        self, historical_data: List[Dict], timeframe: str
    ) -> Dict[str, Any]:
        """期間別階層アプローチでフィボナッチ分析"""
        try:
            lookback_days = self.timeframe_periods[timeframe]
            recent_data = historical_data[-lookback_days:]

            if len(recent_data) < 10:  # 最小データ数チェック
                return {
                    "indicator": "Fibonacci Retracement",
                    "timeframe": timeframe,
                    "error": "Insufficient data for analysis",
                }

            # スイングポイント検出
            # データ構造を確認して適切にアクセス

            if hasattr(recent_data, "columns"):  # pandas DataFrameの場合

                swing_high = float(recent_data["High"].max())
                swing_low = float(recent_data["Low"].min())
                current_price = float(recent_data["Close"].iloc[-1])
            elif (
                isinstance(recent_data, list)
                and len(recent_data) > 0
                and hasattr(recent_data[0], "get")
            ):  # 辞書形式の場合
                print(f"Debug Fib {timeframe}: Processing dict format")
                high_values = [
                    float(d.get("High", d.get("high", 0))) for d in recent_data
                ]
                low_values = [float(d.get("Low", d.get("low", 0))) for d in recent_data]
                swing_high = max(high_values)
                swing_low = min(low_values)
                current_price = float(
                    recent_data[-1].get("Close", recent_data[-1].get("close", 0))
                )
            else:  # その他の場合
                # デバッグ用にデータ構造を確認
                print(f"Debug: recent_data type: {type(recent_data)}")
                print(f"Debug: recent_data length: {len(recent_data)}")
                if len(recent_data) > 0:
                    print(f"Debug: recent_data[0] type: {type(recent_data[0])}")
                    print(f"Debug: recent_data[0] content: {recent_data[0]}")
                    # より詳細な構造確認
                    if hasattr(recent_data[0], "__dict__"):
                        print(
                            f"Debug: recent_data[0].__dict__: {recent_data[0].__dict__}"
                        )
                    if hasattr(recent_data[0], "keys"):
                        print(
                            f"Debug: recent_data[0].keys(): "
                            f"{list(recent_data[0].keys())}"
                        )
                raise ValueError(f"Unsupported data structure: {type(recent_data)}")

            # フィボナッチレベル計算
            levels = self._calculate_levels(swing_high, swing_low)

            # 現在価格の位置を判定
            current_position = self._get_current_position(
                current_price, levels, swing_high, swing_low
            )

            return {
                "indicator": "Fibonacci Retracement",
                "timeframe": timeframe,
                "swing_high": swing_high,
                "swing_low": swing_low,
                "current_price": current_price,
                "levels": levels,
                "current_position": current_position,
                "data_points": len(recent_data),
                "timestamp": datetime.now(timezone(timedelta(hours=9))),
            }

        except Exception as e:
            return {
                "indicator": "Fibonacci Retracement",
                "timeframe": timeframe,
                "error": f"Calculation error: {str(e)}",
            }

    def _calculate_levels(
        self, swing_high: float, swing_low: float
    ) -> Dict[str, float]:
        """フィボナッチレベルを計算"""
        diff = swing_high - swing_low

        if abs(diff) < 0.0001:  # ほぼ同じ値の場合
            raise ValueError(
                f"Swing high and low are too close: high={swing_high}, low={swing_low}"
            )

        levels = {}
        for level in self.fibonacci_levels:
            if swing_high > swing_low:  # 上昇トレンドのリトレースメント
                calculated_level = swing_high - (diff * level)
                levels[f"{level*100:.1f}%"] = calculated_level
            else:  # 下降トレンドのリトレースメント
                calculated_level = swing_low + (diff * level)
                levels[f"{level*100:.1f}%"] = calculated_level

        return levels

    def _get_current_position(
        self,
        current_price: float,
        levels: Dict[str, float],
        swing_high: float,
        swing_low: float,
    ) -> Dict[str, Any]:
        """現在価格のフィボナッチ位置を判定（詳細版）"""
        result = {
            "position": "",
            "percentage": 0.0,
            "nearest_level": "",
            "distance_to_nearest": 0.0,
        }

        if swing_high > swing_low:  # 上昇トレンド
            if current_price > swing_high:
                result["position"] = "above_swing_high"
                result["percentage"] = 100.0
                return result
            elif current_price < swing_low:
                result["position"] = "below_swing_low"
                result["percentage"] = 0.0
                return result
            else:
                # フィボナッチリトレースメントのパーセンテージを計算
                total_range = swing_high - swing_low
                retracement = swing_high - current_price
                percentage = (retracement / total_range) * 100
                result["percentage"] = round(percentage, 1)

                # 最も近いレベルを特定
                nearest_level = ""
                min_distance = float("inf")
                for level_name, level_price in levels.items():
                    distance = abs(current_price - level_price)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_level = level_name

                result["nearest_level"] = nearest_level
                result["distance_to_nearest"] = round(min_distance, 4)

                # 位置の判定
                if min_distance < total_range * 0.01:  # 1%以内
                    result["position"] = f"near_{nearest_level}"
                else:
                    result["position"] = f"between_levels_{result['percentage']}%"

                return result
        else:  # 下降トレンド
            if current_price < swing_low:
                result["position"] = "below_swing_low"
                result["percentage"] = 100.0
                return result
            elif current_price > swing_high:
                result["position"] = "below_swing_low"
                result["percentage"] = 0.0
                return result
            else:
                # フィボナッチエクステンションのパーセンテージを計算
                total_range = swing_low - swing_high
                extension = current_price - swing_low
                percentage = (extension / total_range) * 100
                result["percentage"] = round(percentage, 1)

                # 最も近いレベルを特定
                nearest_level = ""
                min_distance = float("inf")
                for level_name, level_price in levels.items():
                    distance = abs(current_price - level_price)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_level = level_name

                result["nearest_level"] = nearest_level
                result["distance_to_nearest"] = round(min_distance, 4)

                # 位置の判定
                if min_distance < abs(total_range) * 0.01:  # 1%以内
                    result["position"] = f"near_{nearest_level}"
                else:
                    result["position"] = f"between_levels_{result['percentage']}%"

                return result
