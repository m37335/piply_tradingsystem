"""
Redis Cache Client
Redis キャッシュクライアント

設計書参照:
- インフラ・プラグイン設計_20250809.md

Redisを使用した高性能キャッシュシステム
"""

import asyncio
import json
import pickle
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class RedisClient:
    """
    Redis キャッシュクライアント

    責任:
    - Redis接続の管理
    - 非同期キャッシュ操作
    - データのシリアライゼーション
    - TTL（有効期限）管理
    - キー名前空間管理
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        namespace: str = "exchange_analytics",
        encoding: str = "utf-8",
        decode_responses: bool = True,
        max_connections: int = 10,
        retry_on_timeout: bool = True,
        health_check_interval: int = 30,
        **kwargs,
    ):
        """
        初期化

        Args:
            host: Redisホスト
            port: Redisポート
            password: Redis認証パスワード
            db: Redis データベース番号
            namespace: キー名前空間
            encoding: エンコーディング
            decode_responses: レスポンスデコードフラグ
            max_connections: 最大接続数
            retry_on_timeout: タイムアウト時リトライフラグ
            health_check_interval: ヘルスチェック間隔（秒）
            **kwargs: その他のRedis設定
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.namespace = namespace
        self.encoding = encoding
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval

        # Redis接続プール
        self._pool: Optional[redis.ConnectionPool] = None
        self._redis: Optional[Redis] = None
        self._is_connected = False

        # ヘルスチェックタスク
        self._health_check_task: Optional[asyncio.Task] = None

        # 統計情報
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}

        logger.debug(f"Initialized Redis client for {host}:{port}/{db}")

    async def connect(self) -> None:
        """
        Redisに接続
        """
        try:
            if self._is_connected:
                logger.warning("Redis client is already connected")
                return

            # 接続プールを作成
            self._pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                encoding=self.encoding,
                decode_responses=self.decode_responses,
                max_connections=self.max_connections,
                retry_on_timeout=self.retry_on_timeout,
            )

            # Redisクライアントを作成
            self._redis = Redis(connection_pool=self._pool)

            # 接続テスト
            await self._redis.ping()

            self._is_connected = True

            # ヘルスチェックタスクを開始
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            logger.info(f"Connected to Redis at {self.host}:{self.port}/{self.db}")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """
        Redis接続を切断
        """
        try:
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass

            if self._redis:
                await self._redis.close()

            if self._pool:
                await self._pool.disconnect()

            self._is_connected = False

            logger.info("Disconnected from Redis")

        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {str(e)}")

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self.disconnect()

    def _ensure_connected(self) -> None:
        """接続状態をチェック"""
        if not self._is_connected or not self._redis:
            raise RuntimeError("Redis client is not connected")

    def _build_key(self, key: str) -> str:
        """
        名前空間付きキーを構築

        Args:
            key: ベースキー

        Returns:
            str: 名前空間付きキー
        """
        return f"{self.namespace}:{key}"

    def _serialize_value(self, value: Any) -> str:
        """
        値をシリアライズ

        Args:
            value: シリアライズする値

        Returns:
            str: シリアライズされた値
        """
        if isinstance(value, (str, int, float)):
            return str(value)
        elif isinstance(value, (dict, list, tuple)):
            return json.dumps(value, ensure_ascii=False, default=str)
        else:
            # 複雑なオブジェクトはpickleを使用
            return pickle.dumps(value).hex()

    def _deserialize_value(self, value: str, value_type: type = str) -> Any:
        """
        値をデシリアライズ

        Args:
            value: デシリアライズする値
            value_type: 期待される型

        Returns:
            Any: デシリアライズされた値
        """
        if value_type == str:
            return value
        elif value_type == int:
            return int(value)
        elif value_type == float:
            return float(value)
        elif value_type in (dict, list, tuple):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # JSON解析失敗時はpickleを試行
                return pickle.loads(bytes.fromhex(value))
        else:
            # その他の型はpickleでデシリアライズ
            try:
                return pickle.loads(bytes.fromhex(value))
            except:
                return value

    async def get(self, key: str, default: Any = None, value_type: type = str) -> Any:
        """
        キャッシュから値を取得

        Args:
            key: キー
            default: デフォルト値
            value_type: 期待される値の型

        Returns:
            Any: 取得された値またはデフォルト値
        """
        try:
            self._ensure_connected()

            full_key = self._build_key(key)
            value = await self._redis.get(full_key)

            if value is None:
                self._stats["misses"] += 1
                logger.debug(f"Cache miss: {key}")
                return default

            self._stats["hits"] += 1
            logger.debug(f"Cache hit: {key}")

            return self._deserialize_value(value, value_type)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to get cache value for {key}: {str(e)}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        キャッシュに値を設定

        Args:
            key: キー
            value: 値
            ttl: 有効期限（秒）
            nx: キーが存在しない場合のみ設定
            xx: キーが存在する場合のみ設定

        Returns:
            bool: 設定成功時True
        """
        try:
            self._ensure_connected()

            full_key = self._build_key(key)
            serialized_value = self._serialize_value(value)

            result = await self._redis.set(
                full_key, serialized_value, ex=ttl, nx=nx, xx=xx
            )

            if result:
                self._stats["sets"] += 1
                logger.debug(f"Cache set: {key} (TTL: {ttl})")

            return bool(result)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to set cache value for {key}: {str(e)}")
            return False

    async def delete(self, *keys: str) -> int:
        """
        キャッシュからキーを削除

        Args:
            *keys: 削除するキー

        Returns:
            int: 削除されたキー数
        """
        try:
            self._ensure_connected()

            if not keys:
                return 0

            full_keys = [self._build_key(key) for key in keys]
            deleted_count = await self._redis.delete(*full_keys)

            self._stats["deletes"] += deleted_count
            logger.debug(f"Cache deleted: {deleted_count} keys")

            return deleted_count

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to delete cache keys {keys}: {str(e)}")
            return 0

    async def exists(self, *keys: str) -> int:
        """
        キーの存在確認

        Args:
            *keys: 確認するキー

        Returns:
            int: 存在するキー数
        """
        try:
            self._ensure_connected()

            if not keys:
                return 0

            full_keys = [self._build_key(key) for key in keys]
            return await self._redis.exists(*full_keys)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to check key existence {keys}: {str(e)}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        キーに有効期限を設定

        Args:
            key: キー
            ttl: 有効期限（秒）

        Returns:
            bool: 設定成功時True
        """
        try:
            self._ensure_connected()

            full_key = self._build_key(key)
            result = await self._redis.expire(full_key, ttl)

            logger.debug(f"Set expiration for {key}: {ttl}s")
            return bool(result)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to set expiration for {key}: {str(e)}")
            return False

    async def ttl(self, key: str) -> int:
        """
        キーの残り有効期限を取得

        Args:
            key: キー

        Returns:
            int: 残り有効期限（秒）、-1: 無期限、-2: キー存在せず
        """
        try:
            self._ensure_connected()

            full_key = self._build_key(key)
            return await self._redis.ttl(full_key)

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to get TTL for {key}: {str(e)}")
            return -2

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        パターンにマッチするキーを取得

        Args:
            pattern: 検索パターン

        Returns:
            List[str]: マッチするキーのリスト（名前空間除去済み）
        """
        try:
            self._ensure_connected()

            full_pattern = self._build_key(pattern)
            full_keys = await self._redis.keys(full_pattern)

            # 名前空間を除去してキーを返す
            namespace_prefix = f"{self.namespace}:"
            keys = [
                key.replace(namespace_prefix, "", 1)
                for key in full_keys
                if key.startswith(namespace_prefix)
            ]

            return keys

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to get keys with pattern {pattern}: {str(e)}")
            return []

    async def flushdb(self) -> bool:
        """
        現在のデータベースをクリア

        Warning:
            開発・テスト環境でのみ使用すること

        Returns:
            bool: クリア成功時True
        """
        try:
            self._ensure_connected()

            await self._redis.flushdb()
            logger.warning("Redis database flushed")
            return True

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to flush Redis database: {str(e)}")
            return False

    async def ping(self) -> bool:
        """
        Redis接続テスト

        Returns:
            bool: 接続正常時True
        """
        try:
            if not self._is_connected or not self._redis:
                return False

            response = await self._redis.ping()
            return response == True

        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False

    async def info(self) -> Dict[str, Any]:
        """
        Redis情報を取得

        Returns:
            Dict[str, Any]: Redis情報
        """
        try:
            self._ensure_connected()

            info_data = await self._redis.info()
            return info_data

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Failed to get Redis info: {str(e)}")
            return {}

    async def _health_check_loop(self) -> None:
        """
        定期的なヘルスチェック
        """
        while self._is_connected:
            try:
                await asyncio.sleep(self.health_check_interval)

                if not await self.ping():
                    logger.warning("Redis health check failed")
                    # 必要に応じて再接続ロジックを実装
                else:
                    logger.debug("Redis health check passed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        統計情報を取得

        Returns:
            Dict[str, Union[int, float]]: 統計情報
        """
        total_operations = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_operations if total_operations > 0 else 0.0
        )

        return {
            **self._stats,
            "total_operations": total_operations,
            "hit_rate": round(hit_rate, 3),
            "miss_rate": round(1 - hit_rate, 3),
        }

    def reset_stats(self) -> None:
        """統計情報をリセット"""
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}
        logger.debug("Cache statistics reset")

    def __repr__(self) -> str:
        """文字列表現"""
        return f"RedisClient(host={self.host}, port={self.port}, db={self.db}, namespace={self.namespace})"


# 便利関数とデコレータ


def cache_key_builder(*parts: str, separator: str = ":") -> str:
    """
    キャッシュキーを構築

    Args:
        *parts: キーの構成要素
        separator: セパレータ

    Returns:
        str: 構築されたキー
    """
    return separator.join(str(part) for part in parts if part)


class CacheManager:
    """
    キャッシュマネージャー

    複数のキャッシュ操作を簡単にするためのヘルパークラス
    """

    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    async def get_or_set(
        self,
        key: str,
        func,
        ttl: Optional[int] = None,
        value_type: type = str,
        *args,
        **kwargs,
    ) -> Any:
        """
        キャッシュから値を取得、なければ関数を実行して設定

        Args:
            key: キャッシュキー
            func: 値を生成する関数
            ttl: 有効期限
            value_type: 値の型
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            Any: キャッシュされた値または新しい値
        """
        # キャッシュから取得を試行
        cached_value = await self.redis.get(key, value_type=value_type)

        if cached_value is not None:
            return cached_value

        # キャッシュにない場合は関数を実行
        if asyncio.iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)

        # 結果をキャッシュ
        await self.redis.set(key, value, ttl=ttl)

        return value

    @asynccontextmanager
    async def lock(self, key: str, timeout: int = 10) -> AsyncGenerator[bool, None]:
        """
        分散ロック

        Args:
            key: ロックキー
            timeout: タイムアウト（秒）

        Yields:
            bool: ロック取得成功時True
        """
        lock_key = f"lock:{key}"
        lock_value = f"locked:{datetime.utcnow().timestamp()}"

        try:
            # ロック取得を試行
            acquired = await self.redis.set(lock_key, lock_value, ttl=timeout, nx=True)

            yield acquired

        finally:
            if acquired:
                # ロック解除
                await self.redis.delete(lock_key)
