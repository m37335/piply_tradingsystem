#!/usr/bin/env python3
"""
Integrated AI Discord Reporter
通貨相関性を活用した統合AI分析Discord配信システム
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
import pytz
from rich.console import Console

# プロジェクトパス追加
sys.path.append("/app")

# プロジェクト固有のインポート
from src.infrastructure.analysis.currency_correlation_analyzer import (
    CurrencyCorrelationAnalyzer,
)  # noqa: E402
from src.infrastructure.analysis.technical_indicators import (
    TechnicalIndicatorsAnalyzer,
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


class FibonacciAnalyzer:
    """フィボナッチリトレースメント分析クラス（期間別階層アプローチ）"""

    def __init__(self):
        self.fibonacci_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.timeframe_periods = {
            "D1": 90,  # 3ヶ月間
            "H4": 14,  # 2週間
            "H1": 24,  # 24時間（1日分）
            "M5": 48,  # 4時間分（240分 / 5分）
        }

    def calculate_fibonacci_analysis(
        self, historical_data: List[Dict], timeframe: str
    ) -> Dict[str, Any]:
        """期間別階層アプローチでフィボナッチ分析"""
        try:
            lookback_days = self.timeframe_periods[timeframe]
            recent_data = historical_data[-lookback_days:]

            if len(recent_data) < 10:  # 最小データ数チェック
                return {
                    "indicator": "Fibonacci Retracement",
                    "timeframe": timeframe,
                    "error": "Insufficient data for analysis",
                }

            # スイングポイント検出
            # データ構造を確認して適切にアクセス

            if hasattr(recent_data, "columns"):  # pandas DataFrameの場合

                swing_high = float(recent_data["High"].max())
                swing_low = float(recent_data["Low"].min())
                current_price = float(recent_data["Close"].iloc[-1])
            elif (
                isinstance(recent_data, list)
                and len(recent_data) > 0
                and hasattr(recent_data[0], "get")
            ):  # 辞書形式の場合
                print(f"Debug Fib {timeframe}: Processing dict format")
                high_values = [
                    float(d.get("High", d.get("high", 0))) for d in recent_data
                ]
                low_values = [float(d.get("Low", d.get("low", 0))) for d in recent_data]
                swing_high = max(high_values)
                swing_low = min(low_values)
                current_price = float(
                    recent_data[-1].get("Close", recent_data[-1].get("close", 0))
                )
            else:  # その他の場合
                # デバッグ用にデータ構造を確認
                print(f"Debug: recent_data type: {type(recent_data)}")
                print(f"Debug: recent_data length: {len(recent_data)}")
                if len(recent_data) > 0:
                    print(f"Debug: recent_data[0] type: {type(recent_data[0])}")
                    print(f"Debug: recent_data[0] content: {recent_data[0]}")
                    # より詳細な構造確認
                    if hasattr(recent_data[0], "__dict__"):
                        print(
                            f"Debug: recent_data[0].__dict__: {recent_data[0].__dict__}"
                        )
                    if hasattr(recent_data[0], "keys"):
                        print(
                            f"Debug: recent_data[0].keys(): "
                            f"{list(recent_data[0].keys())}"
                        )
                raise ValueError(f"Unsupported data structure: {type(recent_data)}")

            # フィボナッチレベル計算
            levels = self._calculate_levels(swing_high, swing_low)

            # 現在価格の位置を判定
            current_position = self._get_current_position(
                current_price, levels, swing_high, swing_low
            )

            return {
                "indicator": "Fibonacci Retracement",
                "timeframe": timeframe,
                "swing_high": swing_high,
                "swing_low": swing_low,
                "current_price": current_price,
                "levels": levels,
                "current_position": current_position,
                "data_points": len(recent_data),
                "timestamp": datetime.now(timezone(timedelta(hours=9))),
            }

        except Exception as e:
            return {
                "indicator": "Fibonacci Retracement",
                "timeframe": timeframe,
                "error": f"Calculation error: {str(e)}",
            }

    def _calculate_levels(
        self, swing_high: float, swing_low: float
    ) -> Dict[str, float]:
        """フィボナッチレベルを計算"""
        diff = swing_high - swing_low

        if abs(diff) < 0.0001:  # ほぼ同じ値の場合
            raise ValueError(
                f"Swing high and low are too close: high={swing_high}, low={swing_low}"
            )

        levels = {}
        for level in self.fibonacci_levels:
            if swing_high > swing_low:  # 上昇トレンドのリトレースメント
                calculated_level = swing_high - (diff * level)
                levels[f"{level*100:.1f}%"] = calculated_level
            else:  # 下降トレンドのリトレースメント
                calculated_level = swing_low + (diff * level)
                levels[f"{level*100:.1f}%"] = calculated_level

        return levels

    def _get_current_position(
        self,
        current_price: float,
        levels: Dict[str, float],
        swing_high: float,
        swing_low: float,
    ) -> Dict[str, Any]:
        """現在価格のフィボナッチ位置を判定（詳細版）"""
        result = {
            "position": "",
            "percentage": 0.0,
            "nearest_level": "",
            "distance_to_nearest": 0.0,
        }

        if swing_high > swing_low:  # 上昇トレンド
            if current_price > swing_high:
                result["position"] = "above_swing_high"
                result["percentage"] = 100.0
                return result
            elif current_price < swing_low:
                result["position"] = "below_swing_low"
                result["percentage"] = 0.0
                return result
            else:
                # フィボナッチリトレースメントのパーセンテージを計算
                total_range = swing_high - swing_low
                retracement = swing_high - current_price
                percentage = (retracement / total_range) * 100
                result["percentage"] = round(percentage, 1)

                # 最も近いレベルを特定
                nearest_level = ""
                min_distance = float("inf")
                for level_name, level_price in levels.items():
                    distance = abs(current_price - level_price)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_level = level_name

                result["nearest_level"] = nearest_level
                result["distance_to_nearest"] = round(min_distance, 4)

                # 位置の判定
                if min_distance < total_range * 0.01:  # 1%以内
                    result["position"] = f"near_{nearest_level}"
                else:
                    result["position"] = f"between_levels_{result['percentage']}%"

                return result
        else:  # 下降トレンド
            if current_price < swing_low:
                result["position"] = "below_swing_low"
                result["percentage"] = 100.0
                return result
            elif current_price > swing_high:
                result["position"] = "below_swing_low"
                result["percentage"] = 0.0
                return result
            else:
                # フィボナッチエクステンションのパーセンテージを計算
                total_range = swing_low - swing_high
                extension = current_price - swing_low
                percentage = (extension / total_range) * 100
                result["percentage"] = round(percentage, 1)

                # 最も近いレベルを特定
                nearest_level = ""
                min_distance = float("inf")
                for level_name, level_price in levels.items():
                    distance = abs(current_price - level_price)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_level = level_name

                result["nearest_level"] = nearest_level
                result["distance_to_nearest"] = round(min_distance, 4)

                # 位置の判定
                if min_distance < abs(total_range) * 0.01:  # 1%以内
                    result["position"] = f"near_{nearest_level}"
                else:
                    result["position"] = f"between_levels_{result['percentage']}%"

                return result


class IntegratedAIDiscordReporter:
    """統合AI分析Discord配信システム（最適化版）"""

    def __init__(self):
        self.console = Console()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

        # API URLs
        self.openai_url = "https://api.openai.com/v1/chat/completions"

        # 通貨相関アナライザー初期化
        self.correlation_analyzer = CurrencyCorrelationAnalyzer()

        # テクニカル指標アナライザー初期化
        self.technical_analyzer = TechnicalIndicatorsAnalyzer()

        # フィボナッチ分析アナライザー初期化
        self.fibonacci_analyzer = FibonacciAnalyzer()

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
            self.console.print(f"⚠️ 最適化コンポーネント初期化エラー: {str(e)}")
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
                self.console.print(f"❌ 基本機能初期化も失敗: {str(fallback_error)}")
                raise

    async def close_session(self):
        """データベースセッションをクローズ"""
        if self._async_session:
            try:
                await self._async_session.close()
                self.console.print("✅ データベースセッションクローズ完了")
            except Exception as e:
                self.console.print(f"⚠️ セッションクローズエラー: {str(e)}")
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

                        # RSI出力
                        rsi_val = rsi_long_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI_LONG={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI_LONG={rsi_val}")

                        rsi_val = rsi_medium_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI_MEDIUM={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI_MEDIUM={rsi_val}")

                        rsi_val = rsi_short_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI_SHORT={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI_SHORT={rsi_val}")

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
                        bb_data = bb_result
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
                        if tf == "D1":
                            if f"{tf}_MA_LONG" in indicators_data:
                                ma_long_data = indicators_data[f"{tf}_MA_LONG"]
                                ma_long_val = ma_long_data.get("ma_long", "N/A")
                                if isinstance(ma_long_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA200={ma_long_val:.4f}"
                                    )

                            if f"{tf}_MA_MEDIUM" in indicators_data:
                                ma_medium_data = indicators_data[f"{tf}_MA_MEDIUM"]
                                ma_medium_val = ma_medium_data.get("ma_medium", "N/A")
                                if isinstance(ma_medium_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA50={ma_medium_val:.4f}"
                                    )

                        elif tf == "H4":
                            if f"{tf}_MA_MEDIUM" in indicators_data:
                                ma_medium_data = indicators_data[f"{tf}_MA_MEDIUM"]
                                ma_medium_val = ma_medium_data.get("ma_medium", "N/A")
                                if isinstance(ma_medium_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA50={ma_medium_val:.4f}"
                                    )

                            if f"{tf}_MA_SHORT" in indicators_data:
                                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                                ma_short_val = ma_short_data.get("ma_short", "N/A")
                                if isinstance(ma_short_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA20={ma_short_val:.4f}"
                                    )

                        elif tf == "H1":
                            if f"{tf}_MA_SHORT" in indicators_data:
                                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                                ma_short_val = ma_short_data.get("ma_short", "N/A")
                                if isinstance(ma_short_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA20={ma_short_val:.4f}"
                                    )
                        elif tf == "M5":
                            if f"{tf}_MA_SHORT" in indicators_data:
                                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                                ma_short_val = ma_short_data.get("ma_short", "N/A")
                                if isinstance(ma_short_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA20={ma_short_val:.4f}"
                                    )

                        # フィボナッチ分析追加
                        fib_result = (
                            self.fibonacci_analyzer.calculate_fibonacci_analysis(
                                hist_data, tf
                            )
                        )
                        indicators_data[f"{tf}_FIB"] = fib_result

                        # フィボナッチ出力
                        if "error" not in fib_result:
                            swing_high = fib_result.get("swing_high", "N/A")
                            swing_low = fib_result.get("swing_low", "N/A")
                            if isinstance(swing_high, (int, float)) and isinstance(
                                swing_low, (int, float)
                            ):
                                self.console.print(
                                    f"✅ {tf}: Fib High={swing_high:.4f}, "
                                    f"Low={swing_low:.4f}"
                                )
                        else:
                            self.console.print(f"⚠️ {tf}: フィボナッチ計算エラー")

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

                        # RSI出力
                        rsi_val = rsi_long_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI_LONG={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI_LONG={rsi_val}")

                        rsi_val = rsi_medium_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI_MEDIUM={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI_MEDIUM={rsi_val}")

                        rsi_val = rsi_short_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI_SHORT={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI_SHORT={rsi_val}")

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
                        bb_data = bb_result
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
                        if tf == "D1":
                            if f"{tf}_MA_LONG" in indicators_data:
                                ma_long_data = indicators_data[f"{tf}_MA_LONG"]
                                ma_long_val = ma_long_data.get("ma_long", "N/A")
                                if isinstance(ma_long_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA200={ma_long_val:.4f}"
                                    )

                            if f"{tf}_MA_MEDIUM" in indicators_data:
                                ma_medium_data = indicators_data[f"{tf}_MA_MEDIUM"]
                                ma_medium_val = ma_medium_data.get("ma_medium", "N/A")
                                if isinstance(ma_medium_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA50={ma_medium_val:.4f}"
                                    )

                        elif tf == "H4":
                            if f"{tf}_MA_MEDIUM" in indicators_data:
                                ma_medium_data = indicators_data[f"{tf}_MA_MEDIUM"]
                                ma_medium_val = ma_medium_data.get("ma_medium", "N/A")
                                if isinstance(ma_medium_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA50={ma_medium_val:.4f}"
                                    )

                            if f"{tf}_MA_SHORT" in indicators_data:
                                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                                ma_short_val = ma_short_data.get("ma_short", "N/A")
                                if isinstance(ma_short_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA20={ma_short_val:.4f}"
                                    )

                        elif tf == "H1":
                            if f"{tf}_MA_SHORT" in indicators_data:
                                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                                ma_short_val = ma_short_data.get("ma_short", "N/A")
                                if isinstance(ma_short_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA20={ma_short_val:.4f}"
                                    )
                        elif tf == "M5":
                            if f"{tf}_MA_SHORT" in indicators_data:
                                ma_short_data = indicators_data[f"{tf}_MA_SHORT"]
                                ma_short_val = ma_short_data.get("ma_short", "N/A")
                                if isinstance(ma_short_val, (int, float)):
                                    self.console.print(
                                        f"✅ {tf}: MA20={ma_short_val:.4f}"
                                    )

                        # フィボナッチ出力（フォールバック部分）
                        if f"{tf}_FIB" in indicators_data:
                            fib_data = indicators_data[f"{tf}_FIB"]
                            if "error" not in fib_data:
                                swing_high = fib_data.get("swing_high", "N/A")
                                swing_low = fib_data.get("swing_low", "N/A")
                                if isinstance(swing_high, (int, float)) and isinstance(
                                    swing_low, (int, float)
                                ):
                                    self.console.print(
                                        f"✅ {tf}: Fib High={swing_high:.4f}, "
                                        f"Low={swing_low:.4f}"
                                    )
                            else:
                                self.console.print(f"⚠️ {tf}: フィボナッチ計算エラー")

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
            self.console.print(f"❌ {currency_pair} テクニカル指標エラー: {str(e)}")
            return None

    async def generate_integrated_analysis(
        self,
        correlation_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """統合相関分析に基づくAI売買シナリオ生成"""
        self.console.print("🤖 統合AI戦略分析生成中...")

        if not self.openai_key or self.openai_key == "your_openai_api_key":
            self.console.print("⚠️ OpenAI APIキーが未設定。サンプル分析を使用。")
            return self._generate_sample_integrated_scenario(correlation_data)

        # 現在時刻
        current_time = datetime.now(self.jst).strftime("%Y年%m月%d日 %H:%M JST")

        # 相関データ抽出
        usdjpy_forecast = correlation_data.get("usdjpy_forecast", {})
        usd_analysis = correlation_data.get("usd_analysis", {})
        jpy_analysis = correlation_data.get("jpy_analysis", {})
        currency_data = correlation_data.get("currency_data", {})

        # 各通貨ペアの状況
        usdjpy_data = currency_data.get("USD/JPY", {})
        eurusd_data = currency_data.get("EUR/USD", {})
        gbpusd_data = currency_data.get("GBP/USD", {})
        eurjpy_data = currency_data.get("EUR/JPY", {})
        gbpjpy_data = currency_data.get("GBP/JPY", {})

        # 現在レート取得
        current_rate = usdjpy_data.get("rate", 0)
        day_high = usdjpy_data.get("day_high", current_rate)
        day_low = usdjpy_data.get("day_low", current_rate)

        # テクニカル指標データを文字列化（プロンプト用に簡潔化）
        technical_summary = ""
        if technical_data:
            # D1分析サマリー
            d1_summary = []
            if "D1_MA_LONG" in technical_data:
                ma_long = technical_data["D1_MA_LONG"].get("ma_long", "N/A")
                if isinstance(ma_long, (int, float)):
                    d1_summary.append(f"MA200: {ma_long:.4f}")

            if "D1_MA_MEDIUM" in technical_data:
                ma_medium = technical_data["D1_MA_MEDIUM"].get("ma_medium", "N/A")
                if isinstance(ma_medium, (int, float)):
                    d1_summary.append(f"MA50: {ma_medium:.4f}")

            if "D1_RSI_LONG" in technical_data:
                rsi_long = technical_data["D1_RSI_LONG"].get("current_value", "N/A")
                if isinstance(rsi_long, (int, float)):
                    d1_summary.append(f"RSI70: {rsi_long:.1f}")

            if "D1_MACD" in technical_data:
                macd_line = technical_data["D1_MACD"].get("macd_line", "N/A")
                if isinstance(macd_line, (int, float)):
                    d1_summary.append(f"MACD: {macd_line:.4f}")

            if "D1_BB" in technical_data:
                bb_upper = technical_data["D1_BB"].get("upper_band", "N/A")
                bb_lower = technical_data["D1_BB"].get("lower_band", "N/A")
                if isinstance(bb_upper, (int, float)) and isinstance(
                    bb_lower, (int, float)
                ):
                    d1_summary.append(
                        f"BB Upper: {bb_upper:.4f}, Lower: {bb_lower:.4f}"
                    )

            # フィボナッチ分析サマリー（D1）
            if "D1_FIB" in technical_data:
                d1_fib = technical_data["D1_FIB"]
                if "error" not in d1_fib:
                    swing_high = d1_fib.get("swing_high", "N/A")
                    swing_low = d1_fib.get("swing_low", "N/A")
                    current_position = d1_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        d1_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # H4分析サマリー
            h4_summary = []
            if "H4_MA_MEDIUM" in technical_data:
                h4_ma_medium = technical_data["H4_MA_MEDIUM"].get("ma_medium", "N/A")
                if isinstance(h4_ma_medium, (int, float)):
                    h4_summary.append(f"MA50: {h4_ma_medium:.4f}")

            if "H4_RSI_LONG" in technical_data:
                h4_rsi_long = technical_data["H4_RSI_LONG"].get("current_value", "N/A")
                if isinstance(h4_rsi_long, (int, float)):
                    h4_summary.append(f"RSI70: {h4_rsi_long:.1f}")

            # フィボナッチ分析サマリー（H4）
            if "H4_FIB" in technical_data:
                h4_fib = technical_data["H4_FIB"]
                if "error" not in h4_fib:
                    swing_high = h4_fib.get("swing_high", "N/A")
                    swing_low = h4_fib.get("swing_low", "N/A")
                    current_position = h4_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        h4_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # H1分析サマリー
            h1_summary = []
            if "H1_MA_SHORT" in technical_data:
                h1_ma_short = technical_data["H1_MA_SHORT"].get("ma_short", "N/A")
                if isinstance(h1_ma_short, (int, float)):
                    h1_summary.append(f"MA20: {h1_ma_short:.4f}")

            if "H1_RSI_LONG" in technical_data:
                h1_rsi_long = technical_data["H1_RSI_LONG"].get("current_value", "N/A")
                if isinstance(h1_rsi_long, (int, float)):
                    h1_summary.append(f"RSI70: {h1_rsi_long:.1f}")

            # フィボナッチ分析サマリー（H1）
            if "H1_FIB" in technical_data:
                h1_fib = technical_data["H1_FIB"]
                if "error" not in h1_fib:
                    swing_high = h1_fib.get("swing_high", "N/A")
                    swing_low = h1_fib.get("swing_low", "N/A")
                    current_position = h1_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        h1_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # M5分析サマリー
            m5_summary = []
            if "M5_MA_SHORT" in technical_data:
                m5_ma_short = technical_data["M5_MA_SHORT"].get("ma_short", "N/A")
                if isinstance(m5_ma_short, (int, float)):
                    m5_summary.append(f"MA20: {m5_ma_short:.4f}")

            if "M5_RSI_LONG" in technical_data:
                m5_rsi_long = technical_data["M5_RSI_LONG"].get("current_value", "N/A")
                if isinstance(m5_rsi_long, (int, float)):
                    m5_summary.append(f"RSI70: {m5_rsi_long:.1f}")

            # フィボナッチ分析サマリー（M5）
            if "M5_FIB" in technical_data:
                m5_fib = technical_data["M5_FIB"]
                if "error" not in m5_fib:
                    swing_high = m5_fib.get("swing_high", "N/A")
                    swing_low = m5_fib.get("swing_low", "N/A")
                    current_position = m5_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        m5_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # 統合サマリー
            technical_summary = f"""
D1 (Daily): {', '.join(d1_summary)}
H4 (4H): {', '.join(h4_summary)}
H1 (1H): {', '.join(h1_summary)}
M5 (5M): {', '.join(m5_summary)}
"""

        # 統合分析プロンプト作成
        prompt = f"""
あなたはプロFXトレーダーです。
通貨間の相関性とテクニカル指標を活用した統合分析に基づいて、USD/JPYの「負けないトレード」を目指した売買シナリオを2000文字以内で作成してください。
特に、上昇トレンドでの押し目買いまたは下降トレンドでの押し目売りを優先し、損切り幅を小さく、リスクリワード比率を1:2以上に設定してください。
以下のデータを基に、指示に従ってUSD/JPYの売買シナリオを分析してください。

【データ】
分析時刻: {current_time}
現在レート: {current_rate:.4f}
日中高値: {day_high:.4f}
日中安値: {day_low:.4f}
EUR/USD: {eurusd_data.get('rate', 'N/A')} \
({eurusd_data.get('market_change_percent', 'N/A')}%)
GBP/USD: {gbpusd_data.get('rate', 'N/A')} \
({gbpusd_data.get('market_change_percent', 'N/A')}%)
EUR/JPY: {eurjpy_data.get('rate', 'N/A')} \
({eurjpy_data.get('market_change_percent', 'N/A')}%)
GBP/JPY: {gbpjpy_data.get('rate', 'N/A')} \
({gbpjpy_data.get('market_change_percent', 'N/A')}%)

USD分析: {usd_analysis.get('direction', 'N/A')} \
(信頼度{usd_analysis.get('confidence', 'N/A')}%)
JPY分析: {jpy_analysis.get('direction', 'N/A')} \
(信頼度{jpy_analysis.get('confidence', 'N/A')}%)
統合予測: {usdjpy_forecast.get('forecast_direction', 'N/A')} \
(信頼度{usdjpy_forecast.get('forecast_confidence', 'N/A')}%)

{correlation_data}

{technical_summary}

【指示】
以下の手順に従って売買シナリオを作成してください：

売買シナリオ構築の手順（USD/JPYメイン）
① 長期トレンドの方向性を確認（D1）
・MA200・MA50の位置関係と傾き
→ 上昇相場なのか、下降相場なのか、レンジなのかを大きく把握。
・RSI_LONG（70期間）
→ 過熱感（買われすぎ・売られすぎ）を確認。
・フィボナッチ90日（D1）
→ 長期的な押し目・戻りの候補ゾーンを把握。
👉 この段階で「基本的なバイアス（LONG/SHORT/NEUTRAL）」を設定。

② 中期の環境認識（H4）
・移動平均線（MA50・MA20）
→ トレンド方向とクロスの有無を確認。
・MACD（H4）
→ ゴールデンクロスなら上昇継続、デッドクロスなら反落警戒。
・通貨相関（USD強弱・JPY強弱）
→ 両方が噛み合っていればシナリオの信頼度UP。
👉 「順張りで攻める」か「逆張りで反転を狙う」かをここで決定。

③ 短期シナリオ設計（H1）
・MA20 + フィボ24時間
→ 押し目買い/戻り売りの水準を具体化。
・RSI_MEDIUM（50期間）・RSI_SHORT（30期間）
→ エントリータイミングを検出（ダイバージェンスがあれば強いシグナル）。
・ボリンジャーバンド（H1）
→ バンド幅が拡大ならトレンド継続、収縮ならブレイク待ち。
👉 ここで「どこで入るか（価格帯）」と「利確・損切り候補」を明示。

④ 精密エントリー（M5）
・ボリンジャーバンド（M5）
→ バンドウォークなら順張り、反発なら逆張りスキャル。
・フィボ48期間（M5）
→ 短期の押し目・戻りを可視化。
・RSI30（M5）
→ オシレーターで直近の過熱感を確認。
👉 ここで実際のエントリータイミングを決定（指値 or 成行）。

⑤ シナリオとしてまとめる
・基本バイアス（LONG/SHORT/NEUTRAL）
→ 日足/H4のトレンドと通貨強弱で決定
・エントリーポイント
→ H1フィボ38.2% or 61.8%、RSI反発で確認
・利確ポイント
→ 固定 +30pips（2回で60pips/日目標）
→ 直近高値/安値、ボリバン上限/下限で調整
・損切りポイント
→ 直近スイングの外側（20〜30pips）
→ リスクリワード最低 1:1.5 を確保

※シナリオ分岐
ロングシナリオ：押し目買い条件が揃ったら
ショートシナリオ：戻り売り条件が揃ったら
どちらも崩れたら：その日はノートレ

⑥ AI分析レポートイメージ例（USD/JPY）
・【基本バイアス】：LONG（D1で上昇トレンド、USD強・JPY弱）
・【エントリー候補】：H1フィボ38.2%（例：150.20付近）
・【利確】：+30pips（150.50付近）
・【損切り】：直近安値の下（149.90付近）
・【オルタナティブ】：150.80で頭打ち＆RSI70反落なら戻り売り（+30pips狙い）
・【売買シナリオ分析】：売買シナリオ構築の手順①～⑤を組み合わせて作成。
"""

        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,  # 統合分析対応（トークン制限緩和）
                "temperature": 0.7,
            }

            # crontab環境でのネットワーク接続問題に対応
            timeout_config = httpx.Timeout(
                connect=10.0,  # 接続タイムアウト
                read=60.0,  # 読み取りタイムアウト
                write=10.0,  # 書き込みタイムアウト
                pool=10.0,  # プールタイムアウト
            )

            async with httpx.AsyncClient(
                timeout=timeout_config,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            ) as client:
                response = await client.post(
                    self.openai_url, headers=headers, json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    analysis = data["choices"][0]["message"]["content"].strip()
                    self.console.print("✅ 統合AI分析生成成功")
                    return analysis
                else:
                    self.console.print(f"❌ OpenAI APIエラー: {response.status_code}")
                    self.console.print(f"エラー詳細: {response.text}")
                    return None

        except httpx.ReadTimeout as e:
            self.console.print(f"⚠️ OpenAI APIタイムアウト: {str(e)}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)
        except httpx.ConnectTimeout as e:
            self.console.print(f"⚠️ OpenAI API接続タイムアウト: {str(e)}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)
        except httpx.RequestError as e:
            self.console.print(f"⚠️ OpenAI APIリクエストエラー: {str(e)}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)
        except Exception as e:
            error_details = traceback.format_exc()
            self.console.print(f"❌ 統合AI分析生成エラー: {str(e)}")
            self.console.print(f"詳細: {error_details}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)

    def _generate_sample_integrated_scenario(
        self, correlation_data: Dict[str, Any]
    ) -> str:
        """サンプル統合シナリオ生成（OpenAI APIキー未設定時）"""
        usdjpy_forecast = correlation_data.get("usdjpy_forecast", {})
        usd_analysis = correlation_data.get("usd_analysis", {})
        jpy_analysis = correlation_data.get("jpy_analysis", {})

        current_rate = usdjpy_forecast.get("current_rate", 0)
        strategy_bias = usdjpy_forecast.get("strategy_bias", "NEUTRAL")
        forecast_direction = usdjpy_forecast.get("forecast_direction", "不明")
        forecast_confidence = usdjpy_forecast.get("forecast_confidence", 0)

        return f"""
🎯 USD/JPY統合相関分析シナリオ

【相関分析】
• USD状況: {usd_analysis.get('summary', 'N/A')}
• JPY状況: {jpy_analysis.get('summary', 'N/A')}
• 統合判断: {forecast_direction} (信頼度{forecast_confidence}%)

【大局観】マルチタイムフレーム
通貨相関から{strategy_bias}バイアス想定。現在レート{current_rate:.4f}を基準に戦略立案。

【戦術】エントリーゾーン
相関要因: {', '.join(usdjpy_forecast.get('forecast_factors', ['相関データ不足']))}

【統合シナリオ】{strategy_bias}戦略
• エントリー: {current_rate:.3f}付近
• 利確目標: {current_rate + (0.5 if strategy_bias == 'LONG' else -0.5):.3f}
• 損切り: {current_rate - (0.3 if strategy_bias == 'LONG' else -0.3):.3f}

【リスク管理】
通貨相関の逆転リスクに注意。クロス通貨の急変時は即座に見直し。

【実行指示】
{strategy_bias}方向で相関分析通りなら継続、逆行なら早期撤退。

※サンプルシナリオ。実際の投資判断は慎重に行ってください。
        """.strip()

    async def send_integrated_analysis_to_discord(
        self, correlation_data: Dict[str, Any], analysis: str
    ) -> bool:
        """統合分析結果をDiscordに送信"""
        self.console.print("💬 統合分析Discord配信中...")

        if not self.discord_webhook:
            self.console.print("⚠️ Discord Webhook URLが未設定")
            return False

        # データ抽出
        usdjpy_forecast = correlation_data.get("usdjpy_forecast", {})
        usd_analysis = correlation_data.get("usd_analysis", {})
        jpy_analysis = correlation_data.get("jpy_analysis", {})

        current_rate = usdjpy_forecast.get("current_rate", 0)
        current_change = usdjpy_forecast.get("current_change_percent", 0)
        strategy_bias = usdjpy_forecast.get("strategy_bias", "NEUTRAL")
        forecast_confidence = usdjpy_forecast.get("forecast_confidence", 0)

        # 色設定（戦略バイアスに基づく）
        if strategy_bias == "LONG":
            color = 0x00FF00  # 緑色
            trend_emoji = "📈"
        elif strategy_bias == "SHORT":
            color = 0xFF0000  # 赤色
            trend_emoji = "📉"
        else:
            color = 0xFFFF00  # 黄色
            trend_emoji = "🔄"

        # AI分析結果をそのまま使用（フィールド分割で処理）
        analysis_summary = analysis

        # デバッグ用：分析結果の長さをログ出力
        self.console.print(f"🔍 AI分析結果の長さ: {len(analysis_summary)}文字")
        self.console.print(f"🔍 AI分析結果の先頭100文字: {analysis_summary[:100]}...")

        # 分析結果を複数のフィールドに分割
        fields = [
            {
                "name": "💱 USD/JPY レート",
                "value": f"**{current_rate:.4f}** ({current_change:+.2f}%)",
                "inline": True,
            },
            {
                "name": "🎯 戦略バイアス",
                "value": f"**{strategy_bias}**",
                "inline": True,
            },
            {
                "name": "📊 予測信頼度",
                "value": f"**{forecast_confidence}%**",
                "inline": True,
            },
            {
                "name": "💵 USD分析",
                "value": (
                    f"{usd_analysis.get('direction', 'N/A')} "
                    f"({usd_analysis.get('confidence', 0)}%)"
                ),
                "inline": True,
            },
            {
                "name": "💴 JPY分析",
                "value": (
                    f"{jpy_analysis.get('direction', 'N/A')} "
                    f"({jpy_analysis.get('confidence', 0)}%)"
                ),
                "inline": True,
            },
            {
                "name": "🔗 相関要因",
                "value": ", ".join(
                    usdjpy_forecast.get("forecast_factors", ["N/A"])[:2]
                ),  # 最大2個
                "inline": True,
            },
        ]

        # 分析結果を複数のフィールドに分割（各1024文字以内）
        if len(analysis_summary) > 1024:
            # 重要なセクションを抽出して分割
            sections = []
            if "【統合シナリオ】" in analysis_summary:
                scenario_start = analysis_summary.find("【統合シナリオ】")
                # 【統合シナリオ】は最後のセクションなので、次のセクションを探す
                scenario_end = analysis_summary.find("【", scenario_start + 1)
                if scenario_end == -1:
                    # 次のセクションがない場合、テクニカルサマリーの開始位置を探す
                    tech_summary_start = analysis_summary.find("📊 テクニカルサマリー")
                    if tech_summary_start != -1:
                        scenario_end = tech_summary_start
                    else:
                        scenario_end = len(analysis_summary)
                scenario_text = analysis_summary[scenario_start:scenario_end]
                # 【統合シナリオ】のタイトルを除去して内容のみを取得
                if scenario_text.startswith("【統合シナリオ】"):
                    scenario_text = scenario_text[len("【統合シナリオ】") :].strip()
                if len(scenario_text) > 1024:
                    scenario_text = scenario_text[:1024] + "..."
                sections.append(("🎯 統合シナリオ", scenario_text))

            if "【戦術】" in analysis_summary:
                tactics_start = analysis_summary.find("【戦術】")
                tactics_end = analysis_summary.find("【", tactics_start + 1)
                if tactics_end == -1:
                    tactics_end = len(analysis_summary)
                tactics_text = analysis_summary[tactics_start:tactics_end]
                # 【戦術】のタイトルを除去して内容のみを取得
                if tactics_text.startswith("【戦術】"):
                    tactics_text = tactics_text[len("【戦術】") :].strip()
                if len(tactics_text) > 1024:
                    tactics_text = tactics_text[:1024] + "..."
                sections.append(("⚡ 戦術分析", tactics_text))

            if "【大局観】" in analysis_summary:
                overview_start = analysis_summary.find("【大局観】")
                overview_end = analysis_summary.find("【", overview_start + 1)
                if overview_end == -1:
                    overview_end = len(analysis_summary)
                overview_text = analysis_summary[overview_start:overview_end]
                # 【大局観】のタイトルを除去して内容のみを取得
                if overview_text.startswith("【大局観】"):
                    overview_text = overview_text[len("【大局観】") :].strip()
                if len(overview_text) > 1024:
                    overview_text = overview_text[:1024] + "..."
                sections.append(("📊 大局観", overview_text))

            # セクションをフィールドに追加
            for section_name, section_text in sections:
                fields.append(
                    {
                        "name": section_name,
                        "value": section_text,
                        "inline": False,
                    }
                )

            # セクションが見つからない場合は、分析結果全体を分割して追加
            if not sections:
                self.console.print(
                    "⚠️ セクションが見つからないため、分析結果全体を分割して追加"
                )
                # 分析結果を1024文字ずつに分割
                chunks = [
                    analysis_summary[i : i + 1024]
                    for i in range(0, len(analysis_summary), 1024)
                ]
                for i, chunk in enumerate(chunks):
                    fields.append(
                        {
                            "name": f"🎯 AI分析結果 (Part {i+1})",
                            "value": chunk,
                            "inline": False,
                        }
                    )
        else:
            # 短い場合は1つのフィールドに
            fields.append(
                {
                    "name": "🎯 統合売買シナリオ",
                    "value": analysis_summary,
                    "inline": False,
                }
            )

        embed_data = {
            "content": f"{trend_emoji} **🎯 USD/JPY統合相関戦略**",
            "embeds": [
                {
                    "title": "🔗 Integrated Currency Correlation Strategy",
                    "description": "通貨間相関性を活用したUSD/JPY売買シナリオ",
                    "color": color,
                    "fields": fields,
                    "footer": {
                        "text": (
                            "Integrated Currency Correlation Analysis | "
                            "Multi-Currency Strategy"
                        )
                    },
                    "timestamp": datetime.now(self.jst).isoformat(),
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.discord_webhook, json=embed_data)

                if response.status_code == 204:
                    self.console.print("✅ 統合分析Discord配信成功")
                    return True
                else:
                    self.console.print(f"❌ Discord配信失敗: {response.status_code}")
                    self.console.print(f"レスポンス: {response.text}")
                    return False

        except Exception as e:
            self.console.print(f"❌ Discord配信エラー: {str(e)}")
            return False

    async def generate_and_send_integrated_report(self) -> bool:
        """統合相関分析レポート生成・配信"""
        self.console.print("🚀 統合相関分析レポート生成・配信開始")
        self.console.print(
            f"🕘 日本時間: {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M:%S JST')}"
        )

        try:
            # Step 1: 通貨相関分析実行
            correlation_data = (
                await self.correlation_analyzer.perform_integrated_analysis()
            )
            if "error" in correlation_data:
                self.console.print("❌ 通貨相関分析失敗")
                return False

            # 相関分析結果を表示
            self.correlation_analyzer.display_correlation_analysis(correlation_data)

            # Step 2: USD/JPYテクニカル指標取得
            technical_data = await self._fetch_technical_indicators("USD/JPY")

            # Step 3: 統合AI分析生成
            analysis_result = await self.generate_integrated_analysis(
                correlation_data, technical_data
            )
            if not analysis_result:
                self.console.print("❌ 統合AI分析生成失敗")
                return False

            # Step 3: Discord配信
            discord_success = await self.send_integrated_analysis_to_discord(
                correlation_data, analysis_result
            )
            if discord_success:
                self.console.print("✅ 統合相関分析レポート配信成功")
                return True
            else:
                self.console.print("❌ Discord配信失敗")
                return False

        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = (
                f"❌ 統合レポート生成・配信エラー: {str(e)}\n詳細: {error_details}"
            )
            self.console.print(error_msg)

            # エラー通知をDiscordに送信
            try:
                if self.discord_webhook:
                    embed_data = {
                        "content": "🚨 **AI分析レポート配信エラー**",
                        "embeds": [
                            {
                                "title": "❌ Integrated AI Report Error",
                                "description": f"```\n{error_msg[:4000]}\n```",
                                "color": 0xFF0000,
                                "timestamp": datetime.now(self.jst).isoformat(),
                            }
                        ],
                    }
                    # crontab環境でのネットワーク接続問題に対応
                    timeout_config = httpx.Timeout(
                        connect=5.0,  # 接続タイムアウト
                        read=30.0,  # 読み取りタイムアウト
                        write=5.0,  # 書き込みタイムアウト
                        pool=5.0,  # プールタイムアウト
                    )

                    async with httpx.AsyncClient(
                        timeout=timeout_config,
                        limits=httpx.Limits(
                            max_keepalive_connections=3, max_connections=5
                        ),
                    ) as client:
                        await client.post(self.discord_webhook, json=embed_data)
                    self.console.print("✅ エラー通知をDiscordに送信しました")
            except Exception as notify_error:
                self.console.print(f"⚠️ エラー通知送信失敗: {notify_error}")

            return False


async def main():
    """メイン実行関数（最適化版）"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrated AI Discord Reporter (Optimized)"
    )
    parser.add_argument(
        "--test", action="store_true", help="テストモード（Discordに送信しない）"
    )
    parser.add_argument(
        "--no-optimization", action="store_true", help="最適化機能を無効にする"
    )

    args = parser.parse_args()

    # 環境変数読み込み
    if os.path.exists("/app/.env"):
        with open("/app/.env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                    except ValueError:
                        pass

    reporter = IntegratedAIDiscordReporter()

    # 最適化コンポーネント初期化
    if not args.no_optimization:
        try:
            await reporter.initialize_optimization_components()
            reporter.console.print("🚀 最適化機能が有効です")
        except Exception as e:
            reporter.console.print(f"⚠️ 最適化機能初期化失敗: {str(e)}")
            reporter.console.print("📝 従来モードで実行します")
    else:
        reporter.console.print("📝 最適化機能を無効にして実行します")

    if args.test:
        reporter.console.print("🧪 テストモード: Discord配信をスキップ")
        # 通貨相関分析、テクニカル指標、AI分析まで実行
        correlation_data = (
            await reporter.correlation_analyzer.perform_integrated_analysis()
        )
        if "error" not in correlation_data:
            reporter.correlation_analyzer.display_correlation_analysis(correlation_data)

            # テクニカル指標取得
            technical_data = await reporter._fetch_technical_indicators("USD/JPY")

            # 統合AI分析
            analysis = await reporter.generate_integrated_analysis(
                correlation_data, technical_data
            )
            if analysis:
                reporter.console.print("📋 統合AI分析結果:")
                reporter.console.print(f"[cyan]{analysis}[/cyan]")
            else:
                reporter.console.print("⚠️ AI分析はスキップ（API制限のため）")

            # technical_summaryの表示（テスト用）
            if technical_data:
                reporter.console.print("\n📊 テクニカルサマリー（AIプロンプト用）:")
                # technical_summaryの生成（generate_integrated_analysisメソッドの一部を再現）
                technical_summary = ""
                if technical_data:
                    # D1分析サマリー
                    d1_summary = []
                    if "D1_MA_LONG" in technical_data:
                        ma_long = technical_data["D1_MA_LONG"].get("ma_long", "N/A")
                        if isinstance(ma_long, (int, float)):
                            d1_summary.append(f"MA200: {ma_long:.4f}")
                    if "D1_MA_MEDIUM" in technical_data:
                        ma_medium = technical_data["D1_MA_MEDIUM"].get(
                            "ma_medium", "N/A"
                        )
                        if isinstance(ma_medium, (int, float)):
                            d1_summary.append(f"MA50: {ma_medium:.4f}")
                    if "D1_FIB" in technical_data:
                        d1_fib = technical_data["D1_FIB"]
                        if "error" not in d1_fib:
                            swing_high = d1_fib.get("swing_high", "N/A")
                            swing_low = d1_fib.get("swing_low", "N/A")
                            current_position = d1_fib.get("current_position", {})
                            if isinstance(swing_high, (int, float)) and isinstance(
                                swing_low, (int, float)
                            ):
                                position_info = ""
                                if isinstance(current_position, dict):
                                    percentage = current_position.get(
                                        "percentage", "N/A"
                                    )
                                    nearest_level = current_position.get(
                                        "nearest_level", "N/A"
                                    )
                                    # 各フィボナッチレベルの価格を表示（サポート/レジスタンス分類）
                                    levels_info = ""
                                    if "levels" in d1_fib:
                                        levels = d1_fib["levels"]
                                        current_price = d1_fib.get("current_price", 0)
                                        if isinstance(levels, dict):
                                            support_levels = []
                                            resistance_levels = []

                                            for (
                                                level_name,
                                                level_price,
                                            ) in levels.items():
                                                if isinstance(
                                                    level_price, (int, float)
                                                ):
                                                    if level_price < current_price:
                                                        support_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )
                                                    else:
                                                        resistance_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )

                                            if support_levels:
                                                levels_info += (
                                                    f" | サポート: "
                                                    f"{', '.join(support_levels)}"
                                                )
                                            if resistance_levels:
                                                levels_info += (
                                                    f" | レジスタンス: "
                                                    f"{', '.join(resistance_levels)}"
                                                )
                                    position_info = (
                                        f" (現在位置: {percentage}%){levels_info}"
                                    )
                                d1_summary.append(
                                    f"Fib High: {swing_high:.4f}, "
                                    f"Low: {swing_low:.4f}{position_info}"
                                )

                    # H4分析サマリー
                    h4_summary = []
                    if "H4_FIB" in technical_data:
                        h4_fib = technical_data["H4_FIB"]
                        if "error" not in h4_fib:
                            swing_high = h4_fib.get("swing_high", "N/A")
                            swing_low = h4_fib.get("swing_low", "N/A")
                            current_position = h4_fib.get("current_position", {})
                            if isinstance(swing_high, (int, float)) and isinstance(
                                swing_low, (int, float)
                            ):
                                position_info = ""
                                if isinstance(current_position, dict):
                                    percentage = current_position.get(
                                        "percentage", "N/A"
                                    )
                                    # 各フィボナッチレベルの価格を表示（サポート/レジスタンス分類）
                                    levels_info = ""
                                    if "levels" in h4_fib:
                                        levels = h4_fib["levels"]
                                        current_price = h4_fib.get("current_price", 0)
                                        if isinstance(levels, dict):
                                            support_levels = []
                                            resistance_levels = []

                                            for (
                                                level_name,
                                                level_price,
                                            ) in levels.items():
                                                if isinstance(
                                                    level_price, (int, float)
                                                ):
                                                    if level_price < current_price:
                                                        support_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )
                                                    else:
                                                        resistance_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )

                                            if support_levels:
                                                levels_info += (
                                                    f" | サポート: "
                                                    f"{', '.join(support_levels)}"
                                                )
                                            if resistance_levels:
                                                levels_info += (
                                                    f" | レジスタンス: "
                                                    f"{', '.join(resistance_levels)}"
                                                )
                                    position_info = (
                                        f" (現在位置: {percentage}%){levels_info}"
                                    )
                                h4_summary.append(
                                    f"Fib High: {swing_high:.4f}, "
                                    f"Low: {swing_low:.4f}{position_info}"
                                )

                    # H1分析サマリー
                    h1_summary = []
                    if "H1_FIB" in technical_data:
                        h1_fib = technical_data["H1_FIB"]
                        if "error" not in h1_fib:
                            swing_high = h1_fib.get("swing_high", "N/A")
                            swing_low = h1_fib.get("swing_low", "N/A")
                            current_position = h1_fib.get("current_position", {})
                            if isinstance(swing_high, (int, float)) and isinstance(
                                swing_low, (int, float)
                            ):
                                position_info = ""
                                if isinstance(current_position, dict):
                                    percentage = current_position.get(
                                        "percentage", "N/A"
                                    )
                                    # 各フィボナッチレベルの価格を表示（サポート/レジスタンス分類）
                                    levels_info = ""
                                    if "levels" in h1_fib:
                                        levels = h1_fib["levels"]
                                        current_price = h1_fib.get("current_price", 0)
                                        if isinstance(levels, dict):
                                            support_levels = []
                                            resistance_levels = []

                                            for (
                                                level_name,
                                                level_price,
                                            ) in levels.items():
                                                if isinstance(
                                                    level_price, (int, float)
                                                ):
                                                    if level_price < current_price:
                                                        support_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )
                                                    else:
                                                        resistance_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )

                                            if support_levels:
                                                levels_info += (
                                                    f" | サポート: "
                                                    f"{', '.join(support_levels)}"
                                                )
                                            if resistance_levels:
                                                levels_info += (
                                                    f" | レジスタンス: "
                                                    f"{', '.join(resistance_levels)}"
                                                )
                                    position_info = (
                                        f" (現在位置: {percentage}%){levels_info}"
                                    )
                                h1_summary.append(
                                    f"Fib High: {swing_high:.4f}, "
                                    f"Low: {swing_low:.4f}{position_info}"
                                )

                    # M5分析サマリー
                    m5_summary = []
                    if "M5_FIB" in technical_data:
                        m5_fib = technical_data["M5_FIB"]
                        if "error" not in m5_fib:
                            swing_high = m5_fib.get("swing_high", "N/A")
                            swing_low = m5_fib.get("swing_low", "N/A")
                            current_position = m5_fib.get("current_position", {})
                            if isinstance(swing_high, (int, float)) and isinstance(
                                swing_low, (int, float)
                            ):
                                position_info = ""
                                if isinstance(current_position, dict):
                                    percentage = current_position.get(
                                        "percentage", "N/A"
                                    )
                                    # 各フィボナッチレベルの価格を表示（サポート/レジスタンス分類）
                                    levels_info = ""
                                    if "levels" in m5_fib:
                                        levels = m5_fib["levels"]
                                        current_price = m5_fib.get("current_price", 0)
                                        if isinstance(levels, dict):
                                            support_levels = []
                                            resistance_levels = []

                                            for (
                                                level_name,
                                                level_price,
                                            ) in levels.items():
                                                if isinstance(
                                                    level_price, (int, float)
                                                ):
                                                    if level_price < current_price:
                                                        support_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )
                                                    else:
                                                        resistance_levels.append(
                                                            f"{level_name}: "
                                                            f"{level_price:.4f}"
                                                        )

                                            if support_levels:
                                                levels_info += (
                                                    f" | サポート: "
                                                    f"{', '.join(support_levels)}"
                                                )
                                            if resistance_levels:
                                                levels_info += (
                                                    f" | レジスタンス: "
                                                    f"{', '.join(resistance_levels)}"
                                                )
                                    position_info = (
                                        f" (現在位置: {percentage}%){levels_info}"
                                    )
                                m5_summary.append(
                                    f"Fib High: {swing_high:.4f}, "
                                    f"Low: {swing_low:.4f}{position_info}"
                                )

                    technical_summary = f"""
D1 (Daily): {', '.join(d1_summary)}
H4 (4H): {', '.join(h4_summary)}
H1 (1H): {', '.join(h1_summary)}
M5 (5M): {', '.join(m5_summary)}
"""
                reporter.console.print(f"[cyan]{technical_summary}[/cyan]")

                # テクニカル指標の詳細表示
                if technical_data:
                    reporter.console.print("\n🔍 テクニカル指標詳細:")
                    for key, data in technical_data.items():
                        if isinstance(data, dict):
                            reporter.console.print(f"[yellow]{key}:[/yellow] {data}")

                    # フィボナッチデータの詳細表示
                    reporter.console.print("\n🎯 フィボナッチ分析詳細:")
                    for key, data in technical_data.items():
                        if "FIB" in key and isinstance(data, dict):
                            current_position = data.get("current_position", {})
                            if isinstance(current_position, dict):
                                percentage = current_position.get("percentage", "N/A")
                                nearest_level = current_position.get(
                                    "nearest_level", "N/A"
                                )
                                position = current_position.get("position", "N/A")
                                reporter.console.print(
                                    f"[green]{key}:[/green] 現在位置: {percentage}%, "
                                    f"最寄りレベル: {nearest_level}, 位置: {position}"
                                )
                            else:
                                reporter.console.print(
                                    f"[green]{key}:[/green] {current_position}"
                                )

                # 統計情報表示
                if reporter.notification_manager:
                    try:
                        stats = await (
                            reporter.notification_manager.get_notification_statistics()
                        )
                        reporter.console.print("📊 通知統計情報:")
                        reporter.console.print(f"[yellow]{stats}[/yellow]")
                    except Exception as e:
                        # データベース接続エラーの場合は詳細を表示しない
                        if "Connect call failed" in str(e):
                            reporter.console.print("📊 統計情報: データベース接続なし")
                        else:
                            reporter.console.print(f"⚠️ 統計情報取得エラー: {str(e)}")

                reporter.console.print("✅ テスト完了")
            else:
                reporter.console.print("❌ AI分析生成失敗")
        else:
            reporter.console.print("❌ 相関分析失敗")
    else:
        await reporter.generate_and_send_integrated_report()

    # セッションクローズ
    await reporter.close_session()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        error_msg = f"❌ AI分析レポート実行エラー: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)

        # エラー通知をDiscordに送信
        try:
            discord_webhook = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if discord_webhook:
                embed_data = {
                    "content": "🚨 **AI分析レポート実行エラー**",
                    "embeds": [
                        {
                            "title": "❌ Integrated AI Discord Reporter Error",
                            "description": f"```\n{error_msg[:4000]}\n```",
                            "color": 0xFF0000,
                            "timestamp": datetime.now(
                                pytz.timezone("Asia/Tokyo")
                            ).isoformat(),
                        }
                    ],
                }
                import asyncio

                async def send_error():
                    # crontab環境でのネットワーク接続問題に対応
                    timeout_config = httpx.Timeout(
                        connect=5.0,  # 接続タイムアウト
                        read=30.0,  # 読み取りタイムアウト
                        write=5.0,  # 書き込みタイムアウト
                        pool=5.0,  # プールタイムアウト
                    )

                    async with httpx.AsyncClient(
                        timeout=timeout_config,
                        limits=httpx.Limits(
                            max_keepalive_connections=3, max_connections=5
                        ),
                    ) as client:
                        await client.post(discord_webhook, json=embed_data)

                asyncio.run(send_error())
                print("✅ エラー通知をDiscordに送信しました")
        except Exception as notify_error:
            print(f"⚠️ エラー通知送信失敗: {notify_error}")

        exit(1)

        exit(1)
