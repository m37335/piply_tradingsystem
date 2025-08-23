"""
通知クールダウンマネージャー

通知の頻度制御とクールダウン管理
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.domain.entities import EconomicEvent


class NotificationCooldownManager:
    """
    通知クールダウンマネージャー
    
    通知の頻度制御とクールダウン期間の管理を行う
    """

    def __init__(self, default_cooldown: int = 3600):
        """
        初期化
        
        Args:
            default_cooldown: デフォルトクールダウン期間（秒）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.default_cooldown = default_cooldown
        
        # 通知履歴: {key: (last_notification_time, notification_count)}
        self._notification_history = {}
        
        # クールダウン設定: {notification_type: cooldown_seconds}
        self._cooldown_settings = {
            "new_event": 1800,  # 30分
            "forecast_change": 3600,  # 1時間
            "actual_announcement": 7200,  # 2時間
            "ai_report": 3600,  # 1時間
            "error": 300,  # 5分
            "system_status": 1800,  # 30分
        }
        
        # 統計情報
        self._total_notifications = 0
        self._blocked_notifications = 0

    def can_send_notification(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> bool:
        """
        通知送信可能かどうかを判定
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            
        Returns:
            bool: 通知送信可能かどうか
        """
        try:
            # クールダウン期間を取得
            cooldown_period = self._get_cooldown_period(notification_type)
            
            # 通知キーを生成
            notification_key = self._generate_notification_key(event, notification_type)
            
            # 現在時刻
            current_time = time.time()
            
            # 履歴をチェック
            if notification_key in self._notification_history:
                last_time, count = self._notification_history[notification_key]
                time_since_last = current_time - last_time
                
                if time_since_last < cooldown_period:
                    self._blocked_notifications += 1
                    self.logger.debug(
                        f"クールダウン中: {event.event_id}, "
                        f"type: {notification_type}, "
                        f"残り時間: {cooldown_period - time_since_last:.0f}秒"
                    )
                    return False
            
            return True

        except Exception as e:
            self.logger.error(f"クールダウン判定エラー: {e}")
            return True  # エラー時は送信許可

    def record_notification(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> None:
        """
        通知記録
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
        """
        try:
            notification_key = self._generate_notification_key(event, notification_type)
            current_time = time.time()
            
            if notification_key in self._notification_history:
                last_time, count = self._notification_history[notification_key]
                self._notification_history[notification_key] = (current_time, count + 1)
            else:
                self._notification_history[notification_key] = (current_time, 1)
            
            self._total_notifications += 1
            
            self.logger.debug(
                f"通知記録: {event.event_id}, type: {notification_type}"
            )

        except Exception as e:
            self.logger.error(f"通知記録エラー: {e}")

    def get_cooldown_status(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> Dict[str, Any]:
        """
        クールダウン状態を取得
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            
        Returns:
            Dict[str, Any]: クールダウン状態
        """
        try:
            notification_key = self._generate_notification_key(event, notification_type)
            cooldown_period = self._get_cooldown_period(notification_type)
            current_time = time.time()
            
            if notification_key in self._notification_history:
                last_time, count = self._notification_history[notification_key]
                time_since_last = current_time - last_time
                remaining_time = max(0, cooldown_period - time_since_last)
                
                return {
                    "can_send": remaining_time <= 0,
                    "remaining_time": remaining_time,
                    "last_notification": datetime.fromtimestamp(last_time).isoformat(),
                    "notification_count": count,
                    "cooldown_period": cooldown_period,
                }
            else:
                return {
                    "can_send": True,
                    "remaining_time": 0,
                    "last_notification": None,
                    "notification_count": 0,
                    "cooldown_period": cooldown_period,
                }

        except Exception as e:
            self.logger.error(f"クールダウン状態取得エラー: {e}")
            return {
                "can_send": True,
                "remaining_time": 0,
                "last_notification": None,
                "notification_count": 0,
                "cooldown_period": cooldown_period,
            }

    def set_cooldown_period(
        self, 
        notification_type: str, 
        cooldown_seconds: int
    ) -> None:
        """
        クールダウン期間を設定
        
        Args:
            notification_type: 通知タイプ
            cooldown_seconds: クールダウン期間（秒）
        """
        if cooldown_seconds < 0:
            self.logger.warning(f"無効なクールダウン期間: {cooldown_seconds}")
            return
        
        self._cooldown_settings[notification_type] = cooldown_seconds
        self.logger.info(
            f"クールダウン期間を設定: {notification_type} = {cooldown_seconds}秒"
        )

    def get_cooldown_period(self, notification_type: str) -> int:
        """
        クールダウン期間を取得
        
        Args:
            notification_type: 通知タイプ
            
        Returns:
            int: クールダウン期間（秒）
        """
        return self._cooldown_settings.get(notification_type, self.default_cooldown)

    def clear_cooldown(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> None:
        """
        特定の通知のクールダウンをクリア
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
        """
        try:
            notification_key = self._generate_notification_key(event, notification_type)
            
            if notification_key in self._notification_history:
                del self._notification_history[notification_key]
                self.logger.info(
                    f"クールダウンクリア: {event.event_id}, type: {notification_type}"
                )

        except Exception as e:
            self.logger.error(f"クールダウンクリアエラー: {e}")

    def clear_all_cooldowns(self) -> None:
        """全てのクールダウンをクリア"""
        self._notification_history.clear()
        self.logger.info("全てのクールダウンをクリアしました")

    def cleanup_expired_entries(self, max_age_hours: int = 24) -> int:
        """
        期限切れのエントリをクリーンアップ
        
        Args:
            max_age_hours: 最大保持時間（時間）
            
        Returns:
            int: 削除されたエントリ数
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            expired_keys = []
            
            for key, (last_time, count) in self._notification_history.items():
                if current_time - last_time > max_age_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._notification_history[key]
            
            if expired_keys:
                self.logger.info(f"{len(expired_keys)}件の期限切れエントリを削除しました")
            
            return len(expired_keys)

        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")
            return 0

    def get_notification_frequency(
        self, 
        event: EconomicEvent, 
        notification_type: str,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        通知頻度を取得
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            time_window_hours: 時間枠（時間）
            
        Returns:
            Dict[str, Any]: 通知頻度情報
        """
        try:
            current_time = time.time()
            time_window_seconds = time_window_hours * 3600
            notification_key = self._generate_notification_key(event, notification_type)
            
            if notification_key in self._notification_history:
                last_time, count = self._notification_history[notification_key]
                time_since_last = current_time - last_time
                
                # 時間枠内の通知回数を推定
                if time_since_last < time_window_seconds:
                    estimated_frequency = count / (time_since_last / 3600)  # 時間あたり
                else:
                    estimated_frequency = 0
                
                return {
                    "notification_count": count,
                    "last_notification": datetime.fromtimestamp(last_time).isoformat(),
                    "time_since_last": time_since_last,
                    "estimated_frequency_per_hour": estimated_frequency,
                    "time_window_hours": time_window_hours,
                }
            else:
                return {
                    "notification_count": 0,
                    "last_notification": None,
                    "time_since_last": None,
                    "estimated_frequency_per_hour": 0,
                    "time_window_hours": time_window_hours,
                }

        except Exception as e:
            self.logger.error(f"通知頻度取得エラー: {e}")
            return {
                "notification_count": 0,
                "last_notification": None,
                "time_since_last": None,
                "estimated_frequency_per_hour": 0,
                "time_window_hours": time_window_hours,
            }

    def _generate_notification_key(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> str:
        """
        通知キーを生成
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            
        Returns:
            str: 通知キー
        """
        return f"{event.event_id}_{notification_type}"

    def _get_cooldown_period(self, notification_type: str) -> int:
        """
        クールダウン期間を取得
        
        Args:
            notification_type: 通知タイプ
            
        Returns:
            int: クールダウン期間（秒）
        """
        return self._cooldown_settings.get(notification_type, self.default_cooldown)

    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            "manager": "NotificationCooldownManager",
            "total_notifications": self._total_notifications,
            "blocked_notifications": self._blocked_notifications,
            "active_cooldowns": len(self._notification_history),
            "cooldown_settings": self._cooldown_settings.copy(),
            "default_cooldown": self.default_cooldown,
        }

    def health_check(self) -> bool:
        """
        ヘルスチェック
        
        Returns:
            bool: マネージャーが正常かどうか
        """
        try:
            # 基本的な設定の確認
            if self.default_cooldown < 0:
                self.logger.error("デフォルトクールダウン期間が負の値です")
                return False
            
            # クールダウン設定の確認
            for notification_type, cooldown in self._cooldown_settings.items():
                if cooldown < 0:
                    self.logger.error(f"無効なクールダウン期間: {notification_type} = {cooldown}")
                    return False
            
            return True

        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False

    def get_cooldown_summary(self) -> Dict[str, Any]:
        """
        クールダウンサマリーを取得
        
        Returns:
            Dict[str, Any]: クールダウンサマリー
        """
        try:
            current_time = time.time()
            active_cooldowns = 0
            total_wait_time = 0
            
            for key, (last_time, count) in self._notification_history.items():
                # 最も長いクールダウン期間を推定
                notification_type = key.split("_", 1)[1] if "_" in key else "unknown"
                cooldown_period = self._get_cooldown_period(notification_type)
                time_since_last = current_time - last_time
                
                if time_since_last < cooldown_period:
                    active_cooldowns += 1
                    total_wait_time += cooldown_period - time_since_last
            
            return {
                "active_cooldowns": active_cooldowns,
                "total_wait_time": total_wait_time,
                "average_wait_time": total_wait_time / active_cooldowns if active_cooldowns > 0 else 0,
                "total_notifications": self._total_notifications,
                "blocked_notifications": self._blocked_notifications,
                "block_rate": self._blocked_notifications / max(1, self._total_notifications + self._blocked_notifications),
            }

        except Exception as e:
            self.logger.error(f"クールダウンサマリー取得エラー: {e}")
            return {
                "active_cooldowns": 0,
                "total_wait_time": 0,
                "average_wait_time": 0,
                "total_notifications": self._total_notifications,
                "blocked_notifications": self._blocked_notifications,
                "block_rate": 0,
            }
