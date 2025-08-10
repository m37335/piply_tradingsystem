"""
パターン3通知テンプレート

ダイバージェンス警戒用のDiscord通知テンプレート
"""

from datetime import datetime
from typing import Any, Dict

import pandas as pd


class Pattern3Template:
    """パターン3: ダイバージェンス警戒通知テンプレート"""

    def __init__(self):
        self.pattern_name = "ダイバージェンス警戒"
        self.default_color = "0xFFFF00"  # 黄色
        self.pattern_number = 3

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
            "title": detection_result.get("notification_title", "⚠️ ダイバージェンス警戒！"),
            "description": (
                f"**{currency_pair}** でダイバージェンスを検出しました！\n" f"価格とRSIの乖離により急落の可能性があります。"
            ),
            "color": int(
                detection_result.get("notification_color", self.default_color), 16
            ),
            "timestamp": current_time,
            "fields": [
                {
                    "name": "🚨 警戒事項",
                    "value": (
                        f"**戦略**: {detection_result.get('strategy', '利確推奨')}\n"
                        f"**リスク**: {detection_result.get('risk', '急落可能性')}\n"
                        f"**対応**: ポジション調整を推奨"
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
            f"⚠️ **{detection_result.get('notification_title', 'ダイバージェンス警戒！')}**\n\n"
            f"**通貨ペア**: {currency_pair}\n"
            f"**戦略**: {detection_result.get('strategy', '利確推奨')}\n"
            f"**リスク**: {detection_result.get('risk', '急落可能性')}\n"
            f"**信頼度スコア**: {confidence_score:.2f}\n"
            f"**検出時刻**: {current_time}\n\n"
            f"価格とRSIの乖離により急落の可能性があります。ポジション調整を推奨します。"
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

            # 価格とRSIの動向を分析
            price_trend = (
                "上昇"
                if len(price_data) >= 2 and current_price > price_data["Close"].iloc[-2]
                else "下降"
            )
            rsi_trend = (
                "上昇"
                if (
                    rsi_data
                    and "series" in rsi_data
                    and len(rsi_data["series"]) >= 2
                    and rsi_data["series"].iloc[-1] > rsi_data["series"].iloc[-2]
                )
                else "下降"
            )

            timeframe_details[timeframe] = {
                "current_price": current_price,
                "rsi_value": rsi_data.get("current_value", 0.0) if rsi_data else 0.0,
                "price_trend": price_trend,
                "rsi_trend": rsi_trend,
                "divergence_detected": price_trend != rsi_trend,
                "condition_met": conditions_met.get(timeframe, False),
            }

        return {
            "currency_pair": currency_pair,
            "pattern_name": self.pattern_name,
            "pattern_number": self.pattern_number,
            "detection_time": datetime.now().isoformat(),
            "timeframe_details": timeframe_details,
            "overall_confidence": detection_result.get("confidence_score", 0.0),
            "strategy": detection_result.get("strategy", "利確推奨"),
            "risk": detection_result.get("risk", "急落可能性"),
        }

    def create_divergence_alert(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        ダイバージェンス警戒アラートを作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            ダイバージェンス警戒アラートの辞書
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        confidence_score = detection_result.get("confidence_score", 0.0)

        alert = {
            "title": "🚨 ダイバージェンス警戒アラート",
            "message": (
                f"**{currency_pair}** でダイバージェンスを検出しました！\n\n"
                f"**警戒レベル**: {'高' if confidence_score > 0.7 else '中' if confidence_score > 0.5 else '低'}\n"
                f"**信頼度スコア**: {confidence_score:.2f}\n"
                f"**検出時刻**: {current_time}\n\n"
                f"**推奨アクション**:\n"
                f"• 既存ポジションの利確を検討\n"
                f"• 新規エントリーは控えめに\n"
                f"• ストップロスを厳格に設定"
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
            "template_type": "divergence_warning",
            "description": "ダイバージェンス警戒の通知テンプレート",
        }
