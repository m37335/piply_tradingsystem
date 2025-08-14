#!/usr/bin/env python3
"""
データ取得テストスクリプト
Phase 1: データ準備とシステム確認

Alpha Vantage APIからUSD/JPYの実際のデータを取得し、
データの品質と量を確認するテストスクリプト
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import yaml

# プロジェクトのルートディレクトリをパスに追加
sys.path.append('/app')

from src.infrastructure.database.services.price_data_service import PriceDataService
from src.infrastructure.external.alpha_vantage_client import AlphaVantageClient

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataFetchTester:
    """データ取得テストクラス"""

    def __init__(self):
        self.alpha_vantage_client = AlphaVantageClient()
        self.price_data_service = PriceDataService()
        self.test_results = {}

    async def test_data_fetch(self, currency_pair: str, timeframe: str, period: str) -> Dict:
        """データ取得テスト実行"""
        logger.info(f"=== データ取得テスト開始 ===")
        logger.info(f"通貨ペア: {currency_pair}")
        logger.info(f"時間足: {timeframe}")
        logger.info(f"期間: {period}")

        try:
            # 1. API接続テスト
            connection_test = await self._test_api_connection()
            self.test_results['api_connection'] = connection_test

            if not connection_test['success']:
                logger.error("API接続に失敗しました")
                return self.test_results

            # 2. データ取得テスト
            data_fetch_test = await self._test_data_fetch(currency_pair, timeframe, period)
            self.test_results['data_fetch'] = data_fetch_test

            # 3. データ品質テスト
            if data_fetch_test['success']:
                quality_test = await self._test_data_quality(data_fetch_test['data'])
                self.test_results['data_quality'] = quality_test

            # 4. データベース保存テスト
            if data_fetch_test['success']:
                save_test = await self._test_database_save(data_fetch_test['data'])
                self.test_results['database_save'] = save_test

            # 5. 結果サマリー
            self._generate_summary()

            return self.test_results

        except Exception as e:
            logger.error(f"データ取得テストでエラーが発生しました: {e}")
            self.test_results['error'] = str(e)
            return self.test_results

    async def _test_api_connection(self) -> Dict:
        """API接続テスト"""
        logger.info("API接続テスト開始...")
        
        try:
            # APIキーの確認
            api_key = self.alpha_vantage_client.api_key
            if not api_key:
                return {
                    'success': False,
                    'error': 'APIキーが設定されていません'
                }

            # 簡単なAPI呼び出しテスト
            test_data = await self.alpha_vantage_client.get_intraday_data(
                symbol="USDJPY",
                interval="5min",
                outputsize="compact"
            )

            if test_data is not None and len(test_data) > 0:
                logger.info("✅ API接続テスト成功")
                return {
                    'success': True,
                    'message': 'API接続が正常です',
                    'data_count': len(test_data)
                }
            else:
                return {
                    'success': False,
                    'error': 'APIからデータが取得できませんでした'
                }

        except Exception as e:
            logger.error(f"API接続テストでエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _test_data_fetch(self, currency_pair: str, timeframe: str, period: str) -> Dict:
        """データ取得テスト"""
        logger.info("データ取得テスト開始...")

        try:
            # 期間の計算
            end_date = datetime.now()
            if period == "1month":
                start_date = end_date - timedelta(days=30)
            elif period == "3months":
                start_date = end_date - timedelta(days=90)
            elif period == "6months":
                start_date = end_date - timedelta(days=180)
            else:
                start_date = end_date - timedelta(days=30)

            # 時間足のマッピング
            interval_mapping = {
                "5m": "5min",
                "1h": "60min",
                "4h": "daily",  # Alpha Vantageでは4時間足がないため日足を使用
                "1d": "daily"
            }

            interval = interval_mapping.get(timeframe, "5min")

            # データ取得
            data = await self.alpha_vantage_client.get_intraday_data(
                symbol="USDJPY",
                interval=interval,
                outputsize="full"
            )

            if data is None or len(data) == 0:
                return {
                    'success': False,
                    'error': 'データが取得できませんでした'
                }

            # 期間でフィルタリング
            filtered_data = []
            for row in data:
                timestamp = pd.to_datetime(row['timestamp'])
                if start_date <= timestamp <= end_date:
                    filtered_data.append(row)

            logger.info(f"✅ データ取得テスト成功: {len(filtered_data)}件のデータを取得")
            
            return {
                'success': True,
                'data': filtered_data,
                'data_count': len(filtered_data),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'timeframe': timeframe
            }

        except Exception as e:
            logger.error(f"データ取得テストでエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _test_data_quality(self, data: List[Dict]) -> Dict:
        """データ品質テスト"""
        logger.info("データ品質テスト開始...")

        try:
            if not data:
                return {
                    'success': False,
                    'error': 'データが空です'
                }

            # DataFrameに変換
            df = pd.DataFrame(data)
            
            # 必須カラムの確認
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'必須カラムが不足しています: {missing_columns}'
                }

            # データ型の確認
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

            # 欠損値の確認
            null_counts = df.isnull().sum()
            total_rows = len(df)

            # 異常値の確認
            price_stats = {
                'min_price': df['close'].min(),
                'max_price': df['close'].max(),
                'avg_price': df['close'].mean(),
                'price_std': df['close'].std()
            }

            # 時系列の連続性確認
            df_sorted = df.sort_values('timestamp')
            time_gaps = df_sorted['timestamp'].diff().dropna()
            avg_gap = time_gaps.mean()

            quality_score = 100
            issues = []

            # 欠損値チェック
            if null_counts.sum() > 0:
                quality_score -= 20
                issues.append(f"欠損値: {null_counts.sum()}件")

            # 価格範囲チェック
            if price_stats['min_price'] < 100 or price_stats['max_price'] > 200:
                quality_score -= 10
                issues.append("価格範囲が異常です")

            # 時系列ギャップチェック
            if avg_gap > pd.Timedelta(hours=2):
                quality_score -= 10
                issues.append("時系列に大きなギャップがあります")

            logger.info(f"✅ データ品質テスト完了: スコア {quality_score}/100")
            
            return {
                'success': True,
                'quality_score': quality_score,
                'total_rows': total_rows,
                'null_counts': null_counts.to_dict(),
                'price_stats': price_stats,
                'avg_time_gap': str(avg_gap),
                'issues': issues
            }

        except Exception as e:
            logger.error(f"データ品質テストでエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _test_database_save(self, data: List[Dict]) -> Dict:
        """データベース保存テスト"""
        logger.info("データベース保存テスト開始...")

        try:
            if not data:
                return {
                    'success': False,
                    'error': '保存するデータがありません'
                }

            # テスト用のデータを保存
            saved_count = 0
            for row in data[:10]:  # 最初の10件のみテスト
                try:
                    await self.price_data_service.save_price_data(
                        currency_pair="USD/JPY",
                        timestamp=pd.to_datetime(row['timestamp']),
                        open_price=float(row['open']),
                        high_price=float(row['high']),
                        low_price=float(row['low']),
                        close_price=float(row['close']),
                        volume=int(row['volume'])
                    )
                    saved_count += 1
                except Exception as e:
                    logger.warning(f"データ保存でエラー: {e}")

            if saved_count > 0:
                logger.info(f"✅ データベース保存テスト成功: {saved_count}件保存")
                return {
                    'success': True,
                    'saved_count': saved_count,
                    'message': f'{saved_count}件のデータを正常に保存しました'
                }
            else:
                return {
                    'success': False,
                    'error': 'データの保存に失敗しました'
                }

        except Exception as e:
            logger.error(f"データベース保存テストでエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_summary(self):
        """テスト結果サマリー生成"""
        logger.info("=== データ取得テスト結果サマリー ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get('success', False))
        
        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {passed_tests}")
        logger.info(f"失敗: {total_tests - passed_tests}")
        
        # 各テストの詳細結果
        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ 成功" if result.get('success', False) else "❌ 失敗"
                logger.info(f"{test_name}: {status}")
                
                if not result.get('success', False) and 'error' in result:
                    logger.error(f"  エラー: {result['error']}")


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='データ取得テストスクリプト')
    parser.add_argument('--currency-pair', default='USD/JPY', help='通貨ペア')
    parser.add_argument('--timeframe', default='5m', help='時間足 (5m, 1h, 4h, 1d)')
    parser.add_argument('--period', default='3months', help='期間 (1month, 3months, 6months)')
    parser.add_argument('--output', help='結果出力ファイル')
    
    args = parser.parse_args()
    
    # テスト実行
    tester = DataFetchTester()
    results = await tester.test_data_fetch(args.currency_pair, args.timeframe, args.period)
    
    # 結果出力
    if args.output:
        with open(args.output, 'w') as f:
            yaml.dump(results, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"結果を {args.output} に保存しました")
    
    # 終了コード
    success_count = sum(1 for result in results.values() 
                       if isinstance(result, dict) and result.get('success', False))
    total_tests = len([r for r in results.values() if isinstance(r, dict)])
    
    if success_count == total_tests:
        logger.info("🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        logger.error(f"❌ {total_tests - success_count}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
