"""
エラーハンドリングシステム

責任:
- エラーの分類と管理
- エラーログの記録
- 自動復旧機能
- アラート通知
"""

import asyncio
import traceback
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class ErrorSeverity(Enum):
    """エラー深刻度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """エラーカテゴリ"""
    DATABASE = "database"
    NETWORK = "network"
    DATA_PROCESSING = "data_processing"
    API = "api"
    SYSTEM = "system"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """エラー情報"""
    timestamp: datetime
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    stack_trace: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class RecoveryAction:
    """復旧アクション"""
    name: str
    description: str
    action: Callable
    conditions: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    retry_count: int = 0


class ErrorHandler:
    """エラーハンドリングシステム"""
    
    def __init__(self):
        self.errors: List[ErrorInfo] = []
        self.recovery_actions: Dict[ErrorCategory, List[RecoveryAction]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.alert_thresholds: Dict[ErrorSeverity, int] = {
            ErrorSeverity.LOW: 10,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.CRITICAL: 1
        }
        self.auto_recovery_enabled = True
        self.max_errors_per_hour = 100
        
        # デフォルトの復旧アクションを設定
        self._setup_default_recovery_actions()
    
    def _setup_default_recovery_actions(self):
        """デフォルトの復旧アクションを設定"""
        
        # データベースエラーの復旧
        self.add_recovery_action(
            ErrorCategory.DATABASE,
            RecoveryAction(
                name="データベース再接続",
                description="データベース接続を再確立",
                action=self._reconnect_database,
                conditions=["connection", "timeout", "deadlock"],
                timeout_seconds=60
            )
        )
        
        # ネットワークエラーの復旧
        self.add_recovery_action(
            ErrorCategory.NETWORK,
            RecoveryAction(
                name="ネットワーク再試行",
                description="ネットワーク接続を再試行",
                action=self._retry_network_connection,
                conditions=["timeout", "connection", "dns"],
                timeout_seconds=30
            )
        )
        
        # メモリエラーの復旧
        self.add_recovery_action(
            ErrorCategory.MEMORY,
            RecoveryAction(
                name="メモリ最適化",
                description="メモリ使用量を最適化",
                action=self._optimize_memory,
                conditions=["out_of_memory", "memory_leak"],
                timeout_seconds=45
            )
        )
        
        # APIエラーの復旧
        self.add_recovery_action(
            ErrorCategory.API,
            RecoveryAction(
                name="API再試行",
                description="API呼び出しを再試行",
                action=self._retry_api_call,
                conditions=["rate_limit", "timeout", "server_error"],
                timeout_seconds=60
            )
        )
    
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Dict[str, Any] = None,
        auto_recover: bool = True
    ) -> ErrorInfo:
        """エラーを処理"""
        
        # エラー情報を作成
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            category=category,
            severity=severity,
            stack_trace=traceback.format_exc(),
            context=context or {},
            max_retries=self._get_max_retries_for_category(category)
        )
        
        # エラーを記録
        self.errors.append(error_info)
        self.error_counts[error_info.error_type] += 1
        
        # エラーログを記録
        self._log_error(error_info)
        
        # アラートチェック
        self._check_alerts(error_info)
        
        # 自動復旧を試行
        if auto_recover and self.auto_recovery_enabled:
            asyncio.create_task(self._attempt_recovery(error_info))
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """エラーをログに記録"""
        log_message = (
            f"エラー発生: {error_info.error_type} - {error_info.error_message} "
            f"(カテゴリ: {error_info.category.value}, 深刻度: {error_info.severity.value})"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # スタックトレースを記録
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            logger.debug(f"スタックトレース: {error_info.stack_trace}")
    
    def _check_alerts(self, error_info: ErrorInfo):
        """アラートをチェック"""
        threshold = self.alert_thresholds.get(error_info.severity, 1)
        
        # 過去1時間のエラー数をチェック
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [
            e for e in self.errors 
            if e.timestamp >= one_hour_ago and e.severity == error_info.severity
        ]
        
        if len(recent_errors) >= threshold:
            self._send_alert(error_info, recent_errors)
    
    def _send_alert(self, error_info: ErrorInfo, recent_errors: List[ErrorInfo]):
        """アラートを送信"""
        alert_message = (
            f"🚨 エラーアラート: {error_info.severity.value.upper()} "
            f"({len(recent_errors)}件のエラーが過去1時間で発生)"
        )
        
        logger.critical(alert_message)
        
        # ここでDiscord通知やメール通知を実装可能
        # self._send_discord_alert(alert_message, error_info)
        # self._send_email_alert(alert_message, error_info)
    
    async def _attempt_recovery(self, error_info: ErrorInfo):
        """自動復旧を試行"""
        recovery_actions = self.recovery_actions.get(error_info.category, [])
        
        for action in recovery_actions:
            if self._should_attempt_recovery(action, error_info):
                try:
                    logger.info(f"復旧アクション実行: {action.name}")
                    
                    # タイムアウト付きで復旧アクションを実行
                    await asyncio.wait_for(
                        self._execute_recovery_action(action, error_info),
                        timeout=action.timeout_seconds
                    )
                    
                    # 復旧成功
                    error_info.resolved = True
                    error_info.resolution_time = datetime.now()
                    logger.info(f"復旧成功: {action.name}")
                    break
                    
                except asyncio.TimeoutError:
                    logger.warning(f"復旧タイムアウト: {action.name}")
                    action.retry_count += 1
                except Exception as e:
                    logger.error(f"復旧失敗: {action.name} - {e}")
                    action.retry_count += 1
    
    def _should_attempt_recovery(self, action: RecoveryAction, error_info: ErrorInfo) -> bool:
        """復旧を試行すべきかチェック"""
        # 最大リトライ回数をチェック
        if action.retry_count >= 3:
            return False
        
        # エラーメッセージに条件が含まれているかチェック
        error_message_lower = error_info.error_message.lower()
        return any(condition.lower() in error_message_lower for condition in action.conditions)
    
    async def _execute_recovery_action(self, action: RecoveryAction, error_info: ErrorInfo):
        """復旧アクションを実行"""
        if asyncio.iscoroutinefunction(action.action):
            await action.action(error_info)
        else:
            action.action(error_info)
    
    def add_recovery_action(self, category: ErrorCategory, action: RecoveryAction):
        """復旧アクションを追加"""
        self.recovery_actions[category].append(action)
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """エラー統計を取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff_time]
        
        # カテゴリ別統計
        category_stats = defaultdict(int)
        severity_stats = defaultdict(int)
        error_type_stats = defaultdict(int)
        
        for error in recent_errors:
            category_stats[error.category.value] += 1
            severity_stats[error.severity.value] += 1
            error_type_stats[error.error_type] += 1
        
        # 解決済みエラー数
        resolved_count = len([e for e in recent_errors if e.resolved])
        
        return {
            "total_errors": len(recent_errors),
            "resolved_errors": resolved_count,
            "resolution_rate": resolved_count / len(recent_errors) if recent_errors else 0,
            "category_distribution": dict(category_stats),
            "severity_distribution": dict(severity_stats),
            "error_type_distribution": dict(error_type_stats),
            "period_hours": hours
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorInfo]:
        """最近のエラーを取得"""
        return sorted(self.errors, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def clear_old_errors(self, days: int = 7):
        """古いエラーを削除"""
        cutoff_time = datetime.now() - timedelta(days=days)
        self.errors = [e for e in self.errors if e.timestamp >= cutoff_time]
        logger.info(f"{days}日より古いエラーを削除しました")
    
    def _get_max_retries_for_category(self, category: ErrorCategory) -> int:
        """カテゴリ別の最大リトライ回数を取得"""
        retry_config = {
            ErrorCategory.DATABASE: 3,
            ErrorCategory.NETWORK: 5,
            ErrorCategory.API: 3,
            ErrorCategory.MEMORY: 1,
            ErrorCategory.SYSTEM: 2,
            ErrorCategory.VALIDATION: 0,
            ErrorCategory.TIMEOUT: 3,
            ErrorCategory.UNKNOWN: 2
        }
        return retry_config.get(category, 2)
    
    # デフォルト復旧アクションの実装
    async def _reconnect_database(self, error_info: ErrorInfo):
        """データベース再接続"""
        logger.info("データベース再接続を試行中...")
        await asyncio.sleep(2)  # 実際の再接続処理をシミュレート
        logger.info("データベース再接続完了")
    
    async def _retry_network_connection(self, error_info: ErrorInfo):
        """ネットワーク接続再試行"""
        logger.info("ネットワーク接続再試行中...")
        await asyncio.sleep(1)  # 実際の再試行処理をシミュレート
        logger.info("ネットワーク接続再試行完了")
    
    async def _optimize_memory(self, error_info: ErrorInfo):
        """メモリ最適化"""
        logger.info("メモリ最適化実行中...")
        import gc
        gc.collect()
        await asyncio.sleep(1)
        logger.info("メモリ最適化完了")
    
    async def _retry_api_call(self, error_info: ErrorInfo):
        """API呼び出し再試行"""
        logger.info("API呼び出し再試行中...")
        await asyncio.sleep(2)  # 実際のAPI再試行処理をシミュレート
        logger.info("API呼び出し再試行完了")
    
    def generate_error_report(self) -> Dict[str, Any]:
        """エラーレポートを生成"""
        stats = self.get_error_statistics()
        recent_errors = self.get_recent_errors(5)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "recent_errors": [
                {
                    "timestamp": error.timestamp.isoformat(),
                    "type": error.error_type,
                    "message": error.error_message,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "resolved": error.resolved
                }
                for error in recent_errors
            ],
            "recovery_actions": {
                category.value: len(actions)
                for category, actions in self.recovery_actions.items()
            }
        }
