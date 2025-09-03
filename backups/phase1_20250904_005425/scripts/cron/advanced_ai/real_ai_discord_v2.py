#!/usr/bin/env python3
"""
実際のGPT分析結果をDiscordに配信 (Yahoo Finance版)
Yahoo Finance実データ + OpenAI GPT分析 + Discord配信の統合
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
from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


class RealAIDiscordReporter:
    """実AI分析Discord配信システム (Yahoo Finance版)"""

    def __init__(self):
        self.console = Console()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

        # API URLs
        self.openai_url = "https://api.openai.com/v1/chat/completions"

        # Yahoo Finance クライアント初期化
        self.yahoo_client = YahooFinanceClient()

        # テクニカル指標アナライザー初期化
        self.technical_analyzer = TechnicalIndicatorsAnalyzer()

        self.jst = pytz.timezone("Asia/Tokyo")

    async def generate_and_send_real_report(self, currency_pair: str = "USD/JPY"):
        """実データを使用してAI分析レポートを生成・配信"""
        self.console.print(f"🚀 実AI分析レポート生成・配信開始")
        self.console.print(f"💱 通貨ペア: {currency_pair}")
        self.console.print(
            f"🕘 日本時間: {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M:%S JST')}"
        )

        try:
            # Step 1: Yahoo Finance から実データ取得
            market_data = await self._fetch_real_market_data(currency_pair)
            if not market_data:
                self.console.print("❌ 市場データ取得失敗")
                return False

            # Step 2: テクニカル指標データ取得
            technical_data = await self._fetch_technical_indicators(currency_pair)

            # Step 3: OpenAI GPT で実際の分析
            analysis_result = await self._generate_real_ai_analysis(
                currency_pair, market_data, technical_data
            )
            if not analysis_result:
                self.console.print("❌ AI分析生成失敗")
                return False

            # Step 3: Discord に配信
            discord_success = await self._send_to_discord(
                currency_pair, market_data, analysis_result
            )
            if discord_success:
                self.console.print("✅ 実AI分析レポート配信成功")
                return True
            else:
                self.console.print("❌ Discord配信失敗")
                return False

        except Exception as e:
            self.console.print(f"❌ レポート生成・配信エラー: {str(e)}")
            return False

    async def _fetch_real_market_data(
        self, currency_pair: str
    ) -> Optional[Dict[str, Any]]:
        """Yahoo Finance から実際の市場データを取得"""
        self.console.print("📊 Yahoo Finance から実データ取得中...")

        try:
            # Yahoo Finance から現在レート取得
            rates_data = await self.yahoo_client.get_multiple_rates([currency_pair])

            if (
                rates_data
                and "rates" in rates_data
                and currency_pair in rates_data["rates"]
            ):
                rate_info = rates_data["rates"][currency_pair]

                market_data = {
                    "rate": rate_info.get("rate", 0),
                    "bid": rate_info.get("bid"),
                    "ask": rate_info.get("ask"),
                    "market_change": rate_info.get("market_change", 0),
                    "market_change_percent": rate_info.get("market_change_percent", 0),
                    "day_high": rate_info.get("day_high"),
                    "day_low": rate_info.get("day_low"),
                    "last_update": rate_info.get("last_update"),
                    "data_source": "Yahoo Finance",
                }

                self.console.print(f"✅ {currency_pair}: {market_data['rate']:.4f}")
                return market_data
            else:
                self.console.print("❌ Yahoo Finance データ取得失敗")
                return None

        except Exception as e:
            self.console.print(f"❌ データ取得エラー: {str(e)}")
            return None

    async def _fetch_technical_indicators(
        self, currency_pair: str
    ) -> Optional[Dict[str, Any]]:
        """テクニカル指標データを取得"""
        self.console.print("📈 テクニカル指標分析中...")

        try:
            # 複数期間の履歴データ取得
            timeframes = {
                "D1": ("3mo", "1d"),  # 3ヶ月、日足
                "H4": ("1mo", "1h"),  # 1ヶ月、4時間足（1時間足データから分析）
                "H1": ("1wk", "1h"),  # 1週間、1時間足
            }

            indicators_data = {}
            for tf, (period, interval) in timeframes.items():
                hist_data = await self.yahoo_client.get_historical_data(
                    currency_pair, period, interval
                )
                if hist_data is not None and not hist_data.empty:
                    # RSI計算
                    rsi_result = self.technical_analyzer.calculate_rsi(hist_data, tf)

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

                    rsi_val = rsi_result.get("current_value", "N/A")
                    if isinstance(rsi_val, (int, float)):
                        self.console.print(f"✅ {tf}: RSI={rsi_val:.1f}")
                    else:
                        self.console.print(f"✅ {tf}: RSI={rsi_val}")
                else:
                    self.console.print(f"❌ {tf}: 履歴データ取得失敗")

            return indicators_data if indicators_data else None

        except Exception as e:
            self.console.print(f"❌ テクニカル指標エラー: {str(e)}")
            return None

    async def _generate_real_ai_analysis(
        self,
        currency_pair: str,
        market_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """OpenAI GPT を使用してマルチタイムフレーム戦略に基づく売買シナリオを生成"""
        self.console.print("🤖 OpenAI GPT戦略分析生成中...")

        if not self.openai_key or self.openai_key == "your_openai_api_key":
            self.console.print("⚠️ OpenAI APIキーが未設定。サンプル分析を使用。")
            return self._generate_sample_trading_scenario(currency_pair, market_data)

        # 現在時刻と市場データを組み込んだプロンプト作成
        current_time = datetime.now(self.jst).strftime("%Y年%m月%d日 %H:%M JST")

        # ドル円メインの戦略的プロンプト
        is_usdjpy = currency_pair == "USD/JPY"
        analysis_role = "メイン売買対象" if is_usdjpy else "関連通貨分析データ"

        # 現在レート取得
        current_rate = market_data.get("rate", 0)
        day_high = market_data.get("day_high", current_rate)
        day_low = market_data.get("day_low", current_rate)

        # テクニカル指標データを文字列化
        technical_info = ""
        if technical_data:
            technical_info = "\n【テクニカル指標】"
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
                        bb_position = data.get("bb_position", "N/A")
                        bb_signal = data.get("bb_signal", "N/A")
                        technical_info += f"\n{key}: {bb_position} ({bb_signal})"

        prompt = f"""
あなたは経験豊富なプロFXトレーダーかつ親切な投資教育者です。FX初学者にも理解できるよう、専門用語には必ず説明を付けながら、以下のマルチタイムフレーム戦略に基づいて{currency_pair}の実践的な売買シナリオを作成してください。

【戦略ルール】
1. D1・H4で方向性（売買方針）を固定
2. H1でゾーンと反発・継続サインを探す
3. M5でタイミングを絞る（過熱・反発・形状確認）
4. ダイバージェンスは警戒信号として活用
5. シナリオ外（急騰・急落）のケースも1パターン事前に想定

【市場データ - {analysis_role}】
通貨ペア: {currency_pair}
現在レート: {current_rate}
変動: {market_data.get('market_change', 'N/A')} ({market_data.get('market_change_percent', 'N/A')}%)
日中高値: {day_high}
日中安値: {day_low}
データ時刻: {current_time}{technical_info}

【分析要求】
{"🎯 USD/JPY売買シナリオ作成（メイン戦略）" if is_usdjpy else f"📊 {currency_pair}分析（USD/JPY戦略の参考データ）"}

以下の形式で800文字以内で売買シナリオを提供：

【大局観】D1・H4方向性分析（※テクニカル指標含む）
【戦術】H1ゾーン・反発継続分析
【タイミング】M5エントリーポイント
【メインシナリオ】売買方針・具体的価格指示
 ・エントリー価格: ○○.○○○○（具体的な4桁価格）
 ・利確目標: ○○.○○○○（〇〇pips※利益）
 ・損切り価格: ○○.○○○○（〇〇pips※損失）
【サブシナリオ】急変時の対応策
【リスク管理】注意点・ダイバージェンス※警戒

※専門用語解説：
・pips: 通貨ペアの最小価格単位（USD/JPYなら0.01円=1pip）
・ダイバージェンス: 価格とテクニカル指標の動きが逆行する現象
・その他専門用語があれば簡潔に説明

必ず具体的な価格（小数点以下4桁）とpips数を明記し、初学者でも実際にトレードできる実践的な指示を提供してください。
"""

        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,  # 800文字対応
                "temperature": 0.7,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.openai_url, headers=headers, json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    analysis = data["choices"][0]["message"]["content"].strip()
                    self.console.print("✅ AI分析生成成功")
                    return analysis
                else:
                    self.console.print(f"❌ OpenAI APIエラー: {response.status_code}")
                    self.console.print(f"エラー詳細: {response.text}")
                    return None

        except Exception as e:
            self.console.print(f"❌ AI分析生成エラー: {str(e)}")
            return None

    def _generate_sample_trading_scenario(
        self, currency_pair: str, market_data: Dict[str, Any]
    ) -> str:
        """サンプル売買シナリオ生成（OpenAI APIキー未設定時）"""
        rate = market_data.get("rate", 0)
        change = market_data.get("market_change", 0)
        change_percent = market_data.get("market_change_percent", 0)

        is_usdjpy = currency_pair == "USD/JPY"

        if change > 0:
            trend = "上昇"
            direction = "LONG"
            entry_bias = "押し目買い"
        elif change < 0:
            trend = "下落"
            direction = "SHORT"
            entry_bias = "戻り売り"
        else:
            trend = "横ばい"
            direction = "様子見"
            entry_bias = "レンジ逆張り"

        scenario_title = "🎯 USD/JPY売買シナリオ" if is_usdjpy else f"📊 {currency_pair}分析データ"

        # 具体的な価格計算
        entry_price = rate
        if change >= 0:  # LONG戦略
            profit_target = rate + 0.5
            stop_loss = rate - 0.3
            pips_profit = 50
            pips_loss = 30
        else:  # SHORT戦略
            profit_target = rate - 0.5
            stop_loss = rate + 0.3
            pips_profit = 50
            pips_loss = 30

        return f"""
{scenario_title}

【大局観】D1・H4: {trend}トレンド継続想定
現在レート: {rate:.4f} ({change:+.4f}, {change_percent:+.2f}%)

【戦術】H1ゾーン分析
・重要レベル: {market_data.get('day_high', 'N/A')} (日中高値)
・サポート: {market_data.get('day_low', 'N/A')} (日中安値)
・反発継続: {trend}方向への反発を監視

【タイミング】M5エントリー条件
・{entry_bias}タイミングを狙う
・RSI※過熱解消後のエントリー推奨

【メインシナリオ】{direction}戦略・具体的価格指示
・エントリー価格: {entry_price:.4f}
・利確目標: {profit_target:.4f} ({pips_profit}pips※利益)
・損切り価格: {stop_loss:.4f} ({pips_loss}pips※損失)

【サブシナリオ】急変対応
・想定外ブレイク時は即座に損切り
・トレンド※転換確認まで新規ポジション控える

【リスク管理】ダイバージェンス※警戒
・ポジションサイズ: 口座の2%以下
・経済指標発表時は一時撤退
・ダイバージェンス発生時は利確検討

※専門用語解説：
・pips: 通貨ペアの最小価格単位（USD/JPYなら0.01円=1pip）
・RSI: 相対力指数、買われすぎ・売られすぎを示す指標
・ダイバージェンス: 価格とテクニカル指標の動きが逆行する現象
・トレンド: 価格の方向性（上昇・下降・横ばい）

※サンプルシナリオ。実際の投資判断は慎重に行ってください。
        """.strip()

    async def _send_to_discord(
        self, currency_pair: str, market_data: Dict[str, Any], analysis: str
    ) -> bool:
        """Discord Webhook に AI分析結果を送信"""
        self.console.print("💬 Discord配信中...")

        if not self.discord_webhook:
            self.console.print("⚠️ Discord Webhook URLが未設定")
            return False

        # 変動に応じた色設定
        change_percent = market_data.get("market_change_percent", 0)
        if change_percent > 0:
            color = 0x00FF00  # 緑色（上昇）
            trend_emoji = "📈"
        elif change_percent < 0:
            color = 0xFF0000  # 赤色（下落）
            trend_emoji = "📉"
        else:
            color = 0xFFFF00  # 黄色（横ばい）
            trend_emoji = "➡️"

        # ドル円かどうかで配信内容を調整
        is_usdjpy = currency_pair == "USD/JPY"
        content_title = (
            f"🎯 **売買シナリオ - {currency_pair}**"
            if is_usdjpy
            else f"📊 **関連通貨分析 - {currency_pair}**"
        )
        embed_title = (
            f"🎯 Trading Scenario - {currency_pair}"
            if is_usdjpy
            else f"📊 Market Data - {currency_pair}"
        )
        embed_desc = "マルチタイムフレーム戦略に基づく売買シナリオ" if is_usdjpy else "USD/JPY戦略の参考データ分析"

        embed_data = {
            "content": f"{trend_emoji} {content_title}",
            "embeds": [
                {
                    "title": embed_title,
                    "description": f"{embed_desc} | Yahoo Finance実データ",
                    "color": color,
                    "fields": [
                        {
                            "name": "💱 現在レート",
                            "value": f"**{market_data.get('rate', 'N/A'):.4f}**",
                            "inline": True,
                        },
                        {
                            "name": "📊 変動",
                            "value": f"{market_data.get('market_change', 'N/A'):+.4f} ({market_data.get('market_change_percent', 'N/A'):+.2f}%)",
                            "inline": True,
                        },
                        {
                            "name": "🌐 データソース",
                            "value": f"{market_data.get('data_source', 'N/A')}",
                            "inline": True,
                        },
                        {
                            "name": "📈 日中高値",
                            "value": f"{market_data.get('day_high', 'N/A'):.4f}",
                            "inline": True,
                        },
                        {
                            "name": "📉 日中安値",
                            "value": f"{market_data.get('day_low', 'N/A'):.4f}",
                            "inline": True,
                        },
                        {
                            "name": "⏰ 更新時刻",
                            "value": f"{market_data.get('last_update', 'N/A')}",
                            "inline": True,
                        },
                        {
                            "name": "🎯 売買シナリオ" if is_usdjpy else "📊 関連分析",
                            "value": analysis[:1000],  # Discordの制限対応
                            "inline": False,
                        },
                    ],
                    "footer": {
                        "text": "Multi-Timeframe Trading Strategy | Yahoo Finance + OpenAI GPT"
                    },
                    "timestamp": datetime.now(self.jst).isoformat(),
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.discord_webhook, json=embed_data)

                if response.status_code == 204:
                    self.console.print("✅ Discord配信成功")
                    return True
                else:
                    self.console.print(f"❌ Discord配信失敗: {response.status_code}")
                    self.console.print(f"レスポンス: {response.text}")
                    return False

        except Exception as e:
            self.console.print(f"❌ Discord配信エラー: {str(e)}")
            return False


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Real AI Discord Reporter (Yahoo Finance)"
    )
    parser.add_argument(
        "currency_pair", nargs="?", default="USD/JPY", help="通貨ペア（例: USD/JPY）"
    )
    parser.add_argument("--test", action="store_true", help="テストモード（Discordに送信しない）")

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

    reporter = RealAIDiscordReporter()

    if args.test:
        reporter.console.print("🧪 テストモード: Discord配信をスキップ")
        # テストモードでもデータ取得とAI分析は実行
        market_data = await reporter._fetch_real_market_data(args.currency_pair)
        if market_data:
            analysis = await reporter._generate_real_ai_analysis(
                args.currency_pair, market_data
            )
            reporter.console.print("✅ テスト完了")
        else:
            reporter.console.print("❌ テスト失敗")
    else:
        await reporter.generate_and_send_real_report(args.currency_pair)


if __name__ == "__main__":
    asyncio.run(main())
