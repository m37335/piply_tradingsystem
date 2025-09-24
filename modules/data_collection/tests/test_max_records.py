#!/usr/bin/env python3
"""
Yahoo Finance API 最大取得件数テスト

各時間足で取得可能な最大件数を確認します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
from modules.data_collection.providers.base_provider import TimeFrame

# ログ設定
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MaxRecordsTester:
    """最大取得件数テストクラス"""
    
    def __init__(self):
        self.provider = YahooFinanceProvider()
    
    async def test_max_records_per_timeframe(self, symbol="USDJPY=X"):
        """時間足別最大取得件数テスト"""
        logger.info(f"🔍 {symbol} の時間足別最大取得件数をテスト中...")
        
        timeframes = [
            (TimeFrame.M5, "5分足"),
            (TimeFrame.M15, "15分足"), 
            (TimeFrame.H1, "1時間足"),
            (TimeFrame.H4, "4時間足"),
            (TimeFrame.D1, "日足")
        ]
        
        results = {}
        
        for tf, tf_name in timeframes:
            logger.info(f"📊 {tf_name} テスト中...")
            
            # 段階的に期間を延長してテスト
            test_periods = [
                ("1日", timedelta(days=1)),
                ("1週間", timedelta(weeks=1)),
                ("1ヶ月", timedelta(days=30)),
                ("3ヶ月", timedelta(days=90)),
                ("6ヶ月", timedelta(days=180)),
                ("1年", timedelta(days=365)),
                ("2年", timedelta(days=730)),
                ("5年", timedelta(days=1825))
            ]
            
            max_records = 0
            max_period = ""
            last_successful_records = 0
            
            for period_name, period_delta in test_periods:
                try:
                    end_date = datetime.now()
                    start_date = end_date - period_delta
                    
                    result = await self.provider.get_historical_data(
                        symbol=symbol,
                        timeframe=tf,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if result.success and result.data:
                        record_count = len(result.data)
                        logger.info(f"  {period_name}: {record_count}件")
                        
                        if record_count > max_records:
                            max_records = record_count
                            max_period = period_name
                        
                        last_successful_records = record_count
                        
                        # レート制限対策のため少し待機
                        await asyncio.sleep(0.5)
                    else:
                        logger.warning(f"  {period_name}: 取得失敗 - {result.error_message if result else 'Unknown error'}")
                        break
                        
                except Exception as e:
                    logger.error(f"  {period_name}: エラー - {e}")
                    break
            
            results[tf.value] = {
                "max_records": max_records,
                "max_period": max_period,
                "last_successful": last_successful_records,
                "timeframe_name": tf_name
            }
            
            logger.info(f"✅ {tf_name} 最大取得件数: {max_records}件 ({max_period})")
        
        return results
    
    async def test_different_symbols(self):
        """異なるシンボルでの最大取得件数テスト"""
        logger.info("🌍 異なるシンボルでの最大取得件数テスト...")
        
        symbols = ["USDJPY=X", "EURJPY=X", "GBPJPY=X", "EURUSD=X"]
        results = {}
        
        for symbol in symbols:
            logger.info(f"📈 {symbol} テスト中...")
            
            # 1年分のデータでテスト
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            symbol_results = {}
            
            for tf in [TimeFrame.M5, TimeFrame.H1, TimeFrame.D1]:
                try:
                    result = await self.provider.get_historical_data(
                        symbol=symbol,
                        timeframe=tf,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if result.success and result.data:
                        record_count = len(result.data)
                        symbol_results[tf.value] = record_count
                        logger.info(f"  {tf.value}: {record_count}件")
                    else:
                        symbol_results[tf.value] = 0
                        logger.warning(f"  {tf.value}: 取得失敗")
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"  {tf.value}: エラー - {e}")
                    symbol_results[tf.value] = 0
            
            results[symbol] = symbol_results
        
        return results
    
    async def test_rate_limits(self):
        """レート制限テスト"""
        logger.info("⏱️ レート制限テスト...")
        
        # 短時間で複数リクエストを送信してレート制限を確認
        requests_count = 0
        start_time = datetime.now()
        
        for i in range(10):
            try:
                result = await self.provider.get_latest_data("USDJPY=X", TimeFrame.M5)
                requests_count += 1
                
                if result.success:
                    logger.info(f"  リクエスト {i+1}: 成功")
                else:
                    logger.warning(f"  リクエスト {i+1}: 失敗 - {result.error_message}")
                    break
                
                # 短い間隔でリクエスト
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"  リクエスト {i+1}: エラー - {e}")
                break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ {requests_count}リクエストを{duration:.1f}秒で実行")
        logger.info(f"📊 平均レート: {requests_count/duration:.2f} リクエスト/秒")
        
        return {
            "total_requests": requests_count,
            "duration_seconds": duration,
            "rate_per_second": requests_count/duration if duration > 0 else 0
        }
    
    async def run_all_tests(self):
        """全テスト実行"""
        logger.info("🚀 Yahoo Finance API 最大取得件数テスト開始")
        
        all_results = {}
        
        try:
            # 時間足別最大取得件数テスト
            all_results['timeframe_max_records'] = await self.test_max_records_per_timeframe()
            
            # 異なるシンボルテスト
            all_results['symbol_comparison'] = await self.test_different_symbols()
            
            # レート制限テスト
            all_results['rate_limits'] = await self.test_rate_limits()
            
            # 結果サマリー
            logger.info("📊 テスト結果サマリー:")
            logger.info("=" * 60)
            
            logger.info("⏰ 時間足別最大取得件数:")
            for tf, data in all_results['timeframe_max_records'].items():
                logger.info(f"  {data['timeframe_name']}: {data['max_records']}件 ({data['max_period']})")
            
            logger.info("\n🌍 シンボル別比較 (1年分):")
            for symbol, data in all_results['symbol_comparison'].items():
                logger.info(f"  {symbol}:")
                for tf, count in data.items():
                    logger.info(f"    {tf}: {count}件")
            
            logger.info(f"\n⏱️ レート制限:")
            rate_data = all_results['rate_limits']
            logger.info(f"  最大連続リクエスト: {rate_data['total_requests']}件")
            logger.info(f"  実行時間: {rate_data['duration_seconds']:.1f}秒")
            logger.info(f"  平均レート: {rate_data['rate_per_second']:.2f} リクエスト/秒")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ テスト実行中にエラーが発生: {e}")
            return False


async def main():
    """メイン関数"""
    tester = MaxRecordsTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
