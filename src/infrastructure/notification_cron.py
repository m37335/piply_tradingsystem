"""
通知専用cronスクリプト

定期実行によるパターン検出とDiscord通知を管理するスクリプト
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
from src.utils.pattern_utils import PatternUtils


class NotificationCron:
    """通知専用cronスクリプト"""

    def __init__(self):
        self.analyzer = NotificationPatternAnalyzer()
        self.utils = PatternUtils()

        # テンプレートマッピング
        self.templates = {
            1: Pattern1Template(),
            2: Pattern2Template(),
            3: Pattern3Template(),
            4: Pattern4Template(),
            6: Pattern6Template(),
        }

        # 設定
        self.currency_pairs = ["USD/JPY", "EUR/USD", "GBP/USD"]
        self.check_interval = 300  # 5分間隔
        self.notification_cooldown = 3600  # 1時間のクールダウン

        # 通知履歴
        self.notification_history = {}

        # ログ設定
        self.setup_logging()

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("notification_cron.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    async def run_continuous_monitoring(self):
        """継続的な監視を実行"""
        self.logger.info("通知cronスクリプトを開始しました")

        while True:
            try:
                await self.check_all_currency_pairs()
                await asyncio.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.logger.info("監視を停止しました")
                break
            except Exception as e:
                self.logger.error(f"監視中にエラーが発生しました: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def check_all_currency_pairs(self):
        """全通貨ペアをチェック"""
        for currency_pair in self.currency_pairs:
            try:
                await self.check_single_currency_pair(currency_pair)
            except Exception as e:
                self.logger.error(f"{currency_pair}のチェック中にエラー: {e}")

    async def check_single_currency_pair(self, currency_pair: str):
        """単一の通貨ペアをチェック"""
        self.logger.info(f"{currency_pair}をチェック中...")

        # マルチタイムフレームデータを取得
        multi_timeframe_data = await self.get_multi_timeframe_data(currency_pair)

        if not multi_timeframe_data:
            self.logger.warning(f"{currency_pair}のデータ取得に失敗しました")
            return

        # パターン分析を実行
        detected_patterns = self.analyzer.analyze_multi_timeframe_data(
            multi_timeframe_data, currency_pair
        )

        if detected_patterns:
            await self.process_detected_patterns(detected_patterns, currency_pair)
        else:
            self.logger.info(f"{currency_pair}でパターンは検出されませんでした")

    async def get_multi_timeframe_data(
        self, currency_pair: str
    ) -> Optional[Dict[str, Any]]:
        """
        マルチタイムフレームデータを取得

        Args:
            currency_pair: 通貨ペア

        Returns:
            マルチタイムフレームデータ
        """
        try:
            # 実際の実装では、ここでリアルタイムデータを取得
            # 現在はモックデータを使用
            return self.create_mock_multi_timeframe_data()

        except Exception as e:
            self.logger.error(f"データ取得エラー: {e}")
            return None

    def create_mock_multi_timeframe_data(self) -> Dict[str, Any]:
        """モックのマルチタイムフレームデータを作成"""
        # サンプル価格データを作成
        dates = pd.date_range(start="2025-01-01", periods=50, freq="1H")
        prices = pd.Series(
            [100 + i * 0.1 + (i % 10) * 0.05 for i in range(50)], index=dates
        )

        # 指標を計算
        rsi = self.utils.calculate_rsi(prices)
        macd = self.utils.calculate_macd(prices)
        bb = self.utils.calculate_bollinger_bands(prices)

        timeframe_data = {
            "price_data": pd.DataFrame(
                {
                    "Open": prices * 0.999,
                    "High": prices * 1.002,
                    "Low": prices * 0.998,
                    "Close": prices,
                    "Volume": [1000000] * 50,
                },
                index=dates,
            ),
            "indicators": {
                "rsi": {"current_value": rsi.iloc[-1], "series": rsi},
                "macd": macd,
                "bollinger_bands": bb,
            },
        }

        return {
            "D1": timeframe_data,
            "H4": timeframe_data,
            "H1": timeframe_data,
            "M5": timeframe_data,
        }

    async def process_detected_patterns(
        self, detected_patterns: List[Dict[str, Any]], currency_pair: str
    ):
        """
        検出されたパターンを処理

        Args:
            detected_patterns: 検出されたパターンのリスト
            currency_pair: 通貨ペア
        """
        for pattern in detected_patterns:
            pattern_number = pattern.get("pattern_number")

            if not pattern_number or pattern_number not in self.templates:
                self.logger.warning(f"未対応のパターン番号: {pattern_number}")
                continue

            # クールダウンチェック
            if self.is_in_cooldown(pattern_number, currency_pair):
                self.logger.info(f"パターン{pattern_number}はクールダウン中: {currency_pair}")
                continue

            # 通知を送信
            await self.send_notification(pattern, currency_pair)

            # 通知履歴を更新
            self.update_notification_history(pattern_number, currency_pair)

    def is_in_cooldown(self, pattern_number: int, currency_pair: str) -> bool:
        """
        クールダウン期間中かチェック

        Args:
            pattern_number: パターン番号
            currency_pair: 通貨ペア

        Returns:
            クールダウン期間中の場合はTrue
        """
        key = f"{pattern_number}_{currency_pair}"
        last_notification = self.notification_history.get(key)

        if not last_notification:
            return False

        time_since_last = datetime.now() - last_notification
        return time_since_last.total_seconds() < self.notification_cooldown

    def update_notification_history(self, pattern_number: int, currency_pair: str):
        """通知履歴を更新"""
        key = f"{pattern_number}_{currency_pair}"
        self.notification_history[key] = datetime.now()

    async def send_notification(self, pattern: Dict[str, Any], currency_pair: str):
        """
        Discord通知を送信

        Args:
            pattern: 検出されたパターン
            currency_pair: 通貨ペア
        """
        try:
            pattern_number = pattern.get("pattern_number")
            template = self.templates[pattern_number]

            # Embed形式の通知を作成
            embed = template.create_embed(pattern, currency_pair)

            # 実際のDiscord送信処理
            await self.send_discord_notification(embed, pattern, currency_pair)

            self.logger.info(f"通知を送信しました: パターン{pattern_number} - {currency_pair}")

        except Exception as e:
            self.logger.error(f"通知送信エラー: {e}")

    async def send_discord_notification(
        self, embed: Dict[str, Any], pattern: Dict[str, Any], currency_pair: str
    ):
        """
        Discordに通知を送信

        Args:
            embed: Discord Embed
            pattern: 検出されたパターン
            currency_pair: 通貨ペア
        """
        # 実際の実装では、ここでDiscord Webhookを使用
        # 現在はログ出力のみ
        self.logger.info(f"Discord通知送信: {currency_pair}")
        self.logger.info(f"Embed: {embed['title']}")

        # 優先度に基づく処理
        priority = pattern.get("priority", PatternPriority.LOW)
        if priority in [PatternPriority.HIGH, PatternPriority.VERY_HIGH]:
            self.logger.warning(f"高優先度通知: {priority} - {currency_pair}")

    def get_status_summary(self) -> Dict[str, Any]:
        """ステータスサマリーを取得"""
        return {
            "active_currency_pairs": len(self.currency_pairs),
            "active_templates": len(self.templates),
            "notification_history_count": len(self.notification_history),
            "check_interval_seconds": self.check_interval,
            "cooldown_seconds": self.notification_cooldown,
            "last_check": datetime.now().isoformat(),
        }

    async def run_single_check(self):
        """単発チェックを実行"""
        self.logger.info("単発チェックを開始しました")

        for currency_pair in self.currency_pairs:
            await self.check_single_currency_pair(currency_pair)

        self.logger.info("単発チェックが完了しました")


async def main():
    """メイン関数"""
    cron = NotificationCron()

    # コマンドライン引数をチェック
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # 単発チェック
        await cron.run_single_check()
    else:
        # 継続監視
        await cron.run_continuous_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
