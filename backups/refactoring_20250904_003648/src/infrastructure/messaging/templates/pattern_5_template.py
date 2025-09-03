"""
パターン5: RSI50ライン攻防通知テンプレート

RSI50ライン攻防のDiscord通知テンプレート
"""

from datetime import datetime
from typing import Any, Dict


class Pattern5Template:
    """パターン5: RSI50ライン攻防通知テンプレート"""

    def __init__(self):
        self.pattern_name = "RSI50ライン攻防"
        self.default_color = "0xFFA500"  # オレンジ色
        self.pattern_number = 5

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
        current_time = datetime.now().isoformat()

        # 各時間軸の分析結果を取得
        d1_analysis = detection_result.get("d1_analysis", {})
        h4_analysis = detection_result.get("h4_analysis", {})
        h1_analysis = detection_result.get("h1_analysis", {})
        m5_analysis = detection_result.get("m5_analysis", {})

        # 現在価格とRSI値を取得
        current_price = detection_result.get("current_price", 0.0)
        rsi_data = detection_result.get("rsi_data", {})
        macd_data = detection_result.get("macd_data", {})
        bb_data = detection_result.get("bb_data", {})

        embed = {
            "title": detection_result.get("notification_title", "🔄 RSI50ライン攻防！"),
            "description": (
                f"**{currency_pair}** でRSI50ライン攻防を検出しました！\n" f"トレンド継続/転換の分岐点です。"
            ),
            "color": int(
                detection_result.get("notification_color", self.default_color), 16
            ),
            "timestamp": current_time,
            "fields": [
                {
                    "name": "🎯 戦略",
                    "value": detection_result.get("strategy", "様子見推奨"),
                    "inline": True,
                },
                {
                    "name": "⏳ エントリー条件",
                    "value": detection_result.get("entry_condition", "方向性確定後"),
                    "inline": True,
                },
                {
                    "name": "📊 信頼度",
                    "value": f"{detection_result.get('confidence_score', 0.0):.1%}",
                    "inline": True,
                },
                {
                    "name": "📈 D1分析",
                    "value": (
                        f"RSI: {d1_analysis.get('rsi_value', 0):.1f}\n"
                        f"MACD: {d1_analysis.get('macd_value', 0):.3f}\n"
                        f"状況: トレンド継続/転換の分岐"
                    ),
                    "inline": False,
                },
                {
                    "name": "📈 H4分析",
                    "value": (
                        f"RSI: {h4_analysis.get('rsi_value', 0):.1f}\n"
                        f"価格: {h4_analysis.get('current_price', 0):.3f}\n"
                        f"状況: 短期方向性不明"
                    ),
                    "inline": False,
                },
                {
                    "name": "📈 H1分析",
                    "value": (
                        f"RSI: {h1_analysis.get('rsi_value', 0):.1f}\n"
                        f"変動性: {h1_analysis.get('volatility', 0):.4f}\n"
                        f"状況: 変動性増加"
                    ),
                    "inline": False,
                },
                {
                    "name": "📈 M5分析",
                    "value": (
                        f"RSI: {m5_analysis.get('rsi_value', 0):.1f}\n"
                        f"範囲: {m5_analysis.get('rsi_range', 'N/A')}\n"
                        f"状況: 50ライン攻防"
                    ),
                    "inline": False,
                },
            ],
            "footer": {
                "text": f"パターン{self.pattern_number}: {self.pattern_name} | {currency_pair}"
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
            シンプルテキスト形式の通知
        """
        confidence_score = detection_result.get("confidence_score", 0.0)
        strategy = detection_result.get("strategy", "様子見推奨")

        message = (
            f"🔄 **RSI50ライン攻防！**\n"
            f"📊 {currency_pair} トレンド分岐点\n\n"
            f"🎯 **戦略**: {strategy}\n"
            f"🎯 **エントリー**: 方向性確定後\n"
            f"📊 **信頼度**: {confidence_score:.1%}\n\n"
            f"📈 **状況**:\n"
            f"• D1: トレンド継続/転換の分岐\n"
            f"• H4: 短期方向性不明\n"
            f"• H1: 変動性増加\n"
            f"• M5: 50ライン攻防\n\n"
            f"⏳ **判断**: 方向性確定まで待機"
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
        d1_analysis = detection_result.get("d1_analysis", {})
        h4_analysis = detection_result.get("h4_analysis", {})
        h1_analysis = detection_result.get("h1_analysis", {})
        m5_analysis = detection_result.get("m5_analysis", {})

        detailed_analysis = {
            "pattern_info": {
                "pattern_number": self.pattern_number,
                "pattern_name": self.pattern_name,
                "currency_pair": currency_pair,
                "detection_time": detection_result.get("detection_time", ""),
                "confidence_score": detection_result.get("confidence_score", 0.0),
            },
            "timeframe_analysis": {
                "D1": {
                    "rsi_value": d1_analysis.get("rsi_value", 0),
                    "macd_value": d1_analysis.get("macd_value", 0),
                    "signal_value": d1_analysis.get("signal_value", 0),
                    "condition": "RSI 45-55 かつ MACD ゼロライン付近",
                    "status": "トレンド継続/転換の分岐",
                },
                "H4": {
                    "rsi_value": h4_analysis.get("rsi_value", 0),
                    "current_price": h4_analysis.get("current_price", 0),
                    "bb_middle": h4_analysis.get("bb_middle", 0),
                    "condition": "RSI 45-55 かつ ボリンジャーバンド ミドル付近",
                    "status": "短期方向性不明",
                },
                "H1": {
                    "rsi_value": h1_analysis.get("rsi_value", 0),
                    "volatility": h1_analysis.get("volatility", 0),
                    "avg_volatility": h1_analysis.get("avg_volatility", 0),
                    "condition": "RSI 45-55 かつ 価格変動増加",
                    "status": "変動性増加",
                },
                "M5": {
                    "rsi_value": m5_analysis.get("rsi_value", 0),
                    "rsi_range": m5_analysis.get("rsi_range", "N/A"),
                    "condition": "RSI 50 ライン 攻防",
                    "status": "50ライン攻防",
                },
            },
            "strategy_recommendation": {
                "action": "様子見推奨",
                "entry_timing": "方向性確定後",
                "risk_level": "中",
                "expected_outcome": "トレンド継続または転換",
            },
            "technical_indicators": {
                "rsi_status": "中立（45-55範囲）",
                "macd_status": "ゼロライン付近",
                "bollinger_status": "ミドルライン付近",
                "volatility_status": "増加中",
            },
        }

        return detailed_analysis

    def create_rsi_battle_alert(
        self, detection_result: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> str:
        """
        RSI50ライン攻防専用アラートを作成

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            RSI50ライン攻防アラート
        """
        m5_analysis = detection_result.get("m5_analysis", {})
        rsi_value = m5_analysis.get("rsi_value", 0)
        rsi_range = m5_analysis.get("rsi_range", "N/A")

        alert = (
            f"🔄 **RSI50ライン攻防アラート**\n"
            f"📊 {currency_pair}\n\n"
            f"🎯 **現在のRSI**: {rsi_value:.1f}\n"
            f"📈 **RSI範囲**: {rsi_range}\n"
            f"⚔️ **攻防状況**: 50ラインで激しい攻防\n\n"
            f"💡 **戦略**:\n"
            f"• 方向性確定まで待機\n"
            f"• ブレイクアウトを監視\n"
            f"• 急激な動きに注意\n\n"
            f"⏰ **次の確認**: 30分後"
        )

        return alert

    def get_template_info(self) -> Dict[str, Any]:
        """テンプレート情報を取得"""
        return {
            "pattern_number": self.pattern_number,
            "pattern_name": self.pattern_name,
            "default_color": self.default_color,
            "description": "RSI50ライン攻防の通知テンプレート",
        }
