#!/usr/bin/env python3
"""
修正されたプロバイダーで全時間足データを収集・保存するスクリプト
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
from modules.data_collection.config.settings import TimeFrame
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def save_price_data(conn_manager, price_data_list):
    """価格データをデータベースに保存"""
    if not price_data_list:
        return 0
    
    saved_count = 0
    async with conn_manager.get_connection() as conn:
        for data in price_data_list:
            try:
                query = '''
                    INSERT INTO price_data (
                        symbol, timeframe, timestamp, open, close, high, low, volume, 
                        source, data_quality_score, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW()
                    )
                    ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE SET
                        open = EXCLUDED.open,
                        close = EXCLUDED.close,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        volume = EXCLUDED.volume,
                        source = EXCLUDED.source,
                        data_quality_score = EXCLUDED.data_quality_score,
                        updated_at = NOW()
                '''
                
                await conn.execute(
                    query,
                    data.symbol,
                    data.timeframe.value,
                    data.timestamp,
                    data.open,
                    data.close,
                    data.high,
                    data.low,
                    data.volume,
                    data.source,
                    data.quality_score
                )
                saved_count += 1
            except Exception as e:
                logger.error(f'保存エラー: {e}')
                continue
    
    return saved_count


async def collect_and_save_all_data():
    """全時間足のデータを収集・保存"""
    logger.info("📊 修正されたプロバイダーで全時間足データ収集・保存開始")
    logger.info("=" * 80)
    
    # プロバイダーとデータベース設定
    provider = YahooFinanceProvider()
    db_config = DatabaseConfig()
    connection_string = f'postgresql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}'
    
    conn_manager = DatabaseConnectionManager(
        connection_string=connection_string,
        min_connections=db_config.min_connections,
        max_connections=db_config.max_connections
    )
    
    symbol = 'USDJPY=X'
    
    # 各時間足の収集設定（API制限を考慮）
    collection_config = {
        TimeFrame.M5: timedelta(days=30),    # 5分足: 30日（最大60日）
        TimeFrame.M15: timedelta(days=30),   # 15分足: 30日（最大60日）
        TimeFrame.H1: timedelta(days=365),   # 1時間足: 1年（最大730日）
        TimeFrame.H4: timedelta(days=365),   # 4時間足: 1年（最大730日）
        TimeFrame.D1: timedelta(days=5*365)  # 日足: 5年（制限なし）
    }
    
    # 期待される件数（テスト結果から）
    expected_counts = {
        TimeFrame.M5: 5994,
        TimeFrame.M15: 2000,
        TimeFrame.H1: 6144,
        TimeFrame.H4: 1561,
        TimeFrame.D1: 1300
    }
    
    results = {}
    total_collected = 0
    total_saved = 0
    
    try:
        await conn_manager.initialize()
        
        for tf, duration in collection_config.items():
            logger.info(f"📈 {tf.value} データ収集・保存中...")
            
            # データ収集
            end_date = datetime.now(timezone.utc)
            start_date = end_date - duration
            
            logger.info(f"  📅 期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")
            
            collection_result = await provider.get_historical_data(symbol, tf, start_date, end_date)
            
            if collection_result.success and collection_result.data:
                collected_count = len(collection_result.data)
                logger.info(f"  ✅ 取得成功: {collected_count}件 (期待: {expected_counts[tf]}件)")
                
                # データ保存
                saved_count = await save_price_data(conn_manager, collection_result.data)
                logger.info(f"  💾 保存完了: {saved_count}件")
                
                # データ品質確認
                if collected_count > 0:
                    first_record = collection_result.data[0]
                    last_record = collection_result.data[-1]
                    logger.info(f"  📊 期間: {first_record.timestamp} ～ {last_record.timestamp}")
                    
                    # 時間間隔確認
                    if len(collection_result.data) >= 2:
                        time_diff = collection_result.data[1].timestamp - collection_result.data[0].timestamp
                        logger.info(f"  ⏰ 時間間隔: {time_diff}")
                
                results[tf.value] = {
                    'collected': collected_count,
                    'saved': saved_count,
                    'expected': expected_counts[tf],
                    'success': True
                }
                
                total_collected += collected_count
                total_saved += saved_count
                
            else:
                logger.error(f"  ❌ 取得失敗: {collection_result.error_message}")
                results[tf.value] = {
                    'collected': 0,
                    'saved': 0,
                    'expected': expected_counts[tf],
                    'success': False,
                    'error': collection_result.error_message
                }
        
        # 結果サマリー
        logger.info("=" * 80)
        logger.info("📊 データ収集・保存結果サマリー")
        logger.info("=" * 80)
        
        success_count = 0
        for tf_value, result in results.items():
            status = "✅ 成功" if result['success'] else "❌ 失敗"
            logger.info(f"{tf_value:>8}: {status}")
            logger.info(f"         取得: {result['collected']:>6}件 / 期待: {result['expected']:>6}件")
            logger.info(f"         保存: {result['saved']:>6}件")
            if result['success']:
                success_count += 1
        
        logger.info("")
        logger.info("📈 合計:")
        logger.info(f"  取得: {total_collected:>6}件")
        logger.info(f"  保存: {total_saved:>6}件")
        logger.info(f"  成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        if success_count == len(results) and total_saved > 0:
            logger.info("")
            logger.info("🎉 全時間足のデータ収集・保存が正常に完了しました！")
        else:
            logger.error("")
            logger.error("⚠️ 一部の時間足で問題が発生しました。")
        
    except Exception as e:
        logger.error(f"❌ データ収集エラー: {e}")
        raise
    finally:
        await conn_manager.close()


async def main():
    """メイン関数"""
    await collect_and_save_all_data()


if __name__ == "__main__":
    asyncio.run(main())
