"""
パターン1通知テンプレート

強力なトレンド転換シグナル用のDiscord通知テンプレート
"""

from datetime import datetime
from typing import Any, Dict

import pandas as pd


class Pattern1Template:
    """強力なトレンド転換シグナル通知テンプレート"""

    def __init__(self):
        self.pattern_name = "強力なトレンド転換シグナル"
        self.pattern_number = 1
        self.default_color = "0xFF0000"  # 赤色

    def create_embed(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        Discord Embedを作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            Discord Embed辞書
        """
        # 基本情報
        title = detection_result.get("notification_title", "🚨 強力な売りシグナル検出！")
        color = int(detection_result.get("notification_color", self.default_color), 16)

        # 現在価格を取得
        current_price = self._get_current_price(detection_result)

        # エントリー情報
        take_profit = detection_result.get("take_profit", "-50pips")
        stop_loss = detection_result.get("stop_loss", "+30pips")

        # 信頼度スコア
        confidence_score = detection_result.get("confidence_score", 0.0)
        confidence_text = self._get_confidence_text(confidence_score)

        # 条件達成状況
        conditions_met = detection_result.get("conditions_met", {})
        conditions_text = self._format_conditions(conditions_met)

        # Embed作成
        embed = {
            "title": title,
            "color": color,
            "description": f"📊 **{currency_pair}** 全時間軸一致",
            "fields": [
                {
                    "name": "🎯 **エントリー情報**",
                    "value": f"**現在価格**: {current_price}\n"
                    f"**利確**: {take_profit}\n"
                    f"**損切り**: {stop_loss}",
                    "inline": True,
                },
                {"name": "📈 **根拠**", "value": conditions_text, "inline": False},
                {
                    "name": "⚠️ **注意事項**",
                    "value": "• 急落リスク高\n• 全時間軸一致による強力シグナル\n• 即座のエントリー推奨",
                    "inline": False,
                },
                {
                    "name": "✅ **信頼度**",
                    "value": f"{confidence_text} ({confidence_score:.1%})",
                    "inline": True,
                },
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": f"パターン{self.pattern_number} - {self.pattern_name}"},
        }

        return embed

    def create_simple_message(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> str:
        """
        シンプルなテキストメッセージを作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            テキストメッセージ
        """
        current_price = self._get_current_price(detection_result)
        take_profit = detection_result.get("take_profit", "-50pips")
        stop_loss = detection_result.get("stop_loss", "+30pips")
        confidence_score = detection_result.get("confidence_score", 0.0)

        message = (
            f"🚨 **強力な売りシグナル検出！**\n"
            f"📊 {currency_pair} 全時間軸一致\n\n"
            f"🎯 **エントリー**: {current_price}\n"
            f"🎯 **利確**: {take_profit}\n"
            f"🎯 **損切り**: {stop_loss}\n\n"
            f"📈 **根拠**:\n"
            f"• D1: RSI過熱 + MACD転換\n"
            f"• H4: ボリンジャーバンド上限\n"
            f"• H1: 短期過熱確認\n"
            f"• M5: 実行タイミング\n\n"
            f"⚠️ **注意**: 急落リスク高\n"
            f"✅ **信頼度**: {confidence_score:.1%}"
        )

        return message

    def _get_current_price(self, detection_result: Dict[str, Any]) -> str:
        """現在価格を取得"""
        timeframe_data = detection_result.get("timeframe_data", {})

        # M5の最新価格を優先
        if "M5" in timeframe_data:
            m5_data = timeframe_data["M5"]
            price_data = m5_data.get("price_data", pd.DataFrame())
            if not price_data.empty:
                return f"{price_data['Close'].iloc[-1]:.3f}"

        # フォールバック: H1の最新価格
        if "H1" in timeframe_data:
            h1_data = timeframe_data["H1"]
            price_data = h1_data.get("price_data", pd.DataFrame())
            if not price_data.empty:
                return f"{price_data['Close'].iloc[-1]:.3f}"

        return "N/A"

    def _get_confidence_text(self, confidence_score: float) -> str:
        """信頼度テキストを取得"""
        if confidence_score >= 0.9:
            return "最高"
        elif confidence_score >= 0.8:
            return "高"
        elif confidence_score >= 0.7:
            return "中高"
        elif confidence_score >= 0.6:
            return "中"
        else:
            return "低"

    def _format_conditions(self, conditions_met: Dict[str, bool]) -> str:
        """条件達成状況をフォーマット"""
        condition_texts = []

        if conditions_met.get("D1", False):
            condition_texts.append("• D1: RSI過熱 + MACD転換")
        if conditions_met.get("H4", False):
            condition_texts.append("• H4: ボリンジャーバンド上限")
        if conditions_met.get("H1", False):
            condition_texts.append("• H1: 短期過熱確認")
        if conditions_met.get("M5", False):
            condition_texts.append("• M5: 実行タイミング")

        if not condition_texts:
            return "• 条件未達成"

        return "\n".join(condition_texts)

    def get_template_info(self) -> Dict[str, Any]:
        """テンプレート情報を取得"""
        return {
            "pattern_number": self.pattern_number,
            "pattern_name": self.pattern_name,
            "default_color": self.default_color,
            "description": "強力なトレンド転換シグナル用の通知テンプレート",
        }
