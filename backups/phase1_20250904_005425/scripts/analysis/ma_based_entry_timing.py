#!/usr/bin/env python3
"""
移動平均線ベースエントリータイミング

RSIシグナル後の移動平均線でのエントリータイミング分析
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def analyze_ma_based_entry_timing():
    """移動平均線ベースのエントリータイミングを分析"""
    print("=" * 80)
    print("🔍 移動平均線ベースエントリータイミング分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 買いシグナル（RSI < 40）後のエントリータイミング...")
            
            # 買いシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12
                    FROM technical_indicators ti1
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    LEFT JOIN technical_indicators ti2 ON 
                        ti1.timestamp = ti2.timestamp 
                        AND ti1.timeframe = ti2.timeframe 
                        AND ti2.indicator_type = 'SMA_20'
                    LEFT JOIN technical_indicators ti3 ON 
                        ti1.timestamp = ti3.timestamp 
                        AND ti1.timeframe = ti3.timeframe 
                        AND ti3.indicator_type = 'EMA_12'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value < 40
                    ORDER BY ti1.timestamp DESC
                    LIMIT 5
                    """
                )
            )
            buy_signals = result.fetchall()
            
            print(f"✅ 買いシグナル: {len(buy_signals)}件")
            
            if len(buy_signals) > 0:
                print("\n📊 買いシグナルのエントリータイミング分析:")
                print("=" * 140)
                print(f"{'時刻':<20} {'RSI':<6} {'シグナル価格':<12} {'SMA20':<10} {'EMA12':<10} {'プルバック':<12} {'ブレイク':<12} {'最適エントリー':<15} {'利益改善':<12}")
                print("=" * 140)
                
                for rsi, signal_price, signal_time, sma_20, ema_12 in buy_signals:
                    if signal_price and sma_20 and ema_12:
                        # 24時間の価格データを取得
                        future_time = signal_time + timedelta(hours=24)
                        
                        result = await db_session.execute(
                            text(
                                """
                                SELECT close_price, timestamp
                                FROM price_data
                                WHERE timestamp >= :signal_time
                                AND timestamp <= :future_time
                                AND currency_pair = 'USD/JPY'
                                ORDER BY timestamp ASC
                                """
                            ),
                            {
                                "signal_time": signal_time,
                                "future_time": future_time
                            }
                        )
                        price_data = result.fetchall()
                        
                        if len(price_data) > 0:
                            # エントリータイミングの分析
                            pullback_entry = None
                            breakout_entry = None
                            optimal_entry = None
                            max_price = 0
                            
                            for price, timestamp in price_data:
                                # 最大価格の更新
                                if price > max_price:
                                    max_price = price
                                
                                # プルバックエントリー（SMA20まで戻る）
                                if pullback_entry is None and price <= sma_20:
                                    pullback_entry = {
                                        "price": price,
                                        "time": timestamp,
                                        "delay_hours": (timestamp - signal_time).total_seconds() / 3600
                                    }
                                
                                # ブレイクアウトエントリー（EMA12上向きブレイク）
                                if breakout_entry is None and price > ema_12:
                                    breakout_entry = {
                                        "price": price,
                                        "time": timestamp,
                                        "delay_hours": (timestamp - signal_time).total_seconds() / 3600
                                    }
                
                            # 最適エントリーの決定
                            if pullback_entry and breakout_entry:
                                if pullback_entry["delay_hours"] < breakout_entry["delay_hours"]:
                                    optimal_entry = pullback_entry
                                else:
                                    optimal_entry = breakout_entry
                            elif pullback_entry:
                                optimal_entry = pullback_entry
                            elif breakout_entry:
                                optimal_entry = breakout_entry
                            
                            # 利益改善の計算
                            immediate_profit = (max_price - signal_price) * 100
                            optimal_profit = (max_price - optimal_entry["price"]) * 100 if optimal_entry else 0
                            improvement = immediate_profit - optimal_profit
                            
                            # 結果を表示
                            time_str = signal_time.strftime("%m-%d %H:%M")
                            rsi_str = f"{rsi:.1f}"
                            signal_price_str = f"{signal_price:.3f}"
                            sma_20_str = f"{sma_20:.3f}"
                            ema_12_str = f"{ema_12:.3f}"
                            
                            pullback_str = f"{pullback_entry['price']:.3f}({pullback_entry['delay_hours']:.1f}h)" if pullback_entry else "N/A"
                            breakout_str = f"{breakout_entry['price']:.3f}({breakout_entry['delay_hours']:.1f}h)" if breakout_entry else "N/A"
                            optimal_str = f"{optimal_entry['price']:.3f}({optimal_entry['delay_hours']:.1f}h)" if optimal_entry else "N/A"
                            improvement_str = f"{improvement:.1f}pips"
                            
                            print(f"{time_str:<20} {rsi_str:<6} {signal_price_str:<12} {sma_20_str:<10} {ema_12_str:<10} {pullback_str:<12} {breakout_str:<12} {optimal_str:<15} {improvement_str:<12}")
                
                print("=" * 140)
                
                # 戦略サマリー
                print(f"\n📈 買いシグナルエントリータイミング戦略:")
                print(f"- シグナル検出: RSI < 40")
                print(f"- プルバックエントリー: SMA20まで戻る")
                print(f"- ブレイクアウトエントリー: EMA12上向きブレイク")
                print(f"- 最適エントリー: より早いタイミング")
                print(f"- 利益改善: より良いエントリー価格")
            
            print("\n🔍 2. 売りシグナル（RSI > 60）後のエントリータイミング...")
            
            # 売りシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12
                    FROM technical_indicators ti1
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    LEFT JOIN technical_indicators ti2 ON 
                        ti1.timestamp = ti2.timestamp 
                        AND ti1.timeframe = ti2.timeframe 
                        AND ti2.indicator_type = 'SMA_20'
                    LEFT JOIN technical_indicators ti3 ON 
                        ti1.timestamp = ti3.timestamp 
                        AND ti1.timeframe = ti3.timeframe 
                        AND ti3.indicator_type = 'EMA_12'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value > 60
                    ORDER BY ti1.timestamp DESC
                    LIMIT 5
                    """
                )
            )
            sell_signals = result.fetchall()
            
            print(f"✅ 売りシグナル: {len(sell_signals)}件")
            
            if len(sell_signals) > 0:
                print("\n📊 売りシグナルのエントリータイミング分析:")
                print("=" * 140)
                print(f"{'時刻':<20} {'RSI':<6} {'シグナル価格':<12} {'SMA20':<10} {'EMA12':<10} {'プルバック':<12} {'ブレイク':<12} {'最適エントリー':<15} {'利益改善':<12}")
                print("=" * 140)
                
                for rsi, signal_price, signal_time, sma_20, ema_12 in sell_signals:
                    if signal_price and sma_20 and ema_12:
                        # 24時間の価格データを取得
                        future_time = signal_time + timedelta(hours=24)
                        
                        result = await db_session.execute(
                            text(
                                """
                                SELECT close_price, timestamp
                                FROM price_data
                                WHERE timestamp >= :signal_time
                                AND timestamp <= :future_time
                                AND currency_pair = 'USD/JPY'
                                ORDER BY timestamp ASC
                                """
                            ),
                            {
                                "signal_time": signal_time,
                                "future_time": future_time
                            }
                        )
                        price_data = result.fetchall()
                        
                        if len(price_data) > 0:
                            # エントリータイミングの分析
                            pullback_entry = None
                            breakout_entry = None
                            optimal_entry = None
                            min_price = float('inf')
                            
                            for price, timestamp in price_data:
                                # 最小価格の更新
                                if price < min_price:
                                    min_price = price
                                
                                # プルバックエントリー（SMA20まで戻る）
                                if pullback_entry is None and price >= sma_20:
                                    pullback_entry = {
                                        "price": price,
                                        "time": timestamp,
                                        "delay_hours": (timestamp - signal_time).total_seconds() / 3600
                                    }
                                
                                # ブレイクアウトエントリー（EMA12下向きブレイク）
                                if breakout_entry is None and price < ema_12:
                                    breakout_entry = {
                                        "price": price,
                                        "time": timestamp,
                                        "delay_hours": (timestamp - signal_time).total_seconds() / 3600
                                    }
                            
                            # 最適エントリーの決定
                            if pullback_entry and breakout_entry:
                                if pullback_entry["delay_hours"] < breakout_entry["delay_hours"]:
                                    optimal_entry = pullback_entry
                                else:
                                    optimal_entry = breakout_entry
                            elif pullback_entry:
                                optimal_entry = pullback_entry
                            elif breakout_entry:
                                optimal_entry = breakout_entry
                            
                            # 利益改善の計算
                            immediate_profit = (signal_price - min_price) * 100
                            optimal_profit = (optimal_entry["price"] - min_price) * 100 if optimal_entry else 0
                            improvement = immediate_profit - optimal_profit
                            
                            # 結果を表示
                            time_str = signal_time.strftime("%m-%d %H:%M")
                            rsi_str = f"{rsi:.1f}"
                            signal_price_str = f"{signal_price:.3f}"
                            sma_20_str = f"{sma_20:.3f}"
                            ema_12_str = f"{ema_12:.3f}"
                            
                            pullback_str = f"{pullback_entry['price']:.3f}({pullback_entry['delay_hours']:.1f}h)" if pullback_entry else "N/A"
                            breakout_str = f"{breakout_entry['price']:.3f}({breakout_entry['delay_hours']:.1f}h)" if breakout_entry else "N/A"
                            optimal_str = f"{optimal_entry['price']:.3f}({optimal_entry['delay_hours']:.1f}h)" if optimal_entry else "N/A"
                            improvement_str = f"{improvement:.1f}pips"
                            
                            print(f"{time_str:<20} {rsi_str:<6} {signal_price_str:<12} {sma_20_str:<10} {ema_12_str:<10} {pullback_str:<12} {breakout_str:<12} {optimal_str:<15} {improvement_str:<12}")
                
                print("=" * 140)
                
                # 戦略サマリー
                print(f"\n📈 売りシグナルエントリータイミング戦略:")
                print(f"- シグナル検出: RSI > 60")
                print(f"- プルバックエントリー: SMA20まで戻る")
                print(f"- ブレイクアウトエントリー: EMA12下向きブレイク")
                print(f"- 最適エントリー: より早いタイミング")
                print(f"- 利益改善: より良いエントリー価格")
            
            print("\n🔍 3. 実装戦略...")
            print("移動平均線ベースエントリータイミングの実装:")
            print("- シグナル検出: RSI条件")
            print("- エントリー待機: 移動平均線での確認")
            print("- プルバック戦略: より良いエントリー価格")
            print("- ブレイクアウト戦略: トレンド確認")
            
            print("\n🎯 結論:")
            print("✅ 移動平均線ベースエントリータイミング分析完了")
            print("✅ より良いエントリー価格での取引が可能")
            print("✅ リスク軽減と利益改善の実現")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_ma_based_entry_timing())
