"""
フォールバック戦略実装

API障害時の代替戦略を実装します。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class FallbackStrategy(ABC):
    """フォールバック戦略の基底クラス"""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """フォールバック戦略を実行"""
        pass


class CacheFallbackStrategy(FallbackStrategy):
    """キャッシュフォールバック戦略"""
    
    def __init__(self, cache_ttl: int = 300):
        """
        キャッシュフォールバック戦略を初期化
        
        Args:
            cache_ttl: キャッシュの有効期限（秒）
        """
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
    
    async def execute(self, key: str, *args, **kwargs) -> Optional[Any]:
        """
        キャッシュからデータを取得
        
        Args:
            key: キャッシュキー
            *args: その他の引数
            **kwargs: その他のキーワード引数
            
        Returns:
            キャッシュされたデータ、またはNone
        """
        if key in self.cache:
            cached_data = self.cache[key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['data']
            else:
                # 期限切れのキャッシュを削除
                del self.cache[key]
        
        return None
    
    def set_cache(self, key: str, data: Any) -> None:
        """
        キャッシュにデータを保存
        
        Args:
            key: キャッシュキー
            data: 保存するデータ
        """
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }


class AlternativeProviderFallbackStrategy(FallbackStrategy):
    """代替プロバイダーフォールバック戦略"""
    
    def __init__(self, alternative_providers: List[Any]):
        """
        代替プロバイダーフォールバック戦略を初期化
        
        Args:
            alternative_providers: 代替プロバイダーのリスト
        """
        self.alternative_providers = alternative_providers
        self.current_provider_index = 0
    
    async def execute(self, method_name: str, *args, **kwargs) -> Any:
        """
        代替プロバイダーでメソッドを実行
        
        Args:
            method_name: 実行するメソッド名
            *args: メソッドの引数
            **kwargs: メソッドのキーワード引数
            
        Returns:
            メソッドの実行結果
        """
        for provider in self.alternative_providers:
            try:
                method = getattr(provider, method_name)
                return await method(*args, **kwargs)
            except Exception:
                continue
        
        raise Exception("All alternative providers failed")


class OldDataFallbackStrategy(FallbackStrategy):
    """古いデータフォールバック戦略"""
    
    def __init__(self, max_age_seconds: int = 3600):
        """
        古いデータフォールバック戦略を初期化
        
        Args:
            max_age_seconds: 古いデータの最大有効期限（秒）
        """
        self.max_age_seconds = max_age_seconds
        self.old_data: Dict[str, Dict[str, Any]] = {}
    
    async def execute(self, key: str, *args, **kwargs) -> Optional[Any]:
        """
        古いデータを取得
        
        Args:
            key: データキー
            *args: その他の引数
            **kwargs: その他のキーワード引数
            
        Returns:
            古いデータ、またはNone
        """
        if key in self.old_data:
            data_info = self.old_data[key]
            if time.time() - data_info['timestamp'] < self.max_age_seconds:
                return data_info['data']
        
        return None
    
    def set_old_data(self, key: str, data: Any) -> None:
        """
        古いデータを保存
        
        Args:
            key: データキー
            data: 保存するデータ
        """
        self.old_data[key] = {
            'data': data,
            'timestamp': time.time()
        }


class DefaultValueFallbackStrategy(FallbackStrategy):
    """デフォルト値フォールバック戦略"""
    
    def __init__(self, default_value: Any):
        """
        デフォルト値フォールバック戦略を初期化
        
        Args:
            default_value: デフォルト値
        """
        self.default_value = default_value
    
    async def execute(self, *args, **kwargs) -> Any:
        """
        デフォルト値を返す
        
        Args:
            *args: その他の引数
            **kwargs: その他のキーワード引数
            
        Returns:
            デフォルト値
        """
        return self.default_value


class RetryFallbackStrategy(FallbackStrategy):
    """リトライフォールバック戦略"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        リトライフォールバック戦略を初期化
        
        Args:
            max_retries: 最大リトライ回数
            retry_delay: リトライ間隔（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def execute(self, func, *args, **kwargs) -> Any:
        """
        関数をリトライして実行
        
        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数バックオフ
                else:
                    break
        
        raise last_exception
