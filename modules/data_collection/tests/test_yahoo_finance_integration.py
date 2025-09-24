#!/usr/bin/env python3
"""
Yahoo Finance API 統合テスト

Yahoo Finance APIからのデータ取得をテストします。
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


class TestYahooFinanceIntegration:
    """Yahoo Finance API 統合テストクラス"""
    
    def __init__(self):
        self.provider = YahooFinanceProvider()
    
    async def test_health_check(self):
        """ヘルスチェックテスト"""
        logger.info("📡 ヘルスチェック実行中...")
        health = await self.provider.health_check()
        logger.info(f"✅ ヘルスチェック結果: {health}")
        return health
    
    async def test_available_symbols(self):
        """利用可能シンボルテスト"""
        logger.info("📋 利用可能シンボル確認中...")
        symbols = await self.provider.get_available_symbols()
        logger.info(f"✅ 利用可能シンボル数: {len(symbols)}")
        logger.info(f"📊 主要シンボル: {symbols[:10]}")
        return len(symbols) > 0
    
    async def test_latest_data(self):
        """最新データ取得テスト"""
        logger.info("💱 USD/JPY 最新データ取得中...")
        latest_result = await self.provider.get_latest_data("USDJPY=X", TimeFrame.M5)
        
        if latest_result.success:
            logger.info(f"✅ 最新データ取得成功: {len(latest_result.data)}件")
            if latest_result.data:
                latest = latest_result.data[0]
                logger.info(f"📈 最新価格: {latest.close} (時刻: {latest.timestamp})")
            return True
        else:
            logger.error(f"❌ 最新データ取得失敗: {latest_result.error_message}")
            return False
    
    async def test_historical_data(self):
        """履歴データ取得テスト"""
        logger.info("📊 USD/JPY 履歴データ取得中（過去1日）...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        historical_result = await self.provider.get_historical_data(
            symbol="USDJPY=X",
            timeframe=TimeFrame.M5,
            start_date=start_date,
            end_date=end_date
        )
        
        if historical_result.success:
            logger.info(f"✅ 履歴データ取得成功: {len(historical_result.data)}件")
            
            # データ品質チェック
            if historical_result.data:
                first_data = historical_result.data[0]
                last_data = historical_result.data[-1]
                
                logger.info(f"📅 データ期間: {first_data.timestamp} ～ {last_data.timestamp}")
                logger.info(f"💰 価格範囲: {min(d.close for d in historical_result.data):.3f} ～ {max(d.close for d in historical_result.data):.3f}")
                
                # データ品質スコアを計算
                quality_scores = [d.quality_score for d in historical_result.data if hasattr(d, 'quality_score')]
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    logger.info(f"🎯 平均品質スコア: {avg_quality:.3f}")
            
            return True
        else:
            logger.error(f"❌ 履歴データ取得失敗: {historical_result.error_message}")
            return False
    
    async def test_timeframe_max_records(self):
        """時間足別最大取得件数テスト"""
        logger.info("⏰ 時間足別最大取得件数確認中...")
        timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        results = {}
        
        for tf in timeframes:
            tf_result = await self.provider.get_historical_data(
                symbol="USDJPY=X",
                timeframe=tf,
                start_date=start_date,
                end_date=end_date
            )
            
            if tf_result.success:
                results[tf.value] = len(tf_result.data)
                logger.info(f"  {tf.value}: {len(tf_result.data)}件")
            else:
                results[tf.value] = 0
                logger.warning(f"  {tf.value}: 取得失敗 - {tf_result.error_message}")
        
        return results
    
    async def run_all_tests(self):
        """全テスト実行"""
        logger.info("🚀 Yahoo Finance API 統合テスト開始")
        
        test_results = {}
        
        try:
            # ヘルスチェック
            test_results['health_check'] = await self.test_health_check()
            
            # 利用可能シンボル
            test_results['available_symbols'] = await self.test_available_symbols()
            
            # 最新データ
            test_results['latest_data'] = await self.test_latest_data()
            
            # 履歴データ
            test_results['historical_data'] = await self.test_historical_data()
            
            # 時間足別最大取得件数
            test_results['timeframe_records'] = await self.test_timeframe_max_records()
            
            # 結果サマリー
            logger.info("📊 テスト結果サマリー:")
            for test_name, result in test_results.items():
                if test_name == 'timeframe_records':
                    logger.info(f"  {test_name}: {result}")
                else:
                    status = "✅ 成功" if result else "❌ 失敗"
                    logger.info(f"  {test_name}: {status}")
            
            # 全体の成功判定
            success_count = sum(1 for k, v in test_results.items() 
                              if k != 'timeframe_records' and v)
            total_tests = len([k for k in test_results.keys() if k != 'timeframe_records'])
            
            logger.info(f"🎯 テスト成功率: {success_count}/{total_tests}")
            
            if success_count == total_tests:
                logger.info("🎉 全テスト成功！")
                return True
            else:
                logger.warning("⚠️ 一部テストが失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"❌ テスト実行中にエラーが発生: {e}")
            return False


async def main():
    """メイン関数"""
    tester = TestYahooFinanceIntegration()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
