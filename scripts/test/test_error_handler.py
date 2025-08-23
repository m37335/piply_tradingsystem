#!/usr/bin/env python3
"""
エラーハンドリングシステムテスト
"""

import asyncio
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, "/app")

from src.infrastructure.error_handling.error_handler import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    RecoveryAction,
)


class ErrorHandlerTester:
    """エラーハンドリングシステムテスト"""

    def __init__(self):
        self.error_handler = None

    def initialize(self):
        """初期化"""
        print("🔧 エラーハンドリングシステムテストを初期化中...")

        self.error_handler = ErrorHandler()

        print("✅ 初期化完了")

    def test_error_handling(self):
        """エラー処理テスト"""
        print("\n🚨 エラー処理テスト...")

        try:
            # 様々なエラーをテスト
            test_errors = [
                {
                    "error": ValueError("無効な値です"),
                    "category": ErrorCategory.VALIDATION,
                    "severity": ErrorSeverity.MEDIUM,
                },
                {
                    "error": ConnectionError("データベース接続エラー"),
                    "category": ErrorCategory.DATABASE,
                    "severity": ErrorSeverity.HIGH,
                },
                {
                    "error": TimeoutError("API呼び出しタイムアウト"),
                    "category": ErrorCategory.API,
                    "severity": ErrorSeverity.MEDIUM,
                },
                {
                    "error": MemoryError("メモリ不足エラー"),
                    "category": ErrorCategory.MEMORY,
                    "severity": ErrorSeverity.CRITICAL,
                },
            ]

            for i, test_case in enumerate(test_errors, 1):
                print(f"  📝 テストエラー {i}: {test_case['error']}")

                error_info = self.error_handler.handle_error(
                    error=test_case["error"],
                    category=test_case["category"],
                    severity=test_case["severity"],
                    context={"test_case": i},
                )

                print(f"    ✅ エラー処理完了: {error_info.error_type}")
                print(f"    カテゴリ: {error_info.category.value}")
                print(f"    深刻度: {error_info.severity.value}")
                print(f"    解決済み: {error_info.resolved}")

            return True
        except Exception as e:
            print(f"❌ エラー処理テストエラー: {e}")
            return False

    def test_error_statistics(self):
        """エラー統計テスト"""
        print("\n📊 エラー統計テスト...")

        try:
            stats = self.error_handler.get_error_statistics(hours=1)

            print("✅ エラー統計取得成功")
            print(f"   📊 総エラー数: {stats['total_errors']}")
            print(f"   ✅ 解決済みエラー数: {stats['resolved_errors']}")
            print(f"   📈 解決率: {stats['resolution_rate']:.1%}")

            print(f"   📋 カテゴリ別分布:")
            for category, count in stats["category_distribution"].items():
                print(f"     {category}: {count}件")

            print(f"   🚨 深刻度別分布:")
            for severity, count in stats["severity_distribution"].items():
                print(f"     {severity}: {count}件")

            return True
        except Exception as e:
            print(f"❌ エラー統計テストエラー: {e}")
            return False

    def test_recent_errors(self):
        """最近のエラー取得テスト"""
        print("\n📋 最近のエラー取得テスト...")

        try:
            recent_errors = self.error_handler.get_recent_errors(limit=5)

            print(f"✅ 最近のエラー取得成功: {len(recent_errors)}件")

            for i, error in enumerate(recent_errors, 1):
                print(f"  {i}. {error.error_type}: {error.error_message}")
                print(f"     時刻: {error.timestamp.strftime('%H:%M:%S')}")
                print(f"     カテゴリ: {error.category.value}")
                print(f"     深刻度: {error.severity.value}")
                print(f"     解決済み: {error.resolved}")

            return True
        except Exception as e:
            print(f"❌ 最近のエラー取得テストエラー: {e}")
            return False

    def test_custom_recovery_action(self):
        """カスタム復旧アクションテスト"""
        print("\n🔧 カスタム復旧アクションテスト...")

        try:
            # カスタム復旧アクションを追加
            async def custom_recovery_action(error_info):
                print(f"    🔧 カスタム復旧実行: {error_info.error_type}")
                await asyncio.sleep(1)
                print("    ✅ カスタム復旧完了")

            custom_action = RecoveryAction(
                name="カスタム復旧",
                description="テスト用カスタム復旧アクション",
                action=custom_recovery_action,
                conditions=["test", "custom"],
                timeout_seconds=10,
            )

            self.error_handler.add_recovery_action(ErrorCategory.UNKNOWN, custom_action)

            print("✅ カスタム復旧アクション追加完了")

            # テストエラーを発生させて復旧をテスト
            test_error = ValueError("カスタム復旧テストエラー")
            error_info = self.error_handler.handle_error(
                error=test_error,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                context={"test": "custom_recovery"},
            )

            # 復旧処理の完了を待つ
            time.sleep(2)

            print(f"✅ カスタム復旧テスト完了: 解決済み={error_info.resolved}")

            return True
        except Exception as e:
            print(f"❌ カスタム復旧アクションテストエラー: {e}")
            return False

    def test_error_report(self):
        """エラーレポートテスト"""
        print("\n📋 エラーレポートテスト...")

        try:
            report = self.error_handler.generate_error_report()

            print("✅ エラーレポート生成成功")
            print(f"   📅 生成時刻: {report['timestamp']}")

            stats = report["statistics"]
            print(f"   📊 統計情報:")
            print(f"     総エラー数: {stats['total_errors']}")
            print(f"     解決済み: {stats['resolved_errors']}")
            print(f"     解決率: {stats['resolution_rate']:.1%}")

            print(f"   📋 最近のエラー: {len(report['recent_errors'])}件")
            for error in report["recent_errors"]:
                print(f"     - {error['type']}: {error['message']}")

            print(f"   🔧 復旧アクション:")
            for category, count in report["recovery_actions"].items():
                print(f"     {category}: {count}件")

            return True
        except Exception as e:
            print(f"❌ エラーレポートテストエラー: {e}")
            return False

    def test_alert_thresholds(self):
        """アラート閾値テスト"""
        print("\n🚨 アラート閾値テスト...")

        try:
            # 複数のエラーを発生させてアラートをテスト
            print("  📝 複数エラー発生中...")

            for i in range(5):
                test_error = ValueError(f"アラートテストエラー {i+1}")
                self.error_handler.handle_error(
                    error=test_error,
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                )
                time.sleep(0.1)

            print("✅ アラート閾値テスト完了")
            print("  📊 アラートは自動的にログに記録されます")

            return True
        except Exception as e:
            print(f"❌ アラート閾値テストエラー: {e}")
            return False

    def test_error_cleanup(self):
        """エラークリーンアップテスト"""
        print("\n🧹 エラークリーンアップテスト...")

        try:
            initial_count = len(self.error_handler.errors)

            # 古いエラーを削除
            self.error_handler.clear_old_errors(days=0)  # 全てのエラーを削除

            final_count = len(self.error_handler.errors)
            deleted_count = initial_count - final_count

            print(f"✅ エラークリーンアップ完了")
            print(f"   📊 削除前: {initial_count}件")
            print(f"   📊 削除後: {final_count}件")
            print(f"   🗑️  削除数: {deleted_count}件")

            return True
        except Exception as e:
            print(f"❌ エラークリーンアップテストエラー: {e}")
            return False

    def run_all_tests(self):
        """全テストを実行"""
        print("🚀 エラーハンドリングシステムテスト開始")
        print("=" * 60)

        self.initialize()

        tests = [
            ("エラー処理", self.test_error_handling),
            ("エラー統計", self.test_error_statistics),
            ("最近のエラー取得", self.test_recent_errors),
            ("カスタム復旧アクション", self.test_custom_recovery_action),
            ("エラーレポート", self.test_error_report),
            ("アラート閾値", self.test_alert_thresholds),
            ("エラークリーンアップ", self.test_error_cleanup),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
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
            print("🎉 全テスト成功！エラーハンドリングシステムは正常に動作しています。")
        else:
            print("⚠️  一部のテストが失敗しました。詳細を確認してください。")

    def cleanup(self):
        """クリーンアップ"""
        print("\n🧹 クリーンアップ完了")


def main():
    """メイン関数"""
    tester = ErrorHandlerTester()
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
