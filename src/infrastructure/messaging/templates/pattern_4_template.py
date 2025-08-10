"""
パターン4通知テンプレート

ブレイクアウト狙い用のDiscord通知テンプレート
"""

from datetime import datetime
from typing import Any, Dict

import pandas as pd


class Pattern4Template:
    """パターン4: ブレイクアウト狙い通知テンプレート"""

    def __init__(self):
        self.pattern_name = "ブレイクアウト狙い"
        self.default_color = "0x00FFFF"  # シアン色
        self.pattern_number = 4

    def create_embed(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        Discord Embed形式の通知を作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            Discord Embed形式の辞書
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confidence_score = detection_result.get("confidence_score", 0.0)
        conditions_met = detection_result.get("conditions_met", {})

        # 条件達成状況を文字列に変換
        conditions_text = []
        for timeframe, met in conditions_met.items():
            status = "✅" if met else "❌"
            conditions_text.append(f"{timeframe}: {status}")

        embed = {
            "title": detection_result.get("notification_title", "🚀 ブレイクアウト狙い！"),
            "description": (
                f"**{currency_pair}** でブレイクアウト狙いを検出しました！\n"
                f"ボリンジャーバンド突破による上昇トレンドの開始です。"
            ),
            "color": int(
                detection_result.get("notification_color", self.default_color), 16
            ),
            "timestamp": current_time,
            "fields": [
                {
                    "name": "🎯 エントリー戦略",
                    "value": (
                        f"**利確**: {detection_result.get('take_profit', '+100pips')}\n"
                        f"**損切り**: {detection_result.get('stop_loss', '-50pips')}\n"
                        f"**戦略**: ブレイクアウト追従"
                    ),
                    "inline": True,
                },
                {
                    "name": "📊 検出条件",
                    "value": "\n".join(conditions_text),
                    "inline": True,
                },
                {
                    "name": "🔍 詳細分析",
                    "value": (
                        f"**信頼度スコア**: {confidence_score:.2f}\n"
                        f"**検出時刻**: {current_time}\n"
                        f"**パターン**: {self.pattern_name}"
                    ),
                    "inline": False,
                },
            ],
            "footer": {
                "text": f"Discord通知システム - {self.pattern_name} | {currency_pair}"
            },
        }

        return embed

    def create_simple_message(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> str:
        """
        シンプルテキスト形式の通知を作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            シンプルテキスト形式のメッセージ
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confidence_score = detection_result.get("confidence_score", 0.0)

        message = (
            f"🚀 **{detection_result.get('notification_title', 'ブレイクアウト狙い！')}**\n\n"
            f"**通貨ペア**: {currency_pair}\n"
            f"**利確**: {detection_result.get('take_profit', '+100pips')}\n"
            f"**損切り**: {detection_result.get('stop_loss', '-50pips')}\n"
            f"**信頼度スコア**: {confidence_score:.2f}\n"
            f"**検出時刻**: {current_time}\n\n"
            f"ボリンジャーバンド突破による上昇トレンドの開始です。"
        )

        return message

    def create_detailed_analysis(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        詳細分析情報を作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            詳細分析情報の辞書
        """
        timeframe_data = detection_result.get("timeframe_data", {})
        conditions_met = detection_result.get("conditions_met", {})

        # 各時間軸の詳細情報を収集
        timeframe_details = {}
        for timeframe, data in timeframe_data.items():
            if not data:
                continue

            price_data = data.get("price_data", pd.DataFrame())
            indicators = data.get("indicators", {})

            if price_data.empty:
                continue

            current_price = price_data["Close"].iloc[-1]
            rsi_data = indicators.get("rsi", {})
            macd_data = indicators.get("macd", {})
            bb_data = indicators.get("bollinger_bands", {})

            # ブレイクアウト強度を計算
            breakout_strength = 0.0
            if bb_data:
                upper_band = bb_data.get("upper", pd.Series()).iloc[-1]
                if current_price > upper_band:
                    breakout_strength = (current_price - upper_band) / upper_band * 100

            timeframe_details[timeframe] = {
                "current_price": current_price,
                "rsi_value": rsi_data.get("current_value", 0.0) if rsi_data else 0.0,
                "macd_value": (
                    macd_data.get("macd", pd.Series()).iloc[-1]
                    if macd_data and "macd" in macd_data
                    else 0.0
                ),
                "bb_upper": (
                    bb_data.get("upper", pd.Series()).iloc[-1] if bb_data else 0.0
                ),
                "breakout_strength": breakout_strength,
                "condition_met": conditions_met.get(timeframe, False),
            }

        return {
            "currency_pair": currency_pair,
            "pattern_name": self.pattern_name,
            "pattern_number": self.pattern_number,
            "detection_time": datetime.now().isoformat(),
            "timeframe_details": timeframe_details,
            "overall_confidence": detection_result.get("confidence_score", 0.0),
            "take_profit": detection_result.get("take_profit", "+100pips"),
            "stop_loss": detection_result.get("stop_loss", "-50pips"),
        }

    def create_breakout_alert(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        ブレイクアウトアラートを作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            ブレイクアウトアラートの辞書
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confidence_score = detection_result.get("confidence_score", 0.0)

        alert = {
            "title": "🚀 ブレイクアウトアラート",
            "message": (
                f"**{currency_pair}** でブレイクアウトを検出しました！\n\n"
                f"**ブレイクアウト強度**: {'強' if confidence_score > 0.7 else '中' if confidence_score > 0.5 else '弱'}\n"
                f"**信頼度スコア**: {confidence_score:.2f}\n"
                f"**検出時刻**: {current_time}\n\n"
                f"**推奨アクション**:\n"
                f"• ブレイクアウト追従でのエントリー\n"
                f"• 適切なストップロス設定\n"
                f"• 利確目標の段階的設定"
            ),
            "urgency": "high" if confidence_score > 0.7 else "medium",
            "timestamp": current_time,
        }

        return alert

    def get_template_info(self) -> Dict[str, Any]:
        """テンプレート情報を取得"""
        return {
            "pattern_name": self.pattern_name,
            "pattern_number": self.pattern_number,
            "default_color": self.default_color,
            "template_type": "breakout_opportunity",
            "description": "ブレイクアウト狙いの通知テンプレート",
        }
