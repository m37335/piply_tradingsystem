#!/usr/bin/env python3
"""
経済指標データキャッシュ管理システム
API取得数を削減するためのキャッシュ機能
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories.analysis_cache_repository_impl import (
    AnalysisCacheRepositoryImpl,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EconomicCalendarCacheManager:
    """経済指標データキャッシュ管理クラス"""

    def __init__(self):
        self.session = None
        self.analysis_cache_repo = None

        # キャッシュ設定
        self.cache_ttl_hours = {
            "daily": 6,  # 日次データ: 6時間
            "weekly": 24,  # 週次データ: 24時間
            "monthly": 168,  # 月次データ: 1週間
        }

        # キャッシュ統計
        self.cache_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "api_calls_saved": 0,
            "last_cache_cleanup": None,
        }

    async def initialize(self):
        """初期化"""
        try:
            self.session = await get_async_session()
            self.analysis_cache_repo = AnalysisCacheRepositoryImpl(self.session)

            logger.info("✅ 経済指標キャッシュマネージャー初期化完了")

        except Exception as e:
            logger.error(f"❌ キャッシュマネージャー初期化エラー: {e}")
            raise

    async def close(self):
        """セッションクローズ"""
        if self.session:
            await self.session.close()

    async def get_cached_economic_events(
        self,
        from_date: str,
        to_date: str,
        countries: List[str],
        importances: List[str],
        cache_type: str = "daily",
    ) -> Optional[List[Dict[str, Any]]]:
        """
        キャッシュされた経済指標データを取得

        Args:
            from_date: 開始日（DD/MM/YYYY）
            to_date: 終了日（DD/MM/YYYY）
            countries: 対象国リスト
            importances: 重要度リスト
            cache_type: キャッシュタイプ（daily/weekly/monthly）

        Returns:
            Optional[List[Dict[str, Any]]]: キャッシュされたデータ、なければNone
        """
        try:
            # キャッシュキーを生成
            cache_key = self._generate_cache_key(
                from_date, to_date, countries, importances, cache_type
            )

            # 分析キャッシュから検索
            cached_analysis = await self.analysis_cache_repo.find_by_cache_key(
                cache_key
            )

            if cached_analysis and not self._is_cache_expired(
                cached_analysis, cache_type
            ):
                self.cache_stats["cache_hits"] += 1
                logger.info(f"✅ キャッシュヒット: {cache_key}")

                # キャッシュされたデータを返す
                return self._parse_cached_data(cached_analysis.analysis_data)
            else:
                self.cache_stats["cache_misses"] += 1
                logger.info(f"❌ キャッシュミス: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"❌ キャッシュ取得エラー: {e}")
            return None

    async def save_economic_events_cache(
        self,
        events: List[Dict[str, Any]],
        from_date: str,
        to_date: str,
        countries: List[str],
        importances: List[str],
        cache_type: str = "daily",
    ) -> bool:
        """
        経済指標データをキャッシュに保存

        Args:
            events: 経済指標データ
            from_date: 開始日
            to_date: 終了日
            countries: 対象国リスト
            importances: 重要度リスト
            cache_type: キャッシュタイプ

        Returns:
            bool: 保存成功時True
        """
        try:
            # キャッシュキーを生成
            cache_key = self._generate_cache_key(
                from_date, to_date, countries, importances, cache_type
            )

                        # 有効期限を計算
            expires_at = self._calculate_expires_at(cache_type)
            
            # 既存キャッシュを確認
            existing_cache = await self.analysis_cache_repo.find_by_cache_key(cache_key)
            
            if existing_cache:
                # 既存キャッシュの属性を直接更新
                existing_cache.analysis_data = self._serialize_events_data(events)
                existing_cache.expires_at = expires_at
                existing_cache.version = (existing_cache.version or 0) + 1
                
                await self.analysis_cache_repo.save(existing_cache)
                logger.info(f"✅ 経済指標キャッシュ更新: {cache_key} ({len(events)}件)")
            else:
                # 新規キャッシュを作成
                from src.domain.entities.analysis_cache import AnalysisCache
                
                cache_entity = AnalysisCache(
                    cache_key=cache_key,
                    analysis_type="economic_calendar",
                    currency_pair="ALL",  # 全通貨ペア対象
                    analysis_data=self._serialize_events_data(events),
                    expires_at=expires_at,
                )
                
                await self.analysis_cache_repo.save(cache_entity)
                logger.info(f"✅ 経済指標キャッシュ保存: {cache_key} ({len(events)}件)")

            return True

        except Exception as e:
            logger.error(f"❌ キャッシュ保存エラー: {e}")
            return False

    async def get_cached_weekly_events(
        self, start_date: str, countries: List[str], importances: List[str]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        週次経済指標データをキャッシュから取得

        Args:
            start_date: 開始日（DD/MM/YYYY）
            countries: 対象国リスト
            importances: 重要度リスト

        Returns:
            Optional[List[Dict[str, Any]]]: キャッシュされたデータ
        """
        # 週次データの終了日を計算
        start_dt = datetime.strptime(start_date, "%d/%m/%Y")
        end_dt = start_dt + timedelta(days=6)
        end_date = end_dt.strftime("%d/%m/%Y")

        return await self.get_cached_economic_events(
            start_date, end_date, countries, importances, "weekly"
        )

    async def save_weekly_events_cache(
        self,
        events: List[Dict[str, Any]],
        start_date: str,
        countries: List[str],
        importances: List[str],
    ) -> bool:
        """
        週次経済指標データをキャッシュに保存

        Args:
            events: 経済指標データ
            start_date: 開始日
            countries: 対象国リスト
            importances: 重要度リスト

        Returns:
            bool: 保存成功時True
        """
        # 週次データの終了日を計算
        start_dt = datetime.strptime(start_date, "%d/%m/%Y")
        end_dt = start_dt + timedelta(days=6)
        end_date = end_dt.strftime("%d/%m/%Y")

        return await self.save_economic_events_cache(
            events, start_date, end_date, countries, importances, "weekly"
        )

    async def cleanup_expired_cache(self) -> int:
        """
        期限切れキャッシュを削除

        Returns:
            int: 削除されたキャッシュ数
        """
        try:
            deleted_count = await self.analysis_cache_repo.delete_expired()
            self.cache_stats["last_cache_cleanup"] = datetime.now()

            logger.info(f"🗑️ 期限切れキャッシュ削除: {deleted_count}件")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ キャッシュクリーンアップエラー: {e}")
            return 0

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """
        キャッシュ統計を取得

        Returns:
            Dict[str, Any]: キャッシュ統計
        """
        try:
            # 有効なキャッシュ数を取得
            valid_caches = await self.analysis_cache_repo.find_valid_caches(
                "economic_calendar", "ALL"
            )

            stats = {
                **self.cache_stats,
                "valid_cache_count": len(valid_caches),
                "cache_hit_rate": (
                    self.cache_stats["cache_hits"]
                    / (
                        self.cache_stats["cache_hits"]
                        + self.cache_stats["cache_misses"]
                    )
                    if (
                        self.cache_stats["cache_hits"]
                        + self.cache_stats["cache_misses"]
                    )
                    > 0
                    else 0
                ),
                "estimated_api_calls_saved": self.cache_stats["api_calls_saved"],
            }

            return stats

        except Exception as e:
            logger.error(f"❌ キャッシュ統計取得エラー: {e}")
            return self.cache_stats

    def _generate_cache_key(
        self,
        from_date: str,
        to_date: str,
        countries: List[str],
        importances: List[str],
        cache_type: str,
    ) -> str:
        """キャッシュキーを生成"""
        countries_str = "_".join(sorted(countries))
        importances_str = "_".join(sorted(importances))

        return f"economic_calendar_{cache_type}_{from_date}_{to_date}_{countries_str}_{importances_str}"

    def _is_cache_expired(self, cache_entity, cache_type: str) -> bool:
        """キャッシュが期限切れかチェック"""
        if not cache_entity or not cache_entity.expires_at:
            return True
            
        # タイムゾーン情報を除去してUTCで比較
        now = datetime.utcnow()
        expires_at = cache_entity.expires_at
        
        # タイムゾーン情報を除去して比較
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
            
        return now > expires_at

    def _calculate_expires_at(self, cache_type: str) -> datetime:
        """有効期限を計算"""
        ttl_hours = self.cache_ttl_hours.get(cache_type, 24)
        return datetime.utcnow() + timedelta(hours=ttl_hours)

    def _serialize_events_data(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """イベントデータをシリアライズ"""
        return {
            "events": events,
            "cached_at": datetime.utcnow().isoformat(),
            "event_count": len(events),
        }

    def _parse_cached_data(self, cache_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """キャッシュデータをパース"""
        if isinstance(cache_data, dict) and "events" in cache_data:
            return cache_data["events"]
        elif isinstance(cache_data, list):
            return cache_data
        else:
            logger.warning("⚠️ 不明なキャッシュデータ形式")
            return []


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="経済指標キャッシュ管理システム")
    parser.add_argument(
        "--cleanup", action="store_true", help="期限切れキャッシュを削除"
    )
    parser.add_argument("--stats", action="store_true", help="キャッシュ統計を表示")
    parser.add_argument("--test", action="store_true", help="テスト実行")

    args = parser.parse_args()

    cache_manager = EconomicCalendarCacheManager()

    try:
        await cache_manager.initialize()

        if args.cleanup:
            # 期限切れキャッシュ削除
            deleted_count = await cache_manager.cleanup_expired_cache()
            logger.info(f"🗑️ 期限切れキャッシュ削除完了: {deleted_count}件")

        elif args.stats:
            # キャッシュ統計表示
            stats = await cache_manager.get_cache_statistics()
            logger.info(f"📊 キャッシュ統計: {stats}")

        elif args.test:
            # テスト用のキャッシュ操作
            test_events = [
                {
                    "date": "2025-08-25",
                    "time": "08:30",
                    "country": "japan",
                    "event": "Consumer Price Index (CPI)",
                    "importance": "high",
                    "currency": "JPY",
                    "actual": None,
                    "forecast": 2.5,
                    "previous": 2.3,
                }
            ]

            # キャッシュ保存テスト
            success = await cache_manager.save_weekly_events_cache(
                test_events,
                "25/08/2025",
                ["japan", "united states"],
                ["high", "medium"],
            )

            if success:
                logger.info("✅ キャッシュ保存テスト成功")

            # キャッシュ取得テスト
            cached_data = await cache_manager.get_cached_weekly_events(
                "25/08/2025", ["japan", "united states"], ["high", "medium"]
            )

            if cached_data:
                logger.info(f"✅ キャッシュ取得テスト成功: {len(cached_data)}件")

            # 統計取得
            stats = await cache_manager.get_cache_statistics()
            logger.info(f"📊 キャッシュ統計: {stats}")

        else:
            # デフォルト: 統計表示
            stats = await cache_manager.get_cache_statistics()
            logger.info(f"📊 キャッシュ統計: {stats}")

    except Exception as e:
        logger.error(f"❌ 実行エラー: {e}")
    finally:
        await cache_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
