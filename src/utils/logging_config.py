"""
Logging Configuration Utilities
ログ設定ユーティリティ

設計書参照:
- フォルダ構成実装ガイド_20250809.md
- モジュール設計思想_20250809.md

責任:
- YAML設定ファイルの読み込み
- 環境別ログ設定の適用
- ログディレクトリの自動作成
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_logging_config(
    config_path: str = "config/logging.yaml", environment: str = "development"
) -> Dict[str, Any]:
    """
    YAML設定ファイルからログ設定を読み込み

    Args:
        config_path: ログ設定ファイルのパス
        environment: 実行環境 ('development', 'production', 'testing')

    Returns:
        Dict[str, Any]: ログ設定辞書

    Raises:
        FileNotFoundError: 設定ファイルが見つからない場合
        yaml.YAMLError: YAML解析エラーの場合
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Logging config file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 環境固有の設定をマージ
    if environment in config and "loggers" in config[environment]:
        base_loggers = config.get("loggers", {})
        env_loggers = config[environment]["loggers"]

        # 環境固有の設定で基本設定を上書き
        for logger_name, logger_config in env_loggers.items():
            if logger_name in base_loggers:
                base_loggers[logger_name].update(logger_config)
            else:
                base_loggers[logger_name] = logger_config

    # 環境固有のセクションを削除（logging.configでエラーになるため）
    for env in ["development", "production", "testing"]:
        config.pop(env, None)

    return config


def setup_logging_directories() -> None:
    """
    ログディレクトリの作成
    設定ファイルで指定されたディレクトリを自動作成
    """
    log_dirs = ["logs", "logs/archive"]  # アーカイブ用

    for log_dir in log_dirs:
        Path(log_dir).mkdir(parents=True, exist_ok=True)


def configure_logging(
    config_path: str = "config/logging.yaml", environment: str = "development"
) -> logging.Logger:
    """
    ログシステムの設定とメインロガーの取得

    Args:
        config_path: ログ設定ファイルのパス
        environment: 実行環境

    Returns:
        logging.Logger: 設定済みのメインロガー
    """
    # ログディレクトリ作成
    setup_logging_directories()

    try:
        # YAML設定の読み込み
        config = load_logging_config(config_path, environment)

        # ログ設定の適用
        logging.config.dictConfig(config)

        # メインロガーの取得
        logger = logging.getLogger("exchange_analytics")
        logger.info(f"Logging configured for environment: {environment}")

        return logger

    except Exception as e:
        # 設定失敗時はフォールバック設定を使用
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/fallback.log", encoding="utf-8"),
            ],
        )

        logger = logging.getLogger("exchange_analytics")
        logger.error(f"Failed to load logging config: {e}")
        logger.info("Using fallback logging configuration")

        return logger


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得

    Args:
        name: ロガー名

    Returns:
        logging.Logger: ロガーインスタンス
    """
    return logging.getLogger(f"exchange_analytics.{name}")


def log_function_call(logger: logging.Logger):
    """
    関数呼び出しをログに記録するデコレータ

    Args:
        logger: 使用するロガー

    Returns:
        decorator: デコレータ関数
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed with error: {e}")
                raise

        return wrapper

    return decorator


# Application-specific loggers
def get_domain_logger() -> logging.Logger:
    """ドメイン層用ロガー"""
    return get_logger("domain")


def get_application_logger() -> logging.Logger:
    """アプリケーション層用ロガー"""
    return get_logger("application")


def get_infrastructure_logger() -> logging.Logger:
    """インフラストラクチャ層用ロガー"""
    return get_logger("infrastructure")


def get_presentation_logger() -> logging.Logger:
    """プレゼンテーション層用ロガー"""
    return get_logger("presentation")


def get_plugin_logger() -> logging.Logger:
    """プラグインシステム用ロガー"""
    return get_logger("plugins")
