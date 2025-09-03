"""
基底スケジューラー

スケジューラーの基底クラスと共通機能
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

from .scheduler_config import SchedulerConfig


class BaseScheduler(ABC):
    """
    基底スケジューラー
    
    スケジューラーの基底クラスと共通機能
    """

    def __init__(self, config: SchedulerConfig):
        """
        初期化
        
        Args:
            config: スケジューラー設定
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 実行状態
        self._is_running = False
        self._last_execution = None
        self._next_execution = None
        self._execution_count = 0
        self._error_count = 0
        self._last_error = None
        
        # 統計情報
        self._total_execution_time = 0.0
        self._successful_executions = 0
        self._failed_executions = 0

    @abstractmethod
    async def execute_task(self) -> Dict[str, Any]:
        """
        タスク実行（抽象メソッド）
        
        Returns:
            Dict[str, Any]: 実行結果
        """
        pass

    async def execute(self) -> bool:
        """
        スケジューラー実行
        
        Returns:
            bool: 実行成功フラグ
        """
        try:
            if not self.config.enabled:
                self.logger.info(f"スケジューラー {self.config.name} は無効です")
                return False
            
            self.logger.info(f"スケジューラー {self.config.name} 実行開始")
            start_time = datetime.utcnow()
            
            # タイムアウト設定
            if self.config.timeout > 0:
                try:
                    result = await asyncio.wait_for(
                        self.execute_task(),
                        timeout=self.config.timeout
                    )
                except asyncio.TimeoutError:
                    self.logger.error(f"スケジューラー {self.config.name} がタイムアウトしました")
                    await self._handle_error("タイムアウト")
                    return False
            else:
                result = await self.execute_task()
            
            # 実行結果の処理
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            success = result.get("success", False)
            
            if success:
                await self._handle_success(execution_time, result)
            else:
                await self._handle_error(result.get("error", "不明なエラー"))
            
            # 統計情報の更新
            self._update_statistics(execution_time, success)
            
            return success

        except Exception as e:
            self.logger.error(f"スケジューラー {self.config.name} 実行エラー: {e}")
            await self._handle_error(str(e))
            return False

    async def _handle_success(self, execution_time: float, result: Dict[str, Any]):
        """成功時の処理"""
        self._last_execution = datetime.utcnow()
        self._execution_count += 1
        self._error_count = 0  # エラーカウントをリセット
        
        self.logger.info(
            f"スケジューラー {self.config.name} 実行成功: "
            f"{execution_time:.2f}秒"
        )
        
        # 詳細ログ
        if self.config.log_level == "DEBUG":
            self.logger.debug(f"実行結果: {result}")

    async def _handle_error(self, error_message: str):
        """エラー時の処理"""
        self._last_execution = datetime.utcnow()
        self._last_error = error_message
        self._error_count += 1
        
        self.logger.error(
            f"スケジューラー {self.config.name} 実行エラー: {error_message}"
        )
        
        # エラー通知
        if (self.config.error_notification_enabled and 
            self._error_count >= self.config.error_threshold):
            await self._send_error_notification(error_message)

    async def _send_error_notification(self, error_message: str):
        """エラー通知の送信"""
        try:
            # ここでDiscord通知などを実装
            notification_data = {
                "type": "scheduler_error",
                "scheduler_name": self.config.name,
                "error_message": error_message,
                "error_count": self._error_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.warning(f"エラー通知: {notification_data}")
            
        except Exception as e:
            self.logger.error(f"エラー通知送信エラー: {e}")

    def _update_statistics(self, execution_time: float, success: bool):
        """統計情報の更新"""
        self._total_execution_time += execution_time
        
        if success:
            self._successful_executions += 1
        else:
            self._failed_executions += 1

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_executions = self._successful_executions + self._failed_executions
        avg_execution_time = (
            self._total_execution_time / total_executions
            if total_executions > 0 else 0
        )
        
        success_rate = (
            self._successful_executions / total_executions
            if total_executions > 0 else 0
        )
        
        return {
            "scheduler_name": self.config.name,
            "enabled": self.config.enabled,
            "is_running": self._is_running,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None,
            "next_execution": self._next_execution.isoformat() if self._next_execution else None,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "total_executions": total_executions,
            "successful_executions": self._successful_executions,
            "failed_executions": self._failed_executions,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "total_execution_time": self._total_execution_time
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 設定の検証
            if not self.config.validate():
                self.logger.error("スケジューラー設定が無効です")
                return False
            
            # エラーカウントのチェック
            if self._error_count >= self.config.error_threshold:
                self.logger.warning(f"エラーカウントが閾値を超えています: {self._error_count}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False

    def set_next_execution(self, next_execution: datetime):
        """次回実行時刻を設定"""
        self._next_execution = next_execution

    def is_due(self) -> bool:
        """実行時刻かどうかを判定"""
        if not self._next_execution:
            return True
        
        return datetime.utcnow() >= self._next_execution

    def reset_error_count(self):
        """エラーカウントをリセット"""
        self._error_count = 0
        self._last_error = None
