#!/usr/bin/env python3
"""
利用可能なテクニカル指標確認スクリプト

現在のデータベースに保存されているテクニカル指標を確認し、
MACDヒストグラムの代替案を検討します
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


async def check_available_indicators():
    """利用可能なテクニカル指標の確認"""
    print("=" * 80)
    print("📊 利用可能なテクニカル指標確認")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 現在利用可能なテクニカル指標...")
            
            # 利用可能な指標を確認
            result = await db_session.execute(
                text("""
                SELECT 
                    indicator_type,
                    COUNT(*) as count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM technical_indicators
                GROUP BY indicator_type
                ORDER BY count DESC
                """)
            )
            indicators = result.fetchall()
            
            print("✅ 利用可能なテクニカル指標:")
            for indicator_type, count, earliest, latest in indicators:
                print(f"  📊 {indicator_type}: {count:,}件 ({earliest} ～ {latest})")

            print("\n🔍 2. MACD関連指標の確認...")
            
            # MACD関連指標を確認
            result = await db_session.execute(
                text("""
                SELECT 
                    indicator_type,
                    COUNT(*) as count
                FROM technical_indicators
                WHERE indicator_type LIKE 'MACD%'
                GROUP BY indicator_type
                ORDER BY indicator_type
                """)
            )
            macd_indicators = result.fetchall()
            
            if macd_indicators:
                print("✅ MACD関連指標:")
                for indicator_type, count in macd_indicators:
                    print(f"  📊 {indicator_type}: {count:,}件")
            else:
                print("❌ MACD関連指標は保存されていません")

            print("\n🔍 3. 代替案の検討...")
            
            print("✅ MACDヒストグラムの代替案:")
            
            # 代替案1: EMAの傾きを使用
            print("  📊 代替案1: EMAの傾き（モメンタム指標）")
            print("    • EMA_12とEMA_26の傾きを計算")
            print("    • 上昇トレンド: EMA_12 > EMA_26")
            print("    • 下降トレンド: EMA_12 < EMA_26")
            
            # 代替案2: RSIの変化率を使用
            print("  📊 代替案2: RSIの変化率（モメンタム指標）")
            print("    • 前回のRSIと現在のRSIの差分")
            print("    • 上昇モメンタム: RSI変化率 > 0")
            print("    • 下降モメンタム: RSI変化率 < 0")
            
            # 代替案3: 価格の変化率を使用
            print("  📊 代替案3: 価格の変化率（モメンタム指標）")
            print("    • 前回の価格と現在の価格の差分")
            print("    • 上昇モメンタム: 価格変化率 > 0")
            print("    • 下降モメンタム: 価格変化率 < 0")
            
            # 代替案4: ストキャスティクスを使用
            print("  📊 代替案4: ストキャスティクス（オシレーター）")
            print("    • %Kと%Dの位置関係")
            print("    • 上昇シグナル: %K > %D")
            print("    • 下降シグナル: %K < %D")

            print("\n🔍 4. 実際の代替指標のテスト...")
            
            # 代替案1のテスト: EMAの傾き
            print("✅ 代替案1テスト: EMAの傾き")
            result = await db_session.execute(
                text("""
                SELECT 
                    ti1.value as ema_12,
                    ti2.value as ema_26,
                    ti1.timestamp,
                    ti1.timeframe
                FROM technical_indicators ti1
                LEFT JOIN technical_indicators ti2 ON 
                    ti1.timestamp = ti2.timestamp 
                    AND ti1.timeframe = ti2.timeframe 
                    AND ti2.indicator_type = 'EMA_26'
                WHERE ti1.indicator_type = 'EMA_12'
                AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY ti1.timestamp DESC
                LIMIT 5
                """)
            )
            ema_data = result.fetchall()
            
            print(f"✅ EMAデータ: {len(ema_data)}件")
            for ema_12, ema_26, timestamp, timeframe in ema_data:
                if ema_12 and ema_26:
                    momentum = "上昇" if ema_12 > ema_26 else "下降"
                    print(f"  📊 {timeframe}: EMA12={ema_12:.5f}, EMA26={ema_26:.5f} | モメンタム: {momentum}")

            # 代替案2のテスト: RSIの変化率
            print("\n✅ 代替案2テスト: RSIの変化率")
            result = await db_session.execute(
                text("""
                SELECT 
                    value,
                    timestamp,
                    timeframe,
                    LAG(value) OVER (PARTITION BY timeframe ORDER BY timestamp) as prev_rsi
                FROM technical_indicators
                WHERE indicator_type = 'RSI'
                AND timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY timestamp DESC
                LIMIT 5
                """)
            )
            rsi_change_data = result.fetchall()
            
            print(f"✅ RSI変化率データ: {len(rsi_change_data)}件")
            for rsi, timestamp, timeframe, prev_rsi in rsi_change_data:
                if rsi and prev_rsi:
                    change_rate = rsi - prev_rsi
                    momentum = "上昇" if change_rate > 0 else "下降"
                    print(f"  📊 {timeframe}: RSI={rsi:.2f}, 前回={prev_rsi:.2f}, 変化={change_rate:+.2f} | モメンタム: {momentum}")

            print("\n🔍 5. 推奨代替案...")
            
            print("✅ 推奨代替案:")
            print("  🥇 最優先: EMAの傾き（EMA_12 vs EMA_26）")
            print("    • 理由: MACDと同じ移動平均の概念")
            print("    • 実装: 簡単で安定")
            print("    • 精度: 高い")
            
            print("  🥈 次点: RSIの変化率")
            print("    • 理由: モメンタムの変化を直接測定")
            print("    • 実装: 前回値との比較が必要")
            print("    • 精度: 中程度")
            
            print("  🥉 補助: ストキャスティクス")
            print("    • 理由: オシレーターとしてRSIと相補的")
            print("    • 実装: 既にデータあり")
            print("    • 精度: 中程度")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_available_indicators())
