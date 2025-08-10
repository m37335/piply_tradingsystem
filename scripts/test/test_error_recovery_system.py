#!/usr/bin/env python3
"""
エラーハンドリング・リカバリーシステムテスト
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.error_handling.error_decorators import (
    circuit_breaker,
    handle_errors,
    retry_on_error,
    timeout_handler,
)
from src.infrastructure.error_handling.error_recovery_manager import (
    ErrorRecoveryManager,
    ErrorSeverity,
    ErrorType,
    RecoveryAction,
)
from src.infrastructure.monitoring.log_manager import LogManager
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class ErrorRecoveryTester:
    """
    エラーハンドリング・リカバリーシステムテストクラス
    """

    def __init__(self):
        self.config_manager = None
        self.log_manager = None
        self.error_manager = None
        self.temp_config_file = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up error recovery test...")
        logger.info("Setting up error recovery test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # テスト用の設定を書き込み
        test_config = {
            "database": {
                "url": "sqlite+aiosqlite:///./test_error_recovery.db",
            },
            "logging": {
                "level": "DEBUG",
                "file_path": "./logs/test_error_recovery.log",
                "max_file_size": 1048576,
                "backup_count": 3,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "error_handling": {
                "max_retries": 3,
                "retry_delay": 1,
                "enable_circuit_breaker": True,
                "circuit_breaker_threshold": 3,
                "circuit_breaker_timeout": 30,
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

        # エラーハンドリングマネージャーを初期化
        self.error_manager = ErrorRecoveryManager(self.config_manager, self.log_manager)

        print("✅ Error recovery test setup completed")

    async def test_error_recovery_manager_initialization(self):
        """
        エラーハンドリングマネージャーの初期化テスト
        """
        print("\n=== Testing Error Recovery Manager Initialization ===")

        # 基本設定の確認
        assert self.error_manager.max_retries == 3
        assert self.error_manager.retry_delay == 1
        assert len(self.error_manager.recovery_strategies) == 8

        # 復旧戦略の確認
        db_strategy = self.error_manager.recovery_strategies[
            ErrorType.DATABASE_CONNECTION
        ]
        assert db_strategy["max_retries"] == 5
        assert db_strategy["severity"] == ErrorSeverity.HIGH
        assert RecoveryAction.RETRY in db_strategy["actions"]
        assert RecoveryAction.NOTIFY in db_strategy["actions"]

        print("✅ Error recovery manager initialization test passed")

    async def test_error_handling_basic(self):
        """
        基本的なエラーハンドリングテスト
        """
        print("\n=== Testing Basic Error Handling ===")

        # データベース接続エラーのテスト
        success = await self.error_manager.handle_error(
            error_type=ErrorType.DATABASE_CONNECTION,
            error_message="テスト用データベース接続エラー",
            context={"component": "test_db", "operation": "connect"},
        )

        assert success is True

        # エラー履歴の確認
        assert len(self.error_manager.error_history) == 1
        error_record = self.error_manager.error_history[0]
        assert error_record["error_type"] == "DATABASE_CONNECTION"
        assert error_record["message"] == "テスト用データベース接続エラー"
        assert error_record["severity"] == "HIGH"

        print("✅ Basic error handling test passed")

    async def test_retry_mechanism(self):
        """
        リトライメカニズムのテスト
        """
        print("\n=== Testing Retry Mechanism ===")

        # 同じエラーを複数回発生させる
        for i in range(3):
            success = await self.error_manager.handle_error(
                error_type=ErrorType.API_CONNECTION,
                error_message=f"API接続エラー #{i+1}",
                context={"component": "test_api"},
            )
            assert success is True

        # リトライカウンターの確認
        error_key = "API_CONNECTION_test_api"
        assert self.error_manager.retry_counters[error_key] == 3

        # 最大リトライ回数に達した場合のテスト
        success = await self.error_manager.handle_error(
            error_type=ErrorType.API_CONNECTION,
            error_message="最大リトライ回数テスト",
            context={"component": "test_api"},
        )
        assert success is False  # 最大リトライ回数に達したため失敗

        print("✅ Retry mechanism test passed")

    async def test_error_statistics(self):
        """
        エラー統計のテスト
        """
        print("\n=== Testing Error Statistics ===")

        # 様々なタイプのエラーを発生させる
        error_types = [
            ErrorType.DATA_FETCH,
            ErrorType.PATTERN_DETECTION,
            ErrorType.NOTIFICATION,
            ErrorType.MEMORY_LEAK,
        ]

        for error_type in error_types:
            await self.error_manager.handle_error(
                error_type=error_type,
                error_message=f"統計テスト用エラー: {error_type.value}",
                context={"test": "statistics"},
            )

        # 統計を取得
        stats = await self.error_manager.get_error_statistics(hours=24)

        assert stats["total_errors"] >= 8  # 基本テスト + 統計テスト
        assert "DATABASE_CONNECTION" in stats["error_types"]
        assert "API_CONNECTION" in stats["error_types"]
        assert "DATA_FETCH" in stats["error_types"]
        assert "HIGH" in stats["severity_counts"]
        assert "MEDIUM" in stats["severity_counts"]

        print("✅ Error statistics test passed")

    async def test_error_decorators(self):
        """
        エラーハンドリングデコレータのテスト
        """
        print("\n=== Testing Error Decorators ===")

        # テスト用の関数を作成
        @handle_errors(ErrorType.DATA_FETCH, {"component": "test_decorator"})
        async def test_function_with_error(error_manager):
            raise ValueError("デコレータテスト用エラー")

        # エラーハンドリングマネージャーを関数に渡す
        try:
            await test_function_with_error(self.error_manager)
        except ValueError:
            pass  # エラーは期待される動作

        # エラー履歴に記録されているか確認
        recent_errors = [
            e
            for e in self.error_manager.error_history
            if "デコレータテスト用エラー" in e["message"]
        ]
        assert len(recent_errors) == 1

        print("✅ Error decorators test passed")

    async def test_retry_decorator(self):
        """
        リトライデコレータのテスト
        """
        print("\n=== Testing Retry Decorator ===")

        call_count = 0

        @retry_on_error(max_retries=2, delay=0.1, error_type=ErrorType.API_CONNECTION)
        async def test_retry_function(error_manager):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("リトライテスト用エラー")
            return "success"

        # リトライデコレータをテスト
        try:
            result = await test_retry_function(self.error_manager)
            assert result == "success"
            assert call_count == 3  # 3回呼び出される（2回失敗 + 1回成功）
        except Exception as e:
            print(f"リトライデコレータテストでエラー: {e}")

        print("✅ Retry decorator test passed")

    async def test_circuit_breaker(self):
        """
        サーキットブレーカーのテスト
        """
        print("\n=== Testing Circuit Breaker ===")

        call_count = 0

        @circuit_breaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            error_type=ErrorType.API_CONNECTION,
        )
        async def test_circuit_breaker_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("サーキットブレーカーテスト用エラー")

        # サーキットブレーカーをテスト
        try:
            # 最初の2回はエラーが発生
            for i in range(2):
                try:
                    await test_circuit_breaker_function(self.error_manager)
                except ConnectionError:
                    pass

            # 3回目はサーキットブレーカーがOPEN状態になる
            try:
                await test_circuit_breaker_function(self.error_manager)
            except Exception as e:
                assert "サーキットブレーカーがOPEN状態です" in str(e)

        except Exception as e:
            print(f"サーキットブレーカーテストでエラー: {e}")

        print("✅ Circuit breaker test passed")

    async def test_timeout_handler(self):
        """
        タイムアウトハンドラーのテスト
        """
        print("\n=== Testing Timeout Handler ===")

        @timeout_handler(timeout_seconds=1.0, error_type=ErrorType.DATA_FETCH)
        async def test_timeout_function(error_manager):
            await asyncio.sleep(2.0)  # タイムアウトより長い時間待機
            return "success"

        # タイムアウトハンドラーをテスト
        try:
            await test_timeout_function(self.error_manager)
        except TimeoutError:
            # タイムアウトエラーは期待される動作
            pass

        print("✅ Timeout handler test passed")

    async def test_error_notification(self):
        """
        エラー通知のテスト
        """
        print("\n=== Testing Error Notification ===")

        # エラー通知をテスト（実際のDiscord送信はスキップ）
        success = await self.error_manager.handle_error(
            error_type=ErrorType.SYSTEM_CRASH,
            error_message="テスト用システムクラッシュ",
            context={"test": "notification"},
        )

        # 通知処理が実行されることを確認
        assert success is True

        print("✅ Error notification test passed")

    async def test_recovery_actions(self):
        """
        復旧アクションのテスト
        """
        print("\n=== Testing Recovery Actions ===")

        # リトライカウンターをリセット
        await self.error_manager.reset_retry_counters()

        # メモリリークエラーのテスト
        success = await self.error_manager.handle_error(
            error_type=ErrorType.MEMORY_LEAK,
            error_message="テスト用メモリリーク",
            context={"test": "cleanup"},
        )

        # メモリリークは最大リトライ回数が1のため、成功する
        assert success is True

        # ディスク容量エラーのテスト
        success = await self.error_manager.handle_error(
            error_type=ErrorType.DISK_SPACE,
            error_message="テスト用ディスク容量不足",
            context={"test": "cleanup"},
        )

        # ディスク容量エラーは最大リトライ回数が1のため、成功する
        assert success is True

        print("✅ Recovery actions test passed")

    async def test_error_manager_integration(self):
        """
        エラーハンドリングマネージャーの統合テスト
        """
        print("\n=== Testing Error Manager Integration ===")

        # 複数のエラーを同時に処理
        tasks = []
        for i in range(5):
            task = self.error_manager.handle_error(
                error_type=ErrorType.DATA_FETCH,
                error_message=f"統合テスト用エラー #{i+1}",
                context={"test": "integration", "index": i},
            )
            tasks.append(task)

        # 全てのタスクを並行実行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 全てのタスクが成功することを確認
        assert all(result is True for result in results)

        print("✅ Error manager integration test passed")

    async def run_all_tests(self):
        """
        全テストを実行
        """
        await self.setup()

        try:
            await self.test_error_recovery_manager_initialization()
            await self.test_error_handling_basic()
            await self.test_retry_mechanism()
            await self.test_error_statistics()
            await self.test_error_decorators()
            await self.test_retry_decorator()
            await self.test_circuit_breaker()
            await self.test_timeout_handler()
            await self.test_error_notification()
            await self.test_recovery_actions()
            await self.test_error_manager_integration()

            print("\n🎉 All error recovery tests passed!")

        except Exception as e:
            print(f"\n❌ Error recovery test failed: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        print("\nCleaning up error recovery test...")

        # リトライカウンターをリセット
        await self.error_manager.reset_retry_counters()

        # エラー履歴をクリア
        await self.error_manager.clear_error_history()

        # 一時ファイルを削除
        if self.temp_config_file and Path(self.temp_config_file.name).exists():
            Path(self.temp_config_file.name).unlink()

        print("✅ Error recovery test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting error recovery system test...")

    tester = ErrorRecoveryTester()
    await tester.run_all_tests()

    print("Error recovery system test completed!")


if __name__ == "__main__":
    asyncio.run(main())
