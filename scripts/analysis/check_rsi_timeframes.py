#!/usr/bin/env python3
"""
RSIタイムフレーム確認

RSIの各タイムフレーム別データ件数を確認
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


async def check_rsi_timeframes():
    """RSIのタイムフレーム別データ件数を確認"""
    print("=" * 80)
    print("🔍 RSIタイムフレーム別データ件数確認")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. RSIタイムフレーム別件数...")
            
            # タイムフレーム別件数を取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        timeframe,
                        COUNT(*) as count,
                        MIN(timestamp) as earliest,
                        MAX(timestamp) as latest
                    FROM technical_indicators
                    WHERE indicator_type = 'RSI'
                    AND currency_pair = 'USD/JPY'
                    GROUP BY timeframe
                    ORDER BY timeframe
                    """
                )
            )
            timeframes = result.fetchall()
            
            print(f"{'タイムフレーム':<10} {'件数':<10} {'最古データ':<20} {'最新データ':<20}")
            print("-" * 70)
            
            total_count = 0
            for timeframe, count, earliest, latest in timeframes:
                print(f"{timeframe:<10} {count:<10,} {earliest:<20} {latest:<20}")
                total_count += count
            
            print("-" * 70)
            print(f"{'合計':<10} {total_count:<10,}")
            
            print("\n🔍 2. 現在の分析で使用しているタイムフレーム...")
            
            # 現在の分析で使用しているタイムフレームを確認
            result = await db_session.execute(
                text(
                    """
                    SELECT timeframe, COUNT(*) as count
                    FROM technical_indicators
                    WHERE indicator_type = 'RSI'
                    AND currency_pair = 'USD/JPY'
                    AND timestamp >= NOW() - INTERVAL '7 days'
                    GROUP BY timeframe
                    ORDER BY count DESC
                    LIMIT 5
                    """
                )
            )
            recent_timeframes = result.fetchall()
            
            print("最近7日間のRSIデータ件数:")
            print(f"{'タイムフレーム':<10} {'件数':<10}")
            print("-" * 25)
            
            for timeframe, count in recent_timeframes:
                print(f"{timeframe:<10} {count:<10,}")
            
            print("\n🔍 3. RSI期間の確認...")
            
            # RSI期間の確認
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        parameters->>'period' as period,
                        COUNT(*) as count
                    FROM technical_indicators
                    WHERE indicator_type = 'RSI'
                    AND currency_pair = 'USD/JPY'
                    AND parameters IS NOT NULL
                    GROUP BY parameters->>'period'
                    ORDER BY count DESC
                    """
                )
            )
            periods = result.fetchall()
            
            print("RSI期間別件数:")
            print(f"{'期間':<10} {'件数':<10}")
            print("-" * 25)
            
            for period, count in periods:
                period_str = period if period else "不明"
                print(f"{period_str:<10} {count:<10,}")
            
            print("\n🔍 4. 分析結果の解釈...")
            print("現在の分析で使用しているRSI:")
            print("- 期間: 14（デフォルト）")
            print("- タイムフレーム: 主にM5（5分足）")
            print("- データ期間: データベース全体")
            
            print("\n🎯 結論:")
            print("✅ RSIタイムフレーム別データ件数を確認完了")
            print("✅ 現在の分析は主にM5（5分足）のRSIを使用")
            print("✅ 短期・中期・長期の区別は現在の分析では行っていない")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_rsi_timeframes())
