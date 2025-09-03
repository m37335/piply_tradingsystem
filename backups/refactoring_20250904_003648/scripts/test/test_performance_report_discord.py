#!/usr/bin/env python3
"""
パフォーマンスレポートDiscord配信テスト
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
from src.infrastructure.performance.performance_monitor import (
    PerformanceMetrics,
    PerformanceMonitor,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PerformanceReportDiscordTester:
    """
    パフォーマンスレポートDiscord配信テストクラス
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
        print("Setting up performance report Discord test...")
        logger.info("Setting up performance report Discord test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # テスト用の設定を書き込み
        test_config = {
            "database": {
                "url": "sqlite+aiosqlite:///./test_performance_report.db",
            },
            "logging": {
                "level": "DEBUG",
                "file_path": "./logs/test_performance_report.log",
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
                    "webhook_url": "https://canary.discord.com/api/webhooks/1403643478361116672/nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ",
                    "enabled": True,
                },
                "discord_monitoring": {
                    "webhook_url": "https://canary.discord.com/api/webhooks/1404124259520876595/NV4t96suXeoQN6fvOnpKRNpDdBVBESRvChWLp3cZ3TMWuWwJvYX9VfmDWEBzbI9DoX_d",
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

        print("✅ Performance report Discord test setup completed")

    async def test_performance_report_generation(self):
        """
        パフォーマンスレポート生成テスト
        """
        print("\n=== Testing Performance Report Generation ===")

        # テスト用のメトリクスデータを追加
        for i in range(10):
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=30.0 + i * 2,
                memory_percent=50.0 + i * 3,
                memory_used_mb=1000.0 + i * 100,
                disk_usage_percent=60.0 + i * 2,
                network_io={"bytes_sent": 1000 + i * 100, "bytes_recv": 1000 + i * 100},
                process_count=100 + i,
                thread_count=50 + i,
                gc_stats={},
                database_connections=5 + i,
                active_tasks=10 + i,
                response_times={
                    "data_fetch": 0.5 + i * 0.1,
                    "pattern_detection": 1.0 + i * 0.2,
                },
                error_rate=1.0 + i * 0.5,
                throughput={
                    "data_fetch": 100 + i * 10,
                    "pattern_detection": 50 + i * 5,
                },
            )
            self.performance_monitor.metrics_history.append(metrics)

        # パフォーマンス統計を記録
        self.performance_monitor.record_operation_time("data_fetch", 0.8)
        self.performance_monitor.record_operation_time("data_fetch", 1.2)
        self.performance_monitor.record_operation_time("pattern_detection", 2.1)
        self.performance_monitor.record_operation_time("pattern_detection", 1.8)

        self.performance_monitor.record_error("data_fetch")
        self.performance_monitor.record_error("pattern_detection")

        self.performance_monitor.record_throughput("data_fetch")
        self.performance_monitor.record_throughput("data_fetch")
        self.performance_monitor.record_throughput("pattern_detection")

        # レポートを生成
        report = await self.performance_monitor.get_performance_report(hours=24)

        # レポートの内容を確認
        assert report["metrics_count"] >= 10
        assert "cpu" in report
        assert "memory" in report
        assert "disk" in report
        assert report["cpu"]["average"] > 0
        assert report["memory"]["average"] > 0
        assert report["disk"]["average"] > 0

        print(f"✅ Performance report generated: {report['metrics_count']} metrics")
        print(f"   CPU Average: {report['cpu']['average']:.1f}%")
        print(f"   Memory Average: {report['memory']['average']:.1f}%")
        print(f"   Disk Average: {report['disk']['average']:.1f}%")

        return report

    async def test_performance_report_discord_send(self):
        """
        パフォーマンスレポートDiscord送信テスト
        """
        print("\n=== Testing Performance Report Discord Send ===")

        # 1時間のレポートを送信
        print("📊 Sending 1-hour performance report to Discord...")
        await self.performance_monitor.send_performance_report_to_discord(hours=1)

        # 24時間のレポートを送信
        print("📊 Sending 24-hour performance report to Discord...")
        await self.performance_monitor.send_performance_report_to_discord(hours=24)

        print("✅ Performance report Discord send test completed")

    async def test_database_optimization_report(self):
        """
        データベース最適化レポートテスト
        """
        print("\n=== Testing Database Optimization Report ===")

        # データベースセッションを取得
        session = await get_async_session()
        try:
            # データベース最適化を実行
            results = await self.database_optimizer.optimize_database(session)

            print(f"✅ Database optimization completed: {len(results)} optimizations")

            # 最適化履歴を取得
            history = await self.database_optimizer.get_optimization_history(days=7)
            print(f"✅ Optimization history retrieved: {len(history)} records")

        finally:
            await session.close()

    async def test_performance_alerts_discord(self):
        """
        パフォーマンスアラートDiscord送信テスト
        """
        print("\n=== Testing Performance Alerts Discord Send ===")

        # 高負荷状態のメトリクスを作成
        high_load_metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=95.0,  # 危険レベル
            memory_percent=92.0,  # 危険レベル
            memory_used_mb=2000.0,
            disk_usage_percent=88.0,  # 警告レベル
            network_io={"bytes_sent": 5000, "bytes_recv": 5000},
            process_count=150,
            thread_count=80,
            gc_stats={},
            database_connections=15,
            active_tasks=25,
            response_times={"critical_operation": 12.0},  # 危険レベル
            error_rate=8.0,  # 警告レベル
            throughput={"critical_operation": 200},
        )

        # アラートをチェック（Discordに送信される）
        await self.performance_monitor._check_performance_alerts(high_load_metrics)

        print(
            f"✅ Performance alerts generated: {len(self.performance_monitor.alerts_history)} alerts"
        )

        # アラートの詳細を表示
        for alert in self.performance_monitor.alerts_history:
            print(f"   - {alert.alert_type}: {alert.message}")

    async def test_comprehensive_performance_report(self):
        """
        包括的パフォーマンスレポートテスト
        """
        print("\n=== Testing Comprehensive Performance Report ===")

        # より多様なメトリクスデータを追加
        for i in range(20):
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=20.0 + i * 3,
                memory_percent=40.0 + i * 2.5,
                memory_used_mb=800.0 + i * 80,
                disk_usage_percent=55.0 + i * 1.5,
                network_io={"bytes_sent": 800 + i * 80, "bytes_recv": 800 + i * 80},
                process_count=80 + i * 2,
                thread_count=40 + i,
                gc_stats={},
                database_connections=3 + i,
                active_tasks=8 + i,
                response_times={
                    "data_fetch": 0.3 + i * 0.05,
                    "pattern_detection": 0.8 + i * 0.1,
                    "notification_send": 0.2 + i * 0.02,
                },
                error_rate=0.5 + i * 0.3,
                throughput={
                    "data_fetch": 80 + i * 8,
                    "pattern_detection": 40 + i * 4,
                    "notification_send": 60 + i * 6,
                },
            )
            self.performance_monitor.metrics_history.append(metrics)

        # 包括的なレポートを生成
        comprehensive_report = await self.performance_monitor.get_performance_report(
            hours=24
        )

        print(f"✅ Comprehensive report generated:")
        print(f"   Metrics count: {comprehensive_report['metrics_count']}")
        print(f"   Alerts count: {comprehensive_report['alerts_count']}")
        print(
            f"   CPU - Avg: {comprehensive_report['cpu']['average']:.1f}%, Max: {comprehensive_report['cpu']['max']:.1f}%"
        )
        print(
            f"   Memory - Avg: {comprehensive_report['memory']['average']:.1f}%, Max: {comprehensive_report['memory']['max']:.1f}%"
        )
        print(
            f"   Disk - Avg: {comprehensive_report['disk']['average']:.1f}%, Max: {comprehensive_report['disk']['max']:.1f}%"
        )

        # Discordに包括的レポートを送信
        print("📊 Sending comprehensive performance report to Discord...")
        await self.performance_monitor.send_performance_report_to_discord(hours=24)

        print("✅ Comprehensive performance report test completed")

    async def run_all_tests(self):
        """
        全テストを実行
        """
        await self.setup()

        try:
            await self.test_performance_report_generation()
            await self.test_performance_report_discord_send()
            await self.test_database_optimization_report()
            await self.test_performance_alerts_discord()
            await self.test_comprehensive_performance_report()

            print("\n🎉 All performance report Discord tests passed!")

        except Exception as e:
            print(f"\n❌ Performance report Discord test failed: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        print("\nCleaning up performance report Discord test...")

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

        print("✅ Performance report Discord test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting performance report Discord test...")

    tester = PerformanceReportDiscordTester()
    await tester.run_all_tests()

    print("Performance report Discord test completed!")


if __name__ == "__main__":
    asyncio.run(main())
