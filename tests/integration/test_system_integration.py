"""
システム統合テスト

システム全体の統合テストを実行します。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_collection.core.data_collection_service import DataCollectionService
from modules.data_collection.config.settings import DataCollectionSettings
from modules.scheduler.core.scheduler_service import SchedulerService
from modules.scheduler.config.settings import SchedulerSettings
from modules.llm_analysis.core.llm_analysis_service import LLMAnalysisService
from modules.llm_analysis.config.settings import LLMAnalysisSettings
from modules.rate_limiting.core.integrated_rate_limit_manager import IntegratedRateLimitManager
from modules.rate_limiting.config.settings import RateLimitingSettings


class TestSystemIntegration:
    """システム統合テスト"""
    
    @pytest.fixture
    def mock_database_manager(self):
        """モックデータベース管理"""
        manager = AsyncMock()
        manager.initialize = AsyncMock()
        manager.close = AsyncMock()
        manager.health_check = AsyncMock(return_value={"status": "healthy"})
        manager.execute_query = AsyncMock(return_value=[])
        manager.execute_command = AsyncMock()
        return manager
    
    @pytest.fixture
    def mock_settings(self):
        """モック設定"""
        return {
            "data_collection": DataCollectionSettings.from_env(),
            "scheduler": SchedulerSettings.from_env(),
            "llm_analysis": LLMAnalysisSettings.from_env(),
            "rate_limiting": RateLimitingSettings.from_env()
        }
    
    @pytest.mark.asyncio
    async def test_data_collection_service_integration(self, mock_database_manager, mock_settings):
        """データ収集サービスの統合テスト"""
        with patch('modules.data_collection.core.data_collection_service.DatabaseConnectionManager', return_value=mock_database_manager):
            service = DataCollectionService(mock_settings["data_collection"])
            
            # サービスを開始
            await service.start()
            assert service._running is True
            
            # ヘルスチェック
            health = await service.health_check()
            assert health["status"] in ["healthy", "unhealthy"]
            
            # サービスを停止
            await service.stop()
            assert service._running is False
    
    @pytest.mark.asyncio
    async def test_scheduler_service_integration(self, mock_database_manager, mock_settings):
        """スケジューラーサービスの統合テスト"""
        with patch('modules.scheduler.core.scheduler_service.DatabaseConnectionManager', return_value=mock_database_manager), \
             patch('modules.scheduler.core.scheduler_service.MarketHoursManager'), \
             patch('modules.scheduler.core.scheduler_service.TaskScheduler'), \
             patch('modules.scheduler.core.scheduler_service.DataCollectionTasks'):
            
            service = SchedulerService(mock_settings["scheduler"])
            service.market_hours_manager = AsyncMock()
            service.task_scheduler = AsyncMock()
            service.data_collection_tasks = AsyncMock()
            
            # サービスを開始
            await service.start()
            assert service._running is True
            
            # ヘルスチェック
            health = await service.health_check()
            assert health["status"] in ["healthy", "unhealthy"]
            
            # サービスを停止
            await service.stop()
            assert service._running is False
    
    @pytest.mark.asyncio
    async def test_llm_analysis_service_integration(self, mock_database_manager, mock_settings):
        """LLM分析サービスの統合テスト"""
        with patch('modules.llm_analysis.core.llm_analysis_service.DatabaseConnectionManager', return_value=mock_database_manager), \
             patch('modules.llm_analysis.core.llm_analysis_service.DataPreparator'), \
             patch('modules.llm_analysis.core.llm_analysis_service.LLMClient'), \
             patch('modules.llm_analysis.core.llm_analysis_service.AnalysisEngine'), \
             patch('modules.llm_analysis.core.llm_analysis_service.QualityController'):
            
            service = LLMAnalysisService(mock_settings["llm_analysis"])
            service.data_preparator = AsyncMock()
            service.llm_client = AsyncMock()
            service.analysis_engine = AsyncMock()
            service.quality_controller = AsyncMock()
            
            # サービスを開始
            await service.start()
            assert service._running is True
            
            # ヘルスチェック
            health = await service.health_check()
            assert health["status"] in ["healthy", "unhealthy"]
            
            # サービスを停止
            await service.stop()
            assert service._running is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting_service_integration(self, mock_settings):
        """レート制限サービスの統合テスト"""
        with patch('modules.rate_limiting.core.integrated_rate_limit_manager.AdvancedRateLimiter'), \
             patch('modules.rate_limiting.core.integrated_rate_limit_manager.CircuitBreaker'), \
             patch('modules.rate_limiting.core.integrated_rate_limit_manager.LoadBalancer'), \
             patch('modules.rate_limiting.core.integrated_rate_limit_manager.FallbackManager'):
            
            manager = IntegratedRateLimitManager(mock_settings["rate_limiting"])
            manager.rate_limiter = AsyncMock()
            manager.circuit_breaker = AsyncMock()
            manager.load_balancer = AsyncMock()
            manager.fallback_manager = AsyncMock()
            
            # サービスを開始
            await manager.start()
            
            # ヘルスチェック
            health = await manager.health_check()
            assert health["status"] in ["healthy", "unhealthy"]
            
            # サービスを停止
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_end_to_end_data_flow(self, mock_database_manager, mock_settings):
        """エンドツーエンドデータフローテスト"""
        # モックデータ
        mock_price_data = [
            {
                "symbol": "AAPL",
                "timeframe": "5m",
                "timestamp": datetime.now(),
                "open": 150.0,
                "high": 151.0,
                "low": 149.0,
                "close": 150.5,
                "volume": 1000000
            }
        ]
        
        mock_database_manager.execute_query.return_value = mock_price_data
        
        # データ収集サービス
        with patch('modules.data_collection.core.data_collection_service.DatabaseConnectionManager', return_value=mock_database_manager):
            data_service = DataCollectionService(mock_settings["data_collection"])
            await data_service.start()
            
            # データ収集のシミュレーション
            collection_status = await data_service.get_collection_status()
            assert "service_running" in collection_status
            
            await data_service.stop()
        
        # スケジューラーサービス
        with patch('modules.scheduler.core.scheduler_service.DatabaseConnectionManager', return_value=mock_database_manager), \
             patch('modules.scheduler.core.scheduler_service.MarketHoursManager'), \
             patch('modules.scheduler.core.scheduler_service.TaskScheduler'), \
             patch('modules.scheduler.core.scheduler_service.DataCollectionTasks'):
            
            scheduler_service = SchedulerService(mock_settings["scheduler"])
            scheduler_service.market_hours_manager = AsyncMock()
            scheduler_service.task_scheduler = AsyncMock()
            scheduler_service.data_collection_tasks = AsyncMock()
            
            await scheduler_service.start()
            
            # スケジューラーの統計
            scheduler_stats = await scheduler_service.get_scheduler_stats()
            assert "service_running" in scheduler_stats
            
            await scheduler_service.stop()
        
        # LLM分析サービス
        with patch('modules.llm_analysis.core.llm_analysis_service.DatabaseConnectionManager', return_value=mock_database_manager), \
             patch('modules.llm_analysis.core.llm_analysis_service.DataPreparator'), \
             patch('modules.llm_analysis.core.llm_analysis_service.LLMClient'), \
             patch('modules.llm_analysis.core.llm_analysis_service.AnalysisEngine'), \
             patch('modules.llm_analysis.core.llm_analysis_service.QualityController'):
            
            llm_service = LLMAnalysisService(mock_settings["llm_analysis"])
            llm_service.data_preparator = AsyncMock()
            llm_service.llm_client = AsyncMock()
            llm_service.analysis_engine = AsyncMock()
            llm_service.quality_controller = AsyncMock()
            
            await llm_service.start()
            
            # 分析サマリー
            analysis_summary = await llm_service.get_analysis_summary()
            assert "service_running" in analysis_summary
            
            await llm_service.stop()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, mock_database_manager, mock_settings):
        """エラーハンドリングと回復テスト"""
        # データベースエラーのシミュレーション
        mock_database_manager.execute_query.side_effect = Exception("Database connection failed")
        
        with patch('modules.data_collection.core.data_collection_service.DatabaseConnectionManager', return_value=mock_database_manager):
            service = DataCollectionService(mock_settings["data_collection"])
            
            # エラーが発生してもサービスは開始できる
            await service.start()
            assert service._running is True
            
            # エラー時のヘルスチェック
            health = await service.health_check()
            assert health["status"] == "unhealthy"
            
            await service.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, mock_database_manager, mock_settings):
        """並行操作テスト"""
        with patch('modules.data_collection.core.data_collection_service.DatabaseConnectionManager', return_value=mock_database_manager):
            service = DataCollectionService(mock_settings["data_collection"])
            await service.start()
            
            # 並行でヘルスチェックを実行
            tasks = []
            for i in range(5):
                task = service.health_check()
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            # すべてのヘルスチェックが成功
            assert len(results) == 5
            assert all("status" in result for result in results)
            
            await service.stop()
    
    @pytest.mark.asyncio
    async def test_service_lifecycle_management(self, mock_database_manager, mock_settings):
        """サービスライフサイクル管理テスト"""
        with patch('modules.data_collection.core.data_collection_service.DatabaseConnectionManager', return_value=mock_database_manager):
            service = DataCollectionService(mock_settings["data_collection"])
            
            # 初期状態
            assert service._running is False
            
            # 開始
            await service.start()
            assert service._running is True
            
            # 重複開始のテスト
            await service.start()  # 警告が出力されるが、エラーにならない
            assert service._running is True
            
            # 停止
            await service.stop()
            assert service._running is False
            
            # 重複停止のテスト
            await service.stop()  # エラーにならない
            assert service._running is False
    
    @pytest.mark.asyncio
    async def test_configuration_validation(self, mock_settings):
        """設定検証テスト"""
        # データ収集設定の検証
        data_collection_config = mock_settings["data_collection"].to_dict()
        assert "yahoo_finance" in data_collection_config
        assert "database" in data_collection_config
        assert "collection" in data_collection_config
        
        # スケジューラー設定の検証
        scheduler_config = mock_settings["scheduler"].to_dict()
        assert "market_hours" in scheduler_config
        assert "task_scheduler" in scheduler_config
        assert "data_collection" in scheduler_config
        
        # LLM分析設定の検証
        llm_config = mock_settings["llm_analysis"].to_dict()
        assert "llm" in llm_config
        assert "analysis" in llm_config
        assert "data_preparation" in llm_config
        assert "quality_control" in llm_config
        
        # レート制限設定の検証
        rate_limiting_config = mock_settings["rate_limiting"].to_dict()
        assert "rate_limit" in rate_limiting_config
        assert "circuit_breaker" in rate_limiting_config
        assert "load_balancer" in rate_limiting_config
        assert "fallback" in rate_limiting_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
