"""
Analysis Cache System
分析結果キャッシュシステム

設計書参照:
- api_optimization_design_2025.md

分析結果のキャッシュシステム
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...domain.entities.analysis_cache import AnalysisCache
from ...domain.repositories.analysis_cache_repository import AnalysisCacheRepository
from ...utils.cache_utils import generate_cache_key
from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class AnalysisCacheManager:
    """
    分析結果キャッシュ管理システム

    責任:
    - 分析結果のキャッシュ管理
    - キャッシュ無効化
    - 有効期限管理
    - 統計情報提供
    """

    def __init__(
        self,
        repository: AnalysisCacheRepository,
        default_ttl_minutes: int = 60,
        max_cache_age_hours: int = 24,
    ):
        """
        初期化

        Args:
            repository: 分析キャッシュリポジトリ
            default_ttl_minutes: デフォルトTTL（分）
            max_cache_age_hours: 最大キャッシュ年齢（時間）
        """
        self.repository = repository
        self.default_ttl_minutes = default_ttl_minutes
        self.max_cache_age_hours = max_cache_age_hours

        logger.info(
            f"AnalysisCacheManager initialized: "
            f"default_ttl={default_ttl_minutes}min, "
            f"max_age={max_cache_age_hours}h"
        )

    def _generate_cache_key(
        self,
        analysis_type: str,
        currency_pair: str,
        timeframe: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        キャッシュキーを生成

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸
            **kwargs: その他のパラメータ

        Returns:
            str: キャッシュキー
        """
        components = {
            "analysis_type": analysis_type,
            "currency_pair": currency_pair,
            "timeframe": timeframe,
            **kwargs,
        }
        return generate_cache_key("analysis", components)

    def _calculate_expires_at(self, ttl_minutes: Optional[int] = None) -> datetime:
        """
        有効期限を計算

        Args:
            ttl_minutes: TTL（分、Noneの場合はデフォルト値）

        Returns:
            datetime: 有効期限
        """
        if ttl_minutes is None:
            ttl_minutes = self.default_ttl_minutes

        return datetime.utcnow() + timedelta(minutes=ttl_minutes)

    async def get_analysis(
        self,
        analysis_type: str,
        currency_pair: str,
        timeframe: Optional[str] = None,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        分析結果を取得

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸
            **kwargs: その他のパラメータ

        Returns:
            Optional[Dict[str, Any]]: 分析結果
        """
        try:
            cache_key = self._generate_cache_key(
                analysis_type, currency_pair, timeframe, **kwargs
            )

            # キャッシュから取得
            cached_analysis = await self.repository.find_by_cache_key(cache_key)
            if not cached_analysis:
                logger.debug(f"Cache miss: {cache_key}")
                return None

            # 有効期限チェック
            if cached_analysis.is_expired():
                logger.debug(f"Cache expired: {cache_key}")
                await self.repository.delete_by_cache_key(cache_key)
                return None

            # データを取得
            analysis_data = cached_analysis.analysis_data
            logger.debug(f"Cache hit: {cache_key}")
            return analysis_data

        except Exception as e:
            logger.error(
                f"Failed to get analysis cache for {analysis_type} "
                f"{currency_pair}: {str(e)}"
            )
            return None

    async def set_analysis(
        self,
        analysis_type: str,
        currency_pair: str,
        analysis_data: Dict[str, Any],
        timeframe: Optional[str] = None,
        ttl_minutes: Optional[int] = None,
        **kwargs,
    ) -> bool:
        """
        分析結果をキャッシュに保存

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            analysis_data: 分析結果データ
            timeframe: 時間軸
            ttl_minutes: TTL（分、Noneの場合はデフォルト値）
            **kwargs: その他のパラメータ

        Returns:
            bool: 保存成功の場合True
        """
        try:
            cache_key = self._generate_cache_key(
                analysis_type, currency_pair, timeframe, **kwargs
            )
            expires_at = self._calculate_expires_at(ttl_minutes)

            # 分析キャッシュエンティティを作成
            analysis_cache = AnalysisCache(
                analysis_type=analysis_type,
                currency_pair=currency_pair,
                timeframe=timeframe,
                analysis_data=analysis_data,
                cache_key=cache_key,
                expires_at=expires_at,
            )

            # リポジトリに保存
            await self.repository.save(analysis_cache)

            logger.debug(
                f"Analysis cache set: {cache_key}, "
                f"expires: {expires_at.isoformat()}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to set analysis cache for {analysis_type} "
                f"{currency_pair}: {str(e)}"
            )
            return False

    async def invalidate_analysis(
        self,
        analysis_type: Optional[str] = None,
        currency_pair: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> int:
        """
        分析結果キャッシュを無効化

        Args:
            analysis_type: 分析タイプ（Noneの場合は全て）
            currency_pair: 通貨ペア（Noneの場合は全て）
            timeframe: 時間軸（Noneの場合は全て）

        Returns:
            int: 削除されたキャッシュ数
        """
        try:
            deleted_count = 0

            if analysis_type and currency_pair:
                # 特定の分析タイプと通貨ペアのキャッシュを削除
                deleted_count = await self.repository.delete_by_analysis_type(
                    analysis_type, currency_pair
                )
            elif analysis_type:
                # 特定の分析タイプのキャッシュを削除
                deleted_count = await self.repository.delete_by_analysis_type(
                    analysis_type
                )
            elif currency_pair:
                # 特定の通貨ペアのキャッシュを削除
                deleted_count = await self.repository.delete_by_currency_pair(
                    currency_pair
                )
            else:
                # 全てのキャッシュを削除
                deleted_count = await self.repository.delete_expired()

            logger.info(
                f"Invalidated {deleted_count} analysis caches: "
                f"type={analysis_type}, pair={currency_pair}, "
                f"timeframe={timeframe}"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to invalidate analysis cache: {str(e)}")
            return 0

    async def cleanup_expired(self) -> int:
        """
        期限切れキャッシュを削除

        Returns:
            int: 削除されたキャッシュ数
        """
        try:
            deleted_count = await self.repository.delete_expired()
            logger.info(f"Cleaned up {deleted_count} expired analysis caches")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired analysis caches: {str(e)}")
            return 0

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            Dict[str, Any]: キャッシュ統計
        """
        try:
            stats = await self.repository.get_statistics()
            return stats

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            return {"error": str(e)}

    def get_analysis_types(self) -> List[str]:
        """
        キャッシュされている分析タイプを取得

        Returns:
            List[str]: 分析タイプのリスト
        """
        try:
            # リポジトリから分析タイプを取得
            # この実装はリポジトリに依存するため、簡易版
            return ["technical_indicators", "currency_correlation", "ai_analysis"]

        except Exception as e:
            logger.error(f"Failed to get analysis types: {str(e)}")
            return []

    def get_currency_pairs(self) -> List[str]:
        """
        キャッシュされている通貨ペアを取得

        Returns:
            List[str]: 通貨ペアのリスト
        """
        try:
            # リポジトリから通貨ペアを取得
            # この実装はリポジトリに依存するため、簡易版
            return ["USDJPY", "EURUSD", "GBPUSD", "USDCHF", "AUDUSD"]

        except Exception as e:
            logger.error(f"Failed to get currency pairs: {str(e)}")
            return []

    async def is_cache_fresh(
        self,
        analysis_type: str,
        currency_pair: str,
        max_age_minutes: Optional[int] = None,
        **kwargs,
    ) -> bool:
        """
        キャッシュが新鮮かどうかを判定

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            max_age_minutes: 最大年齢（分、Noneの場合はデフォルト値）
            **kwargs: その他のパラメータ

        Returns:
            bool: 新鮮な場合True
        """
        try:
            if max_age_minutes is None:
                max_age_minutes = self.default_ttl_minutes

            cache_key = self._generate_cache_key(analysis_type, currency_pair, **kwargs)

            cached_analysis = await self.repository.find_by_cache_key(cache_key)
            if not cached_analysis:
                return False

            # 有効期限と最大年齢をチェック
            if cached_analysis.is_expired():
                return False

            max_age = timedelta(minutes=max_age_minutes)
            cache_age = datetime.utcnow() - cached_analysis.created_at

            return cache_age <= max_age

        except Exception as e:
            logger.error(f"Failed to check cache freshness: {str(e)}")
            return False

    async def get_cache_info(
        self,
        analysis_type: str,
        currency_pair: str,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        キャッシュ情報を取得

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            **kwargs: その他のパラメータ

        Returns:
            Optional[Dict[str, Any]]: キャッシュ情報
        """
        try:
            cache_key = self._generate_cache_key(analysis_type, currency_pair, **kwargs)

            cached_analysis = await self.repository.find_by_cache_key(cache_key)
            if not cached_analysis:
                return None

            cache_age = datetime.utcnow() - cached_analysis.created_at
            time_to_expiry = cached_analysis.expires_at - datetime.utcnow()

            return {
                "cache_key": cache_key,
                "analysis_type": cached_analysis.analysis_type,
                "currency_pair": cached_analysis.currency_pair,
                "timeframe": cached_analysis.timeframe,
                "created_at": cached_analysis.created_at.isoformat(),
                "expires_at": cached_analysis.expires_at.isoformat(),
                "cache_age_minutes": cache_age.total_seconds() / 60,
                "time_to_expiry_minutes": time_to_expiry.total_seconds() / 60,
                "is_expired": cached_analysis.is_expired(),
                "data_size": len(json.dumps(cached_analysis.analysis_data)),
            }

        except Exception as e:
            logger.error(f"Failed to get cache info: {str(e)}")
            return None
