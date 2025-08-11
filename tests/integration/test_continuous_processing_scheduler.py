"""
ContinuousProcessingSchedulerの統合テスト

テスト対象:
- スケジューラーの開始・停止
- 単一サイクルの実行
- エラーハンドリングとリトライ機能
- 統計情報の管理
- 健全性チェック
- 設定更新機能
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from src.infrastructure.schedulers.continuous_processing_scheduler import (
    ContinuousProcessingScheduler,
)
from src.infrastructure.database.models.price_data_model import PriceDataModel


class TestContinuousProcessingScheduler:
    """ContinuousProcessingSchedulerのテストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        return AsyncMock()

    @pytest.fixture
    def mock_initialization_manager(self):
        """モック初期化マネージャー"""
        mock = AsyncMock()
        mock.run_system_cycle.return_value = {
            "status": "initialized",
            "data_counts": {"5m": 100, "1h": 50, "4h": 30},
        }
        mock.health_check.return_value = {"status": "healthy"}
        return mock

    @pytest.fixture
    def mock_continuous_service(self):
        """モック継続処理サービス"""
        mock = AsyncMock()
        mock.process_5m_data.return_value = {
            "aggregation": {"1h": 1, "4h": 1},
            "indicators": {"rsi": 1, "macd": 1, "bb": 1},
            "patterns": {"breakout": 1},
            "processing_time": 2.5,
        }
        mock.health_check.return_value = {"status": "healthy"}
        return mock

    @pytest.fixture
    def mock_yahoo_client(self):
        """モックYahoo Financeクライアント"""
        mock = AsyncMock()
        mock.get_current_rate.return_value = {
            "open": 150.0,
            "high": 151.0,
            "low": 149.0,
            "close": 150.5,
            "volume": 1000000,
        }
        return mock

    @pytest.fixture
    def scheduler(
        self,
        mock_session,
        mock_initialization_manager,
        mock_continuous_service,
        mock_yahoo_client,
    ):
        """スケジューラーインスタンス"""
        with patch(
            "src.infrastructure.schedulers.continuous_processing_scheduler.SystemInitializationManager",
            return_value=mock_initialization_manager,
        ), patch(
            "src.infrastructure.schedulers.continuous_processing_scheduler.ContinuousProcessingService",
            return_value=mock_continuous_service,
        ), patch(
            "src.infrastructure.schedulers.continuous_processing_scheduler.YahooFinanceClient",
            return_value=mock_yahoo_client,
        ):
            scheduler = ContinuousProcessingScheduler(mock_session)
            return scheduler

    @pytest.mark.asyncio
    async def test_scheduler_initialization(self, scheduler):
        """スケジューラーの初期化テスト"""
        assert scheduler.running is False
        assert scheduler.task is None
        assert scheduler.interval_minutes == 5
        assert scheduler.max_retries == 3
        assert scheduler.retry_delay == 30
        assert scheduler.currency_pair == "USD/JPY"
        assert scheduler.stats["total_runs"] == 0
        assert scheduler.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_scheduler_start_success(self, scheduler):
        """スケジューラー開始の成功テスト"""
        # スケジューラーを開始
        await scheduler.start()

        # 状態確認
        assert scheduler.running is True
        assert scheduler.task is not None
        assert scheduler.stats["start_time"] is not None

        # 初期化チェックが呼ばれたことを確認
        scheduler.initialization_manager.run_system_cycle.assert_called_once()

        # クリーンアップ
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_start_already_running(self, scheduler):
        """既に実行中のスケジューラー開始テスト"""
        # 最初の開始
        await scheduler.start()
        assert scheduler.running is True

        # 2回目の開始（警告が発生するはず）
        await scheduler.start()
        assert scheduler.running is True

        # クリーンアップ
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_scheduler_stop_success(self, scheduler):
        """スケジューラー停止の成功テスト"""
        # 開始
        await scheduler.start()
        assert scheduler.running is True

        # 停止
        await scheduler.stop()
        assert scheduler.running is False
        assert scheduler.task is None

    @pytest.mark.asyncio
    async def test_scheduler_stop_already_stopped(self, scheduler):
        """既に停止中のスケジューラー停止テスト"""
        # 停止（既に停止状態）
        await scheduler.stop()
        assert scheduler.running is False

    @pytest.mark.asyncio
    async def test_run_single_cycle_success(self, scheduler):
        """単一サイクル実行の成功テスト"""
        # サイクル実行
        await scheduler.run_single_cycle()

        # 統計情報の確認
        assert scheduler.stats["total_runs"] == 1
        assert scheduler.stats["successful_runs"] == 1
        assert scheduler.stats["last_run"] is not None
        assert len(scheduler.stats["processing_times"]) == 1
        assert scheduler.consecutive_failures == 0

        # 依存サービスの呼び出し確認
        scheduler.yahoo_client.get_current_rate.assert_called_once_with("USD/JPY")
        scheduler.continuous_service.process_5m_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_single_cycle_data_fetch_failure(self, scheduler):
        """データ取得失敗時のサイクル実行テスト"""
        # データ取得を失敗させる
        scheduler.yahoo_client.get_current_rate.return_value = None

        # サイクル実行
        await scheduler.run_single_cycle()

        # 統計情報の確認
        assert scheduler.stats["total_runs"] == 1
        assert scheduler.stats["failed_runs"] == 1
        assert scheduler.stats["last_error"] is not None
        assert scheduler.consecutive_failures == 1
        assert len(scheduler.error_history) == 1

    @pytest.mark.asyncio
    async def test_run_single_cycle_processing_failure(self, scheduler):
        """処理失敗時のサイクル実行テスト"""
        # 継続処理を失敗させる
        scheduler.continuous_service.process_5m_data.side_effect = Exception("処理エラー")

        # サイクル実行
        await scheduler.run_single_cycle()

        # 統計情報の確認
        assert scheduler.stats["total_runs"] == 1
        assert scheduler.stats["failed_runs"] == 1
        assert scheduler.stats["last_error"] == "処理エラー"
        assert scheduler.consecutive_failures == 1
        assert len(scheduler.error_history) == 1

    @pytest.mark.asyncio
    async def test_fetch_5m_data_success(self, scheduler):
        """5分足データ取得の成功テスト"""
        # データ取得
        result = await scheduler._fetch_5m_data()

        # 結果確認
        assert result is not None
        assert isinstance(result, PriceDataModel)
        assert result.currency_pair == "USD/JPY"
        assert result.close_price == 150.5
        assert result.data_source == "Yahoo Finance Continuous Processing"

        # API呼び出し確認
        scheduler.yahoo_client.get_current_rate.assert_called_once_with("USD/JPY")

    @pytest.mark.asyncio
    async def test_fetch_5m_data_failure(self, scheduler):
        """5分足データ取得の失敗テスト"""
        # API呼び出しを失敗させる
        scheduler.yahoo_client.get_current_rate.return_value = None

        # データ取得
        result = await scheduler._fetch_5m_data()

        # 結果確認
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_and_process_data_success(self, scheduler):
        """データ取得・処理の成功テスト"""
        # 処理実行
        result = await scheduler._fetch_and_process_data()

        # 結果確認
        assert result is not None
        assert "aggregation" in result
        assert "indicators" in result
        assert "patterns" in result

        # 依存サービスの呼び出し確認
        scheduler.yahoo_client.get_current_rate.assert_called_once()
        scheduler.continuous_service.process_5m_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_and_process_data_fetch_failure(self, scheduler):
        """データ取得失敗時の処理テスト"""
        # データ取得を失敗させる
        scheduler.yahoo_client.get_current_rate.return_value = None

        # 処理実行（例外が発生するはず）
        with pytest.raises(Exception, match="5分足データ取得失敗"):
            await scheduler._fetch_and_process_data()

    @pytest.mark.asyncio
    async def test_perform_initialization_check_success(self, scheduler):
        """初期化チェックの成功テスト"""
        # 初期化チェック実行
        await scheduler._perform_initialization_check()

        # 依存サービスの呼び出し確認
        scheduler.initialization_manager.run_system_cycle.assert_called_once()

    @pytest.mark.asyncio
    async def test_perform_initialization_check_failure(self, scheduler):
        """初期化チェックの失敗テスト"""
        # 初期化チェックを失敗させる
        scheduler.initialization_manager.run_system_cycle.side_effect = Exception(
            "初期化エラー"
        )

        # 初期化チェック実行（例外が発生するはず）
        with pytest.raises(Exception, match="初期化エラー"):
            await scheduler._perform_initialization_check()

    @pytest.mark.asyncio
    async def test_handle_error_api_error(self, scheduler):
        """APIエラーのハンドリングテスト"""
        # APIエラーをシミュレート
        api_error = Exception("API制限エラー")

        # エラーハンドリング実行
        await scheduler._handle_error(api_error)

        # 待機時間が延長されることを確認（実際の待機はモックで確認できないが、ログで確認）

    @pytest.mark.asyncio
    async def test_handle_error_database_error(self, scheduler):
        """データベースエラーのハンドリングテスト"""
        # データベースエラーをシミュレート
        db_error = Exception("Database接続エラー")

        # エラーハンドリング実行
        await scheduler._handle_error(db_error)

    @pytest.mark.asyncio
    async def test_handle_error_general_error(self, scheduler):
        """一般的なエラーのハンドリングテスト"""
        # 一般的なエラーをシミュレート
        general_error = Exception("一般的なエラー")

        # エラーハンドリング実行
        await scheduler._handle_error(general_error)

    @pytest.mark.asyncio
    async def test_handle_critical_failure(self, scheduler):
        """重大障害の処理テスト"""
        # スケジューラーを開始
        await scheduler.start()
        assert scheduler.running is True

        # 重大障害処理実行
        await scheduler._handle_critical_failure()

        # スケジューラーが停止されることを確認
        assert scheduler.running is False

    @pytest.mark.asyncio
    async def test_get_scheduler_stats(self, scheduler):
        """スケジューラー統計の取得テスト"""
        # スケジューラーを開始
        await scheduler.start()

        # 統計情報取得
        stats = await scheduler.get_scheduler_stats()

        # 統計情報の確認
        assert "total_runs" in stats
        assert "successful_runs" in stats
        assert "failed_runs" in stats
        assert "running" in stats
        assert "success_rate" in stats
        assert "average_processing_time" in stats
        assert "consecutive_failures" in stats
        assert "error_count" in stats
        assert "interval_minutes" in stats
        assert stats["running"] is True

        # クリーンアップ
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_get_scheduler_stats_with_processing_history(self, scheduler):
        """処理履歴がある場合の統計情報取得テスト"""
        # スケジューラーを開始
        await scheduler.start()

        # いくつかのサイクルを実行
        await scheduler.run_single_cycle()
        await scheduler.run_single_cycle()

        # 統計情報取得
        stats = await scheduler.get_scheduler_stats()

        # 統計情報の確認
        assert stats["total_runs"] == 2
        assert stats["successful_runs"] == 2
        assert stats["success_rate"] == 100.0
        assert len(stats["processing_times"]) == 2

        # クリーンアップ
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_reset_stats(self, scheduler):
        """統計情報のリセットテスト"""
        # スケジューラーを開始
        await scheduler.start()

        # いくつかのサイクルを実行
        await scheduler.run_single_cycle()
        await scheduler.run_single_cycle()

        # 統計情報リセット
        await scheduler.reset_stats()

        # 統計情報の確認
        assert scheduler.stats["total_runs"] == 0
        assert scheduler.stats["successful_runs"] == 0
        assert scheduler.stats["failed_runs"] == 0
        assert len(scheduler.stats["processing_times"]) == 0
        assert len(scheduler.error_history) == 0
        assert scheduler.consecutive_failures == 0

        # クリーンアップ
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, scheduler):
        """健全性チェックの正常テスト"""
        # スケジューラーを開始
        await scheduler.start()

        # 健全性チェック実行
        health = await scheduler.health_check()

        # 健全性情報の確認
        assert health["service"] == "ContinuousProcessingScheduler"
        assert health["status"] == "healthy"
        assert health["running"] is True
        assert "uptime" in health
        assert "consecutive_failures" in health
        assert "initialization_manager" in health
        assert "continuous_service" in health

        # クリーンアップ
        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_health_check_stopped(self, scheduler):
        """停止状態の健全性チェックテスト"""
        # 健全性チェック実行（停止状態）
        health = await scheduler.health_check()

        # 健全性情報の確認
        assert health["status"] == "stopped"
        assert health["running"] is False

    @pytest.mark.asyncio
    async def test_health_check_critical(self, scheduler):
        """重大障害状態の健全性チェックテスト"""
        # 連続失敗回数を上限に設定
        scheduler.consecutive_failures = scheduler.max_consecutive_failures

        # 健全性チェック実行
        health = await scheduler.health_check()

        # 健全性情報の確認
        assert health["status"] == "critical"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, scheduler):
        """劣化状態の健全性チェックテスト"""
        # 連続失敗回数を設定
        scheduler.consecutive_failures = 2

        # 健全性チェック実行
        health = await scheduler.health_check()

        # 健全性情報の確認
        assert health["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_dependency_unhealthy(self, scheduler):
        """依存サービスが不健全な場合の健全性チェックテスト"""
        # 依存サービスの健全性チェックを失敗させる
        scheduler.initialization_manager.health_check.side_effect = Exception("初期化エラー")

        # 健全性チェック実行
        health = await scheduler.health_check()

        # 健全性情報の確認
        assert "initialization_manager" in health
        assert "unhealthy" in health["initialization_manager"]

    @pytest.mark.asyncio
    async def test_update_config_interval_minutes(self, scheduler):
        """実行間隔の設定更新テスト"""
        # 設定更新
        await scheduler.update_config(interval_minutes=10)

        # 設定の確認
        assert scheduler.interval_minutes == 10

    @pytest.mark.asyncio
    async def test_update_config_max_retries(self, scheduler):
        """最大リトライ回数の設定更新テスト"""
        # 設定更新
        await scheduler.update_config(max_retries=5)

        # 設定の確認
        assert scheduler.max_retries == 5

    @pytest.mark.asyncio
    async def test_update_config_retry_delay(self, scheduler):
        """リトライ待機時間の設定更新テスト"""
        # 設定更新
        await scheduler.update_config(retry_delay=60)

        # 設定の確認
        assert scheduler.retry_delay == 60

    @pytest.mark.asyncio
    async def test_update_config_multiple_parameters(self, scheduler):
        """複数パラメータの設定更新テスト"""
        # 設定更新
        await scheduler.update_config(
            interval_minutes=15,
            max_retries=7,
            retry_delay=45,
        )

        # 設定の確認
        assert scheduler.interval_minutes == 15
        assert scheduler.max_retries == 7
        assert scheduler.retry_delay == 45

    @pytest.mark.asyncio
    async def test_consecutive_failures_reset_on_success(self, scheduler):
        """成功時の連続失敗回数リセットテスト"""
        # 連続失敗回数を設定
        scheduler.consecutive_failures = 3

        # 成功するサイクルを実行
        await scheduler.run_single_cycle()

        # 連続失敗回数がリセットされることを確認
        assert scheduler.consecutive_failures == 0

    @pytest.mark.asyncio
    async def test_error_history_accumulation(self, scheduler):
        """エラー履歴の蓄積テスト"""
        # 継続処理を失敗させる
        scheduler.continuous_service.process_5m_data.side_effect = Exception("処理エラー")

        # サイクル実行
        await scheduler.run_single_cycle()

        # エラー履歴の確認
        assert len(scheduler.error_history) == 1
        error_record = scheduler.error_history[0]
        assert error_record["error"] == "処理エラー"
        assert error_record["cycle_number"] == 1
        assert "processing_time" in error_record

    @pytest.mark.asyncio
    async def test_scheduler_loop_cancellation(self, scheduler):
        """スケジューラーループのキャンセルテスト"""
        # スケジューラーを開始
        await scheduler.start()

        # 短時間待機
        await asyncio.sleep(0.1)

        # スケジューラーを停止
        await scheduler.stop()

        # 状態確認
        assert scheduler.running is False
        assert scheduler.task is None
