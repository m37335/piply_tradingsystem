#!/usr/bin/env python3
"""
テスト用シンプルパターン検出器
"""

from datetime import datetime
from typing import Any, Dict, Optional


class SimplePatternDetector:
    """
    テスト用シンプルパターン検出器
    """

    def __init__(self, pattern_number: int):
        self.pattern_number = pattern_number
        self.pattern_names = {
            1: "トレンド転換",
            2: "押し目・戻り売り",
            3: "ダイバージェンス",
            4: "ブレイクアウト",
            5: "RSI50ライン攻防",
            6: "複合シグナル",
        }

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        シンプルなパターン検出

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            検出結果の辞書、検出されない場合はNone
        """
        try:
            # M5データを取得
            m5_data = multi_timeframe_data.get("M5", {})
            if not m5_data:
                return None

            indicators = m5_data.get("indicators", {})

            # RSIデータをチェック
            rsi_data = indicators.get("rsi", {})
            rsi_value = rsi_data.get("current_value", 0) if rsi_data else 0

            # MACDデータをチェック
            macd_data = indicators.get("macd", {})
            macd_value = macd_data.get("macd", 0) if macd_data else 0

            # パターン検出条件
            pattern_detected = False
            confidence = 0.0
            direction = "NEUTRAL"

            if self.pattern_number == 1:  # トレンド転換
                if rsi_value > 70:
                    pattern_detected = True
                    confidence = 0.8
                    direction = "SELL"

            elif self.pattern_number == 2:  # 押し目・戻り売り
                if 30 < rsi_value < 70:
                    pattern_detected = True
                    confidence = 0.7
                    direction = "BUY"

            elif self.pattern_number == 3:  # ダイバージェンス
                if rsi_value < 30:
                    pattern_detected = True
                    confidence = 0.75
                    direction = "BUY"

            elif self.pattern_number == 4:  # ブレイクアウト
                if abs(macd_value) > 0.01:
                    pattern_detected = True
                    confidence = 0.6
                    direction = "BUY" if macd_value > 0 else "SELL"

            elif self.pattern_number == 5:  # RSI50ライン攻防
                if 45 < rsi_value < 55:
                    pattern_detected = True
                    confidence = 0.65
                    direction = "NEUTRAL"

            elif self.pattern_number == 6:  # 複合シグナル
                if rsi_value > 60 and macd_value > 0:
                    pattern_detected = True
                    confidence = 0.85
                    direction = "BUY"

            if pattern_detected:
                return {
                    "pattern_number": self.pattern_number,
                    "pattern_name": self.pattern_names.get(
                        self.pattern_number, f"Pattern {self.pattern_number}"
                    ),
                    "priority": 80,
                    "conditions_met": {
                        "rsi_condition": rsi_value > 50,
                        "macd_condition": abs(macd_value) > 0.001,
                    },
                    "confidence": confidence,
                    "timestamp": datetime.now(),
                    "title": f"{self.pattern_names.get(self.pattern_number, 'Pattern')} Detected",
                    "color": "#FF6B6B",
                    "strategy": f"Strategy for {self.pattern_names.get(self.pattern_number, 'pattern')}",
                    "entry_condition": f"RSI: {rsi_value:.2f}, MACD: {macd_value:.6f}",
                    "take_profit": "150.50",
                    "stop_loss": "149.50",
                    "technical_data": {
                        "rsi": rsi_value,
                        "macd": macd_value,
                        "direction": direction,
                    },
                }

            return None

        except Exception as e:
            print(f"Error in simple pattern detection: {e}")
            return None
