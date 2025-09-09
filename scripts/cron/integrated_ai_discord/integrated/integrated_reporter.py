#!/usr/bin/env python3
"""
Integrated Reporter Module
統合AI分析Discord配信システム（最適化版）
"""

import sys
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import pytz
from rich.console import Console

# プロジェクトパス追加
sys.path.append("/app")

import os

# ローカルモジュールのインポート
import sys

# プロジェクト固有のインポート
from src.infrastructure.analysis.currency_correlation_analyzer import (
    CurrencyCorrelationAnalyzer,
)  # noqa: E402
from src.infrastructure.cache.analysis_cache import AnalysisCacheManager  # noqa: E402
from src.infrastructure.cache.cache_manager import CacheManager  # noqa: E402
from src.infrastructure.database.connection import get_async_session  # noqa: E402
from src.infrastructure.database.repositories.analysis_cache_repository_impl import (
    AnalysisCacheRepositoryImpl,
)  # noqa: E402
from src.infrastructure.database.repositories.notification_history_repository_impl import (
    NotificationHistoryRepositoryImpl,
)  # noqa: E402
from src.infrastructure.messaging.discord_client import DiscordClient  # noqa: E402
from src.infrastructure.messaging.notification_manager import (
    NotificationManager,
)  # noqa: E402
from src.infrastructure.optimization.api_rate_limiter import (
    ApiRateLimiter,
)  # noqa: E402
from src.infrastructure.optimization.batch_processor import BatchProcessor  # noqa: E402
from src.infrastructure.optimization.data_optimizer import DataOptimizer  # noqa: E402

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_analysis.ai_strategy_generator import AIStrategyGenerator
from analyzers.chart_visualizer import ChartVisualizer
from analyzers.fibonacci_analyzer import FibonacciAnalyzer
from analyzers.talib_technical_analyzer import TALibTechnicalIndicatorsAnalyzer
from notifications.discord_sender import DiscordSender

from utils.config_manager import ConfigManager
from utils.error_handler import ErrorHandler


class IntegratedAIDiscordReporter:
    """統合AI分析Discord配信システム（最適化版）"""

    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler()

        # 設定から値を取得
        self.openai_key = self.config_manager.openai_api_key
        self.discord_webhook = self.config_manager.discord_webhook_url

        # 通貨相関アナライザー初期化
        self.correlation_analyzer = CurrencyCorrelationAnalyzer()

        # テクニカル指標アナライザー初期化（TA-Lib標準）
        self.technical_analyzer = TALibTechnicalIndicatorsAnalyzer()

        # フィボナッチ分析アナライザー初期化
        self.fibonacci_analyzer = FibonacciAnalyzer()

        # チャート描写器初期化
        self.chart_visualizer = ChartVisualizer()

        # AI戦略生成器初期化
        self.ai_strategy_generator = AIStrategyGenerator(
            self.openai_key, pytz.timezone("Asia/Tokyo")
        )

        # Discord送信器初期化
        self.discord_sender = DiscordSender(
            self.discord_webhook, pytz.timezone("Asia/Tokyo")
        )

        # 最適化コンポーネント初期化
        self.cache_manager = None
        self.data_optimizer = None
        self.analysis_cache = None
        self.notification_manager = None
        self.discord_client = None

        # データベースセッション管理
        self._async_session = None

        self.jst = pytz.timezone("Asia/Tokyo")

    async def initialize_optimization_components(self):
        """最適化コンポーネントを初期化"""
        try:
            # データベースセッション取得
            self._async_session = await get_async_session()

            # リポジトリ初期化
            analysis_cache_repo = AnalysisCacheRepositoryImpl(self._async_session)
            notification_history_repo = NotificationHistoryRepositoryImpl(
                self._async_session
            )

            # キャッシュマネージャー初期化
            self.cache_manager = CacheManager(
                analysis_cache_repository=analysis_cache_repo
            )

            # API制限管理とバッチ処理初期化
            api_rate_limiter = ApiRateLimiter()
            batch_processor = BatchProcessor(api_rate_limiter=api_rate_limiter)

            # データ最適化器初期化
            self.data_optimizer = DataOptimizer(
                cache_manager=self.cache_manager,
                api_rate_limiter=api_rate_limiter,
                batch_processor=batch_processor,
                yahoo_finance_client=self.correlation_analyzer.yahoo_client,
            )

            # 分析キャッシュマネージャー初期化
            self.analysis_cache = AnalysisCacheManager(analysis_cache_repo)

            # Discordクライアント初期化
            self.discord_client = DiscordClient(
                webhook_url=self.discord_webhook,
                notification_history_repository=notification_history_repo,
                enable_notification_logging=True,
            )

            # 通知マネージャー初期化
            self.notification_manager = NotificationManager(
                discord_client=self.discord_client,
                notification_history_repository=notification_history_repo,
                duplicate_check_window_minutes=30,
                max_notifications_per_hour=10,
                enable_priority_filtering=True,
                enable_duplicate_prevention=True,
            )

            self.console.print("✅ 最適化コンポーネント初期化完了")

        except Exception as e:
            self.error_handler.log_error(e, "最適化コンポーネント初期化")
            self.console.print("📝 データベース接続なしで実行します")

            # データベース接続エラーの場合、基本機能のみ初期化
            try:
                # API制限管理とバッチ処理初期化
                api_rate_limiter = ApiRateLimiter()
                batch_processor = BatchProcessor(api_rate_limiter=api_rate_limiter)

                # データ最適化器初期化（キャッシュなし）
                self.data_optimizer = DataOptimizer(
                    cache_manager=None,
                    api_rate_limiter=api_rate_limiter,
                    batch_processor=batch_processor,
                    yahoo_finance_client=self.correlation_analyzer.yahoo_client,
                )

                # Discordクライアント初期化（履歴なし）
                self.discord_client = DiscordClient(
                    webhook_url=self.discord_webhook,
                    notification_history_repository=None,
                    enable_notification_logging=False,
                )

                # 通知マネージャー初期化（基本機能のみ）
                self.notification_manager = NotificationManager(
                    discord_client=self.discord_client,
                    notification_history_repository=None,
                    duplicate_check_window_minutes=30,
                    max_notifications_per_hour=10,
                    enable_priority_filtering=False,
                    enable_duplicate_prevention=False,
                )

                self.console.print("✅ 基本機能のみで初期化完了")

            except Exception as fallback_error:
                self.error_handler.log_error(fallback_error, "基本機能初期化")
                raise

    async def close_session(self):
        """データベースセッションをクローズ"""
        if self._async_session:
            try:
                await self._async_session.close()
                self.console.print("✅ データベースセッションクローズ完了")
            except Exception as e:
                self.error_handler.log_error(e, "セッションクローズ")
            finally:
                self._async_session = None

    async def _fetch_technical_indicators(
        self, currency_pair: str
    ) -> Optional[Dict[str, Any]]:
        """テクニカル指標データを取得（最適化版）"""
        self.console.print(f"📈 {currency_pair} テクニカル指標分析中...")

        try:
            # キャッシュチェック（データベース接続エラーを考慮）
            if self.analysis_cache:
                # キャッシュを無効化して強制的に再計算
                try:
                    await self.analysis_cache.invalidate_analysis(
                        "technical_indicators", currency_pair
                    )
                    self.console.print(
                        f"🔄 {currency_pair} キャッシュ無効化、再計算実行"
                    )
                except Exception as e:
                    # データベース接続エラーの場合は詳細を表示しない
                    if "Connect call failed" in str(e):
                        self.console.print(
                            f"🔄 {currency_pair} キャッシュ無効、直接計算実行"
                        )
                    else:
                        self.console.print(
                            f"⚠️ キャッシュ無効化エラー（分析は継続）: {str(e)}"
                        )
                        self.console.print(f"🔄 {currency_pair} 強制再計算実行")
            else:
                self.console.print(f"🔄 {currency_pair} キャッシュ無効、直接計算実行")

            # 複数期間の履歴データ取得（最適化版）
            timeframes = {
                "D1": ("1y", "1d"),  # 1年、日足（MA200計算のため）
                "H4": ("1mo", "1h"),  # 1ヶ月、1時間足
                "H1": ("1wk", "1h"),  # 1週間、1時間足
                "M5": ("3d", "5m"),  # 3日、5分足
            }

            indicators_data = {}

            # データ最適化器を使用して効率的にデータ取得
            if self.data_optimizer:
                for tf, (period, interval) in timeframes.items():
                    hist_data = await self.data_optimizer.get_historical_dataframe(
                        currency_pair, period, interval
                    )
                    if hist_data is not None and not hist_data.empty:
                        # RSI計算（複数期間）
                        rsi_long_result = self.technical_analyzer.calculate_rsi(
                            hist_data, tf, period=70
                        )
                        rsi_medium_result = self.technical_analyzer.calculate_rsi(
                            hist_data, tf, period=50
                        )
                        rsi_short_result = self.technical_analyzer.calculate_rsi(
                            hist_data, tf, period=30
                        )
                        indicators_data[f"{tf}_RSI_LONG"] = rsi_long_result
                        indicators_data[f"{tf}_RSI_MEDIUM"] = rsi_medium_result
                        indicators_data[f"{tf}_RSI_SHORT"] = rsi_short_result

                        # MACD計算（D1のみ）
                        if tf == "D1" and len(hist_data) >= 40:
                            macd_result = self.technical_analyzer.calculate_macd(
                                hist_data, tf
                            )
                            indicators_data[f"{tf}_MACD"] = macd_result

                        # ボリンジャーバンド計算
                        bb_result = self.technical_analyzer.calculate_bollinger_bands(
                            hist_data, tf
                        )
                        indicators_data[f"{tf}_BB"] = bb_result

                        # 移動平均線計算（時間軸別に異なる期間）
                        if tf == "D1":
                            # D1: 長期(200)と中期(50)
                            ma_long_result = (
                                self.technical_analyzer.calculate_moving_averages(
                                    hist_data, tf, ma_type="SMA", period=200
                                )
                            )
                            ma_medium_result = (
                                self.technical_analyzer.calculate_moving_averages(
                                    hist_data, tf, ma_type="SMA", period=50
                                )
                            )
                            indicators_data[f"{tf}_MA_LONG"] = ma_long_result
                            indicators_data[f"{tf}_MA_MEDIUM"] = ma_medium_result
                        elif tf == "H4":
                            # H4: 中期(50)と短期(20)
                            ma_medium_result = (
                                self.technical_analyzer.calculate_moving_averages(
                                    hist_data, tf, ma_type="SMA", period=50
                                )
                            )
                            ma_short_result = (
                                self.technical_analyzer.calculate_moving_averages(
                                    hist_data, tf, ma_type="SMA", period=20
                                )
                            )
                            indicators_data[f"{tf}_MA_MEDIUM"] = ma_medium_result
                            indicators_data[f"{tf}_MA_SHORT"] = ma_short_result
                        elif tf == "H1":
                            # H1: 短期(20)
                            ma_short_result = (
                                self.technical_analyzer.calculate_moving_averages(
                                    hist_data, tf, ma_type="SMA", period=20
                                )
                            )
                            indicators_data[f"{tf}_MA_SHORT"] = ma_short_result
                        elif tf == "M5":
                            # M5: 短期(20)
                            ma_short_result = (
                                self.technical_analyzer.calculate_moving_averages(
                                    hist_data, tf, ma_type="SMA", period=20
                                )
                            )
                            indicators_data[f"{tf}_MA_SHORT"] = ma_short_result

                        # フィボナッチ分析追加
                        fib_result = (
                            self.fibonacci_analyzer.calculate_fibonacci_analysis(
                                hist_data, tf
                            )
                        )
                        indicators_data[f"{tf}_FIB"] = fib_result

                        # ATR(14)計算
                        atr_result = self.technical_analyzer.calculate_atr(
                            hist_data, tf, period=14
                        )
                        indicators_data[f"{tf}_ATR"] = atr_result

                        # ADX(14)計算
                        adx_result = self.technical_analyzer.calculate_adx(
                            hist_data, tf, period=14
                        )
                        indicators_data[f"{tf}_ADX"] = adx_result

                        # H1のMACD計算を追加
                        if tf == "H1":
                            try:
                                macd_result = self.technical_analyzer.calculate_macd(
                                    hist_data, tf
                                )
                                indicators_data[f"{tf}_MACD"] = macd_result
                                self.console.print(f"✅ H1: MACD計算成功")
                            except Exception as e:
                                self.console.print(f"❌ H1: MACD計算失敗 - {e}")
                                indicators_data[f"{tf}_MACD"] = {"current_value": None}

                        # 結果出力
                        self._log_technical_results(tf, indicators_data)

                        # H1データのデバッグ出力
                        if tf == "H1":
                            self.console.print(
                                f"🔍 H1 indicators_data: {list(indicators_data.keys())}"
                            )
                            for key, value in indicators_data.items():
                                if isinstance(value, dict) and "current_value" in value:
                                    self.console.print(
                                        f"🔍 {key}: {value.get('current_value', 'N/A')}"
                                    )
                                elif key == "H1_MACD":
                                    self.console.print(f"🔍 {key}: {value}")

                    else:
                        self.console.print(f"❌ {tf}: 履歴データ取得失敗")
            else:
                # フォールバック: 従来の方法
                yahoo_client = self.correlation_analyzer.yahoo_client
                for tf, (period, interval) in timeframes.items():
                    hist_data = await yahoo_client.get_historical_data(
                        currency_pair, period, interval
                    )
                    if hist_data is not None and not hist_data.empty:
                        # 同様の処理を実行
                        self._process_technical_data(
                            hist_data, tf, indicators_data, currency_pair
                        )
                    else:
                        self.console.print(f"❌ {tf}: 履歴データ取得失敗")

            # 結果をキャッシュに保存（データベース接続エラーを考慮）
            if indicators_data and self.analysis_cache:
                try:
                    await self.analysis_cache.set_analysis(
                        "technical_indicators",
                        currency_pair,
                        indicators_data,
                        "multi_timeframe",
                    )
                    self.console.print(f"✅ {currency_pair} キャッシュ保存成功")
                except Exception as e:
                    # データベース接続エラーの場合は詳細を表示しない
                    if "Connect call failed" in str(e):
                        self.console.print(
                            f"✅ {currency_pair} 分析完了（キャッシュ無効）"
                        )
                    else:
                        self.console.print(
                            f"⚠️ キャッシュ保存エラー（分析は継続）: {str(e)}"
                        )
                    # キャッシュエラーでも分析結果は返す

            return indicators_data if indicators_data else None

        except Exception as e:
            self.error_handler.log_error(e, f"{currency_pair} テクニカル指標")
            return None

    def _log_technical_results(self, tf: str, indicators_data: Dict[str, Any]):
        """テクニカル指標結果をログ出力"""
        # RSI出力
        for period in ["LONG", "MEDIUM", "SHORT"]:
            key = f"{tf}_RSI_{period}"
            if key in indicators_data:
                rsi_val = indicators_data[key].get("current_value", "N/A")
                if isinstance(rsi_val, (int, float)):
                    self.console.print(f"✅ {tf}: RSI_{period}={rsi_val:.1f}")
                else:
                    self.console.print(f"✅ {tf}: RSI_{period}={rsi_val}")

        # MACD出力（D1のみ）
        if tf == "D1" and f"{tf}_MACD" in indicators_data:
            macd_data = indicators_data[f"{tf}_MACD"]
            macd_line = macd_data.get("macd_line", "N/A")
            signal_line = macd_data.get("signal_line", "N/A")
            histogram = macd_data.get("histogram", "N/A")
            if isinstance(macd_line, (int, float)) and isinstance(
                signal_line, (int, float)
            ):
                self.console.print(
                    f"✅ {tf}: MACD={macd_line:.4f}, "
                    f"Signal={signal_line:.4f}, Hist={histogram:.4f}"
                )

        # ボリンジャーバンド出力
        if f"{tf}_BB" in indicators_data:
            bb_data = indicators_data[f"{tf}_BB"]
            upper_band = bb_data.get("upper_band", "N/A")
            middle_band = bb_data.get("middle_band", "N/A")
            lower_band = bb_data.get("lower_band", "N/A")
            if isinstance(upper_band, (int, float)) and isinstance(
                middle_band, (int, float)
            ):
                self.console.print(
                    f"✅ {tf}: BB Upper={upper_band:.4f}, "
                    f"Middle={middle_band:.4f}, Lower={lower_band:.4f}"
                )

        # 移動平均線出力
        self._log_moving_averages(tf, indicators_data)

        # フィボナッチ出力
        if f"{tf}_FIB" in indicators_data:
            fib_result = indicators_data[f"{tf}_FIB"]
            if "error" not in fib_result:
                swing_high = fib_result.get("swing_high", "N/A")
                swing_low = fib_result.get("swing_low", "N/A")
                levels = fib_result.get("levels", {})
                current_position = fib_result.get("current_position", {})

                if isinstance(swing_high, (int, float)) and isinstance(
                    swing_low, (int, float)
                ):
                    # 基本情報
                    fib_info = (
                        f"✅ {tf}: Fib High={swing_high:.4f}, Low={swing_low:.4f}"
                    )

                    # 現在位置情報
                    if isinstance(current_position, dict):
                        percentage = current_position.get("percentage", "N/A")
                        nearest_level = current_position.get("nearest_level", "N/A")
                        fib_info += (
                            f" | 現在位置: {percentage}% (最寄り: {nearest_level})"
                        )

                    self.console.print(fib_info)

                    # 各フィボナッチレベルの価格を表示
                    if isinstance(levels, dict) and levels:
                        level_prices = []
                        for level_name, level_price in levels.items():
                            if isinstance(level_price, (int, float)):
                                level_prices.append(f"{level_name}={level_price:.4f}")

                        if level_prices:
                            self.console.print(
                                f"   📊 {tf} Fib Levels: {', '.join(level_prices)}"
                            )
            else:
                self.console.print(f"⚠️ {tf}: フィボナッチ計算エラー")

        # ATR出力
        if f"{tf}_ATR" in indicators_data:
            atr_data = indicators_data[f"{tf}_ATR"]
            if "error" not in atr_data:
                atr_value = atr_data.get("current_value", "N/A")
                if isinstance(atr_value, (int, float)):
                    self.console.print(f"✅ {tf}: ATR(14)={atr_value:.4f}")
            else:
                self.console.print(f"⚠️ {tf}: ATR計算エラー")

        # ADX出力
        if f"{tf}_ADX" in indicators_data:
            adx_data = indicators_data[f"{tf}_ADX"]
            if "error" not in adx_data:
                adx_value = adx_data.get("current_value", "N/A")
                if isinstance(adx_value, (int, float)):
                    self.console.print(f"✅ {tf}: ADX(14)={adx_value:.1f}")
            else:
                self.console.print(f"⚠️ {tf}: ADX計算エラー")

    def _log_moving_averages(self, tf: str, indicators_data: Dict[str, Any]):
        """移動平均線結果をログ出力"""
        if tf == "D1":
            if f"{tf}_MA_LONG" in indicators_data:
                ma_long_data = indicators_data[f"{tf}_MA_LONG"]
                ma_long_val = ma_long_data.get("ma_long", "N/A")
                if isinstance(ma_long_val, (int, float)):
                    self.console.print(f"✅ {tf}: MA200={ma_long_val:.4f}")

            if f"{tf}_MA_MEDIUM" in indicators_data:
                ma_medium_data = indicators_data[f"{tf}_MA_MEDIUM"]
                ma_medium_val = ma_medium_data.get("ma_medium", "N/A")
                if isinstance(ma_medium_val, (int, float)):
                    self.console.print(f"✅ {tf}: MA50={ma_medium_val:.4f}")

        elif tf == "H4":
            if f"{tf}_MA_MEDIUM" in indicators_data:
                ma_medium_data = indicators_data[f"{tf}_MA_MEDIUM"]
                ma_medium_val = ma_medium_data.get("ma_medium", "N/A")
                if isinstance(ma_medium_val, (int, float)):
                    self.console.print(f"✅ {tf}: MA50={ma_medium_val:.4f}")

            if f"{tf}_MA_SHORT" in indicators_data:
                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                ma_short_val = ma_short_data.get("ma_short", "N/A")
                if isinstance(ma_short_val, (int, float)):
                    self.console.print(f"✅ {tf}: MA20={ma_short_val:.4f}")

        elif tf in ["H1", "M5"]:
            if f"{tf}_MA_SHORT" in indicators_data:
                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                ma_short_val = ma_short_data.get("ma_short", "N/A")
                if isinstance(ma_short_val, (int, float)):
                    self.console.print(f"✅ {tf}: MA20={ma_short_val:.4f}")

    def _process_technical_data(
        self, hist_data, tf: str, indicators_data: Dict[str, Any], currency_pair: str
    ):
        """テクニカルデータ処理（フォールバック用）"""
        # RSI計算（複数期間）
        rsi_long_result = self.technical_analyzer.calculate_rsi(
            hist_data, tf, period=70
        )
        rsi_medium_result = self.technical_analyzer.calculate_rsi(
            hist_data, tf, period=50
        )
        rsi_short_result = self.technical_analyzer.calculate_rsi(
            hist_data, tf, period=30
        )
        indicators_data[f"{tf}_RSI_LONG"] = rsi_long_result
        indicators_data[f"{tf}_RSI_MEDIUM"] = rsi_medium_result
        indicators_data[f"{tf}_RSI_SHORT"] = rsi_short_result

        # MACD計算（D1のみ）
        if tf == "D1" and len(hist_data) >= 40:
            macd_result = self.technical_analyzer.calculate_macd(hist_data, tf)
            indicators_data[f"{tf}_MACD"] = macd_result

        # ボリンジャーバンド計算
        bb_result = self.technical_analyzer.calculate_bollinger_bands(hist_data, tf)
        indicators_data[f"{tf}_BB"] = bb_result

        # 移動平均線計算
        if tf == "D1":
            ma_long_result = self.technical_analyzer.calculate_moving_averages(
                hist_data, tf, ma_type="SMA", period=200
            )
            ma_medium_result = self.technical_analyzer.calculate_moving_averages(
                hist_data, tf, ma_type="SMA", period=50
            )
            indicators_data[f"{tf}_MA_LONG"] = ma_long_result
            indicators_data[f"{tf}_MA_MEDIUM"] = ma_medium_result
        elif tf in ["H4", "H1", "M5"]:
            ma_short_result = self.technical_analyzer.calculate_moving_averages(
                hist_data, tf, ma_type="SMA", period=20
            )
            indicators_data[f"{tf}_MA_SHORT"] = ma_short_result

        # フィボナッチ分析
        fib_result = self.fibonacci_analyzer.calculate_fibonacci_analysis(hist_data, tf)
        indicators_data[f"{tf}_FIB"] = fib_result

        # ATR(14)計算
        atr_result = self.technical_analyzer.calculate_atr(hist_data, tf, period=14)
        indicators_data[f"{tf}_ATR"] = atr_result

        # ADX(14)計算
        adx_result = self.technical_analyzer.calculate_adx(hist_data, tf, period=14)
        indicators_data[f"{tf}_ADX"] = adx_result

    async def generate_and_send_integrated_report(self) -> bool:
        """統合相関分析レポート生成・配信"""
        self.console.print("🚀 統合相関分析レポート生成・配信開始")
        self.console.print(
            f"🕘 日本時間: {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M:%S JST')}"
        )

        try:
            # Step 1: USD/JPYテクニカル指標取得
            technical_data = await self._fetch_technical_indicators("USD/JPY")

            # Step 2: 通貨相関分析実行（テクニカル指標統合）
            correlation_data = (
                await self.correlation_analyzer.perform_integrated_analysis(
                    technical_data
                )
            )
            if "error" in correlation_data:
                self.console.print("❌ 通貨相関分析失敗")
                return False

            # H1専用のテクニカルデータを追加
            self.console.print("🔍 H1データ抽出開始...")
            h1_technical_data = self._extract_h1_technical_data(technical_data)
            correlation_data["h1_technical_data"] = h1_technical_data
            self.console.print(f"🔍 H1データ抽出完了: {h1_technical_data}")

            # 相関分析結果を表示
            self.correlation_analyzer.display_correlation_analysis(correlation_data)

            # Step 2.5: H1チャート生成
            chart_file_path = await self._generate_h1_chart("USD/JPY", technical_data)

            # Step 3: 統合AI分析生成
            analysis_result = (
                await self.ai_strategy_generator.generate_integrated_analysis(
                    correlation_data, technical_data
                )
            )
            self.console.print(
                f"🔍 分析結果の状態: {type(analysis_result)} - {bool(analysis_result)}"
            )
            if not analysis_result:
                self.console.print("❌ 統合AI分析生成失敗")
                return False

            # Step 4: Discord配信（分析結果）
            discord_success = (
                await self.discord_sender.send_integrated_analysis_to_discord(
                    correlation_data, analysis_result
                )
            )
            if not discord_success:
                self.console.print("❌ 分析結果Discord配信失敗")

            # Step 5: H1チャート生成・配信
            h1_chart_success = False
            if chart_file_path:
                h1_chart_success = await self.discord_sender.send_chart_to_discord(
                    chart_file_path, "USD/JPY H1"
                )
                if h1_chart_success:
                    self.console.print("✅ H1チャート画像Discord配信成功")
                else:
                    self.console.print("❌ H1チャート画像Discord配信失敗")
            else:
                self.console.print(
                    "⚠️ H1チャートファイルが生成されていないため、H1チャート配信をスキップ"
                )

            # Step 6: H4チャート生成・配信
            h4_chart_success = False
            h4_chart_file_path = await self._generate_h4_chart(
                "USD/JPY", technical_data
            )
            if h4_chart_file_path:
                h4_chart_success = await self.discord_sender.send_chart_to_discord(
                    h4_chart_file_path, "USD/JPY H4"
                )
                if h4_chart_success:
                    self.console.print("✅ H4チャート画像Discord配信成功")
                else:
                    self.console.print("❌ H4チャート画像Discord配信失敗")
            else:
                self.console.print(
                    "⚠️ H4チャートファイルが生成されていないため、H4チャート配信をスキップ"
                )

            # 成功判定（分析結果またはチャートのいずれかが成功すればOK）
            if discord_success or h1_chart_success or h4_chart_success:
                self.console.print("✅ 統合相関分析レポート配信完了")
                return True
            else:
                self.console.print("❌ Discord配信失敗")
                return False

        except Exception as e:
            error_msg = self.error_handler.format_error_message(
                e, "統合レポート生成・配信"
            )
            self.console.print(error_msg)

            # エラー通知をDiscordに送信
            await self.discord_sender.send_error_notification(error_msg)

            return False

    async def _generate_h1_chart(
        self, currency_pair: str, technical_data: Dict[str, Any]
    ) -> Optional[str]:
        """H1チャート生成"""
        try:
            # H1データを取得（EMA200計算のためにより長期間取得）
            if self.data_optimizer:
                hist_data = await self.data_optimizer.get_historical_dataframe(
                    currency_pair, "3mo", "1h"  # 1週間 → 3ヶ月に延長
                )

                if hist_data is not None and not hist_data.empty:
                    # デバッグ情報を追加
                    self.console.print(f"📊 H1データ取得: {len(hist_data)}行")
                    self.console.print(
                        f"📊 H1データインデックス: {type(hist_data.index)}"
                    )
                    self.console.print(
                        f"📊 H1データインデックスサンプル: {hist_data.index[:3]}"
                    )
                    self.console.print(f"📊 H1データカラム: {list(hist_data.columns)}")

                    # 日時インデックスを追加（1週間分のH1データ）
                    if isinstance(hist_data.index, pd.RangeIndex):
                        # 現在時刻から1週間前まで、1時間間隔で日時を作成
                        end_time = pd.Timestamp.now(self.jst)
                        start_time = end_time - pd.Timedelta(days=7)
                        date_range = pd.date_range(
                            start=start_time, end=end_time, freq="H"
                        )

                        # データの長さに合わせて日時を調整
                        if len(date_range) >= len(hist_data):
                            hist_data.index = date_range[-len(hist_data) :]
                        else:
                            # データが多すぎる場合は、最新のデータのみ使用
                            hist_data = hist_data.tail(len(date_range))
                            hist_data.index = date_range

                        self.console.print(f"📊 日時インデックス追加完了")
                        self.console.print(
                            f"📊 新しいインデックスサンプル: {hist_data.index[:3]}"
                        )

                    # チャート生成
                    chart_file_path = self.chart_visualizer.create_h1_chart(
                        hist_data, currency_pair, technical_data
                    )

                    if chart_file_path:
                        self.console.print(f"✅ H1チャート生成完了: {chart_file_path}")
                        return chart_file_path
                    else:
                        self.console.print("⚠️ H1チャート生成失敗")
                        return None
                else:
                    self.console.print("❌ H1データ取得失敗")
                    return None
            else:
                self.console.print("⚠️ データ最適化器が利用できません")
                return None

        except Exception as e:
            self.error_handler.log_error(e, f"{currency_pair} H1チャート生成")
            return None

    async def _generate_h4_chart(
        self, currency_pair: str, technical_data: Dict[str, Any]
    ) -> Optional[str]:
        """H4チャート生成"""
        try:
            # H4データを取得（EMA200計算のためにより長期間取得）
            if self.data_optimizer:
                hist_data = await self.data_optimizer.get_historical_dataframe(
                    currency_pair, "3mo", "4h"  # 1ヶ月 → 3ヶ月に延長
                )

                if hist_data is not None and not hist_data.empty:
                    # デバッグ情報を追加
                    self.console.print(f"📊 H4データ取得: {len(hist_data)}行")
                    self.console.print(
                        f"📊 H4データインデックス: {type(hist_data.index)}"
                    )
                    self.console.print(
                        f"📊 H4データインデックスサンプル: {hist_data.index[:3]}"
                    )
                    self.console.print(f"📊 H4データカラム: {list(hist_data.columns)}")

                    # 日時インデックスを追加（3ヶ月分のH4データ）
                    if isinstance(hist_data.index, pd.RangeIndex):
                        # 現在時刻から3ヶ月前まで、4時間間隔で日時を作成
                        end_time = pd.Timestamp.now(self.jst)
                        start_time = end_time - pd.Timedelta(days=90)
                        date_range = pd.date_range(
                            start=start_time, end=end_time, freq="4H"
                        )

                        # データの長さに合わせて日時を調整
                        if len(date_range) >= len(hist_data):
                            hist_data.index = date_range[-len(hist_data) :]
                        else:
                            # データが多すぎる場合は、最新のデータのみ使用
                            hist_data = hist_data.tail(len(date_range))
                            hist_data.index = date_range

                        self.console.print(f"📊 H4日時インデックス追加完了")
                        self.console.print(
                            f"📊 H4新しいインデックスサンプル: {hist_data.index[:3]}"
                        )

                    # H4フィボナッチデータを取得
                    h4_fib_data = {}
                    if self.fibonacci_analyzer:
                        fib_result = (
                            self.fibonacci_analyzer.calculate_fibonacci_analysis(
                                hist_data, "H4"
                            )
                        )
                        h4_fib_data = {"H4_FIB": fib_result}
                        self.console.print(f"📊 H4フィボナッチデータ取得: {fib_result}")

                    # チャート生成
                    chart_file_path = self.chart_visualizer.create_h4_chart(
                        hist_data, currency_pair, h4_fib_data
                    )

                    if chart_file_path:
                        self.console.print(f"✅ H4チャート生成完了: {chart_file_path}")
                        return chart_file_path
                    else:
                        self.console.print("⚠️ H4チャート生成失敗")
                        return None
                else:
                    self.console.print("❌ H4データ取得失敗")
                    return None
            else:
                self.console.print("⚠️ データ最適化器が利用できません")
                return None

        except Exception as e:
            self.error_handler.log_error(e, f"{currency_pair} H4チャート生成")
            return None

    def _extract_h1_technical_data(
        self, technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """H1専用のテクニカルデータを抽出"""
        h1_data = technical_data.get("H1", {})

        # H1データを直接検索
        h1_data = {}
        for key, value in technical_data.items():
            if key.startswith("H1_"):
                h1_data[key] = value

        # H1のテクニカル指標を抽出
        h1_technical = {
            "trend_type": "N/A",
            "macd_value": "N/A",
            "rsi_value": "N/A",
            "atr_value": "N/A",
            "adx_value": "N/A",
        }

        # MACD
        h1_macd = h1_data.get("H1_MACD", {})
        if h1_macd and h1_macd.get("macd_line") is not None:
            h1_technical["macd_value"] = f"{h1_macd['macd_line']:.3f}"

        # RSI
        h1_rsi = h1_data.get("H1_RSI_LONG", {})
        if h1_rsi and h1_rsi.get("current_value") is not None:
            h1_technical["rsi_value"] = f"{h1_rsi['current_value']:.1f}"

        # ATR
        h1_atr = h1_data.get("H1_ATR", {})
        if h1_atr and h1_atr.get("current_value") is not None:
            h1_technical["atr_value"] = f"{h1_atr['current_value']:.3f}"

        # ADX
        h1_adx = h1_data.get("H1_ADX", {})
        if h1_adx and h1_adx.get("current_value") is not None:
            h1_technical["adx_value"] = f"{h1_adx['current_value']:.1f}"

        # トレンド判定（MACDとRSIに基づく）
        if h1_technical["macd_value"] != "N/A" and h1_technical["rsi_value"] != "N/A":
            macd_val = float(h1_technical["macd_value"])
            rsi_val = float(h1_technical["rsi_value"])

            if macd_val > 0 and rsi_val > 50:
                h1_technical["trend_type"] = "上昇トレンド"
            elif macd_val < 0 and rsi_val < 50:
                h1_technical["trend_type"] = "下降トレンド"
            else:
                h1_technical["trend_type"] = "レンジ相場"

        return h1_technical
