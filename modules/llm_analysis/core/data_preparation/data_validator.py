"""
データ検証器

LLM分析用のデータを検証します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    quality_score: float
    issues: List[str]
    warnings: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DataValidator:
    """データ検証器"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """データ検証器を初期化"""
        self._initialized = True
        logger.info("Data validator initialized")
    
    async def close(self) -> None:
        """データ検証器を閉じる"""
        self._initialized = False
        logger.info("Data validator closed")
    
    async def validate(self, data: Any) -> ValidationResult:
        """
        データを検証
        
        Args:
            data: 検証するデータ
            
        Returns:
            検証結果
        """
        try:
            logger.info("Validating data")
            
            issues = []
            warnings = []
            quality_score = 1.0
            
            # データの存在チェック
            if not hasattr(data, 'price_data') or not data.price_data:
                issues.append("No price data available")
                quality_score -= 0.3
            
            # データの完全性チェック
            if hasattr(data, 'price_data') and data.price_data:
                if len(data.price_data) < 10:
                    warnings.append("Limited price data available")
                    quality_score -= 0.1
            
            # データの一貫性チェック
            if hasattr(data, 'volume_data') and data.volume_data:
                if len(data.price_data) != len(data.volume_data):
                    issues.append("Price and volume data length mismatch")
                    quality_score -= 0.2
            
            # 最終的な品質スコア
            quality_score = max(0.0, quality_score)
            is_valid = len(issues) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                issues=issues,
                warnings=warnings,
                metadata={
                    "validated_at": datetime.now(),
                    "data_points": len(data.price_data) if hasattr(data, 'price_data') and data.price_data else 0
                }
            )
            
            logger.info(f"Data validation completed: {is_valid}")
            return result
        
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                quality_score=0.0,
                issues=[f"Validation error: {str(e)}"],
                warnings=[]
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        return {
            "status": "healthy" if self._initialized else "unhealthy",
            "component": "data_validator"
        }
