"""
Analysis Cache Repository Interface
分析キャッシュリポジトリインターフェース

設計書参照:
- api_optimization_design_2025.md

分析結果キャッシュのリポジトリインターフェース
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.analysis_cache import AnalysisCache


class AnalysisCacheRepository(ABC):
    """
    分析キャッシュリポジトリインターフェース

    責任:
    - 分析結果キャッシュの永続化
    - キャッシュキーによる検索
    - 有効期限管理
    - 期限切れデータの削除
    """

    @abstractmethod
    async def find_by_cache_key(self, cache_key: str) -> Optional[AnalysisCache]:
        """
        キャッシュキーによる検索

        Args:
            cache_key: キャッシュキー

        Returns:
            Optional[AnalysisCache]: 見つかったキャッシュ、存在しない場合None
        """
        pass

    @abstractmethod
    async def find_by_analysis_type(
        self, analysis_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> List[AnalysisCache]:
        """
        分析タイプと通貨ペアによる検索

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸（オプション）

        Returns:
            List[AnalysisCache]: 見つかったキャッシュのリスト
        """
        pass

    @abstractmethod
    async def find_valid_caches(
        self, analysis_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> List[AnalysisCache]:
        """
        有効なキャッシュを検索（期限切れでないもの）

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸（オプション）

        Returns:
            List[AnalysisCache]: 有効なキャッシュのリスト
        """
        pass

    @abstractmethod
    async def save(self, analysis_cache: AnalysisCache) -> AnalysisCache:
        """
        キャッシュを保存

        Args:
            analysis_cache: 保存するキャッシュ

        Returns:
            AnalysisCache: 保存されたキャッシュ
        """
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """
        期限切れのキャッシュを削除

        Returns:
            int: 削除された件数
        """
        pass

    @abstractmethod
    async def delete_by_cache_key(self, cache_key: str) -> bool:
        """
        キャッシュキーによる削除

        Args:
            cache_key: キャッシュキー

        Returns:
            bool: 削除成功の場合True
        """
        pass

    @abstractmethod
    async def delete_by_currency_pair(self, currency_pair: str) -> int:
        """
        通貨ペアによる削除

        Args:
            currency_pair: 通貨ペア

        Returns:
            int: 削除された件数
        """
        pass

    @abstractmethod
    async def get_cache_statistics(self) -> dict:
        """
        キャッシュ統計を取得

        Returns:
            dict: キャッシュ統計情報
        """
        pass

    @abstractmethod
    async def find_caches_expiring_soon(
        self, within_minutes: int = 30
    ) -> List[AnalysisCache]:
        """
        まもなく期限切れになるキャッシュを検索

        Args:
            within_minutes: 何分以内に期限切れになるか

        Returns:
            List[AnalysisCache]: まもなく期限切れになるキャッシュのリスト
        """
        pass

    @abstractmethod
    async def cleanup_old_caches(self, older_than_hours: int = 24) -> int:
        """
        古いキャッシュを削除

        Args:
            older_than_hours: 何時間以上古いものを削除するか

        Returns:
            int: 削除された件数
        """
        pass
