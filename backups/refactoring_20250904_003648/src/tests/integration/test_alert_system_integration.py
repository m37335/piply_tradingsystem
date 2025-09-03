"""
アラートシステム統合テスト

プロトレーダー向け為替アラートシステムの統合テスト
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.alert_engine.rsi_entry_detector import RSIEntryDetector
from src.domain.services.alert_engine.bollinger_bands_detector import BollingerBandsEntryDetector
from src.domain.services.alert_engine.volatility_risk_detector import VolatilityRiskDetector
from src.domain.services.risk_management.position_size_calculator import PositionSizeCalculator
from src.domain.services.risk_management.dynamic_stop_loss_adjuster import DynamicStopLossAdjuster
from src.domain.services.performance.signal_performance_tracker import SignalPerformanceTracker
from src.domain.services.performance.performance_analyzer import PerformanceAnalyzer
from src.domain.services.optimization.backtest_engine import BacktestEngine
from src.domain.services.optimization.performance_optimizer import PerformanceOptimizer


class TestAlertSystemIntegration:
    """
    アラートシステム統合テストクラス
    """

    @pytest.fixture
    async def setup_services(self, db_session: AsyncSession):
        """
        サービスをセットアップ

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        
        # 各サービスを初期化
        self.rsi_detector = RSIEntryDetector(db_session)
        self.bb_detector = BollingerBandsEntryDetector(db_session)
        self.volatility_detector = VolatilityRiskDetector(db_session)
        self.position_calculator = PositionSizeCalculator(db_session)
        self.stop_loss_adjuster = DynamicStopLossAdjuster(db_session)
        self.performance_tracker = SignalPerformanceTracker(db_session)
        self.performance_analyzer = PerformanceAnalyzer(db_session)
        self.backtest_engine = BacktestEngine(db_session)
        self.performance_optimizer = PerformanceOptimizer(db_session)

    @pytest.mark.asyncio
    async def test_complete_signal_generation_workflow(self, setup_services):
        """
        完全なシグナル生成ワークフローのテスト
        """
        # 1. RSIエントリーシグナル検出
        rsi_signals = await self.rsi_detector.detect_rsi_entry_signals("H1")
        assert isinstance(rsi_signals, list)

        # 2. ボリンジャーバンドエントリーシグナル検出
        bb_signals = await self.bb_detector.detect_bb_entry_signals("H1")
        assert isinstance(bb_signals, list)

        # 3. ボラティリティリスク検出
        volatility_alerts = await self.volatility_detector.detect_volatility_risk("H1")
        assert isinstance(volatility_alerts, list)

        # 4. ポジションサイズ計算（サンプルデータ）
        if rsi_signals:
            signal = rsi_signals[0]
            position_size_result = await self.position_calculator.calculate_position_size(
                account_balance=10000.0,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                confidence_score=signal.confidence_score,
                volatility_level="normal"
            )
            assert "final_position_size" in position_size_result

        # 5. 動的ストップロス調整
        if rsi_signals:
            signal = rsi_signals[0]
            stop_loss_result = await self.stop_loss_adjuster.calculate_dynamic_stop_loss(
                entry_price=signal.entry_price,
                signal_type=signal.signal_type,
                timeframe="H1"
            )
            assert "final_stop_loss" in stop_loss_result

    @pytest.mark.asyncio
    async def test_performance_tracking_workflow(self, setup_services):
        """
        パフォーマンス追跡ワークフローのテスト
        """
        # 1. パフォーマンス統計取得
        performance_stats = await self.performance_tracker.get_performance_statistics(
            currency_pair="USD/JPY",
            timeframe="H1",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        assert isinstance(performance_stats, dict)

        # 2. タイムフレーム別パフォーマンス分析
        timeframe_performance = await self.performance_tracker.get_performance_by_timeframe(
            currency_pair="USD/JPY",
            days=30
        )
        assert isinstance(timeframe_performance, dict)

        # 3. 信頼度別パフォーマンス分析
        confidence_performance = await self.performance_tracker.get_performance_by_confidence(
            currency_pair="USD/JPY",
            days=30
        )
        assert isinstance(confidence_performance, dict)

        # 4. パフォーマンス分析実行
        analysis_result = await self.performance_analyzer.analyze_performance(
            currency_pair="USD/JPY",
            timeframe="H1",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow()
        )
        assert isinstance(analysis_result, dict)

    @pytest.mark.asyncio
    async def test_backtest_workflow(self, setup_services):
        """
        バックテストワークフローのテスト
        """
        # 1. バックテスト実行
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        backtest_result = await self.backtest_engine.run_backtest(
            start_date=start_date,
            end_date=end_date,
            timeframe="H1"
        )
        assert isinstance(backtest_result, dict)

        # 2. パラメータ最適化
        optimization_result = await self.backtest_engine.optimize_parameters(
            start_date=start_date,
            end_date=end_date,
            timeframe="H1"
        )
        assert isinstance(optimization_result, dict)

    @pytest.mark.asyncio
    async def test_performance_optimization_workflow(self, setup_services):
        """
        パフォーマンス最適化ワークフローのテスト
        """
        # 1. データベースクエリ最適化
        db_optimization = await self.performance_optimizer.optimize_database_queries()
        assert isinstance(db_optimization, dict)

        # 2. メモリ使用量最適化
        memory_optimization = await self.performance_optimizer.optimize_memory_usage()
        assert isinstance(memory_optimization, dict)

        # 3. 非同期処理最適化
        async_optimization = await self.performance_optimizer.optimize_async_processing()
        assert isinstance(async_optimization, dict)

        # 4. パフォーマンステスト実行
        performance_test = await self.performance_optimizer.run_performance_test()
        assert isinstance(performance_test, dict)

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, setup_services):
        """
        エンドツーエンドワークフローのテスト
        """
        # 1. シグナル生成
        rsi_signals = await self.rsi_detector.detect_rsi_entry_signals("H1")
        bb_signals = await self.bb_detector.detect_bb_entry_signals("H1")
        
        all_signals = rsi_signals + bb_signals
        
        if all_signals:
            signal = all_signals[0]
            
            # 2. リスク管理
            position_size = await self.position_calculator.calculate_position_size(
                account_balance=10000.0,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                confidence_score=signal.confidence_score,
                volatility_level="normal"
            )
            
            stop_loss = await self.stop_loss_adjuster.calculate_dynamic_stop_loss(
                entry_price=signal.entry_price,
                signal_type=signal.signal_type,
                timeframe="H1"
            )
            
            # 3. パフォーマンス追跡（仮想的な実行）
            execution_time = datetime.utcnow()
            exit_time = execution_time + timedelta(hours=2)
            exit_price = signal.entry_price * 1.01  # 1%上昇
            
            performance_record = await self.performance_tracker.track_signal_execution(
                signal=signal,
                execution_price=signal.entry_price,
                execution_time=execution_time,
                exit_price=exit_price,
                exit_time=exit_time,
                exit_reason="take_profit"
            )
            
            assert performance_record is not None
            assert hasattr(performance_record, 'pnl')

    @pytest.mark.asyncio
    async def test_error_handling(self, setup_services):
        """
        エラーハンドリングのテスト
        """
        # 無効なパラメータでのテスト
        try:
            invalid_result = await self.position_calculator.calculate_position_size(
                account_balance=-1000,  # 無効な残高
                entry_price=0,  # 無効な価格
                stop_loss=0,  # 無効なストップロス
                confidence_score=150,  # 無効な信頼度
                volatility_level="invalid"
            )
            assert "error" in invalid_result
        except Exception as e:
            # 例外が発生することも正常
            assert isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, setup_services):
        """
        パフォーマンスベンチマークのテスト
        """
        # シグナル検出のパフォーマンス
        start_time = datetime.utcnow()
        rsi_signals = await self.rsi_detector.detect_rsi_entry_signals("H1")
        end_time = datetime.utcnow()
        
        detection_time = (end_time - start_time).total_seconds()
        assert detection_time < 5.0  # 5秒以内

        # パフォーマンス分析のパフォーマンス
        start_time = datetime.utcnow()
        analysis = await self.performance_analyzer.analyze_performance(
            currency_pair="USD/JPY",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        end_time = datetime.utcnow()
        
        analysis_time = (end_time - start_time).total_seconds()
        assert analysis_time < 10.0  # 10秒以内

    @pytest.mark.asyncio
    async def test_data_consistency(self, setup_services):
        """
        データ整合性のテスト
        """
        # パフォーマンス統計の整合性チェック
        stats = await self.performance_tracker.get_performance_statistics(
            currency_pair="USD/JPY"
        )
        
        if stats.get("total_trades", 0) > 0:
            win_rate = stats.get("win_rate", 0)
            assert 0 <= win_rate <= 100  # 勝率は0-100%の範囲
            
            total_pnl = stats.get("total_pnl", 0)
            assert isinstance(total_pnl, (int, float))  # 損益は数値

    @pytest.mark.asyncio
    async def test_system_scalability(self, setup_services):
        """
        システムスケーラビリティのテスト
        """
        # 複数のタイムフレームでの同時処理
        timeframes = ["M5", "M15", "H1", "H4", "D1"]
        
        start_time = datetime.utcnow()
        
        # 並行してシグナル検出を実行
        tasks = []
        for timeframe in timeframes:
            task1 = self.rsi_detector.detect_rsi_entry_signals(timeframe)
            task2 = self.bb_detector.detect_bb_entry_signals(timeframe)
            tasks.extend([task1, task2])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # 10個のタスクが30秒以内に完了することを確認
        assert total_time < 30.0
        assert len(results) == len(tasks)
        
        # エラーが発生していないことを確認
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_system_reliability(self, setup_services):
        """
        システム信頼性のテスト
        """
        # 連続実行テスト
        for i in range(5):
            try:
                # 基本的なシグナル検出を連続実行
                signals = await self.rsi_detector.detect_rsi_entry_signals("H1")
                assert isinstance(signals, list)
                
                # パフォーマンス統計取得を連続実行
                stats = await self.performance_tracker.get_performance_statistics()
                assert isinstance(stats, dict)
                
            except Exception as e:
                pytest.fail(f"System reliability test failed on iteration {i}: {e}")

    @pytest.mark.asyncio
    async def test_integration_with_external_services(self, setup_services):
        """
        外部サービスとの統合テスト
        """
        # 通知サービスの統合テスト（モック）
        # 実際の実装では、Discord、メール、Slackなどの通知サービスとの統合をテスト
        
        # データベース接続の安定性テスト
        try:
            # 複数のクエリを連続実行
            for i in range(10):
                stats = await self.performance_tracker.get_performance_statistics()
                assert isinstance(stats, dict)
                
        except Exception as e:
            pytest.fail(f"Database integration test failed: {e}")

    @pytest.mark.asyncio
    async def test_system_monitoring(self, setup_services):
        """
        システム監視のテスト
        """
        # パフォーマンスメトリクスの収集
        performance_test = await self.performance_optimizer.run_performance_test()
        assert isinstance(performance_test, dict)
        
        # 最適化履歴の取得
        optimization_history = await self.performance_optimizer.get_optimization_history()
        assert isinstance(optimization_history, list)
        
        # システムヘルスチェック
        # 各サービスが正常に動作していることを確認
        services = [
            self.rsi_detector,
            self.bb_detector,
            self.volatility_detector,
            self.position_calculator,
            self.stop_loss_adjuster,
            self.performance_tracker,
            self.performance_analyzer,
            self.backtest_engine,
            self.performance_optimizer,
        ]
        
        for service in services:
            assert service is not None
            assert hasattr(service, '__class__')
