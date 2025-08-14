#!/usr/bin/env python3
"""
パフォーマンス監視システムテスト
"""

import asyncio
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, "/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.monitoring.performance_monitor import PerformanceMonitor


class PerformanceMonitorTester:
    """パフォーマンス監視システムテスト"""

    def __init__(self):
        self.session = None
        self.monitor = None

    async def initialize(self):
        """初期化"""
        print("🔧 パフォーマンス監視システムテストを初期化中...")

        # データベースセッションを取得
        self.session = await get_async_session()
        self.monitor = PerformanceMonitor(self.session)

        print("✅ 初期化完了")

    async def test_system_metrics(self):
        """システムメトリクス収集テスト"""
        print("\n📊 システムメトリクス収集テスト...")

        try:
            metrics = await self.monitor.collect_system_metrics()

            print("✅ システムメトリクス収集成功")
            print(f"   CPU使用率: {metrics.get('cpu_percent', 'N/A'):.1f}%")
            print(f"   メモリ使用率: {metrics.get('memory_percent', 'N/A'):.1f}%")
            print(f"   メモリ使用量: {metrics.get('memory_mb', 'N/A'):.1f} MB")
            print(f"   ディスク使用率: {metrics.get('disk_usage_percent', 'N/A'):.1f}%")
            print(
                f"   データベースサイズ: {metrics.get('database_size_mb', 'N/A'):.1f} MB"
            )
            print(f"   アクティブ接続数: {metrics.get('active_connections', 'N/A')}")

            return True
        except Exception as e:
            print(f"❌ システムメトリクス収集エラー: {e}")
            return False

    async def test_query_performance(self):
        """クエリパフォーマンス測定テスト"""
        print("\n⚡ クエリパフォーマンス測定テスト...")

        try:
            # サンプルクエリのパフォーマンスを測定
            result = await self.monitor.measure_query_performance(
                self.monitor._sample_query
            )

            print("✅ クエリパフォーマンス測定成功")
            print(f"   実行時間: {result.get('execution_time_ms', 'N/A'):.2f} ms")
            print(f"   成功: {result.get('success', False)}")

            if result.get("result"):
                print(f"   結果: {result['result']}")

            return True
        except Exception as e:
            print(f"❌ クエリパフォーマンス測定エラー: {e}")
            return False

    async def test_data_processing_performance(self):
        """データ処理パフォーマンス測定テスト"""
        print("\n🔄 データ処理パフォーマンス測定テスト...")

        try:
            # サンプルデータ処理のパフォーマンスを測定
            result = await self.monitor.measure_data_processing_performance(
                self.monitor._sample_data_processing
            )

            print("✅ データ処理パフォーマンス測定成功")
            print(f"   処理時間: {result.get('processing_time_ms', 'N/A'):.2f} ms")
            print(f"   成功: {result.get('success', False)}")

            if result.get("result"):
                print(f"   結果: {result['result']}")

            return True
        except Exception as e:
            print(f"❌ データ処理パフォーマンス測定エラー: {e}")
            return False

    async def test_comprehensive_metrics(self):
        """包括的メトリクス収集テスト"""
        print("\n📈 包括的メトリクス収集テスト...")

        try:
            # 複数回メトリクスを収集
            for i in range(3):
                metrics = await self.monitor.collect_comprehensive_metrics()
                print(
                    f"   収集 {i+1}: CPU={metrics.cpu_percent:.1f}%, "
                    f"メモリ={metrics.memory_percent:.1f}%, "
                    f"クエリ時間={metrics.query_execution_time_ms:.2f}ms"
                )
                await asyncio.sleep(1)

            print("✅ 包括的メトリクス収集成功")
            return True
        except Exception as e:
            print(f"❌ 包括的メトリクス収集エラー: {e}")
            return False

    async def test_performance_summary(self):
        """パフォーマンスサマリーテスト"""
        print("\n📋 パフォーマンスサマリーテスト...")

        try:
            summary = self.monitor.get_performance_summary(hours=1)

            if "error" in summary:
                print(f"⚠️  サマリーエラー: {summary['error']}")
                return False

            print("✅ パフォーマンスサマリー取得成功")
            print(f"   期間: {summary.get('period_hours', 'N/A')}時間")
            print(f"   測定回数: {summary.get('total_measurements', 'N/A')}")
            print(f"   平均CPU使用率: {summary.get('avg_cpu_percent', 'N/A'):.1f}%")
            print(
                f"   平均メモリ使用率: {summary.get('avg_memory_percent', 'N/A'):.1f}%"
            )
            print(
                f"   平均クエリ時間: {summary.get('avg_query_time_ms', 'N/A'):.2f} ms"
            )
            print(
                f"   平均処理時間: {summary.get('avg_processing_time_ms', 'N/A'):.2f} ms"
            )
            print(f"   総エラー数: {summary.get('total_errors', 'N/A')}")
            print(f"   総成功数: {summary.get('total_successes', 'N/A')}")
            print(f"   稼働時間: {summary.get('uptime_hours', 'N/A'):.1f}時間")

            return True
        except Exception as e:
            print(f"❌ パフォーマンスサマリーエラー: {e}")
            return False

    async def test_alerts(self):
        """アラート機能テスト"""
        print("\n🚨 アラート機能テスト...")

        try:
            alerts = self.monitor.get_alerts()

            print("✅ アラート機能テスト成功")
            print(f"   アラート数: {len(alerts)}")

            for alert in alerts:
                print(f"   - {alert['severity'].upper()}: {alert['message']}")

            return True
        except Exception as e:
            print(f"❌ アラート機能テストエラー: {e}")
            return False

    async def run_all_tests(self):
        """全テストを実行"""
        print("🚀 パフォーマンス監視システムテスト開始")
        print("=" * 60)

        await self.initialize()

        tests = [
            ("システムメトリクス収集", self.test_system_metrics),
            ("クエリパフォーマンス測定", self.test_query_performance),
            ("データ処理パフォーマンス測定", self.test_data_processing_performance),
            ("包括的メトリクス収集", self.test_comprehensive_metrics),
            ("パフォーマンスサマリー", self.test_performance_summary),
            ("アラート機能", self.test_alerts),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}で予期しないエラー: {e}")
                results.append((test_name, False))

        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)

        passed = 0
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1

        print(f"\n結果: {passed}/{total} テスト成功")

        if passed == total:
            print("🎉 全テスト成功！パフォーマンス監視システムは正常に動作しています。")
        else:
            print("⚠️  一部のテストが失敗しました。詳細を確認してください。")

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()
        print("\n🧹 クリーンアップ完了")


async def main():
    """メイン関数"""
    tester = PerformanceMonitorTester()
    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
