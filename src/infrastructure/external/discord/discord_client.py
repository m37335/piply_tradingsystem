"""
Discordクライアント
Discord Webhookを使用した通知機能を提供
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .discord_embed_builder import DiscordEmbedBuilder
from .discord_error_handler import DiscordErrorHandler
from src.infrastructure.config.notification import DiscordConfig


class DiscordClient:
    """Discord Webhookクライアント"""

    def __init__(
        self,
        webhook_url: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        config: Optional[DiscordConfig] = None,
    ):
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.config = config or DiscordConfig.from_env()
        self.logger = logging.getLogger(self.__class__.__name__)

        # コンポーネント
        self.embed_builder = DiscordEmbedBuilder()
        self.error_handler = DiscordErrorHandler()

        # セッション管理
        self._session: Optional[ClientSession] = None
        self._rate_limit_reset = 0
        self._rate_limit_remaining = 5

    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.disconnect()

    async def connect(self) -> bool:
        """HTTPセッションを開始"""
        try:
            timeout = ClientTimeout(total=self.timeout)
            self._session = ClientSession(timeout=timeout)
            self.logger.info("Discord client session started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Discord session: {e}")
            return False

    async def disconnect(self) -> None:
        """HTTPセッションを終了"""
        try:
            if self._session:
                await self._session.close()
                self._session = None
                self.logger.info("Discord client session closed")
        except Exception as e:
            self.logger.error(f"Error closing Discord session: {e}")

    async def _check_rate_limit(self) -> bool:
        """レート制限をチェック"""
        current_time = time.time()

        if current_time < self._rate_limit_reset:
            return False

        if self._rate_limit_remaining <= 0:
            return False

        return True

    async def _update_rate_limit(self, headers: Dict[str, str]) -> None:
        """レート制限情報を更新"""
        try:
            if "X-RateLimit-Reset" in headers:
                self._rate_limit_reset = int(headers["X-RateLimit-Reset"])

            if "X-RateLimit-Remaining" in headers:
                self._rate_limit_remaining = int(headers["X-RateLimit-Remaining"])
        except (ValueError, KeyError) as e:
            self.logger.warning(f"Failed to parse rate limit headers: {e}")

    async def send_message(
        self,
        content: str,
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        channel_type: str = "default",
    ) -> Optional[str]:
        """
        メッセージを送信

        Args:
            content: メッセージ内容
            embeds: 埋め込みメッセージのリスト
            username: 送信者名（オーバーライド）
            avatar_url: アバターURL（オーバーライド）

        Returns:
            Optional[str]: 送信されたメッセージのID
        """
        if not self._session:
            self.logger.error("Discord session not initialized")
            return None

        # レート制限チェック
        if not await self._check_rate_limit():
            self.logger.warning("Rate limit exceeded, skipping message")
            return None

        # ペイロードの構築
        payload = {
            "content": content,
            "username": username or self.username,
            "avatar_url": avatar_url or self.avatar_url,
        }

        if embeds:
            payload["embeds"] = embeds

        # チャンネルタイプに応じたWebhook URLを取得
        webhook_url = self._get_webhook_url(channel_type)

        # 送信の実行
        for attempt in range(self.max_retries):
            try:
                async with self._session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    # レート制限情報を更新
                    await self._update_rate_limit(response.headers)

                    if response.status == 204:
                        self.logger.info("Message sent successfully")
                        return "success"  # Discord WebhookはメッセージIDを返さない
                    elif response.status == 429:
                        # レート制限
                        retry_after = int(
                            response.headers.get("Retry-After", self.retry_delay)
                        )
                        self.logger.warning(
                            f"Rate limited, retrying after {retry_after} seconds"
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Failed to send message: {response.status} - {error_text}"
                        )
                        return None

            except ClientError as e:
                self.logger.error(
                    f"Network error sending message (attempt {attempt + 1}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected error sending message: {e}")
                return None

        return None

    async def send_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00FF00,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        channel_type: str = "default",
    ) -> Optional[str]:
        """
        埋め込みメッセージを送信

        Args:
            title: タイトル
            description: 説明
            color: 色（16進数）
            fields: フィールドのリスト
            footer: フッター情報
            timestamp: タイムスタンプ
            username: 送信者名
            avatar_url: アバターURL

        Returns:
            Optional[str]: 送信されたメッセージのID
        """
        embed = self.embed_builder.create_embed(
            title=title,
            description=description,
            color=color,
            fields=fields,
            footer=footer,
            timestamp=timestamp,
        )

        return await self.send_message(
            content="",
            embeds=[embed],
            username=username,
            avatar_url=avatar_url,
            channel_type=channel_type,
        )

    async def send_economic_event_notification(
        self, event_data: Dict[str, Any], notification_type: str = "new_event"
    ) -> Optional[str]:
        """
        経済イベント通知を送信

        Args:
            event_data: イベントデータ
            notification_type: 通知タイプ

        Returns:
            Optional[str]: 送信されたメッセージのID
        """
        try:
            # 通知タイプに応じた埋め込みメッセージを作成
            embed = self.embed_builder.create_economic_event_embed(
                event_data, notification_type
            )

            # メッセージを送信
            return await self.send_message(
                content="", embeds=[embed], username="Economic Calendar Bot"
            )

        except Exception as e:
            self.logger.error(f"Error sending economic event notification: {e}")
            return None

    async def send_ai_report_notification(
        self, report_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        AIレポート通知を送信

        Args:
            report_data: レポートデータ

        Returns:
            Optional[str]: 送信されたメッセージのID
        """
        try:
            # AIレポート用の埋め込みメッセージを作成
            embed = self.embed_builder.create_ai_report_embed(report_data)

            # メッセージを送信
            return await self.send_message(
                content="", embeds=[embed], username="AI Analysis Bot"
            )

        except Exception as e:
            self.logger.error(f"Error sending AI report notification: {e}")
            return None

    async def send_error_notification(
        self,
        error_message: str,
        error_type: str = "general",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        エラー通知を送信

        Args:
            error_message: エラーメッセージ
            error_type: エラータイプ
            context: エラーコンテキスト

        Returns:
            Optional[str]: 送信されたメッセージのID
        """
        try:
            # エラー用の埋め込みメッセージを作成
            embed = self.embed_builder.create_error_embed(
                error_message, error_type, context
            )

            # メッセージを送信
            return await self.send_message(
                content="⚠️ システムエラーが発生しました",
                embeds=[embed],
                username="System Monitor",
            )

        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return None

    async def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功時True
        """
        try:
            if not self._session:
                return False

            # 簡単なテストメッセージを送信
            result = await self.send_message(
                content="🔧 接続テスト - システムは正常に動作しています",
                username="System Test",
            )

            return result is not None

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        クライアントの状態を取得

        Returns:
            Dict[str, Any]: 状態情報
        """
        return {
            "webhook_url": self.webhook_url,
            "username": self.username,
            "session_active": self._session is not None,
            "rate_limit_reset": self._rate_limit_reset,
            "rate_limit_remaining": self._rate_limit_remaining,
        }

    def _get_webhook_url(self, channel_type: str = "default") -> str:
        """
        チャンネルタイプに応じたWebhook URLを取得
        
        Args:
            channel_type: チャンネルタイプ ("default", "economic_indicators")
            
        Returns:
            str: Webhook URL
        """
        return self.config.get_webhook_url(channel_type)
