"""
品質管理コントローラー

LLM分析の品質を管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """品質レポート"""
    analysis_id: str
    quality_score: float
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QualityController:
    """品質管理コントローラー"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """品質管理コントローラーを初期化"""
        self._initialized = True
        logger.info("Quality controller initialized")
    
    async def close(self) -> None:
        """品質管理コントローラーを閉じる"""
        self._initialized = False
        logger.info("Quality controller closed")
    
    async def evaluate_quality(self, analysis_result: Any) -> QualityReport:
        """
        分析結果の品質を評価
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            品質レポート
        """
        try:
            logger.info("Evaluating analysis quality")
            
            issues = []
            recommendations = []
            quality_score = 1.0
            
            # 信頼度スコアのチェック
            if hasattr(analysis_result, 'confidence_score'):
                if analysis_result.confidence_score < 0.5:
                    issues.append("Low confidence score")
                    recommendations.append("Consider using more data or different analysis approach")
                    quality_score -= 0.3
            
            # 結果の完全性チェック
            if hasattr(analysis_result, 'results'):
                if not analysis_result.results:
                    issues.append("Empty analysis results")
                    recommendations.append("Check data quality and analysis parameters")
                    quality_score -= 0.4
            
            # エラーのチェック
            if hasattr(analysis_result, 'error_message') and analysis_result.error_message:
                issues.append(f"Analysis error: {analysis_result.error_message}")
                recommendations.append("Review error logs and retry analysis")
                quality_score -= 0.5
            
            # 最終的な品質スコア
            quality_score = max(0.0, quality_score)
            
            report = QualityReport(
                analysis_id=getattr(analysis_result, 'symbol', 'unknown'),
                quality_score=quality_score,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now(),
                metadata={
                    "evaluated_at": datetime.now(),
                    "analysis_type": getattr(analysis_result, 'analysis_type', 'unknown')
                }
            )
            
            logger.info(f"Quality evaluation completed: {quality_score}")
            return report
        
        except Exception as e:
            logger.error(f"Quality evaluation failed: {e}")
            return QualityReport(
                analysis_id="unknown",
                quality_score=0.0,
                issues=[f"Quality evaluation error: {str(e)}"],
                recommendations=["Review system logs"],
                timestamp=datetime.now()
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "component": "quality_controller"
        }
