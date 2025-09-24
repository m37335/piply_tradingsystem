"""
レート制限管理システムの統合テスト

レート制限管理システムの統合機能をテストします。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from ..config.settings import RateLimitingSettings
from ..main import RateLimitingService


class TestRateLimitingIntegration:
    """レート制限管理システムの統合テスト"""
    
    @pytest.fixture
    def mock_settings(self):
        """モック設定"""
        return RateLimitingSettings.from_env()
    
    @pytest.fixture
    def mock_service(self, mock_settings):
        """モックサービス"""
        with patch('modules.rate_limiting.main.IntegratedRateLimitManager'):
            service = RateLimitingService(mock_settings)
            service.manager = AsyncMock()
            return service
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, mock_service):
        """サービスのライフサイクルテスト"""
        # サービスを開始
        await mock_service.start()
        assert mock_service._running is True
        mock_service.manager.start.assert_called_once()
        
        # サービスを停止
        await mock_service.stop()
        assert mock_service._running is False
        mock_service.manager.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_provider_management(self, mock_service):
        """プロバイダー管理テスト"""
        # モックプロバイダー
        mock_provider = MagicMock()
        mock_alt_provider = MagicMock()
        
        # プロバイダーを追加
        await mock_service.add_provider("test_provider", mock_provider, 1.0)
        mock_service.manager.add_provider.assert_called_once_with("test_provider", mock_provider, 1.0)
        
        # 代替プロバイダーを追加
        await mock_service.add_alternative_provider("test_alt_provider", mock_alt_provider)
        mock_service.manager.add_alternative_provider.assert_called_once_with("test_alt_provider", mock_alt_provider)
    
    @pytest.mark.asyncio
    async def test_request_execution(self, mock_service):
        """リクエスト実行テスト"""
        # モックの設定
        mock_service.manager.execute_request = AsyncMock(return_value="success")
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # リクエストを実行
        result = await mock_service.execute_request(mock_request_func, "test_cache_key", "test_arg")
        
        # アサーション
        assert result == "success"
        mock_service.manager.execute_request.assert_called_once_with(mock_request_func, "test_cache_key", "test_arg")
    
    @pytest.mark.asyncio
    async def test_stats_and_health(self, mock_service):
        """統計とヘルスチェックテスト"""
        # モックの設定
        mock_stats = {"total_requests": 100, "success_rate": 95.0}
        mock_health = {"status": "healthy", "components": {}}
        
        mock_service.manager.get_stats = MagicMock(return_value=mock_stats)
        mock_service.manager.health_check = AsyncMock(return_value=mock_health)
        
        # 統計情報を取得
        stats = await mock_service.get_stats()
        assert stats == mock_stats
        
        # ヘルスチェック
        health = await mock_service.health_check()
        assert health == mock_health
    
    @pytest.mark.asyncio
    async def test_stats_reset(self, mock_service):
        """統計リセットテスト"""
        # モックの設定
        mock_service.manager.reset_stats = AsyncMock()
        
        # 統計をリセット
        await mock_service.reset_stats()
        
        # アサーション
        mock_service.manager.reset_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_service):
        """エラーハンドリングテスト"""
        # サービス開始時のエラー
        mock_service.manager.start = AsyncMock(side_effect=Exception("Start failed"))
        
        with pytest.raises(Exception, match="Start failed"):
            await mock_service.start()
        
        # サービス停止時のエラー
        mock_service.manager.stop = AsyncMock(side_effect=Exception("Stop failed"))
        
        with pytest.raises(Exception, match="Stop failed"):
            await mock_service.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_service):
        """並行リクエストテスト"""
        # モックの設定
        mock_service.manager.execute_request = AsyncMock(return_value="success")
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            await asyncio.sleep(0.1)  # 少し待機
            return f"success_{args[0]}"
        
        # 並行リクエストを実行
        tasks = []
        for i in range(5):
            task = mock_service.execute_request(mock_request_func, f"cache_key_{i}", f"arg_{i}")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # アサーション
        assert len(results) == 5
        assert all(result == "success" for result in results)
        assert mock_service.manager.execute_request.call_count == 5
    
    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self, mock_service):
        """レート制限動作テスト"""
        # モックの設定
        call_count = 0
        
        async def mock_execute_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return "success"
            else:
                raise Exception("Rate limit exceeded")
        
        mock_service.manager.execute_request = mock_execute_request
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # 複数回リクエストを実行
        results = []
        for i in range(5):
            try:
                result = await mock_service.execute_request(mock_request_func, f"cache_key_{i}", f"arg_{i}")
                results.append(result)
            except Exception as e:
                results.append(f"error: {str(e)}")
        
        # アサーション
        assert len(results) == 5
        assert results[:3] == ["success", "success", "success"]
        assert "error: Rate limit exceeded" in results[3:]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_behavior(self, mock_service):
        """サーキットブレーカー動作テスト"""
        # モックの設定
        call_count = 0
        
        async def mock_execute_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Service unavailable")
            else:
                return "success"
        
        mock_service.manager.execute_request = mock_execute_request
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # 複数回リクエストを実行
        results = []
        for i in range(4):
            try:
                result = await mock_service.execute_request(mock_request_func, f"cache_key_{i}", f"arg_{i}")
                results.append(result)
            except Exception as e:
                results.append(f"error: {str(e)}")
        
        # アサーション
        assert len(results) == 4
        assert "error: Service unavailable" in results[:2]
        assert "success" in results[2:]
    
    @pytest.mark.asyncio
    async def test_fallback_behavior(self, mock_service):
        """フォールバック動作テスト"""
        # モックの設定
        call_count = 0
        
        async def mock_execute_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Primary service failed")
            else:
                return "fallback_success"
        
        mock_service.manager.execute_request = mock_execute_request
        
        # リクエスト関数
        async def mock_request_func(provider, *args, **kwargs):
            return "success"
        
        # リクエストを実行
        result = await mock_service.execute_request(mock_request_func, "cache_key", "arg")
        
        # アサーション
        assert result == "fallback_success"
        assert mock_service.manager.execute_request.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])
