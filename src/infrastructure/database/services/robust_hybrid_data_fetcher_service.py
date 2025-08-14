#!/usr/bin/env python3
"""
堅牢なハイブリッドデータ取得サービス
データ欠損を考慮した多層補完戦略
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from ...external_apis.yahoo_finance_client import YahooFinanceClient
from ...database.models.price_data_model import PriceDataModel
from ...database.repositories.price_data_repository_impl import PriceDataRepositoryImpl
from ...database.services.timeframe_aggregator_service import TimeframeAggregatorService
from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class RobustHybridDataFetcherService:
    """
    堅牢なハイブリッドデータ取得サービス
    
    責任:
    - 多層のデータ取得戦略
    - 欠損データの自動補完
    - 代替集計元の活用
    """

    def __init__(self, session: AsyncSession, currency_pair: str = "USD/JPY"):
        self.session = session
        self.currency_pair = currency_pair
        self.yahoo_client = YahooFinanceClient()
        self.price_repo = PriceDataRepositoryImpl(session)
        self.aggregator = TimeframeAggregatorService(session, currency_pair)

        # 時間足設定（充足率に基づく優先順位）
        self.timeframes = {
            "4h": {"period": "60d", "interval": "4h", "description": "4時間足", "priority": 1},
            "1d": {"period": "365d", "interval": "1d", "description": "日足", "priority": 2},
            "1h": {"period": "30d", "interval": "1h", "description": "1時間足", "priority": 3},
            "5m": {"period": "7d", "interval": "5m", "description": "5分足", "priority": 4},
        }

        # 多層補完戦略
        self.completion_strategy = {
            "4h": {
                "primary": "direct",  # 直接取得優先（充足率99.4%）
                "fallback": ["from_1h", "from_5m"],  # 1時間足→5分足の順で補完
                "min_data_points": {"from_1h": 4, "from_5m": 48}
            },
            "1d": {
                "primary": "direct",  # 直接取得優先（充足率99.2%）
                "fallback": ["from_4h", "from_1h", "from_5m"],  # 4時間足→1時間足→5分足の順で補完
                "min_data_points": {"from_4h": 6, "from_1h": 24, "from_5m": 288}
            },
            "1h": {
                "primary": "direct",  # 直接取得優先（充足率96.8%）
                "fallback": ["from_5m"],  # 5分足で補完
                "min_data_points": {"from_5m": 12}
            },
            "5m": {
                "primary": "direct",  # 直接取得のみ（充足率91.7%だが他から集計不可）
                "fallback": [],
                "min_data_points": {}
            }
        }

        logger.info(f"Initialized RobustHybridDataFetcherService for {currency_pair}")

    async def fetch_all_timeframes_robust(self) -> Dict[str, Dict]:
        """
        堅牢な方式で全時間足データ取得
        
        Returns:
            Dict[str, Dict]: 各時間足の取得結果詳細
        """
        results = {}
        
        try:
            logger.info("🚀 堅牢なハイブリッド方式で全時間足データ取得開始")
            
            # 優先順位順に処理
            sorted_timeframes = sorted(
                self.timeframes.items(), 
                key=lambda x: x[1]["priority"]
            )
            
            for timeframe, config in sorted_timeframes:
                logger.info(f"📊 {timeframe}時間足処理開始（優先度: {config['priority']}）")
                
                result = await self._fetch_timeframe_robust(timeframe)
                results[timeframe] = result
                
                logger.info(f"✅ {timeframe}処理完了: {result['total_count']}件")
            
            logger.info(f"🎉 堅牢なハイブリッド取得完了")
            return results
            
        except Exception as e:
            logger.error(f"❌ 堅牢なハイブリッド取得エラー: {e}")
            return results

    async def _fetch_timeframe_robust(self, timeframe: str) -> Dict:
        """
        特定時間足を堅牢な方式で取得
        
        Args:
            timeframe: 時間足
            
        Returns:
            Dict: 取得結果詳細
        """
        result = {
            "timeframe": timeframe,
            "direct_count": 0,
            "fallback_counts": {},
            "total_count": 0,
            "strategy_used": [],
            "errors": []
        }
        
        try:
            strategy = self.completion_strategy[timeframe]
            
            # 1. プライマリ戦略（直接取得）
            if strategy["primary"] == "direct":
                direct_count = await self._fetch_direct_timeframe(timeframe)
                result["direct_count"] = direct_count
                result["strategy_used"].append("direct")
                
                if direct_count > 0:
                    logger.info(f"   ✅ {timeframe}直接取得成功: {direct_count}件")
                else:
                    logger.warning(f"   ⚠️ {timeframe}直接取得失敗")
            
            # 2. フォールバック戦略
            for fallback_method in strategy["fallback"]:
                try:
                    fallback_count = await self._execute_fallback_strategy(
                        timeframe, fallback_method, strategy["min_data_points"]
                    )
                    
                    if fallback_count > 0:
                        result["fallback_counts"][fallback_method] = fallback_count
                        result["strategy_used"].append(fallback_method)
                        logger.info(f"   🔧 {timeframe}{fallback_method}補完成功: {fallback_count}件")
                    else:
                        logger.warning(f"   ⚠️ {timeframe}{fallback_method}補完失敗")
                        
                except Exception as e:
                    error_msg = f"{fallback_method}補完エラー: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(f"   ❌ {timeframe}{error_msg}")
            
            # 3. 合計計算
            result["total_count"] = (
                result["direct_count"] + 
                sum(result["fallback_counts"].values())
            )
            
            return result
            
        except Exception as e:
            error_msg = f"堅牢取得エラー: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(f"❌ {timeframe}{error_msg}")
            return result

    async def _execute_fallback_strategy(
        self, 
        target_timeframe: str, 
        method: str, 
        min_data_points: Dict[str, int]
    ) -> int:
        """
        フォールバック戦略を実行
        
        Args:
            target_timeframe: 対象時間足
            method: 補完方法
            min_data_points: 最小データポイント要件
            
        Returns:
            int: 補完件数
        """
        try:
            if method == "from_5m":
                return await self._aggregate_from_5m(target_timeframe, min_data_points.get("from_5m", 0))
            elif method == "from_1h":
                return await self._aggregate_from_1h(target_timeframe, min_data_points.get("from_1h", 0))
            elif method == "from_4h":
                return await self._aggregate_from_4h(target_timeframe, min_data_points.get("from_4h", 0))
            else:
                logger.warning(f"⚠️ 未対応のフォールバック方法: {method}")
                return 0
                
        except Exception as e:
            logger.error(f"❌ フォールバック戦略実行エラー: {e}")
            return 0

    async def _aggregate_from_5m(self, target_timeframe: str, min_points: int) -> int:
        """5分足から集計"""
        try:
            # 5分足データを取得
            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                datetime.now() - timedelta(days=7),
                datetime.now(),
                self.currency_pair,
                "5m",
                1000
            )
            
            if len(m5_data) < min_points:
                logger.warning(f"⚠️ {target_timeframe}集計用5分足データ不足: {len(m5_data)}件 < {min_points}件")
                return 0
            
            # 集計実行
            if target_timeframe == "1h":
                aggregated_data = await self.aggregator.aggregate_1h_data(m5_data)
            elif target_timeframe == "4h":
                aggregated_data = await self.aggregator.aggregate_4h_data(m5_data)
            elif target_timeframe == "1d":
                aggregated_data = await self.aggregator.aggregate_1d_data(m5_data)
            else:
                return 0
            
            return await self._save_aggregated_data(aggregated_data, target_timeframe, "from_5m")
            
        except Exception as e:
            logger.error(f"❌ 5分足からの集計エラー: {e}")
            return 0

    async def _aggregate_from_1h(self, target_timeframe: str, min_points: int) -> int:
        """1時間足から集計"""
        try:
            # 1時間足データを取得
            h1_data = await self.price_repo.find_by_date_range_and_timeframe(
                datetime.now() - timedelta(days=30),
                datetime.now(),
                self.currency_pair,
                "1h",
                1000
            )
            
            if len(h1_data) < min_points:
                logger.warning(f"⚠️ {target_timeframe}集計用1時間足データ不足: {len(h1_data)}件 < {min_points}件")
                return 0
            
            # 4時間足への集計のみ対応
            if target_timeframe == "4h":
                aggregated_data = await self._aggregate_1h_to_4h(h1_data)
                return await self._save_aggregated_data(aggregated_data, target_timeframe, "from_1h")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ 1時間足からの集計エラー: {e}")
            return 0

    async def _aggregate_from_4h(self, target_timeframe: str, min_points: int) -> int:
        """4時間足から集計"""
        try:
            # 4時間足データを取得
            h4_data = await self.price_repo.find_by_date_range_and_timeframe(
                datetime.now() - timedelta(days=60),
                datetime.now(),
                self.currency_pair,
                "4h",
                1000
            )
            
            if len(h4_data) < min_points:
                logger.warning(f"⚠️ {target_timeframe}集計用4時間足データ不足: {len(h4_data)}件 < {min_points}件")
                return 0
            
            # 日足への集計のみ対応
            if target_timeframe == "1d":
                aggregated_data = await self._aggregate_4h_to_1d(h4_data)
                return await self._save_aggregated_data(aggregated_data, target_timeframe, "from_4h")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ 4時間足からの集計エラー: {e}")
            return 0

    async def _aggregate_1h_to_4h(self, h1_data: List[PriceDataModel]) -> List[PriceDataModel]:
        """1時間足から4時間足への集計"""
        # 実装は簡略化（実際はTimeframeAggregatorServiceに追加する必要あり）
        return []

    async def _aggregate_4h_to_1d(self, h4_data: List[PriceDataModel]) -> List[PriceDataModel]:
        """4時間足から日足への集計"""
        # 実装は簡略化（実際はTimeframeAggregatorServiceに追加する必要あり）
        return []

    async def _save_aggregated_data(
        self, 
        aggregated_data: List[PriceDataModel], 
        timeframe: str, 
        source_method: str
    ) -> int:
        """集計データを保存"""
        if not aggregated_data:
            return 0
        
        saved_count = 0
        for data in aggregated_data:
            # データソースを更新
            data.data_source = f"Yahoo Finance ({timeframe.upper()}) Aggregated ({source_method})"
            
            # 重複チェック
            existing = await self.price_repo.find_by_timestamp_and_source(
                data.timestamp,
                self.currency_pair,
                data.data_source
            )
            
            if not existing:
                await self.price_repo.save(data)
                saved_count += 1
        
        return saved_count

    async def _fetch_direct_timeframe(self, timeframe: str) -> int:
        """時間足を直接取得"""
        try:
            config = self.timeframes[timeframe]
            
            data = await self.yahoo_client.get_historical_data(
                self.currency_pair,
                period=config["period"],
                interval=config["interval"]
            )
            
            if data is None or data.empty:
                return 0
            
            saved_count = 0
            for _, row in data.iterrows():
                price_data = self._create_price_data_model(row, timeframe, "direct")
                
                existing = await self.price_repo.find_by_timestamp_and_source(
                    price_data.timestamp,
                    self.currency_pair,
                    price_data.data_source
                )
                
                if not existing:
                    await self.price_repo.save(price_data)
                    saved_count += 1
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ {timeframe}直接取得エラー: {e}")
            return 0

    def _create_price_data_model(
        self, row: pd.Series, timeframe: str, source_type: str
    ) -> PriceDataModel:
        """価格データモデルを作成"""
        return PriceDataModel(
            currency_pair=self.currency_pair,
            timestamp=row.name,
            open_price=row["Open"],
            high_price=row["High"],
            low_price=row["Low"],
            close_price=row["Close"],
            volume=row.get("Volume", 1000000),
            data_source=f"Yahoo Finance ({timeframe.upper()}) {source_type.title()}",
            data_timestamp=row.name,
            fetched_at=datetime.now(),
        )
