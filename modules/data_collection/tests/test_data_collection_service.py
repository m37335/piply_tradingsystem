"""
データ収集サービスのテスト

データ収集サービスの機能をテストします。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ..core.data_collection_service import DataCollectionService
from ..config.settings import DataCollectionSettings, TimeFrame, DataCollectionMode


class TestDataCollectionService:
    """データ収集サービスのテスト"""
    
    @pytest.fixture
    def mock_settings(self):
        """モック設定"""
        return DataCollectionSettings(
            yahoo_finance=MagicMock(),
            database=MagicMock(),
            collection=MagicMock(
                symbols=["AAPL", "MSFT"],
                timeframes=[TimeFrame.M5, TimeFrame.H1],
                mode=DataCollectionMode.CONTINUOUS,
                batch_size=100,
                max_workers=5,
                collection_interval_seconds=300
            ),
            log_level="INFO",
            enable_quality_checks=True,
            quality_threshold=0.95
        )
    
    @pytest.fixture
    def mock_service(self, mock_settings):
        """モックサービス"""
        with patch('modules.data_collection.core.data_collection_service.YahooFinanceProvider'), \
             patch('modules.data_collection.core.data_collection_service.IntelligentDataCollector'), \
             patch('modules.data_collection.core.data_collection_service.DatabaseConnectionManager'), \
             patch('modules.data_collection.core.data_collection_service.DatabaseSaver'):
            
            service = DataCollectionService(mock_settings)
            service.database_manager = AsyncMock()
            service.database_saver = AsyncMock()
            service.collector = AsyncMock()
            service.provider = AsyncMock()
            
            return service
    
    @pytest.mark.asyncio
    async def test_start_service(self, mock_service):
        """サービスの開始テスト"""
        # モックの設定
        mock_service.database_manager.initialize = AsyncMock()
        mock_service._start_continuous_collection = AsyncMock()
        
        # サービスを開始
        await mock_service.start()
        
        # アサーション
        assert mock_service._running is True
        mock_service.database_manager.initialize.assert_called_once()
        mock_service._start_continuous_collection.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_service(self, mock_service):
        """サービスの停止テスト"""
        # モックの設定
        mock_service._running = True
        mock_service._tasks = [AsyncMock(), AsyncMock()]
        mock_service.database_manager.close = AsyncMock()
        
        # サービスを停止
        await mock_service.stop()
        
        # アサーション
        assert mock_service._running is False
        mock_service.database_manager.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_latest_data(self, mock_service):
        """最新データ収集テスト"""
        # モックの設定
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
        
        mock_service.collector.collect_data = AsyncMock(return_value=mock_price_data)
        mock_service.database_saver.save_price_data = AsyncMock()
        mock_service._check_data_quality = AsyncMock()
        
        # 最新データを収集
        await mock_service._collect_latest_data("AAPL", TimeFrame.M5)
        
        # アサーション
        mock_service.collector.collect_data.assert_called_once()
        mock_service.database_saver.save_price_data.assert_called_once_with(mock_price_data)
        mock_service._check_data_quality.assert_called_once_with("AAPL", TimeFrame.M5, mock_price_data)
    
    @pytest.mark.asyncio
    async def test_get_latest_timestamp(self, mock_service):
        """最新タイムスタンプ取得テスト"""
        # モックの設定
        mock_result = [{"latest_timestamp": datetime.now()}]
        mock_service.database_manager.execute_query = AsyncMock(return_value=mock_result)
        
        # 最新タイムスタンプを取得
        result = await mock_service._get_latest_timestamp("AAPL", TimeFrame.M5)
        
        # アサーション
        assert result is not None
        mock_service.database_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_manual(self, mock_service):
        """手動データ収集テスト"""
        # モックの設定
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
        
        mock_service.collector.collect_data = AsyncMock(return_value=mock_price_data)
        mock_service.database_saver.save_price_data = AsyncMock()
        mock_service.database_saver.save_price_data.return_value.records_saved = 1
        mock_service.database_saver.save_price_data.return_value.records_updated = 0
        
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        
        # 手動データ収集
        result = await mock_service.collect_manual("AAPL", TimeFrame.M5, start_date, end_date)
        
        # アサーション
        assert result["success"] is True
        assert result["records_collected"] == 1
        assert result["records_saved"] == 1
        mock_service.collector.collect_data.assert_called_once()
        mock_service.database_saver.save_price_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_collection_status(self, mock_service):
        """収集状況取得テスト"""
        # モックの設定
        mock_service._running = True
        mock_service._tasks = [AsyncMock(), AsyncMock()]
        mock_service.database_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_service._get_latest_timestamp = AsyncMock(return_value=datetime.now())
        
        # 収集状況を取得
        status = await mock_service.get_collection_status()
        
        # アサーション
        assert status["service_running"] is True
        assert status["active_tasks"] == 2
        assert status["database_health"]["status"] == "healthy"
        assert "symbol_status" in status
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_service):
        """ヘルスチェックテスト"""
        # モックの設定
        mock_service._running = True
        mock_service._tasks = [AsyncMock(), AsyncMock()]
        mock_service.database_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_service.provider.health_check = AsyncMock(return_value=True)
        
        # ヘルスチェック
        health = await mock_service.health_check()
        
        # アサーション
        assert health["status"] == "healthy"
        assert health["service_running"] is True
        assert health["active_tasks"] == 2
        assert health["database"]["status"] == "healthy"
        assert health["provider"] is True
    
    @pytest.mark.asyncio
    async def test_check_data_quality(self, mock_service):
        """データ品質チェックテスト"""
        # テストデータ
        price_data = [
            {
                "symbol": "AAPL",
                "timeframe": "5m",
                "timestamp": datetime.now(),
                "open": 150.0,
                "high": 151.0,
                "low": 149.0,
                "close": 150.5,
                "volume": 1000000
            },
            {
                "symbol": "AAPL",
                "timeframe": "5m",
                "timestamp": datetime.now() - timedelta(minutes=5),
                "open": 149.0,
                "high": 150.0,
                "low": 148.0,
                "close": 149.5,
                "volume": 900000
            }
        ]
        
        # データ品質チェック
        await mock_service._check_data_quality("AAPL", TimeFrame.M5, price_data)
        
        # ログが出力されることを確認（実際の実装では品質スコアを計算）
        # このテストでは例外が発生しないことを確認
        assert True
    
    @pytest.mark.asyncio
    async def test_backfill_collection(self, mock_service):
        """バックフィル収集テスト"""
        # モックの設定
        mock_service._get_latest_timestamp = AsyncMock(return_value=None)
        mock_service._collect_historical_data = AsyncMock()
        
        # バックフィル収集
        await mock_service._backfill_symbol_timeframe("AAPL", TimeFrame.M5)
        
        # アサーション
        mock_service._get_latest_timestamp.assert_called_once_with("AAPL", TimeFrame.M5)
        mock_service._collect_historical_data.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
