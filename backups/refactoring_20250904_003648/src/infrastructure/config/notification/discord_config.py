"""
Discord設定クラス
Discord通知の設定を管理
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiscordConfig:
    """Discord設定"""

    # Webhook URL設定
    webhook_url: str
    economic_indicators_webhook_url: Optional[str] = None

    # メッセージ設定
    username: str = "Economic Calendar Bot"
    avatar_url: str = ""

    # 通知設定
    cooldown_period: int = 3600  # 秒
    max_message_length: int = 2000
    max_embed_fields: int = 25

    # エラー設定
    retry_attempts: int = 3
    retry_delay: int = 5

    # ログ設定
    enable_debug_logging: bool = False
    log_webhook_calls: bool = True

    @classmethod
    def from_env(cls) -> "DiscordConfig":
        """環境変数から設定を読み込み"""
        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL", "")
        economic_indicators_webhook_url = os.getenv(
            "DISCORD_ECONOMICINDICATORS_WEBHOOK_URL", None
        )

        return cls(
            webhook_url=webhook_url,
            economic_indicators_webhook_url=economic_indicators_webhook_url,
            username=os.getenv("DISCORD_USERNAME", "Economic Calendar Bot"),
            avatar_url=os.getenv("DISCORD_AVATAR_URL", ""),
            cooldown_period=int(os.getenv("DISCORD_COOLDOWN_PERIOD", "3600")),
            max_message_length=int(os.getenv("DISCORD_MAX_MESSAGE_LENGTH", "2000")),
            max_embed_fields=int(os.getenv("DISCORD_MAX_EMBED_FIELDS", "25")),
            retry_attempts=int(os.getenv("DISCORD_RETRY_ATTEMPTS", "3")),
            retry_delay=int(os.getenv("DISCORD_RETRY_DELAY", "5")),
            enable_debug_logging=os.getenv("DISCORD_DEBUG", "false").lower() == "true",
            log_webhook_calls=os.getenv("DISCORD_LOG_WEBHOOK", "true").lower()
            == "true",
        )

    def validate(self) -> bool:
        """設定の妥当性を検証"""
        # 少なくとも1つのWebhook URLが設定されているかチェック
        if not self.webhook_url and not self.economic_indicators_webhook_url:
            logging.error("Discord Webhook URLが設定されていません")
            return False

        # デフォルトWebhook URLの検証
        if self.webhook_url and not (
            self.webhook_url.startswith("https://discord.com/api/webhooks/")
            or self.webhook_url.startswith("https://canary.discord.com/api/webhooks/")
        ):
            logging.error("無効なDiscord Webhook URL形式です")
            return False

        # 経済指標専用Webhook URLの検証
        if self.economic_indicators_webhook_url and not (
            self.economic_indicators_webhook_url.startswith(
                "https://discord.com/api/webhooks/"
            )
            or self.economic_indicators_webhook_url.startswith(
                "https://canary.discord.com/api/webhooks/"
            )
        ):
            logging.error("無効な経済指標専用Discord Webhook URL形式です")
            return False

        if self.cooldown_period < 0:
            logging.error("クールダウン期間は0以上である必要があります")
            return False

        if self.max_message_length <= 0:
            logging.error("最大メッセージ長は0より大きい必要があります")
            return False

        return True

    def get_webhook_url(self, channel_type: str = "default") -> str:
        """
        チャンネルタイプに応じたWebhook URLを取得

        Args:
            channel_type: チャンネルタイプ ("default", "economic_indicators")

        Returns:
            str: Webhook URL
        """
        if (
            channel_type == "economic_indicators"
            and self.economic_indicators_webhook_url
        ):
            return self.economic_indicators_webhook_url

        # デフォルトURLがない場合は経済指標専用URLを使用
        if not self.webhook_url and self.economic_indicators_webhook_url:
            return self.economic_indicators_webhook_url

        return self.webhook_url

    def get_config_summary(self) -> dict:
        """設定サマリーを取得"""
        return {
            "webhook_url_configured": bool(self.webhook_url),
            "economic_indicators_webhook_configured": bool(
                self.economic_indicators_webhook_url
            ),
            "username": self.username,
            "cooldown_period": self.cooldown_period,
            "retry_attempts": self.retry_attempts,
            "debug_logging": self.enable_debug_logging,
        }
