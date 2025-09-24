"""
統合レート制限管理システムのテスト

統合レート制限管理システムの機能をテストします。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from ..core.integrated_rate_limit_manager import IntegratedRateLimitManager, IntegratedRateLimitConfig
from ..core.rate_limiter.advanced_rate_limiter import RateLimitAlgorithm
from ..core.circuit_breaker.circuit_breaker import CircuitState
from ..core.load_balancer.load_balancer import LoadBalancingStrategy
from ..core.fallback_manager.fallback_manager import FallbackStrategy


class TestIntegratedRateLimitManager:
    """統合レート制限管理システムのテスト"""
    
    @pytest.fixture
    def mock_config(self):
        """モック設定"""
        return IntegratedRateLimitConfig(
            rate_limit_algorithm=RateLimitAlgorithm.ADAPTIVE,
            requests_per_second=10.0,
            burst_capacity=50,
            circuit_breaker_enabled=True,
            failure_threshold=5,
            recovery_timeout=60,
            load_balancing_strategy=LoadBalancingStrategy.HEALTH_BASED,
            max_retries=3,
            fallback_strategies=[FallbackStrategy.CACHE, FallbackStrategy.ALTERNATIVE_PROVIDER],
            cache_ttl_seconds=300
        )
    
    @pytest.fixture
    def mock_manager(self, mock_config):
        """モック管理システム"""
        with patch('modules.rate_limiting.core.integrated_rate_limit_manager.AdvancedRateLimiter'), \
             patch('modules.rate_limiting.core.integrated_rate_limit_manager.CircuitBreaker'), \
             patch('modules.rate_limiting.core.integrated_rate_limit_manager.LoadBalancer'), \
             patch('modules.rate_limiting.core.integrated_rate_limit_manager.FallbackManager'):
            
            manager = IntegratedRateLimitManager(mock_config)
            manager.rate_limiter = AsyncMock()
            manager.circuit_breaker = AsyncMock()
            manager.load_balancer = AsyncMock()
            manager.fallback_manager = AsyncMock()
            
            return manager
    
    @pytest.mark.asyncio
    async def test_start_manager(self, mock_manager):
        """管理システムの開始テスト"""
        # モックの設定
        mock_manager.load_balancer.start = AsyncMock()
        
        # 管理システムを開始
        await mock_manager.start()
        
        # アサーション
        mock_manager.load_balancer.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_manager(self, mock_manager):
        """管理システムの停止テスト"""
        # モックの設定
        mock_manager.load_balancer.stop = AsyncMock()
        
        # 管理システムを停止
        await mock_manager.stop()
        
        # アサーション
        mock_manager.load_balancer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_provider(self, mock_manager):
        """プロバイダー追加テスト"""
        # モックプロバイダー
        mock_provider = MagicMock()
        
        # プロバイダーを追加
        mock_manager.add_provider("test_provider", mock_provider, 1.0)
        
        # アサーション
        mock_manager.load_balancer.add_provider.assert_called_once_with("test_provider", mock_provider, 1.0)
    
    @pytest.mark.asyncio
    async def test_add_alternative_provider(self, mock_manager):
        """代替プロバイダー追加テスト"""
        # モックプロバイダー
        mock_provider = MagicMock()
        
        # 代替プロバイダーを追加
        mock_manager.add_alternative_provider("test_alt_provider", mock_provider)
        
        # アサーション
        mock_manager.fallback_manager.add_alternative_provider.assert_called_once_with("test_alt_provider", mock_provider)
    
    @pytest.mark.asyncio
    async def test_execute_request_success(self, mock_manager):
        """リクエスト実行成功テスト"""
        # モックの設定
        mock_manager.rate_limiter.acquire = AsyncMock(return_value=True)
        mock_manager.circuit_breaker.call = AsyncMock(return_value="success")
        mock_manager.fallback_manager.cache_data = AsyncMock()
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # リクエストを実行
        result = await mock_manager.execute_request(mock_request_func, "test_cache_key", "test_arg")
        
        # アサーション
        assert result == "success"
        mock_manager.rate_limiter.acquire.assert_called_once()
        mock_manager.circuit_breaker.call.assert_called_once()
        mock_manager.fallback_manager.cache_data.assert_called_once_with("test_cache_key", "success")
    
    @pytest.mark.asyncio
    async def test_execute_request_rate_limited(self, mock_manager):
        """レート制限時のリクエスト実行テスト"""
        # モックの設定
        mock_manager.rate_limiter.acquire = AsyncMock(return_value=False)
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # リクエストを実行（レート制限で失敗）
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await mock_manager.execute_request(mock_request_func, "test_cache_key", "test_arg")
        
        # アサーション
        mock_manager.rate_limiter.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_request_circuit_breaker_open(self, mock_manager):
        """サーキットブレーカーオープン時のリクエスト実行テスト"""
        # モックの設定
        mock_manager.rate_limiter.acquire = AsyncMock(return_value=True)
        mock_manager.circuit_breaker.call = AsyncMock(side_effect=Exception("Circuit breaker open"))
        mock_manager.fallback_manager.execute_with_fallback = AsyncMock(return_value="fallback_success")
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # リクエストを実行
        result = await mock_manager.execute_request(mock_request_func, "test_cache_key", "test_arg")
        
        # アサーション
        assert result == "fallback_success"
        mock_manager.rate_limiter.acquire.assert_called_once()
        mock_manager.circuit_breaker.call.assert_called_once()
        mock_manager.fallback_manager.execute_with_fallback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_request_fallback_failure(self, mock_manager):
        """フォールバック失敗時のリクエスト実行テスト"""
        # モックの設定
        mock_manager.rate_limiter.acquire = AsyncMock(return_value=True)
        mock_manager.circuit_breaker.call = AsyncMock(side_effect=Exception("Circuit breaker open"))
        mock_manager.fallback_manager.execute_with_fallback = AsyncMock(side_effect=Exception("All fallback strategies failed"))
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # リクエストを実行（フォールバックも失敗）
        with pytest.raises(Exception, match="All fallback strategies failed"):
            await mock_manager.execute_request(mock_request_func, "test_cache_key", "test_arg")
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_manager):
        """ヘルスチェックテスト"""
        # モックの設定
        mock_manager.rate_limiter.get_stats = MagicMock(return_value={"status": "healthy"})
        mock_manager.circuit_breaker.get_state = MagicMock(return_value={"state": "closed"})
        mock_manager.load_balancer.get_stats = MagicMock(return_value={"overall": {"healthy_providers": 2, "total_providers": 2}})
        mock_manager.fallback_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # ヘルスチェック
        health = await mock_manager.health_check()
        
        # アサーション
        assert health["overall"] == "healthy"
        assert "components" in health
        assert "rate_limiter" in health["components"]
        assert "circuit_breaker" in health["components"]
        assert "load_balancer" in health["components"]
        assert "fallback_manager" in health["components"]
    
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_manager):
        """統計情報取得テスト"""
        # モックの設定
        mock_manager.rate_limiter.get_stats = MagicMock(return_value={"total_requests": 100})
        mock_manager.circuit_breaker.get_state = MagicMock(return_value={"state": "closed"})
        mock_manager.load_balancer.get_stats = MagicMock(return_value={"overall": {"total_requests": 100}})
        mock_manager.fallback_manager.get_stats = MagicMock(return_value={"total_fallbacks": 10})
        
        # 統計情報を取得
        stats = mock_manager.get_stats()
        
        # アサーション
        assert "overall" in stats
        assert "rate_limiter" in stats
        assert "circuit_breaker" in stats
        assert "load_balancer" in stats
        assert "fallback_manager" in stats
    
    @pytest.mark.asyncio
    async def test_reset_stats(self, mock_manager):
        """統計リセットテスト"""
        # モックの設定
        mock_manager.rate_limiter.reset = AsyncMock()
        mock_manager.circuit_breaker.reset = AsyncMock()
        
        # 統計をリセット
        await mock_manager.reset_stats()
        
        # アサーション
        mock_manager.rate_limiter.reset.assert_called_once()
        mock_manager.circuit_breaker.reset.assert_called_once()
        
        # 統計がリセットされていることを確認
        assert mock_manager.total_requests == 0
        assert mock_manager.successful_requests == 0
        assert mock_manager.failed_requests == 0
        assert mock_manager.rate_limited_requests == 0
        assert mock_manager.circuit_breaker_blocked_requests == 0
        assert mock_manager.fallback_used_requests == 0


if __name__ == "__main__":
    pytest.main([__file__])
