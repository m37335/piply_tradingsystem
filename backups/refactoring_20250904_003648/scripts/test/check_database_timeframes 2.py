"""
データベース時間足確認スクリプト

データベースに保存されている時間足データを確認し、
どの時間足のデータが利用可能かを調査する
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseTimeframeChecker:
    """データベース時間足確認器"""

    async def check_database_timeframes(self) -> Dict:
        """データベースの時間足データを確認"""
        logger.info("=== データベース時間足確認開始 ===")

        try:
            # データベース接続
            await db_manager.initialize("sqlite+aiosqlite:///./data/exchange_analytics.db")
            logger.info("✅ データベース接続完了")

            # データベース構造確認
            structure_info = await self._check_database_structure()
            
            # 時間足データ確認
            timeframe_info = await self._check_timeframe_data()
            
            # データベース接続終了
            await db_manager.close()
            
            return {
                "structure": structure_info,
                "timeframes": timeframe_info
            }

        except Exception as e:
            logger.error(f"時間足確認エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _check_database_structure(self) -> Dict:
        """データベース構造確認"""
        try:
            async with db_manager.get_session() as session:
                # テーブル一覧取得
                query = text("SELECT name FROM sqlite_master WHERE type='table'")
                result = await session.execute(query)
                tables = [row[0] for row in result.fetchall()]
                
                logger.info(f"テーブル一覧: {tables}")
                
                # price_dataテーブルの構造確認
                if 'price_data' in tables:
                    query = text("PRAGMA table_info(price_data)")
                    result = await session.execute(query)
                    columns = [{"name": row[1], "type": row[2]} for row in result.fetchall()]
                    
                    logger.info(f"price_dataテーブル構造: {columns}")
                    
                    return {
                        "tables": tables,
                        "price_data_columns": columns
                    }
                else:
                    return {
                        "tables": tables,
                        "price_data_columns": []
                    }

        except Exception as e:
            logger.error(f"データベース構造確認エラー: {e}")
            return {"error": str(e)}

    async def _check_timeframe_data(self) -> Dict:
        """時間足データ確認"""
        try:
            async with db_manager.get_session() as session:
                # 最新のデータを取得して時間間隔を分析
                query = text("""
                    SELECT 
                        timestamp,
                        currency_pair,
                        open_price,
                        high_price,
                        low_price,
                        close_price
                    FROM price_data 
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                
                result = await session.execute(query)
                rows = result.fetchall()
                
                if not rows:
                    return {"error": "データが見つかりません"}
                
                # データをDataFrameに変換
                data = pd.DataFrame(rows, columns=[
                    "timestamp", "currency_pair", "open_price", "high_price", "low_price", "close_price"
                ])
                
                # 時間間隔を分析
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.sort_values('timestamp')
                
                # 時間間隔を計算
                time_diffs = data['timestamp'].diff().dropna()
                
                # 時間間隔の統計
                timeframe_stats = {
                    "total_records": len(data),
                    "date_range": f"{data['timestamp'].min()} - {data['timestamp'].max()}",
                    "time_diffs": {
                        "mean": str(time_diffs.mean()),
                        "median": str(time_diffs.median()),
                        "min": str(time_diffs.min()),
                        "max": str(time_diffs.max()),
                        "mode": str(time_diffs.mode().iloc[0] if len(time_diffs.mode()) > 0 else "N/A")
                    }
                }
                
                # 時間足の推定
                median_diff = time_diffs.median()
                if median_diff <= timedelta(minutes=1):
                    estimated_timeframe = "1分足"
                elif median_diff <= timedelta(minutes=5):
                    estimated_timeframe = "5分足"
                elif median_diff <= timedelta(minutes=15):
                    estimated_timeframe = "15分足"
                elif median_diff <= timedelta(hours=1):
                    estimated_timeframe = "1時間足"
                elif median_diff <= timedelta(hours=4):
                    estimated_timeframe = "4時間足"
                elif median_diff <= timedelta(days=1):
                    estimated_timeframe = "日足"
                else:
                    estimated_timeframe = "不明"
                
                timeframe_stats["estimated_timeframe"] = estimated_timeframe
                
                # 通貨ペア別のデータ量確認
                currency_query = text("""
                    SELECT 
                        currency_pair,
                        COUNT(*) as count,
                        MIN(timestamp) as min_date,
                        MAX(timestamp) as max_date
                    FROM price_data 
                    GROUP BY currency_pair
                    ORDER BY count DESC
                """)
                
                currency_result = await session.execute(currency_query)
                currency_stats = [
                    {
                        "currency_pair": row[0],
                        "count": row[1],
                        "date_range": f"{row[2]} - {row[3]}"
                    }
                    for row in currency_result.fetchall()
                ]
                
                timeframe_stats["currency_stats"] = currency_stats
                
                logger.info(f"推定時間足: {estimated_timeframe}")
                logger.info(f"データ件数: {len(data)}件")
                logger.info(f"時間間隔の中央値: {median_diff}")
                
                return timeframe_stats

        except Exception as e:
            logger.error(f"時間足データ確認エラー: {e}")
            return {"error": str(e)}


async def main():
    """メイン関数"""
    checker = DatabaseTimeframeChecker()
    results = await checker.check_database_timeframes()
    
    if "error" in results:
        print(f"\n❌ 確認エラー: {results['error']}")
        return
    
    print("\n=== データベース時間足確認結果 ===")
    
    # データベース構造
    print(f"\n📊 データベース構造:")
    structure = results["structure"]
    print(f"  テーブル一覧: {structure['tables']}")
    if structure['price_data_columns']:
        print(f"  price_dataテーブル構造:")
        for col in structure['price_data_columns']:
            print(f"    {col['name']}: {col['type']}")
    
    # 時間足情報
    print(f"\n⏰ 時間足情報:")
    timeframes = results["timeframes"]
    if "error" not in timeframes:
        print(f"  推定時間足: {timeframes['estimated_timeframe']}")
        print(f"  総データ件数: {timeframes['total_records']}件")
        print(f"  データ期間: {timeframes['date_range']}")
        print(f"  時間間隔統計:")
        for key, value in timeframes['time_diffs'].items():
            print(f"    {key}: {value}")
        
        print(f"\n💱 通貨ペア別統計:")
        for currency in timeframes['currency_stats']:
            print(f"  {currency['currency_pair']}: {currency['count']}件 ({currency['date_range']})")
    else:
        print(f"  エラー: {timeframes['error']}")


if __name__ == "__main__":
    asyncio.run(main())
