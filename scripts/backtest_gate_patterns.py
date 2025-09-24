#!/usr/bin/env python3
"""
三層ゲートパターンのバックテストスクリプト
過去のデータを使用してGATE 1-3のパターン設定をテストする
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import Dict, List, Any

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.data_persistence.core.database import DatabaseManager
from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.llm_analysis.core.pattern_loader import PatternLoader

class GatePatternBacktester:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.pattern_loader = PatternLoader()
        self.three_gate_engine = ThreeGateEngine()
        
    async def initialize(self):
        """初期化"""
        await self.db_manager.initialize()
        print("✅ バックテスター初期化完了")
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> Dict[str, pd.DataFrame]:
        """過去N日間のデータを取得"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        query = """
        SELECT timestamp, open, high, low, close, volume, timeframe
        FROM price_data 
        WHERE symbol = %s 
        AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp ASC
        """
        
        async with self.db_manager.get_connection() as conn:
            result = await conn.fetch(query, symbol, start_time, end_time)
        
        # 時間足別にデータを分離
        data_by_timeframe = {}
        for row in result:
            timeframe = row['timeframe']
            if timeframe not in data_by_timeframe:
                data_by_timeframe[timeframe] = []
            
            data_by_timeframe[timeframe].append({
                'timestamp': row['timestamp'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume']) if row['volume'] else 0.0
            })
        
        # DataFrameに変換
        df_data = {}
        for timeframe, records in data_by_timeframe.items():
            if records:
                df = pd.DataFrame(records)
                df.set_index('timestamp', inplace=True)
                df_data[timeframe] = df
        
        return df_data
    
    async def test_gate_patterns(self, symbol: str = "USDJPY=X", days: int = 7):
        """GATE パターンをテスト"""
        print(f"🚀 {symbol} の過去{days}日間でGATEパターンをテスト開始")
        
        # 過去データを取得
        historical_data = await self.get_historical_data(symbol, days)
        
        if not historical_data:
            print("❌ 過去データが見つかりません")
            return
        
        print(f"📊 取得した時間足: {list(historical_data.keys())}")
        
        # 各時間足のデータ数を表示
        for timeframe, df in historical_data.items():
            print(f"  - {timeframe}: {len(df)}件")
        
        # 最新のデータポイントでテスト
        test_results = []
        
        for timeframe in ['1d', '4h', '1h', '5m']:
            if timeframe in historical_data:
                df = historical_data[timeframe]
                if len(df) > 0:
                    # 最新のデータポイントを取得
                    latest_data = df.iloc[-1]
                    
                    # テクニカル指標を計算
                    indicators = await self.technical_calculator.calculate_all_indicators({timeframe: df})
                    
                    # データを統合
                    test_data = {
                        f"{timeframe}_close": latest_data['close'],
                        f"{timeframe}_open": latest_data['open'],
                        f"{timeframe}_high": latest_data['high'],
                        f"{timeframe}_low": latest_data['low'],
                        f"{timeframe}_volume": latest_data['volume'],
                        **indicators
                    }
                    
                    # GATE評価を実行
                    result = await self.three_gate_engine.evaluate(test_data)
                    
                    test_results.append({
                        'timeframe': timeframe,
                        'timestamp': latest_data.name,
                        'price': latest_data['close'],
                        'result': result
                    })
                    
                    print(f"\n📈 {timeframe} テスト結果:")
                    print(f"  時刻: {latest_data.name}")
                    print(f"  価格: {latest_data['close']:.5f}")
                    if result:
                        print(f"  シグナル: {result.signal_type}")
                        print(f"  信頼度: {result.confidence:.2f}")
                        print(f"  エントリー: {result.entry_price:.5f}")
                        print(f"  ストップロス: {result.stop_loss:.5f}")
                    else:
                        print("  シグナル: なし")
        
        return test_results
    
    async def test_specific_scenarios(self, symbol: str = "USDJPY=X"):
        """特定のシナリオをテスト"""
        print(f"\n🎯 {symbol} の特定シナリオテスト")
        
        # 異なる期間のデータをテスト
        scenarios = [
            {"name": "直近1日", "days": 1},
            {"name": "直近3日", "days": 3},
            {"name": "直近7日", "days": 7},
            {"name": "直近14日", "days": 14}
        ]
        
        for scenario in scenarios:
            print(f"\n📊 {scenario['name']}のテスト:")
            results = await self.test_gate_patterns(symbol, scenario['days'])
            
            if results:
                signal_count = sum(1 for r in results if r['result'] and r['result'].signal_type)
                print(f"  シグナル生成数: {signal_count}/{len(results)}")
    
    async def analyze_pattern_performance(self, symbol: str = "USDJPY=X", days: int = 30):
        """パターンの性能分析"""
        print(f"\n📊 {symbol} のパターン性能分析（過去{days}日間）")
        
        historical_data = await self.get_historical_data(symbol, days)
        
        if not historical_data:
            print("❌ データが見つかりません")
            return
        
        # 各時間足でパターンの通過率を分析
        pattern_stats = {
            'gate1_passed': 0,
            'gate2_passed': 0,
            'gate3_passed': 0,
            'signals_generated': 0,
            'total_tests': 0
        }
        
        # 5m足のデータで詳細分析
        if '5m' in historical_data:
            df_5m = historical_data['5m']
            print(f"📈 5m足データ: {len(df_5m)}件")
            
            # 最新100件でテスト
            test_data_points = min(100, len(df_5m))
            for i in range(-test_data_points, 0):
                data_point = df_5m.iloc[i]
                
                # その時点までのデータでテクニカル指標を計算
                historical_up_to_point = df_5m.iloc[:i+1]
                if len(historical_up_to_point) < 50:  # 十分なデータがない場合はスキップ
                    continue
                
                indicators = await self.technical_calculator.calculate_all_indicators({'5m': historical_up_to_point})
                
                test_data = {
                    '5m_close': data_point['close'],
                    '5m_open': data_point['open'],
                    '5m_high': data_point['high'],
                    '5m_low': data_point['low'],
                    '5m_volume': data_point['volume'],
                    **indicators
                }
                
                result = await self.three_gate_engine.evaluate(test_data)
                pattern_stats['total_tests'] += 1
                
                if result:
                    if result.gate1_passed:
                        pattern_stats['gate1_passed'] += 1
                    if result.gate2_passed:
                        pattern_stats['gate2_passed'] += 1
                    if result.gate3_passed:
                        pattern_stats['gate3_passed'] += 1
                    if result.signal_type:
                        pattern_stats['signals_generated'] += 1
        
        # 統計を表示
        print(f"\n📊 パターン性能統計:")
        print(f"  総テスト数: {pattern_stats['total_tests']}")
        print(f"  GATE 1通過率: {pattern_stats['gate1_passed']}/{pattern_stats['total_tests']} ({pattern_stats['gate1_passed']/max(pattern_stats['total_tests'], 1)*100:.1f}%)")
        print(f"  GATE 2通過率: {pattern_stats['gate2_passed']}/{pattern_stats['total_tests']} ({pattern_stats['gate2_passed']/max(pattern_stats['total_tests'], 1)*100:.1f}%)")
        print(f"  GATE 3通過率: {pattern_stats['gate3_passed']}/{pattern_stats['total_tests']} ({pattern_stats['gate3_passed']/max(pattern_stats['total_tests'], 1)*100:.1f}%)")
        print(f"  シグナル生成率: {pattern_stats['signals_generated']}/{pattern_stats['total_tests']} ({pattern_stats['signals_generated']/max(pattern_stats['total_tests'], 1)*100:.1f}%)")

async def main():
    """メイン関数"""
    backtester = GatePatternBacktester()
    await backtester.initialize()
    
    try:
        # 基本的なテスト
        await backtester.test_gate_patterns("USDJPY=X", 7)
        
        # 特定シナリオのテスト
        await backtester.test_specific_scenarios("USDJPY=X")
        
        # パターン性能分析
        await backtester.analyze_pattern_performance("USDJPY=X", 30)
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await backtester.db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
