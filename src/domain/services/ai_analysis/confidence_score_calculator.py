"""
信頼度計算器

AI分析の信頼度スコアを計算する
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from src.domain.entities import EconomicEvent


class ConfidenceScoreCalculator:
    """
    信頼度計算器
    
    AI分析の信頼度スコアを計算する
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 統計情報
        self._calculation_count = 0
        self._total_confidence = 0.0

    async def calculate_confidence(
        self, event: EconomicEvent, prediction_data: Dict[str, Any]
    ) -> float:
        """
        信頼度スコアの計算
        
        Args:
            event: 経済イベント
            prediction_data: 予測データ
            
        Returns:
            float: 信頼度スコア（0.0-1.0）
        """
        try:
            self._calculation_count += 1
            
            # 基本信頼度の計算
            base_confidence = await self._calculate_base_confidence(event)
            
            # データ品質による調整
            data_quality_factor = await self._calculate_data_quality_factor(event)
            
            # 予測データの整合性による調整
            prediction_consistency = await self._calculate_prediction_consistency(
                prediction_data
            )
            
            # 重要度による調整
            importance_factor = await self._calculate_importance_factor(event)
            
            # 時間的要因による調整
            time_factor = await self._calculate_time_factor(event)
            
            # 総合信頼度の計算
            total_confidence = (
                base_confidence *
                data_quality_factor *
                prediction_consistency *
                importance_factor *
                time_factor
            )
            
            # 0.0-1.0の範囲に制限
            total_confidence = max(0.0, min(1.0, total_confidence))
            
            self._total_confidence += total_confidence
            
            return total_confidence

        except Exception as e:
            self.logger.error(f"信頼度計算エラー: {e}")
            return 0.5  # デフォルト値

    async def _calculate_base_confidence(self, event: EconomicEvent) -> float:
        """基本信頼度の計算"""
        base_confidence = 0.7  # 基本値
        
        # イベント名の明確性
        if event.event_name and len(event.event_name) > 5:
            base_confidence += 0.1
        
        # 国の明確性
        if event.country and event.country in [
            "japan", "united states", "euro zone", "united kingdom"
        ]:
            base_confidence += 0.1
        
        # 日時の明確性
        if event.date_utc:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    async def _calculate_data_quality_factor(self, event: EconomicEvent) -> float:
        """データ品質による調整係数"""
        quality_score = 1.0
        
        # 予測値の有無
        if event.forecast_value is not None:
            quality_score += 0.1
        else:
            quality_score -= 0.2
        
        # 前回値の有無
        if event.previous_value is not None:
            quality_score += 0.1
        else:
            quality_score -= 0.1
        
        # 実際値の有無（事後分析の場合）
        if event.actual_value is not None:
            quality_score += 0.2
        else:
            quality_score -= 0.1
        
        # 単位の明確性
        if event.unit:
            quality_score += 0.05
        
        return max(0.1, min(1.5, quality_score))

    async def _calculate_prediction_consistency(
        self, prediction_data: Dict[str, Any]
    ) -> float:
        """予測データの整合性による調整係数"""
        consistency_score = 1.0
        
        # 方向性の明確性
        direction = prediction_data.get("direction", "")
        if direction in ["bullish", "bearish", "neutral"]:
            consistency_score += 0.1
        else:
            consistency_score -= 0.2
        
        # 強度の妥当性
        strength = prediction_data.get("strength", 0.0)
        if isinstance(strength, (int, float)) and 0.0 <= strength <= 1.0:
            consistency_score += 0.1
        else:
            consistency_score -= 0.2
        
        # 理由の有無
        reasons = prediction_data.get("reasons", [])
        if reasons and len(reasons) > 0:
            consistency_score += 0.1
        else:
            consistency_score -= 0.1
        
        # 要因の詳細性
        technical_factors = prediction_data.get("technical_factors", [])
        fundamental_factors = prediction_data.get("fundamental_factors", [])
        
        if technical_factors or fundamental_factors:
            consistency_score += 0.1
        
        return max(0.1, min(1.5, consistency_score))

    async def _calculate_importance_factor(self, event: EconomicEvent) -> float:
        """重要度による調整係数"""
        importance_multipliers = {
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8
        }
        
        return importance_multipliers.get(event.importance.value, 1.0)

    async def _calculate_time_factor(self, event: EconomicEvent) -> float:
        """時間的要因による調整係数"""
        if not event.date_utc:
            return 0.8
        
        current_time = datetime.utcnow()
        time_diff = (event.date_utc - current_time).total_seconds() / 3600
        
        # 発表時刻が近いほど信頼度が高い
        if -2 <= time_diff <= 24:  # 発表2時間前から24時間後
            return 1.2
        elif -24 <= time_diff <= 168:  # 発表1日前から1週間後
            return 1.0
        else:
            return 0.8

    async def calculate_aggregate_confidence(
        self, confidence_scores: List[float]
    ) -> Dict[str, Any]:
        """
        複数信頼度スコアの集計
        
        Args:
            confidence_scores: 信頼度スコアのリスト
            
        Returns:
            Dict[str, Any]: 集計結果
        """
        try:
            if not confidence_scores:
                return {
                    "avg_confidence": 0.0,
                    "min_confidence": 0.0,
                    "max_confidence": 0.0,
                    "confidence_distribution": {}
                }
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            min_confidence = min(confidence_scores)
            max_confidence = max(confidence_scores)
            
            # 信頼度分布の計算
            distribution = {
                "high": len([s for s in confidence_scores if s >= 0.8]),
                "medium": len([s for s in confidence_scores if 0.5 <= s < 0.8]),
                "low": len([s for s in confidence_scores if s < 0.5])
            }
            
            return {
                "avg_confidence": avg_confidence,
                "min_confidence": min_confidence,
                "max_confidence": max_confidence,
                "confidence_distribution": distribution,
                "total_analyses": len(confidence_scores)
            }

        except Exception as e:
            self.logger.error(f"集計信頼度計算エラー: {e}")
            return {
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "confidence_distribution": {},
                "error": str(e)
            }

    async def assess_confidence_reliability(
        self, confidence_score: float, event: EconomicEvent
    ) -> Dict[str, Any]:
        """
        信頼度の信頼性評価
        
        Args:
            confidence_score: 信頼度スコア
            event: 経済イベント
            
        Returns:
            Dict[str, Any]: 信頼性評価結果
        """
        try:
            reliability_assessment = {
                "confidence_level": "unknown",
                "reliability_factors": [],
                "risk_factors": [],
                "recommendations": []
            }
            
            # 信頼度レベルの判定
            if confidence_score >= 0.8:
                reliability_assessment["confidence_level"] = "high"
            elif confidence_score >= 0.6:
                reliability_assessment["confidence_level"] = "medium"
            elif confidence_score >= 0.4:
                reliability_assessment["confidence_level"] = "low"
            else:
                reliability_assessment["confidence_level"] = "very_low"
            
            # 信頼性要因の評価
            if event.forecast_value is not None:
                reliability_assessment["reliability_factors"].append(
                    "予測値が利用可能"
                )
            
            if event.previous_value is not None:
                reliability_assessment["reliability_factors"].append(
                    "前回値が利用可能"
                )
            
            if event.is_high_importance:
                reliability_assessment["reliability_factors"].append(
                    "高重要度イベント"
                )
            
            # リスク要因の評価
            if event.forecast_value is None:
                reliability_assessment["risk_factors"].append(
                    "予測値が不明"
                )
            
            if event.previous_value is None:
                reliability_assessment["risk_factors"].append(
                    "前回値が不明"
                )
            
            if not event.event_name or len(event.event_name) < 3:
                reliability_assessment["risk_factors"].append(
                    "イベント名が不明確"
                )
            
            # 推奨事項の生成
            if confidence_score < 0.6:
                reliability_assessment["recommendations"].append(
                    "追加データの収集を推奨"
                )
            
            if len(reliability_assessment["risk_factors"]) > 2:
                reliability_assessment["recommendations"].append(
                    "手動での検証を推奨"
                )
            
            return reliability_assessment

        except Exception as e:
            self.logger.error(f"信頼性評価エラー: {e}")
            return {
                "confidence_level": "unknown",
                "reliability_factors": [],
                "risk_factors": ["評価エラー"],
                "recommendations": ["手動での検証を推奨"]
            }

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        avg_confidence = (
            self._total_confidence / max(1, self._calculation_count)
            if self._calculation_count > 0 else 0
        )
        
        return {
            "calculator": "ConfidenceScoreCalculator",
            "calculation_count": self._calculation_count,
            "total_confidence": self._total_confidence,
            "avg_confidence": avg_confidence
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な動作確認
            if self._calculation_count < 0:
                self.logger.error("計算回数が負の値です")
                return False
            
            if self._total_confidence < 0:
                self.logger.error("総信頼度が負の値です")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
