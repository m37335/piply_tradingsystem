#!/usr/bin/env python3
"""
条件最適化スクリプト

より多くのデータで条件を最適化し、勝率が高い条件を特定します
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


async def optimize_conditions():
    """条件を最適化"""
    print("=" * 80)
    print("🔧 条件最適化 - 勝率が高い条件を特定")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 条件パターンの定義...")
            
            # テストする条件パターン
            condition_patterns = [
                # 現在の条件
                {"name": "現在の条件", "buy_rsi": 45, "sell_rsi": 55},
                # より厳しい条件
                {"name": "厳しい条件", "buy_rsi": 40, "sell_rsi": 60},
                {"name": "より厳しい条件", "buy_rsi": 35, "sell_rsi": 65},
                # より緩い条件
                {"name": "緩い条件", "buy_rsi": 50, "sell_rsi": 50},
                {"name": "より緩い条件", "buy_rsi": 55, "sell_rsi": 45},
                # 非対称条件
                {"name": "買い重視", "buy_rsi": 40, "sell_rsi": 60},
                {"name": "売り重視", "buy_rsi": 50, "sell_rsi": 50},
            ]
            
            print(f"✅ テストする条件パターン: {len(condition_patterns)}種類")
            
            results = []
            
            for pattern in condition_patterns:
                print(f"\n🔍 2. {pattern['name']}のテスト...")
                print(f"   買い条件: RSI < {pattern['buy_rsi']}")
                print(f"   売り条件: RSI > {pattern['sell_rsi']}")
                
                # シグナル発生データを取得
                result = await db_session.execute(
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
                        AND (
                            (ti1.value < :buy_rsi AND pd.close_price > ti2.value AND ti3.value > ti4.value AND 0.01 <= ti5.value AND ti5.value <= 0.10) OR
                            (ti1.value > :sell_rsi AND pd.close_price < ti2.value AND ti3.value < ti4.value AND 0.01 <= ti5.value AND ti5.value <= 0.10)
                        )
                        ORDER BY ti1.timestamp DESC
                        LIMIT 50
                        """
                    ),
                    {"buy_rsi": pattern['buy_rsi'], "sell_rsi": pattern['sell_rsi']}
                )
                signals = result.fetchall()
                
                print(f"✅ 検出されたシグナル: {len(signals)}件")
                
                if len(signals) == 0:
                    print("   ❌ シグナルなし - スキップ")
                    continue
                
                # パフォーマンス検証
                total_profit = 0
                winning_signals = 0
                losing_signals = 0
                total_profit_4h = 0
                total_profit_1d = 0
                
                for rsi, sma, ema_12, ema_26, atr, signal_price, signal_time, timeframe in signals:
                    if rsi and sma and ema_12 and ema_26 and atr and signal_price:
                        # シグナルタイプを判定
                        buy_condition = rsi < pattern['buy_rsi'] and signal_price > sma and ema_12 > ema_26 and 0.01 <= atr <= 0.10
                        sell_condition = rsi > pattern['sell_rsi'] and signal_price < sma and ema_12 < ema_26 and 0.01 <= atr <= 0.10
                        
                        signal_type = "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                        
                        # 1時間後、4時間後、1日後の価格を取得
                        time_periods = [(1, "1時間後"), (4, "4時間後"), (24, "1日後")]
                        
                        signal_profit = 0
                        signal_profit_4h = 0
                        signal_profit_1d = 0
                        
                        for hours, period_name in time_periods:
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
                                
                                # 利益計算
                                if signal_type == "BUY":
                                    profit_pips = (future_price - signal_price) * 100
                                else:  # SELL
                                    profit_pips = (signal_price - future_price) * 100
                                
                                if hours == 1:
                                    signal_profit = profit_pips
                                elif hours == 4:
                                    signal_profit_4h = profit_pips
                                elif hours == 24:
                                    signal_profit_1d = profit_pips
                        
                        # 結果を集計
                        total_profit += signal_profit
                        total_profit_4h += signal_profit_4h
                        total_profit_1d += signal_profit_1d
                        
                        if signal_profit > 0:
                            winning_signals += 1
                        else:
                            losing_signals += 1
                
                # 統計計算
                avg_profit = total_profit / len(signals)
                avg_profit_4h = total_profit_4h / len(signals)
                avg_profit_1d = total_profit_1d / len(signals)
                win_rate = (winning_signals / len(signals)) * 100
                
                result_data = {
                    "name": pattern['name'],
                    "buy_rsi": pattern['buy_rsi'],
                    "sell_rsi": pattern['sell_rsi'],
                    "total_signals": len(signals),
                    "win_rate": win_rate,
                    "avg_profit_1h": avg_profit,
                    "avg_profit_4h": avg_profit_4h,
                    "avg_profit_1d": avg_profit_1d,
                    "total_profit_1h": total_profit,
                    "total_profit_4h": total_profit_4h,
                    "total_profit_1d": total_profit_1d,
                }
                
                results.append(result_data)
                
                print(f"   勝率: {win_rate:.1f}% ({winning_signals}勝/{len(signals)}件)")
                print(f"   平均利益(1時間): {avg_profit:.2f} pips")
                print(f"   平均利益(4時間): {avg_profit_4h:.2f} pips")
                print(f"   平均利益(1日): {avg_profit_1d:.2f} pips")

            print("\n🔍 3. 結果の比較・分析...")
            
            if results:
                print("✅ 条件別パフォーマンス比較:")
                print("=" * 100)
                print(f"{'条件名':<15} {'買いRSI':<8} {'売りRSI':<8} {'シグナル数':<10} {'勝率':<8} {'1時間利益':<12} {'4時間利益':<12} {'1日利益':<12}")
                print("=" * 100)
                
                for result in results:
                    print(f"{result['name']:<15} {result['buy_rsi']:<8} {result['sell_rsi']:<8} {result['total_signals']:<10} {result['win_rate']:<8.1f} {result['avg_profit_1h']:<12.2f} {result['avg_profit_4h']:<12.2f} {result['avg_profit_1d']:<12.2f}")
                
                print("=" * 100)
                
                # 最適な条件を特定
                print("\n🎯 最適条件の特定...")
                
                # 勝率でソート
                results_by_winrate = sorted(results, key=lambda x: x['win_rate'], reverse=True)
                print(f"✅ 最高勝率: {results_by_winrate[0]['name']} ({results_by_winrate[0]['win_rate']:.1f}%)")
                
                # 1時間利益でソート
                results_by_profit_1h = sorted(results, key=lambda x: x['avg_profit_1h'], reverse=True)
                print(f"✅ 最高1時間利益: {results_by_profit_1h[0]['name']} ({results_by_profit_1h[0]['avg_profit_1h']:.2f} pips)")
                
                # 4時間利益でソート
                results_by_profit_4h = sorted(results, key=lambda x: x['avg_profit_4h'], reverse=True)
                print(f"✅ 最高4時間利益: {results_by_profit_4h[0]['name']} ({results_by_profit_4h[0]['avg_profit_4h']:.2f} pips)")
                
                # 1日利益でソート
                results_by_profit_1d = sorted(results, key=lambda x: x['avg_profit_1d'], reverse=True)
                print(f"✅ 最高1日利益: {results_by_profit_1d[0]['name']} ({results_by_profit_1d[0]['avg_profit_1d']:.2f} pips)")
                
                # 総合評価（勝率 + 利益のバランス）
                print("\n🏆 総合評価（勝率50%以上 + 利益プラス）:")
                good_strategies = [r for r in results if r['win_rate'] >= 50 and r['avg_profit_1h'] > 0]
                
                if good_strategies:
                    for strategy in good_strategies:
                        print(f"   ✅ {strategy['name']}: 勝率{strategy['win_rate']:.1f}%, 利益{strategy['avg_profit_1h']:.2f}pips")
                else:
                    print("   ❌ 条件を満たす戦略なし")

            print("\n🔍 4. 推奨アクション...")
            print("✅ 推奨アクション:")
            print("   1. 最適な条件でRSIエントリー検出器を更新")
            print("   2. より長期間のデータで検証")
            print("   3. 他のタイムフレームでの検証")
            print("   4. リスク管理パラメータの最適化")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(optimize_conditions())
