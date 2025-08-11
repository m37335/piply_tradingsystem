"""
システム設定管理

USD/JPY特化の5分おきデータ取得システム用の設定管理システム
環境変数、デフォルト設定、動的更新、検証機能を統合

責任:
- システム全体の設定管理
- 環境変数の読み込みと検証
- デフォルト設定の提供
- 設定の動的更新
- 設定の永続化
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.utils.logging_config import get_infrastructure_logger


class SystemConfigManager:
    """
    システム設定管理クラス

    責任:
    - システム全体の設定管理
    - 環境変数の読み込みと検証
    - デフォルト設定の提供
    - 設定の動的更新
    - 設定の永続化
    """

    def __init__(self, config_file_path: Optional[str] = None):
        self.logger = get_infrastructure_logger()
        self.config_file_path = config_file_path or "config/system_config.json"

        # 設定データ
        self._config = {}
        self._default_config = self._get_default_config()

        # 設定ファイルのパスを確保
        self._ensure_config_directory()

        # 初期化
        self._load_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """
        デフォルト設定を取得
        """
        return {
            # データベース設定
            "database": {
                "url": "sqlite+aiosqlite:///./app.db",
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
            },
            # データ取得設定
            "data_fetch": {
                "currency_pair": "USD/JPY",
                "symbol": "USDJPY=X",
                "intervals": {
                    "5m": {"seconds": 300, "description": "5分足"},
                    "1h": {"seconds": 3600, "description": "1時間足"},
                    "4h": {"seconds": 14400, "description": "4時間足"},
                    "1d": {"seconds": 86400, "description": "日足"},
                },
                "max_retries": 3,
                "retry_delay": 60,
                "fetch_history_days": 7,
            },
            # スケジューラー設定
            "scheduler": {
                "data_fetch_interval": 300,  # 5分
                "d1_fetch_interval": 86400,  # 24時間
                "pattern_detection_interval": 300,  # 5分
                "notification_interval": 60,  # 1分
                "max_concurrent_tasks": 5,
                "task_timeout": 300,
            },
            # テクニカル指標設定
            "technical_indicators": {
                "rsi": {
                    "period": 14,
                    "overbought_threshold": 70,
                    "oversold_threshold": 30,
                },
                "macd": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9,
                },
                "bollinger_bands": {
                    "period": 20,
                    "std_dev": 2,
                },
            },
            # パターン検出設定
            "pattern_detection": {
                "confidence_threshold": 60.0,
                "max_patterns_per_cycle": 10,
                "duplicate_check_hours": 24,
                "enabled_patterns": [
                    "trend_reversal",
                    "pullback",
                    "divergence",
                    "breakout",
                    "rsi_battle",
                    "composite_signal",
                ],
            },
            # 通知設定
            "notifications": {
                "discord": {
                    "webhook_url": "",
                    "enabled": True,
                    "notification_types": ["pattern_detection"],
                    "rate_limit_per_minute": 20,
                },
                "discord_monitoring": {
                    "webhook_url": "",
                    "enabled": True,
                    "notification_types": [
                        "system_status",
                        "error_alert",
                        "performance_report",
                        "log_summary",
                    ],
                    "rate_limit_per_minute": 10,
                },
                "email": {
                    "enabled": False,
                    "smtp_server": "",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "recipients": [],
                },
            },
            # ログ設定
            "logging": {
                "level": "INFO",
                "file_path": "logs/app.log",
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            # システム設定
            "system": {
                "timezone": "Asia/Tokyo",
                "locale": "ja_JP.UTF-8",
                "debug_mode": False,
                "maintenance_mode": False,
                "auto_restart": True,
                "health_check_interval": 300,
            },
            # パフォーマンス設定
            "performance": {
                "max_memory_usage": 1073741824,  # 1GB
                "max_cpu_usage": 80.0,
                "data_cleanup_interval": 86400,  # 24時間
                "data_retention_days": 30,
                "cache_size": 1000,
            },
        }

    def _ensure_config_directory(self):
        """
        設定ディレクトリを確保
        """
        config_dir = Path(self.config_file_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """
        設定を読み込み
        """
        try:
            # 環境変数から設定を読み込み
            self._load_from_environment()

            # 設定ファイルから設定を読み込み
            self._load_from_file()

            # デフォルト設定で補完
            self._merge_with_defaults()

            # 設定を検証
            self._validate_config()

            self.logger.info("システム設定の読み込みが完了しました")

        except Exception as e:
            self.logger.error(f"設定の読み込みに失敗しました: {e}")
            # デフォルト設定を使用
            self._config = self._default_config.copy()
            self.logger.warning("デフォルト設定を使用します")

    def _load_from_environment(self):
        """
        環境変数から設定を読み込み
        """
        env_mappings = {
            "DATABASE_URL": ("database", "url"),
            "DISCORD_WEBHOOK_URL": ("notifications", "discord", "webhook_url"),
            "DISCORD_MONITORING_WEBHOOK_URL": (
                "notifications",
                "discord_monitoring",
                "webhook_url",
            ),
            "LOG_LEVEL": ("logging", "level"),
            "DEBUG_MODE": ("system", "debug_mode"),
            "TIMEZONE": ("system", "timezone"),
            "CURRENCY_PAIR": ("data_fetch", "currency_pair"),
            "SYMBOL": ("data_fetch", "symbol"),
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 環境変数の値を適切な型に変換
                converted_value = self._convert_env_value(env_var, value)
                self._set_nested_value(self._config, config_path, converted_value)

    def _convert_env_value(self, env_var: str, value: str) -> Any:
        """
        環境変数の値を適切な型に変換
        """
        if env_var == "DEBUG_MODE":
            return value.lower() in ("true", "1", "yes", "on")
        elif env_var in [
            "DATABASE_URL",
            "DISCORD_WEBHOOK_URL",
            "LOG_LEVEL",
            "TIMEZONE",
            "CURRENCY_PAIR",
            "SYMBOL",
        ]:
            return value
        else:
            # 数値として解析を試行
            try:
                if "." in value:
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                return value

    def _load_from_file(self):
        """
        設定ファイルから設定を読み込み
        """
        try:
            if Path(self.config_file_path).exists():
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:  # ファイルが空でない場合のみJSON解析
                        file_config = json.loads(content)
                        self._merge_configs(self._config, file_config)
                        self.logger.info(f"設定ファイルを読み込みました: {self.config_file_path}")
                    else:
                        self.logger.info(f"設定ファイルが空です: {self.config_file_path}")
        except Exception as e:
            self.logger.warning(f"設定ファイルの読み込みに失敗しました: {e}")

    def _merge_with_defaults(self):
        """
        デフォルト設定で補完
        """
        self._merge_configs(self._config, self._default_config)

    def _merge_configs(self, target: Dict, source: Dict):
        """
        設定をマージ
        """
        for key, value in source.items():
            if key not in target:
                target[key] = value
            elif isinstance(value, dict) and isinstance(target[key], dict):
                self._merge_configs(target[key], value)

    def _set_nested_value(self, config: Dict, path: tuple, value: Any):
        """
        ネストした設定値を設定
        """
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    def _validate_config(self):
        """
        設定を検証
        """
        errors = []

        # 必須設定の検証
        required_configs = [
            ("database", "url"),
            ("data_fetch", "currency_pair"),
            ("data_fetch", "symbol"),
        ]

        for config_path in required_configs:
            if not self._get_nested_value(self._config, config_path):
                errors.append(f"必須設定が不足しています: {'.'.join(config_path)}")

        # 値の検証
        if self._config.get("scheduler", {}).get("data_fetch_interval", 0) <= 0:
            errors.append("data_fetch_intervalは正の値である必要があります")

        if self._config.get("data_fetch", {}).get("max_retries", 0) < 0:
            errors.append("max_retriesは0以上の値である必要があります")

        if errors:
            error_msg = "; ".join(errors)
            self.logger.error(f"設定検証エラー: {error_msg}")
            raise ValueError(f"設定検証エラー: {error_msg}")

    def _get_nested_value(self, config: Dict, path: tuple) -> Any:
        """
        ネストした設定値を取得
        """
        current = config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            key: 設定キー（例: "database.url", "scheduler.data_fetch_interval"）
            default: デフォルト値

        Returns:
            設定値
        """
        try:
            keys = key.split(".")
            value = self._get_nested_value(self._config, tuple(keys))
            return value if value is not None else default
        except Exception as e:
            self.logger.warning(f"設定値の取得に失敗しました: {key}, {e}")
            return default

    def set(self, key: str, value: Any, validate: bool = True):
        """
        設定値を設定

        Args:
            key: 設定キー（例: "database.url", "scheduler.data_fetch_interval"）
            value: 設定値
            validate: 設定後に検証を実行するかどうか
        """
        try:
            keys = key.split(".")
            self._set_nested_value(self._config, tuple(keys), value)

            # 設定値を設定後に検証を実行（オプション）
            if validate:
                self._validate_config()

            self.logger.info(f"設定値を更新しました: {key} = {value}")
        except Exception as e:
            self.logger.error(f"設定値の設定に失敗しました: {key}, {e}")
            raise

    def get_database_config(self) -> Dict[str, Any]:
        """
        データベース設定を取得
        """
        return self._config.get("database", {})

    def get_data_fetch_config(self) -> Dict[str, Any]:
        """
        データ取得設定を取得
        """
        return self._config.get("data_fetch", {})

    def get_scheduler_config(self) -> Dict[str, Any]:
        """
        スケジューラー設定を取得
        """
        return self._config.get("scheduler", {})

    def get_technical_indicators_config(self) -> Dict[str, Any]:
        """
        テクニカル指標設定を取得
        """
        return self._config.get("technical_indicators", {})

    def get_pattern_detection_config(self) -> Dict[str, Any]:
        """
        パターン検出設定を取得
        """
        return self._config.get("pattern_detection", {})

    def get_notifications_config(self) -> Dict[str, Any]:
        """
        通知設定を取得
        """
        return self._config.get("notifications", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        ログ設定を取得
        """
        return self._config.get("logging", {})

    def get_system_config(self) -> Dict[str, Any]:
        """
        システム設定を取得
        """
        return self._config.get("system", {})

    def get_performance_config(self) -> Dict[str, Any]:
        """
        パフォーマンス設定を取得
        """
        return self._config.get("performance", {})

    def save_config(self):
        """
        設定をファイルに保存
        """
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"設定を保存しました: {self.config_file_path}")
        except Exception as e:
            self.logger.error(f"設定の保存に失敗しました: {e}")
            raise

    def reload_config(self):
        """
        設定を再読み込み
        """
        self.logger.info("設定を再読み込み中...")
        self._config = {}
        self._load_config()
        self.logger.info("設定の再読み込みが完了しました")

    def get_all_config(self) -> Dict[str, Any]:
        """
        全設定を取得
        """
        return self._config.copy()

    def update_config(self, updates: Dict[str, Any]):
        """
        設定を一括更新

        Args:
            updates: 更新する設定の辞書
        """
        try:
            self._merge_configs(self._config, updates)
            self._validate_config()
            self.logger.info("設定を一括更新しました")
        except Exception as e:
            self.logger.error(f"設定の一括更新に失敗しました: {e}")
            raise

    def reset_to_defaults(self):
        """
        設定をデフォルトにリセット
        """
        self.logger.info("設定をデフォルトにリセット中...")
        self._config = self._default_config.copy()
        self.logger.info("設定をデフォルトにリセットしました")

    def export_config(self, file_path: str):
        """
        設定をエクスポート

        Args:
            file_path: エクスポート先ファイルパス
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"設定をエクスポートしました: {file_path}")
        except Exception as e:
            self.logger.error(f"設定のエクスポートに失敗しました: {e}")
            raise

    def import_config(self, file_path: str):
        """
        設定をインポート

        Args:
            file_path: インポート元ファイルパス
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                imported_config = json.load(f)
            self._config = imported_config
            self._validate_config()
            self.logger.info(f"設定をインポートしました: {file_path}")
        except Exception as e:
            self.logger.error(f"設定のインポートに失敗しました: {e}")
            raise

    def get_config_summary(self) -> Dict[str, Any]:
        """
        設定のサマリーを取得
        """
        return {
            "database_url": self.get("database.url", ""),
            "currency_pair": self.get("data_fetch.currency_pair", ""),
            "data_fetch_interval": self.get("scheduler.data_fetch_interval", 0),
            "discord_enabled": self.get("notifications.discord.enabled", False),
            "debug_mode": self.get("system.debug_mode", False),
            "log_level": self.get("logging.level", ""),
            "timezone": self.get("system.timezone", ""),
        }


# グローバル設定マネージャーインスタンス
_config_manager: Optional[SystemConfigManager] = None


def get_config_manager() -> SystemConfigManager:
    """
    グローバル設定マネージャーを取得
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = SystemConfigManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """
    設定値を取得（簡易アクセス）
    """
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any):
    """
    設定値を設定（簡易アクセス）
    """
    get_config_manager().set(key, value)
