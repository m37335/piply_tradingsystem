"""
テクニカル指標計算の差分検知サービス

責任:
- 未計算データの検知
- 差分計算対象の特定
- 計算状態の管理
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

import pytz
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DiffDetectionService:
    """
    テクニカル指標計算の差分検知サービス
    
    責任:
    - 未計算データの検知
    - 差分計算対象の特定
    - 計算状態の管理
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.price_repo = PriceDataRepositoryImpl(session)
        
        # 各時間足のデータソースマッピング
        self.timeframe_sources = {
            "5m": ["yahoo_finance_5m_continuous", "yahoo_finance_5m_differential"],
            "1h": ["yahoo_finance_1h_differential"],
            "4h": ["yahoo_finance_4h_differential"],
            "1d": ["yahoo_finance_1d_differential"]
        }
    
    async def detect_calculation_differences(self) -> Dict[str, int]:
        """
        各時間足の未計算データ件数を検知
        
        Returns:
            Dict[str, int]: 時間足別の未計算件数
        """
        try:
            logger.info("🔍 差分検知を開始...")
            differences = {}
            
            for timeframe, sources in self.timeframe_sources.items():
                # 未計算データの件数を取得
                count = await self._count_uncalculated_data(sources)
                differences[timeframe] = count
                logger.info(f"📊 {timeframe}: {count}件の未計算データを検出")
            
            total_uncalculated = sum(differences.values())
            logger.info(f"📈 総未計算件数: {total_uncalculated}件")
            
            return differences
            
        except Exception as e:
            logger.error(f"❌ 差分検知エラー: {e}")
            return {}
    
    async def get_uncalculated_data(
        self, 
        timeframe: str, 
        limit: Optional[int] = None
    ) -> List[PriceDataModel]:
        """
        指定時間足の未計算データを取得
        
        Args:
            timeframe: 時間足（"5m", "1h", "4h", "1d"）
            limit: 取得件数制限
            
        Returns:
            List[PriceDataModel]: 未計算データのリスト
        """
        try:
            if timeframe not in self.timeframe_sources:
                logger.error(f"❌ 無効な時間足: {timeframe}")
                return []
            
            sources = self.timeframe_sources[timeframe]
            logger.info(f"📥 {timeframe}の未計算データを取得中...")
            
            # 未計算データを取得
            query = select(PriceDataModel).where(
                and_(
                    PriceDataModel.data_source.in_(sources),
                    PriceDataModel.technical_indicators_calculated.is_(False)
                )
            ).order_by(PriceDataModel.timestamp.asc())
            
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            uncalculated_data = result.scalars().all()
            
            logger.info(f"✅ {timeframe}: {len(uncalculated_data)}件の未計算データを取得")
            return uncalculated_data
            
        except Exception as e:
            logger.error(f"❌ 未計算データ取得エラー: {e}")
            return []
    
    async def update_calculation_flags(
        self, 
        processed_data: List[PriceDataModel],
        version: int = 1
    ) -> bool:
        """
        計算完了フラグを更新
        
        Args:
            processed_data: 計算処理したデータのリスト
            version: 計算バージョン
            
        Returns:
            bool: 更新成功時True
        """
        try:
            if not processed_data:
                logger.warning("⚠️ 更新対象データがありません")
                return True
            
            current_time = datetime.now(pytz.timezone("Asia/Tokyo"))
            
            # フラグを更新
            for data in processed_data:
                data.technical_indicators_calculated = True
                data.technical_indicators_calculated_at = current_time
                data.technical_indicators_version = version
            
            # バッチ更新
            await self.price_repo.update_batch(processed_data)
            
            logger.info(f"✅ 計算フラグ更新完了: {len(processed_data)}件")
            return True
            
        except Exception as e:
            logger.error(f"❌ 計算フラグ更新エラー: {e}")
            return False
    
    async def get_calculation_status(self) -> Dict[str, Any]:
        """
        計算状況の統計を取得
        
        Returns:
            Dict[str, Any]: 計算状況の詳細
        """
        try:
            logger.info("📊 計算状況の統計を取得中...")
            
            # 全体の統計
            total_query = select(func.count(PriceDataModel.id))
            total_result = await self.session.execute(total_query)
            total_count = total_result.scalar()
            
            # 計算済みの統計
            calculated_query = select(func.count(PriceDataModel.id)).where(
                PriceDataModel.technical_indicators_calculated.is_(True)
            )
            calculated_result = await self.session.execute(calculated_query)
            calculated_count = calculated_result.scalar()
            
            # 未計算の統計
            uncalculated_count = total_count - calculated_count
            
            # 時間足別の統計
            timeframe_stats = {}
            for timeframe, sources in self.timeframe_sources.items():
                calculated_query = select(func.count(PriceDataModel.id)).where(
                    and_(
                        PriceDataModel.data_source.in_(sources),
                        PriceDataModel.technical_indicators_calculated.is_(True)
                    )
                )
                calculated_result = await self.session.execute(calculated_query)
                calculated = calculated_result.scalar()
                
                total_query = select(func.count(PriceDataModel.id)).where(
                    PriceDataModel.data_source.in_(sources)
                )
                total_result = await self.session.execute(total_query)
                total = total_result.scalar()
                
                progress = (calculated / total * 100) if total > 0 else 0
                timeframe_stats[timeframe] = {
                    "total": total,
                    "calculated": calculated,
                    "uncalculated": total - calculated,
                    "progress": progress
                }
            
            status = {
                "total_records": total_count,
                "calculated_records": calculated_count,
                "uncalculated_records": uncalculated_count,
                "overall_progress": (
                    (calculated_count / total_count * 100) if total_count > 0 else 0
                ),
                "timeframe_stats": timeframe_stats,
                "last_updated": (
                    datetime.now(pytz.timezone("Asia/Tokyo")).isoformat()
                )
            }
            
            progress_percent = status['overall_progress']
            logger.info(
                f"📊 計算状況: {calculated_count}/{total_count} ({progress_percent:.1f}%)"
            )
            return status
            
        except Exception as e:
            logger.error(f"❌ 計算状況取得エラー: {e}")
            return {}
    
    async def _count_uncalculated_data(self, sources: List[str]) -> int:
        """
        指定データソースの未計算データ件数を取得
        
        Args:
            sources: データソースのリスト
            
        Returns:
            int: 未計算データ件数
        """
        try:
            query = select(func.count(PriceDataModel.id)).where(
                and_(
                    PriceDataModel.data_source.in_(sources),
                    PriceDataModel.technical_indicators_calculated.is_(False)
                )
            )
            
            result = await self.session.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"❌ 未計算データ件数取得エラー: {e}")
            return 0
    
    async def reset_calculation_flags(self, timeframe: Optional[str] = None) -> bool:
        """
        計算フラグをリセット
        
        Args:
            timeframe: 特定の時間足のみリセット（Noneの場合は全件）
            
        Returns:
            bool: リセット成功時True
        """
        try:
            if timeframe:
                if timeframe not in self.timeframe_sources:
                    logger.error(f"❌ 無効な時間足: {timeframe}")
                    return False
                
                sources = self.timeframe_sources[timeframe]
                query = select(PriceDataModel).where(
                    PriceDataModel.data_source.in_(sources)
                )
                logger.info(f"🔄 {timeframe}の計算フラグをリセット中...")
            else:
                query = select(PriceDataModel)
                logger.info("🔄 全時間足の計算フラグをリセット中...")
            
            result = await self.session.execute(query)
            all_data = result.scalars().all()
            
            # フラグをリセット
            for data in all_data:
                data.technical_indicators_calculated = False
                data.technical_indicators_calculated_at = None
                data.technical_indicators_version = 0
            
            # バッチ更新
            await self.price_repo.update_batch(all_data)
            
            logger.info(f"✅ 計算フラグリセット完了: {len(all_data)}件")
            return True
            
        except Exception as e:
            logger.error(f"❌ 計算フラグリセットエラー: {e}")
            return False
