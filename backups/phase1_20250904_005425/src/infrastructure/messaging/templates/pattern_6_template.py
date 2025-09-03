"""
パターン6通知テンプレート

複合シグナル強化用のDiscord通知テンプレート
"""

from datetime import datetime
from typing import Any, Dict

import pandas as pd


class Pattern6Template:
    """パターン6: 複合シグナル強化通知テンプレート"""

    def __init__(self):
        self.pattern_name = "複合シグナル強化"
        self.default_color = "0x800080"  # 紫色
        self.pattern_number = 6

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
            "title": detection_result.get("notification_title", "💪 複合シグナル強化！"),
            "description": (
                f"**{currency_pair}** で複合シグナル強化を検出しました！\n" f"複数の指標が一致し、最高レベルの信頼度です。"
            ),
            "color": int(
                detection_result.get("notification_color", self.default_color), 16
            ),
            "timestamp": current_time,
            "fields": [
                {
                    "name": "🎯 エントリー戦略",
                    "value": (
                        f"**利確**: {detection_result.get('take_profit', '+120pips')}\n"
                        f"**損切り**: {detection_result.get('stop_loss', '-60pips')}\n"
                        f"**信頼度**: {detection_result.get('confidence', '最高（複合シグナル）')}"
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
            f"💪 **{detection_result.get('notification_title', '複合シグナル強化！')}**\n\n"
            f"**通貨ペア**: {currency_pair}\n"
            f"**利確**: {detection_result.get('take_profit', '+120pips')}\n"
            f"**損切り**: {detection_result.get('stop_loss', '-60pips')}\n"
            f"**信頼度**: {detection_result.get('confidence', '最高（複合シグナル）')}\n"
            f"**信頼度スコア**: {confidence_score:.2f}\n"
            f"**検出時刻**: {current_time}\n\n"
            f"複数の指標が一致し、最高レベルの信頼度です。"
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

            # 複合シグナルスコアを計算
            composite_score = 0.0
            signal_count = 0

            # RSIスコア
            if rsi_data and "current_value" in rsi_data:
                rsi_value = rsi_data["current_value"]
                if 30 <= rsi_value <= 70:
                    composite_score += 1.0
                    signal_count += 1

            # MACDスコア
            if macd_data and "macd" in macd_data and "signal" in macd_data:
                current_macd = macd_data["macd"].iloc[-1]
                current_signal = macd_data["signal"].iloc[-1]
                if current_macd > current_signal:
                    composite_score += 1.0
                    signal_count += 1

            # ボリンジャーバンドスコア
            if bb_data:
                upper_band = bb_data.get("upper", pd.Series()).iloc[-1]
                lower_band = bb_data.get("lower", pd.Series()).iloc[-1]
                if lower_band <= current_price <= upper_band:
                    composite_score += 1.0
                    signal_count += 1

            # 価格形状スコア
            if len(price_data) >= 5:
                recent_prices = price_data["Close"].iloc[-5:]
                price_volatility = recent_prices.std() / recent_prices.mean()
                if price_volatility < 0.02:
                    composite_score += 1.0
                    signal_count += 1

            # 平均スコアを計算
            if signal_count > 0:
                composite_score = composite_score / signal_count

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
                "bb_lower": (
                    bb_data.get("lower", pd.Series()).iloc[-1] if bb_data else 0.0
                ),
                "composite_score": composite_score,
                "signal_count": signal_count,
                "condition_met": conditions_met.get(timeframe, False),
            }

        return {
            "currency_pair": currency_pair,
            "pattern_name": self.pattern_name,
            "pattern_number": self.pattern_number,
            "detection_time": datetime.now().isoformat(),
            "timeframe_details": timeframe_details,
            "overall_confidence": detection_result.get("confidence_score", 0.0),
            "take_profit": detection_result.get("take_profit", "+120pips"),
            "stop_loss": detection_result.get("stop_loss", "-60pips"),
            "confidence": detection_result.get("confidence", "最高（複合シグナル）"),
        }

    def create_composite_alert(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        複合シグナルアラートを作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            複合シグナルアラートの辞書
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confidence_score = detection_result.get("confidence_score", 0.0)

        alert = {
            "title": "💪 複合シグナルアラート",
            "message": (
                f"**{currency_pair}** で複合シグナルを検出しました！\n\n"
                f"**シグナル強度**: {'最高' if confidence_score > 0.8 else '高' if confidence_score > 0.6 else '中'}\n"
                f"**信頼度スコア**: {confidence_score:.2f}\n"
                f"**検出時刻**: {current_time}\n\n"
                f"**推奨アクション**:\n"
                f"• 積極的なエントリー検討\n"
                f"• 大きな利確目標設定\n"
                f"• 複数指標による高精度トレード"
            ),
            "urgency": "very_high" if confidence_score > 0.8 else "high",
            "timestamp": current_time,
        }

        return alert

    def get_template_info(self) -> Dict[str, Any]:
        """テンプレート情報を取得"""
        return {
            "pattern_name": self.pattern_name,
            "pattern_number": self.pattern_number,
            "default_color": self.default_color,
            "template_type": "composite_signal",
            "description": "複合シグナル強化の通知テンプレート",
        }
