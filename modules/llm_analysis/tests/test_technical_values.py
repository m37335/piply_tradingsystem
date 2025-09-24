"""
テクニカル指標の実際の値を確認

現在の市場データで各テクニカル指標の値を表示
"""

import asyncio
import logging
import sys
import os

# パスの設定
sys.path.append('/app')

from modules.llm_analysis.core.data_preparator import LLMDataPreparator


async def test_technical_values():
    """テクニカル指標の実際の値を確認"""
    print("📊 テクニカル指標値確認テスト開始")
    print("=" * 60)
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # データ準備器の初期化
    data_preparator = LLMDataPreparator()
    
    try:
        # 初期化
        print("📋 データ準備器初期化中...")
        await data_preparator.initialize()
        print("✅ データ準備器初期化完了")
        
        # 分析データの準備
        print("📊 分析データ準備中...")
        analysis_data = await data_preparator.prepare_analysis_data(
            analysis_type='trend_direction',
            symbol='USDJPY=X',
            timeframes=['5m', '15m', '1h', '4h', '1d']
        )
        
        if not analysis_data:
            print("❌ 分析データの準備に失敗")
            return
        
        print(f"📊 分析データ構造: {type(analysis_data)}")
        print(f"📊 時間足キー: {list(analysis_data.get('timeframes', {}).keys())}")
        
        # 各時間足の最新データを表示
        for timeframe, data in analysis_data.get('timeframes', {}).items():
            print(f"📊 {timeframe}足データ型: {type(data)}")
            if data is not None:
                if isinstance(data, dict):
                    print(f"   📊 辞書キー: {list(data.keys())}")
                    if 'data' in data and hasattr(data['data'], 'empty') and not data['data'].empty:
                        latest = data['data'].iloc[-1]
                        print(f"\n📈 {timeframe}足の最新データ:")
                        print(f"   時刻: {latest.name}")
                        print(f"   価格: {latest['close']:.5f}")
                        print(f"   RSI_14: {latest.get('RSI_14', 'N/A'):.2f}" if 'RSI_14' in latest else "   RSI_14: N/A")
                        print(f"   EMA_200: {latest.get('EMA_200', 'N/A'):.5f}" if 'EMA_200' in latest else "   EMA_200: N/A")
                        print(f"   EMA_21: {latest.get('EMA_21', 'N/A'):.5f}" if 'EMA_21' in latest else "   EMA_21: N/A")
                        print(f"   EMA_55: {latest.get('EMA_55', 'N/A'):.5f}" if 'EMA_55' in latest else "   EMA_55: N/A")
                        print(f"   MACD: {latest.get('MACD', 'N/A'):.5f}" if 'MACD' in latest else "   MACD: N/A")
                        print(f"   MACD_Signal: {latest.get('MACD_Signal', 'N/A'):.5f}" if 'MACD_Signal' in latest else "   MACD_Signal: N/A")
                        print(f"   Fib_0.5: {latest.get('Fib_0.5', 'N/A'):.5f}" if 'Fib_0.5' in latest else "   Fib_0.5: N/A")
                        print(f"   Fib_0.618: {latest.get('Fib_0.618', 'N/A'):.5f}" if 'Fib_0.618' in latest else "   Fib_0.618: N/A")
                        print(f"   Fib_0.786: {latest.get('Fib_0.786', 'N/A'):.5f}" if 'Fib_0.786' in latest else "   Fib_0.786: N/A")
                elif hasattr(data, 'empty') and not data.empty:
                    latest = data.iloc[-1]
                    print(f"\n📈 {timeframe}足の最新データ:")
                    print(f"   時刻: {latest.name}")
                    print(f"   価格: {latest['close']:.5f}")
                    print(f"   RSI_14: {latest.get('RSI_14', 'N/A'):.2f}" if 'RSI_14' in latest else "   RSI_14: N/A")
                    print(f"   EMA_200: {latest.get('EMA_200', 'N/A'):.5f}" if 'EMA_200' in latest else "   EMA_200: N/A")
                    print(f"   EMA_21: {latest.get('EMA_21', 'N/A'):.5f}" if 'EMA_21' in latest else "   EMA_21: N/A")
                    print(f"   EMA_55: {latest.get('EMA_55', 'N/A'):.5f}" if 'EMA_55' in latest else "   EMA_55: N/A")
                    print(f"   MACD: {latest.get('MACD', 'N/A'):.5f}" if 'MACD' in latest else "   MACD: N/A")
                    print(f"   MACD_Signal: {latest.get('MACD_Signal', 'N/A'):.5f}" if 'MACD_Signal' in latest else "   MACD_Signal: N/A")
                    print(f"   Fib_0.5: {latest.get('Fib_0.5', 'N/A'):.5f}" if 'Fib_0.5' in latest else "   Fib_0.5: N/A")
                    print(f"   Fib_0.618: {latest.get('Fib_0.618', 'N/A'):.5f}" if 'Fib_0.618' in latest else "   Fib_0.618: N/A")
                    print(f"   Fib_0.786: {latest.get('Fib_0.786', 'N/A'):.5f}" if 'Fib_0.786' in latest else "   Fib_0.786: N/A")
        
        # ルール条件のチェック
        print(f"\n🔍 ルール条件チェック:")
        print("-" * 40)
        
        # D1とH4のデータを使用（階層的判定）
        d1_data = analysis_data['timeframes'].get('1d')
        h4_data = analysis_data['timeframes'].get('4h')
        
        if d1_data is not None and hasattr(d1_data, 'empty') and not d1_data.empty:
            latest_d1 = d1_data.iloc[-1]
            print(f"📊 D1足での条件チェック:")
            print(f"   RSI_14: {latest_d1.get('RSI_14', 'N/A'):.2f}")
            print(f"   price < EMA_200: {latest_d1['close']:.5f} < {latest_d1.get('EMA_200', 'N/A'):.5f}")
            print(f"   EMA_21 < EMA_55: {latest_d1.get('EMA_21', 'N/A'):.5f} < {latest_d1.get('EMA_55', 'N/A'):.5f}")
            print(f"   MACD < 0: {latest_d1.get('MACD', 'N/A'):.5f} < 0")
            print(f"   MACD < MACD_Signal: {latest_d1.get('MACD', 'N/A'):.5f} < {latest_d1.get('MACD_Signal', 'N/A'):.5f}")
        
        if h4_data is not None and hasattr(h4_data, 'empty') and not h4_data.empty:
            latest_h4 = h4_data.iloc[-1]
            print(f"\n📊 H4足での条件チェック:")
            print(f"   RSI_14: {latest_h4.get('RSI_14', 'N/A'):.2f}")
            print(f"   price < EMA_200: {latest_h4['close']:.5f} < {latest_h4.get('EMA_200', 'N/A'):.5f}")
            print(f"   EMA_21 < EMA_55: {latest_h4.get('EMA_21', 'N/A'):.5f} < {latest_h4.get('EMA_55', 'N/A'):.5f}")
            print(f"   MACD < 0: {latest_h4.get('MACD', 'N/A'):.5f} < 0")
            print(f"   MACD < MACD_Signal: {latest_h4.get('MACD', 'N/A'):.5f} < {latest_h4.get('MACD_Signal', 'N/A'):.5f}")
        
        print("\n✅ テクニカル指標値確認テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        try:
            await data_preparator.close()
            print("🧹 リソースクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")


if __name__ == "__main__":
    asyncio.run(test_technical_values())
