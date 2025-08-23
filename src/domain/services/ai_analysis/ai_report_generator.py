"""
AIレポート生成器

AI分析結果からレポートコンテンツを生成する
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from src.domain.entities import EconomicEvent, USDJPYPrediction


class AIReportGenerator:
    """
    AIレポート生成器
    
    AI分析結果からレポートコンテンツを生成する
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 統計情報
        self._generation_count = 0
        self._total_content_length = 0

    async def generate_pre_event_content(
        self,
        event: EconomicEvent,
        prediction: USDJPYPrediction,
        ai_response: str
    ) -> str:
        """
        事前レポートコンテンツの生成
        
        Args:
            event: 経済イベント
            prediction: USD/JPY予測
            ai_response: AI応答
            
        Returns:
            str: 生成されたレポートコンテンツ
        """
        try:
            self._generation_count += 1
            
            content = f"""
# USD/JPY 事前分析レポート

## 📊 経済指標情報
- **イベント**: {event.event_name}
- **国**: {event.country}
- **重要度**: {event.importance.value}
- **発表予定**: {event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
- **予測値**: {event.forecast_value if event.forecast_value else '未発表'}
- **前回値**: {event.previous_value if event.previous_value else 'なし'}
- **単位**: {event.unit if event.unit else 'なし'}

## 🎯 USD/JPY 予測
- **方向性**: {self._get_direction_emoji(prediction.direction)} {prediction.direction.upper()}
- **強度**: {prediction.strength:.2f}/1.00
- **時間枠**: {prediction.timeframe}
- **信頼度**: {prediction.confidence_score:.2f}/1.00

## 📈 分析根拠
{self._format_reasons(prediction.reasons)}

## 🔧 テクニカル要因
{self._format_factors(prediction.technical_factors)}

## 💼 ファンダメンタル要因
{self._format_factors(prediction.fundamental_factors)}

## ⚠️ リスク要因
{self._format_factors(prediction.risk_factors)}

## 📋 投資戦略
{self._generate_investment_strategy(prediction)}

## 📝 AI分析サマリー
{self._extract_summary_from_ai_response(ai_response)}

---
*生成日時: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
*信頼度スコア: {prediction.confidence_score:.2f}/1.00*
            """.strip()
            
            self._total_content_length += len(content)
            
            return content

        except Exception as e:
            self.logger.error(f"事前レポート生成エラー: {e}")
            return self._get_fallback_content(event, "事前分析")

    async def generate_post_event_content(
        self,
        event: EconomicEvent,
        prediction: USDJPYPrediction,
        ai_response: str
    ) -> str:
        """
        事後レポートコンテンツの生成
        
        Args:
            event: 経済イベント
            prediction: USD/JPY予測
            ai_response: AI応答
            
        Returns:
            str: 生成されたレポートコンテンツ
        """
        try:
            self._generation_count += 1
            
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
            
            content = f"""
# USD/JPY 事後分析レポート

## 📊 経済指標結果
- **イベント**: {event.event_name}
- **国**: {event.country}
- **重要度**: {event.importance.value}
- **発表日時**: {event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
{surprise_info}
- **前回値**: {event.previous_value if event.previous_value else 'なし'}
- **単位**: {event.unit if event.unit else 'なし'}

## 🎯 USD/JPY 影響分析
- **方向性**: {self._get_direction_emoji(prediction.direction)} {prediction.direction.upper()}
- **強度**: {prediction.strength:.2f}/1.00
- **時間枠**: {prediction.timeframe}
- **信頼度**: {prediction.confidence_score:.2f}/1.00

## 📈 市場影響の根拠
{self._format_reasons(prediction.reasons)}

## 🔧 テクニカル要因
{self._format_factors(prediction.technical_factors)}

## 💼 ファンダメンタル要因
{self._format_factors(prediction.fundamental_factors)}

## ⚠️ リスク要因
{self._format_factors(prediction.risk_factors)}

## 📋 今後の投資戦略
{self._generate_post_event_strategy(prediction, event)}

## 📝 AI分析サマリー
{self._extract_summary_from_ai_response(ai_response)}

---
*生成日時: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
*信頼度スコア: {prediction.confidence_score:.2f}/1.00*
            """.strip()
            
            self._total_content_length += len(content)
            
            return content

        except Exception as e:
            self.logger.error(f"事後レポート生成エラー: {e}")
            return self._get_fallback_content(event, "事後分析")

    async def generate_forecast_change_content(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent,
        prediction: USDJPYPrediction,
        ai_response: str
    ) -> str:
        """
        予測値変更レポートコンテンツの生成
        
        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント
            prediction: USD/JPY予測
            ai_response: AI応答
            
        Returns:
            str: 生成されたレポートコンテンツ
        """
        try:
            self._generation_count += 1
            
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
            
            content = f"""
# USD/JPY 予測値変更分析レポート

## 📊 予測値変更情報
- **イベント**: {new_event.event_name}
- **国**: {new_event.country}
- **重要度**: {new_event.importance.value}
- **発表予定**: {new_event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}
{change_info}
- **前回値**: {new_event.previous_value if new_event.previous_value else 'なし'}
- **単位**: {new_event.unit if new_event.unit else 'なし'}

## 🎯 USD/JPY 影響分析
- **方向性**: {self._get_direction_emoji(prediction.direction)} {prediction.direction.upper()}
- **強度**: {prediction.strength:.2f}/1.00
- **時間枠**: {prediction.timeframe}
- **信頼度**: {prediction.confidence_score:.2f}/1.00

## 📈 変更影響の根拠
{self._format_reasons(prediction.reasons)}

## 🔧 テクニカル要因
{self._format_factors(prediction.technical_factors)}

## 💼 ファンダメンタル要因
{self._format_factors(prediction.fundamental_factors)}

## ⚠️ リスク要因
{self._format_factors(prediction.risk_factors)}

## 📋 投資戦略の調整
{self._generate_forecast_change_strategy(prediction, old_event, new_event)}

## 📝 AI分析サマリー
{self._extract_summary_from_ai_response(ai_response)}

---
*生成日時: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
*信頼度スコア: {prediction.confidence_score:.2f}/1.00*
            """.strip()
            
            self._total_content_length += len(content)
            
            return content

        except Exception as e:
            self.logger.error(f"予測値変更レポート生成エラー: {e}")
            return self._get_fallback_content(new_event, "予測値変更分析")

    def _get_direction_emoji(self, direction: str) -> str:
        """方向性の絵文字を取得"""
        direction_emojis = {
            "bullish": "📈",
            "bearish": "📉",
            "neutral": "➡️"
        }
        return direction_emojis.get(direction, "❓")

    def _format_reasons(self, reasons: List[str]) -> str:
        """理由のフォーマット"""
        if not reasons:
            return "- 分析データが不足しています"
        
        formatted_reasons = []
        for i, reason in enumerate(reasons, 1):
            formatted_reasons.append(f"{i}. {reason}")
        
        return "\n".join(formatted_reasons)

    def _format_factors(self, factors: List[str]) -> str:
        """要因のフォーマット"""
        if not factors:
            return "- 該当する要因はありません"
        
        formatted_factors = []
        for i, factor in enumerate(factors, 1):
            formatted_factors.append(f"{i}. {factor}")
        
        return "\n".join(formatted_factors)

    def _generate_investment_strategy(self, prediction: USDJPYPrediction) -> str:
        """投資戦略の生成"""
        if prediction.direction == "bullish":
            if prediction.strength >= 0.7:
                return "- **強力な買いポジション**を推奨\n- ストップロス: 現在価格の-1%程度\n- 利益確定: 現在価格の+2-3%程度"
            elif prediction.strength >= 0.4:
                return "- **中程度の買いポジション**を推奨\n- ストップロス: 現在価格の-0.5%程度\n- 利益確定: 現在価格の+1-2%程度"
            else:
                return "- **軽微な買いポジション**を推奨\n- ストップロス: 現在価格の-0.3%程度\n- 利益確定: 現在価格の+0.5-1%程度"
        
        elif prediction.direction == "bearish":
            if prediction.strength >= 0.7:
                return "- **強力な売りポジション**を推奨\n- ストップロス: 現在価格の+1%程度\n- 利益確定: 現在価格の-2-3%程度"
            elif prediction.strength >= 0.4:
                return "- **中程度の売りポジション**を推奨\n- ストップロス: 現在価格の+0.5%程度\n- 利益確定: 現在価格の-1-2%程度"
            else:
                return "- **軽微な売りポジション**を推奨\n- ストップロス: 現在価格の+0.3%程度\n- 利益確定: 現在価格の-0.5-1%程度"
        
        else:
            return "- **ポジション調整**を推奨\n- 既存ポジションの見直し\n- 新規ポジションは控えめに"

    def _generate_post_event_strategy(
        self, prediction: USDJPYPrediction, event: EconomicEvent
    ) -> str:
        """事後投資戦略の生成"""
        base_strategy = self._generate_investment_strategy(prediction)
        
        # サプライズの考慮
        if event.actual_value and event.forecast_value:
            surprise = event.actual_value - event.forecast_value
            if abs(surprise) > 0.1:  # 10%以上のサプライズ
                base_strategy += "\n\n⚠️ **サプライズが大きいため、市場の反応を慎重に監視してください**"
        
        return base_strategy

    def _generate_forecast_change_strategy(
        self,
        prediction: USDJPYPrediction,
        old_event: EconomicEvent,
        new_event: EconomicEvent
    ) -> str:
        """予測値変更時の投資戦略の生成"""
        base_strategy = self._generate_investment_strategy(prediction)
        
        # 予測値変更の影響を考慮
        if old_event.forecast_value and new_event.forecast_value:
            change = new_event.forecast_value - old_event.forecast_value
            if abs(change) > 0.05:  # 5%以上の変更
                base_strategy += "\n\n📊 **予測値の大幅な変更により、市場予想の調整が予想されます**"
        
        return base_strategy

    def _extract_summary_from_ai_response(self, ai_response: str) -> str:
        """AI応答からサマリーを抽出"""
        try:
            # サマリーセクションの検索
            summary_patterns = [
                r'サマリー[：:]\s*(.+)',
                r'summary[：:]\s*(.+)',
                r'要約[：:]\s*(.+)'
            ]
            
            for pattern in summary_patterns:
                match = re.search(pattern, ai_response, re.MULTILINE | re.DOTALL)
                if match:
                    return match.group(1).strip()
            
            # デフォルトサマリー
            return "AI分析により、上記の予測が生成されました。投資判断の際は、リスク管理を十分に行ってください。"
            
        except Exception as e:
            self.logger.error(f"サマリー抽出エラー: {e}")
            return "AI分析により予測が生成されました。投資判断の際は、リスク管理を十分に行ってください。"

    def _get_fallback_content(self, event: EconomicEvent, report_type: str) -> str:
        """フォールバックコンテンツ"""
        return f"""
# USD/JPY {report_type}レポート

## 📊 経済指標情報
- **イベント**: {event.event_name}
- **国**: {event.country}
- **重要度**: {event.importance.value}
- **発表予定**: {event.date_utc.strftime('%Y-%m-%d %H:%M UTC')}

## ⚠️ エラーが発生しました
申し訳ございませんが、AI分析中にエラーが発生しました。
手動での分析をお勧めします。

---
*生成日時: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*
*エラー: レポート生成に失敗しました*
        """.strip()

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        avg_content_length = (
            self._total_content_length / max(1, self._generation_count)
            if self._generation_count > 0 else 0
        )
        
        return {
            "generator": "AIReportGenerator",
            "generation_count": self._generation_count,
            "total_content_length": self._total_content_length,
            "avg_content_length": avg_content_length
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な動作確認
            if self._generation_count < 0:
                self.logger.error("生成回数が負の値です")
                return False
            
            if self._total_content_length < 0:
                self.logger.error("総コンテンツ長が負の値です")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
