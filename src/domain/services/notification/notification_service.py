"""
通知サービス

Discord通知のメインサービス（多国対応）
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.domain.entities import AIReport, EconomicEvent
from src.infrastructure.external.discord import DiscordClient

from .discord_message_builder import DiscordMessageBuilder
from .notification_cooldown_manager import NotificationCooldownManager
from .notification_rule_engine import NotificationRuleEngine


class NotificationService:
    """
    通知サービス

    Discord通知の送信、ルール適用、クールダウン管理を統合する
    """

    def __init__(
        self,
        discord_client: DiscordClient,
        message_builder: Optional[DiscordMessageBuilder] = None,
        rule_engine: Optional[NotificationRuleEngine] = None,
        cooldown_manager: Optional[NotificationCooldownManager] = None,
    ):
        """
        初期化

        Args:
            discord_client: Discordクライアント
            message_builder: メッセージビルダー（デフォルト値あり）
            rule_engine: ルールエンジン（デフォルト値あり）
            cooldown_manager: クールダウンマネージャー（デフォルト値あり）
        """
        self.discord_client = discord_client
        self.logger = logging.getLogger(self.__class__.__name__)

        # デフォルトのサブコンポーネントを作成
        self.message_builder = message_builder or DiscordMessageBuilder()
        self.rule_engine = rule_engine or NotificationRuleEngine()
        self.cooldown_manager = cooldown_manager or NotificationCooldownManager()

    async def send_event_notification(
        self,
        event: EconomicEvent,
        notification_type: str = "new_event",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        イベント通知を送信

        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            additional_data: 追加データ

        Returns:
            bool: 送信成功時True
        """
        try:
            self.logger.info(
                f"イベント通知送信開始: {event.event_id}, " f"type: {notification_type}"
            )

            # 通知ルールの確認
            if not self.rule_engine.should_send_notification(event, notification_type):
                self.logger.debug(
                    f"ルールによりスキップ: {event.event_id}, "
                    f"type: {notification_type}"
                )
                return False

            # クールダウンの確認
            if not self.cooldown_manager.can_send_notification(
                event, notification_type
            ):
                self.logger.debug(
                    f"クールダウンによりスキップ: {event.event_id}, "
                    f"type: {notification_type}"
                )
                return False

            # メッセージの作成
            message_data = self.message_builder.build_event_message(
                event, notification_type, additional_data
            )

            # Discord送信
            success = await self._send_discord_message(message_data)

            if success:
                # クールダウンの記録
                self.cooldown_manager.record_notification(event, notification_type)

                self.logger.info(f"イベント通知送信完了: {event.event_id}")
            else:
                self.logger.error(f"イベント通知送信失敗: {event.event_id}")

            return success

        except Exception as e:
            self.logger.error(
                f"イベント通知送信エラー: {e}, event_id: {event.event_id}"
            )
            return False

    async def send_forecast_change_notification(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        予測値変更通知を送信

        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント
            additional_data: 追加データ

        Returns:
            bool: 送信成功時True
        """
        try:
            self.logger.info(f"予測値変更通知送信開始: {new_event.event_id}")

            # 変更の計算
            change_data = self._calculate_forecast_change(old_event, new_event)

            # 通知ルールの確認
            if not self.rule_engine.should_send_forecast_change_notification(
                old_event, new_event, change_data
            ):
                self.logger.debug(
                    f"予測値変更ルールによりスキップ: {new_event.event_id}"
                )
                return False

            # クールダウンの確認
            if not self.cooldown_manager.can_send_notification(
                new_event, "forecast_change"
            ):
                self.logger.debug(
                    f"予測値変更クールダウンによりスキップ: {new_event.event_id}"
                )
                return False

            # メッセージの作成
            message_data = self.message_builder.build_forecast_change_message(
                old_event, new_event, change_data, additional_data
            )

            # Discord送信
            success = await self._send_discord_message(message_data)

            if success:
                self.cooldown_manager.record_notification(new_event, "forecast_change")

                self.logger.info(f"予測値変更通知送信完了: {new_event.event_id}")

            return success

        except Exception as e:
            self.logger.error(
                f"予測値変更通知送信エラー: {e}, event_id: {new_event.event_id}"
            )
            return False

    async def send_actual_announcement_notification(
        self, event: EconomicEvent, additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        実際値発表通知を送信

        Args:
            event: 経済イベント
            additional_data: 追加データ

        Returns:
            bool: 送信成功時True
        """
        try:
            self.logger.info(f"実際値発表通知送信開始: {event.event_id}")

            # サプライズの計算
            surprise_data = self._calculate_surprise(event)

            # 通知ルールの確認
            if not self.rule_engine.should_send_actual_announcement_notification(
                event, surprise_data
            ):
                self.logger.debug(f"実際値発表ルールによりスキップ: {event.event_id}")
                return False

            # メッセージの作成
            message_data = self.message_builder.build_actual_announcement_message(
                event, surprise_data, additional_data
            )

            # Discord送信
            success = await self._send_discord_message(message_data)

            if success:
                self.cooldown_manager.record_notification(event, "actual_announcement")

                self.logger.info(f"実際値発表通知送信完了: {event.event_id}")

            return success

        except Exception as e:
            self.logger.error(
                f"実際値発表通知送信エラー: {e}, event_id: {event.event_id}"
            )
            return False

    async def send_ai_report_notification(
        self,
        event: EconomicEvent,
        ai_report: AIReport,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        AIレポート通知を送信

        Args:
            event: 経済イベント
            ai_report: AIレポート
            additional_data: 追加データ

        Returns:
            bool: 送信成功時True
        """
        try:
            self.logger.info(
                f"AIレポート通知送信開始: {event.event_id}, "
                f"report_id: {ai_report.id}"
            )

            # 通知ルールの確認
            if not self.rule_engine.should_send_ai_report_notification(
                event, ai_report
            ):
                self.logger.debug(f"AIレポートルールによりスキップ: {event.event_id}")
                return False

            # メッセージの作成
            message_data = self.message_builder.build_ai_report_message(
                event, ai_report, additional_data
            )

            # Discord送信
            success = await self._send_discord_message(message_data)

            if success:
                self.cooldown_manager.record_notification(event, "ai_report")

                self.logger.info(f"AIレポート通知送信完了: {event.event_id}")

            return success

        except Exception as e:
            self.logger.error(
                f"AIレポート通知送信エラー: {e}, event_id: {event.event_id}"
            )
            return False

    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        エラー通知を送信

        Args:
            error_type: エラータイプ
            error_message: エラーメッセージ
            context_data: コンテキストデータ

        Returns:
            bool: 送信成功時True
        """
        try:
            self.logger.info(f"エラー通知送信開始: {error_type}")

            # メッセージの作成
            message_data = self.message_builder.build_error_message(
                error_type, error_message, context_data
            )

            # Discord送信
            success = await self._send_discord_message(message_data)

            if success:
                self.logger.info(f"エラー通知送信完了: {error_type}")

            return success

        except Exception as e:
            self.logger.error(f"エラー通知送信エラー: {e}")
            return False

    async def send_system_status_notification(
        self, status: str, details: Dict[str, Any]
    ) -> bool:
        """
        システム状態通知を送信

        Args:
            status: システム状態
            details: 詳細情報

        Returns:
            bool: 送信成功時True
        """
        try:
            self.logger.info(f"システム状態通知送信開始: {status}")

            # メッセージの作成
            message_data = self.message_builder.build_system_status_message(
                status, details
            )

            # Discord送信
            success = await self._send_discord_message(message_data)

            if success:
                self.logger.info(f"システム状態通知送信完了: {status}")

            return success

        except Exception as e:
            self.logger.error(f"システム状態通知送信エラー: {e}")
            return False

    async def send_bulk_notifications(
        self,
        events: List[EconomicEvent],
        notification_type: str = "bulk_update",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        一括通知送信

        Args:
            events: 経済イベントリスト
            notification_type: 通知タイプ
            additional_data: 追加データ

        Returns:
            Dict[str, Any]: 送信結果
        """
        results = {
            "total": len(events),
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

        for event in events:
            try:
                success = await self.send_event_notification(
                    event, notification_type, additional_data
                )

                if success:
                    results["successful"] += 1
                else:
                    results["skipped"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"event_id": event.event_id, "error": str(e)})

        self.logger.info(
            f"一括通知送信完了: 成功={results['successful']}, "
            f"失敗={results['failed']}, スキップ={results['skipped']}"
        )

        return results

    async def _send_discord_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Discordメッセージ送信

        Args:
            message_data: メッセージデータ

        Returns:
            bool: 送信成功時True
        """
        try:
            # 経済指標専用チャンネルを使用
            channel_type = "economic_indicators"

            if "embeds" in message_data:
                # Embedメッセージの送信
                embed = message_data["embeds"][0] if message_data["embeds"] else {}
                success = await self.discord_client.send_embed(
                    title=embed.get("title", ""),
                    description=embed.get("description", ""),
                    color=embed.get("color", 0x00FF00),
                    fields=embed.get("fields", []),
                    footer=embed.get("footer"),
                    timestamp=embed.get("timestamp"),
                    username=embed.get("username"),
                    avatar_url=embed.get("avatar_url"),
                    channel_type=channel_type,
                )
            else:
                # プレーンテキストメッセージの送信
                success = await self.discord_client.send_message(
                    content=message_data.get("content", ""), channel_type=channel_type
                )

            return success

        except Exception as e:
            self.logger.error(f"Discord送信エラー: {e}")
            return False

    def _calculate_forecast_change(
        self, old_event: EconomicEvent, new_event: EconomicEvent
    ) -> Dict[str, Any]:
        """
        予測値変更の計算

        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント

        Returns:
            Dict[str, Any]: 変更データ
        """
        change_data = {
            "old_forecast": old_event.forecast_value,
            "new_forecast": new_event.forecast_value,
            "change_amount": None,
            "change_percentage": None,
            "direction": "no_change",
        }

        if (
            old_event.forecast_value is not None
            and new_event.forecast_value is not None
        ):

            change_amount = new_event.forecast_value - old_event.forecast_value
            change_data["change_amount"] = change_amount

            if old_event.forecast_value != 0:
                change_percentage = (change_amount / old_event.forecast_value) * 100
                change_data["change_percentage"] = change_percentage

            if change_amount > 0:
                change_data["direction"] = "increase"
            elif change_amount < 0:
                change_data["direction"] = "decrease"

        return change_data

    def _calculate_surprise(self, event: EconomicEvent) -> Dict[str, Any]:
        """
        サプライズの計算

        Args:
            event: 経済イベント

        Returns:
            Dict[str, Any]: サプライズデータ
        """
        surprise_data = {
            "actual": event.actual_value,
            "forecast": event.forecast_value,
            "surprise_amount": None,
            "surprise_percentage": None,
            "direction": "no_surprise",
            "magnitude": "none",
        }

        if event.actual_value is not None and event.forecast_value is not None:

            surprise_amount = event.actual_value - event.forecast_value
            surprise_data["surprise_amount"] = surprise_amount

            if event.forecast_value != 0:
                surprise_percentage = (surprise_amount / event.forecast_value) * 100
                surprise_data["surprise_percentage"] = surprise_percentage

                # 方向の判定
                if surprise_amount > 0:
                    surprise_data["direction"] = "positive"
                elif surprise_amount < 0:
                    surprise_data["direction"] = "negative"

                # 大きさの判定
                abs_percentage = abs(surprise_percentage)
                if abs_percentage > 20:
                    surprise_data["magnitude"] = "large"
                elif abs_percentage > 10:
                    surprise_data["magnitude"] = "medium"
                elif abs_percentage > 5:
                    surprise_data["magnitude"] = "small"

        return surprise_data

    async def get_service_stats(self) -> Dict[str, Any]:
        """
        サービス統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            return {
                "service": "NotificationService",
                "message_builder_stats": self.message_builder.get_stats(),
                "rule_engine_stats": self.rule_engine.get_stats(),
                "cooldown_manager_stats": self.cooldown_manager.get_stats(),
                "discord_client_health": await self.discord_client.health_check(),
            }
        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {
                "service": "NotificationService",
                "error": str(e),
            }

    async def health_check(self) -> bool:
        """
        ヘルスチェック

        Returns:
            bool: サービスが正常かどうか
        """
        try:
            # Discordクライアントの確認
            discord_health = await self.discord_client.health_check()

            # 各コンポーネントの確認
            message_builder_health = self.message_builder.health_check()
            rule_engine_health = self.rule_engine.health_check()
            cooldown_manager_health = self.cooldown_manager.health_check()

            return all(
                [
                    discord_health,
                    message_builder_health,
                    rule_engine_health,
                    cooldown_manager_health,
                ]
            )

        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
