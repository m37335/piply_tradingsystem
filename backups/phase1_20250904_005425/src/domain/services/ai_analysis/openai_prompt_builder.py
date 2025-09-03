"""
OpenAIプロンプトビルダー

ChatGPT用のプロンプトを構築する
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.domain.entities import EconomicEvent


class OpenAIPromptBuilder:
    """
    OpenAIプロンプトビルダー
    
    ChatGPT用のプロンプトを構築する
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 統計情報
        self._prompt_count = 0
        self._total_tokens_estimated = 0

    async def build_pre_event_prompt(self, event: EconomicEvent) -> str:
        """
        事前レポート用プロンプト作成
        
        Args:
            event: 経済イベント
            
        Returns:
            str: 構築されたプロンプト
        """
        try:
            self._prompt_count += 1
            
            prompt = f"""
あなたは為替市場の専門アナリストです。以下の経済指標について、USD/JPYへの影響を分析してください。

## 経済指標情報
- **イベント名**: {event.event_name}
- **国**: {event.country}
- **重要度**: {event.importance.value}
- **発表予定日時**: {event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
- **予測値**: {event.forecast_value if event.forecast_value else '未発表'}
- **前回値**: {event.previous_value if event.previous_value else 'なし'}
- **単位**: {event.unit if event.unit else 'なし'}

## 分析要求
以下の形式でJSONレスポンスを返してください：

```json
{{
    "direction": "bullish/bearish/neutral",
    "strength": 0.0-1.0,
    "timeframe": "1-4 hours",
    "confidence_score": 0.0-1.0,
    "reasons": [
        "理由1",
        "理由2"
    ],
    "technical_factors": [
        "テクニカル要因1",
        "テクニカル要因2"
    ],
    "fundamental_factors": [
        "ファンダメンタル要因1",
        "ファンダメンタル要因2"
    ],
    "risk_factors": [
        "リスク要因1",
        "リスク要因2"
    ],
    "summary": "簡潔な分析サマリー"
}}
```

## 分析のポイント
1. **方向性**: この指標がUSD/JPYを押し上げるか(bullish)、押し下げるか(bearish)、中立か(neutral)
2. **強度**: 影響の強さを0.0-1.0で評価
3. **時間枠**: 影響が及ぶ時間範囲
4. **信頼度**: 分析の信頼度を0.0-1.0で評価
5. **理由**: 分析の根拠となる具体的な理由
6. **要因**: テクニカル・ファンダメンタル・リスク要因の詳細

## 注意事項
- 必ずJSON形式で回答してください
- 数値は適切な範囲内で設定してください
- 分析は客観的で根拠のある内容にしてください
- 日本語で回答してください
            """.strip()
            
            self._total_tokens_estimated += len(prompt) // 4  # 概算
            
            return prompt

        except Exception as e:
            self.logger.error(f"事前レポートプロンプト作成エラー: {e}")
            return self._get_fallback_prompt()

    async def build_post_event_prompt(self, event: EconomicEvent) -> str:
        """
        事後レポート用プロンプト作成
        
        Args:
            event: 経済イベント
            
        Returns:
            str: 構築されたプロンプト
        """
        try:
            self._prompt_count += 1
            
            # サプライズの計算
            surprise_info = ""
            if event.actual_value and event.forecast_value:
                surprise = event.actual_value - event.forecast_value
                surprise_pct = (surprise / event.forecast_value) * 100 if event.forecast_value != 0 else 0
                surprise_info = f"""
- **実際値**: {event.actual_value}
- **予測値**: {event.forecast_value}
- **サプライズ**: {surprise:+.2f} ({surprise_pct:+.1f}%)
                """.strip()
            
            prompt = f"""
あなたは為替市場の専門アナリストです。以下の経済指標の発表結果について、USD/JPYへの影響を分析してください。

## 経済指標情報
- **イベント名**: {event.event_name}
- **国**: {event.country}
- **重要度**: {event.importance.value}
- **発表日時**: {event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
{surprise_info}
- **前回値**: {event.previous_value if event.previous_value else 'なし'}
- **単位**: {event.unit if event.unit else 'なし'}

## 分析要求
以下の形式でJSONレスポンスを返してください：

```json
{{
    "direction": "bullish/bearish/neutral",
    "strength": 0.0-1.0,
    "timeframe": "1-4 hours",
    "confidence_score": 0.0-1.0,
    "reasons": [
        "理由1",
        "理由2"
    ],
    "technical_factors": [
        "テクニカル要因1",
        "テクニカル要因2"
    ],
    "fundamental_factors": [
        "ファンダメンタル要因1",
        "ファンダメンタル要因2"
    ],
    "risk_factors": [
        "リスク要因1",
        "リスク要因2"
    ],
    "market_reaction": "予想される市場反応",
    "summary": "簡潔な分析サマリー"
}}
```

## 分析のポイント
1. **サプライズの影響**: 予測値との乖離が市場に与える影響
2. **方向性**: 実際値がUSD/JPYを押し上げるか(bullish)、押し下げるか(bearish)、中立か(neutral)
3. **強度**: 影響の強さを0.0-1.0で評価
4. **市場反応**: 予想される市場の反応パターン
5. **継続性**: 影響の継続期間と強度の変化

## 注意事項
- 必ずJSON形式で回答してください
- 数値は適切な範囲内で設定してください
- 分析は客観的で根拠のある内容にしてください
- 日本語で回答してください
            """.strip()
            
            self._total_tokens_estimated += len(prompt) // 4  # 概算
            
            return prompt

        except Exception as e:
            self.logger.error(f"事後レポートプロンプト作成エラー: {e}")
            return self._get_fallback_prompt()

    async def build_forecast_change_prompt(
        self, old_event: EconomicEvent, new_event: EconomicEvent
    ) -> str:
        """
        予測値変更用プロンプト作成
        
        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント
            
        Returns:
            str: 構築されたプロンプト
        """
        try:
            self._prompt_count += 1
            
            # 変更の計算
            change_info = ""
            if old_event.forecast_value and new_event.forecast_value:
                change = new_event.forecast_value - old_event.forecast_value
                change_pct = (change / old_event.forecast_value) * 100 if old_event.forecast_value != 0 else 0
                change_info = f"""
- **変更前予測値**: {old_event.forecast_value}
- **変更後予測値**: {new_event.forecast_value}
- **変更幅**: {change:+.2f} ({change_pct:+.1f}%)
                """.strip()
            
            prompt = f"""
あなたは為替市場の専門アナリストです。以下の経済指標の予測値変更について、USD/JPYへの影響を分析してください。

## 経済指標情報
- **イベント名**: {new_event.event_name}
- **国**: {new_event.country}
- **重要度**: {new_event.importance.value}
- **発表予定日時**: {new_event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
{change_info}
- **前回値**: {new_event.previous_value if new_event.previous_value else 'なし'}
- **単位**: {new_event.unit if new_event.unit else 'なし'}

## 分析要求
以下の形式でJSONレスポンスを返してください：

```json
{{
    "direction": "bullish/bearish/neutral",
    "strength": 0.0-1.0,
    "timeframe": "1-4 hours",
    "confidence_score": 0.0-1.0,
    "reasons": [
        "理由1",
        "理由2"
    ],
    "technical_factors": [
        "テクニカル要因1",
        "テクニカル要因2"
    ],
    "fundamental_factors": [
        "ファンダメンタル要因1",
        "ファンダメンタル要因2"
    ],
    "risk_factors": [
        "リスク要因1",
        "リスク要因2"
    ],
    "forecast_impact": "予測値変更の影響",
    "summary": "簡潔な分析サマリー"
}}
```

## 分析のポイント
1. **予測値変更の意味**: 変更が示す経済状況の変化
2. **方向性**: 変更がUSD/JPYを押し上げるか(bullish)、押し下げるか(bearish)、中立か(neutral)
3. **強度**: 影響の強さを0.0-1.0で評価
4. **市場予想**: 変更に対する市場の予想調整
5. **リスク**: 予測値変更に伴うリスク要因

## 注意事項
- 必ずJSON形式で回答してください
- 数値は適切な範囲内で設定してください
- 分析は客観的で根拠のある内容にしてください
- 日本語で回答してください
            """.strip()
            
            self._total_tokens_estimated += len(prompt) // 4  # 概算
            
            return prompt

        except Exception as e:
            self.logger.error(f"予測値変更プロンプト作成エラー: {e}")
            return self._get_fallback_prompt()

    async def build_sentiment_analysis_prompt(
        self, events: List[EconomicEvent]
    ) -> str:
        """
        センチメント分析用プロンプト作成
        
        Args:
            events: 経済イベントリスト
            
        Returns:
            str: 構築されたプロンプト
        """
        try:
            self._prompt_count += 1
            
            # イベント情報の整理
            events_info = []
            for event in events:
                event_info = f"""
- **{event.event_name}** ({event.country})
  - 重要度: {event.importance.value}
  - 発表予定: {event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
  - 予測値: {event.forecast_value if event.forecast_value else '未発表'}
                """.strip()
                events_info.append(event_info)
            
            events_text = "\n".join(events_info)
            
            prompt = f"""
あなたは為替市場の専門アナリストです。以下の経済指標群について、USD/JPYへの全体的な市場センチメントを分析してください。

## 分析対象イベント
{events_text}

## 分析要求
以下の形式でJSONレスポンスを返してください：

```json
{{
    "overall_sentiment": "bullish/bearish/neutral",
    "confidence": 0.0-1.0,
    "factors": [
        "センチメント要因1",
        "センチメント要因2"
    ],
    "country_sentiment": {{
        "japan": "bullish/bearish/neutral",
        "united states": "bullish/bearish/neutral",
        "euro zone": "bullish/bearish/neutral"
    }},
    "category_sentiment": {{
        "inflation": "bullish/bearish/neutral",
        "employment": "bullish/bearish/neutral",
        "interest_rate": "bullish/bearish/neutral"
    }},
    "summary": "全体的なセンチメント分析サマリー"
}}
```

## 分析のポイント
1. **全体的センチメント**: 複数イベントを総合した市場ムード
2. **国別センチメント**: 各国の経済指標が示す方向性
3. **カテゴリ別センチメント**: 指標カテゴリ別の方向性
4. **信頼度**: 分析の信頼度を0.0-1.0で評価
5. **要因**: センチメントを形成する主要要因

## 注意事項
- 必ずJSON形式で回答してください
- 数値は適切な範囲内で設定してください
- 分析は客観的で根拠のある内容にしてください
- 日本語で回答してください
            """.strip()
            
            self._total_tokens_estimated += len(prompt) // 4  # 概算
            
            return prompt

        except Exception as e:
            self.logger.error(f"センチメント分析プロンプト作成エラー: {e}")
            return self._get_fallback_prompt()

    def _get_fallback_prompt(self) -> str:
        """フォールバックプロンプト"""
        return """
あなたは為替市場の専門アナリストです。USD/JPYの分析を行ってください。

以下の形式でJSONレスポンスを返してください：

```json
{
    "direction": "neutral",
    "strength": 0.0,
    "timeframe": "1-4 hours",
    "confidence_score": 0.0,
    "reasons": ["分析データが不足しています"],
    "technical_factors": [],
    "fundamental_factors": [],
    "risk_factors": ["データ不足"],
    "summary": "データ不足のため分析できません"
}
```

必ずJSON形式で回答してください。
        """.strip()

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "builder": "OpenAIPromptBuilder",
            "prompt_count": self._prompt_count,
            "total_tokens_estimated": self._total_tokens_estimated,
            "avg_tokens_per_prompt": (
                self._total_tokens_estimated / max(1, self._prompt_count)
            )
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な動作確認
            test_prompt = self._get_fallback_prompt()
            if not test_prompt or len(test_prompt) < 100:
                self.logger.error("フォールバックプロンプトが不適切です")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
