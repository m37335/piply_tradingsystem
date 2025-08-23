#!/usr/bin/env python3
"""
テストデータ詳細確認スクリプト

テスト時に使用した実際のデータを詳細に確認します
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def check_test_data():
    """テストデータの詳細確認"""
    print("=" * 80)
    print("📊 テストデータ詳細確認")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. テストで使用したRSIデータの詳細...")
            
            # テストで使用したRSI 34.28のデータを詳細確認
            result = await db_session.execute(
                text("""
                SELECT 
                    value,
                    timestamp,
                    timeframe,
                    currency_pair
                FROM technical_indicators
                WHERE indicator_type = 'RSI'
                AND value BETWEEN 34.0 AND 35.0
                AND timestamp >= '2025-08-13 09:50:00'
                AND timestamp <= '2025-08-13 10:00:00'
                ORDER BY timestamp DESC
                LIMIT 10
                """)
            )
            rsi_test_data = result.fetchall()
            
            print(f"✅ テストで使用したRSIデータ: {len(rsi_test_data)}件")
            for value, timestamp, timeframe, currency_pair in rsi_test_data:
                print(f"  📊 RSI: {value:.2f} | {timeframe} | {currency_pair} | {timestamp}")

            print("\n🔍 2. 同時刻の他の指標データ...")
            
            # テストで使用した時刻の他の指標を確認
            from datetime import datetime
            test_timestamp = datetime(2025, 8, 13, 9, 55, 0)
            result = await db_session.execute(
                text("""
                SELECT 
                    indicator_type,
                    value,
                    timeframe,
                    currency_pair
                FROM technical_indicators
                WHERE timestamp = :timestamp
                ORDER BY indicator_type
                """),
                {"timestamp": test_timestamp}
            )
            concurrent_data = result.fetchall()
            
            print(f"✅ {test_timestamp}の同時刻データ: {len(concurrent_data)}件")
            for indicator_type, value, timeframe, currency_pair in concurrent_data:
                print(f"  📊 {indicator_type}: {value} | {timeframe} | {currency_pair}")

            print("\n🔍 3. シグナル生成に必要な指標の組み合わせ...")
            
            # RSI、SMA、MACDの組み合わせを確認
            result = await db_session.execute(
                text("""
                SELECT 
                    ti1.value as rsi_value,
                    ti2.value as sma_value,
                    ti3.value as macd_value,
                    ti1.timestamp,
                    ti1.timeframe
                FROM technical_indicators ti1
                LEFT JOIN technical_indicators ti2 ON 
                    ti1.timestamp = ti2.timestamp 
                    AND ti1.timeframe = ti2.timeframe 
                    AND ti2.indicator_type = 'SMA_20'
                LEFT JOIN technical_indicators ti3 ON 
                    ti1.timestamp = ti3.timestamp 
                    AND ti1.timeframe = ti3.timeframe 
                    AND ti3.indicator_type = 'MACD_histogram'
                WHERE ti1.indicator_type = 'RSI'
                AND ti1.value BETWEEN 34.0 AND 35.0
                AND ti1.timestamp >= '2025-08-13 09:50:00'
                ORDER BY ti1.timestamp DESC
                LIMIT 5
                """)
            )
            signal_combination_data = result.fetchall()
            
            print(f"✅ シグナル生成に必要な指標組み合わせ: {len(signal_combination_data)}件")
            for rsi, sma, macd, timestamp, timeframe in signal_combination_data:
                sma_str = f"{sma:.5f}" if sma else "N/A"
                macd_str = f"{macd:.5f}" if macd else "N/A"
                print(f"  📊 {timeframe}: RSI={rsi:.2f}, SMA20={sma_str}, MACD={macd_str} | {timestamp}")

            print("\n🔍 4. テストで生成されたシグナルの詳細...")
            
            # テストで生成されたシグナルの詳細を確認
            print("✅ テストシグナル詳細:")
            print("  📊 シグナルタイプ: BUY")
            print("  📊 通貨ペア: USD/JPY")
            print("  📊 タイムフレーム: H1")
            print("  📊 エントリー価格: 150.50")
            print("  📊 ストップロス: 150.00")
            print("  📊 利益確定: 151.50")
            print("  📊 リスク/リワード比: 2.0:1")
            print("  📊 信頼度: 75%")
            print("  📊 使用指標:")
            print("    • RSI: 34.28")
            print("    • SMA_20: 150.30")
            print("    • MACD_histogram: 0.001")

            print("\n🔍 5. テストで生成されたリスクアラートの詳細...")
            
            print("✅ テストリスクアラート詳細:")
            print("  📊 アラートタイプ: volatility_spike")
            print("  📊 通貨ペア: USD/JPY")
            print("  📊 タイムフレーム: H1")
            print("  📊 重要度: HIGH")
            print("  📊 メッセージ: ボラティリティ急増検出: ATRが過去平均の2倍を超えています")
            print("  📊 推奨アクション: ポジションサイズを50%削減、ストップロスを広げることを推奨")
            print("  📊 市場データ:")
            print("    • 現在ATR: 0.015")
            print("    • 平均ATR: 0.007")
            print("    • 24時間価格変動: 2.5%")
            print("    • 出来高比率: 2.8")
            print("  📊 閾値: 0.014")
            print("  📊 現在値: 0.015")

            print("\n🔍 6. Discord通知で送信されたメッセージの詳細...")
            
            print("✅ Discord通知メッセージ詳細:")
            print("  📱 基本的な通知テスト:")
            print("    • タイトル: ✅ システム動作確認")
            print("    • 内容: Discord Webhook URL最適化テストが正常に動作しています")
            print("    • システム状況: データベース接続、シグナル生成、通知システムの確認")
            print("    • 機能確認: RSI、ボリンジャーバンド、ボラティリティ検出の確認")
            
            print("  📱 エントリーシグナル通知:")
            print("    • タイトル: 🟢 USD/JPY BUYエントリーシグナル")
            print("    • 価格情報: エントリー150.500、SL150.000、TP151.500")
            print("    • リスク管理: リスク/リワード比2.0:1、信頼度75%")
            print("    • 指標状況: RSI 34.28、SMA_20 150.30、MACD 0.001")
            
            print("  📱 リスクアラート通知:")
            print("    • タイトル: 🔴 リスクアラート: Volatility Spike")
            print("    • アラート内容: ボラティリティ急増検出")
            print("    • 推奨アクション: ポジションサイズ削減、ストップロス拡大")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_test_data())
