"""
システム設定リポジトリインターフェース

USD/JPY特化の5分おきデータ取得システム用のシステム設定リポジトリ
設計書参照: /app/note/database_implementation_design_2025.md
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.infrastructure.database.models.system_config_model import SystemConfigModel


class SystemConfigRepository(ABC):
    """
    システム設定リポジトリインターフェース

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

    @abstractmethod
    async def save(self, config: SystemConfigModel) -> SystemConfigModel:
        """
        システム設定を保存

        Args:
            config: 保存するシステム設定

        Returns:
            SystemConfigModel: 保存されたシステム設定
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[SystemConfigModel]:
        """
        IDでシステム設定を取得

        Args:
            id: システム設定ID

        Returns:
            Optional[SystemConfigModel]: システム設定（存在しない場合はNone）
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def find_active_configs(self) -> List[SystemConfigModel]:
        """
        アクティブな設定を取得

        Returns:
            List[SystemConfigModel]: アクティブなシステム設定リスト
        """
        pass

    @abstractmethod
    async def find_inactive_configs(self) -> List[SystemConfigModel]:
        """
        非アクティブな設定を取得

        Returns:
            List[SystemConfigModel]: 非アクティブなシステム設定リスト
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def count_by_category(self, category: str, is_active: bool = True) -> int:
        """
        カテゴリ別の設定数を取得

        Args:
            category: 設定カテゴリ
            is_active: アクティブ設定のみカウント（デフォルト: True）

        Returns:
            int: 設定数
        """
        pass

    @abstractmethod
    async def get_config_statistics(self) -> dict:
        """
        設定統計情報を取得

        Returns:
            dict: 統計情報（カテゴリ別件数、型別件数等）
        """
        pass

    @abstractmethod
    async def delete_by_key(self, key: str) -> int:
        """
        キーで設定を削除

        Args:
            key: 設定キー

        Returns:
            int: 削除された設定数
        """
        pass

    @abstractmethod
    async def delete_by_category(self, category: str) -> int:
        """
        カテゴリで設定を削除

        Args:
            category: 設定カテゴリ

        Returns:
            int: 削除された設定数
        """
        pass

    @abstractmethod
    async def delete_old_history(self, days_to_keep: int = 90) -> int:
        """
        古い設定履歴を削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 90）

        Returns:
            int: 削除された設定数
        """
        pass

    @abstractmethod
    async def exists_by_key(self, key: str, is_active: bool = True) -> bool:
        """
        キーの設定が存在するかチェック

        Args:
            key: 設定キー
            is_active: アクティブ設定のみチェック（デフォルト: True）

        Returns:
            bool: 存在する場合True
        """
        pass

    @abstractmethod
    async def get_categories(self) -> List[str]:
        """
        カテゴリ一覧を取得

        Returns:
            List[str]: カテゴリ一覧
        """
        pass

    @abstractmethod
    async def get_value_types(self) -> List[str]:
        """
        値型一覧を取得

        Returns:
            List[str]: 値型一覧
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def activate_config(self, key: str) -> bool:
        """
        設定をアクティブ化

        Args:
            key: 設定キー

        Returns:
            bool: アクティブ化成功の場合True
        """
        pass

    @abstractmethod
    async def deactivate_config(self, key: str) -> bool:
        """
        設定を非アクティブ化

        Args:
            key: 設定キー

        Returns:
            bool: 非アクティブ化成功の場合True
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def clear_cache(self) -> None:
        """
        キャッシュをクリア

        Returns:
            None
        """
        pass

    @abstractmethod
    async def reload_configs(self) -> None:
        """
        設定を再読み込み

        Returns:
            None
        """
        pass
