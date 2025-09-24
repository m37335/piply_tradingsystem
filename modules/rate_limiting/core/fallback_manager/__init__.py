"""
フォールバック管理システム

API障害時の代替戦略を提供します。
"""

from .fallback_manager import FallbackManager
from .cache_fallback import CacheFallback
from .alternative_provider_fallback import AlternativeProviderFallback

__all__ = [
    'FallbackManager',
    'CacheFallback',
    'AlternativeProviderFallback'
]
