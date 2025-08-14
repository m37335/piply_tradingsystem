"""
最新データ表示スクリプト

データベースの最新30件のUSD/JPY価格データを表示する
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from sqlalchemy import text

from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RecentDataViewer:
    """最新データ表示器"""

    def __init__(self):
        self.limit = 30

    async def show_recent_data(self) -> Dict:
        """最新データの表示"""
        logger.info("=== 最新データ表示開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 最新データ取得
            recent_data = await self._fetch_recent_data(self.limit)

            # データベース接続終了
            await db_manager.close()

            return {
                "recent_data": recent_data,
                "total_count": len(recent_data),
                "display_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"最新データ表示エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _fetch_recent_data(self, limit: int) -> list:
        """最新データの取得"""
        try:
            async with db_manager.get_session() as session:
                query = text(
                    """
                    SELECT 
                        timestamp,
                        currency_pair,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    FROM price_data 
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT :limit
                    """
                )

                result = await session.execute(query, {"limit": limit})
                rows = result.fetchall()

                if not rows:
                    return []

                # データを時系列順に並び替え（古い順）
                data = [
                    {
                        "timestamp": row[0],
                        "currency_pair": row[1],
                        "open": float(row[2]),
                        "high": float(row[3]),
                        "low": float(row[4]),
                        "close": float(row[5]),
                        "volume": float(row[6]) if row[6] else 0,
                    }
                    for row in rows
                ]

                # 時系列順にソート（古い順）
                data.sort(key=lambda x: x["timestamp"])

                return data

        except Exception as e:
            logger.error(f"最新データ取得エラー: {e}")
            return []


async def main():
    """メイン関数"""
    viewer = RecentDataViewer()
    results = await viewer.show_recent_data()

    if "error" in results:
        print(f"\n❌ 表示エラー: {results['error']}")
        return

    print("\n=== 最新30件のUSD/JPY価格データ ===")

    recent_data = results.get("recent_data", [])
    total_count = results.get("total_count", 0)

    print(f"\n📊 データ概要:")
    print(f"  表示件数: {total_count}件")

    if recent_data:
        print(f"  期間: {recent_data[0]['timestamp']} ～ {recent_data[-1]['timestamp']}")
        
        # 価格統計
        closes = [d["close"] for d in recent_data]
        highs = [d["high"] for d in recent_data]
        lows = [d["low"] for d in recent_data]
        
        print(f"  終値範囲: {min(closes):.2f} - {max(closes):.2f}")
        print(f"  高値範囲: {min(highs):.2f} - {max(highs):.2f}")
        print(f"  安値範囲: {min(lows):.2f} - {max(lows):.2f}")

    print(f"\n📈 詳細データ:")
    print(f"{'No.':<3} {'Timestamp':<25} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8} {'Volume':<10}")
    print("-" * 80)

    for i, data in enumerate(recent_data, 1):
        timestamp = data["timestamp"]
        # タイムスタンプを短縮表示
        if len(timestamp) > 19:
            timestamp = timestamp[:19]  # YYYY-MM-DD HH:MM:SS まで
        
        print(
            f"{i:<3} {timestamp:<25} "
            f"{data['open']:<8.2f} {data['high']:<8.2f} "
            f"{data['low']:<8.2f} {data['close']:<8.2f} "
            f"{data['volume']:<10.0f}"
        )

    # 価格変動の分析
    if len(recent_data) > 1:
        print(f"\n📊 価格変動分析:")
        
        # 終値の変動
        close_changes = []
        for i in range(1, len(recent_data)):
            change = recent_data[i]["close"] - recent_data[i-1]["close"]
            close_changes.append(change)
        
        if close_changes:
            positive_changes = sum(1 for c in close_changes if c > 0)
            negative_changes = sum(1 for c in close_changes if c < 0)
            zero_changes = sum(1 for c in close_changes if c == 0)
            
            print(f"  終値変動: +{positive_changes} -{negative_changes} ={zero_changes}")
            print(f"  平均変動: {sum(close_changes)/len(close_changes):.4f}")
            print(f"  最大上昇: {max(close_changes):.4f}")
            print(f"  最大下降: {min(close_changes):.4f}")
        
        # 価格範囲の分析
        price_ranges = [d["high"] - d["low"] for d in recent_data]
        if price_ranges:
            print(f"  価格範囲平均: {sum(price_ranges)/len(price_ranges):.4f}")
            print(f"  最大価格範囲: {max(price_ranges):.4f}")
            print(f"  最小価格範囲: {min(price_ranges):.4f}")

    # データの特徴
    print(f"\n🔍 データ特徴:")
    
    # 重複値の確認
    unique_closes = len(set(closes))
    unique_highs = len(set(highs))
    unique_lows = len(set(lows))
    
    print(f"  終値ユニーク値: {unique_closes}/{total_count}")
    print(f"  高値ユニーク値: {unique_highs}/{total_count}")
    print(f"  安値ユニーク値: {unique_lows}/{total_count}")
    
    # データの一貫性
    consistent_count = sum(
        1 for d in recent_data 
        if d["high"] >= d["low"] and d["high"] >= d["open"] and d["high"] >= d["close"]
        and d["low"] <= d["open"] and d["low"] <= d["close"]
    )
    print(f"  価格論理一貫性: {consistent_count}/{total_count} ({consistent_count/total_count*100:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())
