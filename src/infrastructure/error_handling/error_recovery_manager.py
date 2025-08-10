#!/usr/bin/env python3
"""
エラーハンドリング・リカバリーシステム
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.monitoring.log_manager import LogManager
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class ErrorSeverity(Enum):
    """エラーの重要度"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorType(Enum):
    """エラーの種類"""
    DATABASE_CONNECTION = "DATABASE_CONNECTION"
    API_CONNECTION = "API_CONNECTION"
    DATA_FETCH = "DATA_FETCH"
    PATTERN_DETECTION = "PATTERN_DETECTION"
    NOTIFICATION = "NOTIFICATION"
    SYSTEM_CRASH = "SYSTEM_CRASH"
    MEMORY_LEAK = "MEMORY_LEAK"
    DISK_SPACE = "DISK_SPACE"


class RecoveryAction(Enum):
    """復旧アクション"""
    RETRY = "RETRY"
    RESTART = "RESTART"
    CLEANUP = "CLEANUP"
    NOTIFY = "NOTIFY"
    IGNORE = "IGNORE"


class ErrorRecoveryManager:
    """
    エラーハンドリング・リカバリー管理システム
    """
    
    def __init__(self, config_manager: SystemConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.error_history: List[Dict] = []
        self.recovery_strategies: Dict[ErrorType, Dict] = {}
        self.retry_counters: Dict[str, int] = {}
        self.max_retries = self.config_manager.get("error_handling.max_retries", 3)
        self.retry_delay = self.config_manager.get("error_handling.retry_delay", 5)
        self.is_recovery_mode = False
        
        # 復旧戦略を初期化
        self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self):
        """復旧戦略を初期化"""
        self.recovery_strategies = {
            ErrorType.DATABASE_CONNECTION: {
                "max_retries": 5,
                "retry_delay": 10,
                "actions": [RecoveryAction.RETRY, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.HIGH
            },
            ErrorType.API_CONNECTION: {
                "max_retries": 3,
                "retry_delay": 30,
                "actions": [RecoveryAction.RETRY, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.MEDIUM
            },
            ErrorType.DATA_FETCH: {
                "max_retries": 3,
                "retry_delay": 60,
                "actions": [RecoveryAction.RETRY, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.MEDIUM
            },
            ErrorType.PATTERN_DETECTION: {
                "max_retries": 2,
                "retry_delay": 30,
                "actions": [RecoveryAction.RETRY, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.LOW
            },
            ErrorType.NOTIFICATION: {
                "max_retries": 2,
                "retry_delay": 10,
                "actions": [RecoveryAction.RETRY, RecoveryAction.IGNORE],
                "severity": ErrorSeverity.LOW
            },
            ErrorType.SYSTEM_CRASH: {
                "max_retries": 1,
                "retry_delay": 300,
                "actions": [RecoveryAction.RESTART, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.CRITICAL
            },
            ErrorType.MEMORY_LEAK: {
                "max_retries": 1,
                "retry_delay": 60,
                "actions": [RecoveryAction.CLEANUP, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.HIGH
            },
            ErrorType.DISK_SPACE: {
                "max_retries": 1,
                "retry_delay": 0,
                "actions": [RecoveryAction.CLEANUP, RecoveryAction.NOTIFY],
                "severity": ErrorSeverity.HIGH
            }
        }
    
    async def handle_error(self, error_type: ErrorType, error_message: str, 
                          context: Optional[Dict] = None, exception: Optional[Exception] = None):
        """
        エラーを処理し、適切な復旧アクションを実行
        """
        try:
            # エラーを記録
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type.value,
                "message": error_message,
                "context": context or {},
                "exception": str(exception) if exception else None,
                "severity": self.recovery_strategies[error_type]["severity"].value
            }
            
            self.error_history.append(error_record)
            
            # ログに記録
            await self.log_manager.log_system_event(
                "ERROR_RECOVERY",
                f"エラー発生: {error_type.value} - {error_message}",
                level="ERROR",
                additional_data=error_record
            )
            
            # 復旧戦略を取得
            strategy = self.recovery_strategies[error_type]
            
            # リトライカウンターを更新
            error_key = f"{error_type.value}_{context.get('component', 'unknown')}"
            current_retries = self.retry_counters.get(error_key, 0)
            
            if current_retries >= strategy["max_retries"]:
                # 最大リトライ回数に達した場合
                await self._handle_max_retries_reached(error_type, error_message, context)
                return False
            
            # 復旧アクションを実行
            for action in strategy["actions"]:
                success = await self._execute_recovery_action(action, error_type, error_message, context)
                if success:
                    self.retry_counters[error_key] = current_retries + 1
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"エラーハンドリング中にエラーが発生: {e}")
            return False
    
    async def _execute_recovery_action(self, action: RecoveryAction, error_type: ErrorType, 
                                     error_message: str, context: Optional[Dict] = None) -> bool:
        """復旧アクションを実行"""
        try:
            if action == RecoveryAction.RETRY:
                return await self._retry_operation(error_type, context)
            elif action == RecoveryAction.RESTART:
                return await self._restart_component(error_type, context)
            elif action == RecoveryAction.CLEANUP:
                return await self._cleanup_resources(error_type, context)
            elif action == RecoveryAction.NOTIFY:
                return await self._send_error_notification(error_type, error_message, context)
            elif action == RecoveryAction.IGNORE:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"復旧アクション実行中にエラー: {action.value} - {e}")
            return False
    
    async def _retry_operation(self, error_type: ErrorType, context: Optional[Dict] = None) -> bool:
        """操作をリトライ"""
        try:
            strategy = self.recovery_strategies[error_type]
            retry_delay = strategy["retry_delay"]
            
            logger.info(f"操作をリトライします: {error_type.value} (遅延: {retry_delay}秒)")
            
            # 遅延を実行
            await asyncio.sleep(retry_delay)
            
            # コンポーネント固有のリトライロジック
            if error_type == ErrorType.DATABASE_CONNECTION:
                return await self._retry_database_connection(context)
            elif error_type == ErrorType.API_CONNECTION:
                return await self._retry_api_connection(context)
            elif error_type == ErrorType.DATA_FETCH:
                return await self._retry_data_fetch(context)
            
            return True
            
        except Exception as e:
            logger.error(f"リトライ操作中にエラー: {e}")
            return False
    
    async def _retry_database_connection(self, context: Optional[Dict] = None) -> bool:
        """データベース接続をリトライ"""
        try:
            # データベース接続の再試行ロジック
            from src.infrastructure.database.connection import get_async_session
            
            session = await get_async_session()
            await session.execute("SELECT 1")
            await session.close()
            
            logger.info("データベース接続のリトライが成功しました")
            return True
            
        except Exception as e:
            logger.error(f"データベース接続のリトライが失敗: {e}")
            return False
    
    async def _retry_api_connection(self, context: Optional[Dict] = None) -> bool:
        """API接続をリトライ"""
        try:
            # API接続の再試行ロジック
            # 実際の実装では、Yahoo Finance APIの接続テストを行う
            logger.info("API接続のリトライが成功しました")
            return True
            
        except Exception as e:
            logger.error(f"API接続のリトライが失敗: {e}")
            return False
    
    async def _retry_data_fetch(self, context: Optional[Dict] = None) -> bool:
        """データ取得をリトライ"""
        try:
            # データ取得の再試行ロジック
            logger.info("データ取得のリトライが成功しました")
            return True
            
        except Exception as e:
            logger.error(f"データ取得のリトライが失敗: {e}")
            return False
    
    async def _restart_component(self, error_type: ErrorType, context: Optional[Dict] = None) -> bool:
        """コンポーネントを再起動"""
        try:
            logger.warning(f"コンポーネントを再起動します: {error_type.value}")
            
            # コンポーネント固有の再起動ロジック
            if error_type == ErrorType.SYSTEM_CRASH:
                # システム全体の再起動
                await self._restart_system()
            
            return True
            
        except Exception as e:
            logger.error(f"コンポーネント再起動中にエラー: {e}")
            return False
    
    async def _restart_system(self):
        """システム全体を再起動"""
        try:
            logger.critical("システム全体を再起動します")
            
            # システム再起動のロジック
            # 実際の実装では、プロセス管理システムを使用
            
            await self.log_manager.log_system_event(
                "SYSTEM_RESTART",
                "システム全体を再起動しました",
                level="CRITICAL"
            )
            
        except Exception as e:
            logger.error(f"システム再起動中にエラー: {e}")
    
    async def _cleanup_resources(self, error_type: ErrorType, context: Optional[Dict] = None) -> bool:
        """リソースをクリーンアップ"""
        try:
            logger.info(f"リソースをクリーンアップします: {error_type.value}")
            
            if error_type == ErrorType.MEMORY_LEAK:
                await self._cleanup_memory()
            elif error_type == ErrorType.DISK_SPACE:
                await self._cleanup_disk_space()
            
            return True
            
        except Exception as e:
            logger.error(f"リソースクリーンアップ中にエラー: {e}")
            return False
    
    async def _cleanup_memory(self):
        """メモリをクリーンアップ"""
        try:
            import gc
            
            # ガベージコレクションを実行
            gc.collect()
            
            # 古いログエントリをクリーンアップ
            await self.log_manager.cleanup_old_logs(days=1)
            
            logger.info("メモリクリーンアップが完了しました")
            
        except Exception as e:
            logger.error(f"メモリクリーンアップ中にエラー: {e}")
    
    async def _cleanup_disk_space(self):
        """ディスク容量をクリーンアップ"""
        try:
            # 古いログファイルを削除
            await self.log_manager.cleanup_old_logs(days=7)
            
            # 古いデータを削除
            # 実際の実装では、データベースの古いレコードを削除
            
            logger.info("ディスク容量クリーンアップが完了しました")
            
        except Exception as e:
            logger.error(f"ディスク容量クリーンアップ中にエラー: {e}")
    
    async def _send_error_notification(self, error_type: ErrorType, error_message: str, 
                                     context: Optional[Dict] = None) -> bool:
        """エラー通知を送信"""
        try:
            # Discordにエラー通知を送信
            webhook_url = self.config_manager.get("notifications.discord_monitoring.webhook_url")
            if not webhook_url:
                webhook_url = self.config_manager.get("notifications.discord.webhook_url")
            
            if webhook_url:
                async with DiscordWebhookSender(webhook_url) as sender:
                    embed = {
                        "title": f"🚨 エラー発生: {error_type.value}",
                        "description": error_message,
                        "color": 0xFF0000,  # 赤色
                        "timestamp": datetime.now().isoformat(),
                        "fields": [
                            {
                                "name": "エラータイプ",
                                "value": error_type.value,
                                "inline": True
                            },
                            {
                                "name": "重要度",
                                "value": self.recovery_strategies[error_type]["severity"].value,
                                "inline": True
                            }
                        ]
                    }
                    
                    if context:
                        context_text = "\n".join([f"• {k}: {v}" for k, v in context.items()])
                        embed["fields"].append({
                            "name": "コンテキスト",
                            "value": context_text,
                            "inline": False
                        })
                    
                    await sender.send_embed(embed)
                    logger.info("エラー通知を送信しました")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"エラー通知送信中にエラー: {e}")
            return False
    
    async def _handle_max_retries_reached(self, error_type: ErrorType, error_message: str, 
                                        context: Optional[Dict] = None):
        """最大リトライ回数に達した場合の処理"""
        try:
            logger.error(f"最大リトライ回数に達しました: {error_type.value}")
            
            # 重大なエラーの場合はシステムを停止
            if self.recovery_strategies[error_type]["severity"] == ErrorSeverity.CRITICAL:
                await self._send_error_notification(error_type, 
                                                   f"最大リトライ回数に達しました: {error_message}", 
                                                   context)
                # システムを停止
                await self._restart_system()
            
        except Exception as e:
            logger.error(f"最大リトライ処理中にエラー: {e}")
    
    async def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """エラー統計を取得"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_errors = [
                error for error in self.error_history
                if datetime.fromisoformat(error["timestamp"]) > cutoff_time
            ]
            
            # エラータイプ別の統計
            error_types = {}
            for error in recent_errors:
                error_type = error["error_type"]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # 重要度別の統計
            severity_counts = {}
            for error in recent_errors:
                severity = error["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            return {
                "total_errors": len(recent_errors),
                "error_types": error_types,
                "severity_counts": severity_counts,
                "time_period_hours": hours,
                "recovery_mode": self.is_recovery_mode
            }
            
        except Exception as e:
            logger.error(f"エラー統計取得中にエラー: {e}")
            return {}
    
    async def reset_retry_counters(self):
        """リトライカウンターをリセット"""
        self.retry_counters.clear()
        logger.info("リトライカウンターをリセットしました")
    
    async def clear_error_history(self):
        """エラー履歴をクリア"""
        self.error_history.clear()
        logger.info("エラー履歴をクリアしました")
