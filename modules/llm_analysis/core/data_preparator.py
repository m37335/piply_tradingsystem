"""
データベース連携型データ準備器

TimescaleDBから複数時間足の価格データを取得し、
ルールベース売買システム用にデータを準備・整形する。
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import numpy as np
except ImportError:
    np = None

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_collection.utils.timezone_utils import TimezoneUtils
from .technical_calculator import TechnicalIndicatorCalculator


class LLMDataPreparator:
    """LLM分析用データ準備器（ルールベース売買システム用）"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        # データベース接続文字列を設定（環境変数から取得）
        import os
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # dotenvが利用できない場合は環境変数を直接使用
        
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'trading_system')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'Postgres_Secure_2025!')
        
        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.connection_manager = DatabaseConnectionManager(connection_string)
        self.timezone_utils = TimezoneUtils()
        self.technical_calculator = TechnicalIndicatorCalculator()
        self._initialized = False
        
        # 分析タイプ別設定
        self.analysis_configs = {
            "trend_direction": {
                "timeframes": ["1d", "4h"],
                "lookback_hours": 8760,  # 1年間（365日 × 24時間）
                "max_data_points": 400   # 1年分の日足データ用
            },
            "zone_decision": {
                "timeframes": ["1h"],
                "lookback_hours": 72,   # 3日間
                "max_data_points": 100
            },
            "timing_execution": {
                "timeframes": ["5m"],
                "lookback_hours": 24,   # 1日間
                "max_data_points": 300
            },
            "trend_reinforcement": {
                "timeframes": ["5m", "15m", "1h", "4h", "1d"],
                "lookback_hours": 24,   # 1日間
                "max_data_points": 500
            }
        }

    async def initialize(self) -> None:
        """データベース接続を初期化"""
        if not self._initialized:
            try:
                await self.connection_manager.initialize()
                self._initialized = True
                self.logger.info("✅ データ準備器の初期化完了")
            except Exception as e:
                self.logger.error(f"❌ データ準備器の初期化エラー: {e}")
                raise

    async def prepare_analysis_data(
        self,
        analysis_type: str,
        symbol: str = 'USDJPY=X',
        timeframes: Optional[List[str]] = None
    ) -> Dict:
        """
        分析用データの準備
        
        Args:
            analysis_type: 分析タイプ (trend_direction, zone_decision, timing_execution, trend_reinforcement)
            symbol: 通貨ペアシンボル
            timeframes: 時間足リスト（指定しない場合は設定から取得）
        
        Returns:
            分析用データ辞書
        """
        if not self._initialized:
            await self.initialize()
        self.logger.info(f"📊 分析データ準備開始: {analysis_type} for {symbol}")
        
        try:
            # 分析設定の取得
            config = self.analysis_configs.get(analysis_type)
            if not config:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            # 時間足の決定
            if timeframes is None:
                timeframes = config["timeframes"]
            
            if timeframes is None:
                raise ValueError("timeframesが設定されていません")
            
            # データ取得期間の計算
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=config["lookback_hours"])
            
            # 各時間足のデータを取得
            timeframe_data = {}
            for timeframe in timeframes:
                self.logger.info(f"⏰ {timeframe}足データ取得中...")
                
                # データベースからデータ取得
                raw_data = await self._fetch_timeframe_data(
                    symbol, timeframe, start_time, end_time
                )
                
                # データが空かどうかをチェック
                is_empty = False
                try:
                    if pd is not None and hasattr(raw_data, 'empty'):
                        is_empty = getattr(raw_data, 'empty', True)
                    else:
                        is_empty = not raw_data or len(raw_data) == 0
                except (AttributeError, TypeError):
                    is_empty = not raw_data or len(raw_data) == 0
                
                if is_empty:
                    self.logger.warning(f"⚠️ {timeframe}足データが空です")
                    continue
                
                # データ品質チェック
                quality_score = self._check_data_quality(raw_data, timeframe)
                
                # テクニカル指標計算
                processed_data = self.technical_calculator.calculate_all_indicators(
                    {timeframe: raw_data}
                )[timeframe]
                
                # データ点数制限
                if len(processed_data) > config["max_data_points"]:
                    processed_data = processed_data.tail(config["max_data_points"])
                
                timeframe_data[timeframe] = {
                    "data": processed_data,
                    "count": len(processed_data),
                    "latest": processed_data.index[-1] if not processed_data.empty else None,
                    "range": (processed_data.index[0], processed_data.index[-1]) if not processed_data.empty else None,
                    "quality_score": quality_score
                }
                
                self.logger.info(f"✅ {timeframe}足: {len(processed_data)}件, 品質スコア: {quality_score:.2f}")
            
            # メタデータの作成
            metadata = {
                "analysis_type": analysis_type,
                "symbol": symbol,
                "lookback_hours": config["lookback_hours"],
                "data_quality": np.mean([tf["quality_score"] for tf in timeframe_data.values()]) if np is not None else sum([tf["quality_score"] for tf in timeframe_data.values()]) / len(timeframe_data),
                "prepared_at": datetime.now(timezone.utc),
                "timeframes_available": list(timeframe_data.keys())
            }
            
            result = {
                "symbol": symbol,
                "timeframes": timeframe_data,
                "metadata": metadata
            }
            
            self.logger.info(f"📊 分析データ準備完了: {len(timeframe_data)}個の時間足")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ データ準備エラー: {e}")
            raise

    async def _fetch_timeframe_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ):
        """
        指定された時間足のデータをデータベースから取得
        
        Args:
            symbol: 通貨ペアシンボル
            timeframe: 時間足
            start_time: 開始時刻
            end_time: 終了時刻
        
        Returns:
            価格データのDataFrame
        """
        try:
            # SQLクエリの構築（asyncpg用のプレースホルダー）
            query = """
            SELECT 
                timestamp,
                open,
                high,
                low,
                close,
                volume,
                data_quality_score
            FROM price_data 
            WHERE symbol = $1 
                AND timeframe = $2 
                AND timestamp >= $3 
                AND timestamp <= $4
            ORDER BY timestamp ASC
            """
            
            # データベースからデータ取得
            rows = await self.connection_manager.execute_query(
                query, symbol, timeframe, start_time, end_time
            )
            
            if not rows:
                return pd.DataFrame() if pd is not None else []
            
            if pd is None:
                # pandasが利用できない場合は辞書のリストを返す
                return [dict(zip(['timestamp', 'open', 'high', 'low', 'close', 'volume', 'data_quality_score'], row)) for row in rows]
            
            # DataFrameに変換
            df = pd.DataFrame(rows, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'data_quality_score'
            ])
            
            # インデックスをtimestampに設定
            df.set_index('timestamp', inplace=True)
            
            # データ型の変換
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            df['data_quality_score'] = pd.to_numeric(df['data_quality_score'], errors='coerce')
            
            # 欠損値の処理
            df = df.dropna()
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ データ取得エラー ({timeframe}): {e}")
            return pd.DataFrame() if pd is not None else []

    def _check_data_quality(self, data, timeframe: str) -> float:
        """
        データ品質のチェック
        
        Args:
            data: 価格データ（DataFrameまたは辞書のリスト）
            timeframe: 時間足
        
        Returns:
            品質スコア (0.0-1.0)
        """
        if pd is None:
            # pandasが利用できない場合は基本的なチェックのみ
            if not data or len(data) == 0:
                return 0.0
            return 0.8  # 基本的な品質スコア
        
        if data.empty:
            return 0.0
        
        try:
            quality_factors = []
            
            # 1. データ完全性チェック
            expected_columns = ['open', 'high', 'low', 'close', 'volume']
            completeness = sum(1 for col in expected_columns if col in data.columns) / len(expected_columns)
            quality_factors.append(completeness)
            
            # 2. 欠損値チェック
            missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
            quality_factors.append(1.0 - missing_ratio)
            
            # 3. 価格データの妥当性チェック
            price_columns = ['open', 'high', 'low', 'close']
            valid_prices = True
            for col in price_columns:
                if col in data.columns:
                    if (data[col] <= 0).any():
                        valid_prices = False
                        break
            quality_factors.append(1.0 if valid_prices else 0.0)
            
            # 4. 高値・安値の妥当性チェック
            if all(col in data.columns for col in ['high', 'low', 'open', 'close']):
                invalid_hl = (data['high'] < data['low']).any() or \
                           (data['high'] < data['open']).any() or \
                           (data['high'] < data['close']).any() or \
                           (data['low'] > data['open']).any() or \
                           (data['low'] > data['close']).any()
                quality_factors.append(0.0 if invalid_hl else 1.0)
            else:
                quality_factors.append(0.0)
            
            # 5. データ密度チェック（時間足に応じた期待データ数）
            expected_intervals = {
                '5m': 12,   # 1時間に12本
                '15m': 4,   # 1時間に4本
                '1h': 1,    # 1時間に1本
                '4h': 0.25, # 1時間に0.25本
                '1d': 0.042 # 1時間に0.042本
            }
            
            if timeframe in expected_intervals:
                # 最新24時間のデータ密度をチェック
                expected_count = int(24 * expected_intervals[timeframe])
                if len(data) >= expected_count:
                    recent_data = data.tail(expected_count)
                    density_score = min(1.0, len(recent_data) / expected_count)
                    quality_factors.append(density_score)
                else:
                    # データ数が少ない場合は、利用可能なデータ数で評価
                    density_score = min(1.0, len(data) / expected_count)
                    quality_factors.append(density_score)
            else:
                quality_factors.append(1.0)
            
            # 総合品質スコアの計算
            overall_score = np.mean(quality_factors) if np is not None else sum(quality_factors) / len(quality_factors)
            
            return max(0.0, min(1.0, overall_score))
            
        except Exception as e:
            self.logger.error(f"❌ データ品質チェックエラー: {e}")
            return 0.0

    async def get_latest_data_summary(self, symbol: str = 'USDJPY=X') -> Dict:
        """
        最新データのサマリーを取得
        
        Args:
            symbol: 通貨ペアシンボル
        
        Returns:
            最新データサマリー
        """
        try:
            # データベース接続の初期化
            await self.connection_manager.initialize()
            
            timeframes = ['5m', '15m', '1h', '4h', '1d']
            summary = {}
            
            for timeframe in timeframes:
                # 最新データを取得
                query = """
                SELECT 
                    timestamp,
                    close,
                    volume,
                    data_quality_score
                FROM price_data 
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp DESC
                LIMIT 1
                """
                
                rows = await self.connection_manager.execute_query(query, symbol, timeframe)
                row = rows[0] if rows else None
                
                if row:
                    summary[timeframe] = {
                        "latest_timestamp": row[0],
                        "latest_price": float(row[1]),
                        "latest_volume": int(row[2]) if row[2] else 0,
                        "quality_score": float(row[3]) if row[3] else 0.0
                    }
                else:
                    summary[timeframe] = None
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ 最新データサマリー取得エラー: {e}")
            return {}

    async def close(self):
        """リソースのクリーンアップ"""
        await self.connection_manager.close()
        self._initialized = False


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    preparator = LLMDataPreparator()
    
    try:
        # トレンド方向分析用データの準備
        print("🧪 トレンド方向分析用データ準備テスト...")
        trend_data = await preparator.prepare_analysis_data("trend_direction")
        print(f"✅ トレンド方向データ準備完了: {len(trend_data['timeframes'])}個の時間足")
        
        # 最新データサマリーの取得
        print("\n🧪 最新データサマリーテスト...")
        summary = await preparator.get_latest_data_summary()
        for tf, data in summary.items():
            if data:
                print(f"  {tf}: {data['latest_price']:.5f} @ {data['latest_timestamp']}")
            else:
                print(f"  {tf}: データなし")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        await preparator.close()


if __name__ == "__main__":
    asyncio.run(main())
