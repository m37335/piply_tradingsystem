"""
OpenAIプロンプトマネージャー
AI分析用のプロンプトを管理・生成
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


class OpenAIPromptManager:
    """OpenAIプロンプトマネージャー"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_system_prompt(self, analysis_type: str = "general") -> str:
        """
        システムプロンプトを取得

        Args:
            analysis_type: 分析タイプ

        Returns:
            str: システムプロンプト
        """
        base_prompt = (
            "あなたは経済分析の専門家です。"
            "経済指標の分析とUSD/JPY為替レートへの影響を専門的に分析します。"
            "常に客観的で根拠のある分析を提供してください。"
            "レスポンスは必ず有効なJSON形式で返してください。"
            "JSONの文字列内では改行は使用せず、適切にエスケープしてください。"
            '文字列内に引用符がある場合は必ずエスケープ（\\"）してください。'
        )

        if analysis_type == "pre_event":
            return (
                f"{base_prompt}\n"
                "イベント前の分析では、予測値と前回値の比較、"
                "市場の期待値、USD/JPYへの潜在的な影響を分析してください。"
            )
        elif analysis_type == "post_event":
            return (
                f"{base_prompt}\n"
                "イベント後の分析では、実際値と予測値の乖離、"
                "サプライズ要因、USD/JPYへの実際の影響を分析してください。"
            )
        elif analysis_type == "forecast_change":
            return (
                f"{base_prompt}\n"
                "予測値変更の分析では、変更の理由、"
                "市場への影響、USD/JPYへの新しい影響を分析してください。"
            )
        else:
            return base_prompt

    def get_usd_jpy_system_prompt(self) -> str:
        """
        USD/JPY予測用のシステムプロンプトを取得

        Returns:
            str: システムプロンプト
        """
        return (
            "あなたは為替分析の専門家です。"
            "経済指標の発表がUSD/JPY為替レートに与える影響を分析し、"
            "具体的な予測を提供します。"
            "以下の形式でJSONレスポンスを返してください：\n"
            "{\n"
            '  "direction": "buy" or "sell",\n'
            '  "strength": "weak", "moderate", or "strong",\n'
            '  "target_price": "150.50",\n'
            '  "confidence_score": 0.85,\n'
            '  "fundamental_reasons": [\n'
            '    "ファンダメンタル要因1（具体的な説明を含む）",\n'
            '    "ファンダメンタル要因2（具体的な説明を含む）"\n'
            "  ],\n"
            '  "technical_reasons": [\n'
            '    "テクニカル要因1（具体的な説明を含む）",\n'
            '    "テクニカル要因2（具体的な説明を含む）"\n'
            "  ],\n"
            '  "risk_factors": [\n'
            '    "リスク要因1（具体的な説明を含む）",\n'
            '    "リスク要因2（具体的な説明を含む）"\n'
            "  ],\n"
            '  "timeframe": "1-4 hours",\n'
            '  "analysis_summary": "予測の根拠となる総合的な分析を詳しく説明してください。"\n'
            "}\n\n"
            "注意: JSONの文字列内では改行は使用せず、一行で記述してください。文字列内に引用符がある場合は必ずエスケープしてください。"
        )

    def get_report_system_prompt(self) -> str:
        """
        レポート生成用のシステムプロンプトを取得

        Returns:
            str: システムプロンプト
        """
        return (
            "あなたは経済分析レポートの専門家です。"
            "経済指標の分析結果とUSD/JPY予測を含む"
            "包括的なレポートを生成します。"
            "以下の形式でJSONレスポンスを返してください：\n"
            "{\n"
            '  "summary": "レポートの要約を、主要なポイントと結論を含めて詳しく説明してください。",\n'
            '  "analysis": "詳細な分析を、経済的背景、市場の反応、為替レートへの影響を含めて詳しく説明してください。",\n'
            '  "usd_jpy_impact": "USD/JPY為替レートへの具体的な影響を、方向性、強度、タイミングを含めて詳しく説明してください。",\n'
            '  "key_points": [\n'
            '    "重要なポイント1（具体的な内容と理由を含む）",\n'
            '    "重要なポイント2（具体的な内容と理由を含む）",\n'
            '    "重要なポイント3（具体的な内容と理由を含む）"\n'
            "  ],\n"
            '  "recommendations": [\n'
            '    "投資家向け推奨事項1（具体的な行動指針を含む）",\n'
            '    "投資家向け推奨事項2（具体的な行動指針を含む）",\n'
            '    "投資家向け推奨事項3（具体的な行動指針を含む）"\n'
            "  ],\n"
            '  "risk_assessment": "リスク評価を、具体的なリスク要因とその影響度を含めて詳しく説明してください。",\n'
            '  "market_outlook": "今後の市場見通しを、短期的・中長期的な視点を含めて詳しく説明してください。"\n'
            "}\n\n"
            "注意: JSONの文字列内では改行は使用せず、一行で記述してください。文字列内に引用符がある場合は必ずエスケープしてください。"
        )

    def create_economic_analysis_prompt(
        self, event_data: Dict[str, Any], analysis_type: str = "pre_event"
    ) -> str:
        """
        経済分析用のプロンプトを作成

        Args:
            event_data: イベントデータ
            analysis_type: 分析タイプ

        Returns:
            str: プロンプト
        """
        event_name = event_data.get("event_name", "Unknown Event")
        country = event_data.get("country", "Unknown")
        importance = event_data.get("importance", "medium")
        date_utc = event_data.get("date_utc", "")

        if isinstance(date_utc, datetime):
            date_str = date_utc.strftime("%Y-%m-%d %H:%M UTC")
        else:
            date_str = str(date_utc)

        base_info = f"""
経済イベント分析を依頼します。

イベント情報:
- イベント名: {event_name}
- 国: {country}
- 重要度: {importance}
- 日時: {date_str}
"""

        # 分析タイプに応じた情報を追加
        if analysis_type == "pre_event":
            forecast = event_data.get("forecast_value")
            previous = event_data.get("previous_value")

            prompt = f"{base_info}\n"
            if forecast is not None:
                prompt += f"- 予測値: {forecast}\n"
            if previous is not None:
                prompt += f"- 前回値: {previous}\n"

            prompt += """
この経済指標の発表がUSD/JPY為替レートに与える影響を分析してください。
以下の項目を含めて有効なJSON形式で回答してください。
重要：文字列内では改行は使用せず、引用符は必ずエスケープしてください：

{
  "event_analysis": {
    "significance": "指標の重要性について、市場への影響度と理由を詳しく説明してください。",
    "market_expectations": "市場の期待値と、その期待値が形成された背景を説明してください。",
    "potential_impact": "USD/JPY為替レートへの潜在的な影響を、具体的な方向性と強度を含めて説明してください。"
  },
  "usd_jpy_analysis": {
    "direction": "buy/sell",
    "strength": "weak/moderate/strong",
    "reasoning": "分析理由を、ファンダメンタル要因とテクニカル要因を含めて詳しく説明してください。",
    "confidence": 0.85
  },
  "key_factors": [
    "主要な影響要因1（具体的な説明を含む）",
    "主要な影響要因2（具体的な説明を含む）",
    "主要な影響要因3（具体的な説明を含む）"
  ],
  "risk_considerations": [
    "考慮すべきリスク要因1（具体的な説明を含む）",
    "考慮すべきリスク要因2（具体的な説明を含む）"
  ]
}

注意: JSONの文字列内では改行は使用せず、一行で記述してください。文字列内に引用符がある場合は必ずエスケープしてください。
"""

        elif analysis_type == "post_event":
            actual = event_data.get("actual_value")
            forecast = event_data.get("forecast_value")
            previous = event_data.get("previous_value")

            prompt = f"{base_info}\n"
            if actual is not None:
                prompt += f"- 実際値: {actual}\n"
            if forecast is not None:
                prompt += f"- 予測値: {forecast}\n"
            if previous is not None:
                prompt += f"- 前回値: {previous}\n"

            prompt += """
この経済指標の発表結果を分析し、USD/JPY為替レートへの実際の影響を評価してください。
以下の項目を含めてJSON形式で回答してください：

{
  "result_analysis": {
    "surprise_factor": "サプライズ要因について、予想との乖離度と市場への衝撃を詳しく説明してください。",
    "deviation_from_forecast": "予測値からの乖離について、具体的な数値とその意味を説明してください。",
    "market_reaction": "市場の反応について、為替レートの動きとその背景を詳しく説明してください。"
  },
  "usd_jpy_impact": {
    "immediate_effect": "即座の影響について、発表直後の為替レートの動きとその理由を説明してください。",
    "sustained_effect": "持続的な影響について、中長期的な為替レートへの影響を説明してください。",
    "reasoning": "影響の理由について、ファンダメンタル要因とテクニカル要因を含めて詳しく説明してください。"
  },
  "lessons_learned": [
    "今回の発表から得られる教訓1（具体的な内容を含む）",
    "今回の発表から得られる教訓2（具体的な内容を含む）"
  ],
  "future_implications": "今後の示唆について、今後の経済指標発表や為替レートへの影響を詳しく説明してください。"
}

注意: JSONの文字列内では改行は使用せず、一行で記述してください。文字列内に引用符がある場合は必ずエスケープしてください。
"""

        else:
            prompt = f"{base_info}\n"
            prompt += """
この経済指標の一般的な分析をしてください。
"""

        return prompt

    def create_usd_jpy_prediction_prompt(
        self,
        event_data: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        USD/JPY予測用のプロンプトを作成

        Args:
            event_data: イベントデータ
            market_context: 市場コンテキスト

        Returns:
            str: プロンプト
        """
        event_name = event_data.get("event_name", "Unknown Event")
        country = event_data.get("country", "Unknown")
        importance = event_data.get("importance", "medium")

        prompt = f"""
USD/JPY為替レート予測を依頼します。

経済指標情報:
- イベント名: {event_name}
- 国: {country}
- 重要度: {importance}
"""

        # イベントデータの詳細を追加
        for key, value in event_data.items():
            if key in ["forecast_value", "actual_value", "previous_value"]:
                prompt += f"- {key}: {value}\n"

        # 市場コンテキストを追加
        if market_context:
            prompt += "\n市場コンテキスト:\n"
            for key, value in market_context.items():
                prompt += f"- {key}: {value}\n"

        prompt += """
この経済指標の発表に基づいて、USD/JPY為替レートの方向性と強度を予測してください。
現在のUSD/JPYレートを考慮し、具体的な目標価格と信頼度スコアを含めて回答してください。

予測の根拠として、ファンダメンタル要因、テクニカル要因、リスク要因を明確にしてください。
"""

        return prompt

    def create_report_generation_prompt(
        self,
        event_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]] = None,
        report_type: str = "pre_event",
    ) -> str:
        """
        レポート生成用のプロンプトを作成

        Args:
            event_data: イベントデータ
            prediction_data: 予測データ
            report_type: レポートタイプ

        Returns:
            str: プロンプト
        """
        event_name = event_data.get("event_name", "Unknown Event")
        country = event_data.get("country", "Unknown")

        prompt = f"""
経済分析レポートの生成を依頼します。

レポート情報:
- イベント名: {event_name}
- 国: {country}
- レポートタイプ: {report_type}
"""

        # イベントデータの詳細を追加
        for key, value in event_data.items():
            if key in [
                "forecast_value",
                "actual_value",
                "previous_value",
                "importance",
            ]:
                prompt += f"- {key}: {value}\n"

        # 予測データを追加
        if prediction_data:
            prompt += "\n予測データ:\n"
            for key, value in prediction_data.items():
                prompt += f"- {key}: {value}\n"

        prompt += f"""
{report_type}レポートを生成してください。
以下の要素を含む包括的なレポートを作成してください：

1. イベントの重要性と市場への影響
2. USD/JPY為替レートへの具体的な影響分析
3. 投資家向けの推奨事項
4. リスク要因と注意点
5. 今後の市場動向への示唆

レポートは専門的でありながら、投資家が理解しやすい内容にしてください。
"""

        return prompt

    def create_market_context_prompt(
        self,
        current_usd_jpy: float,
        market_sentiment: str = "neutral",
        recent_events: Optional[List[str]] = None,
    ) -> str:
        """
        市場コンテキスト用のプロンプトを作成

        Args:
            current_usd_jpy: 現在のUSD/JPYレート
            market_sentiment: 市場センチメント
            recent_events: 最近のイベント

        Returns:
            str: プロンプト
        """
        prompt = f"""
現在の市場状況を分析してください。

市場情報:
- 現在のUSD/JPY: {current_usd_jpy}
- 市場センチメント: {market_sentiment}
"""

        if recent_events:
            prompt += "\n最近の重要なイベント:\n"
            for event in recent_events:
                prompt += f"- {event}\n"

        prompt += """
この市場環境における経済指標の影響を分析してください。
"""

        return prompt
