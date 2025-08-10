#!/usr/bin/env python3
"""
Integrated AI Discord Reporter
通貨相関性を活用した統合AI分析Discord配信システム
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import pytz
from rich.console import Console

# プロジェクトパス追加
sys.path.append("/app")
from src.infrastructure.analysis.currency_correlation_analyzer import (
    CurrencyCorrelationAnalyzer,
)
from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.cache.analysis_cache import AnalysisCacheManager
from src.infrastructure.cache.cache_manager import CacheManager
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories.analysis_cache_repository_impl import (
    AnalysisCacheRepositoryImpl,
)
from src.infrastructure.database.repositories.notification_history_repository_impl import (
    NotificationHistoryRepositoryImpl,
)
from src.infrastructure.messaging.discord_client import DiscordClient
from src.infrastructure.messaging.notification_manager import NotificationManager
from src.infrastructure.optimization.api_rate_limiter import ApiRateLimiter
from src.infrastructure.optimization.batch_processor import BatchProcessor
from src.infrastructure.optimization.data_optimizer import DataOptimizer


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
            self.console.print(f"❌ 最適化コンポーネント初期化エラー: {str(e)}")
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
            # キャッシュチェック（一時的に無効化してテクニカル指標計算を確認）
            if self.analysis_cache:
                # キャッシュを無効化して強制的に再計算
                try:
                    await self.analysis_cache.invalidate_analysis(
                        "technical_indicators", currency_pair
                    )
                    self.console.print(f"🔄 {currency_pair} キャッシュ無効化、再計算実行")
                except Exception as e:
                    self.console.print(f"⚠️ キャッシュ無効化エラー: {str(e)}")
                    self.console.print(f"🔄 {currency_pair} 強制再計算実行")
                cached_data = None
            else:
                cached_data = None

            # 複数期間の履歴データ取得（最適化版）
            timeframes = {
                "D1": ("3mo", "1d"),  # 3ヶ月、日足
                "H4": ("1mo", "1h"),  # 1ヶ月、1時間足
                "H1": ("1wk", "1h"),  # 1週間、1時間足
            }

            indicators_data = {}

            # データ最適化器を使用して効率的にデータ取得
            if self.data_optimizer:
                for tf, (period, interval) in timeframes.items():
                    hist_data = await self.data_optimizer.get_historical_dataframe(
                        currency_pair, period, interval
                    )
                    if hist_data is not None and not hist_data.empty:
                        # RSI計算
                        rsi_result = self.technical_analyzer.calculate_rsi(
                            hist_data, tf
                        )

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

                        indicators_data[f"{tf}_RSI"] = rsi_result
                        indicators_data[f"{tf}_BB"] = bb_result

                        # RSI出力
                        rsi_val = rsi_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI={rsi_val}")

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
                                    f"✅ {tf}: MACD={macd_line:.4f}, Signal={signal_line:.4f}, Hist={histogram:.4f}"
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
                                f"✅ {tf}: BB Upper={upper_band:.4f}, Middle={middle_band:.4f}, Lower={lower_band:.4f}"
                            )
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
                        # RSI計算
                        rsi_result = self.technical_analyzer.calculate_rsi(
                            hist_data, tf
                        )

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

                        indicators_data[f"{tf}_RSI"] = rsi_result
                        indicators_data[f"{tf}_BB"] = bb_result

                        # RSI出力
                        rsi_val = rsi_result.get("current_value", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            self.console.print(f"✅ {tf}: RSI={rsi_val:.1f}")
                        else:
                            self.console.print(f"✅ {tf}: RSI={rsi_val}")

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
                                    f"✅ {tf}: MACD={macd_line:.4f}, Signal={signal_line:.4f}, Hist={histogram:.4f}"
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
                                f"✅ {tf}: BB Upper={upper_band:.4f}, Middle={middle_band:.4f}, Lower={lower_band:.4f}"
                            )
                    else:
                        self.console.print(f"❌ {tf}: 履歴データ取得失敗")

            # 結果をキャッシュに保存
            if indicators_data and self.analysis_cache:
                await self.analysis_cache.set_analysis(
                    "technical_indicators",
                    currency_pair,
                    indicators_data,
                    "multi_timeframe",
                )

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

        # テクニカル指標データを文字列化
        technical_info = ""
        if technical_data:
            technical_info = "\n【USD/JPYテクニカル指標】"
            for key, data in technical_data.items():
                if isinstance(data, dict):
                    if "RSI" in key:
                        rsi_val = data.get("current_value", "N/A")
                        rsi_state = data.get("state", "N/A")
                        if isinstance(rsi_val, (int, float)):
                            technical_info += f"\n{key}: {rsi_val:.1f} ({rsi_state})"
                        else:
                            technical_info += f"\n{key}: {rsi_val} ({rsi_state})"
                    elif "MACD" in key:
                        macd_line = data.get("macd_line", "N/A")
                        signal_line = data.get("signal_line", "N/A")
                        cross_signal = data.get("cross_signal", "N/A")
                        if isinstance(macd_line, (int, float)) and isinstance(
                            signal_line, (int, float)
                        ):
                            technical_info += f"\n{key}: MACD={macd_line:.4f}, Signal={signal_line:.4f}, Cross={cross_signal}"
                        else:
                            technical_info += f"\n{key}: MACD={macd_line}, Signal={signal_line}, Cross={cross_signal}"
                    elif "BB" in key:
                        bb_position = data.get("band_position", "N/A")
                        bb_signal = data.get("band_walk", "N/A")
                        technical_info += f"\n{key}: {bb_position} ({bb_signal})"

        # 統合分析プロンプト作成
        prompt = f"""
あなたは経験豊富なプロFXトレーダーかつ親切な投資教育者です。FX初学者にも理解できるよう、専門用語には必ず説明を付けながら、通貨間の相関性とテクニカル指標を活用した統合分析に基づいて、USD/JPY の実践的な売買シナリオを作成してください。

【統合相関分析結果】
分析時刻: {current_time}

◆ USD/JPY メイン通貨ペア
現在レート: {current_rate}
変動: {usdjpy_data.get('market_change', 'N/A')} ({usdjpy_data.get('market_change_percent', 'N/A')}%)
日中高値: {day_high}
日中安値: {day_low}{technical_info}

◆ USD強弱分析
方向性: {usd_analysis.get('direction', 'N/A')} (信頼度{usd_analysis.get('confidence', 'N/A')}%)
サポート要因: {', '.join(usd_analysis.get('supporting_pairs', []))}
リスク要因: {', '.join(usd_analysis.get('conflicting_pairs', []))}
EUR/USD: {eurusd_data.get('rate', 'N/A')} ({eurusd_data.get('market_change_percent', 'N/A')}%)
GBP/USD: {gbpusd_data.get('rate', 'N/A')} ({gbpusd_data.get('market_change_percent', 'N/A')}%)

◆ JPY強弱分析
方向性: {jpy_analysis.get('direction', 'N/A')} (信頼度{jpy_analysis.get('confidence', 'N/A')}%)
サポート要因: {', '.join(jpy_analysis.get('supporting_pairs', []))}
リスク要因: {', '.join(jpy_analysis.get('conflicting_pairs', []))}
EUR/JPY: {eurjpy_data.get('rate', 'N/A')} ({eurjpy_data.get('market_change_percent', 'N/A')}%)
GBP/JPY: {gbpjpy_data.get('rate', 'N/A')} ({gbpjpy_data.get('market_change_percent', 'N/A')}%)

◆ 統合予測
予測方向: {usdjpy_forecast.get('forecast_direction', 'N/A')} (信頼度{usdjpy_forecast.get('forecast_confidence', 'N/A')}%)
戦略バイアス: {usdjpy_forecast.get('strategy_bias', 'N/A')}
トレンド整合: {usdjpy_forecast.get('trend_alignment', 'N/A')}
相関要因: {', '.join(usdjpy_forecast.get('forecast_factors', []))}

【戦略要求】
上記の通貨相関分析とテクニカル指標を踏まえ、以下の形式で1600文字以内の統合売買シナリオを作成：

【相関分析】他通貨の動きから見るUSD/JPY方向性
【大局観】D1・H4マルチタイムフレーム分析（※テクニカル指標含む）
【戦術】H1エントリーゾーン・タイミング分析
【統合シナリオ】相関性とテクニカル指標を考慮した売買戦略・具体的価格指示
 ・エントリー価格: ○○.○○○○（具体的な4桁価格）
 ・利確目標: ○○.○○○○（〇〇pips※利益）
 ・損切り価格: ○○.○○○○（〇〇pips※損失）
【リスク管理】通貨相関リスク・ダイバージェンス※警戒
【実行指示】初学者向け実践的トレード指示。ただし「初学者」という言葉は使わない。

※専門用語解説：
・pips: 通貨ペアの最小価格単位（USD/JPYなら0.01円=1pip）
・ダイバージェンス: 価格とテクニカル指標の動きが逆行する現象
・その他専門用語があれば簡潔に説明

「EUR/USDがこうだから」「クロス円がこうだから」「テクニカル指標がこうだから」「だからUSD/JPYはこう動く可能性が高い」という統合的で根拠のある分析を重視し、必ず具体的な価格（小数点以下4桁）とpips数を明記してください。
"""

        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1200,  # 統合分析対応
                "temperature": 0.7,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
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

        except Exception as e:
            self.console.print(f"❌ 統合AI分析生成エラー: {str(e)}")
            return None

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

        embed_data = {
            "content": f"{trend_emoji} **🎯 USD/JPY統合相関戦略**",
            "embeds": [
                {
                    "title": "🔗 Integrated Currency Correlation Strategy",
                    "description": "通貨間相関性を活用したUSD/JPY売買シナリオ",
                    "color": color,
                    "fields": [
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
                            "value": f"{usd_analysis.get('direction', 'N/A')} ({usd_analysis.get('confidence', 0)}%)",
                            "inline": True,
                        },
                        {
                            "name": "💴 JPY分析",
                            "value": f"{jpy_analysis.get('direction', 'N/A')} ({jpy_analysis.get('confidence', 0)}%)",
                            "inline": True,
                        },
                        {
                            "name": "🔗 相関要因",
                            "value": ", ".join(
                                usdjpy_forecast.get("forecast_factors", ["N/A"])[:2]
                            ),  # 最大2個
                            "inline": True,
                        },
                        {
                            "name": "🎯 統合売買シナリオ",
                            "value": analysis[:1000],  # Discord制限対応
                            "inline": False,
                        },
                    ],
                    "footer": {
                        "text": "Integrated Currency Correlation Analysis | Multi-Currency Strategy"
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
            self.console.print(f"❌ 統合レポート生成・配信エラー: {str(e)}")
            return False


async def main():
    """メイン実行関数（最適化版）"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrated AI Discord Reporter (Optimized)"
    )
    parser.add_argument("--test", action="store_true", help="テストモード（Discordに送信しない）")
    parser.add_argument("--no-optimization", action="store_true", help="最適化機能を無効にする")

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

                # 統計情報表示
                if reporter.notification_manager:
                    stats = (
                        await reporter.notification_manager.get_notification_statistics()
                    )
                    reporter.console.print("📊 通知統計情報:")
                    reporter.console.print(f"[yellow]{stats}[/yellow]")

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
    asyncio.run(main())
