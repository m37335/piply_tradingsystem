#!/usr/bin/env python3
"""
パターン3詳細テストスクリプト
パターン3（ダイバージェンス検出）専用の詳細テスト

パターン3の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append('/app')

from src.infrastructure.analysis.pattern_detectors.divergence_detector import (
    DivergenceDetector
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Pattern3DetailedTester:
    """パターン3詳細テストクラス"""

    def __init__(self):
        self.detector = DivergenceDetector()

    async def test_pattern3_detailed(self) -> Dict:
        """パターン3詳細テスト実行"""
        logger.info("=== パターン3詳細テスト開始 ===")

        try:
            # パターン3の条件を満たすテストデータを作成
            test_data = self._create_pattern3_test_data()
            
            # 検出テスト
            result = self.detector.detect(test_data)
            
            # 結果分析
            if result is not None:
                logger.info("✅ パターン3検出成功！")
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
                logger.info("❌ パターン3は検出されませんでした")
                
                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)
                
                return {
                    'success': True,
                    'detected': False,
                    'condition_analysis': condition_analysis
                }

        except Exception as e:
            logger.error(f"パターン3詳細テストでエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_pattern3_test_data(self) -> Dict:
        """パターン3の条件を満たすテストデータ作成"""
        logger.info("パターン3用テストデータ作成中...")
        
        # パターン3の条件:
        # D1: 価格上昇トレンド（3期間連続） + RSI平均値未達
        # H4: 価格上昇トレンド（3期間連続） + RSI下降トレンド（3期間連続）
        # H1: 価格上昇トレンド（3期間連続） + RSI下降トレンド（3期間連続）
        # M5: 価格上昇トレンド（3期間連続） + RSI下降トレンド（3期間連続）
        
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
        """D1データ作成（価格上昇トレンド + RSI平均値未達）"""
        # 価格データ（上昇トレンド）
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        prices = []
        
        for i in range(50):
            # 上昇トレンド（直近3期間で連続上昇）
            if i < 47:
                price = 150.0 + i * 0.2
            else:
                # 直近3期間で連続上昇
                base_price = 159.4
                price = base_price + (i - 47) * 0.3
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.1 for p in prices],
            'High': [p + 0.2 for p in prices],
            'Low': [p - 0.2 for p in prices],
            'Close': prices,
            'Volume': [1000 + i * 10 for i in range(50)]
        })
        
        # RSIデータ（価格上昇に追いつかない）
        rsi_values = []
        for i in range(50):
            if i < 45:
                rsi_values.append(60 + i * 0.5)  # 徐々に上昇
            else:
                # 直近5期間でRSIが平均値を下回る
                rsi_values.append(75 - (i - 45) * 2)  # 急激に下降
        
        # 他の指標データ
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values,
                'series': pd.Series(rsi_values)
            },
            'macd': {
                'macd': [0.1 + i * 0.01 for i in range(50)],
                'signal': [0.05 + i * 0.008 for i in range(50)],
                'histogram': [0.05 + i * 0.002 for i in range(50)]
            },
            'bollinger_bands': {
                'upper': [p + 0.5 for p in prices],
                'middle': prices,
                'lower': [p - 0.5 for p in prices],
                'std': [0.5] * 50
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _create_h4_data(self) -> Dict:
        """H4データ作成（価格上昇トレンド + RSI下降トレンド）"""
        # 価格データ（上昇トレンド）
        dates = pd.date_range(start='2024-01-01', periods=100, freq='4H')
        prices = []
        
        for i in range(100):
            if i < 97:
                price = 150.0 + i * 0.1
            else:
                # 直近3期間で連続上昇
                base_price = 159.7
                price = base_price + (i - 97) * 0.2
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.05 for p in prices],
            'High': [p + 0.1 for p in prices],
            'Low': [p - 0.1 for p in prices],
            'Close': prices,
            'Volume': [1000 + i * 5 for i in range(100)]
        })
        
        # RSIデータ（下降トレンド）
        rsi_values = []
        for i in range(100):
            if i < 97:
                rsi_values.append(70 - i * 0.2)  # 徐々に下降
            else:
                # 直近3期間で連続下降
                base_rsi = 50.6
                rsi_values.append(base_rsi - (i - 97) * 3)
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values,
                'series': pd.Series(rsi_values)
            },
            'macd': {
                'macd': [0.1 + i * 0.01 for i in range(100)],
                'signal': [0.05 + i * 0.008 for i in range(100)],
                'histogram': [0.05 + i * 0.002 for i in range(100)]
            },
            'bollinger_bands': {
                'upper': [p + 0.5 for p in prices],
                'middle': prices,
                'lower': [p - 0.5 for p in prices],
                'std': [0.5] * 100
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _create_h1_data(self) -> Dict:
        """H1データ作成（価格上昇トレンド + RSI下降トレンド）"""
        # H4と同様のデータ構造
        dates = pd.date_range(start='2024-01-01', periods=200, freq='H')
        prices = []
        
        for i in range(200):
            if i < 197:
                price = 150.0 + i * 0.05
            else:
                # 直近3期間で連続上昇
                base_price = 159.85
                price = base_price + (i - 197) * 0.1
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.03 for p in prices],
            'High': [p + 0.05 for p in prices],
            'Low': [p - 0.05 for p in prices],
            'Close': prices,
            'Volume': [1000 + i * 2 for i in range(200)]
        })
        
        # RSIデータ（下降トレンド）
        rsi_values = []
        for i in range(200):
            if i < 197:
                rsi_values.append(65 - i * 0.1)  # 徐々に下降
            else:
                # 直近3期間で連続下降
                base_rsi = 45.3
                rsi_values.append(base_rsi - (i - 197) * 2)
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values,
                'series': pd.Series(rsi_values)
            },
            'macd': {
                'macd': [0.1 + i * 0.01 for i in range(200)],
                'signal': [0.05 + i * 0.008 for i in range(200)],
                'histogram': [0.05 + i * 0.002 for i in range(200)]
            },
            'bollinger_bands': {
                'upper': [p + 0.3 for p in prices],
                'middle': prices,
                'lower': [p - 0.3 for p in prices],
                'std': [0.3] * 200
            }
        }
        
        return {
            'price_data': price_data,
            'indicators': indicators
        }

    def _create_m5_data(self) -> Dict:
        """M5データ作成（価格上昇トレンド + RSI下降トレンド）"""
        # 価格データ（上昇トレンド）
        dates = pd.date_range(start='2024-01-01', periods=500, freq='5min')
        prices = []
        
        for i in range(500):
            if i < 497:
                price = 150.0 + i * 0.02
            else:
                # 直近3期間で連続上昇
                base_price = 159.94
                price = base_price + (i - 497) * 0.05
            prices.append(price)
        
        price_data = pd.DataFrame({
            'Date': dates,
            'Open': [p - 0.01 for p in prices],
            'High': [p + 0.02 for p in prices],
            'Low': [p - 0.02 for p in prices],
            'Close': prices,
            'Volume': [1000 + i for i in range(500)]
        })
        
        # RSIデータ（下降トレンド）
        rsi_values = []
        for i in range(500):
            if i < 497:
                rsi_values.append(60 - i * 0.04)  # 徐々に下降
            else:
                # 直近3期間で連続下降
                base_rsi = 40.12
                rsi_values.append(base_rsi - (i - 497) * 1)
        
        indicators = {
            'rsi': {
                'current_value': rsi_values[-1],
                'values': rsi_values,
                'series': pd.Series(rsi_values)
            },
            'macd': {
                'macd': [0.1 + i * 0.01 for i in range(500)],
                'signal': [0.05 + i * 0.008 for i in range(500)],
                'histogram': [0.05 + i * 0.002 for i in range(500)]
            },
            'bollinger_bands': {
                'upper': [p + 0.3 for p in prices],
                'middle': prices,
                'lower': [p - 0.3 for p in prices],
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
            
            # 価格トレンド分析
            if not price_data.empty and len(price_data) >= 5:
                recent_prices = price_data['Close'].iloc[-5:]
                if len(recent_prices) >= 3:
                    price_trend = (
                        recent_prices.iloc[-1] > recent_prices.iloc[-2] > recent_prices.iloc[-3]
                    )
                    
                    timeframe_analysis['price_trend'] = {
                        'recent_prices': recent_prices.tolist(),
                        'trend_condition': price_trend
                    }
            
            # RSI分析
            if 'rsi' in indicators and 'series' in indicators['rsi']:
                rsi_series = indicators['rsi']['series']
                if len(rsi_series) >= 5:
                    recent_rsi = rsi_series.iloc[-5:]
                    
                    if timeframe == 'D1':
                        # D1: RSI平均値未達チェック
                        if len(recent_rsi) >= 5:
                            rsi_avg = recent_rsi.iloc[-5:].mean()
                            current_rsi = recent_rsi.iloc[-1]
                            rsi_condition = current_rsi < rsi_avg
                            
                            timeframe_analysis['rsi'] = {
                                'current_value': current_rsi,
                                'average_value': rsi_avg,
                                'condition_met': rsi_condition
                            }
                    else:
                        # H4, H1, M5: RSI下降トレンドチェック
                        if len(recent_rsi) >= 3:
                            rsi_trend = (
                                recent_rsi.iloc[-1] < recent_rsi.iloc[-2] < recent_rsi.iloc[-3]
                            )
                            
                            timeframe_analysis['rsi'] = {
                                'recent_values': recent_rsi.tolist(),
                                'trend_condition': rsi_trend
                            }
            
            analysis[timeframe] = timeframe_analysis
        
        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern3DetailedTester()
    results = await tester.test_pattern3_detailed()
    
    # 結果表示
    if results.get('success', False):
        if results.get('detected', False):
            logger.info("🎉 パターン3が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン3は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get('condition_analysis', {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
