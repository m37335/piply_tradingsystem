"""
ContinuousProcessingMonitorの統合テスト

テスト対象:
- 監視の開始・停止
- 処理サイクルの監視
- システム健全性チェック
- アラート機能
- 監視指標の管理
- アラート閾値の更新
"""

from datetime import datetime, timedelta

import pytest

from src.infrastructure.monitoring.continuous_processing_monitor import (
    ContinuousProcessingMonitor,
)


class TestContinuousProcessingMonitor:
    """ContinuousProcessingMonitorのテストクラス"""

    @pytest.fixture
    def monitor(self):
        """監視サービスインスタンス"""
        return ContinuousProcessingMonitor()

    @pytest.mark.asyncio
    async def test_monitor_initialization(self, monitor):
        """監視サービスの初期化テスト"""
        assert monitor.is_monitoring is False
        assert monitor.monitoring_interval == 60
        assert monitor.stats["total_cycles"] == 0
        assert monitor.stats["successful_cycles"] == 0
        assert monitor.stats["failed_cycles"] == 0
        assert monitor.stats["total_alerts"] == 0
        assert "max_processing_time" in monitor.alert_thresholds
        assert "min_success_rate" in monitor.alert_thresholds
        assert "max_error_count" in monitor.alert_thresholds

    @pytest.mark.asyncio
    async def test_start_monitoring_success(self, monitor):
        """監視開始の成功テスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 状態確認
        assert monitor.is_monitoring is True
        assert monitor.stats["monitoring_start_time"] is not None

    @pytest.mark.asyncio
    async def test_start_monitoring_already_running(self, monitor):
        """既に実行中の監視開始テスト"""
        # 最初の開始
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True

        # 2回目の開始（警告が発生するはず）
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True

    @pytest.mark.asyncio
    async def test_stop_monitoring_success(self, monitor):
        """監視停止の成功テスト"""
        # 開始
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True

        # 停止
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    @pytest.mark.asyncio
    async def test_stop_monitoring_already_stopped(self, monitor):
        """既に停止中の監視停止テスト"""
        # 停止（既に停止状態）
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False

    @pytest.mark.asyncio
    async def test_monitor_processing_cycle_success(self, monitor):
        """処理サイクル監視の成功テスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 正常なサイクルデータ
        cycle_data = {
            "processing_time": 2.5,
            "total_runs": 10,
            "successful_runs": 10,
            "data_volume": 15,
            "error_count": 0,
            "status": "success",
        }

        # サイクル監視実行
        await monitor.monitor_processing_cycle(cycle_data)

        # 統計情報の確認
        assert monitor.stats["total_cycles"] == 1
        assert monitor.stats["successful_cycles"] == 1
        assert monitor.stats["failed_cycles"] == 0
        assert len(monitor.metrics["processing_times"]) == 1
        assert monitor.metrics["processing_times"][0] == 2.5
        assert monitor.metrics["success_rates"]["overall"] == 1.0
        assert len(monitor.metrics["data_volumes"]) == 1

    @pytest.mark.asyncio
    async def test_monitor_processing_cycle_not_monitoring(self, monitor):
        """監視停止中のサイクル監視テスト"""
        # 監視を停止した状態
        assert monitor.is_monitoring is False

        # サイクルデータ
        cycle_data = {
            "processing_time": 2.5,
            "total_runs": 10,
            "successful_runs": 10,
            "data_volume": 15,
            "error_count": 0,
            "status": "success",
        }

        # サイクル監視実行（何も起こらないはず）
        await monitor.monitor_processing_cycle(cycle_data)

        # 統計情報が更新されていないことを確認
        assert monitor.stats["total_cycles"] == 0
        assert len(monitor.metrics["processing_times"]) == 0

    @pytest.mark.asyncio
    async def test_monitor_processing_cycle_performance_alert(self, monitor):
        """処理時間超過時のアラートテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 処理時間が閾値を超過するサイクルデータ
        cycle_data = {
            "processing_time": 400,  # 閾値300秒を超過
            "total_runs": 10,
            "successful_runs": 10,
            "data_volume": 15,
            "error_count": 0,
            "status": "success",
        }

        # サイクル監視実行
        await monitor.monitor_processing_cycle(cycle_data)

        # アラートが送信されたことを確認
        assert monitor.stats["total_alerts"] == 1
        assert len(monitor.metrics["alert_history"]) == 1
        assert monitor.metrics["alert_history"][0]["type"] == "PERFORMANCE"

    @pytest.mark.asyncio
    async def test_monitor_processing_cycle_reliability_alert(self, monitor):
        """成功率低下時のアラートテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 成功率が閾値を下回るサイクルデータ
        cycle_data = {
            "processing_time": 2.5,
            "total_runs": 10,
            "successful_runs": 8,  # 80%の成功率（閾値95%を下回る）
            "data_volume": 15,
            "error_count": 2,
            "status": "success",
        }

        # サイクル監視実行
        await monitor.monitor_processing_cycle(cycle_data)

        # アラートが送信されたことを確認
        assert monitor.stats["total_alerts"] == 1
        assert len(monitor.metrics["alert_history"]) == 1
        assert monitor.metrics["alert_history"][0]["type"] == "RELIABILITY"

    @pytest.mark.asyncio
    async def test_monitor_processing_cycle_data_volume_alert(self, monitor):
        """データ量不足時のアラートテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # データ量が閾値を下回るサイクルデータ
        cycle_data = {
            "processing_time": 2.5,
            "total_runs": 10,
            "successful_runs": 10,
            "data_volume": 5,  # 閾値10件を下回る
            "error_count": 0,
            "status": "success",
        }

        # サイクル監視実行
        await monitor.monitor_processing_cycle(cycle_data)

        # アラートが送信されたことを確認
        assert monitor.stats["total_alerts"] == 1
        assert len(monitor.metrics["alert_history"]) == 1
        assert monitor.metrics["alert_history"][0]["type"] == "DATA_VOLUME"

    @pytest.mark.asyncio
    async def test_monitor_processing_cycle_error_rate_alert(self, monitor):
        """エラー率超過時のアラートテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # エラー数が閾値を超過するサイクルデータ
        cycle_data = {
            "processing_time": 2.5,
            "total_runs": 10,
            "successful_runs": 10,
            "data_volume": 15,
            "error_count": 7,  # 閾値5回を超過
            "status": "success",
        }

        # サイクル監視実行
        await monitor.monitor_processing_cycle(cycle_data)

        # アラートが送信されたことを確認
        assert monitor.stats["total_alerts"] == 1
        assert len(monitor.metrics["alert_history"]) == 1
        assert monitor.metrics["alert_history"][0]["type"] == "ERROR_RATE"

    @pytest.mark.asyncio
    async def test_check_system_health_healthy(self, monitor):
        """健全性チェックの正常テスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 健全性チェック実行
        health = await monitor.check_system_health()

        # 健全性情報の確認
        assert health["service"] == "ContinuousProcessingMonitor"
        assert health["status"] == "healthy"
        assert health["is_monitoring"] is True
        assert "uptime" in health
        assert "stats" in health

    @pytest.mark.asyncio
    async def test_check_system_health_degraded_processing_time(self, monitor):
        """処理時間劣化時の健全性チェックテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 処理時間が閾値を超過するデータを追加
        monitor.metrics["processing_times"] = [400, 350, 380]  # 閾値300秒を超過

        # 健全性チェック実行
        health = await monitor.check_system_health()

        # 健全性情報の確認
        assert health["status"] == "degraded"
        assert "issues" in health
        assert "処理時間が閾値を超過" in health["issues"]

    @pytest.mark.asyncio
    async def test_check_system_health_degraded_success_rate(self, monitor):
        """成功率劣化時の健全性チェックテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 成功率が閾値を下回るデータを追加
        monitor.metrics["success_rates"]["overall"] = 0.90  # 閾値0.95を下回る

        # 健全性チェック実行
        health = await monitor.check_system_health()

        # 健全性情報の確認
        assert health["status"] == "degraded"
        assert "issues" in health
        assert "成功率が閾値を下回る" in health["issues"]

    @pytest.mark.asyncio
    async def test_check_system_health_degraded_error_rate(self, monitor):
        """エラー率劣化時の健全性チェックテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # エラー数が閾値を超過するデータを追加
        recent_time = datetime.now().isoformat()
        monitor.metrics["error_counts"][recent_time] = 7  # 閾値5回を超過

        # 健全性チェック実行
        health = await monitor.check_system_health()

        # 健全性情報の確認
        assert health["status"] == "degraded"
        assert "issues" in health
        assert "エラー数が閾値を超過" in health["issues"]

    @pytest.mark.asyncio
    async def test_check_system_health_degraded_data_volume(self, monitor):
        """データ量劣化時の健全性チェックテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # データ量が閾値を下回るデータを追加
        monitor.metrics["data_volumes"] = [3, 2, 1]  # 閾値10件を下回る

        # 健全性チェック実行
        health = await monitor.check_system_health()

        # 健全性情報の確認
        assert health["status"] == "degraded"
        assert "issues" in health
        assert "データ量が閾値を下回る" in health["issues"]

    @pytest.mark.asyncio
    async def test_send_alert_success(self, monitor):
        """アラート送信の成功テスト"""
        # アラート送信
        await monitor.send_alert("PERFORMANCE", "処理時間が閾値を超過")

        # アラート履歴の確認
        assert monitor.stats["total_alerts"] == 1
        assert len(monitor.metrics["alert_history"]) == 1
        assert monitor.metrics["alert_history"][0]["type"] == "PERFORMANCE"
        assert monitor.metrics["alert_history"][0]["message"] == "処理時間が閾値を超過"
        assert monitor.metrics["alert_history"][0]["severity"] == "warning"
        assert monitor.stats["last_alert"] is not None

    @pytest.mark.asyncio
    async def test_get_alert_severity(self, monitor):
        """アラート重要度の取得テスト"""
        # 各アラートタイプの重要度を確認
        assert monitor._get_alert_severity("PERFORMANCE") == "warning"
        assert monitor._get_alert_severity("RELIABILITY") == "critical"
        assert monitor._get_alert_severity("ERROR_RATE") == "critical"
        assert monitor._get_alert_severity("DATA_VOLUME") == "warning"
        assert monitor._get_alert_severity("SYSTEM_HEALTH") == "critical"
        assert monitor._get_alert_severity("UNKNOWN") == "info"

    @pytest.mark.asyncio
    async def test_get_monitoring_metrics(self, monitor):
        """監視指標の取得テスト"""
        # 監視指標取得
        metrics = await monitor.get_monitoring_metrics()

        # 指標の確認
        assert "metrics" in metrics
        assert "stats" in metrics
        assert "thresholds" in metrics
        assert "is_monitoring" in metrics
        assert "monitoring_interval" in metrics
        assert metrics["is_monitoring"] is False
        assert metrics["monitoring_interval"] == 60

    @pytest.mark.asyncio
    async def test_reset_metrics(self, monitor):
        """監視指標のリセットテスト"""
        # 監視を開始してデータを追加
        await monitor.start_monitoring()
        monitor.metrics["processing_times"] = [1.0, 2.0, 3.0]
        monitor.metrics["alert_history"] = [{"test": "data"}]
        monitor.stats["total_cycles"] = 5
        monitor.stats["total_alerts"] = 3

        # 指標リセット
        await monitor.reset_metrics()

        # 指標がリセットされたことを確認
        assert len(monitor.metrics["processing_times"]) == 0
        assert len(monitor.metrics["alert_history"]) == 0
        assert monitor.stats["total_cycles"] == 0
        assert monitor.stats["total_alerts"] == 0

    @pytest.mark.asyncio
    async def test_update_alert_thresholds(self, monitor):
        """アラート閾値の更新テスト"""
        # 閾値を更新

        # 閾値を更新
        await monitor.update_alert_thresholds(
            max_processing_time=600,
            min_success_rate=0.90,
        )

        # 閾値が更新されたことを確認
        assert monitor.alert_thresholds["max_processing_time"] == 600
        assert monitor.alert_thresholds["min_success_rate"] == 0.90

    @pytest.mark.asyncio
    async def test_get_alert_history(self, monitor):
        """アラート履歴の取得テスト"""
        # アラートを送信
        await monitor.send_alert("PERFORMANCE", "テストアラート1")
        await monitor.send_alert("RELIABILITY", "テストアラート2")

        # アラート履歴を取得
        history = await monitor.get_alert_history(hours=24)

        # 履歴の確認
        assert len(history) == 2
        assert history[0]["type"] == "PERFORMANCE"
        assert history[1]["type"] == "RELIABILITY"

    @pytest.mark.asyncio
    async def test_get_alert_history_with_time_filter(self, monitor):
        """時間フィルタ付きアラート履歴の取得テスト"""
        # 古いアラートを追加（手動でタイムスタンプを設定）
        old_alert = {
            "timestamp": datetime.now() - timedelta(hours=25),
            "type": "PERFORMANCE",
            "message": "古いアラート",
            "severity": "warning",
        }
        monitor.metrics["alert_history"].append(old_alert)

        # 新しいアラートを追加
        await monitor.send_alert("RELIABILITY", "新しいアラート")

        # 24時間以内のアラート履歴を取得
        history = await monitor.get_alert_history(hours=24)

        # 新しいアラートのみが含まれることを確認
        assert len(history) == 1
        assert history[0]["type"] == "RELIABILITY"

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_no_data(self, monitor):
        """データ不足時のパフォーマンス傾向分析テスト"""
        # パフォーマンス傾向分析実行
        analysis = await monitor.analyze_performance_trends()

        # 分析結果の確認
        assert "message" in analysis
        assert analysis["message"] == "分析データが不足しています"

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_stable(self, monitor):
        """安定傾向のパフォーマンス分析テスト"""
        # 安定した処理時間データを追加
        monitor.metrics["processing_times"] = [2.0, 2.1, 2.2, 2.0, 2.1]

        # パフォーマンス傾向分析実行
        analysis = await monitor.analyze_performance_trends()

        # 分析結果の確認
        assert "overall" in analysis
        assert "recent" in analysis
        assert "trend" in analysis
        assert analysis["trend"] == "stable"
        assert analysis["overall"]["total_samples"] == 5
        assert analysis["recent"]["samples"] == 5

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_degrading(self, monitor):
        """劣化傾向のパフォーマンス分析テスト"""
        # 劣化する処理時間データを追加
        monitor.metrics["processing_times"] = [
            1.0,
            1.1,
            1.2,
            1.3,
            1.4,
            1.5,
            1.6,
            1.7,
            1.8,
            1.9,
            8.0,
        ]

        # パフォーマンス傾向分析実行
        analysis = await monitor.analyze_performance_trends()

        # 分析結果の確認
        assert analysis["trend"] == "degrading"

    @pytest.mark.asyncio
    async def test_analyze_performance_trends_improving(self, monitor):
        """改善傾向のパフォーマンス分析テスト"""
        # 改善する処理時間データを追加
        monitor.metrics["processing_times"] = [
            8.0,
            7.5,
            7.0,
            6.5,
            6.0,
            5.5,
            5.0,
            4.5,
            4.0,
            3.5,
            1.0,
        ]

        # パフォーマンス傾向分析実行
        analysis = await monitor.analyze_performance_trends()

        # 分析結果の確認
        assert analysis["trend"] == "improving"

    @pytest.mark.asyncio
    async def test_multiple_alerts_in_cycle(self, monitor):
        """単一サイクルでの複数アラートテスト"""
        # 監視を開始
        await monitor.start_monitoring()

        # 複数の閾値を超過するサイクルデータ
        cycle_data = {
            "processing_time": 400,  # 処理時間超過
            "total_runs": 10,
            "successful_runs": 8,  # 成功率低下
            "data_volume": 5,  # データ量不足
            "error_count": 7,  # エラー数超過
            "status": "success",
        }

        # サイクル監視実行
        await monitor.monitor_processing_cycle(cycle_data)

        # 複数のアラートが送信されたことを確認
        assert monitor.stats["total_alerts"] == 4
        assert len(monitor.metrics["alert_history"]) == 4

        # アラートタイプの確認
        alert_types = [alert["type"] for alert in monitor.metrics["alert_history"]]
        assert "PERFORMANCE" in alert_types
        assert "RELIABILITY" in alert_types
        assert "DATA_VOLUME" in alert_types
        assert "ERROR_RATE" in alert_types
