#!/usr/bin/env python3
"""
価格データクリーニングスクリプト

高値・安値矛盾を修正してデータ品質を向上させます。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PriceDataCleaner:
    """価格データクリーナー"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
    
    async def initialize(self):
        """初期化"""
        await self.connection_manager.initialize()
        logger.info("✅ データベース接続を初期化しました")
    
    async def clean_price_data(self, symbol: str = "USDJPY=X", timeframe: str = "1d"):
        """価格データのクリーニング"""
        logger.info(f"🧹 価格データクリーニング開始: {symbol} ({timeframe})")
        
        try:
            # 矛盾データを取得
            invalid_data = await self._get_invalid_data(symbol, timeframe)
            
            if not invalid_data:
                logger.info("✅ 修正が必要なデータはありません")
                return
            
            logger.info(f"📊 修正対象データ: {len(invalid_data)}件")
            
            # データを修正
            fixed_count = 0
            for record in invalid_data:
                fixed = await self._fix_price_record(record)
                if fixed:
                    fixed_count += 1
            
            logger.info(f"✅ データ修正完了: {fixed_count}/{len(invalid_data)}件")
            
            # 修正後の品質チェック
            await self._verify_fix(symbol, timeframe)
            
        except Exception as e:
            logger.error(f"❌ データクリーニングエラー: {e}")
            raise
    
    async def _get_invalid_data(self, symbol: str, timeframe: str):
        """矛盾データを取得"""
        query = """
        SELECT symbol, timeframe, timestamp, open, high, low, close, volume
        FROM price_data 
        WHERE symbol = $1 AND timeframe = $2
        AND (
            high < low OR
            high < open OR
            high < close OR
            low > open OR
            low > close
        )
        ORDER BY timestamp
        """
        
        async with self.connection_manager.get_connection() as conn:
            rows = await conn.fetch(query, symbol, timeframe)
            return [dict(row) for row in rows]
    
    async def _fix_price_record(self, record):
        """個別レコードの修正"""
        try:
            # 元の値
            original_open = float(record['open'])
            original_high = float(record['high'])
            original_low = float(record['low'])
            original_close = float(record['close'])
            
            # 修正ロジック
            # 1. 高値は open, high, low, close の最大値
            # 2. 安値は open, high, low, close の最小値
            corrected_high = max(original_open, original_high, original_low, original_close)
            corrected_low = min(original_open, original_high, original_low, original_close)
            
            # 修正が必要かチェック
            if corrected_high == original_high and corrected_low == original_low:
                return False  # 修正不要
            
            # データベースを更新
            update_query = """
            UPDATE price_data 
            SET high = $1, low = $2, updated_at = NOW()
            WHERE symbol = $3 AND timeframe = $4 AND timestamp = $5
            """
            
            async with self.connection_manager.get_connection() as conn:
                await conn.execute(update_query, corrected_high, corrected_low, 
                                 record['symbol'], record['timeframe'], record['timestamp'])
            
            logger.info(f"🔧 修正: {record['timestamp']} - H:{original_high:.5f}→{corrected_high:.5f}, L:{original_low:.5f}→{corrected_low:.5f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ レコード修正エラー ({record['timestamp']}): {e}")
            return False
    
    async def _verify_fix(self, symbol: str, timeframe: str):
        """修正結果の検証"""
        query = """
        SELECT COUNT(*) as invalid_count
        FROM price_data 
        WHERE symbol = $1 AND timeframe = $2
        AND (
            high < low OR
            high < open OR
            high < close OR
            low > open OR
            low > close
        )
        """
        
        async with self.connection_manager.get_connection() as conn:
            result = await conn.fetchrow(query, symbol, timeframe)
            invalid_count = result['invalid_count']
        
        if invalid_count == 0:
            logger.info("✅ 検証完了: すべての矛盾が修正されました")
        else:
            logger.warning(f"⚠️ 検証結果: {invalid_count}件の矛盾が残っています")
    
    async def get_quality_score(self, symbol: str, timeframe: str):
        """品質スコアの計算"""
        query = """
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN high < low OR high < open OR high < close OR low > open OR low > close THEN 1 ELSE 0 END) as invalid_count
        FROM price_data 
        WHERE symbol = $1 AND timeframe = $2
        """
        
        async with self.connection_manager.get_connection() as conn:
            result = await conn.fetchrow(query, symbol, timeframe)
            total_count = result['total_count']
            invalid_count = result['invalid_count']
        
        if total_count == 0:
            return 0.0
        
        # 品質スコア計算（矛盾がない場合1.0、矛盾がある場合減点）
        quality_score = 1.0 - (invalid_count / total_count)
        return quality_score
    
    async def close(self):
        """リソースの解放"""
        await self.connection_manager.close()
        logger.info("✅ データベース接続を閉じました")


async def main():
    """メイン関数"""
    cleaner = PriceDataCleaner()
    
    try:
        await cleaner.initialize()
        
        # 修正前の品質スコア
        before_score = await cleaner.get_quality_score("USDJPY=X", "1d")
        logger.info(f"📊 修正前の品質スコア: {before_score:.2f}")
        
        # データクリーニング実行
        await cleaner.clean_price_data("USDJPY=X", "1d")
        
        # 修正後の品質スコア
        after_score = await cleaner.get_quality_score("USDJPY=X", "1d")
        logger.info(f"📊 修正後の品質スコア: {after_score:.2f}")
        
        improvement = after_score - before_score
        logger.info(f"📈 品質スコア改善: +{improvement:.2f}")
        
    except Exception as e:
        logger.error(f"❌ メイン処理エラー: {e}")
        sys.exit(1)
    
    finally:
        await cleaner.close()


if __name__ == "__main__":
    asyncio.run(main())
