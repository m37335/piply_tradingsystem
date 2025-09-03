"""
システム設定リポジトリ実装

USD/JPY特化の5分おきデータ取得システム用のシステム設定リポジトリ実装
設計書参照: /app/note/database_implementation_design_2025.md
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.system_config_model import SystemConfigModel
from src.infrastructure.database.repositories.base_repository_impl import (
    BaseRepositoryImpl,
)
from src.infrastructure.database.repositories.system_config_repository import (
    SystemConfigRepository,
)

logger = logging.getLogger(__name__)


class SystemConfigRepositoryImpl(BaseRepositoryImpl, SystemConfigRepository):
    """
    システム設定リポジトリ実装

    責任:
    - システム設定の永続化
    - 設定値の取得・更新
    - 設定履歴管理
    - 動的設定管理

    特徴:
    - 型別設定値保存
    - 設定履歴管理
    - アクティブ/非アクティブ管理
    - キャッシュ機能
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._cache: Dict[str, SystemConfigModel] = {}
        self._cache_enabled = True

    async def save(self, config: SystemConfigModel) -> SystemConfigModel:
        """
        システム設定を保存

        Args:
            config: 保存するシステム設定

        Returns:
            SystemConfigModel: 保存されたシステム設定
        """
        try:
            # バリデーション
            if not config.validate():
                raise ValueError("Invalid system config")

            # 既存設定を非アクティブ化
            if config.is_active:
                await self._deactivate_existing_config(config.key)

            # 保存
            saved_config = await super().save(config)

            # キャッシュ更新
            if self._cache_enabled:
                self._cache[saved_config.key] = saved_config

            logger.info(
                f"Saved system config {saved_config.key} "
                f"in category {saved_config.category}"
            )
            return saved_config

        except Exception as e:
            logger.error(f"Error saving system config: {e}")
            raise

    async def save_batch(
        self, config_list: List[SystemConfigModel]
    ) -> List[SystemConfigModel]:
        """
        システム設定をバッチ保存

        Args:
            config_list: 保存するシステム設定リスト

        Returns:
            List[SystemConfigModel]: 保存されたシステム設定リスト
        """
        try:
            saved_configs = []
            for config in config_list:
                if config.validate():
                    saved_config = await self.save(config)
                    saved_configs.append(saved_config)
                else:
                    logger.warning(f"Invalid system config skipped: {config}")

            logger.info(f"Saved {len(saved_configs)} system configs")
            return saved_configs

        except Exception as e:
            logger.error(f"Error saving system configs batch: {e}")
            raise

    async def find_by_id(self, id: int) -> Optional[SystemConfigModel]:
        """
        IDでシステム設定を取得

        Args:
            id: システム設定ID

        Returns:
            Optional[SystemConfigModel]: システム設定（存在しない場合はNone）
        """
        try:
            return await super().get_by_id(id)
        except Exception as e:
            logger.error(f"Error finding system config by ID {id}: {e}")
            return None

    async def find_by_key(
        self, key: str, is_active: bool = True
    ) -> Optional[SystemConfigModel]:
        """
        キーでシステム設定を取得

        Args:
            key: 設定キー
            is_active: アクティブ設定のみ取得（デフォルト: True）

        Returns:
            Optional[SystemConfigModel]: システム設定（存在しない場合はNone）
        """
        try:
            # キャッシュチェック
            if self._cache_enabled and key in self._cache:
                cached_config = self._cache[key]
                if not is_active or cached_config.is_active:
                    return cached_config

            # データベースから取得
            conditions = [SystemConfigModel.key == key]
            if is_active:
                conditions.append(SystemConfigModel.is_active.is_(True))

            query = (
                select(SystemConfigModel)
                .where(and_(*conditions))
                .order_by(SystemConfigModel.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(query)
            config = result.scalar_one_or_none()

            # キャッシュ更新
            if config and self._cache_enabled:
                self._cache[key] = config

            return config

        except Exception as e:
            logger.error(f"Error finding system config by key {key}: {e}")
            return None

    async def find_by_category(
        self, category: str, is_active: bool = True
    ) -> List[SystemConfigModel]:
        """
        カテゴリでシステム設定を取得

        Args:
            category: 設定カテゴリ
            is_active: アクティブ設定のみ取得（デフォルト: True）

        Returns:
            List[SystemConfigModel]: システム設定リスト
        """
        try:
            conditions = [SystemConfigModel.category == category]
            if is_active:
                conditions.append(SystemConfigModel.is_active.is_(True))

            query = (
                select(SystemConfigModel)
                .where(and_(*conditions))
                .order_by(SystemConfigModel.key)
            )
            result = await self._session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding system configs by category {category}: {e}")
            return []

    async def find_by_type(
        self, value_type: str, is_active: bool = True
    ) -> List[SystemConfigModel]:
        """
        型でシステム設定を取得

        Args:
            value_type: 設定値型
            is_active: アクティブ設定のみ取得（デフォルト: True）

        Returns:
            List[SystemConfigModel]: システム設定リスト
        """
        try:
            conditions = [SystemConfigModel.value_type == value_type]
            if is_active:
                conditions.append(SystemConfigModel.is_active.is_(True))

            query = (
                select(SystemConfigModel)
                .where(and_(*conditions))
                .order_by(SystemConfigModel.category, SystemConfigModel.key)
            )
            result = await self._session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding system configs by type {value_type}: {e}")
            return []

    async def find_active_configs(self) -> List[SystemConfigModel]:
        """
        アクティブな設定を取得

        Returns:
            List[SystemConfigModel]: アクティブなシステム設定リスト
        """
        try:
            query = (
                select(SystemConfigModel)
                .where(SystemConfigModel.is_active.is_(True))
                .order_by(SystemConfigModel.category, SystemConfigModel.key)
            )
            result = await self._session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding active system configs: {e}")
            return []

    async def find_inactive_configs(self) -> List[SystemConfigModel]:
        """
        非アクティブな設定を取得

        Returns:
            List[SystemConfigModel]: 非アクティブなシステム設定リスト
        """
        try:
            query = (
                select(SystemConfigModel)
                .where(SystemConfigModel.is_active.is_(False))
                .order_by(SystemConfigModel.category, SystemConfigModel.key)
            )
            result = await self._session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding inactive system configs: {e}")
            return []

    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[SystemConfigModel]:
        """
        日付範囲でシステム設定を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            category: 設定カテゴリ（デフォルト: None）
            is_active: アクティブ設定のみ取得（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[SystemConfigModel]: システム設定リスト
        """
        try:
            conditions = [
                SystemConfigModel.created_at >= start_date,
                SystemConfigModel.created_at <= end_date,
            ]

            if category:
                conditions.append(SystemConfigModel.category == category)

            if is_active is not None:
                conditions.append(SystemConfigModel.is_active.is_(is_active))

            query = (
                select(SystemConfigModel)
                .where(and_(*conditions))
                .order_by(SystemConfigModel.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self._session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding system configs by date range: {e}")
            return []

    async def find_config_history(
        self,
        key: str,
        limit: Optional[int] = None,
    ) -> List[SystemConfigModel]:
        """
        設定履歴を取得

        Args:
            key: 設定キー
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[SystemConfigModel]: 設定履歴リスト
        """
        try:
            query = (
                select(SystemConfigModel)
                .where(SystemConfigModel.key == key)
                .order_by(SystemConfigModel.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self._session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding config history for key {key}: {e}")
            return []

    async def count_by_category(self, category: str, is_active: bool = True) -> int:
        """
        カテゴリ別の設定数を取得

        Args:
            category: 設定カテゴリ
            is_active: アクティブ設定のみカウント（デフォルト: True）

        Returns:
            int: 設定数
        """
        try:
            conditions = [SystemConfigModel.category == category]
            if is_active:
                conditions.append(SystemConfigModel.is_active.is_(True))

            query = select(func.count(SystemConfigModel.id)).where(and_(*conditions))
            result = await self._session.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Error counting system configs by category {category}: {e}")
            return 0

    async def get_config_statistics(self) -> dict:
        """
        設定統計情報を取得

        Returns:
            dict: 統計情報（カテゴリ別件数、型別件数等）
        """
        try:
            # カテゴリ別統計
            category_stats_query = select(
                SystemConfigModel.category,
                func.count(SystemConfigModel.id).label("count"),
            ).group_by(SystemConfigModel.category)
            category_result = await self._session.execute(category_stats_query)
            category_stats = category_result.all()

            # 型別統計
            type_stats_query = select(
                SystemConfigModel.value_type,
                func.count(SystemConfigModel.id).label("count"),
            ).group_by(SystemConfigModel.value_type)
            type_result = await self._session.execute(type_stats_query)
            type_stats = type_result.all()

            # アクティブ/非アクティブ統計
            active_stats_query = select(
                SystemConfigModel.is_active,
                func.count(SystemConfigModel.id).label("count"),
            ).group_by(SystemConfigModel.is_active)
            active_result = await self._session.execute(active_stats_query)
            active_stats = active_result.all()

            return {
                "category_stats": [
                    {
                        "category": stat.category,
                        "count": stat.count,
                    }
                    for stat in category_stats
                ],
                "type_stats": [
                    {
                        "value_type": stat.value_type,
                        "count": stat.count,
                    }
                    for stat in type_stats
                ],
                "active_stats": [
                    {
                        "is_active": stat.is_active,
                        "count": stat.count,
                    }
                    for stat in active_stats
                ],
            }

        except Exception as e:
            logger.error(f"Error getting config statistics: {e}")
            return {
                "category_stats": [],
                "type_stats": [],
                "active_stats": [],
            }

    async def delete_by_key(self, key: str) -> int:
        """
        キーで設定を削除

        Args:
            key: 設定キー

        Returns:
            int: 削除された設定数
        """
        try:
            # 削除前に件数を取得
            count_query = select(func.count(SystemConfigModel.id)).where(
                SystemConfigModel.key == key
            )
            count_result = await self._session.execute(count_query)
            delete_count = count_result.scalar()

            # 削除実行
            delete_query = delete(SystemConfigModel).where(SystemConfigModel.key == key)
            await self._session.execute(delete_query)

            # キャッシュから削除
            if self._cache_enabled and key in self._cache:
                del self._cache[key]

            logger.info(f"Deleted {delete_count} system configs for key {key}")
            return delete_count

        except Exception as e:
            logger.error(f"Error deleting system configs by key {key}: {e}")
            return 0

    async def delete_by_category(self, category: str) -> int:
        """
        カテゴリで設定を削除

        Args:
            category: 設定カテゴリ

        Returns:
            int: 削除された設定数
        """
        try:
            # 削除前に件数を取得
            count_query = select(func.count(SystemConfigModel.id)).where(
                SystemConfigModel.category == category
            )
            count_result = await self._session.execute(count_query)
            delete_count = count_result.scalar()

            # 削除実行
            delete_query = delete(SystemConfigModel).where(
                SystemConfigModel.category == category
            )
            await self._session.execute(delete_query)

            # キャッシュから削除
            if self._cache_enabled:
                keys_to_remove = [
                    key
                    for key, config in self._cache.items()
                    if config.category == category
                ]
                for key in keys_to_remove:
                    del self._cache[key]

            logger.info(
                f"Deleted {delete_count} system configs for category {category}"
            )
            return delete_count

        except Exception as e:
            logger.error(f"Error deleting system configs by category {category}: {e}")
            return 0

    async def delete_old_history(self, days_to_keep: int = 90) -> int:
        """
        古い設定履歴を削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 90）

        Returns:
            int: 削除された設定数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # 削除前に件数を取得
            count_query = select(func.count(SystemConfigModel.id)).where(
                SystemConfigModel.created_at < cutoff_date
            )
            count_result = await self._session.execute(count_query)
            delete_count = count_result.scalar()

            # 削除実行
            delete_query = delete(SystemConfigModel).where(
                SystemConfigModel.created_at < cutoff_date
            )
            await self._session.execute(delete_query)

            logger.info(f"Deleted {delete_count} old system configs")
            return delete_count

        except Exception as e:
            logger.error(f"Error deleting old system configs: {e}")
            return 0

    async def exists_by_key(self, key: str, is_active: bool = True) -> bool:
        """
        キーの設定が存在するかチェック

        Args:
            key: 設定キー
            is_active: アクティブ設定のみチェック（デフォルト: True）

        Returns:
            bool: 存在する場合True
        """
        try:
            conditions = [SystemConfigModel.key == key]
            if is_active:
                conditions.append(SystemConfigModel.is_active.is_(True))

            query = select(func.count(SystemConfigModel.id)).where(and_(*conditions))
            result = await self._session.execute(query)
            return result.scalar() > 0

        except Exception as e:
            logger.error(f"Error checking system config existence for key {key}: {e}")
            return False

    async def get_categories(self) -> List[str]:
        """
        カテゴリ一覧を取得

        Returns:
            List[str]: カテゴリ一覧
        """
        try:
            query = (
                select(SystemConfigModel.category)
                .distinct()
                .order_by(SystemConfigModel.category)
            )
            result = await self._session.execute(query)
            return [row.category for row in result.scalars()]

        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    async def get_value_types(self) -> List[str]:
        """
        値型一覧を取得

        Returns:
            List[str]: 値型一覧
        """
        try:
            query = (
                select(SystemConfigModel.value_type)
                .distinct()
                .order_by(SystemConfigModel.value_type)
            )
            result = await self._session.execute(query)
            return [row.value_type for row in result.scalars()]

        except Exception as e:
            logger.error(f"Error getting value types: {e}")
            return []

    async def update_config_value(
        self,
        key: str,
        value: Union[str, int, float, bool, Dict[str, Any]],
        description: Optional[str] = None,
    ) -> bool:
        """
        設定値を更新

        Args:
            key: 設定キー
            value: 新しい設定値
            description: 説明（デフォルト: None）

        Returns:
            bool: 更新成功の場合True
        """
        try:
            # 既存設定を取得
            existing_config = await self.find_by_key(key, is_active=True)
            if not existing_config:
                logger.warning(f"System config not found: {key}")
                return False

            # 新しい設定を作成
            new_config = SystemConfigModel(
                key=key,
                value=value,
                value_type=type(value).__name__,
                category=existing_config.category,
                description=description or existing_config.description,
                is_active=True,
            )

            # 保存
            await self.save(new_config)

            logger.info(f"Updated system config value for key {key}")
            return True

        except Exception as e:
            logger.error(f"Error updating system config value for key {key}: {e}")
            return False

    async def activate_config(self, key: str) -> bool:
        """
        設定をアクティブ化

        Args:
            key: 設定キー

        Returns:
            bool: アクティブ化成功の場合True
        """
        try:
            config = await self.find_by_key(key, is_active=False)
            if not config:
                logger.warning(f"System config not found: {key}")
                return False

            config.is_active = True
            await self._session.commit()

            # キャッシュ更新
            if self._cache_enabled:
                self._cache[key] = config

            logger.info(f"Activated system config: {key}")
            return True

        except Exception as e:
            logger.error(f"Error activating system config {key}: {e}")
            return False

    async def deactivate_config(self, key: str) -> bool:
        """
        設定を非アクティブ化

        Args:
            key: 設定キー

        Returns:
            bool: 非アクティブ化成功の場合True
        """
        try:
            config = await self.find_by_key(key, is_active=True)
            if not config:
                logger.warning(f"System config not found: {key}")
                return False

            config.is_active = False
            await self._session.commit()

            # キャッシュから削除
            if self._cache_enabled and key in self._cache:
                del self._cache[key]

            logger.info(f"Deactivated system config: {key}")
            return True

        except Exception as e:
            logger.error(f"Error deactivating system config {key}: {e}")
            return False

    async def get_config_value(
        self,
        key: str,
        default_value: Optional[Union[str, int, float, bool, Dict[str, Any]]] = None,
    ) -> Optional[Union[str, int, float, bool, Dict[str, Any]]]:
        """
        設定値を取得

        Args:
            key: 設定キー
            default_value: デフォルト値（デフォルト: None）

        Returns:
            Optional[Union[str, int, float, bool, Dict[str, Any]]]: 設定値
        """
        try:
            config = await self.find_by_key(key, is_active=True)
            if not config:
                return default_value

            return config.get_value()

        except Exception as e:
            logger.error(f"Error getting config value for key {key}: {e}")
            return default_value

    async def get_config_dict(
        self, category: Optional[str] = None
    ) -> Dict[str, Union[str, int, float, bool, Dict[str, Any]]]:
        """
        設定辞書を取得

        Args:
            category: 設定カテゴリ（デフォルト: None）

        Returns:
            Dict[str, Union[str, int, float, bool, Dict[str, Any]]]: 設定辞書
        """
        try:
            if category:
                configs = await self.find_by_category(category, is_active=True)
            else:
                configs = await self.find_active_configs()

            config_dict = {}
            for config in configs:
                config_dict[config.key] = config.get_value()

            return config_dict

        except Exception as e:
            logger.error(f"Error getting config dict: {e}")
            return {}

    async def clear_cache(self) -> None:
        """
        キャッシュをクリア

        Returns:
            None
        """
        try:
            self._cache.clear()
            logger.info("System config cache cleared")
        except Exception as e:
            logger.error(f"Error clearing system config cache: {e}")

    async def reload_configs(self) -> None:
        """
        設定を再読み込み

        Returns:
            None
        """
        try:
            # キャッシュをクリア
            await self.clear_cache()

            # アクティブな設定を再読み込み
            active_configs = await self.find_active_configs()
            for config in active_configs:
                self._cache[config.key] = config

            logger.info(f"Reloaded {len(active_configs)} system configs")
        except Exception as e:
            logger.error(f"Error reloading system configs: {e}")

    async def _deactivate_existing_config(self, key: str) -> None:
        """
        既存の設定を非アクティブ化

        Args:
            key: 設定キー

        Returns:
            None
        """
        try:
            existing_config = await self.find_by_key(key, is_active=True)
            if existing_config:
                existing_config.is_active = False
                await self._session.commit()

                # キャッシュから削除
                if self._cache_enabled and key in self._cache:
                    del self._cache[key]

        except Exception as e:
            logger.error(f"Error deactivating existing config {key}: {e}")
