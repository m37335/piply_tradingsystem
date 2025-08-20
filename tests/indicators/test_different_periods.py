#!/usr/bin/env python3
"""
異なる期間テストスクリプト

SMAとEMAの異なる期間を考慮して条件をテスト
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


async def test_different_periods():
    """異なる期間をテスト"""
    print("=" * 80)
    print("🔍 異なる期間テスト - SMA/EMA期間最適化")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 利用可能な期間の確認...")
            
            # 利用可能なSMA期間を確認
            sma_result = await db_session.execute(
                text(
                    """
                    SELECT DISTINCT indicator_type
                    FROM technical_indicators
                    WHERE indicator_type LIKE 'SMA_%'
                    ORDER BY indicator_type
                    """
                )
            )
            sma_periods = [row[0] for row in sma_result.fetchall()]
            print(f"✅ 利用可能なSMA期間: {sma_periods}")
            
            # 利用可能なEMA期間を確認
            ema_result = await db_session.execute(
                text(
                    """
                    SELECT DISTINCT indicator_type
                    FROM technical_indicators
                    WHERE indicator_type LIKE 'EMA_%'
                    ORDER BY indicator_type
                    """
                )
            )
            ema_periods = [row[0] for row in ema_result.fetchall()]
            print(f"✅ 利用可能なEMA期間: {ema_periods}")
            
            print("\n🔍 2. 異なる期間の組み合わせテスト...")
            
            # テストする期間の組み合わせ
            period_combinations = [
                {"name": "現在(20/12-26)", "sma": "SMA_20", "ema_short": "EMA_12", "ema_long": "EMA_26"},
                {"name": "短期(10/5-12)", "sma": "SMA_10", "ema_short": "EMA_5", "ema_long": "EMA_12"},
                {"name": "中期(30/12-26)", "sma": "SMA_30", "ema_short": "EMA_12", "ema_long": "EMA_26"},
                {"name": "長期(50/26-50)", "sma": "SMA_50", "ema_short": "EMA_26", "ema_long": "EMA_50"},
                {"name": "混合1(20/5-26)", "sma": "SMA_20", "ema_short": "EMA_5", "ema_long": "EMA_26"},
                {"name": "混合2(30/12-50)", "sma": "SMA_30", "ema_short": "EMA_12", "ema_long": "EMA_50"},
            ]
            
            # 利用可能な期間のみをフィルタリング
            available_combinations = []
            for combo in period_combinations:
                if (combo["sma"] in sma_periods and 
                    combo["ema_short"] in ema_periods and 
                    combo["ema_long"] in ema_periods):
                    available_combinations.append(combo)
            
            print(f"✅ テスト可能な組み合わせ: {len(available_combinations)}種類")
            
            all_results = []
            
            for combo in available_combinations:
                print(f"\n🔍 3. {combo['name']}のテスト...")
                print(f"   SMA: {combo['sma']}")
                print(f"   EMA短期: {combo['ema_short']}")
                print(f"   EMA長期: {combo['ema_long']}")
                
                # 買いシグナルのテスト
                buy_result = await db_session.execute(
                    text(
                        f"""
                        SELECT 
                            ti1.value as rsi_value,
                            ti2.value as sma_value,
                            ti3.value as ema_short,
                            ti4.value as ema_long,
                            ti5.value as atr_value,
                            pd.close_price as signal_price,
                            ti1.timestamp as signal_time,
                            ti1.timeframe
                        FROM technical_indicators ti1
                        LEFT JOIN technical_indicators ti2 ON 
                            ti1.timestamp = ti2.timestamp 
                            AND ti1.timeframe = ti2.timeframe 
                            AND ti2.indicator_type = '{combo["sma"]}'
                        LEFT JOIN technical_indicators ti3 ON 
                            ti1.timestamp = ti3.timestamp 
                            AND ti1.timeframe = ti3.timeframe 
                            AND ti3.indicator_type = '{combo["ema_short"]}'
                        LEFT JOIN technical_indicators ti4 ON 
                            ti1.timestamp = ti4.timestamp 
                            AND ti1.timeframe = ti4.timeframe 
                            AND ti4.indicator_type = '{combo["ema_long"]}'
                        LEFT JOIN technical_indicators ti5 ON 
                            ti1.timestamp = ti5.timestamp 
                            AND ti1.timeframe = ti5.timeframe 
                            AND ti5.indicator_type = 'ATR'
                        LEFT JOIN price_data pd ON 
                            ti1.timestamp = pd.timestamp
                            AND ti1.currency_pair = pd.currency_pair
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.value < 55 
                        AND pd.close_price > ti2.value 
                        AND ti3.value > ti4.value 
                        AND 0.01 <= ti5.value 
                        AND ti5.value <= 0.10
                        ORDER BY ti1.timestamp DESC
                        LIMIT 15
                        """
                    )
                )
                buy_signals = buy_result.fetchall()
                
                # 売りシグナルのテスト
                sell_result = await db_session.execute(
                    text(
                        f"""
                        SELECT 
                            ti1.value as rsi_value,
                            ti2.value as sma_value,
                            ti3.value as ema_short,
                            ti4.value as ema_long,
                            ti5.value as atr_value,
                            pd.close_price as signal_price,
                            ti1.timestamp as signal_time,
                            ti1.timeframe
                        FROM technical_indicators ti1
                        LEFT JOIN technical_indicators ti2 ON 
                            ti1.timestamp = ti2.timestamp 
                            AND ti1.timeframe = ti2.timeframe 
                            AND ti2.indicator_type = '{combo["sma"]}'
                        LEFT JOIN technical_indicators ti3 ON 
                            ti1.timestamp = ti3.timestamp 
                            AND ti1.timeframe = ti3.timeframe 
                            AND ti3.indicator_type = '{combo["ema_short"]}'
                        LEFT JOIN technical_indicators ti4 ON 
                            ti1.timestamp = ti4.timestamp 
                            AND ti1.timeframe = ti4.timeframe 
                            AND ti4.indicator_type = '{combo["ema_long"]}'
                        LEFT JOIN technical_indicators ti5 ON 
                            ti1.timestamp = ti5.timestamp 
                            AND ti1.timeframe = ti5.timeframe 
                            AND ti5.indicator_type = 'ATR'
                        LEFT JOIN price_data pd ON 
                            ti1.timestamp = pd.timestamp
                            AND ti1.currency_pair = pd.currency_pair
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.value > 45 
                        AND pd.close_price < ti2.value 
                        AND ti3.value < ti4.value 
                        AND 0.01 <= ti5.value 
                        AND ti5.value <= 0.10
                        ORDER BY ti1.timestamp DESC
                        LIMIT 15
                        """
                    )
                )
                sell_signals = sell_result.fetchall()
                
                print(f"   買いシグナル: {len(buy_signals)}件")
                print(f"   売りシグナル: {len(sell_signals)}件")
                
                # パフォーマンス分析
                buy_profits_1h = []
                buy_profits_4h = []
                buy_profits_1d = []
                sell_profits_1h = []
                sell_profits_4h = []
                sell_profits_1d = []
                
                # 買いシグナルの利益計算
                for rsi, sma, ema_short, ema_long, atr, signal_price, signal_time, timeframe in buy_signals:
                    if rsi and sma and ema_short and ema_long and atr and signal_price:
                        for hours in [1, 4, 24]:
                            future_time = signal_time + timedelta(hours=hours)
                            
                            result = await db_session.execute(
                                text(
                                    """
                                    SELECT close_price
                                    FROM price_data
                                    WHERE timestamp >= :future_time
                                    AND currency_pair = 'USD/JPY'
                                    ORDER BY timestamp ASC
                                    LIMIT 1
                                    """
                                ),
                                {"future_time": future_time}
                            )
                            future_price_result = result.fetchone()
                            
                            if future_price_result:
                                future_price = future_price_result[0]
                                profit_pips = (future_price - signal_price) * 100
                                
                                if hours == 1:
                                    buy_profits_1h.append(profit_pips)
                                elif hours == 4:
                                    buy_profits_4h.append(profit_pips)
                                elif hours == 24:
                                    buy_profits_1d.append(profit_pips)
                
                # 売りシグナルの利益計算
                for rsi, sma, ema_short, ema_long, atr, signal_price, signal_time, timeframe in sell_signals:
                    if rsi and sma and ema_short and ema_long and atr and signal_price:
                        for hours in [1, 4, 24]:
                            future_time = signal_time + timedelta(hours=hours)
                            
                            result = await db_session.execute(
                                text(
                                    """
                                    SELECT close_price
                                    FROM price_data
                                    WHERE timestamp >= :future_time
                                    AND currency_pair = 'USD/JPY'
                                    ORDER BY timestamp ASC
                                    LIMIT 1
                                    """
                                ),
                                {"future_time": future_time}
                            )
                            future_price_result = result.fetchone()
                            
                            if future_price_result:
                                future_price = future_price_result[0]
                                profit_pips = (signal_price - future_price) * 100
                                
                                if hours == 1:
                                    sell_profits_1h.append(profit_pips)
                                elif hours == 4:
                                    sell_profits_4h.append(profit_pips)
                                elif hours == 24:
                                    sell_profits_1d.append(profit_pips)
                
                # 統計計算
                result_data = {
                    "name": combo['name'],
                    "sma": combo['sma'],
                    "ema_short": combo['ema_short'],
                    "ema_long": combo['ema_long'],
                    "buy_count": len(buy_signals),
                    "sell_count": len(sell_signals),
                }
                
                # 買い統計
                if buy_profits_1h:
                    result_data["buy_avg_1h"] = sum(buy_profits_1h) / len(buy_profits_1h)
                    result_data["buy_win_rate_1h"] = len([p for p in buy_profits_1h if p > 0]) / len(buy_profits_1h) * 100
                else:
                    result_data["buy_avg_1h"] = 0
                    result_data["buy_win_rate_1h"] = 0
                
                if buy_profits_4h:
                    result_data["buy_avg_4h"] = sum(buy_profits_4h) / len(buy_profits_4h)
                    result_data["buy_win_rate_4h"] = len([p for p in buy_profits_4h if p > 0]) / len(buy_profits_4h) * 100
                else:
                    result_data["buy_avg_4h"] = 0
                    result_data["buy_win_rate_4h"] = 0
                
                if buy_profits_1d:
                    result_data["buy_avg_1d"] = sum(buy_profits_1d) / len(buy_profits_1d)
                    result_data["buy_win_rate_1d"] = len([p for p in buy_profits_1d if p > 0]) / len(buy_profits_1d) * 100
                else:
                    result_data["buy_avg_1d"] = 0
                    result_data["buy_win_rate_1d"] = 0
                
                # 売り統計
                if sell_profits_1h:
                    result_data["sell_avg_1h"] = sum(sell_profits_1h) / len(sell_profits_1h)
                    result_data["sell_win_rate_1h"] = len([p for p in sell_profits_1h if p > 0]) / len(sell_profits_1h) * 100
                else:
                    result_data["sell_avg_1h"] = 0
                    result_data["sell_win_rate_1h"] = 0
                
                if sell_profits_4h:
                    result_data["sell_avg_4h"] = sum(sell_profits_4h) / len(sell_profits_4h)
                    result_data["sell_win_rate_4h"] = len([p for p in sell_profits_4h if p > 0]) / len(sell_profits_4h) * 100
                else:
                    result_data["sell_avg_4h"] = 0
                    result_data["sell_win_rate_4h"] = 0
                
                if sell_profits_1d:
                    result_data["sell_avg_1d"] = sum(sell_profits_1d) / len(sell_profits_1d)
                    result_data["sell_win_rate_1d"] = len([p for p in sell_profits_1d if p > 0]) / len(sell_profits_1d) * 100
                else:
                    result_data["sell_avg_1d"] = 0
                    result_data["sell_win_rate_1d"] = 0
                
                all_results.append(result_data)
                
                print(f"   買い - 1時間: {result_data['buy_avg_1h']:.2f}pips ({result_data['buy_win_rate_1h']:.1f}%)")
                print(f"   買い - 4時間: {result_data['buy_avg_4h']:.2f}pips ({result_data['buy_win_rate_4h']:.1f}%)")
                print(f"   買い - 1日: {result_data['buy_avg_1d']:.2f}pips ({result_data['buy_win_rate_1d']:.1f}%)")
                print(f"   売り - 1時間: {result_data['sell_avg_1h']:.2f}pips ({result_data['sell_win_rate_1h']:.1f}%)")
                print(f"   売り - 4時間: {result_data['sell_avg_4h']:.2f}pips ({result_data['sell_win_rate_4h']:.1f}%)")
                print(f"   売り - 1日: {result_data['sell_avg_1d']:.2f}pips ({result_data['sell_win_rate_1d']:.1f}%)")
            
            # 結果の比較分析
            print("\n🔍 4. 期間別比較分析...")
            print("=" * 120)
            print(f"{'期間名':<15} {'SMA':<8} {'EMA短':<8} {'EMA長':<8} {'買い数':<6} {'売り数':<6} {'買い1時間':<12} {'売り1時間':<12} {'買い4時間':<12} {'売り4時間':<12} {'買い1日':<12} {'売り1日':<12}")
            print("=" * 120)
            
            for result in all_results:
                print(f"{result['name']:<15} {result['sma']:<8} {result['ema_short']:<8} {result['ema_long']:<8} {result['buy_count']:<6} {result['sell_count']:<6} {result['buy_avg_1h']:<12.2f} {result['sell_avg_1h']:<12.2f} {result['buy_avg_4h']:<12.2f} {result['sell_avg_4h']:<12.2f} {result['buy_avg_1d']:<12.2f} {result['sell_avg_1d']:<12.2f}")
            
            print("=" * 120)
            
            # 最適期間の特定
            print("\n🎯 最適期間の特定...")
            
            # 1時間後の最適期間
            best_1h = max(all_results, key=lambda x: (x['buy_avg_1h'] + x['sell_avg_1h']) / 2)
            print(f"✅ 1時間後最適: {best_1h['name']} (買い{best_1h['buy_avg_1h']:.2f}, 売り{best_1h['sell_avg_1h']:.2f})")
            
            # 4時間後の最適期間
            best_4h = max(all_results, key=lambda x: (x['buy_avg_4h'] + x['sell_avg_4h']) / 2)
            print(f"✅ 4時間後最適: {best_4h['name']} (買い{best_4h['buy_avg_4h']:.2f}, 売り{best_4h['sell_avg_4h']:.2f})")
            
            # 1日後の最適期間
            best_1d = max(all_results, key=lambda x: (x['buy_avg_1d'] + x['sell_avg_1d']) / 2)
            print(f"✅ 1日後最適: {best_1d['name']} (買い{best_1d['buy_avg_1d']:.2f}, 売り{best_1d['sell_avg_1d']:.2f})")
            
            # 総合最適期間
            best_overall = max(all_results, key=lambda x: (
                x['buy_avg_1h'] + x['sell_avg_1h'] + 
                x['buy_avg_4h'] + x['sell_avg_4h'] + 
                x['buy_avg_1d'] + x['sell_avg_1d']
            ) / 6)
            print(f"✅ 総合最適: {best_overall['name']} (全時間軸平均)")
            
            print("\n💡 期間選択の洞察:")
            print("1. 短期期間: より敏感なシグナル、ノイズも多い")
            print("2. 長期期間: 安定したシグナル、機会は少ない")
            print("3. 混合期間: バランスの取れたシグナル")
            print("4. 時間軸との関係: 取引時間に応じた期間選択が重要")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_different_periods())
