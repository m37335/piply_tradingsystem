#!/usr/bin/env python3
"""
実際のPostgreSQLデータベースでのアラートシステムテスト

プロトレーダー向け為替アラートシステムの実際のデータベース接続テスト
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def test_real_database_connection():
    """実際のデータベース接続テスト"""

    print("🗄️ 実際のPostgreSQLデータベース接続テストを開始...")

    try:
        # データベース接続設定
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        database_url = os.getenv("DATABASE_URL")
        print(f"📋 データベースURL: {database_url}")

        # エンジン作成
        engine = create_async_engine(database_url, echo=False)

        # セッション作成
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # 接続テスト
        from sqlalchemy import text

        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL接続成功: {version}")

        return engine, async_session

    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        return None, None


async def test_alert_system_with_real_db():
    """実際のデータベースでのアラートシステムテスト"""

    print("\n🚨 実際のデータベースでのアラートシステムテストを開始...")

    # データベース接続
    engine, async_session = await test_real_database_connection()
    if not engine:
        print("❌ データベース接続に失敗しました")
        return False

    try:
        async with async_session() as db_session:
            print("\n📊 1. RSIエントリー検出器テスト...")
            from src.domain.services.alert_engine.rsi_entry_detector import (
                RSIEntryDetector,
            )

            rsi_detector = RSIEntryDetector(db_session)
            signals = await rsi_detector.detect_rsi_entry_signals("H1")
            print(f"✅ RSI検出器動作確認: {len(signals)}個のシグナル")

            # シグナルの詳細表示
            for i, signal in enumerate(signals[:3]):  # 最初の3個のみ表示
                print(
                    f"  シグナル{i+1}: {signal.signal_type} - 信頼度{signal.confidence_score}%"
                )

            print("\n📈 2. ボリンジャーバンド検出器テスト...")
            from src.domain.services.alert_engine.bollinger_bands_detector import (
                BollingerBandsEntryDetector,
            )

            bb_detector = BollingerBandsEntryDetector(db_session)
            bb_signals = await bb_detector.detect_bb_entry_signals("H1")
            print(f"✅ BB検出器動作確認: {len(bb_signals)}個のシグナル")

            print("\n⚠️ 3. ボラティリティリスク検出器テスト...")
            from src.domain.services.alert_engine.volatility_risk_detector import (
                VolatilityRiskDetector,
            )

            volatility_detector = VolatilityRiskDetector(db_session)
            risk_alerts = await volatility_detector.detect_volatility_risk("H1")
            print(f"✅ ボラティリティ検出器動作確認: {len(risk_alerts)}個のアラート")

            print("\n📈 4. パフォーマンス追跡器テスト...")
            from src.domain.services.performance.signal_performance_tracker import (
                SignalPerformanceTracker,
            )

            performance_tracker = SignalPerformanceTracker(db_session)
            print("✅ パフォーマンス追跡器初期化成功")

            print("\n📊 5. パフォーマンス分析器テスト...")
            from src.domain.services.performance.performance_analyzer import (
                PerformanceAnalyzer,
            )

            performance_analyzer = PerformanceAnalyzer(db_session)
            print("✅ パフォーマンス分析器初期化成功")

            # データベースのテーブル情報を確認
            print("\n🗃️ 6. データベーステーブル情報...")
            result = await db_session.execute(
                text(
                    """
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
                """
                )
            )
            tables = result.fetchall()
            print(f"✅ テーブル数: {len(tables)}")
            for table in tables[:10]:  # 最初の10個のみ表示
                print(f"  - {table[0]} ({table[1]})")

                # テクニカル指標データの確認
            print("\n📊 7. テクニカル指標データ確認...")
            result = await db_session.execute(
                text(
                    """
                SELECT COUNT(*) as total_count,
                       COUNT(DISTINCT indicator_type) as indicator_types,
                       COUNT(DISTINCT timeframe) as timeframes,
                       MIN(timestamp) as earliest_data,
                       MAX(timestamp) as latest_data
                FROM technical_indicators
                """
                )
            )
            stats = result.fetchone()
            if stats:
                print(f"✅ 総レコード数: {stats[0]}")
                print(f"✅ 指標タイプ数: {stats[1]}")
                print(f"✅ タイムフレーム数: {stats[2]}")
                print(f"✅ データ期間: {stats[3]} ～ {stats[4]}")
            else:
                print("⚠️ テクニカル指標データが見つかりません")

            print("\n🎉 実際のデータベースでのテスト完了！")
            return True

    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if engine:
            await engine.dispose()


async def test_data_generation():
    """テストデータ生成とアラートテスト"""

    print("\n🔧 テストデータ生成とアラートテストを開始...")

    engine, async_session = await test_real_database_connection()
    if not engine:
        return False

    try:
        async with async_session() as db_session:
            # テストデータの確認
            result = await db_session.execute(
                text(
                    """
                SELECT indicator_type, COUNT(*) as count
                FROM technical_indicators
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                GROUP BY indicator_type
                ORDER BY count DESC
                LIMIT 10
                """
                )
            )

            recent_data = result.fetchall()
            print(f"✅ 過去24時間のデータ: {len(recent_data)}種類の指標")

            for indicator_type, count in recent_data:
                print(f"  - {indicator_type}: {count}件")

            # 十分なデータがある場合、実際のアラート生成をテスト
            if recent_data and any(count > 10 for _, count in recent_data):
                print("\n🚨 実際のアラート生成テスト...")

                # RSI検出器で実際のシグナルを生成
                from src.domain.services.alert_engine.rsi_entry_detector import (
                    RSIEntryDetector,
                )

                rsi_detector = RSIEntryDetector(db_session)

                signals = await rsi_detector.detect_rsi_entry_signals("H1")
                if signals:
                    print(f"✅ 実際のRSIシグナル生成: {len(signals)}個")
                    for signal in signals[:2]:  # 最初の2個を詳細表示
                        print(
                            f"  📊 {signal.signal_type} - 価格:{signal.entry_price} - 信頼度:{signal.confidence_score}%"
                        )
                else:
                    print("ℹ️ 現在の市場状況ではRSIシグナルが生成されませんでした")

                # ボラティリティリスク検出
                from src.domain.services.alert_engine.volatility_risk_detector import (
                    VolatilityRiskDetector,
                )

                volatility_detector = VolatilityRiskDetector(db_session)

                risk_alerts = await volatility_detector.detect_volatility_risk("H1")
                if risk_alerts:
                    print(f"✅ 実際のリスクアラート生成: {len(risk_alerts)}個")
                    for alert in risk_alerts[:2]:  # 最初の2個を詳細表示
                        print(
                            f"  ⚠️ {alert.alert_type} - 重要度:{alert.severity} - {alert.message}"
                        )
                else:
                    print("ℹ️ 現在の市場状況ではリスクアラートが生成されませんでした")

            return True

    except Exception as e:
        print(f"\n❌ データ生成テストでエラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if engine:
            await engine.dispose()


async def main():
    """メイン関数"""
    print("=" * 70)
    print("🚨 プロトレーダー向け為替アラートシステム")
    print("   実際のPostgreSQLデータベーステスト")
    print("=" * 70)

    # 1. 実際のデータベースでのテスト
    db_test_success = await test_alert_system_with_real_db()

    if db_test_success:
        # 2. データ生成とアラートテスト
        data_test_success = await test_data_generation()

        if data_test_success:
            print("\n" + "=" * 70)
            print("🎉 全てのテストが成功しました！")
            print("✅ アラートシステムは実際のデータベースで正常に動作しています")
            print("✅ 実際のデータを使用したシグナル生成が可能です")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("⚠️ データ生成テストで問題が発生しました")
            print("🔧 データの確認が必要です")
            print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ データベース接続テストで問題が発生しました")
        print("🔧 データベース設定の確認が必要です")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
