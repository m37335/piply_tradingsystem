#!/usr/bin/env python3
"""
パターン6詳細テストスクリプト
パターン6（複合シグナル検出）専用の詳細テスト

パターン6の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append('/app')

from src.infrastructure.analysis.pattern_detectors.composite_signal_detector import (
    CompositeSignalDetector
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Pattern6DetailedTester:
    """パターン6詳細テストクラス"""

    def __init__(self):
        self.detector = CompositeSignalDetector()

    async def test_pattern6_detailed(self) -> Dict:
        """パターン6詳細テスト実行"""
        logger.info("=== パターン6詳細テスト開始 ===")

        try:
            # パターン6の条件を満たすテストデータを作成
            test_data = self._create_pattern6_test_data()
            
            # 検出テスト
            result = self.detector.detect(test_data)
            
            # 結果分析
            if result is not None:
                logger.info("✅ パターン6検出成功！")
                logger.info(f"  信頼度: {result.get('confidence_score', 'N/A')}")
                logger.info(f"  条件: {result.get('conditions_met', {})}")
                
                return {
                    'success': True,
                    'detected': True,
                    'confidence_score': result.get('confidence_score'),
                    'conditions_met': result.get('conditions_met'),
                    'pattern_info': result
                }
            else:
                logger.info("❌ パターン6は検出されませんでした")
                
                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)
                
                return {
                    'success': True,
                    'detected': False,
                    'condition_analysis': condition_analysis
                }

        except Exception as e:
            logger.error(f"パターン6詳細テストでエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_pattern6_test_data(self) -> Dict:
        """パターン6の条件を満たすテストデータ作成"""
        logger.info("パターン6用テストデータ作成中...")
        
        # パターン6の条件:
        # D1: RSI 25-75 + MACD上昇/上昇傾向 + 価格上昇/安定（3つ一致）
        # H4: RSI 25-75 + ボリンジャーバンド内/ミドル付近（2つ一致）
        # H1: RSI 25-75 + ボリンジャーバンド内/ミドル付近（2つ一致）
        # M5: RSI 25-75 + 価格形状安定（5%以下変動率）（2つ一致）
        
        test_data = {}
        
        # D1データ作成
        d1_data = self._create_d1_data()
        test_data['D1'] = d1_data
        
        # H4データ作成
        h4_data = self._create_h4_data()
        test_data['H4'] = h4_data
        
        # H1データ作成
        h1_data = self._create_h1_data()
        test_data['H1'] = h1_data
        
        # M5データ作成
        m5_data = self._create_m5_data()
        test_data['M5'] = m5_data
        
        logger.info("✅ テストデータ作成完了")
        return test_data

    def _create_d1_data(self) -> Dict:
        """D1データ作成（RSI 25-75 + MACD上昇 + 価格上昇/安定）"""
        # 価格データ（上昇傾向）
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        prices = []
        
        for i in range(50):
            # 上昇傾向
            price = 150.0 + i * 0.2
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Close': prices,
            'Volume': [1000 + i * 10 for i in range(50)]
        })
        
        # RSIデータ（25-75の範囲）
        rsi_values = [50 + i * 0.5 for i in range(50)]
        
        # MACDデータ（上昇傾向）
        macd_values = []
        signal_values = []
        for i in range(50):
            # MACDが上昇傾向
            macd_values.append(0.1 + i * 0.02)
            signal_values.append(0.05 + i * 0.015)
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values
            },
            'macd': {
                'macd': pd.Series(macd_values),
                'signal': pd.Series(signal_values),
                'histogram': [m - s for m, s in zip(macd_values, signal_values)]
            },
            'bollinger_bands': {
                'upper': pd.Series([p + 0.5 for p in prices]),
                'middle': pd.Series(prices),
                'lower': pd.Series([p - 0.5 for p in prices]),
                'std': [0.5] * 50
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _create_h4_data(self) -> Dict:
        """H4データ作成（RSI 25-75 + ボリンジャーバンド内/ミドル付近）"""
        # 価格データ（ボリンジャーバンドミドル付近）
        dates = pd.date_range(start='2024-01-01', periods=100, freq='4H')
        prices = []
        
        for i in range(100):
            # ボリンジャーバンドミドル付近
            base_price = 150.0 + i * 0.1
            price = base_price + (i % 3 - 1) * 0.02  # ミドル付近の小さな変動
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.05 for p in prices],
            'High': [p + 0.1 for p in prices],
            'Low': [p - 0.1 for p in prices],
            'Close': prices,
            'Volume': [1000 + i * 5 for i in range(100)]
        })
        
        # RSIデータ（25-75の範囲）
        rsi_values = [50 + (i % 10 - 5) * 2 for i in range(100)]
        
        # ボリンジャーバンド計算
        bb_upper = []
        bb_middle = []
        bb_lower = []
        
        for i, price in enumerate(prices):
            middle = price
            upper = price + 0.3
            lower = price - 0.3
            
            bb_upper.append(upper)
            bb_middle.append(middle)
            bb_lower.append(lower)
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values
            },
            'macd': {
                'macd': pd.Series([0.1 + i * 0.01 for i in range(100)]),
                'signal': pd.Series([0.05 + i * 0.008 for i in range(100)]),
                'histogram': [0.05 + i * 0.002 for i in range(100)]
            },
            'bollinger_bands': {
                'upper': pd.Series(bb_upper),
                'middle': pd.Series(bb_middle),
                'lower': pd.Series(bb_lower),
                'std': [0.3] * 100
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _create_h1_data(self) -> Dict:
        """H1データ作成（RSI 25-75 + ボリンジャーバンド内/ミドル付近）"""
        # H4と同様のデータ構造
        dates = pd.date_range(start='2024-01-01', periods=200, freq='H')
        prices = []
        
        for i in range(200):
            # ボリンジャーバンドミドル付近
            base_price = 150.0 + i * 0.05
            price = base_price + (i % 5 - 2) * 0.01  # ミドル付近の小さな変動
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.03 for p in prices],
            'High': [p + 0.05 for p in prices],
            'Low': [p - 0.05 for p in prices],
            'Close': prices,
            'Volume': [1000 + i * 2 for i in range(200)]
        })
        
        # RSIデータ（25-75の範囲）
        rsi_values = [50 + (i % 15 - 7) * 1.5 for i in range(200)]
        
        # ボリンジャーバンド計算
        bb_upper = []
        bb_middle = []
        bb_lower = []
        
        for i, price in enumerate(prices):
            middle = price
            upper = price + 0.3
            lower = price - 0.3
            
            bb_upper.append(upper)
            bb_middle.append(middle)
            bb_lower.append(lower)
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values
            },
            'macd': {
                'macd': pd.Series([0.1 + i * 0.01 for i in range(200)]),
                'signal': pd.Series([0.05 + i * 0.008 for i in range(200)]),
                'histogram': [0.05 + i * 0.002 for i in range(200)]
            },
            'bollinger_bands': {
                'upper': pd.Series(bb_upper),
                'middle': pd.Series(bb_middle),
                'lower': pd.Series(bb_lower),
                'std': [0.3] * 200
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _create_m5_data(self) -> Dict:
        """M5データ作成（RSI 25-75 + 価格形状安定）"""
        # 価格データ（安定した形状）
        dates = pd.date_range(start='2024-01-01', periods=500, freq='5min')
        prices = []
        
        for i in range(500):
            # 安定した価格（5%以下の変動率）
            base_price = 150.0
            price = base_price + (i % 10 - 5) * 0.005  # 小さな変動
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.002 for p in prices],
            'High': [p + 0.005 for p in prices],
            'Low': [p - 0.005 for p in prices],
            'Close': prices,
            'Volume': [1000 + i for i in range(500)]
        })
        
        # RSIデータ（25-75の範囲）
        rsi_values = [50 + (i % 20 - 10) * 1 for i in range(500)]
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values
            },
            'macd': {
                'macd': pd.Series([0.1 + i * 0.01 for i in range(500)]),
                'signal': pd.Series([0.05 + i * 0.008 for i in range(500)]),
                'histogram': [0.05 + i * 0.002 for i in range(500)]
            },
            'bollinger_bands': {
                'upper': pd.Series([p + 0.3 for p in prices]),
                'middle': pd.Series(prices),
                'lower': pd.Series([p - 0.3 for p in prices]),
                'std': [0.3] * 500
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _analyze_conditions(self, test_data: Dict) -> Dict:
        """条件の詳細分析"""
        analysis = {}
        
        for timeframe, data in test_data.items():
            indicators = data.get('indicators', {})
            price_data = data.get('price_data', pd.DataFrame())
            
            timeframe_analysis = {}
            
            # RSI分析
            if 'rsi' in indicators:
                rsi_value = indicators['rsi'].get('current_value', 0)
                rsi_condition = 25 <= rsi_value <= 75
                
                timeframe_analysis['rsi'] = {
                    'value': rsi_value,
                    'condition_met': rsi_condition
                }
            
            # MACD分析（D1のみ）
            if timeframe == 'D1' and 'macd' in indicators:
                macd_data = indicators['macd']
                if 'macd' in macd_data and 'signal' in macd_data:
                    macd_series = macd_data['macd']
                    signal_series = macd_data['signal']
                    
                    if len(macd_series) >= 3:
                        recent_macd = macd_series.iloc[-3:]
                        recent_signal = signal_series.iloc[-3:]
                        
                        current_macd = recent_macd.iloc[-1]
                        current_signal = recent_signal.iloc[-1]
                        
                        macd_condition = current_macd > current_signal or (
                            recent_macd.iloc[-1] > recent_macd.iloc[-2] > recent_macd.iloc[-3]
                        )
                        
                        timeframe_analysis['macd'] = {
                            'current_macd': current_macd,
                            'current_signal': current_signal,
                            'rising_trend': recent_macd.iloc[-1] > recent_macd.iloc[-2] > recent_macd.iloc[-3],
                            'condition_met': macd_condition
                        }
            
            # 価格分析（D1のみ）
            if timeframe == 'D1' and not price_data.empty:
                if len(price_data) >= 5:
                    recent_prices = price_data['Close'].iloc[-5:]
                    price_condition = (
                        recent_prices.iloc[-1] > recent_prices.iloc[-2] or
                        abs(recent_prices.iloc[-1] - recent_prices.iloc[-2]) / recent_prices.iloc[-2] < 0.01
                    )
                    
                    timeframe_analysis['price'] = {
                        'recent_prices': recent_prices.tolist(),
                        'condition_met': price_condition
                    }
            
            # ボリンジャーバンド分析（H4, H1のみ）
            if timeframe in ['H4', 'H1'] and 'bollinger_bands' in indicators:
                bb_data = indicators['bollinger_bands']
                if not price_data.empty:
                    current_price = price_data['Close'].iloc[-1]
                    upper_band = bb_data['upper'].iloc[-1]
                    lower_band = bb_data['lower'].iloc[-1]
                    middle_band = bb_data['middle'].iloc[-1]
                    
                    bb_condition = (
                        lower_band <= current_price <= upper_band or
                        abs(current_price - middle_band) / middle_band < 0.02
                    )
                    
                    timeframe_analysis['bollinger_bands'] = {
                        'current_price': current_price,
                        'upper_band': upper_band,
                        'lower_band': lower_band,
                        'middle_band': middle_band,
                        'condition_met': bb_condition
                    }
            
            # 価格形状分析（M5のみ）
            if timeframe == 'M5' and not price_data.empty:
                if len(price_data) >= 5:
                    recent_prices = price_data['Close'].iloc[-5:]
                    price_volatility = recent_prices.std() / recent_prices.mean()
                    price_shape_condition = price_volatility < 0.05
                    
                    timeframe_analysis['price_shape'] = {
                        'recent_prices': recent_prices.tolist(),
                        'volatility': price_volatility,
                        'condition_met': price_shape_condition
                    }
            
            analysis[timeframe] = timeframe_analysis
        
        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern6DetailedTester()
    results = await tester.test_pattern6_detailed()
    
    # 結果表示
    if results.get('success', False):
        if results.get('detected', False):
            logger.info("🎉 パターン6が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン6は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get('condition_analysis', {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
