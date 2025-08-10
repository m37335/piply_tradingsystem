"""
File Cache System
ファイルキャッシュシステム

設計書参照:
- api_optimization_design_2025.md

ディスクベースのキャッシュシステム
"""

import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class FileCache:
    """
    ファイルキャッシュシステム

    責任:
    - ディスクベースキャッシュの管理
    - サイズ制限の管理
    - TTL管理
    - 圧縮機能
    - 自動クリーンアップ
    """

    def __init__(
        self,
        cache_dir: str = "/app/cache",
        max_size_mb: int = 100,
        ttl_seconds: int = 1800,
        enable_compression: bool = True,
    ):
        """
        初期化

        Args:
            cache_dir: キャッシュディレクトリ
            max_size_mb: 最大サイズ（MB）
            ttl_seconds: TTL（秒）
            enable_compression: 圧縮を有効にするかどうか
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_mb = max_size_mb
        self.ttl_seconds = ttl_seconds
        self.enable_compression = enable_compression

        # キャッシュディレクトリを作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"FileCache initialized: {cache_dir}, "
            f"max_size: {max_size_mb}MB, ttl: {ttl_seconds}s"
        )

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """
        キャッシュファイルのパスを取得

        Args:
            cache_key: キャッシュキー

        Returns:
            Path: キャッシュファイルのパス
        """
        # キャッシュキーをハッシュ化してファイル名に変換
        safe_key = cache_key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.cache"

    def _get_metadata_file_path(self, cache_key: str) -> Path:
        """
        メタデータファイルのパスを取得

        Args:
            cache_key: キャッシュキー

        Returns:
            Path: メタデータファイルのパス
        """
        safe_key = cache_key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.meta"

    def _compress_data(self, data: str) -> bytes:
        """
        データを圧縮

        Args:
            data: 圧縮するデータ

        Returns:
            bytes: 圧縮されたデータ
        """
        if self.enable_compression:
            return gzip.compress(data.encode("utf-8"))
        else:
            return data.encode("utf-8")

    def _decompress_data(self, compressed_data: bytes) -> str:
        """
        データを解凍

        Args:
            compressed_data: 解凍するデータ

        Returns:
            str: 解凍されたデータ
        """
        if self.enable_compression:
            return gzip.decompress(compressed_data).decode("utf-8")
        else:
            return compressed_data.decode("utf-8")

    def _save_metadata(self, cache_key: str, metadata: Dict[str, Any]) -> None:
        """
        メタデータを保存

        Args:
            cache_key: キャッシュキー
            metadata: メタデータ
        """
        metadata_file = self._get_metadata_file_path(cache_key)
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _load_metadata(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        メタデータを読み込み

        Args:
            cache_key: キャッシュキー

        Returns:
            Optional[Dict[str, Any]]: メタデータ
        """
        metadata_file = self._get_metadata_file_path(cache_key)
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata for {cache_key}: {str(e)}")
            return None

    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """
        キャッシュが期限切れかどうかを判定

        Args:
            metadata: メタデータ

        Returns:
            bool: 期限切れの場合True
        """
        if "expires_at" not in metadata:
            return True

        try:
            expires_at = datetime.fromisoformat(metadata["expires_at"])
            return datetime.utcnow() > expires_at
        except Exception as e:
            logger.error(f"Failed to check expiration: {str(e)}")
            return True

    def _get_cache_size_mb(self) -> float:
        """
        キャッシュサイズを取得（MB）

        Returns:
            float: キャッシュサイズ（MB）
        """
        total_size = 0
        for file_path in self.cache_dir.glob("*.cache"):
            total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)

    def _cleanup_expired_files(self) -> int:
        """
        期限切れファイルを削除

        Returns:
            int: 削除されたファイル数
        """
        deleted_count = 0
        for file_path in self.cache_dir.glob("*.cache"):
            cache_key = file_path.stem
            metadata = self._load_metadata(cache_key)

            if metadata and self._is_expired(metadata):
                try:
                    # キャッシュファイルとメタデータファイルを削除
                    file_path.unlink()
                    metadata_file = self._get_metadata_file_path(cache_key)
                    if metadata_file.exists():
                        metadata_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete expired file {file_path}: {str(e)}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired cache files")

        return deleted_count

    def _cleanup_oldest_files(self, target_size_mb: float) -> int:
        """
        古いファイルを削除してサイズを調整

        Args:
            target_size_mb: 目標サイズ（MB）

        Returns:
            int: 削除されたファイル数
        """
        deleted_count = 0
        current_size = self._get_cache_size_mb()

        if current_size <= target_size_mb:
            return deleted_count

        # ファイルを更新時刻でソート
        files_with_time = []
        for file_path in self.cache_dir.glob("*.cache"):
            try:
                mtime = file_path.stat().st_mtime
                files_with_time.append((file_path, mtime))
            except Exception as e:
                logger.error(f"Failed to get file time {file_path}: {str(e)}")

        # 古い順にソート
        files_with_time.sort(key=lambda x: x[1])

        # 古いファイルから削除
        for file_path, _ in files_with_time:
            if self._get_cache_size_mb() <= target_size_mb:
                break

            try:
                cache_key = file_path.stem
                file_path.unlink()
                metadata_file = self._get_metadata_file_path(cache_key)
                if metadata_file.exists():
                    metadata_file.unlink()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {str(e)}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old cache files")

        return deleted_count

    def get(self, cache_key: str) -> Optional[Any]:
        """
        キャッシュからデータを取得

        Args:
            cache_key: キャッシュキー

        Returns:
            Optional[Any]: キャッシュされたデータ
        """
        try:
            cache_file = self._get_cache_file_path(cache_key)
            if not cache_file.exists():
                return None

            # メタデータをチェック
            metadata = self._load_metadata(cache_key)
            if not metadata or self._is_expired(metadata):
                self.delete(cache_key)
                return None

            # データを読み込み
            with open(cache_file, "rb") as f:
                compressed_data = f.read()

            data_str = self._decompress_data(compressed_data)
            data = json.loads(data_str)

            logger.debug(f"Cache hit: {cache_key}")
            return data

        except Exception as e:
            logger.error(f"Failed to get cache for {cache_key}: {str(e)}")
            return None

    def set(self, cache_key: str, data: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        キャッシュにデータを保存

        Args:
            cache_key: キャッシュキー
            data: 保存するデータ
            ttl_seconds: TTL（秒、Noneの場合はデフォルト値）

        Returns:
            bool: 保存成功の場合True
        """
        try:
            # 期限切れファイルをクリーンアップ
            self._cleanup_expired_files()

            # サイズ制限をチェック
            if self._get_cache_size_mb() > self.max_size_mb * 0.9:
                self._cleanup_oldest_files(self.max_size_mb * 0.8)

            # TTLを設定
            if ttl_seconds is None:
                ttl_seconds = self.ttl_seconds

            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)

            # メタデータを作成
            metadata = {
                "cache_key": cache_key,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl_seconds": ttl_seconds,
                "compressed": self.enable_compression,
            }

            # データをJSON文字列に変換
            data_str = json.dumps(data, ensure_ascii=False, indent=2)
            compressed_data = self._compress_data(data_str)

            # ファイルに保存
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, "wb") as f:
                f.write(compressed_data)

            # メタデータを保存
            self._save_metadata(cache_key, metadata)

            logger.debug(f"Cache set: {cache_key}, size: {len(compressed_data)} bytes")
            return True

        except Exception as e:
            logger.error(f"Failed to set cache for {cache_key}: {str(e)}")
            return False

    def delete(self, cache_key: str) -> bool:
        """
        キャッシュを削除

        Args:
            cache_key: キャッシュキー

        Returns:
            bool: 削除成功の場合True
        """
        try:
            cache_file = self._get_cache_file_path(cache_key)
            metadata_file = self._get_metadata_file_path(cache_key)

            deleted = False
            if cache_file.exists():
                cache_file.unlink()
                deleted = True

            if metadata_file.exists():
                metadata_file.unlink()

            if deleted:
                logger.debug(f"Cache deleted: {cache_key}")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete cache for {cache_key}: {str(e)}")
            return False

    def clear(self) -> int:
        """
        全キャッシュを削除

        Returns:
            int: 削除されたファイル数
        """
        try:
            deleted_count = 0
            for file_path in self.cache_dir.glob("*.cache"):
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {str(e)}")

            # メタデータファイルも削除
            for file_path in self.cache_dir.glob("*.meta"):
                try:
                    file_path.unlink()
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {str(e)}")

            logger.info(f"Cleared {deleted_count} cache files")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            Dict[str, Any]: キャッシュ統計
        """
        try:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_files = len(cache_files)
            total_size_mb = self._get_cache_size_mb()

            # 期限切れファイル数をカウント
            expired_count = 0
            for file_path in cache_files:
                cache_key = file_path.stem
                metadata = self._load_metadata(cache_key)
                if metadata and self._is_expired(metadata):
                    expired_count += 1

            statistics = {
                "total_files": total_files,
                "total_size_mb": total_size_mb,
                "expired_files": expired_count,
                "valid_files": total_files - expired_count,
                "max_size_mb": self.max_size_mb,
                "usage_percentage": (total_size_mb / self.max_size_mb) * 100,
                "compression_enabled": self.enable_compression,
                "cache_directory": str(self.cache_dir),
            }

            logger.debug(f"Cache statistics: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            return {"error": str(e)}
