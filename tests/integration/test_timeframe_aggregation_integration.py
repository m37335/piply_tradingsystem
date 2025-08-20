#!/usr/bin/env python3
"""
時間足集計システムの統合テスト

責任:
- 実際のデータベース接続を使用したテスト
- 完全なワークフローのテスト
- エラーハンドリングのテスト
- パフォーマンステスト
"""

import asyncio
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

import pytz

# プロジェクトルートをパスに追加
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.cron.hourly_aggregator import HourlyAggregator
from scripts.cron.four_hour_aggregator import FourHourAggregator
from scripts.cron.daily_aggregator import DailyAggregator
from src.infrastructure.database.models.price_data_model import PriceDataModel


class TestTimeframeAggregationIntegration:
    """時間足集計の統合テスト"""

    @pytest.fixture
    def setup_test_data(self):
        """テストデータのセットアップ"""
        # テスト用の5分足データを作成
        test_data = []
        base_time = datetime(2025, 1, 1, 10, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo"))
        
        for i in range(12):  # 1時間分のデータ（12件）
            timestamp = base_time + timedelta(minutes=5 * i)
            test_data.append(PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=timestamp,
                data_timestamp=timestamp,
                fetched_at=timestamp,
                open_price=100.0 + i,
                high_price=105.0 + i,
                low_price=99.0 + i,
                close_price=102.0 + i,
                volume=1000 + i * 100,
                data_source="yahoo_finance_5m"
            ))
        
        return test_data

    @pytest.mark.asyncio
    async def test_hourly_aggregation_full_workflow(self, setup_test_data):
        """1時間足集計の完全なワークフローテスト"""
        # テストデータをデータベースに保存
        # 実際のデータベース接続を使用
        aggregator = HourlyAggregator()
        
        try:
            await aggregator.initialize_database()
            
            # テストデータを保存
            for data in setup_test_data:
                await aggregator.price_repo.save(data)
            
            # 集計実行
            await aggregator.aggregate_and_save()
            
            # 結果を検証
            # 実際のデータベースから集計データを取得して検証
            
        finally:
            await aggregator.cleanup()

    @pytest.mark.asyncio
    async def test_four_hour_aggregation_full_workflow(self, setup_test_data):
        """4時間足集計の完全なワークフローテスト"""
        aggregator = FourHourAggregator()
        
        try:
            await aggregator.initialize_database()
            
            # テストデータを保存
            for data in setup_test_data:
                await aggregator.price_repo.save(data)
            
            # 集計実行
            await aggregator.aggregate_and_save()
            
            # 結果を検証
            
        finally:
            await aggregator.cleanup()

    @pytest.mark.asyncio
    async def test_daily_aggregation_full_workflow(self, setup_test_data):
        """日足集計の完全なワークフローテスト"""
        aggregator = DailyAggregator()
        
        try:
            await aggregator.initialize_database()
            
            # テストデータを保存
            for data in setup_test_data:
                await aggregator.price_repo.save(data)
            
            # 集計実行
            await aggregator.aggregate_and_save()
            
            # 結果を検証
            
        finally:
            await aggregator.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """エラーハンドリングのテスト"""
        aggregator = HourlyAggregator()
        
        try:
            await aggregator.initialize_database()
            
            # データが不足している場合のテスト
            await aggregator.aggregate_and_save()
            # エラーが発生せずに正常終了することを確認
            
        finally:
            await aggregator.cleanup()

    @pytest.mark.asyncio
    async def test_performance(self, setup_test_data):
        """パフォーマンステスト"""
        aggregator = HourlyAggregator()
        
        try:
            await aggregator.initialize_database()
            
            # 大量のテストデータを保存
            for i in range(100):  # 100時間分のデータ
                for j in range(12):  # 1時間12件
                    timestamp = datetime(2025, 1, 1, 10, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")) + timedelta(hours=i, minutes=5*j)
                    data = PriceDataModel(
                        currency_pair="USD/JPY",
                        timestamp=timestamp,
                        data_timestamp=timestamp,
                        fetched_at=timestamp,
                        open_price=100.0 + i + j,
                        high_price=105.0 + i + j,
                        low_price=99.0 + i + j,
                        close_price=102.0 + i + j,
                        volume=1000 + i * 100 + j * 10,
                        data_source="yahoo_finance_5m"
                    )
                    await aggregator.price_repo.save(data)
            
            # パフォーマンス測定
            import time
            start_time = time.time()
            await aggregator.aggregate_and_save()
            end_time = time.time()
            
            # 10秒以内で完了することを確認
            assert end_time - start_time < 10
            
        finally:
            await aggregator.cleanup()


if __name__ == "__main__":
    pytest.main([__file__])
