"""
通知ルールエンジン

通知条件の判定とルール管理
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.domain.entities import EconomicEvent, AIReport


class NotificationRuleEngine:
    """
    通知ルールエンジン
    
    経済イベントの通知条件を判定し、ルールを管理する
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        self._rule_count = 0
        
        # デフォルトルール設定
        self.default_rules = {
            "importance_threshold": "medium",
            "countries_filter": [
                "japan", "united states", "euro zone", 
                "united kingdom", "australia", "canada"
            ],
            "categories_filter": [
                "inflation", "employment", "interest_rate", 
                "gdp", "trade"
            ],
            "forecast_change_threshold": 0.1,  # 10%
            "surprise_threshold": 0.2,  # 20%
            "cooldown_period": 3600,  # 1時間
            "max_notifications_per_hour": 10,
            "enable_ai_report_notifications": True,
            "ai_report_importance_threshold": "high",
        }
        
        # 通知履歴（簡易版）
        self._notification_history = {}

    def should_send_notification(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> bool:
        """
        通知送信の判定
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            
        Returns:
            bool: 通知送信すべきかどうか
        """
        try:
            self.logger.debug(
                f"通知判定: {event.event_id}, type: {notification_type}"
            )

            # 基本条件のチェック
            if not self._check_basic_conditions(event):
                return False

            # 通知タイプ別の判定
            if notification_type == "new_event":
                return self._should_send_new_event_notification(event)
            elif notification_type == "forecast_change":
                return self._should_send_forecast_change_notification(event)
            elif notification_type == "actual_announcement":
                return self._should_send_actual_announcement_notification(event)
            elif notification_type == "ai_report":
                return self._should_send_ai_report_notification(event)
            else:
                # 未知の通知タイプは送信
                return True

        except Exception as e:
            self.logger.error(f"通知判定エラー: {e}")
            return False

    def should_send_forecast_change_notification(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent,
        change_data: Dict[str, Any]
    ) -> bool:
        """
        予測値変更通知の判定
        
        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント
            change_data: 変更データ
            
        Returns:
            bool: 通知送信すべきかどうか
        """
        try:
            # 基本条件のチェック
            if not self._check_basic_conditions(new_event):
                return False

            # 変更率のチェック
            change_percentage = change_data.get("change_percentage", 0)
            threshold = self.default_rules["forecast_change_threshold"]
            
            if abs(change_percentage) < threshold:
                self.logger.debug(
                    f"変更率が閾値を下回る: {change_percentage:.2%} < {threshold:.2%}"
                )
                return False

            # 重要度のチェック
            if not self._check_importance_threshold(new_event):
                return False

            # クールダウンのチェック
            if not self._check_cooldown(new_event, "forecast_change"):
                return False

            return True

        except Exception as e:
            self.logger.error(f"予測値変更通知判定エラー: {e}")
            return False

    def should_send_actual_announcement_notification(
        self,
        event: EconomicEvent,
        surprise_data: Dict[str, Any]
    ) -> bool:
        """
        実際値発表通知の判定
        
        Args:
            event: 経済イベント
            surprise_data: サプライズデータ
            
        Returns:
            bool: 通知送信すべきかどうか
        """
        try:
            # 基本条件のチェック
            if not self._check_basic_conditions(event):
                return False

            # サプライズの大きさチェック
            surprise_percentage = surprise_data.get("surprise_percentage", 0)
            threshold = self.default_rules["surprise_threshold"]
            
            if abs(surprise_percentage) < threshold:
                self.logger.debug(
                    f"サプライズが閾値を下回る: {surprise_percentage:.2%} < {threshold:.2%}"
                )
                return False

            # 重要度のチェック
            if not self._check_importance_threshold(event):
                return False

            # クールダウンのチェック
            if not self._check_cooldown(event, "actual_announcement"):
                return False

            return True

        except Exception as e:
            self.logger.error(f"実際値発表通知判定エラー: {e}")
            return False

    def should_send_ai_report_notification(
        self,
        event: EconomicEvent,
        ai_report: AIReport
    ) -> bool:
        """
        AIレポート通知の判定
        
        Args:
            event: 経済イベント
            ai_report: AIレポート
            
        Returns:
            bool: 通知送信すべきかどうか
        """
        try:
            # AIレポート通知が有効かチェック
            if not self.default_rules["enable_ai_report_notifications"]:
                return False

            # 基本条件のチェック
            if not self._check_basic_conditions(event):
                return False

            # 重要度のチェック（AIレポートは高重要度のみ）
            ai_threshold = self.default_rules["ai_report_importance_threshold"]
            if not self._check_importance_threshold(event, ai_threshold):
                return False

            # 信頼度のチェック
            if ai_report.confidence_score and ai_report.confidence_score < 0.7:
                self.logger.debug(
                    f"AIレポート信頼度が低い: {ai_report.confidence_score:.2%}"
                )
                return False

            # クールダウンのチェック
            if not self._check_cooldown(event, "ai_report"):
                return False

            return True

        except Exception as e:
            self.logger.error(f"AIレポート通知判定エラー: {e}")
            return False

    def _check_basic_conditions(self, event: EconomicEvent) -> bool:
        """
        基本条件のチェック
        
        Args:
            event: 経済イベント
            
        Returns:
            bool: 基本条件を満たすかどうか
        """
        # 国フィルター
        if event.country.lower() not in [
            country.lower() for country in self.default_rules["countries_filter"]
        ]:
            self.logger.debug(f"対象外の国: {event.country}")
            return False

        # 重要度フィルター
        if not self._check_importance_threshold(event):
            return False

        # カテゴリフィルター（イベント名から推定）
        if not self._check_category_filter(event):
            return False

        return True

    def _check_importance_threshold(
        self, 
        event: EconomicEvent, 
        threshold: str = None
    ) -> bool:
        """
        重要度閾値のチェック
        
        Args:
            event: 経済イベント
            threshold: 閾値（デフォルトは設定値）
            
        Returns:
            bool: 閾値を満たすかどうか
        """
        if threshold is None:
            threshold = self.default_rules["importance_threshold"]

        importance_levels = {
            "low": 1,
            "medium": 2,
            "high": 3
        }

        event_level = importance_levels.get(event.importance.value.lower(), 0)
        threshold_level = importance_levels.get(threshold.lower(), 0)

        if event_level < threshold_level:
            self.logger.debug(
                f"重要度が閾値を下回る: {event.importance} < {threshold}"
            )
            return False

        return True

    def _check_category_filter(self, event: EconomicEvent) -> bool:
        """
        カテゴリフィルターのチェック
        
        Args:
            event: 経済イベント
            
        Returns:
            bool: カテゴリフィルターを満たすかどうか
        """
        event_name_lower = event.event_name.lower()
        
        # カテゴリキーワードのチェック
        for category in self.default_rules["categories_filter"]:
            if category.lower() in event_name_lower:
                return True

        # 特定のイベント名のチェック
        important_events = [
            "cpi", "inflation", "employment", "gdp", "interest rate",
            "fed", "boj", "ecb", "boe", "payroll", "trade balance"
        ]
        
        for keyword in important_events:
            if keyword in event_name_lower:
                return True

        self.logger.debug(f"対象外のカテゴリ: {event.event_name}")
        return False

    def _check_cooldown(
        self, 
        event: EconomicEvent, 
        notification_type: str
    ) -> bool:
        """
        クールダウンのチェック
        
        Args:
            event: 経済イベント
            notification_type: 通知タイプ
            
        Returns:
            bool: クールダウン期間を過ぎているかどうか
        """
        cooldown_period = self.default_rules["cooldown_period"]
        current_time = datetime.utcnow()
        
        # イベントIDと通知タイプの組み合わせでキーを作成
        key = f"{event.event_id}_{notification_type}"
        
        if key in self._notification_history:
            last_notification = self._notification_history[key]
            time_diff = (current_time - last_notification).total_seconds()
            
            if time_diff < cooldown_period:
                self.logger.debug(
                    f"クールダウン期間中: {time_diff:.0f}s < {cooldown_period}s"
                )
                return False

        return True

    def _should_send_new_event_notification(self, event: EconomicEvent) -> bool:
        """新規イベント通知の判定"""
        # 新規イベントは基本条件を満たしていれば送信
        return self._check_basic_conditions(event)

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
        key = f"{event.event_id}_{notification_type}"
        self._notification_history[key] = datetime.utcnow()
        self._rule_count += 1

    def update_rules(self, new_rules: Dict[str, Any]) -> None:
        """
        ルールの更新
        
        Args:
            new_rules: 新しいルール設定
        """
        self.default_rules.update(new_rules)
        self.logger.info("通知ルールを更新しました")

    def get_rules(self) -> Dict[str, Any]:
        """
        現在のルールを取得
        
        Returns:
            Dict[str, Any]: ルール設定
        """
        return self.default_rules.copy()

    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            "engine": "NotificationRuleEngine",
            "total_notifications": self._rule_count,
            "active_rules": len(self.default_rules),
            "notification_history_size": len(self._notification_history),
            "rules": self.get_rules(),
        }

    def health_check(self) -> bool:
        """
        ヘルスチェック
        
        Returns:
            bool: エンジンが正常かどうか
        """
        try:
            # 基本的なルール設定の確認
            required_rules = [
                "importance_threshold", "countries_filter", 
                "categories_filter", "cooldown_period"
            ]
            
            for rule in required_rules:
                if rule not in self.default_rules:
                    self.logger.error(f"必須ルールが不足: {rule}")
                    return False

            # ルール値の妥当性確認
            if self.default_rules["cooldown_period"] < 0:
                self.logger.error("クールダウン期間が負の値です")
                return False

            return True

        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False

    def clear_history(self) -> None:
        """通知履歴のクリア"""
        self._notification_history.clear()
        self.logger.info("通知履歴をクリアしました")

    def get_notification_summary(self) -> Dict[str, Any]:
        """
        通知サマリーを取得
        
        Returns:
            Dict[str, Any]: 通知サマリー
        """
        return {
            "total_notifications": self._rule_count,
            "recent_notifications": len(self._notification_history),
            "rules_active": len(self.default_rules),
            "last_activity": max(self._notification_history.values()) if self._notification_history else None,
        }
