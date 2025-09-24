"""
代替プロバイダーフォールバック

代替プロバイダーを使用したフォールバック戦略を実装します。
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .fallback_config import FallbackConfig, FallbackStrategy


@dataclass
class Provider:
    """プロバイダー"""
    id: str
    name: str
    is_available: bool = True
    last_used: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    response_time: float = 0.0


class AlternativeProviderFallback:
    """代替プロバイダーフォールバック"""
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        self.providers: List[Provider] = []
        self.current_provider_index = 0
    
    def add_provider(self, provider_id: str, name: str) -> None:
        """
        プロバイダーを追加
        
        Args:
            provider_id: プロバイダーID
            name: プロバイダー名
        """
        provider = Provider(id=provider_id, name=name)
        self.providers.append(provider)
    
    def remove_provider(self, provider_id: str) -> bool:
        """
        プロバイダーを削除
        
        Args:
            provider_id: プロバイダーID
            
        Returns:
            削除が成功したかどうか
        """
        for i, provider in enumerate(self.providers):
            if provider.id == provider_id:
                del self.providers[i]
                return True
        return False
    
    def get_next_provider(self) -> Optional[Provider]:
        """
        次のプロバイダーを取得
        
        Returns:
            次のプロバイダー、またはNone
        """
        if not self.providers:
            return None
        
        # 利用可能なプロバイダーのみを取得
        available_providers = [p for p in self.providers if p.is_available]
        
        if not available_providers:
            return None
        
        # ラウンドロビンでプロバイダーを選択
        provider = available_providers[self.current_provider_index % len(available_providers)]
        self.current_provider_index = (self.current_provider_index + 1) % len(available_providers)
        
        # プロバイダーの使用情報を更新
        provider.last_used = time.time()
        
        return provider
    
    def get_provider_by_id(self, provider_id: str) -> Optional[Provider]:
        """
        IDでプロバイダーを取得
        
        Args:
            provider_id: プロバイダーID
            
        Returns:
            プロバイダー、またはNone
        """
        for provider in self.providers:
            if provider.id == provider_id:
                return provider
        return None
    
    def mark_provider_unavailable(self, provider_id: str) -> None:
        """
        プロバイダーを利用不可としてマーク
        
        Args:
            provider_id: プロバイダーID
        """
        provider = self.get_provider_by_id(provider_id)
        if provider:
            provider.is_available = False
    
    def mark_provider_available(self, provider_id: str) -> None:
        """
        プロバイダーを利用可能としてマーク
        
        Args:
            provider_id: プロバイダーID
        """
        provider = self.get_provider_by_id(provider_id)
        if provider:
            provider.is_available = True
    
    def record_success(self, provider_id: str, response_time: float) -> None:
        """
        成功を記録
        
        Args:
            provider_id: プロバイダーID
            response_time: レスポンス時間
        """
        provider = self.get_provider_by_id(provider_id)
        if provider:
            provider.success_count += 1
            provider.response_time = (provider.response_time + response_time) / 2
    
    def record_failure(self, provider_id: str) -> None:
        """
        失敗を記録
        
        Args:
            provider_id: プロバイダーID
        """
        provider = self.get_provider_by_id(provider_id)
        if provider:
            provider.failure_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        total_providers = len(self.providers)
        available_providers = sum(1 for p in self.providers if p.is_available)
        total_requests = sum(p.success_count + p.failure_count for p in self.providers)
        
        return {
            "total_providers": total_providers,
            "available_providers": available_providers,
            "unavailable_providers": total_providers - available_providers,
            "total_requests": total_requests,
            "current_provider_index": self.current_provider_index
        }
    
    def get_provider_stats(self) -> List[Dict[str, Any]]:
        """
        プロバイダー別の統計情報を取得
        
        Returns:
            プロバイダー統計のリスト
        """
        return [
            {
                "id": provider.id,
                "name": provider.name,
                "is_available": provider.is_available,
                "success_count": provider.success_count,
                "failure_count": provider.failure_count,
                "response_time": provider.response_time,
                "last_used": provider.last_used
            }
            for provider in self.providers
        ]
    
    def reset_stats(self) -> None:
        """統計をリセット"""
        for provider in self.providers:
            provider.success_count = 0
            provider.failure_count = 0
            provider.response_time = 0.0
            provider.last_used = 0.0
        self.current_provider_index = 0
