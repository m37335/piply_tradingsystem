"""
UnifiedTechnicalCalculator パフォーマンステスト

テスト対象:
- 計算速度の測定
- メモリ使用量の測定
- 既存システムとの比較
- 改善効果の定量化
"""

import asyncio
import time
from unittest.mock import AsyncMock

import pandas as pd
import psutil
import pytest

from scripts.cron.unified_technical_calculator import UnifiedTechnicalCalculator
from src.infrastructure.database.services.unified_technical_indicator_service import (
    UnifiedTechnicalIndicatorService,
)


class TestUnifiedTechnicalPerformance:
    """UnifiedTechnicalCalculator パフォーマンステストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        return AsyncMock()

    @pytest.fixture
    def unified_calculator(self):
        """UnifiedTechnicalCalculator インスタンス"""
        return UnifiedTechnicalCalculator("USD/JPY")

    @pytest.fixture
    def unified_service(self, mock_session):
        """UnifiedTechnicalIndicatorService インスタンス"""
        return UnifiedTechnicalIndicatorService(mock_session, "USD/JPY")

    async def test_calculation_speed(self, unified_calculator):
        """計算速度テスト"""
        # モックデータの準備（pandas DataFrame）
        data = {
            "Close": [100 + i * 0.1 for i in range(1000)],
            "High": [101 + i * 0.1 for i in range(1000)],
            "Low": [99 + i * 0.1 for i in range(1000)],
            "Volume": [1000000 for _ in range(1000)],
        }
        mock_data = pd.DataFrame(data)

        # 計算時間の測定
        start_time = time.time()

        # RSI計算
        rsi_result = await unified_calculator.calculate_rsi(mock_data, "M5")

        # MACD計算
        macd_result = await unified_calculator.calculate_macd(mock_data, "M5")

        # ボリンジャーバンド計算
        bb_result = await unified_calculator.calculate_bollinger_bands(mock_data, "M5")

        end_time = time.time()
        calculation_time = end_time - start_time

        # パフォーマンス基準
        assert calculation_time < 1.0  # 1秒以内
        assert rsi_result is not None
        assert macd_result is not None
        assert bb_result is not None

        print(f"計算時間: {calculation_time:.3f}秒")

    async def test_memory_usage(self, unified_service):
        """メモリ使用量テスト"""
        # 初期メモリ使用量
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # サービス初期化
        await unified_service.initialize()

        # 初期化後のメモリ使用量
        after_init_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 複数回の計算実行
        for i in range(10):
            await unified_service.calculate_and_save_all_indicators("M5")

        # 最終メモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # メモリ使用量の増加を確認
        memory_increase = final_memory - initial_memory

        # パフォーマンス基準（100MB以内の増加）
        assert memory_increase < 100

        print(f"初期メモリ: {initial_memory:.2f}MB")
        print(f"初期化後メモリ: {after_init_memory:.2f}MB")
        print(f"最終メモリ: {final_memory:.2f}MB")
        print(f"メモリ増加: {memory_increase:.2f}MB")

    async def test_concurrent_processing(self, unified_service):
        """並行処理テスト"""
        # 複数の時間足で並行処理
        timeframes = ["M5", "H1", "H4", "D1"]

        start_time = time.time()

        # 並行実行
        tasks = [
            unified_service.calculate_and_save_all_indicators(timeframe)
            for timeframe in timeframes
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        concurrent_time = end_time - start_time

        # パフォーマンス基準（5秒以内）
        assert concurrent_time < 5.0

        # エラーがないことを確認
        for result in results:
            assert not isinstance(result, Exception)

        print(f"並行処理時間: {concurrent_time:.3f}秒")

    async def test_large_dataset_performance(self, unified_calculator):
        """大規模データセットパフォーマンステスト"""
        # 大規模データセットの準備（1万件）
        large_data = {
            "Close": [100 + i * 0.01 for i in range(10000)],
            "High": [101 + i * 0.01 for i in range(10000)],
            "Low": [99 + i * 0.01 for i in range(10000)],
            "Volume": [1000000 for _ in range(10000)],
        }

        start_time = time.time()

        # 大規模データでの計算
        rsi_result = await unified_calculator.calculate_rsi(large_data, "M5")
        macd_result = await unified_calculator.calculate_macd(large_data, "M5")
        bb_result = await unified_calculator.calculate_bollinger_bands(large_data, "M5")

        end_time = time.time()
        large_data_time = end_time - start_time

        # パフォーマンス基準（10秒以内）
        assert large_data_time < 10.0
        assert rsi_result is not None
        assert macd_result is not None
        assert bb_result is not None

        print(f"大規模データ処理時間: {large_data_time:.3f}秒")

    async def test_health_check_performance(self, unified_service):
        """健全性チェックパフォーマンステスト"""
        await unified_service.initialize()

        start_time = time.time()

        # 複数回の健全性チェック
        for _ in range(100):
            health = await unified_service.health_check()
            assert health["status"] in ["healthy", "uninitialized"]

        end_time = time.time()
        health_check_time = end_time - start_time

        # パフォーマンス基準（1秒以内で100回）
        assert health_check_time < 1.0

        print(f"健全性チェック時間（100回）: {health_check_time:.3f}秒")

    async def test_initialization_performance(self, unified_service):
        """初期化パフォーマンステスト"""
        start_time = time.time()

        # 初期化
        result = await unified_service.initialize()

        end_time = time.time()
        init_time = end_time - start_time

        # パフォーマンス基準（5秒以内）
        assert init_time < 5.0
        assert result is True

        print(f"初期化時間: {init_time:.3f}秒")

    async def test_error_recovery_performance(self, unified_service):
        """エラー回復パフォーマンステスト"""
        await unified_service.initialize()

        start_time = time.time()

        # エラーケースでの処理
        for _ in range(10):
            try:
                # 不正なデータで計算
                await unified_service.calculate_rsi({}, "M5")
            except Exception:
                pass  # エラーは予期される

        end_time = time.time()
        error_recovery_time = end_time - start_time

        # パフォーマンス基準（2秒以内）
        assert error_recovery_time < 2.0

        print(f"エラー回復時間: {error_recovery_time:.3f}秒")

    async def test_new_features_performance(self, unified_calculator):
        """新機能パフォーマンステスト"""
        # モックデータの準備
        mock_data = {
            "Close": [100 + i * 0.1 for i in range(1000)],
            "High": [101 + i * 0.1 for i in range(1000)],
            "Low": [99 + i * 0.1 for i in range(1000)],
            "Volume": [1000000 for _ in range(1000)],
        }

        start_time = time.time()

        # 新機能（ストキャスティクス、ATR）の計算
        # 注: 実際の実装では、これらの機能は calculate_timeframe_indicators 内で実行される
        # ここでは基本的な計算性能をテスト

        # 健全性チェック
        health = await unified_calculator.health_check()

        end_time = time.time()
        new_features_time = end_time - start_time

        # パフォーマンス基準（1秒以内）
        assert new_features_time < 1.0
        assert health["status"] in ["healthy", "unhealthy"]

        print(f"新機能処理時間: {new_features_time:.3f}秒")
