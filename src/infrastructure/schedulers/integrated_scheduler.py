"""
統合スケジューラー

USD/JPY特化の5分おきデータ取得システム用の統合スケジューラー
データ取得、指標計算、パターン検出を統合した自動化システム

責任:
- 5分足データの定期取得
- 日足データの定期取得
- テクニカル指標の計算
- パターン検出の実行
- Discord通知の送信
- エラーハンドリングとリトライ
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.efficient_pattern_detection_service import (
    EfficientPatternDetectionService,
)
from src.infrastructure.database.services.multi_timeframe_data_fetcher_service import (
    MultiTimeframeDataFetcherService,
)
from src.infrastructure.database.services.multi_timeframe_technical_indicator_service import (
    MultiTimeframeTechnicalIndicatorService,
)
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.utils.logging_config import get_infrastructure_logger


class IntegratedScheduler:
    """
    統合スケジューラー

    責任:
    - データ取得、指標計算、パターン検出の統合管理
    - スケジュール管理
    - エラーハンドリング
    - システム監視
    """

    def __init__(self):
        self.logger = get_infrastructure_logger()
        self.session = None
        self.data_fetcher = None
        self.technical_indicator_service = None
        self.pattern_detection_service = None
        self.discord_sender = None

        # スケジューラー状態
        self.is_running = False
        self.tasks = []

        # 設定
        self.data_fetch_interval = 300  # 5分（秒）
        self.d1_fetch_interval = 86400  # 24時間（秒）
        self.pattern_detection_interval = 300  # 5分（秒）
        self.retry_attempts = 3
        self.retry_delay = 60  # 1分（秒）

    async def setup(self):
        """
        スケジューラーの初期化
        """
        self.logger.info("統合スケジューラーを初期化中...")

        try:
            # データベースセッションを取得
            self.session = await get_async_session()

            # 各サービスを初期化
            self.data_fetcher = MultiTimeframeDataFetcherService(self.session)
            self.technical_indicator_service = MultiTimeframeTechnicalIndicatorService(
                self.session
            )
            self.pattern_detection_service = EfficientPatternDetectionService(
                self.session
            )

            # Discord送信者を初期化
            import os

            webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL", "")
            self.discord_sender = DiscordWebhookSender(webhook_url)

            self.logger.info("統合スケジューラーの初期化が完了しました")

        except Exception as e:
            self.logger.error(f"統合スケジューラーの初期化に失敗しました: {e}")
            raise

    async def start_data_collection(self):
        """
        データ取得サービスを開始
        """
        self.logger.info("データ取得サービスを開始します")

        # 5分足データ取得タスク
        task_5m = asyncio.create_task(self._schedule_5m_data_fetch())
        self.tasks.append(task_5m)

        # 日足データ取得タスク
        task_d1 = asyncio.create_task(self._schedule_d1_data_fetch())
        self.tasks.append(task_d1)

        self.logger.info("データ取得サービスが開始されました")

    async def start_pattern_detection(self):
        """
        パターン検出サービスを開始
        """
        self.logger.info("パターン検出サービスを開始します")

        # パターン検出タスク
        task_pattern = asyncio.create_task(self._schedule_pattern_detection())
        self.tasks.append(task_pattern)

        self.logger.info("パターン検出サービスが開始されました")

    async def start_notification_service(self):
        """
        通知サービスを開始
        """
        self.logger.info("通知サービスを開始します")

        # 通知監視タスク
        task_notification = asyncio.create_task(self._monitor_notifications())
        self.tasks.append(task_notification)

        self.logger.info("通知サービスが開始されました")

    async def _schedule_5m_data_fetch(self):
        """
        5分足データ取得のスケジューリング
        """
        self.logger.info("5分足データ取得スケジューラーを開始します")

        while self.is_running:
            try:
                self.logger.info("5分足データを取得中...")

                # 5分足データを取得
                await self._fetch_5m_data_with_retry()

                # 次の実行まで待機
                await asyncio.sleep(self.data_fetch_interval)

            except asyncio.CancelledError:
                self.logger.info("5分足データ取得スケジューラーが停止されました")
                break
            except Exception as e:
                self.logger.error(f"5分足データ取得でエラーが発生しました: {e}")
                await asyncio.sleep(self.retry_delay)

    async def _schedule_d1_data_fetch(self):
        """
        日足データ取得のスケジューリング
        """
        self.logger.info("日足データ取得スケジューラーを開始します")

        while self.is_running:
            try:
                self.logger.info("日足データを取得中...")

                # 日足データを取得
                await self._fetch_d1_data_with_retry()

                # 次の実行まで待機（24時間）
                await asyncio.sleep(self.d1_fetch_interval)

            except asyncio.CancelledError:
                self.logger.info("日足データ取得スケジューラーが停止されました")
                break
            except Exception as e:
                self.logger.error(f"日足データ取得でエラーが発生しました: {e}")
                await asyncio.sleep(self.retry_delay)

    async def _schedule_pattern_detection(self):
        """
        パターン検出のスケジューリング
        """
        self.logger.info("パターン検出スケジューラーを開始します")

        while self.is_running:
            try:
                self.logger.info("パターン検出を実行中...")

                # パターン検出を実行
                await self._detect_patterns_with_retry()

                # 次の実行まで待機
                await asyncio.sleep(self.pattern_detection_interval)

            except asyncio.CancelledError:
                self.logger.info("パターン検出スケジューラーが停止されました")
                break
            except Exception as e:
                self.logger.error(f"パターン検出でエラーが発生しました: {e}")
                await asyncio.sleep(self.retry_delay)

    async def _monitor_notifications(self):
        """
        通知の監視
        """
        self.logger.info("通知監視サービスを開始します")

        while self.is_running:
            try:
                # 通知の監視処理（必要に応じて実装）
                await asyncio.sleep(60)  # 1分間隔で監視

            except asyncio.CancelledError:
                self.logger.info("通知監視サービスが停止されました")
                break
            except Exception as e:
                self.logger.error(f"通知監視でエラーが発生しました: {e}")
                await asyncio.sleep(self.retry_delay)

    async def _fetch_5m_data_with_retry(self):
        """
        5分足データ取得（リトライ機能付き）
        """
        for attempt in range(self.retry_attempts):
            try:
                # 5分足データを取得
                await self.data_fetcher.fetch_timeframe_data("5m")

                # テクニカル指標を計算
                await self.technical_indicator_service.calculate_all_timeframe_indicators()

                self.logger.info("5分足データ取得と指標計算が完了しました")
                return

            except Exception as e:
                self.logger.warning(
                    f"5分足データ取得試行 {attempt + 1}/{self.retry_attempts} が失敗しました: {e}"
                )

                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("5分足データ取得が最大試行回数に達しました")
                    raise

    async def _fetch_d1_data_with_retry(self):
        """
        日足データ取得（リトライ機能付き）
        """
        for attempt in range(self.retry_attempts):
            try:
                # 日足データを取得
                await self.data_fetcher.fetch_timeframe_data("1d")

                self.logger.info("日足データ取得が完了しました")
                return

            except Exception as e:
                self.logger.warning(
                    f"日足データ取得試行 {attempt + 1}/{self.retry_attempts} が失敗しました: {e}"
                )

                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("日足データ取得が最大試行回数に達しました")
                    raise

    async def _detect_patterns_with_retry(self):
        """
        パターン検出（リトライ機能付き）
        """
        for attempt in range(self.retry_attempts):
            try:
                # パターン検出を実行
                detected_patterns = (
                    await self.pattern_detection_service.detect_all_patterns()
                )

                if detected_patterns:
                    self.logger.info(f"{len(detected_patterns)}個のパターンが検出されました")

                    # Discord通知を送信
                    await self._send_pattern_notifications(detected_patterns)
                else:
                    self.logger.info("検出されたパターンはありません")

                return

            except Exception as e:
                self.logger.warning(
                    f"パターン検出試行 {attempt + 1}/{self.retry_attempts} が失敗しました: {e}"
                )

                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    self.logger.error("パターン検出が最大試行回数に達しました")
                    raise

    async def _send_pattern_notifications(self, patterns):
        """
        パターン検出結果をDiscordに通知
        """
        if not self.discord_sender.webhook_url:
            self.logger.warning("Discord Webhook URLが設定されていません")
            return

        try:
            async with self.discord_sender:
                for pattern in patterns:
                    # パターン情報をDiscord Embed形式で作成
                    embed = self._create_pattern_embed(pattern)

                    # Discord通知を送信
                    success = await self.discord_sender.send_embed(embed)

                    if success:
                        self.logger.info(f"パターン通知を送信しました: {pattern.pattern_name}")
                    else:
                        self.logger.error(f"パターン通知の送信に失敗しました: {pattern.pattern_name}")

                    # 通知間隔を空ける
                    await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"パターン通知送信中にエラーが発生しました: {e}")

    def _create_pattern_embed(self, pattern):
        """
        パターン検出結果のDiscord Embedを作成
        """
        from datetime import datetime

        # 方向に応じた色と絵文字を設定
        direction_config = {
            "BUY": {"color": 0x00FF00, "emoji": "🟢", "text": "買い"},
            "SELL": {"color": 0xFF0000, "emoji": "🔴", "text": "売り"},
            "hold": {"color": 0xFFFF00, "emoji": "🟡", "text": "ホールド"},
        }

        config = direction_config.get(pattern.direction, direction_config["hold"])

        # 信頼度に応じた評価
        confidence_emoji = (
            "🟢"
            if pattern.confidence_score >= 80
            else "🟡"
            if pattern.confidence_score >= 60
            else "🔴"
        )

        # detection_dataから値を取得
        detection_data = pattern.detection_data or {}
        entry_price = detection_data.get("entry_price", 0.0)
        stop_loss = detection_data.get("stop_loss", 0.0)
        take_profit = detection_data.get("take_profit", 0.0)
        timeframe = detection_data.get("timeframe", "Unknown")
        description = detection_data.get("description", "パターンが検出されました")

        # 埋め込みデータを作成
        embed = {
            "title": f"{config['emoji']} {pattern.pattern_name}",
            "description": description,
            "color": config["color"],
            "fields": [
                {"name": "通貨ペア", "value": pattern.currency_pair, "inline": True},
                {
                    "name": "方向",
                    "value": f"{config['emoji']} {config['text']}",
                    "inline": True,
                },
                {
                    "name": "信頼度",
                    "value": f"{confidence_emoji} {pattern.confidence_score:.1f}%",
                    "inline": True,
                },
                {"name": "時間軸", "value": timeframe, "inline": True},
                {
                    "name": "エントリー価格",
                    "value": f"¥{entry_price:.2f}",
                    "inline": True,
                },
                {
                    "name": "損切り",
                    "value": f"¥{stop_loss:.2f}",
                    "inline": True,
                },
                {
                    "name": "利確",
                    "value": f"¥{take_profit:.2f}",
                    "inline": True,
                },
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "USD/JPY パターン検出システム"},
        }

        # リスク/リワード比を計算
        if entry_price and stop_loss and take_profit:
            if pattern.direction == "BUY":
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit

            if risk > 0:
                rr_ratio = reward / risk
                embed["fields"].append(
                    {
                        "name": "リスク/リワード比",
                        "value": f"{rr_ratio:.2f}",
                        "inline": True,
                    }
                )

        return embed

    async def start(self):
        """
        統合スケジューラーを開始
        """
        self.logger.info("統合スケジューラーを開始します")

        try:
            # 初期化
            await self.setup()

            # 実行フラグを設定
            self.is_running = True

            # 各サービスを開始
            await self.start_data_collection()
            await self.start_pattern_detection()
            await self.start_notification_service()

            # シグナルハンドラーを設定
            self._setup_signal_handlers()

            self.logger.info("統合スケジューラーが開始されました")

            # メインループ
            while self.is_running:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"統合スケジューラーでエラーが発生しました: {e}")
            raise
        finally:
            await self.stop()

    async def stop(self):
        """
        統合スケジューラーを停止
        """
        self.logger.info("統合スケジューラーを停止中...")

        # 実行フラグを無効化
        self.is_running = False

        # タスクをキャンセル
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # タスクの完了を待機
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # セッションを閉じる
        if self.session:
            await self.session.close()

        self.logger.info("統合スケジューラーが停止されました")

    def _setup_signal_handlers(self):
        """
        シグナルハンドラーを設定
        """

        def signal_handler(signum, frame):
            self.logger.info(f"シグナル {signum} を受信しました。スケジューラーを停止します。")
            asyncio.create_task(self.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """
    メイン関数
    """
    scheduler = IntegratedScheduler()

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        print("\nユーザーによって停止されました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
