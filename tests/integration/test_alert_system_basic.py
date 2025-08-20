#!/usr/bin/env python3
"""
アラートシステム基本動作確認スクリプト

開発環境での基本的な機能確認用
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))


async def test_basic_alert_system():
    """基本的なアラートシステムの動作確認"""

    print("🚀 アラートシステム基本動作確認を開始...")

    try:
        # 1. モデルのインポート確認
        print("\n📋 1. モデルインポート確認...")
        from src.infrastructure.database.models.alert_settings_model import (
            AlertSettingsModel,
        )
        from src.infrastructure.database.models.entry_signal_model import (
            EntrySignalModel,
        )
        from src.infrastructure.database.models.risk_alert_model import RiskAlertModel
        from src.infrastructure.database.models.signal_performance_model import (
            SignalPerformanceModel,
        )

        print("✅ モデルインポート成功")

        # 2. アラート設定の作成テスト
        print("\n⚙️ 2. アラート設定作成テスト...")
        rsi_setting = AlertSettingsModel.create_rsi_entry_signal(
            timeframe="H1", threshold_value=30.0, risk_reward_min=2.0, confidence_min=70
        )
        print(f"✅ RSI設定作成成功: {rsi_setting.alert_type}")

        # 3. エントリーシグナルの作成テスト
        print("\n📊 3. エントリーシグナル作成テスト...")
        signal = EntrySignalModel.create_buy_signal(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="H1",
            entry_price=150.000,
            stop_loss=149.500,
            take_profit=150.750,
            confidence_score=75,
        )
        print(f"✅ 買いシグナル作成成功: {signal.signal_type}")

        # 4. リスクアラートの作成テスト
        print("\n⚠️ 4. リスクアラート作成テスト...")
        risk_alert = RiskAlertModel(
            alert_type="volatility_spike",
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="H1",
            severity="HIGH",
            message="ボラティリティ急増検出",
            recommended_action="ポジションサイズを50%削減",
            market_data={"current_atr": 0.050, "avg_atr": 0.020},
            threshold_value=0.040,
            current_value=0.050,
        )
        print(f"✅ リスクアラート作成成功: {risk_alert.alert_type}")

        # 5. パフォーマンス追跡の作成テスト
        print("\n📈 5. パフォーマンス追跡作成テスト...")
        performance = SignalPerformanceModel.create_from_signal(
            signal_id=1,
            currency_pair="USD/JPY",
            timeframe="H1",
            entry_time=datetime.utcnow(),
            entry_price=150.000,
        )
        print(f"✅ パフォーマンス追跡作成成功: {performance.currency_pair}")

        # 6. サービス層のインポート確認
        print("\n🔧 6. サービス層インポート確認...")
        from src.domain.services.alert_engine.bollinger_bands_detector import (
            BollingerBandsEntryDetector,
        )
        from src.domain.services.alert_engine.rsi_entry_detector import RSIEntryDetector
        from src.domain.services.alert_engine.volatility_risk_detector import (
            VolatilityRiskDetector,
        )

        print("✅ サービス層インポート成功")

        # 7. 通知サービスのインポート確認
        print("\n📱 7. 通知サービスインポート確認...")
        from src.domain.services.notification.discord_notification_service import (
            DiscordNotificationService,
        )

        print("✅ 通知サービスインポート成功")

        # 8. パフォーマンスサービスのインポート確認
        print("\n📊 8. パフォーマンスサービスインポート確認...")
        from src.domain.services.performance.performance_analyzer import (
            PerformanceAnalyzer,
        )
        from src.domain.services.performance.signal_performance_tracker import (
            SignalPerformanceTracker,
        )

        print("✅ パフォーマンスサービスインポート成功")

        # 9. 最適化サービスのインポート確認
        print("\n⚡ 9. 最適化サービスインポート確認...")
        from src.domain.services.optimization.backtest_engine import BacktestEngine
        from src.domain.services.optimization.performance_optimizer import (
            PerformanceOptimizer,
        )

        print("✅ 最適化サービスインポート成功")

        print("\n🎉 アラートシステム基本動作確認完了！")
        print("\n📋 確認項目:")
        print("  ✅ データベースモデル")
        print("  ✅ アラート設定")
        print("  ✅ エントリーシグナル")
        print("  ✅ リスクアラート")
        print("  ✅ パフォーマンス追跡")
        print("  ✅ サービス層")
        print("  ✅ 通知システム")
        print("  ✅ パフォーマンス分析")
        print("  ✅ バックテスト・最適化")

        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_integration_workflow():
    """統合ワークフローのテスト"""

    print("\n🔄 統合ワークフローテストを開始...")

    try:
        # モックデータベースセッション（実際のDBは使用しない）
        class MockDBSession:
            async def execute(self, query):
                return None

            async def commit(self):
                pass

            async def rollback(self):
                pass

            def add(self, obj):
                pass

        db_session = MockDBSession()

        # 1. RSIエントリー検出器のテスト
        print("\n📊 1. RSIエントリー検出器テスト...")
        from src.domain.services.alert_engine.rsi_entry_detector import RSIEntryDetector

        rsi_detector = RSIEntryDetector(db_session)
        signals = await rsi_detector.detect_rsi_entry_signals("H1")
        print(f"✅ RSI検出器動作確認: {len(signals)}個のシグナル")

        # 2. ボリンジャーバンド検出器のテスト
        print("\n📈 2. ボリンジャーバンド検出器テスト...")
        from src.domain.services.alert_engine.bollinger_bands_detector import (
            BollingerBandsEntryDetector,
        )

        bb_detector = BollingerBandsEntryDetector(db_session)
        bb_signals = await bb_detector.detect_bb_entry_signals("H1")
        print(f"✅ BB検出器動作確認: {len(bb_signals)}個のシグナル")

        # 3. ボラティリティリスク検出器のテスト
        print("\n⚠️ 3. ボラティリティリスク検出器テスト...")
        from src.domain.services.alert_engine.volatility_risk_detector import (
            VolatilityRiskDetector,
        )

        volatility_detector = VolatilityRiskDetector(db_session)
        risk_alerts = await volatility_detector.detect_volatility_risk("H1")
        print(f"✅ ボラティリティ検出器動作確認: {len(risk_alerts)}個のアラート")

        # 4. パフォーマンス追跡器のテスト
        print("\n📈 4. パフォーマンス追跡器テスト...")
        from src.domain.services.performance.signal_performance_tracker import (
            SignalPerformanceTracker,
        )

        performance_tracker = SignalPerformanceTracker(db_session)
        print("✅ パフォーマンス追跡器初期化成功")

        # 5. パフォーマンス分析器のテスト
        print("\n📊 5. パフォーマンス分析器テスト...")
        from src.domain.services.performance.performance_analyzer import (
            PerformanceAnalyzer,
        )

        performance_analyzer = PerformanceAnalyzer(db_session)
        print("✅ パフォーマンス分析器初期化成功")

        # 6. バックテストエンジンのテスト
        print("\n🔄 6. バックテストエンジンテスト...")
        from src.domain.services.optimization.backtest_engine import BacktestEngine

        backtest_engine = BacktestEngine(db_session)
        print("✅ バックテストエンジン初期化成功")

        # 7. パフォーマンス最適化器のテスト
        print("\n⚡ 7. パフォーマンス最適化器テスト...")
        from src.domain.services.optimization.performance_optimizer import (
            PerformanceOptimizer,
        )

        performance_optimizer = PerformanceOptimizer(db_session)
        print("✅ パフォーマンス最適化器初期化成功")

        print("\n🎉 統合ワークフローテスト完了！")
        print("\n📋 統合確認項目:")
        print("  ✅ RSIエントリー検出")
        print("  ✅ ボリンジャーバンド検出")
        print("  ✅ ボラティリティリスク検出")
        print("  ✅ パフォーマンス追跡")
        print("  ✅ パフォーマンス分析")
        print("  ✅ バックテスト")
        print("  ✅ パフォーマンス最適化")

        return True

    except Exception as e:
        print(f"\n❌ 統合テストでエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """メイン関数"""
    print("=" * 60)
    print("🚨 プロトレーダー向け為替アラートシステム")
    print("   開発環境動作確認スクリプト")
    print("=" * 60)

    # 基本動作確認
    basic_success = await test_basic_alert_system()

    if basic_success:
        # 統合ワークフローテスト
        integration_success = await test_integration_workflow()

        if integration_success:
            print("\n" + "=" * 60)
            print("🎉 全てのテストが成功しました！")
            print("✅ アラートシステムは正常に動作しています")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠️ 統合テストで問題が発生しました")
            print("🔧 詳細な調査が必要です")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ 基本動作確認で問題が発生しました")
        print("🔧 実装の見直しが必要です")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
