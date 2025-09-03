#!/usr/bin/env python3
"""
パフォーマンス最適化システムテスト
"""

import asyncio
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.monitoring.log_manager import LogManager
from src.infrastructure.performance.database_optimizer import DatabaseOptimizer
from src.infrastructure.performance.performance_monitor import PerformanceMonitor
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PerformanceOptimizationTester:
    """
    パフォーマンス最適化システムテストクラス
    """

    def __init__(self):
        self.config_manager = None
        self.log_manager = None
        self.performance_monitor = None
        self.database_optimizer = None
        self.temp_config_file = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up performance optimization test...")
        logger.info("Setting up performance optimization test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # テスト用の設定を書き込み
        test_config = {
            "database": {
                "url": "sqlite+aiosqlite:///./test_performance_optimization.db",
            },
            "logging": {
                "level": "DEBUG",
                "file_path": "./logs/test_performance_optimization.log",
                "max_file_size": 1048576,
                "backup_count": 3,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "performance": {
                "monitoring_interval": 10,
                "alert_cooldown": 60,
                "cpu_warning": 70.0,
                "cpu_critical": 90.0,
                "memory_warning": 80.0,
                "memory_critical": 95.0,
                "disk_warning": 85.0,
                "disk_critical": 95.0,
                "response_time_warning": 5.0,
                "response_time_critical": 10.0,
                "error_rate_warning": 5.0,
                "error_rate_critical": 10.0,
                "table_size_threshold": 1000,
                "fragmentation_threshold": 30.0,
                "cache_hit_threshold": 80.0,
                "slow_query_threshold": 5.0,
            },
            "notifications": {
                "discord": {
                    "webhook_url": "https://discord.com/api/webhooks/test",
                    "enabled": True,
                },
                "discord_monitoring": {
                    "webhook_url": "https://discord.com/api/webhooks/test",
                    "enabled": True,
                },
            },
        }

        import json

        with open(self.temp_config_file.name, "w") as f:
            json.dump(test_config, f, indent=2)

        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager(self.temp_config_file.name)

        # ログ管理を初期化
        self.log_manager = LogManager(self.config_manager)

        # パフォーマンス監視を初期化
        self.performance_monitor = PerformanceMonitor(
            self.config_manager, self.log_manager
        )

        # データベース最適化を初期化
        self.database_optimizer = DatabaseOptimizer(
            self.config_manager, self.log_manager
        )

        print("✅ Performance optimization test setup completed")

    async def test_performance_monitor_initialization(self):
        """
        パフォーマンス監視の初期化テスト
        """
        print("\n=== Testing Performance Monitor Initialization ===")

        # 基本設定の確認
        assert self.performance_monitor.monitoring_interval == 10
        assert self.performance_monitor.alert_cooldown == 60
        assert len(self.performance_monitor.performance_thresholds) == 5

        # 閾値の確認
        cpu_thresholds = self.performance_monitor.performance_thresholds["cpu"]
        assert cpu_thresholds["warning"] == 70.0
        assert cpu_thresholds["critical"] == 90.0

        print("✅ Performance monitor initialization test passed")

    async def test_performance_metrics_collection(self):
        """
        パフォーマンスメトリクス収集テスト
        """
        print("\n=== Testing Performance Metrics Collection ===")

        # メトリクスを収集
        metrics = await self.performance_monitor._collect_performance_metrics()

        # 基本メトリクスの確認
        assert metrics.cpu_percent >= 0.0
        assert metrics.memory_percent >= 0.0
        assert metrics.disk_usage_percent >= 0.0
        assert metrics.process_count > 0
        assert metrics.thread_count > 0
        assert metrics.active_tasks >= 0
        assert metrics.error_rate >= 0.0

        print("✅ Performance metrics collection test passed")

    async def test_performance_alerts(self):
        """
        パフォーマンスアラートテスト
        """
        print("\n=== Testing Performance Alerts ===")

        # テスト用のメトリクスを作成（高負荷状態をシミュレート）
        from src.infrastructure.performance.performance_monitor import (
            PerformanceMetrics,
        )

        high_load_metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=95.0,  # 危険レベル
            memory_percent=90.0,  # 危険レベル
            memory_used_mb=1000.0,
            disk_usage_percent=90.0,  # 危険レベル
            network_io={"bytes_sent": 1000, "bytes_recv": 1000},
            process_count=100,
            thread_count=50,
            gc_stats={},
            database_connections=10,
            active_tasks=20,
            response_times={"test_operation": 15.0},  # 危険レベル
            error_rate=15.0,  # 危険レベル
            throughput={"test_operation": 100},
        )

        # アラートをチェック
        await self.performance_monitor._check_performance_alerts(high_load_metrics)

        # アラートが生成されたことを確認
        assert len(self.performance_monitor.alerts_history) > 0

        print("✅ Performance alerts test passed")

    async def test_performance_statistics(self):
        """
        パフォーマンス統計テスト
        """
        print("\n=== Testing Performance Statistics ===")

        # 操作時間を記録
        self.performance_monitor.record_operation_time("test_operation", 1.5)
        self.performance_monitor.record_operation_time("test_operation", 2.0)
        self.performance_monitor.record_operation_time("test_operation", 1.0)

        # エラーを記録
        self.performance_monitor.record_error("test_operation")
        self.performance_monitor.record_error("test_operation")

        # スループットを記録
        self.performance_monitor.record_throughput("test_operation")
        self.performance_monitor.record_throughput("test_operation")
        self.performance_monitor.record_throughput("test_operation")

        # 統計を確認
        response_times = self.performance_monitor._calculate_average_response_times()
        error_rate = self.performance_monitor._calculate_error_rate()
        throughput = self.performance_monitor._calculate_throughput()

        assert "test_operation" in response_times
        assert response_times["test_operation"] == 1.5  # (1.5 + 2.0 + 1.0) / 3
        assert error_rate == (2 / 3) * 100  # 2エラー / 3操作 * 100
        assert throughput["test_operation"] == 3

        print("✅ Performance statistics test passed")

    async def test_performance_report(self):
        """
        パフォーマンスレポートテスト
        """
        print("\n=== Testing Performance Report ===")

        # メトリクス履歴にデータを追加
        from src.infrastructure.performance.performance_monitor import (
            PerformanceMetrics,
        )

        for i in range(5):
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=50.0 + i,
                memory_percent=60.0 + i,
                memory_used_mb=1000.0 + i * 100,
                disk_usage_percent=70.0 + i,
                network_io={"bytes_sent": 1000 + i, "bytes_recv": 1000 + i},
                process_count=100 + i,
                thread_count=50 + i,
                gc_stats={},
                database_connections=10 + i,
                active_tasks=20 + i,
                response_times={"test_operation": 1.0 + i * 0.1},
                error_rate=2.0 + i,
                throughput={"test_operation": 100 + i},
            )
            self.performance_monitor.metrics_history.append(metrics)

        # レポートを取得
        report = await self.performance_monitor.get_performance_report(hours=24)

        # レポートの内容を確認
        assert report["metrics_count"] >= 5
        assert "cpu" in report
        assert "memory" in report
        assert "disk" in report
        assert report["cpu"]["average"] > 0
        assert report["memory"]["average"] > 0
        assert report["disk"]["average"] > 0

        print("✅ Performance report test passed")

    async def test_database_optimizer_initialization(self):
        """
        データベース最適化の初期化テスト
        """
        print("\n=== Testing Database Optimizer Initialization ===")

        # 基本設定の確認
        assert len(self.database_optimizer.optimization_thresholds) == 4

        # 閾値の確認
        assert (
            self.database_optimizer.optimization_thresholds["table_size_threshold"]
            == 1000
        )
        assert (
            self.database_optimizer.optimization_thresholds["fragmentation_threshold"]
            == 30.0
        )

        print("✅ Database optimizer initialization test passed")

    async def test_database_performance_analysis(self):
        """
        データベースパフォーマンス分析テスト
        """
        print("\n=== Testing Database Performance Analysis ===")

        # データベースセッションを取得
        session = await get_async_session()
        try:
            # データベースパフォーマンスを分析
            metrics = await self.database_optimizer.analyze_database_performance(
                session
            )

            # 基本メトリクスの確認
            assert metrics.timestamp is not None
            assert isinstance(metrics.table_sizes, dict)
            assert isinstance(metrics.index_sizes, dict)
            assert isinstance(metrics.query_performance, dict)
            assert metrics.connection_count >= 0
            assert metrics.active_queries >= 0
            assert metrics.slow_queries >= 0
            assert metrics.cache_hit_ratio >= 0.0
            assert metrics.fragmentation_ratio >= 0.0

            print("✅ Database performance analysis test passed")
        finally:
            await session.close()

    async def test_database_optimization(self):
        """
        データベース最適化テスト
        """
        print("\n=== Testing Database Optimization ===")

        # データベースセッションを取得
        session = await get_async_session()
        try:
            # データベース最適化を実行
            results = await self.database_optimizer.optimize_database(session)

            # 最適化結果を確認
            assert isinstance(results, list)

            # 最適化履歴に追加されたことを確認
            assert len(self.database_optimizer.optimization_history) >= len(results)

            print("✅ Database optimization test passed")
        finally:
            await session.close()

    async def test_optimization_history(self):
        """
        最適化履歴テスト
        """
        print("\n=== Testing Optimization History ===")

        # 最適化履歴を取得
        history = await self.database_optimizer.get_optimization_history(days=7)

        # 履歴の形式を確認
        assert isinstance(history, list)

        print("✅ Optimization history test passed")

    async def test_performance_monitoring_integration(self):
        """
        パフォーマンス監視統合テスト
        """
        print("\n=== Testing Performance Monitoring Integration ===")

        # パフォーマンス監視を開始
        await self.performance_monitor.start_monitoring()

        # 短時間監視を実行
        await asyncio.sleep(5)

        # パフォーマンス監視を停止
        await self.performance_monitor.stop_monitoring()

        # メトリクスが収集されたことを確認
        assert len(self.performance_monitor.metrics_history) > 0

        print("✅ Performance monitoring integration test passed")

    async def test_discord_notification(self):
        """
        Discord通知テスト
        """
        print("\n=== Testing Discord Notification ===")

        # パフォーマンスレポートをDiscordに送信
        await self.performance_monitor.send_performance_report_to_discord(hours=1)

        print("✅ Discord notification test passed")

    async def run_all_tests(self):
        """
        全テストを実行
        """
        await self.setup()

        try:
            await self.test_performance_monitor_initialization()
            await self.test_performance_metrics_collection()
            await self.test_performance_alerts()
            await self.test_performance_statistics()
            await self.test_performance_report()
            await self.test_database_optimizer_initialization()
            await self.test_database_performance_analysis()
            await self.test_database_optimization()
            await self.test_optimization_history()
            await self.test_performance_monitoring_integration()
            await self.test_discord_notification()

            print("\n🎉 All performance optimization tests passed!")

        except Exception as e:
            print(f"\n❌ Performance optimization test failed: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        print("\nCleaning up performance optimization test...")

        # パフォーマンス監視を停止
        if self.performance_monitor:
            await self.performance_monitor.stop_monitoring()
            self.performance_monitor.clear_history()

        # 最適化履歴をクリア
        if self.database_optimizer:
            self.database_optimizer.clear_optimization_history()

        # 一時ファイルを削除
        if self.temp_config_file and Path(self.temp_config_file.name).exists():
            Path(self.temp_config_file.name).unlink()

        print("✅ Performance optimization test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting performance optimization system test...")

    tester = PerformanceOptimizationTester()
    await tester.run_all_tests()

    print("Performance optimization system test completed!")


if __name__ == "__main__":
    asyncio.run(main())
