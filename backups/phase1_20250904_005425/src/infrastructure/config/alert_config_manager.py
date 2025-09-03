"""
Alert Configuration Manager
アラート設定管理サービス

責任:
- アラート設定の読み込み・保存
- 設定の検証
- デフォルト設定の管理
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class RateThresholdConfig(BaseModel):
    """レート閾値設定"""

    upper_threshold: float
    lower_threshold: float
    check_interval_minutes: int = 5
    severity: str = "medium"


class PatternDetectionConfig(BaseModel):
    """パターン検出設定"""

    confidence_threshold: float = 0.80
    patterns: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class SystemResourceConfig(BaseModel):
    """システムリソース設定"""

    cpu_usage: Dict[str, Any] = Field(default_factory=dict)
    memory_usage: Dict[str, Any] = Field(default_factory=dict)
    disk_usage: Dict[str, Any] = Field(default_factory=dict)


class NotificationConfig(BaseModel):
    """通知設定"""

    email: Dict[str, Any] = Field(default_factory=dict)
    discord: Dict[str, Any] = Field(default_factory=dict)
    slack: Dict[str, Any] = Field(default_factory=dict)


class AlertManagementConfig(BaseModel):
    """アラート管理設定"""

    auto_resolve: Dict[str, Any] = Field(default_factory=dict)
    escalation: Dict[str, Any] = Field(default_factory=dict)
    retention: Dict[str, Any] = Field(default_factory=dict)


class AlertConfig(BaseModel):
    """アラート設定全体"""

    rate_threshold_alerts: Dict[str, Any] = Field(default_factory=dict)
    pattern_detection_alerts: Dict[str, Any] = Field(default_factory=dict)
    system_resource_alerts: Dict[str, Any] = Field(default_factory=dict)
    api_error_alerts: Dict[str, Any] = Field(default_factory=dict)
    data_fetch_alerts: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
    alert_management: Dict[str, Any] = Field(default_factory=dict)


class AlertConfigManager:
    """
    アラート設定管理クラス

    責任:
    - 設定ファイルの読み込み
    - 設定の検証
    - 設定の保存
    - デフォルト設定の提供
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス
        """
        self.config_path = config_path or "config/alerts.yaml"
        self._config: Optional[AlertConfig] = None

        # .envファイルを読み込み
        self._load_env_file()

        self._load_config()

    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            config_file = Path(self.config_path)

            if not config_file.exists():
                logger.warning(f"設定ファイルが見つかりません: {self.config_path}")
                logger.info("デフォルト設定を使用します")
                self._config = self._get_default_config()
                return

            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # 環境変数の置換
            config_data = self._replace_env_vars(config_data)

            # Pydanticモデルで検証
            self._config = AlertConfig(**config_data)

            logger.info(f"アラート設定を読み込みました: {self.config_path}")

        except Exception as e:
            logger.error(f"設定ファイルの読み込みエラー: {e}")
            logger.info("デフォルト設定を使用します")
            self._config = self._get_default_config()

    def _replace_env_vars(self, data: Any) -> Any:
        """環境変数を置換"""
        if isinstance(data, dict):
            return {k: self._replace_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            env_var = data[2:-1]
            # 環境変数を取得（.envファイルからも読み込み）
            env_value = os.getenv(env_var)
            if env_value:
                return env_value
            else:
                # DISCORD_CHANNEL_IDはオプショナルなので警告を出さない
                if env_var != "DISCORD_CHANNEL_ID":
                    logger.warning(f"環境変数 {env_var} が見つかりません")
                return data
        else:
            return data

    def _load_env_file(self) -> None:
        """.envファイルを読み込み"""
        try:
            from dotenv import load_dotenv

            # .envファイルを読み込み
            env_loaded = load_dotenv()
            if env_loaded:
                logger.info(".envファイルを読み込みました")
            else:
                logger.warning(".envファイルが見つかりません")

        except ImportError:
            logger.warning(
                "python-dotenvがインストールされていません。手動で.envファイルを読み込みます"
            )
            self._load_env_manual()
        except Exception as e:
            logger.error(f".envファイルの読み込みエラー: {e}")
            self._load_env_manual()

    def _load_env_manual(self) -> None:
        """手動で.envファイルを読み込み"""
        env_file = Path(".env")
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key] = value
                            logger.debug(f"環境変数 {key} を読み込みました")
                logger.info("手動で.envファイルを読み込みました")
            except Exception as e:
                logger.error(f"手動.env読み込みエラー: {e}")
        else:
            logger.warning(".envファイルが見つかりません")

    def _get_default_config(self) -> AlertConfig:
        """デフォルト設定を取得"""
        return AlertConfig(
            rate_threshold_alerts={
                "enabled": True,
                "currency_pairs": {
                    "USD/JPY": {
                        "upper_threshold": 151.00,
                        "lower_threshold": 140.00,
                        "check_interval_minutes": 5,
                        "severity": "high",
                    }
                },
            },
            pattern_detection_alerts={
                "enabled": True,
                "confidence_threshold": 0.80,
                "patterns": {
                    "reversal": {
                        "enabled": True,
                        "severity": "high",
                        "min_confidence": 0.85,
                    }
                },
            },
            system_resource_alerts={
                "enabled": True,
                "cpu_usage": {
                    "warning_threshold": 70,
                    "critical_threshold": 90,
                    "severity": "medium",
                },
                "memory_usage": {
                    "warning_threshold": 80,
                    "critical_threshold": 95,
                    "severity": "high",
                },
            },
            api_error_alerts={
                "enabled": True,
                "rate_limit_threshold": 5,
                "timeout_threshold": 3,
                "severity": "medium",
            },
            data_fetch_alerts={
                "enabled": True,
                "consecutive_failures": 3,
                "severity": "high",
                "timeframes": ["5m", "1h", "4h", "1d"],
            },
            notification_settings={
                "email": {"enabled": False, "recipients": []},
                "discord": {"enabled": True, "webhook_url": "", "channel_id": ""},
                "slack": {"enabled": False, "webhook_url": ""},
            },
            alert_management={
                "auto_resolve": {"enabled": True, "resolve_after_hours": 24},
                "escalation": {"enabled": True, "escalation_after_hours": 2},
                "retention": {"keep_resolved_days": 30},
            },
        )

    def get_config(self) -> AlertConfig:
        """
        設定を取得

        Returns:
            AlertConfig: アラート設定
        """
        return self._config

    def get_rate_threshold_config(self, currency_pair: str) -> Optional[Dict[str, Any]]:
        """
        レート閾値設定を取得

        Args:
            currency_pair: 通貨ペア

        Returns:
            Optional[Dict[str, Any]]: レート閾値設定
        """
        if not self._config:
            return None

        rate_config = self._config.rate_threshold_alerts
        if not rate_config.get("enabled", False):
            return None

        currency_pairs = rate_config.get("currency_pairs", {})
        return currency_pairs.get(currency_pair)

    def get_pattern_detection_config(
        self, pattern_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        パターン検出設定を取得

        Args:
            pattern_type: パターンタイプ

        Returns:
            Optional[Dict[str, Any]]: パターン検出設定
        """
        if not self._config:
            return None

        pattern_config = self._config.pattern_detection_alerts
        if not pattern_config.get("enabled", False):
            return None

        patterns = pattern_config.get("patterns", {})
        return patterns.get(pattern_type)

    def get_system_resource_config(self) -> Dict[str, Any]:
        """
        システムリソース設定を取得

        Returns:
            Dict[str, Any]: システムリソース設定
        """
        if not self._config:
            return {}

        return self._config.system_resource_alerts

    def get_notification_config(self) -> Dict[str, Any]:
        """
        通知設定を取得

        Returns:
            Dict[str, Any]: 通知設定
        """
        if not self._config:
            return {}

        return self._config.notification_settings

    def get_discord_webhook_url(self, alert_type: str) -> Optional[str]:
        """
        アラートタイプに応じたDiscord Webhook URLを取得

        Args:
            alert_type: アラートタイプ

        Returns:
            Optional[str]: Discord Webhook URL
        """
        if not self._config:
            return None

        notification_config = self._config.notification_settings
        discord_config = notification_config.get("discord", {})

        if not discord_config.get("enabled", False):
            return None

        # アラートタイプ別のWebhook URL設定を確認
        alert_type_webhooks = discord_config.get("alert_type_webhooks", {})

        # 特定のアラートタイプのWebhook URLを取得
        webhook_url = alert_type_webhooks.get(alert_type)

        # 設定されていない場合はデフォルトを使用
        if not webhook_url:
            webhook_url = alert_type_webhooks.get("default")

        # デフォルトも設定されていない場合は従来の設定を使用
        if not webhook_url:
            webhook_url = discord_config.get("webhook_url")

        return webhook_url

    def get_discord_channel_id(self) -> Optional[str]:
        """
        DiscordチャンネルIDを取得

        Returns:
            Optional[str]: DiscordチャンネルID
        """
        try:
            notification_config = self._config.notification_settings
            discord_config = notification_config.get("discord", {})

            return discord_config.get("channel_id")

        except Exception as e:
            logger.error(f"DiscordチャンネルID取得エラー: {e}")
            return None

    def is_alert_enabled(self, alert_type: str) -> bool:
        """
        アラートタイプが有効かどうかを確認

        Args:
            alert_type: アラートタイプ

        Returns:
            bool: 有効な場合True
        """
        if not self._config:
            return False

        config_map = {
            "rate_threshold": self._config.rate_threshold_alerts,
            "pattern_detection": self._config.pattern_detection_alerts,
            "system_resource": self._config.system_resource_alerts,
            "api_error": self._config.api_error_alerts,
            "data_fetch": self._config.data_fetch_alerts,
        }

        config = config_map.get(alert_type, {})
        return config.get("enabled", False)

    def reload_config(self) -> None:
        """設定を再読み込み"""
        logger.info("アラート設定を再読み込みします")
        self._load_config()

    def save_config(self, config: AlertConfig) -> bool:
        """
        設定を保存

        Args:
            config: 保存する設定

        Returns:
            bool: 保存成功時True
        """
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            # Pydanticモデルを辞書に変換
            config_dict = config.dict()

            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

            self._config = config
            logger.info(f"アラート設定を保存しました: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            return False
