"""
品質メトリクス

LLM分析の品質メトリクスを管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QualityMetric:
    """品質メトリクス"""
    name: str
    value: float
    threshold: float
    status: str  # "pass", "warning", "fail"
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QualityMetrics:
    """品質メトリクス管理"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """品質メトリクスを初期化"""
        self._initialized = True
        logger.info("Quality metrics initialized")
    
    async def close(self) -> None:
        """品質メトリクスを閉じる"""
        self._initialized = False
        logger.info("Quality metrics closed")
    
    async def calculate_metrics(self, analysis_result: Any) -> List[QualityMetric]:
        """
        品質メトリクスを計算
        
        Args:
            analysis_result: 分析結果
            
        Returns:
            品質メトリクスのリスト
        """
        try:
            metrics = []
            
            # 信頼度メトリクス
            confidence_score = getattr(analysis_result, 'confidence_score', 0.0)
            metrics.append(QualityMetric(
                name="confidence_score",
                value=confidence_score,
                threshold=0.7,
                status="pass" if confidence_score >= 0.7 else "warning" if confidence_score >= 0.5 else "fail",
                timestamp=datetime.now()
            ))
            
            # 結果の完全性メトリクス
            has_results = bool(getattr(analysis_result, 'results', None))
            metrics.append(QualityMetric(
                name="result_completeness",
                value=1.0 if has_results else 0.0,
                threshold=1.0,
                status="pass" if has_results else "fail",
                timestamp=datetime.now()
            ))
            
            # エラー率メトリクス
            has_error = bool(getattr(analysis_result, 'error_message', None))
            metrics.append(QualityMetric(
                name="error_rate",
                value=0.0 if not has_error else 1.0,
                threshold=0.0,
                status="pass" if not has_error else "fail",
                timestamp=datetime.now()
            ))
            
            return metrics
        
        except Exception as e:
            logger.error(f"Quality metrics calculation failed: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "component": "quality_metrics"
        }
