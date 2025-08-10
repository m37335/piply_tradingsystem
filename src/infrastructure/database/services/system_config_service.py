"""
システム設定管理サービス

USD/JPY特化の動的設定管理サービス
設計書参照: /app/note/database_implementation_design_2025.md
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.system_config_model import SystemConfigModel
from src.infrastructure.database.repositories.system_config_repository_impl import (
    SystemConfigRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class SystemConfigService:
    """
    システム設定管理サービス

    責任:
    - 設定値の動的変更
    - 設定履歴の管理
    - 設定のバリデーション
    - 設定のキャッシュ

    特徴:
    - USD/JPY特化設計
    - データベースベース管理
    - 型別設定値保存
    - 設定履歴管理
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session
        self.config_repo = SystemConfigRepositoryImpl(session)

        # 設定キャッシュ
        self._cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5分

        # デフォルト設定
        self.default_configs = {
            "data_fetch_interval_minutes": {
                "value": "5",
                "type": "integer",
                "description": "データ取得間隔（分）",
            },
            "currency_pairs": {
                "value": '["USD/JPY"]',
                "type": "json",
                "description": "取得対象通貨ペア",
            },
            "yahoo_finance_retry_count": {
                "value": "3",
                "type": "integer",
                "description": "Yahoo Finance API リトライ回数",
            },
            "yahoo_finance_retry_delay": {
                "value": "2.0",
                "type": "float",
                "description": "リトライ間隔（秒）",
            },
            "technical_indicators_enabled": {
                "value": "true",
                "type": "boolean",
                "description": "テクニカル指標計算有効化",
            },
            "pattern_detection_enabled": {
                "value": "true",
                "type": "boolean",
                "description": "パターン検出有効化",
            },
            "notification_enabled": {
                "value": "true",
                "type": "boolean",
                "description": "通知機能有効化",
            },
            "data_retention_days": {
                "value": "90",
                "type": "integer",
                "description": "データ保持期間（日）",
            },
            "min_confidence_threshold": {
                "value": "0.7",
                "type": "float",
                "description": "最小信頼度閾値",
            },
            "min_priority_threshold": {
                "value": "70",
                "type": "integer",
                "description": "最小優先度閾値",
            },
            "max_notifications_per_run": {
                "value": "5",
                "type": "integer",
                "description": "1回の実行での最大通知数",
            },
            "duplicate_check_window_hours": {
                "value": "1",
                "type": "integer",
                "description": "重複チェック期間（時間）",
            },
        }

        logger.info("Initialized SystemConfigService")

    async def initialize_default_configs(self):
        """
        デフォルト設定を初期化
        """
        try:
            logger.info("Initializing default system configurations...")

            for config_key, config_data in self.default_configs.items():
                # 既存設定をチェック
                existing = await self.config_repo.find_by_key(config_key)
                
                if not existing:
                    # 新しい設定を作成
                    config = SystemConfigModel(
                        config_key=config_key,
                        config_value=config_data["value"],
                        config_type=config_data["type"],
                        description=config_data["description"],
                        is_active=True,
                    )

                    await self.config_repo.save(config)
                    logger.info(f"Created default config: {config_key}")

            logger.info("Default system configurations initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing default configs: {e}")
            raise

    async def get_config(self, config_key: str, use_cache: bool = True) -> Any:
        """
        設定値を取得

        Args:
            config_key: 設定キー
            use_cache: キャッシュ使用フラグ

        Returns:
            Any: 設定値
        """
        try:
            # キャッシュチェック
            if use_cache and self._is_cache_valid():
                if config_key in self._cache:
                    return self._cache[config_key]

            # データベースから取得
            config = await self.config_repo.find_by_key(config_key)
            
            if not config or not config.is_active:
                # デフォルト値を返す
                if config_key in self.default_configs:
                    default_value = self.default_configs[config_key]["value"]
                    default_type = self.default_configs[config_key]["type"]
                    return self._parse_config_value(default_value, default_type)
                else:
                    raise ValueError(f"Config key not found: {config_key}")

            # 値をパース
            parsed_value = self._parse_config_value(
                config.config_value, config.config_type
            )

            # キャッシュに保存
            if use_cache:
                self._cache[config_key] = parsed_value

            return parsed_value

        except Exception as e:
            logger.error(f"Error getting config {config_key}: {e}")
            raise

    async def set_config(
        self,
        config_key: str,
        config_value: Any,
        config_type: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SystemConfigModel:
        """
        設定値を設定

        Args:
            config_key: 設定キー
            config_value: 設定値
            config_type: 設定タイプ（デフォルト: None）
            description: 説明（デフォルト: None）

        Returns:
            SystemConfigModel: 設定モデル
        """
        try:
            logger.info(f"Setting config: {config_key} = {config_value}")

            # 既存設定を取得
            existing_config = await self.config_repo.find_by_key(config_key)

            if existing_config:
                # 既存設定を更新
                existing_config.config_value = str(config_value)
                if config_type:
                    existing_config.config_type = config_type
                if description:
                    existing_config.description = description
                existing_config.updated_at = datetime.now()

                updated_config = await self.config_repo.save(existing_config)
                logger.info(f"Updated config: {config_key}")

            else:
                # 新しい設定を作成
                if not config_type:
                    config_type = self._infer_config_type(config_value)
                if not description:
                    description = f"Configuration for {config_key}"

                config = SystemConfigModel(
                    config_key=config_key,
                    config_value=str(config_value),
                    config_type=config_type,
                    description=description,
                    is_active=True,
                )

                updated_config = await self.config_repo.save(config)
                logger.info(f"Created new config: {config_key}")

            # キャッシュをクリア
            self._clear_cache()

            return updated_config

        except Exception as e:
            logger.error(f"Error setting config {config_key}: {e}")
            raise

    async def get_all_configs(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        全設定値を取得

        Args:
            use_cache: キャッシュ使用フラグ

        Returns:
            Dict[str, Any]: 全設定値の辞書
        """
        try:
            # キャッシュチェック
            if use_cache and self._is_cache_valid():
                return self._cache.copy()

            # データベースから全設定を取得
            configs = await self.config_repo.find_all_active()

            result = {}
            for config in configs:
                try:
                    parsed_value = self._parse_config_value(
                        config.config_value, config.config_type
                    )
                    result[config.config_key] = parsed_value
                except Exception as e:
                    logger.warning(f"Error parsing config {config.config_key}: {e}")

            # デフォルト値で補完
            for config_key, config_data in self.default_configs.items():
                if config_key not in result:
                    default_value = self._parse_config_value(
                        config_data["value"], config_data["type"]
                    )
                    result[config_key] = default_value

            # キャッシュに保存
            if use_cache:
                self._cache = result.copy()
                self._cache_timestamp = datetime.now()

            return result

        except Exception as e:
            logger.error(f"Error getting all configs: {e}")
            raise

    async def delete_config(self, config_key: str) -> bool:
        """
        設定を削除

        Args:
            config_key: 設定キー

        Returns:
            bool: 削除成功の場合True
        """
        try:
            logger.info(f"Deleting config: {config_key}")

            config = await self.config_repo.find_by_key(config_key)
            if not config:
                logger.warning(f"Config not found: {config_key}")
                return False

            # 非アクティブ化
            config.is_active = False
            config.updated_at = datetime.now()
            await self.config_repo.save(config)

            # キャッシュをクリア
            self._clear_cache()

            logger.info(f"Deleted config: {config_key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting config {config_key}: {e}")
            raise

    async def get_config_history(self, config_key: str) -> List[SystemConfigModel]:
        """
        設定履歴を取得

        Args:
            config_key: 設定キー

        Returns:
            List[SystemConfigModel]: 設定履歴リスト
        """
        try:
            history = await self.config_repo.find_history_by_key(config_key)
            return history

        except Exception as e:
            logger.error(f"Error getting config history for {config_key}: {e}")
            raise

    async def validate_config(self, config_key: str, config_value: Any) -> bool:
        """
        設定値をバリデーション

        Args:
            config_key: 設定キー
            config_value: 設定値

        Returns:
            bool: バリデーション成功の場合True
        """
        try:
            # 設定キーの存在チェック
            if config_key not in self.default_configs:
                logger.warning(f"Unknown config key: {config_key}")
                return False

            config_type = self.default_configs[config_key]["type"]

            # 型チェック
            if config_type == "integer":
                try:
                    int(config_value)
                except (ValueError, TypeError):
                    logger.error(f"Invalid integer value for {config_key}: {config_value}")
                    return False

            elif config_type == "float":
                try:
                    float(config_value)
                except (ValueError, TypeError):
                    logger.error(f"Invalid float value for {config_key}: {config_value}")
                    return False

            elif config_type == "boolean":
                if str(config_value).lower() not in ["true", "false", "1", "0"]:
                    logger.error(f"Invalid boolean value for {config_key}: {config_value}")
                    return False

            elif config_type == "json":
                try:
                    json.loads(str(config_value))
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON value for {config_key}: {config_value}")
                    return False

            # 範囲チェック
            if config_key == "data_fetch_interval_minutes":
                interval = int(config_value)
                if interval < 1 or interval > 60:
                    logger.error(f"Invalid interval for {config_key}: {interval}")
                    return False

            elif config_key == "data_retention_days":
                days = int(config_value)
                if days < 1 or days > 365:
                    logger.error(f"Invalid retention days for {config_key}: {days}")
                    return False

            elif config_key == "min_confidence_threshold":
                confidence = float(config_value)
                if confidence < 0.0 or confidence > 1.0:
                    logger.error(f"Invalid confidence for {config_key}: {confidence}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating config {config_key}: {e}")
            return False

    def _parse_config_value(self, config_value: str, config_type: str) -> Any:
        """
        設定値をパース

        Args:
            config_value: 設定値文字列
            config_type: 設定タイプ

        Returns:
            Any: パースされた値
        """
        try:
            if config_type == "integer":
                return int(config_value)
            elif config_type == "float":
                return float(config_value)
            elif config_type == "boolean":
                return config_value.lower() in ["true", "1"]
            elif config_type == "json":
                return json.loads(config_value)
            else:
                return config_value

        except Exception as e:
            logger.error(f"Error parsing config value: {e}")
            raise

    def _infer_config_type(self, config_value: Any) -> str:
        """
        設定タイプを推論

        Args:
            config_value: 設定値

        Returns:
            str: 推論された設定タイプ
        """
        if isinstance(config_value, bool):
            return "boolean"
        elif isinstance(config_value, int):
            return "integer"
        elif isinstance(config_value, float):
            return "float"
        elif isinstance(config_value, (list, dict)):
            return "json"
        else:
            return "string"

    def _is_cache_valid(self) -> bool:
        """
        キャッシュが有効かチェック

        Returns:
            bool: キャッシュが有効の場合True
        """
        if not self._cache_timestamp:
            return False

        elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl

    def _clear_cache(self):
        """
        キャッシュをクリア
        """
        self._cache.clear()
        self._cache_timestamp = None

    async def get_system_statistics(self) -> Dict[str, Any]:
        """
        システム統計を取得

        Returns:
            Dict[str, Any]: システム統計
        """
        try:
            total_configs = await self.config_repo.count_all()
            active_configs = await self.config_repo.count_active()
            
            return {
                "total_configs": total_configs,
                "active_configs": active_configs,
                "cache_size": len(self._cache),
                "cache_valid": self._is_cache_valid(),
                "default_configs_count": len(self.default_configs),
            }

        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            raise
