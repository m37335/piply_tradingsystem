#!/usr/bin/env python3
"""
ログ管理システム

USD/JPY特化の5分おきデータ取得システムのログ管理機能
"""

import asyncio
import json
import logging
import logging.handlers
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class LogManager:
    """
    ログ管理クラス
    """

    def __init__(self, config_manager: SystemConfigManager):
        self.config_manager = config_manager
        self.log_file_path = config_manager.get("logging.file_path")
        self.max_file_size = config_manager.get("logging.max_file_size", 52428800)
        self.backup_count = config_manager.get("logging.backup_count", 10)
        self.log_format = config_manager.get("logging.format")
        self.log_level = config_manager.get("logging.level", "INFO")

        self.setup_logging()
        self.log_entries = []
        self.error_count = 0
        self.warning_count = 0
        self.info_count = 0

    def setup_logging(self):
        """
        ログ設定をセットアップ
        """
        try:
            # ログディレクトリを作成
            log_dir = Path(self.log_file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)

            # ログフォーマッターを設定
            formatter = logging.Formatter(self.log_format)

            # ファイルハンドラーを設定（ローテーション付き）
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file_path,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)

            # コンソールハンドラーを設定
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            # ルートロガーを設定
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, self.log_level))

            # 既存のハンドラーをクリア
            root_logger.handlers.clear()

            # 新しいハンドラーを追加
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)

            logger.info("Logging setup completed")

        except Exception as e:
            print(f"Logging setup failed: {e}")

    async def log_system_event(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        additional_data: Optional[Dict] = None,
    ):
        """
        システムイベントをログに記録
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "message": message,
                "level": level,
                "additional_data": additional_data or {},
            }

            # ログエントリを保存
            self.log_entries.append(log_entry)

            # カウンターを更新
            if level == "ERROR":
                self.error_count += 1
            elif level == "WARNING":
                self.warning_count += 1
            elif level == "INFO":
                self.info_count += 1

            # ログレベルに応じてログ出力
            if level == "ERROR":
                logger.error(f"[{event_type}] {message}")
            elif level == "WARNING":
                logger.warning(f"[{event_type}] {message}")
            elif level == "DEBUG":
                logger.debug(f"[{event_type}] {message}")
            else:
                logger.info(f"[{event_type}] {message}")

            # ログエントリをファイルに保存
            await self._save_log_entry(log_entry)

        except Exception as e:
            print(f"Error logging system event: {e}")

    async def _save_log_entry(self, log_entry: Dict):
        """
        ログエントリをファイルに保存
        """
        try:
            log_file = Path(self.log_file_path)

            # JSON形式でログエントリを保存
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"Error saving log entry: {e}")

    async def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        ログ統計を取得
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # 指定時間内のログエントリをフィルタリング
            recent_entries = [
                entry
                for entry in self.log_entries
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]

            # 統計を計算
            stats = {
                "total_entries": len(recent_entries),
                "error_count": len(
                    [e for e in recent_entries if e["level"] == "ERROR"]
                ),
                "warning_count": len(
                    [e for e in recent_entries if e["level"] == "WARNING"]
                ),
                "info_count": len([e for e in recent_entries if e["level"] == "INFO"]),
                "debug_count": len(
                    [e for e in recent_entries if e["level"] == "DEBUG"]
                ),
                "event_types": {},
                "time_period_hours": hours,
            }

            # イベントタイプ別の統計
            for entry in recent_entries:
                event_type = entry["event_type"]
                stats["event_types"][event_type] = (
                    stats["event_types"].get(event_type, 0) + 1
                )

            return stats

        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {}

    async def search_logs(
        self,
        search_term: str,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        hours: int = 24,
    ) -> List[Dict]:
        """
        ログを検索
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # 指定時間内のログエントリをフィルタリング
            recent_entries = [
                entry
                for entry in self.log_entries
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]

            # 検索条件でフィルタリング
            filtered_entries = []
            for entry in recent_entries:
                # レベルフィルター
                if level and entry["level"] != level:
                    continue

                # イベントタイプフィルター
                if event_type and entry["event_type"] != event_type:
                    continue

                # 検索語フィルター
                if search_term.lower() in entry["message"].lower():
                    filtered_entries.append(entry)

            return filtered_entries

        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []

    async def cleanup_old_logs(self, days: int = 7):
        """
        古いログをクリーンアップ
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)

            # 古いログエントリを削除
            self.log_entries = [
                entry
                for entry in self.log_entries
                if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]

            # ログファイルのローテーションを確認
            log_file = Path(self.log_file_path)
            if log_file.exists() and log_file.stat().st_size > self.max_file_size:
                logger.info("Log file rotation triggered")

            logger.info(
                f"Log cleanup completed: removed entries older than {days} days"
            )

        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")

    async def export_logs(
        self, start_time: datetime, end_time: datetime, format: str = "json"
    ) -> str:
        """
        ログをエクスポート
        """
        try:
            # 指定期間のログエントリをフィルタリング
            filtered_entries = [
                entry
                for entry in self.log_entries
                if start_time <= datetime.fromisoformat(entry["timestamp"]) <= end_time
            ]

            if format == "json":
                return json.dumps(filtered_entries, ensure_ascii=False, indent=2)
            elif format == "csv":
                # CSV形式でエクスポート
                csv_lines = ["timestamp,event_type,level,message"]
                for entry in filtered_entries:
                    message = entry["message"].replace('"', '""')
                    csv_lines.append(
                        f'"{entry["timestamp"]}","{entry["event_type"]}",'
                        f'"{entry["level"]}","{message}"'
                    )
                return "\n".join(csv_lines)
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return ""

    async def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        エラーサマリーを取得
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # エラーログを取得
            error_entries = [
                entry
                for entry in self.log_entries
                if entry["level"] == "ERROR"
                and datetime.fromisoformat(entry["timestamp"]) > cutoff_time
            ]

            # エラータイプ別にグループ化
            error_types = {}
            for entry in error_entries:
                event_type = entry["event_type"]
                if event_type not in error_types:
                    error_types[event_type] = []
                error_types[event_type].append(entry)

            summary = {
                "total_errors": len(error_entries),
                "error_types": {
                    error_type: len(entries)
                    for error_type, entries in error_types.items()
                },
                "recent_errors": error_entries[-10:],  # 最新10件
                "time_period_hours": hours,
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {}

    def get_log_file_info(self) -> Dict[str, Any]:
        """
        ログファイル情報を取得
        """
        try:
            log_file = Path(self.log_file_path)

            if log_file.exists():
                stat = log_file.stat()
                return {
                    "file_path": str(log_file),
                    "file_size_bytes": stat.st_size,
                    "file_size_mb": stat.st_size / 1024 / 1024,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "exists": True,
                }
            else:
                return {"file_path": str(log_file), "exists": False}

        except Exception as e:
            logger.error(f"Error getting log file info: {e}")
            return {"error": str(e)}

    async def send_log_summary_to_discord(self, hours: int = 24):
        """
        ログサマリーをDiscordに送信
        """
        try:
            # システム監視専用のWebhook URLを使用
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                # フォールバック: 通常のDiscord Webhook URLを使用
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )
                if not webhook_url:
                    logger.warning("Discord webhook URL not configured")
                    return

            # ログ統計を取得
            stats = await self.get_log_statistics(hours)
            error_summary = await self.get_error_summary(hours)

            # エラー数に応じて色を設定
            if error_summary["total_errors"] > 10:
                color = 0xFF0000  # 赤色（危険）
            elif error_summary["total_errors"] > 5:
                color = 0xFFA500  # オレンジ（警告）
            else:
                color = 0x00FF00  # 緑色（正常）

            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "📋 ログ管理レポート",
                    "description": f"USD/JPY パターン検出システムのログ状況（過去{hours}時間）",
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                    "fields": [
                        {
                            "name": "📊 ログ統計",
                            "value": f"総ログ数: {stats['total_entries']}件\n"
                            f"エラー: {stats['error_count']}件\n"
                            f"警告: {stats['warning_count']}件\n"
                            f"情報: {stats['info_count']}件",
                            "inline": True,
                        },
                        {
                            "name": "⚠️ エラーサマリー",
                            "value": f"総エラー数: {error_summary['total_errors']}件\n"
                            f"エラータイプ数: {len(error_summary['error_types'])}種類",
                            "inline": True,
                        },
                    ],
                }

                # エラータイプ別の詳細を追加
                if error_summary["error_types"]:
                    error_types_text = "\n".join(
                        [
                            f"• {error_type}: {count}件"
                            for error_type, count in error_summary[
                                "error_types"
                            ].items()
                        ]
                    )
                    embed["fields"].append(
                        {
                            "name": "🔍 エラータイプ別",
                            "value": error_types_text,
                            "inline": False,
                        }
                    )

                # 最新のエラーを追加
                if error_summary["recent_errors"]:
                    recent_errors_text = "\n".join(
                        [
                            f"• {error['timestamp'][:19]}: {error['message'][:50]}..."
                            for error in error_summary["recent_errors"][-3:]  # 最新3件
                        ]
                    )
                    embed["fields"].append(
                        {
                            "name": "🕐 最新エラー",
                            "value": recent_errors_text,
                            "inline": False,
                        }
                    )

                await sender.send_embed(embed)
                logger.info("Log summary sent to Discord")

        except Exception as e:
            logger.error(f"Failed to send log summary to Discord: {e}")

    async def send_error_alert_to_discord(
        self, error_type: str, message: str, additional_data: Optional[Dict] = None
    ):
        """
        エラーアラートをDiscordに送信
        """
        try:
            # システム監視専用のWebhook URLを使用
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                # フォールバック: 通常のDiscord Webhook URLを使用
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )
                if not webhook_url:
                    logger.warning("Discord webhook URL not configured")
                    return

            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": f"🚨 ログエラーアラート: {error_type}",
                    "description": message,
                    "color": 0xFF0000,  # 赤色
                    "timestamp": datetime.now().isoformat(),
                    "fields": [],
                }

                # 追加データがある場合はフィールドに追加
                if additional_data:
                    for key, value in additional_data.items():
                        embed["fields"].append(
                            {"name": key, "value": str(value), "inline": True}
                        )

                await sender.send_embed(embed)
                logger.info(f"Error alert sent to Discord: {error_type}")

        except Exception as e:
            logger.error(f"Failed to send error alert to Discord: {e}")
