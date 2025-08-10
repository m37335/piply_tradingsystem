"""
Cache Manager System
3層キャッシュ管理システム

設計書参照:
- api_optimization_design_2025.md

メモリ、ファイル、データベースの3層キャッシュシステム
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ...domain.repositories.analysis_cache_repository import AnalysisCacheRepository
from ...utils.cache_utils import generate_cache_key
from ...utils.logging_config import get_infrastructure_logger
from .analysis_cache import AnalysisCacheManager
from .file_cache import FileCache

logger = get_infrastructure_logger()


class MemoryCache:
    """
    メモリキャッシュシステム

    責任:
    - 高速なメモリベースキャッシュ
    - サイズ制限管理
    - TTL管理
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        初期化

        Args:
            max_size: 最大エントリ数
            ttl_seconds: TTL（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, datetime] = {}

        logger.info(f"MemoryCache initialized: max_size={max_size}, ttl={ttl_seconds}s")

    def _is_expired(self, access_time: datetime) -> bool:
        """
        期限切れかどうかを判定

        Args:
            access_time: アクセス時刻

        Returns:
            bool: 期限切れの場合True
        """
        return datetime.utcnow() - access_time > timedelta(seconds=self.ttl_seconds)

    def _cleanup_expired(self) -> int:
        """
        期限切れエントリを削除

        Returns:
            int: 削除されたエントリ数
        """
        expired_keys = [
            key
            for key, access_time in self._access_times.items()
            if self._is_expired(access_time)
        ]

        for key in expired_keys:
            del self._cache[key]
            del self._access_times[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired memory cache entries")

        return len(expired_keys)

    def _evict_oldest(self) -> int:
        """
        古いエントリを削除

        Returns:
            int: 削除されたエントリ数
        """
        if len(self._cache) <= self.max_size:
            return 0

        # アクセス時刻でソート
        sorted_items = sorted(self._access_times.items(), key=lambda x: x[1])

        # 古い順に削除
        to_delete = len(self._cache) - self.max_size
        deleted_count = 0

        for key, _ in sorted_items[:to_delete]:
            del self._cache[key]
            del self._access_times[key]
            deleted_count += 1

        if deleted_count > 0:
            logger.debug(f"Evicted {deleted_count} old memory cache entries")

        return deleted_count

    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュからデータを取得

        Args:
            key: キャッシュキー

        Returns:
            Optional[Any]: キャッシュされたデータ
        """
        try:
            # 期限切れエントリをクリーンアップ
            self._cleanup_expired()

            if key not in self._cache:
                return None

            # アクセス時刻を更新
            self._access_times[key] = datetime.utcnow()
            data = self._cache[key]

            logger.debug(f"Memory cache hit: {key}")
            return data

        except Exception as e:
            logger.error(f"Failed to get memory cache for {key}: {str(e)}")
            return None

    def set(self, key: str, data: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        キャッシュにデータを保存

        Args:
            key: キャッシュキー
            data: 保存するデータ
            ttl_seconds: TTL（秒、Noneの場合はデフォルト値）

        Returns:
            bool: 保存成功の場合True
        """
        try:
            # 期限切れエントリをクリーンアップ
            self._cleanup_expired()

            # サイズ制限をチェック
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            # TTLを設定
            if ttl_seconds is None:
                ttl_seconds = self.ttl_seconds

            # データを保存
            self._cache[key] = data
            self._access_times[key] = datetime.utcnow()

            logger.debug(f"Memory cache set: {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to set memory cache for {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        キャッシュを削除

        Args:
            key: キャッシュキー

        Returns:
            bool: 削除成功の場合True
        """
        try:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                logger.debug(f"Memory cache deleted: {key}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete memory cache for {key}: {str(e)}")
            return False

    def clear(self) -> int:
        """
        全キャッシュを削除

        Returns:
            int: 削除されたエントリ数
        """
        try:
            count = len(self._cache)
            self._cache.clear()
            self._access_times.clear()
            logger.info(f"Cleared {count} memory cache entries")
            return count

        except Exception as e:
            logger.error(f"Failed to clear memory cache: {str(e)}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            Dict[str, Any]: キャッシュ統計
        """
        try:
            # 期限切れエントリをクリーンアップ
            expired_count = self._cleanup_expired()

            total_entries = len(self._cache)
            valid_entries = total_entries - expired_count

            statistics = {
                "total_entries": total_entries,
                "valid_entries": valid_entries,
                "expired_entries": expired_count,
                "max_size": self.max_size,
                "usage_percentage": (total_entries / self.max_size) * 100,
                "ttl_seconds": self.ttl_seconds,
            }

            logger.debug(f"Memory cache statistics: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"Failed to get memory cache statistics: {str(e)}")
            return {"error": str(e)}


class CacheManager:
    """
    3層キャッシュ管理システム

    責任:
    - メモリキャッシュ管理
    - ファイルキャッシュ管理
    - データベースキャッシュ管理
    - 有効期限管理
    - 自動クリーンアップ
    """

    def __init__(
        self,
        analysis_cache_repository: AnalysisCacheRepository,
        memory_cache_size: int = 1000,
        memory_cache_ttl: int = 300,
        file_cache_dir: str = "/app/cache",
        file_cache_size_mb: int = 100,
        file_cache_ttl: int = 1800,
        analysis_cache_ttl_minutes: int = 60,
    ):
        """
        初期化

        Args:
            analysis_cache_repository: 分析キャッシュリポジトリ
            memory_cache_size: メモリキャッシュサイズ
            memory_cache_ttl: メモリキャッシュTTL（秒）
            file_cache_dir: ファイルキャッシュディレクトリ
            file_cache_size_mb: ファイルキャッシュサイズ（MB）
            file_cache_ttl: ファイルキャッシュTTL（秒）
            analysis_cache_ttl_minutes: 分析キャッシュTTL（分）
        """
        # 3層キャッシュを初期化
        self.memory_cache = MemoryCache(
            max_size=memory_cache_size,
            ttl_seconds=memory_cache_ttl,
        )

        self.file_cache = FileCache(
            cache_dir=file_cache_dir,
            max_size_mb=file_cache_size_mb,
            ttl_seconds=file_cache_ttl,
        )

        self.analysis_cache = AnalysisCacheManager(
            repository=analysis_cache_repository,
            default_ttl_minutes=analysis_cache_ttl_minutes,
        )

        logger.info(
            f"CacheManager initialized with 3-layer cache system: "
            f"memory({memory_cache_size} entries, {memory_cache_ttl}s), "
            f"file({file_cache_size_mb}MB, {file_cache_ttl}s), "
            f"analysis({analysis_cache_ttl_minutes}min)"
        )

    def _generate_cache_key(self, cache_type: str, components: Dict[str, Any]) -> str:
        """
        キャッシュキーを生成

        Args:
            cache_type: キャッシュタイプ
            components: キーコンポーネント

        Returns:
            str: キャッシュキー
        """
        return generate_cache_key(cache_type, components)

    async def get(
        self,
        cache_type: str,
        components: Dict[str, Any],
        use_memory: bool = True,
        use_file: bool = True,
        use_database: bool = True,
    ) -> Optional[Any]:
        """
        キャッシュからデータを取得（3層検索）

        Args:
            cache_type: キャッシュタイプ
            components: キーコンポーネント
            use_memory: メモリキャッシュを使用するか
            use_file: ファイルキャッシュを使用するか
            use_database: データベースキャッシュを使用するか

        Returns:
            Optional[Any]: キャッシュされたデータ
        """
        try:
            cache_key = self._generate_cache_key(cache_type, components)

            # 1. メモリキャッシュから検索
            if use_memory:
                data = self.memory_cache.get(cache_key)
                if data is not None:
                    logger.debug(f"Cache hit (memory): {cache_key}")
                    return data

            # 2. ファイルキャッシュから検索
            if use_file:
                data = self.file_cache.get(cache_key)
                if data is not None:
                    # メモリキャッシュにも保存
                    if use_memory:
                        self.memory_cache.set(cache_key, data)
                    logger.debug(f"Cache hit (file): {cache_key}")
                    return data

            # 3. データベースキャッシュから検索（分析キャッシュの場合）
            if use_database and cache_type == "analysis":
                data = await self.analysis_cache.get_analysis(**components)
                if data is not None:
                    # メモリとファイルキャッシュにも保存
                    if use_memory:
                        self.memory_cache.set(cache_key, data)
                    if use_file:
                        self.file_cache.set(cache_key, data)
                    logger.debug(f"Cache hit (database): {cache_key}")
                    return data

            logger.debug(f"Cache miss: {cache_key}")
            return None

        except Exception as e:
            logger.error(f"Failed to get cache for {cache_type}: {str(e)}")
            return None

    async def set(
        self,
        cache_type: str,
        components: Dict[str, Any],
        data: Any,
        ttl_seconds: Optional[int] = None,
        use_memory: bool = True,
        use_file: bool = True,
        use_database: bool = True,
    ) -> bool:
        """
        キャッシュにデータを保存（3層保存）

        Args:
            cache_type: キャッシュタイプ
            components: キーコンポーネント
            data: 保存するデータ
            ttl_seconds: TTL（秒、Noneの場合はデフォルト値）
            use_memory: メモリキャッシュを使用するか
            use_file: ファイルキャッシュを使用するか
            use_database: データベースキャッシュを使用するか

        Returns:
            bool: 保存成功の場合True
        """
        try:
            cache_key = self._generate_cache_key(cache_type, components)
            success_count = 0

            # 1. メモリキャッシュに保存
            if use_memory:
                if self.memory_cache.set(cache_key, data, ttl_seconds):
                    success_count += 1

            # 2. ファイルキャッシュに保存
            if use_file:
                if self.file_cache.set(cache_key, data, ttl_seconds):
                    success_count += 1

            # 3. データベースキャッシュに保存（分析キャッシュの場合）
            if use_database and cache_type == "analysis":
                ttl_minutes = ttl_seconds // 60 if ttl_seconds else None
                if await self.analysis_cache.set_analysis(
                    **components, analysis_data=data, ttl_minutes=ttl_minutes
                ):
                    success_count += 1

            logger.debug(f"Cache set: {cache_key} ({success_count} layers)")
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to set cache for {cache_type}: {str(e)}")
            return False

    async def delete(
        self,
        cache_type: str,
        components: Dict[str, Any],
        use_memory: bool = True,
        use_file: bool = True,
        use_database: bool = True,
    ) -> bool:
        """
        キャッシュを削除（3層削除）

        Args:
            cache_type: キャッシュタイプ
            components: キーコンポーネント
            use_memory: メモリキャッシュを使用するか
            use_file: ファイルキャッシュを使用するか
            use_database: データベースキャッシュを使用するか

        Returns:
            bool: 削除成功の場合True
        """
        try:
            cache_key = self._generate_cache_key(cache_type, components)
            success_count = 0

            # 1. メモリキャッシュから削除
            if use_memory:
                if self.memory_cache.delete(cache_key):
                    success_count += 1

            # 2. ファイルキャッシュから削除
            if use_file:
                if self.file_cache.delete(cache_key):
                    success_count += 1

            # 3. データベースキャッシュから削除（分析キャッシュの場合）
            if use_database and cache_type == "analysis":
                # 分析キャッシュの削除は別途実装が必要
                pass

            logger.debug(f"Cache deleted: {cache_key} ({success_count} layers)")
            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to delete cache for {cache_type}: {str(e)}")
            return False

    async def clear_all(self) -> Dict[str, int]:
        """
        全キャッシュを削除

        Returns:
            Dict[str, int]: 各層で削除されたエントリ数
        """
        try:
            memory_count = self.memory_cache.clear()
            file_count = self.file_cache.clear()
            analysis_count = await self.analysis_cache.cleanup_expired()

            result = {
                "memory": memory_count,
                "file": file_count,
                "analysis": analysis_count,
                "total": memory_count + file_count + analysis_count,
            }

            logger.info(f"Cleared all caches: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to clear all caches: {str(e)}")
            return {"error": str(e)}

    async def get_statistics(self) -> Dict[str, Any]:
        """
        全キャッシュの統計を取得

        Returns:
            Dict[str, Any]: 全キャッシュの統計
        """
        try:
            memory_stats = self.memory_cache.get_statistics()
            file_stats = self.file_cache.get_statistics()
            analysis_stats = await self.analysis_cache.get_cache_statistics()

            statistics = {
                "memory_cache": memory_stats,
                "file_cache": file_stats,
                "analysis_cache": analysis_stats,
                "total_entries": (
                    memory_stats.get("total_entries", 0)
                    + file_stats.get("total_files", 0)
                    + analysis_stats.get("total_entries", 0)
                ),
            }

            logger.debug(f"Cache statistics: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            return {"error": str(e)}

    async def cleanup_expired(self) -> Dict[str, int]:
        """
        期限切れキャッシュを削除

        Returns:
            Dict[str, int]: 各層で削除されたエントリ数
        """
        try:
            memory_count = self.memory_cache._cleanup_expired()
            file_count = self.file_cache._cleanup_expired_files()
            analysis_count = await self.analysis_cache.cleanup_expired()

            result = {
                "memory": memory_count,
                "file": file_count,
                "analysis": analysis_count,
                "total": memory_count + file_count + analysis_count,
            }

            logger.info(f"Cleaned up expired caches: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to cleanup expired caches: {str(e)}")
            return {"error": str(e)}

    async def invalidate_analysis(
        self,
        analysis_type: Optional[str] = None,
        currency_pair: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> int:
        """
        分析キャッシュを無効化

        Args:
            analysis_type: 分析タイプ（Noneの場合は全て）
            currency_pair: 通貨ペア（Noneの場合は全て）
            timeframe: 時間軸（Noneの場合は全て）

        Returns:
            int: 削除されたキャッシュ数
        """
        try:
            deleted_count = await self.analysis_cache.invalidate_analysis(
                analysis_type, currency_pair, timeframe
            )

            logger.info(f"Invalidated {deleted_count} analysis caches")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to invalidate analysis cache: {str(e)}")
            return 0
