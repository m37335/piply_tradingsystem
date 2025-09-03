"""
通知マネージャー統合

既存のnotification_manager.pyとの統合を管理するクラス
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.notification_pattern_analyzer import (
    NotificationPatternAnalyzer,
)
from src.infrastructure.messaging.templates import (
    Pattern1Template,
    Pattern2Template,
    Pattern3Template,
    Pattern4Template,
    Pattern6Template,
)


class NotificationManagerIntegration:
    """通知マネージャー統合クラス"""

    def __init__(self):
        self.analyzer = NotificationPatternAnalyzer()

        # テンプレートマッピング
        self.templates = {
            1: Pattern1Template(),
            2: Pattern2Template(),
            3: Pattern3Template(),
            4: Pattern4Template(),
            6: Pattern6Template(),
        }

        # 設定ファイルパス
        self.config_file = "notification_config.json"
        self.history_file = "notification_history.json"

        # 設定を読み込み
        self.config = self.load_config()
        self.notification_history = self.load_history()

        # ログ設定
        self.setup_logging()

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        default_config = {
            "enabled_patterns": [1, 2, 3, 4, 6],
            "currency_pairs": ["USD/JPY", "EUR/USD", "GBP/USD"],
            "notification_cooldown": 3600,
            "discord_webhook_url": "",
            "priority_settings": {
                "VERY_HIGH": {"enabled": True, "delay": 0},
                "HIGH": {"enabled": True, "delay": 0},
                "MEDIUM": {"enabled": True, "delay": 300},
                "LOW": {"enabled": False, "delay": 600},
            },
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # デフォルト設定とマージ
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                self.logger.error(f"設定ファイル読み込みエラー: {e}")
                return default_config
        else:
            # デフォルト設定を保存
            self.save_config(default_config)
            return default_config

    def save_config(self, config: Dict[str, Any]):
        """設定ファイルを保存"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")

    def load_history(self) -> Dict[str, Any]:
        """通知履歴を読み込み"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"履歴ファイル読み込みエラー: {e}")
                return {}
        return {}

    def save_history(self):
        """通知履歴を保存"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.notification_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"履歴ファイル保存エラー: {e}")

    def is_pattern_enabled(self, pattern_number: int) -> bool:
        """パターンが有効かチェック"""
        return pattern_number in self.config.get("enabled_patterns", [])

    def is_priority_enabled(self, priority: PatternPriority) -> bool:
        """優先度が有効かチェック"""
        priority_settings = self.config.get("priority_settings", {})
        priority_config = priority_settings.get(priority.name, {})
        return priority_config.get("enabled", True)

    def get_priority_delay(self, priority: PatternPriority) -> int:
        """優先度に基づく遅延時間を取得"""
        priority_settings = self.config.get("priority_settings", {})
        priority_config = priority_settings.get(priority.name, {})
        return priority_config.get("delay", 0)

    def is_in_cooldown(self, pattern_number: int, currency_pair: str) -> bool:
        """クールダウン期間中かチェック"""
        key = f"{pattern_number}_{currency_pair}"
        last_notification = self.notification_history.get(key)

        if not last_notification:
            return False

        cooldown = self.config.get("notification_cooldown", 3600)
        last_time = datetime.fromisoformat(last_notification)
        time_since_last = (datetime.now() - last_time).total_seconds()

        return time_since_last < cooldown

    def update_notification_history(self, pattern_number: int, currency_pair: str):
        """通知履歴を更新"""
        key = f"{pattern_number}_{currency_pair}"
        self.notification_history[key] = datetime.now().isoformat()
        self.save_history()

    async def process_detection_result(
        self, detection_result: Dict[str, Any], currency_pair: str
    ) -> bool:
        """
        検出結果を処理

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            通知が送信された場合はTrue
        """
        pattern_number = detection_result.get("pattern_number")
        priority = detection_result.get("priority", PatternPriority.LOW)

        # パターンが有効かチェック
        if not self.is_pattern_enabled(pattern_number):
            self.logger.info(f"パターン{pattern_number}は無効です")
            return False

        # 優先度が有効かチェック
        if not self.is_priority_enabled(priority):
            self.logger.info(f"優先度{priority}は無効です")
            return False

        # クールダウンチェック
        if self.is_in_cooldown(pattern_number, currency_pair):
            self.logger.info(f"パターン{pattern_number}はクールダウン中: {currency_pair}")
            return False

        # 遅延時間を取得
        delay = self.get_priority_delay(priority)

        # 遅延がある場合は待機
        if delay > 0:
            self.logger.info(f"通知を{delay}秒遅延: パターン{pattern_number}")
            await asyncio.sleep(delay)

        # 通知を送信
        success = await self.send_notification(detection_result, currency_pair)

        if success:
            self.update_notification_history(pattern_number, currency_pair)

        return success

    async def send_notification(
        self, detection_result: Dict[str, Any], currency_pair: str
    ) -> bool:
        """
        通知を送信

        Args:
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            送信成功時はTrue
        """
        try:
            pattern_number = detection_result.get("pattern_number")
            template = self.templates.get(pattern_number)

            if not template:
                self.logger.warning(f"テンプレートが見つかりません: パターン{pattern_number}")
                return False

            # Embed形式の通知を作成
            embed = template.create_embed(detection_result, currency_pair)

            # 既存のnotification_managerに送信
            success = await self.send_to_existing_manager(
                embed, detection_result, currency_pair
            )

            if success:
                self.logger.info(f"通知を送信しました: パターン{pattern_number} - {currency_pair}")

            return success

        except Exception as e:
            self.logger.error(f"通知送信エラー: {e}")
            return False

    async def send_to_existing_manager(
        self,
        embed: Dict[str, Any],
        detection_result: Dict[str, Any],
        currency_pair: str,
    ) -> bool:
        """
        既存のnotification_managerに送信

        Args:
            embed: Discord Embed
            detection_result: 検出結果
            currency_pair: 通貨ペア

        Returns:
            送信成功時はTrue
        """
        try:
            # 実際の実装では、ここで既存のnotification_managerを呼び出し
            # 現在はログ出力のみ
            self.logger.info(f"既存マネージャーに送信: {currency_pair}")
            self.logger.info(f"Embed: {embed['title']}")

            # 優先度に基づく処理
            priority = detection_result.get("priority", PatternPriority.LOW)
            if priority in [PatternPriority.HIGH, PatternPriority.VERY_HIGH]:
                self.logger.warning(f"高優先度通知: {priority} - {currency_pair}")

            return True

        except Exception as e:
            self.logger.error(f"既存マネージャー送信エラー: {e}")
            return False

    def get_integration_status(self) -> Dict[str, Any]:
        """統合ステータスを取得"""
        return {
            "config_loaded": bool(self.config),
            "enabled_patterns": self.config.get("enabled_patterns", []),
            "currency_pairs": self.config.get("currency_pairs", []),
            "notification_cooldown": self.config.get("notification_cooldown", 3600),
            "history_count": len(self.notification_history),
            "templates_available": len(self.templates),
            "last_update": datetime.now().isoformat(),
        }

    def update_config(self, new_config: Dict[str, Any]):
        """設定を更新"""
        self.config.update(new_config)
        self.save_config(self.config)
        self.logger.info("設定を更新しました")

    def reset_history(self):
        """通知履歴をリセット"""
        self.notification_history = {}
        self.save_history()
        self.logger.info("通知履歴をリセットしました")


# 統合テスト用の関数
async def test_integration():
    """統合テスト"""
    integration = NotificationManagerIntegration()

    # ステータスを表示
    status = integration.get_integration_status()
    print("統合ステータス:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # モック検出結果を作成
    mock_detection = {
        "pattern_number": 1,
        "pattern_name": "強力なトレンド転換シグナル",
        "priority": PatternPriority.HIGH,
        "confidence_score": 0.85,
        "notification_title": "🚨 強力な売りシグナル検出！",
        "notification_color": "0xFF0000",
        "take_profit": "-50pips",
        "stop_loss": "+30pips",
    }

    # 処理テスト
    result = await integration.process_detection_result(mock_detection, "USD/JPY")
    print(f"処理結果: {result}")


if __name__ == "__main__":
    asyncio.run(test_integration())
