"""
Dependency Injection Container
依存性注入コンテナ - アプリケーション全体の依存関係を管理

設計書参照:
- モジュール設計思想_20250809.md
- フォルダ構成実装ガイド_20250809.md

SOLID原則のD（依存関係逆転原則）に基づいて実装
"""

import logging
from typing import Optional

from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from config.base import BaseConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig
from config.testing import TestingConfig
from src.utils.logging_config import configure_logging


class Container(containers.DeclarativeContainer):
    """
    DIコンテナ - アプリケーション全体の依存関係を一元管理

    責任:
    - 設定の管理
    - サービスのライフサイクル管理
    - 依存関係の解決
    - プラグインシステムとの統合
    """

    # Wiring configuration - 依存性注入を有効にするモジュール
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.presentation.api",
            "src.application.handlers",
            "src.infrastructure.database",
            "src.infrastructure.external_apis",
        ]
    )

    # Configuration providers - 設定管理
    config = providers.Configuration()

    # Core configuration based on environment - will be set after function definition
    app_config = providers.Factory(
        lambda env: _get_config_class(env), env=config.environment
    )

    # Logging configuration
    logging_provider = providers.Singleton(
        lambda config: _setup_logging(config), config=app_config
    )

    # Database providers (will be implemented in Infrastructure phase)
    # database_engine = providers.Singleton(...)
    # database_session = providers.Factory(...)

    # Repository providers (will be implemented in Infrastructure phase)
    # exchange_rate_repository = providers.Factory(...)
    # ai_report_repository = providers.Factory(...)

    # External API providers (will be implemented in Infrastructure phase)
    # alpha_vantage_client = providers.Singleton(...)
    # openai_client = providers.Singleton(...)
    # discord_client = providers.Singleton(...)

    # Application service providers (will be implemented in Application phase)
    # data_handler = providers.Factory(...)
    # report_handler = providers.Factory(...)

    # Domain service providers (will be implemented in Domain phase)
    # exchange_rate_service = providers.Factory(...)
    # analysis_service = providers.Factory(...)

    # Plugin system providers (will be implemented in Plugin phase)
    # plugin_manager = providers.Singleton(...)


def _get_config_class(env: Optional[str] = None) -> BaseConfig:
    """
    環境に応じた設定クラスを返す

    Args:
        env: 環境名 ('development', 'production', 'testing')

    Returns:
        BaseConfig: 環境に対応した設定クラスのインスタンス
    """
    config_map = {
        "development": DevelopmentConfig(),
        "production": ProductionConfig(),
        "testing": TestingConfig(),
    }

    # デフォルトは開発環境
    return config_map.get(env, DevelopmentConfig())


def _setup_logging(config: BaseConfig) -> logging.Logger:
    """
    ログ設定を初期化（YAML設定使用）

    Args:
        config: アプリケーション設定

    Returns:
        logging.Logger: 設定されたロガー
    """
    # 環境を判定
    environment = "development"
    if hasattr(config, "__class__"):
        if "Production" in config.__class__.__name__:
            environment = "production"
        elif "Testing" in config.__class__.__name__:
            environment = "testing"

    # YAML設定を使用してログシステムを初期化
    logger = configure_logging(environment=environment)
    logger.info(f"Logging system initialized for {environment} environment")
    return logger


def setup_container(environment: str = "development") -> Container:
    """
    DIコンテナのセットアップ

    Args:
        environment: 実行環境 ('development', 'production', 'testing')

    Returns:
        Container: 設定済みのDIコンテナ
    """
    container = Container()

    # 環境設定を注入
    container.config.environment.from_value(environment)

    # Wireup - 依存性注入を有効化
    container.wire(modules=container.wiring_config.modules)

    return container


# Global container instance - アプリケーション全体で使用
container: Optional[Container] = None


def get_container() -> Container:
    """
    グローバルコンテナインスタンスを取得

    Returns:
        Container: DIコンテナインスタンス

    Raises:
        RuntimeError: コンテナが初期化されていない場合
    """
    global container
    if container is None:
        raise RuntimeError("Container not initialized. Call setup_container() first.")
    return container


def initialize_container(environment: str = "development") -> None:
    """
    グローバルコンテナを初期化

    Args:
        environment: 実行環境
    """
    global container
    container = setup_container(environment)


# Convenience decorators for dependency injection
def inject_config() -> callable:
    """設定を注入するデコレータ"""
    return inject(Provide[Container.app_config])


def inject_logger() -> callable:
    """ロガーを注入するデコレータ"""
    return inject(Provide[Container.logging_provider])
