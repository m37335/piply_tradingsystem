"""
データプロバイダーの基底クラス

すべてのデータプロバイダーが実装すべきインターフェースを定義します。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class TimeFrame(Enum):
    """時間軸の種類"""
    M5 = "5m"      # 5分足（メイン対象）
    M15 = "15m"    # 15分足
    H1 = "1h"      # 1時間足
    H4 = "4h"      # 4時間足
    D1 = "1d"      # 日足


@dataclass
class PriceData:
    """価格データの構造"""
    symbol: str
    timeframe: TimeFrame
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str
    quality_score: float = 1.0


@dataclass
class DataCollectionResult:
    """データ収集結果"""
    success: bool
    data: List[PriceData]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseDataProvider(ABC):
    """データプロバイダーの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
        self._is_available = True
    
    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_date: datetime,
        end_date: datetime
    ) -> DataCollectionResult:
        """履歴データを取得"""
        pass
    
    @abstractmethod
    async def get_latest_data(
        self,
        symbol: str,
        timeframe: TimeFrame
    ) -> DataCollectionResult:
        """最新データを取得"""
        pass
    
    @abstractmethod
    async def get_available_symbols(self) -> List[str]:
        """利用可能なシンボル一覧を取得"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """プロバイダーが利用可能かチェック"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass
    
    def _validate_data(self, data: List[PriceData]) -> List[PriceData]:
        """データの妥当性をチェック"""
        validated_data = []
        
        for item in data:
            # 基本的な妥当性チェック
            if (item.open > 0 and item.high > 0 and 
                item.low > 0 and item.close > 0 and 
                item.volume >= 0):
                validated_data.append(item)
        
        return validated_data
    
    def _calculate_quality_score(self, data: PriceData) -> float:
        """データ品質スコアを計算"""
        score = 1.0
        
        # 価格の妥当性チェック
        if not (item.low <= item.open <= item.high and 
                item.low <= item.close <= item.high):
            score -= 0.3
        
        # ボリュームの妥当性チェック
        if item.volume < 0:
            score -= 0.2
        
        # タイムスタンプの妥当性チェック
        now = datetime.now()
        if item.timestamp > now or item.timestamp < now - timedelta(days=365):
            score -= 0.1
        
        return max(0.0, score)
