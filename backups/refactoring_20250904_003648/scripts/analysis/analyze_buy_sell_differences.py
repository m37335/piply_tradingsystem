#!/usr/bin/env python3
"""
買い売り差異分析スクリプト

買いと売りで結果が異なる理由を分析し、より良い条件設定を探す
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


async def analyze_buy_sell_differences():
    """買い売り差異を分析"""
    print("=" * 80)
    print("🔍 買い売り差異分析 - 条件最適化")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 現在の条件での買い売り分析...")
            
            # 現在の条件で買いと売りを分けて分析
            conditions = [
                {"name": "現在の条件", "buy_rsi": 55, "sell_rsi": 45},
                {"name": "対称条件1", "buy_rsi": 50, "sell_rsi": 50},
                {"name": "対称条件2", "buy_rsi": 45, "sell_rsi": 55},
                {"name": "対称条件3", "buy_rsi": 40, "sell_rsi": 60},
                {"name": "買い重視", "buy_rsi": 60, "sell_rsi": 40},
                {"name": "売り重視", "buy_rsi": 40, "sell_rsi": 60},
                {"name": "緩い条件", "buy_rsi": 60, "sell_rsi": 40},
                {"name": "厳しい条件", "buy_rsi": 35, "sell_rsi": 65},
            ]
            
            all_results = []
            
            for condition in conditions:
                print(f"\n🔍 2. {condition['name']}のテスト...")
                print(f"   買い条件: RSI < {condition['buy_rsi']}")
                print(f"   売り条件: RSI > {condition['sell_rsi']}")
                
                # 買いシグナルのみ
                buy_result = await db_session.execute(
                    text(
                        """
                        SELECT 
                            ti1.value as rsi_value,
                            ti2.value as sma_value,
                            ti3.value as ema_12,
                            ti4.value as ema_26,
                            ti5.value as atr_value,
                            pd.close_price as signal_price,
                            ti1.timestamp as signal_time,
                            ti1.timeframe
                        FROM technical_indicators ti1
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
                            AND ti4.indicator_type = 'EMA_26'
                        LEFT JOIN technical_indicators ti5 ON 
                            ti1.timestamp = ti5.timestamp 
                            AND ti1.timeframe = ti5.timeframe 
                            AND ti5.indicator_type = 'ATR'
                        LEFT JOIN price_data pd ON 
                            ti1.timestamp = pd.timestamp
                            AND ti1.currency_pair = pd.currency_pair
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.value < :buy_rsi 
                        AND pd.close_price > ti2.value 
                        AND ti3.value > ti4.value 
                        AND 0.01 <= ti5.value 
                        AND ti5.value <= 0.10
                        ORDER BY ti1.timestamp DESC
                        LIMIT 20
                        """
                    ),
                    {"buy_rsi": condition['buy_rsi']}
                )
                buy_signals = buy_result.fetchall()
                
                # 売りシグナルのみ
                sell_result = await db_session.execute(
                    text(
                        """
                        SELECT 
                            ti1.value as rsi_value,
                            ti2.value as sma_value,
                            ti3.value as ema_12,
                            ti4.value as ema_26,
                            ti5.value as atr_value,
                            pd.close_price as signal_price,
                            ti1.timestamp as signal_time,
                            ti1.timeframe
                        FROM technical_indicators ti1
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
                            AND ti4.indicator_type = 'EMA_26'
                        LEFT JOIN technical_indicators ti5 ON 
                            ti1.timestamp = ti5.timestamp 
                            AND ti1.timeframe = ti5.timeframe 
                            AND ti5.indicator_type = 'ATR'
                        LEFT JOIN price_data pd ON 
                            ti1.timestamp = pd.timestamp
                            AND ti1.currency_pair = pd.currency_pair
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.value > :sell_rsi 
                        AND pd.close_price < ti2.value 
                        AND ti3.value < ti4.value 
                        AND 0.01 <= ti5.value 
                        AND ti5.value <= 0.10
                        ORDER BY ti1.timestamp DESC
                        LIMIT 20
                        """
                    ),
                    {"sell_rsi": condition['sell_rsi']}
                )
                sell_signals = sell_result.fetchall()
                
                print(f"   買いシグナル: {len(buy_signals)}件")
                print(f"   売りシグナル: {len(sell_signals)}件")
                
                # 買いシグナルのパフォーマンス分析
                buy_profits_1h = []
                buy_profits_4h = []
                buy_profits_1d = []
                
                for rsi, sma, ema_12, ema_26, atr, signal_price, signal_time, timeframe in buy_signals:
                    if rsi and sma and ema_12 and ema_26 and atr and signal_price:
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
                
                # 売りシグナルのパフォーマンス分析
                sell_profits_1h = []
                sell_profits_4h = []
                sell_profits_1d = []
                
                for rsi, sma, ema_12, ema_26, atr, signal_price, signal_time, timeframe in sell_signals:
                    if rsi and sma and ema_12 and ema_26 and atr and signal_price:
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
                    "name": condition['name'],
                    "buy_rsi": condition['buy_rsi'],
                    "sell_rsi": condition['sell_rsi'],
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
            print("\n🔍 3. 条件別比較分析...")
            print("=" * 140)
            print(f"{'条件名':<12} {'買いRSI':<8} {'売りRSI':<8} {'買い数':<6} {'売り数':<6} {'買い1時間':<12} {'売り1時間':<12} {'買い4時間':<12} {'売り4時間':<12} {'買い1日':<12} {'売り1日':<12}")
            print("=" * 140)
            
            for result in all_results:
                print(f"{result['name']:<12} {result['buy_rsi']:<8} {result['sell_rsi']:<8} {result['buy_count']:<6} {result['sell_count']:<6} {result['buy_avg_1h']:<12.2f} {result['sell_avg_1h']:<12.2f} {result['buy_avg_4h']:<12.2f} {result['sell_avg_4h']:<12.2f} {result['buy_avg_1d']:<12.2f} {result['sell_avg_1d']:<12.2f}")
            
            print("=" * 140)
            
            # 最適条件の特定
            print("\n🎯 最適条件の特定...")
            
            # 1時間後の最適条件
            best_1h = max(all_results, key=lambda x: (x['buy_avg_1h'] + x['sell_avg_1h']) / 2)
            print(f"✅ 1時間後最適: {best_1h['name']} (買い{best_1h['buy_avg_1h']:.2f}, 売り{best_1h['sell_avg_1h']:.2f})")
            
            # 4時間後の最適条件
            best_4h = max(all_results, key=lambda x: (x['buy_avg_4h'] + x['sell_avg_4h']) / 2)
            print(f"✅ 4時間後最適: {best_4h['name']} (買い{best_4h['buy_avg_4h']:.2f}, 売り{best_4h['sell_avg_4h']:.2f})")
            
            # 1日後の最適条件
            best_1d = max(all_results, key=lambda x: (x['buy_avg_1d'] + x['sell_avg_1d']) / 2)
            print(f"✅ 1日後最適: {best_1d['name']} (買い{best_1d['buy_avg_1d']:.2f}, 売り{best_1d['sell_avg_1d']:.2f})")
            
            # 総合最適条件（全時間軸の平均）
            best_overall = max(all_results, key=lambda x: (
                x['buy_avg_1h'] + x['sell_avg_1h'] + 
                x['buy_avg_4h'] + x['sell_avg_4h'] + 
                x['buy_avg_1d'] + x['sell_avg_1d']
            ) / 6)
            print(f"✅ 総合最適: {best_overall['name']} (全時間軸平均)")
            
            print("\n💡 買い売り差異の理由分析:")
            print("1. 市場の非対称性: 上昇トレンドと下降トレンドの性質が異なる")
            print("2. 時間軸の影響: 短期的と長期的で市場の動きが変化")
            print("3. RSIの特性: 過売りと過買いの反応速度が異なる")
            print("4. トレンドの持続性: 上昇トレンドと下降トレンドの持続時間が異なる")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_buy_sell_differences())
