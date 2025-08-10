"""
API Call History Repository Interface
API呼び出し履歴リポジトリインターフェース

設計書参照:
- api_optimization_design_2025.md

API呼び出し履歴のリポジトリインターフェース
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from ..entities.api_call_history import ApiCallHistory


class ApiCallHistoryRepository(ABC):
    """
    API呼び出し履歴リポジトリインターフェース

    責任:
    - API呼び出し履歴の永続化
    - レート制限監視
    - パフォーマンス測定
    - エラー追跡
    """

    @abstractmethod
    async def save(self, api_call_history: ApiCallHistory) -> ApiCallHistory:
        """
        API呼び出し履歴を保存

        Args:
            api_call_history: 保存するAPI呼び出し履歴

        Returns:
            ApiCallHistory: 保存されたAPI呼び出し履歴
        """
        pass

    @abstractmethod
    async def find_recent_calls(
        self, api_name: str, minutes: int = 60
    ) -> List[ApiCallHistory]:
        """
        最近のAPI呼び出しを検索

        Args:
            api_name: API名
            minutes: 何分以内の呼び出しを検索するか

        Returns:
            List[ApiCallHistory]: 最近のAPI呼び出しのリスト
        """
        pass

    @abstractmethod
    async def get_call_statistics(
        self, api_name: str, hours: int = 24
    ) -> Dict[str, any]:
        """
        API呼び出し統計を取得

        Args:
            api_name: API名
            hours: 何時間分の統計を取得するか

        Returns:
            Dict[str, any]: API呼び出し統計情報
        """
        pass

    @abstractmethod
    async def find_rate_limit_errors(
        self, api_name: str, hours: int = 24
    ) -> List[ApiCallHistory]:
        """
        レート制限エラーを検索

        Args:
            api_name: API名
            hours: 何時間分を検索するか

        Returns:
            List[ApiCallHistory]: レート制限エラーのリスト
        """
        pass

    @abstractmethod
    async def find_slow_responses(
        self, api_name: str, threshold_ms: int = 5000, hours: int = 24
    ) -> List[ApiCallHistory]:
        """
        遅いレスポンスを検索

        Args:
            api_name: API名
            threshold_ms: 閾値（ミリ秒）
            hours: 何時間分を検索するか

        Returns:
            List[ApiCallHistory]: 遅いレスポンスのリスト
        """
        pass

    @abstractmethod
    async def get_performance_summary(
        self, api_name: str, hours: int = 24
    ) -> Dict[str, any]:
        """
        パフォーマンスサマリーを取得

        Args:
            api_name: API名
            hours: 何時間分のサマリーを取得するか

        Returns:
            Dict[str, any]: パフォーマンスサマリー
        """
        pass

    @abstractmethod
    async def cleanup_old_calls(self, older_than_days: int = 7) -> int:
        """
        古いAPI呼び出し履歴を削除

        Args:
            older_than_days: 何日以上古いものを削除するか

        Returns:
            int: 削除された件数
        """
        pass

    @abstractmethod
    async def find_failed_calls(
        self, api_name: str, hours: int = 24
    ) -> List[ApiCallHistory]:
        """
        失敗したAPI呼び出しを検索

        Args:
            api_name: API名
            hours: 何時間分を検索するか

        Returns:
            List[ApiCallHistory]: 失敗したAPI呼び出しのリスト
        """
        pass

    @abstractmethod
    async def get_error_summary(self, api_name: str, hours: int = 24) -> Dict[str, any]:
        """
        エラーサマリーを取得

        Args:
            api_name: API名
            hours: 何時間分のサマリーを取得するか

        Returns:
            Dict[str, any]: エラーサマリー
        """
        pass
