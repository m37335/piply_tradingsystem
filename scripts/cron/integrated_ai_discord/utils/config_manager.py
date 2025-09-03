#!/usr/bin/env python3
"""
Config Manager Module
設定管理機能
"""

import os
from typing import Optional


class ConfigManager:
    """設定管理クラス"""

    def __init__(self):
        self._load_env_file()

    def _load_env_file(self):
        """環境変数ファイルを読み込み"""
        if os.path.exists("/app/.env"):
            with open("/app/.env", "r") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        try:
                            key, value = line.strip().split("=", 1)
                            os.environ[key] = value
                        except ValueError:
                            pass

    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI APIキーを取得"""
        return os.getenv("OPENAI_API_KEY")

    @property
    def discord_webhook_url(self) -> Optional[str]:
        """Discord Webhook URLを取得"""
        return os.getenv("DISCORD_WEBHOOK_URL")

    @property
    def discord_monitoring_webhook_url(self) -> Optional[str]:
        """Discord監視用Webhook URLを取得"""
        return os.getenv("DISCORD_MONITORING_WEBHOOK_URL")

    def validate_config(self) -> bool:
        """設定の妥当性を検証"""
        if not self.openai_api_key or self.openai_api_key == "your_openai_api_key":
            print("⚠️ OpenAI APIキーが未設定です")
            return False

        if not self.discord_webhook_url:
            print("⚠️ Discord Webhook URLが未設定です")
            return False

        return True

    def get_config_summary(self) -> dict:
        """設定サマリーを取得"""
        return {
            "openai_api_key_set": bool(
                self.openai_api_key and self.openai_api_key != "your_openai_api_key"
            ),
            "discord_webhook_set": bool(self.discord_webhook_url),
            "monitoring_webhook_set": bool(self.discord_monitoring_webhook_url),
        }
