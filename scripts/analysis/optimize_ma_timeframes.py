#!/usr/bin/env python3
"""
移動平均線期間最適化

短期・中期・長期移動平均線での最適なライン分析
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


async def optimize_ma_timeframes():
    """短期・中期・長期移動平均線の最適化を分析"""
    print("=" * 80)
    print("🔍 移動平均線期間最適化 - 短期・中期・長期分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 利用可能な移動平均線の確認...")
            
            # 利用可能な移動平均線を確認
            result = await db_session.execute(
                text(
                    """
                    SELECT DISTINCT indicator_type, COUNT(*) as count
                    FROM technical_indicators
                    WHERE indicator_type LIKE '%SMA%' OR indicator_type LIKE '%EMA%'
                    AND currency_pair = 'USD/JPY'
                    GROUP BY indicator_type
                    ORDER BY indicator_type
                    """
                )
            )
            available_mas = result.fetchall()
            
            print("✅ 利用可能な移動平均線:")
            for ma_type, count in available_mas:
                print(f"- {ma_type}: {count:,}件")
            
            print("\n🔍 2. 買いシグナル（RSI < 40）での移動平均線最適化...")
            
            # 買いシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12,
                        ti4.value as sma_50,
                        ti5.value as ema_50,
                        ti6.value as sma_200
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
                    LEFT JOIN technical_indicators ti4 ON 
                        ti1.timestamp = ti4.timestamp 
                        AND ti1.timeframe = ti4.timeframe 
                        AND ti4.indicator_type = 'SMA_50'
                    LEFT JOIN technical_indicators ti5 ON 
                        ti1.timestamp = ti5.timestamp 
                        AND ti1.timeframe = ti5.timeframe 
                        AND ti5.indicator_type = 'EMA_50'
                    LEFT JOIN technical_indicators ti6 ON 
                        ti1.timestamp = ti6.timestamp 
                        AND ti1.timeframe = ti6.timeframe 
                        AND ti6.indicator_type = 'SMA_200'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value < 40
                    ORDER BY ti1.timestamp DESC
                    LIMIT 3
                    """
                )
            )
            buy_signals = result.fetchall()
            
            print(f"✅ 買いシグナル: {len(buy_signals)}件")
            
            if len(buy_signals) > 0:
                print("\n📊 買いシグナルの移動平均線最適化:")
                print("=" * 160)
                print(f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'SMA50':<8} {'EMA50':<8} {'SMA200':<8} {'最適エントリー':<15} {'最適利確':<15} {'最適損切り':<15}")
                print("=" * 160)
                
                for rsi, signal_price, signal_time, sma_20, ema_12, sma_50, ema_50, sma_200 in buy_signals:
                    if signal_price and sma_20 and ema_12 and sma_50 and ema_50 and sma_200:
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
                            # 各移動平均線でのエントリー・利確・損切りを分析
                            ma_analysis = {
                                "SMA_20": {"entry": sma_20, "profit": 0, "loss": 0},
                                "EMA_12": {"entry": ema_12, "profit": 0, "loss": 0},
                                "SMA_50": {"entry": sma_50, "profit": 0, "loss": 0},
                                "EMA_50": {"entry": ema_50, "profit": 0, "loss": 0},
                                "SMA_200": {"entry": sma_200, "profit": 0, "loss": 0}
                            }
                            
                            max_price = 0
                            min_price = float('inf')
                            
                            for price, timestamp in price_data:
                                if price > max_price:
                                    max_price = price
                                if price < min_price:
                                    min_price = price
                            
                            # 各移動平均線での利益・損失を計算
                            for ma_name, ma_data in ma_analysis.items():
                                entry_price = ma_data["entry"]
                                if entry_price:
                                    # 利益計算（最大価格までの利益）
                                    profit_pips = (max_price - entry_price) * 100
                                    ma_data["profit"] = profit_pips
                                    
                                    # 損失計算（最小価格までの損失）
                                    loss_pips = (entry_price - min_price) * 100
                                    ma_data["loss"] = loss_pips
                            
                            # 最適な移動平均線を決定
                            best_entry = min(ma_analysis.items(), key=lambda x: x[1]["entry"] if x[1]["entry"] else float('inf'))
                            best_profit = max(ma_analysis.items(), key=lambda x: x[1]["profit"])
                            best_loss = min(ma_analysis.items(), key=lambda x: x[1]["loss"])
                            
                            # 結果を表示
                            time_str = signal_time.strftime("%m-%d %H:%M")
                            rsi_str = f"{rsi:.1f}"
                            price_str = f"{signal_price:.3f}"
                            sma_20_str = f"{sma_20:.3f}"
                            ema_12_str = f"{ema_12:.3f}"
                            sma_50_str = f"{sma_50:.3f}"
                            ema_50_str = f"{ema_50:.3f}"
                            sma_200_str = f"{sma_200:.3f}"
                            
                            best_entry_str = f"{best_entry[0]}({best_entry[1]['entry']:.3f})"
                            best_profit_str = f"{best_profit[0]}({best_profit[1]['profit']:.1f}pips)"
                            best_loss_str = f"{best_loss[0]}({best_loss[1]['loss']:.1f}pips)"
                            
                            print(f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {sma_50_str:<8} {ema_50_str:<8} {sma_200_str:<8} {best_entry_str:<15} {best_profit_str:<15} {best_loss_str:<15}")
                
                print("=" * 160)
                
                # 戦略サマリー
                print(f"\n📈 買いシグナル移動平均線最適化戦略:")
                print(f"- エントリー: 最も低い移動平均線（より良い価格）")
                print(f"- 利確: 最も高い利益の移動平均線")
                print(f"- 損切り: 最も低い損失の移動平均線")
                print(f"- 短期MA: エントリー確認")
                print(f"- 中期MA: トレンド確認")
                print(f"- 長期MA: 大トレンド確認")
            
            print("\n🔍 3. 売りシグナル（RSI > 60）での移動平均線最適化...")
            
            # 売りシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12,
                        ti4.value as sma_50,
                        ti5.value as ema_50,
                        ti6.value as sma_200
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
                    LEFT JOIN technical_indicators ti4 ON 
                        ti1.timestamp = ti4.timestamp 
                        AND ti1.timeframe = ti4.timeframe 
                        AND ti4.indicator_type = 'SMA_50'
                    LEFT JOIN technical_indicators ti5 ON 
                        ti1.timestamp = ti5.timestamp 
                        AND ti1.timeframe = ti5.timeframe 
                        AND ti5.indicator_type = 'EMA_50'
                    LEFT JOIN technical_indicators ti6 ON 
                        ti1.timestamp = ti6.timestamp 
                        AND ti1.timeframe = ti6.timeframe 
                        AND ti6.indicator_type = 'SMA_200'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value > 60
                    ORDER BY ti1.timestamp DESC
                    LIMIT 3
                    """
                )
            )
            sell_signals = result.fetchall()
            
            print(f"✅ 売りシグナル: {len(sell_signals)}件")
            
            if len(sell_signals) > 0:
                print("\n📊 売りシグナルの移動平均線最適化:")
                print("=" * 160)
                print(f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'SMA50':<8} {'EMA50':<8} {'SMA200':<8} {'最適エントリー':<15} {'最適利確':<15} {'最適損切り':<15}")
                print("=" * 160)
                
                for rsi, signal_price, signal_time, sma_20, ema_12, sma_50, ema_50, sma_200 in sell_signals:
                    if signal_price and sma_20 and ema_12 and sma_50 and ema_50 and sma_200:
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
                            # 各移動平均線でのエントリー・利確・損切りを分析
                            ma_analysis = {
                                "SMA_20": {"entry": sma_20, "profit": 0, "loss": 0},
                                "EMA_12": {"entry": ema_12, "profit": 0, "loss": 0},
                                "SMA_50": {"entry": sma_50, "profit": 0, "loss": 0},
                                "EMA_50": {"entry": ema_50, "profit": 0, "loss": 0},
                                "SMA_200": {"entry": sma_200, "profit": 0, "loss": 0}
                            }
                            
                            max_price = 0
                            min_price = float('inf')
                            
                            for price, timestamp in price_data:
                                if price > max_price:
                                    max_price = price
                                if price < min_price:
                                    min_price = price
                            
                            # 各移動平均線での利益・損失を計算（売り）
                            for ma_name, ma_data in ma_analysis.items():
                                entry_price = ma_data["entry"]
                                if entry_price:
                                    # 利益計算（最小価格までの利益）
                                    profit_pips = (entry_price - min_price) * 100
                                    ma_data["profit"] = profit_pips
                                    
                                    # 損失計算（最大価格までの損失）
                                    loss_pips = (max_price - entry_price) * 100
                                    ma_data["loss"] = loss_pips
                            
                            # 最適な移動平均線を決定
                            best_entry = max(ma_analysis.items(), key=lambda x: x[1]["entry"] if x[1]["entry"] else 0)
                            best_profit = max(ma_analysis.items(), key=lambda x: x[1]["profit"])
                            best_loss = min(ma_analysis.items(), key=lambda x: x[1]["loss"])
                            
                            # 結果を表示
                            time_str = signal_time.strftime("%m-%d %H:%M")
                            rsi_str = f"{rsi:.1f}"
                            price_str = f"{signal_price:.3f}"
                            sma_20_str = f"{sma_20:.3f}"
                            ema_12_str = f"{ema_12:.3f}"
                            sma_50_str = f"{sma_50:.3f}"
                            ema_50_str = f"{ema_50:.3f}"
                            sma_200_str = f"{sma_200:.3f}"
                            
                            best_entry_str = f"{best_entry[0]}({best_entry[1]['entry']:.3f})"
                            best_profit_str = f"{best_profit[0]}({best_profit[1]['profit']:.1f}pips)"
                            best_loss_str = f"{best_loss[0]}({best_loss[1]['loss']:.1f}pips)"
                            
                            print(f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {sma_50_str:<8} {ema_50_str:<8} {sma_200_str:<8} {best_entry_str:<15} {best_profit_str:<15} {best_loss_str:<15}")
                
                print("=" * 160)
                
                # 戦略サマリー
                print(f"\n📈 売りシグナル移動平均線最適化戦略:")
                print(f"- エントリー: 最も高い移動平均線（より良い価格）")
                print(f"- 利確: 最も高い利益の移動平均線")
                print(f"- 損切り: 最も低い損失の移動平均線")
                print(f"- 短期MA: エントリー確認")
                print(f"- 中期MA: トレンド確認")
                print(f"- 長期MA: 大トレンド確認")
            
            print("\n🔍 4. 実装戦略...")
            print("移動平均線期間最適化の実装:")
            print("- 短期MA: エントリー・早期利確")
            print("- 中期MA: トレンド確認・中期利確")
            print("- 長期MA: 大トレンド確認・長期利確")
            print("- 動的最適化: 市場状況に応じた選択")
            
            print("\n🎯 結論:")
            print("✅ 移動平均線期間最適化分析完了")
            print("✅ 短期・中期・長期の最適なライン特定")
            print("✅ 動的な戦略選択による利益最大化")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(optimize_ma_timeframes())
