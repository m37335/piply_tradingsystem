#!/usr/bin/env python3
"""
実際の市場データでのPhase 2パターン検出検証

USD/JPYの実際のデータを使用して、Phase 2で実装した
チャートパターン検出システムの動作を検証
"""

import asyncio
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.infrastructure.analysis.notification_pattern_analyzer import NotificationPatternAnalyzer
from src.infrastructure.analysis.pattern_detectors.double_top_bottom_detector import DoubleTopBottomDetector
from src.infrastructure.analysis.pattern_detectors.flag_pattern_detector import FlagPatternDetector


def create_multi_timeframe_data(price_data: pd.DataFrame) -> Dict[str, Any]:
    """マルチタイムフレームデータを作成"""
    # 実際の実装では、各時間軸のデータを適切に集約する必要があります
    # ここでは簡易的に同じデータを使用
    return {
        "D1": {"price_data": price_data},
        "H4": {"price_data": price_data},
        "H1": {"price_data": price_data},
        "M5": {"price_data": price_data}
    }


async def test_pattern_detection_with_real_data():
    """実際のデータでパターン検出をテスト"""
    print("=== 実際の市場データでのPhase 2パターン検出検証 ===\n")
    
    # クライアントとアナライザーを初期化
    client = YahooFinanceClient()
    analyzer = NotificationPatternAnalyzer()
    
    print("✅ システム初期化完了")
    print(f"📊 登録済みパターン数: {len(analyzer.detectors)}")
    print(f"🎯 Phase 2パターン: {[k for k in analyzer.detectors.keys() if k >= 10]}\n")
    
    # 実際のUSD/JPYデータを取得
    print("📈 USD/JPYデータを取得中...")
    try:
        # 過去30日間のデータを取得
        price_data = await client.get_historical_data(
            currency_pair="USD/JPY",
            period="1mo",
            interval="1d"
        )
        
        if price_data is None or price_data.empty:
            print("❌ データ取得に失敗しました")
            return
        
        print(f"✅ データ取得成功: {len(price_data)}件")
        print(f"📅 期間: {price_data.index[0].date()} 〜 {price_data.index[-1].date()}")
        print(f"💰 価格範囲: {price_data['Close'].min():.2f} 〜 {price_data['Close'].max():.2f}\n")
        
        # データを適切な形式に変換
        formatted_data = pd.DataFrame({
            'high': price_data['High'],
            'low': price_data['Low'],
            'close': price_data['Close'],
            'open': price_data['Open']
        })
        
        # マルチタイムフレームデータを作成
        multi_timeframe_data = create_multi_timeframe_data(formatted_data)
        
        # Phase 2の各パターンを個別にテスト
        print("🔍 Phase 2パターン検出テスト開始...\n")
        
        # パターン10: ダブルトップ/ボトム
        print("=== パターン10: ダブルトップ/ボトム検出 ===")
        detector_10 = DoubleTopBottomDetector()
        result_10 = detector_10.detect(multi_timeframe_data)
        if result_10:
            print(f"✅ 検出成功: {result_10['pattern_name']}")
            print(f"📊 信頼度: {result_10['confidence_score']:.2%}")
            print(f"🎯 優先度: {result_10['priority']}")
        else:
            print("❌ パターン10は検出されませんでした")
        print()
        
        # パターン12: フラッグパターン
        print("=== パターン12: フラッグパターン検出 ===")
        detector_12 = FlagPatternDetector()
        result_12 = detector_12.detect(multi_timeframe_data)
        if result_12:
            print(f"✅ 検出成功: {result_12['pattern_name']}")
            print(f"📊 信頼度: {result_12['confidence_score']:.2%}")
            print(f"🎯 優先度: {result_12['priority']}")
        else:
            print("❌ パターン12は検出されませんでした")
        print()
        
        # 統合分析エンジンでのテスト
        print("=== 統合分析エンジンテスト ===")
        all_results = analyzer.analyze_multi_timeframe_data(multi_timeframe_data)
        
        if all_results:
            print(f"✅ 検出されたパターン数: {len(all_results)}")
            for result in all_results:
                print(f"🎯 パターン{result['pattern_number']}: {result['pattern_name']}")
                print(f"   📊 信頼度: {result['confidence_score']:.2%}")
                print(f"   🎯 優先度: {result['priority']}")
        else:
            print("❌ 統合分析ではパターンが検出されませんでした")
        
        print("\n=== 検証完了 ===")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


async def test_data_quality():
    """データ品質の確認"""
    print("=== データ品質確認 ===")
    
    client = YahooFinanceClient()
    
    try:
        # 異なる期間のデータを取得して品質を確認
        periods = [
            ("1週間", "1wk"),
            ("2週間", "2wk"),
            ("1ヶ月", "1mo"),
            ("3ヶ月", "3mo")
        ]
        
        for period_name, period in periods:
            data = await client.get_historical_data(
                currency_pair="USD/JPY",
                period=period,
                interval="1d"
            )
            
            if data is not None and not data.empty:
                print(f"✅ {period_name}: {len(data)}件")
                print(f"   📅 {data.index[0].date()} 〜 {data.index[-1].date()}")
                print(f"   💰 価格範囲: {data['Close'].min():.2f} 〜 {data['Close'].max():.2f}")
                print(f"   📊 変動率: {((data['Close'].max() - data['Close'].min()) / data['Close'].min() * 100):.2f}%")
            else:
                print(f"❌ {period_name}: データ取得失敗")
            print()
            
    except Exception as e:
        print(f"❌ データ品質確認でエラー: {e}")


async def main():
    """メイン関数"""
    print("🚀 実際の市場データでのPhase 2パターン検出検証を開始\n")
    
    # データ品質確認
    await test_data_quality()
    
    # パターン検出テスト
    await test_pattern_detection_with_real_data()


if __name__ == "__main__":
    asyncio.run(main())
