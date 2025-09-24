"""
スケジューラーサービスのテスト

スケジューラーサービスの機能をテストします。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ..core.scheduler_service import SchedulerService
from ..config.settings import SchedulerSettings, TaskPriority, MarketStatus


class TestSchedulerService:
    """スケジューラーサービスのテスト"""
    
    @pytest.fixture
    def mock_settings(self):
        """モック設定"""
        return SchedulerSettings.from_env()
    
    @pytest.fixture
    def mock_service(self, mock_settings):
        """モックサービス"""
        with patch('modules.scheduler.core.scheduler_service.MarketHoursManager'), \
             patch('modules.scheduler.core.scheduler_service.TaskScheduler'), \
             patch('modules.scheduler.core.scheduler_service.DataCollectionTasks'):
            
            service = SchedulerService(mock_settings)
            service.market_hours_manager = AsyncMock()
            service.task_scheduler = AsyncMock()
            service.data_collection_tasks = AsyncMock()
            
            return service
    
    @pytest.mark.asyncio
    async def test_start_service(self, mock_service):
        """サービスの開始テスト"""
        # モックの設定
        mock_service.task_scheduler.start = AsyncMock()
        mock_service._register_data_collection_tasks = AsyncMock()
        mock_service._main_loop = AsyncMock()
        
        # サービスを開始
        await mock_service.start()
        
        # アサーション
        assert mock_service._running is True
        mock_service.task_scheduler.start.assert_called_once()
        mock_service._register_data_collection_tasks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_service(self, mock_service):
        """サービスの停止テスト"""
        # モックの設定
        mock_service._running = True
        mock_service._tasks = [AsyncMock(), AsyncMock()]
        mock_service.task_scheduler.stop = AsyncMock()
        
        # サービスを停止
        await mock_service.stop()
        
        # アサーション
        assert mock_service._running is False
        mock_service.task_scheduler.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_data_collection_tasks(self, mock_service):
        """データ収集タスク登録テスト"""
        # モックの設定
        mock_service.task_scheduler.schedule_task = AsyncMock()
        
        # データ収集タスクを登録
        await mock_service._register_data_collection_tasks()
        
        # アサーション
        # シンボル数 × タイムフレーム数 + 1（バックフィルタスク）のタスクが登録される
        expected_tasks = len(mock_service.settings.data_collection.symbols) * len(mock_service.settings.data_collection.timeframes) + 1
        assert mock_service.task_scheduler.schedule_task.call_count == expected_tasks
    
    @pytest.mark.asyncio
    async def test_adjust_tasks_for_market_status(self, mock_service):
        """市場状況に応じたタスク調整テスト"""
        # モックの設定
        mock_service._adjust_collection_frequency = AsyncMock()
        
        # 市場が開いている場合
        await mock_service._adjust_tasks_for_market_status(MarketStatus.OPEN)
        mock_service._adjust_collection_frequency.assert_called_with(300)  # 5分間隔
        
        # 市場が閉まっている場合
        await mock_service._adjust_tasks_for_market_status(MarketStatus.CLOSED)
        mock_service._adjust_collection_frequency.assert_called_with(3600)  # 1時間間隔
    
    @pytest.mark.asyncio
    async def test_adjust_collection_frequency(self, mock_service):
        """データ収集頻度調整テスト"""
        # モックの設定
        mock_service.task_scheduler.update_task_interval = AsyncMock()
        
        # データ収集頻度を調整
        await mock_service._adjust_collection_frequency(600)
        
        # アサーション
        # シンボル数 × タイムフレーム数のタスクの間隔が更新される
        expected_calls = len(mock_service.settings.data_collection.symbols) * len(mock_service.settings.data_collection.timeframes)
        assert mock_service.task_scheduler.update_task_interval.call_count == expected_calls
    
    @pytest.mark.asyncio
    async def test_schedule_custom_task(self, mock_service):
        """カスタムタスクスケジュールテスト"""
        # モックの設定
        mock_service.task_scheduler.schedule_task = AsyncMock()
        
        # カスタムタスクをスケジュール
        async def test_task():
            return "test_result"
        
        await mock_service.schedule_custom_task(
            name="test_task",
            func=test_task,
            interval_seconds=60,
            priority=TaskPriority.HIGH
        )
        
        # アサーション
        mock_service.task_scheduler.schedule_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, mock_service):
        """タスクキャンセルテスト"""
        # モックの設定
        mock_service.task_scheduler.cancel_task = AsyncMock()
        
        # タスクをキャンセル
        await mock_service.cancel_task("test_task")
        
        # アサーション
        mock_service.task_scheduler.cancel_task.assert_called_once_with("test_task")
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, mock_service):
        """タスクステータス取得テスト"""
        # モックの設定
        mock_status = {"status": "running", "last_run": datetime.now()}
        mock_service.task_scheduler.get_task_status = AsyncMock(return_value=mock_status)
        
        # タスクステータスを取得
        status = await mock_service.get_task_status("test_task")
        
        # アサーション
        assert status == mock_status
        mock_service.task_scheduler.get_task_status.assert_called_once_with("test_task")
    
    @pytest.mark.asyncio
    async def test_get_all_tasks_status(self, mock_service):
        """全タスクステータス取得テスト"""
        # モックの設定
        mock_status = {"task1": {"status": "running"}, "task2": {"status": "completed"}}
        mock_service.task_scheduler.get_all_tasks_status = AsyncMock(return_value=mock_status)
        
        # 全タスクステータスを取得
        status = await mock_service.get_all_tasks_status()
        
        # アサーション
        assert status == mock_status
        mock_service.task_scheduler.get_all_tasks_status.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_market_status(self, mock_service):
        """市場状況取得テスト"""
        # モックの設定
        mock_service.market_hours_manager.get_market_status = AsyncMock(return_value=MarketStatus.OPEN)
        mock_service.market_hours_manager.get_market_info = AsyncMock(return_value={"next_close": "16:00"})
        
        # 市場状況を取得
        status = await mock_service.get_market_status()
        
        # アサーション
        assert status["status"] == "open"
        assert "info" in status
        mock_service.market_hours_manager.get_market_status.assert_called_once()
        mock_service.market_hours_manager.get_market_info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_scheduler_stats(self, mock_service):
        """スケジューラー統計取得テスト"""
        # モックの設定
        mock_service._running = True
        mock_service._tasks = [AsyncMock(), AsyncMock()]
        mock_service.task_scheduler.get_stats = AsyncMock(return_value={"total_tasks": 10})
        mock_service.get_market_status = AsyncMock(return_value={"status": "open"})
        
        # スケジューラー統計を取得
        stats = await mock_service.get_scheduler_stats()
        
        # アサーション
        assert stats["service_running"] is True
        assert stats["active_tasks"] == 2
        assert "task_scheduler" in stats
        assert "market_status" in stats
        assert "settings" in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self, mock_service):
        """ヘルスチェックテスト"""
        # モックの設定
        mock_service._running = True
        mock_service._tasks = [AsyncMock(), AsyncMock()]
        mock_service.task_scheduler.health_check = AsyncMock(return_value={"status": "healthy"})
        mock_service.market_hours_manager.health_check = AsyncMock(return_value={"status": "healthy"})
        
        # ヘルスチェック
        health = await mock_service.health_check()
        
        # アサーション
        assert health["status"] == "healthy"
        assert health["service_running"] is True
        assert health["active_tasks"] == 2
        assert "scheduler" in health
        assert "market_hours" in health
    
    @pytest.mark.asyncio
    async def test_trigger_manual_task(self, mock_service):
        """手動タスク実行テスト"""
        # モックの設定
        mock_service.task_scheduler.trigger_task = AsyncMock(return_value="task_result")
        
        # 手動でタスクを実行
        result = await mock_service.trigger_manual_task("test_task")
        
        # アサーション
        assert result["success"] is True
        assert result["task_name"] == "test_task"
        assert result["result"] == "task_result"
        mock_service.task_scheduler.trigger_task.assert_called_once_with("test_task")
    
    @pytest.mark.asyncio
    async def test_trigger_manual_task_failure(self, mock_service):
        """手動タスク実行失敗テスト"""
        # モックの設定
        mock_service.task_scheduler.trigger_task = AsyncMock(side_effect=Exception("Task failed"))
        
        # 手動でタスクを実行
        result = await mock_service.trigger_manual_task("test_task")
        
        # アサーション
        assert result["success"] is False
        assert result["task_name"] == "test_task"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_task_history(self, mock_service):
        """タスク履歴取得テスト"""
        # モックの設定
        mock_history = [
            {"task_name": "test_task", "status": "completed", "timestamp": datetime.now()},
            {"task_name": "test_task", "status": "failed", "timestamp": datetime.now()}
        ]
        mock_service.task_scheduler.get_task_history = AsyncMock(return_value=mock_history)
        
        # タスク履歴を取得
        history = await mock_service.get_task_history("test_task", 10)
        
        # アサーション
        assert history == mock_history
        mock_service.task_scheduler.get_task_history.assert_called_once_with("test_task", 10)
    
    @pytest.mark.asyncio
    async def test_cleanup_old_tasks(self, mock_service):
        """古いタスククリーンアップテスト"""
        # モックの設定
        mock_service.task_scheduler.cleanup_old_tasks = AsyncMock()
        
        # 古いタスクをクリーンアップ
        await mock_service.cleanup_old_tasks()
        
        # アサーション
        mock_service.task_scheduler.cleanup_old_tasks.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
