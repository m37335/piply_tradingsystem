"""
Discordメッセージビルダー

国別のメッセージ作成を担当
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from src.domain.entities import AIReport, EconomicEvent


class DiscordMessageBuilder:
    """
    Discordメッセージビルダー

    各種通知メッセージとEmbedの作成を行う
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._message_count = 0

        # 国別の色設定
        self.country_colors = {
            "japan": 0xFF4500,  # オレンジレッド
            "united states": 0x0066CC,  # ブルー
            "euro zone": 0x0066FF,  # ヨーロッパブルー
            "united kingdom": 0x800080,  # パープル
            "australia": 0x00FF00,  # グリーン
            "canada": 0xFF0000,  # レッド
            "default": 0x808080,  # グレー
        }

        # 重要度別の色設定
        self.importance_colors = {
            "high": 0xFF0000,  # 赤
            "medium": 0xFFA500,  # オレンジ
            "low": 0x00FF00,  # 緑
        }

    def build_event_message(
        self,
        event: EconomicEvent,
        notification_type: str = "new_event",
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        イベントメッセージの作成

        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            additional_data: 追加データ

        Returns:
            Dict[str, Any]: メッセージデータ
        """
        try:
            self.logger.debug(f"イベントメッセージ作成: {event.event_id}")

            # Embedの作成
            embed = self._create_event_embed(event, notification_type)

            # 追加データがある場合は追加
            if additional_data:
                embed = self._add_additional_fields(embed, additional_data)

            # コンテンツメッセージの作成
            content = self._create_event_content(event, notification_type)

            self._message_count += 1

            return {
                "content": content,
                "embeds": [embed],
                "notification_type": notification_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"イベントメッセージ作成エラー: {e}")
            return self._create_fallback_message(event, notification_type)

    def build_forecast_change_message(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent,
        change_data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        予測値変更メッセージの作成

        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント
            change_data: 変更データ
            additional_data: 追加データ

        Returns:
            Dict[str, Any]: メッセージデータ
        """
        try:
            self.logger.debug(f"予測値変更メッセージ作成: {new_event.event_id}")

            # Embedの作成
            embed = self._create_forecast_change_embed(
                old_event, new_event, change_data
            )

            # 追加データがある場合は追加
            if additional_data:
                embed = self._add_additional_fields(embed, additional_data)

            # コンテンツメッセージの作成
            content = self._create_forecast_change_content(new_event, change_data)

            self._message_count += 1

            return {
                "content": content,
                "embeds": [embed],
                "notification_type": "forecast_change",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"予測値変更メッセージ作成エラー: {e}")
            return self._create_fallback_message(new_event, "forecast_change")

    def build_actual_announcement_message(
        self,
        event: EconomicEvent,
        surprise_data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        実際値発表メッセージの作成

        Args:
            event: 経済イベント
            surprise_data: サプライズデータ
            additional_data: 追加データ

        Returns:
            Dict[str, Any]: メッセージデータ
        """
        try:
            self.logger.debug(f"実際値発表メッセージ作成: {event.event_id}")

            # Embedの作成
            embed = self._create_actual_announcement_embed(event, surprise_data)

            # 追加データがある場合は追加
            if additional_data:
                embed = self._add_additional_fields(embed, additional_data)

            # コンテンツメッセージの作成
            content = self._create_actual_announcement_content(event, surprise_data)

            self._message_count += 1

            return {
                "content": content,
                "embeds": [embed],
                "notification_type": "actual_announcement",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"実際値発表メッセージ作成エラー: {e}")
            return self._create_fallback_message(event, "actual_announcement")

    def build_ai_report_message(
        self,
        event: EconomicEvent,
        ai_report: AIReport,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        AIレポートメッセージの作成

        Args:
            event: 経済イベント
            ai_report: AIレポート
            additional_data: 追加データ

        Returns:
            Dict[str, Any]: メッセージデータ
        """
        try:
            self.logger.debug(f"AIレポートメッセージ作成: {event.event_id}")

            # Embedの作成
            embed = self._create_ai_report_embed(event, ai_report)

            # 追加データがある場合は追加
            if additional_data:
                embed = self._add_additional_fields(embed, additional_data)

            # コンテンツメッセージの作成
            content = self._create_ai_report_content(event, ai_report)

            self._message_count += 1

            return {
                "content": content,
                "embeds": [embed],
                "notification_type": "ai_report",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"AIレポートメッセージ作成エラー: {e}")
            return self._create_fallback_message(event, "ai_report")

    def build_error_message(
        self,
        error_type: str,
        error_message: str,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        エラーメッセージの作成

        Args:
            error_type: エラータイプ
            error_message: エラーメッセージ
            context_data: コンテキストデータ

        Returns:
            Dict[str, Any]: メッセージデータ
        """
        try:
            embed = {
                "title": f"🚨 システムエラー: {error_type}",
                "description": error_message,
                "color": 0xFF0000,  # 赤
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [],
            }

            if context_data:
                for key, value in context_data.items():
                    embed["fields"].append(
                        {
                            "name": key,
                            "value": str(value)[:1024],  # Discord制限
                            "inline": True,
                        }
                    )

            content = f"⚠️ **エラー発生**: {error_type}"

            self._message_count += 1

            return {
                "content": content,
                "embeds": [embed],
                "notification_type": "error",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"エラーメッセージ作成エラー: {e}")
            return {
                "content": f"システムエラーが発生しました: {error_type}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def build_system_status_message(
        self, status: str, details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        システム状態メッセージの作成

        Args:
            status: システム状態
            details: 詳細情報

        Returns:
            Dict[str, Any]: メッセージデータ
        """
        try:
            # 状態に応じた色とアイコン
            status_config = {
                "healthy": {"color": 0x00FF00, "icon": "✅"},
                "warning": {"color": 0xFFA500, "icon": "⚠️"},
                "error": {"color": 0xFF0000, "icon": "🚨"},
                "maintenance": {"color": 0x808080, "icon": "🔧"},
            }

            config = status_config.get(status, {"color": 0x808080, "icon": "ℹ️"})

            embed = {
                "title": f"{config['icon']} システム状態: {status}",
                "color": config["color"],
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [],
            }

            for key, value in details.items():
                embed["fields"].append(
                    {"name": key, "value": str(value)[:1024], "inline": True}
                )

            content = f"{config['icon']} **システム状態更新**: {status}"

            self._message_count += 1

            return {
                "content": content,
                "embeds": [embed],
                "notification_type": "system_status",
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"システム状態メッセージ作成エラー: {e}")
            return {
                "content": f"システム状態: {status}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _create_event_embed(
        self, event: EconomicEvent, notification_type: str
    ) -> Dict[str, Any]:
        """イベントEmbed作成"""
        # 通知タイプに応じたアイコン
        type_icons = {
            "new_event": "📊",
            "upcoming_event": "⏰",
            "high_importance": "🚨",
        }

        icon = type_icons.get(notification_type, "📊")

        # 国別の色を取得
        color = self.country_colors.get(
            event.country.lower(),
            self.importance_colors.get(event.importance.value.lower(), 0x808080),
        )

        embed = {
            "title": f"{icon} {self._get_country_flag(event.country)} {event.event_name}",
            "color": color,
            "timestamp": (
                event.date_utc.isoformat()
                if event.date_utc
                else datetime.utcnow().isoformat()
            ),
            "fields": [
                {"name": "🏳️ 国", "value": event.country, "inline": True},
                {
                    "name": "⚡ 重要度",
                    "value": event.importance.value.upper(),
                    "inline": True,
                },
                {
                    "name": "📅 日時",
                    "value": (
                        self._format_datetime(event.date_utc)
                        if event.date_utc
                        else "未定"
                    ),
                    "inline": True,
                },
            ],
        }

        # 数値データがある場合は追加
        if event.forecast_value is not None:
            embed["fields"].append(
                {
                    "name": "🔮 予測値",
                    "value": f"{event.forecast_value} {event.unit or ''}",
                    "inline": True,
                }
            )

        if event.previous_value is not None:
            embed["fields"].append(
                {
                    "name": "📊 前回値",
                    "value": f"{event.previous_value} {event.unit or ''}",
                    "inline": True,
                }
            )

        if event.actual_value is not None:
            embed["fields"].append(
                {
                    "name": "✅ 実際値",
                    "value": f"{event.actual_value} {event.unit or ''}",
                    "inline": True,
                }
            )

        return embed

    def _create_forecast_change_embed(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent,
        change_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """予測値変更Embed作成"""

        # 変更方向に応じたアイコンと色
        direction = change_data.get("direction", "no_change")
        if direction == "increase":
            icon = "📈"
            color = 0x00FF00  # 緑
        elif direction == "decrease":
            icon = "📉"
            color = 0xFF0000  # 赤
        else:
            icon = "📊"
            color = 0xFFA500  # オレンジ

        embed = {
            "title": f"{icon} 予測値変更: {self._get_country_flag(new_event.country)} {new_event.event_name}",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "🏳️ 国", "value": new_event.country, "inline": True},
                {
                    "name": "📊 変更前",
                    "value": f"{change_data.get('old_forecast', 'N/A')} {new_event.unit or ''}",
                    "inline": True,
                },
                {
                    "name": "📊 変更後",
                    "value": f"{change_data.get('new_forecast', 'N/A')} {new_event.unit or ''}",
                    "inline": True,
                },
            ],
        }

        # 変更量と変更率を追加
        if change_data.get("change_amount") is not None:
            embed["fields"].append(
                {
                    "name": "💹 変更量",
                    "value": f"{change_data['change_amount']:+.2f} {new_event.unit or ''}",
                    "inline": True,
                }
            )

        if change_data.get("change_percentage") is not None:
            embed["fields"].append(
                {
                    "name": "📊 変更率",
                    "value": f"{change_data['change_percentage']:+.1f}%",
                    "inline": True,
                }
            )

        return embed

    def _create_actual_announcement_embed(
        self, event: EconomicEvent, surprise_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """実際値発表Embed作成"""

        # サプライズの方向と大きさに応じたアイコンと色
        direction = surprise_data.get("direction", "no_surprise")
        magnitude = surprise_data.get("magnitude", "none")

        if direction == "positive":
            icon = "🎉" if magnitude == "large" else "📈"
            color = 0x00FF00  # 緑
        elif direction == "negative":
            icon = "🚨" if magnitude == "large" else "📉"
            color = 0xFF0000  # 赤
        else:
            icon = "📊"
            color = 0x808080  # グレー

        embed = {
            "title": f"{icon} 実際値発表: {self._get_country_flag(event.country)} {event.event_name}",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {"name": "🏳️ 国", "value": event.country, "inline": True},
                {
                    "name": "🔮 予測値",
                    "value": f"{surprise_data.get('forecast', 'N/A')} {event.unit or ''}",
                    "inline": True,
                },
                {
                    "name": "✅ 実際値",
                    "value": f"{surprise_data.get('actual', 'N/A')} {event.unit or ''}",
                    "inline": True,
                },
            ],
        }

        # サプライズ情報を追加
        if surprise_data.get("surprise_amount") is not None:
            embed["fields"].append(
                {
                    "name": "💥 サプライズ",
                    "value": f"{surprise_data['surprise_amount']:+.2f} {event.unit or ''}",
                    "inline": True,
                }
            )

        if surprise_data.get("surprise_percentage") is not None:
            embed["fields"].append(
                {
                    "name": "📊 サプライズ率",
                    "value": f"{surprise_data['surprise_percentage']:+.1f}%",
                    "inline": True,
                }
            )

        return embed

    def _create_ai_report_embed(
        self, event: EconomicEvent, ai_report: AIReport
    ) -> Dict[str, Any]:
        """AIレポートEmbed作成"""

        # USD/JPY予測に応じた色
        usd_jpy_prediction = ai_report.usd_jpy_prediction
        if usd_jpy_prediction and usd_jpy_prediction.direction == "buy":
            color = 0x00FF00  # 緑（買い）
        elif usd_jpy_prediction and usd_jpy_prediction.direction == "sell":
            color = 0xFF0000  # 赤（売り）
        else:
            color = 0x0066CC  # 青（中立）

        embed = {
            "title": f"🤖 AI分析レポート: {self._get_country_flag(event.country)} {event.event_name}",
            "color": color,
            "timestamp": (
                ai_report.generated_at.isoformat()
                if ai_report.generated_at
                else datetime.utcnow().isoformat()
            ),
            "fields": [
                {"name": "🏳️ 国", "value": event.country, "inline": True},
                {
                    "name": "📊 レポートタイプ",
                    "value": ai_report.report_type,
                    "inline": True,
                },
                {
                    "name": "🎯 信頼度",
                    "value": (
                        f"{ai_report.confidence_score:.1%}"
                        if ai_report.confidence_score
                        else "N/A"
                    ),
                    "inline": True,
                },
            ],
        }

        # USD/JPY予測情報を追加
        if usd_jpy_prediction:
            direction_text = (
                "🟢 買い" if usd_jpy_prediction.direction == "buy" else "🔴 売り"
            )
            embed["fields"].append(
                {"name": "💱 USD/JPY予測", "value": direction_text, "inline": True}
            )

            if usd_jpy_prediction.strength:
                embed["fields"].append(
                    {
                        "name": "💪 強度",
                        "value": usd_jpy_prediction.strength,
                        "inline": True,
                    }
                )

            if usd_jpy_prediction.confidence:
                embed["fields"].append(
                    {
                        "name": "🎯 予測信頼度",
                        "value": f"{usd_jpy_prediction.confidence:.1%}",
                        "inline": True,
                    }
                )

        # レポート内容（要約）
        if ai_report.report_content:
            content_summary = (
                ai_report.report_content[:500] + "..."
                if len(ai_report.report_content) > 500
                else ai_report.report_content
            )
            embed["fields"].append(
                {"name": "📝 分析要約", "value": content_summary, "inline": False}
            )

        return embed

    def _create_event_content(
        self, event: EconomicEvent, notification_type: str
    ) -> str:
        """イベントコンテンツメッセージ作成"""
        type_messages = {
            "new_event": "📊 新しい経済イベント",
            "upcoming_event": "⏰ 間もなく発表",
            "high_importance": "🚨 重要経済指標",
        }

        message_type = type_messages.get(notification_type, "📊 経済イベント")
        return f"{message_type}: **{event.event_name}** ({event.country})"

    def _create_forecast_change_content(
        self, event: EconomicEvent, change_data: Dict[str, Any]
    ) -> str:
        """予測値変更コンテンツメッセージ作成"""
        direction = change_data.get("direction", "no_change")

        if direction == "increase":
            icon = "📈"
            direction_text = "上方修正"
        elif direction == "decrease":
            icon = "📉"
            direction_text = "下方修正"
        else:
            icon = "📊"
            direction_text = "修正"

        return (
            f"{icon} **予測値{direction_text}**: {event.event_name} ({event.country})"
        )

    def _create_actual_announcement_content(
        self, event: EconomicEvent, surprise_data: Dict[str, Any]
    ) -> str:
        """実際値発表コンテンツメッセージ作成"""
        magnitude = surprise_data.get("magnitude", "none")

        if magnitude == "large":
            icon = "💥"
            surprise_text = "大きなサプライズ"
        elif magnitude in ["medium", "small"]:
            icon = "📊"
            surprise_text = "サプライズ"
        else:
            icon = "✅"
            surprise_text = "発表"

        return f"{icon} **実際値{surprise_text}**: {event.event_name} ({event.country})"

    def _create_ai_report_content(
        self, event: EconomicEvent, ai_report: AIReport
    ) -> str:
        """AIレポートコンテンツメッセージ作成"""
        usd_jpy_prediction = ai_report.usd_jpy_prediction

        if usd_jpy_prediction:
            direction_text = (
                "買い推奨" if usd_jpy_prediction.direction == "buy" else "売り推奨"
            )
            return f"🤖 **AI分析完了**: {event.event_name} ({event.country}) - USD/JPY {direction_text}"
        else:
            return f"🤖 **AI分析完了**: {event.event_name} ({event.country})"

    def _get_country_flag(self, country: str) -> str:
        """国旗絵文字を取得"""
        flag_mapping = {
            "japan": "🇯🇵",
            "united states": "🇺🇸",
            "euro zone": "🇪🇺",
            "eurozone": "🇪🇺",
            "united kingdom": "🇬🇧",
            "australia": "🇦🇺",
            "canada": "🇨🇦",
            "switzerland": "🇨🇭",
            "new zealand": "🇳🇿",
        }

        return flag_mapping.get(country.lower(), "🌍")

    def _format_datetime(self, dt: datetime) -> str:
        """日時フォーマット"""
        if not dt:
            return "未定"

        try:
            # JSTに変換して表示
            jst_offset = 9  # UTC+9
            from datetime import timedelta

            jst_dt = dt + timedelta(hours=jst_offset)
            return jst_dt.strftime("%Y-%m-%d %H:%M JST")
        except:
            return str(dt)

    def _add_additional_fields(
        self, embed: Dict[str, Any], additional_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """追加フィールドを追加"""
        for key, value in additional_data.items():
            embed["fields"].append(
                {"name": key, "value": str(value)[:1024], "inline": True}  # Discord制限
            )

        return embed

    def _create_fallback_message(
        self, event: EconomicEvent, notification_type: str
    ) -> Dict[str, Any]:
        """フォールバックメッセージ作成"""
        content = f"📊 {event.event_name} ({event.country}) - {notification_type}"

        return {
            "content": content,
            "notification_type": notification_type,
            "timestamp": datetime.utcnow().isoformat(),
            "fallback": True,
        }

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "builder": "DiscordMessageBuilder",
            "messages_created": self._message_count,
            "country_colors": len(self.country_colors),
            "importance_colors": len(self.importance_colors),
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な機能の確認
            test_event = EconomicEvent(
                event_id="test",
                event_name="Test Event",
                country="japan",
                importance="high",
                date_utc=datetime.utcnow(),
            )

            # テストメッセージの作成
            test_message = self.build_event_message(test_event, "test")

            # 必要なフィールドの確認
            required_fields = ["content", "notification_type", "timestamp"]
            return all(field in test_message for field in required_fields)

        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
