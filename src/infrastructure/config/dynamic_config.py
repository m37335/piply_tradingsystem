"""
Dynamic Configuration Management
動的設定管理システム

設計書参照:
- インフラ・プラグイン設計_20250809.md

データベースベースの動的設定管理とホットリロード機能
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession

from ...utils.logging_config import get_infrastructure_logger
from ..database.models.base import BaseModel

logger = get_infrastructure_logger()


class ConfigModel(BaseModel):
    """
    設定項目データベースモデル

    責任:
    - 設定項目の永続化
    - バージョン管理
    - 環境別設定
    """

    __tablename__ = "configurations"

    # 設定キー（例: "api.alpha_vantage.rate_limit"）
    key = Column(String(255), nullable=False, index=True, comment="設定キー")

    # 設定値（JSON形式）
    value = Column(Text, nullable=False, comment="設定値（JSON形式）")

    # 設定の説明
    description = Column(Text, nullable=True, comment="設定の説明")

    # 環境（development, production, testing等）
    environment = Column(
        String(50), nullable=False, default="default", index=True, comment="環境"
    )

    # データ型（string, integer, float, boolean, json）
    data_type = Column(String(20), nullable=False, default="string", comment="データ型")

    # デフォルト値
    default_value = Column(Text, nullable=True, comment="デフォルト値")

    # 必須フラグ
    is_required = Column(Integer, default=0, comment="必須フラグ")

    # 検証ルール（JSON形式）
    validation_rules = Column(Text, nullable=True, comment="検証ルール（JSON形式）")

    # 最後に更新したユーザー
    updated_by = Column(String(100), nullable=True, comment="更新者")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug(f"Created ConfigModel: {self.key}")

    def to_config_item(self) -> "ConfigItem":
        """
        ConfigItemに変換

        Returns:
            ConfigItem: 設定アイテム
        """
        return ConfigItem(
            key=self.key,
            value=self._parse_value(),
            description=self.description,
            environment=self.environment,
            data_type=self.data_type,
            default_value=self._parse_default_value(),
            is_required=bool(self.is_required),
            validation_rules=self._parse_validation_rules(),
            updated_by=self.updated_by,
            updated_at=self.updated_at,
        )

    def _parse_value(self) -> Any:
        """設定値をパース"""
        try:
            if self.data_type == "json":
                return json.loads(self.value)
            elif self.data_type == "integer":
                return int(self.value)
            elif self.data_type == "float":
                return float(self.value)
            elif self.data_type == "boolean":
                return self.value.lower() in ("true", "1", "yes", "on")
            else:
                return self.value
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse config value for {self.key}: {e}")
            return self.value

    def _parse_default_value(self) -> Any:
        """デフォルト値をパース"""
        if not self.default_value:
            return None

        try:
            if self.data_type == "json":
                return json.loads(self.default_value)
            elif self.data_type == "integer":
                return int(self.default_value)
            elif self.data_type == "float":
                return float(self.default_value)
            elif self.data_type == "boolean":
                return self.default_value.lower() in ("true", "1", "yes", "on")
            else:
                return self.default_value
        except (ValueError, json.JSONDecodeError):
            return self.default_value

    def _parse_validation_rules(self) -> Optional[Dict[str, Any]]:
        """検証ルールをパース"""
        if not self.validation_rules:
            return None

        try:
            return json.loads(self.validation_rules)
        except json.JSONDecodeError:
            return None


class ConfigItem:
    """
    設定アイテム

    単一の設定項目を表現するデータクラス
    """

    def __init__(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
        environment: str = "default",
        data_type: str = "string",
        default_value: Any = None,
        is_required: bool = False,
        validation_rules: Optional[Dict[str, Any]] = None,
        updated_by: Optional[str] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.key = key
        self.value = value
        self.description = description
        self.environment = environment
        self.data_type = data_type
        self.default_value = default_value
        self.is_required = is_required
        self.validation_rules = validation_rules or {}
        self.updated_by = updated_by
        self.updated_at = updated_at or datetime.utcnow()

    def validate(self) -> List[str]:
        """
        設定値を検証

        Returns:
            List[str]: 検証エラーのリスト
        """
        errors = []

        # 必須チェック
        if self.is_required and self.value is None:
            errors.append(f"Required config '{self.key}' is missing")

        # 型チェック
        if self.value is not None:
            try:
                self._validate_type()
            except ValueError as e:
                errors.append(f"Type validation failed for '{self.key}': {e}")

        # カスタム検証ルール
        if self.validation_rules:
            custom_errors = self._validate_custom_rules()
            errors.extend(custom_errors)

        return errors

    def _validate_type(self) -> None:
        """型検証"""
        if self.data_type == "integer" and not isinstance(self.value, int):
            raise ValueError(f"Expected integer, got {type(self.value).__name__}")
        elif self.data_type == "float" and not isinstance(self.value, (int, float)):
            raise ValueError(f"Expected float, got {type(self.value).__name__}")
        elif self.data_type == "boolean" and not isinstance(self.value, bool):
            raise ValueError(f"Expected boolean, got {type(self.value).__name__}")
        elif self.data_type == "string" and not isinstance(self.value, str):
            raise ValueError(f"Expected string, got {type(self.value).__name__}")

    def _validate_custom_rules(self) -> List[str]:
        """カスタム検証ルール"""
        errors = []

        # 最小値チェック
        if "min" in self.validation_rules:
            min_val = self.validation_rules["min"]
            if isinstance(self.value, (int, float)) and self.value < min_val:
                errors.append(f"Value {self.value} is less than minimum {min_val}")

        # 最大値チェック
        if "max" in self.validation_rules:
            max_val = self.validation_rules["max"]
            if isinstance(self.value, (int, float)) and self.value > max_val:
                errors.append(f"Value {self.value} is greater than maximum {max_val}")

        # 最小長チェック
        if "min_length" in self.validation_rules:
            min_len = self.validation_rules["min_length"]
            if isinstance(self.value, str) and len(self.value) < min_len:
                errors.append(
                    f"String length {len(self.value)} is less than minimum {min_len}"
                )

        # 最大長チェック
        if "max_length" in self.validation_rules:
            max_len = self.validation_rules["max_length"]
            if isinstance(self.value, str) and len(self.value) > max_len:
                errors.append(
                    f"String length {len(self.value)} is greater than maximum {max_len}"
                )

        # 選択肢チェック
        if "choices" in self.validation_rules:
            choices = self.validation_rules["choices"]
            if self.value not in choices:
                errors.append(
                    f"Value '{self.value}' is not in allowed choices: {choices}"
                )

        # 正規表現チェック
        if "pattern" in self.validation_rules:
            import re

            pattern = self.validation_rules["pattern"]
            if isinstance(self.value, str) and not re.match(pattern, self.value):
                errors.append(
                    f"Value '{self.value}' does not match pattern '{pattern}'"
                )

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "environment": self.environment,
            "data_type": self.data_type,
            "default_value": self.default_value,
            "is_required": self.is_required,
            "validation_rules": self.validation_rules,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DynamicConfigManager:
    """
    動的設定管理マネージャー

    責任:
    - データベースベースの設定管理
    - ホットリロード機能
    - 設定値の検証
    - 環境別設定
    """

    def __init__(self, session: AsyncSession, environment: str = "default"):
        self.session = session
        self.environment = environment
        self._config_cache: Dict[str, ConfigItem] = {}
        self._reload_interval = 30  # 30秒間隔でリロード
        self._reload_task: Optional[asyncio.Task] = None
        self._is_running = False

        logger.info(f"Initialized DynamicConfigManager for environment: {environment}")

    async def start(self) -> None:
        """
        設定管理を開始
        """
        if self._is_running:
            logger.warning("DynamicConfigManager is already running")
            return

        # 初期ロード
        await self.reload()

        # 定期リロードタスクを開始
        self._is_running = True
        self._reload_task = asyncio.create_task(self._reload_loop())

        logger.info("DynamicConfigManager started")

    async def stop(self) -> None:
        """
        設定管理を停止
        """
        self._is_running = False

        if self._reload_task:
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                pass

        logger.info("DynamicConfigManager stopped")

    async def get(
        self, key: str, default: Any = None, environment: Optional[str] = None
    ) -> Any:
        """
        設定値を取得

        Args:
            key: 設定キー
            default: デフォルト値
            environment: 環境名（指定しない場合は初期化時の環境）

        Returns:
            Any: 設定値
        """
        env = environment or self.environment
        full_key = f"{env}:{key}"

        # キャッシュから取得
        if full_key in self._config_cache:
            return self._config_cache[full_key].value

        # 環境固有の設定がない場合はデフォルト環境を試行
        if env != "default":
            default_key = f"default:{key}"
            if default_key in self._config_cache:
                return self._config_cache[default_key].value

        # キャッシュにない場合はデータベースから取得
        config_item = await self._load_config_item(key, env)
        if config_item:
            self._config_cache[full_key] = config_item
            return config_item.value

        logger.debug(f"Config not found: {key} (env: {env}), using default: {default}")
        return default

    async def set(
        self,
        key: str,
        value: Any,
        description: Optional[str] = None,
        data_type: str = "string",
        environment: Optional[str] = None,
        updated_by: Optional[str] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        設定値を更新

        Args:
            key: 設定キー
            value: 設定値
            description: 説明
            data_type: データ型
            environment: 環境名
            updated_by: 更新者
            validation_rules: 検証ルール

        Returns:
            bool: 更新成功時True
        """
        try:
            env = environment or self.environment

            # 設定アイテムを作成
            config_item = ConfigItem(
                key=key,
                value=value,
                description=description,
                environment=env,
                data_type=data_type,
                updated_by=updated_by,
                validation_rules=validation_rules,
            )

            # 検証
            errors = config_item.validate()
            if errors:
                logger.error(f"Config validation failed for {key}: {errors}")
                return False

            # データベースに保存
            await self._save_config_item(config_item)

            # キャッシュを更新
            full_key = f"{env}:{key}"
            self._config_cache[full_key] = config_item

            logger.info(f"Config updated: {key} = {value} (env: {env})")
            return True

        except Exception as e:
            logger.error(f"Failed to set config {key}: {str(e)}")
            return False

    async def delete(self, key: str, environment: Optional[str] = None) -> bool:
        """
        設定を削除

        Args:
            key: 設定キー
            environment: 環境名

        Returns:
            bool: 削除成功時True
        """
        try:
            env = environment or self.environment

            # データベースから削除
            await self._delete_config_item(key, env)

            # キャッシュから削除
            full_key = f"{env}:{key}"
            self._config_cache.pop(full_key, None)

            logger.info(f"Config deleted: {key} (env: {env})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete config {key}: {str(e)}")
            return False

    async def reload(self) -> None:
        """
        設定をデータベースから再読み込み
        """
        try:
            # データベースから全設定を取得
            from sqlalchemy import select

            result = await self.session.execute(
                select(ConfigModel).where(
                    ConfigModel.environment.in_([self.environment, "default"])
                )
            )

            models = result.scalars().all()

            # キャッシュをクリア
            self._config_cache.clear()

            # 新しい設定をキャッシュに登録
            for model in models:
                config_item = model.to_config_item()
                full_key = f"{config_item.environment}:{config_item.key}"
                self._config_cache[full_key] = config_item

            logger.debug(f"Reloaded {len(models)} config items")

        except Exception as e:
            logger.error(f"Failed to reload config: {str(e)}")

    async def get_all(self, environment: Optional[str] = None) -> Dict[str, ConfigItem]:
        """
        全設定を取得

        Args:
            environment: 環境名

        Returns:
            Dict[str, ConfigItem]: 設定アイテムの辞書
        """
        env = environment or self.environment

        result = {}
        for full_key, config_item in self._config_cache.items():
            if full_key.startswith(f"{env}:"):
                key = full_key[len(f"{env}:") :]
                result[key] = config_item

        return result

    async def _load_config_item(
        self, key: str, environment: str
    ) -> Optional[ConfigItem]:
        """データベースから設定アイテムを読み込み"""
        try:
            from sqlalchemy import select

            result = await self.session.execute(
                select(ConfigModel).where(
                    ConfigModel.key == key, ConfigModel.environment == environment
                )
            )

            model = result.scalar_one_or_none()
            return model.to_config_item() if model else None

        except Exception as e:
            logger.error(f"Failed to load config item {key}: {str(e)}")
            return None

    async def _save_config_item(self, config_item: ConfigItem) -> None:
        """設定アイテムをデータベースに保存"""
        from sqlalchemy import select

        # 既存の設定を検索
        result = await self.session.execute(
            select(ConfigModel).where(
                ConfigModel.key == config_item.key,
                ConfigModel.environment == config_item.environment,
            )
        )

        model = result.scalar_one_or_none()

        if model:
            # 更新
            model.value = (
                json.dumps(config_item.value)
                if config_item.data_type == "json"
                else str(config_item.value)
            )
            model.description = config_item.description
            model.data_type = config_item.data_type
            model.validation_rules = (
                json.dumps(config_item.validation_rules)
                if config_item.validation_rules
                else None
            )
            model.updated_by = config_item.updated_by
            model.updated_at = datetime.utcnow()
        else:
            # 新規作成
            model = ConfigModel(
                key=config_item.key,
                value=(
                    json.dumps(config_item.value)
                    if config_item.data_type == "json"
                    else str(config_item.value)
                ),
                description=config_item.description,
                environment=config_item.environment,
                data_type=config_item.data_type,
                is_required=1 if config_item.is_required else 0,
                validation_rules=(
                    json.dumps(config_item.validation_rules)
                    if config_item.validation_rules
                    else None
                ),
                updated_by=config_item.updated_by,
            )

            self.session.add(model)

        await self.session.commit()

    async def _delete_config_item(self, key: str, environment: str) -> None:
        """設定アイテムをデータベースから削除"""
        from sqlalchemy import delete

        await self.session.execute(
            delete(ConfigModel).where(
                ConfigModel.key == key, ConfigModel.environment == environment
            )
        )

        await self.session.commit()

    async def _reload_loop(self) -> None:
        """定期的なリロードループ"""
        while self._is_running:
            try:
                await asyncio.sleep(self._reload_interval)
                await self.reload()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reload loop: {str(e)}")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        キャッシュ統計を取得

        Returns:
            Dict[str, int]: キャッシュ統計
        """
        env_counts = {}
        for full_key in self._config_cache.keys():
            env = full_key.split(":", 1)[0]
            env_counts[env] = env_counts.get(env, 0) + 1

        return {
            "total_items": len(self._config_cache),
            "environments": env_counts,
            "reload_interval": self._reload_interval,
        }
