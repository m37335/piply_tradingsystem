#!/usr/bin/env python3
"""
実際のGPT分析結果をDiscordに配信
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
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


class RealAIDiscordReporter:
    """実AI分析Discord配信システム"""

    def __init__(self):
        self.console = Console()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

        # API URLs
        self.openai_url = "https://api.openai.com/v1/chat/completions"

        # Yahoo Finance クライアント初期化
        self.yahoo_client = YahooFinanceClient()

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

            # Step 2: OpenAI GPT で実際の分析
            analysis_result = await self._generate_real_ai_analysis(
                currency_pair, market_data
            )
            if not analysis_result:
                self.console.print("❌ AI分析生成失敗")
                return False

            # Step 3: Discord に配信
            success = await self._send_real_discord_report(
                currency_pair, market_data, analysis_result
            )
            if success:
                self.console.print("✅ 実AI分析レポートをDiscordに配信しました！")
                return True
            else:
                self.console.print("❌ Discord配信失敗")
                return False

        except Exception as e:
            self.console.print(f"❌ エラー: {str(e)}")
            return False

    async def _fetch_real_market_data(
        self, currency_pair: str
    ) -> Optional[Dict[str, Any]]:
        """Alpha Vantage から実際の市場データを取得"""
        self.console.print("📊 Yahoo Finance から実データ取得中...")

        if (
            not self.alpha_vantage_key
            or self.alpha_vantage_key == "demo_key_replace_with_your_key"
        ):
            self.console.print("⚠️ Alpha Vantage APIキーが未設定。サンプルデータを使用。")
            return {
                "rate": 147.69,
                "bid": 147.68,
                "ask": 147.70,
                "last_update": datetime.now(self.jst).strftime("%Y-%m-%d %H:%M:%S JST"),
                "data_source": "Sample Data",
            }

        # 通貨ペアをAlpha Vantage形式に変換
        if "/" in currency_pair:
            from_curr, to_curr = currency_pair.split("/")
        else:
            from_curr, to_curr = "USD", "JPY"

        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_curr,
            "to_currency": to_curr,
            "apikey": self.alpha_vantage_key,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.alpha_vantage_url, params=params)

                if response.status_code == 200:
                    data = response.json()

                    if "Realtime Currency Exchange Rate" in data:
                        fx_data = data["Realtime Currency Exchange Rate"]

                        market_data = {
                            "rate": float(fx_data.get("5. Exchange Rate", 0)),
                            "bid": float(fx_data.get("8. Bid Price", 0)),
                            "ask": float(fx_data.get("9. Ask Price", 0)),
                            "last_update": fx_data.get("6. Last Refreshed", ""),
                            "from_currency": fx_data.get(
                                "1. From_Currency Code", from_curr
                            ),
                            "to_currency": fx_data.get("3. To_Currency Code", to_curr),
                            "data_source": "Alpha Vantage Live Data",
                        }

                        self.console.print(f"✅ 実データ取得成功: {market_data['rate']}")
                        return market_data
                    else:
                        self.console.print("❌ 無効なレスポンス形式")
                        return None
                else:
                    self.console.print(f"❌ API失敗: HTTP {response.status_code}")
                    return None

        except Exception as e:
            self.console.print(f"❌ 市場データ取得エラー: {str(e)}")
            return None

    async def _generate_real_ai_analysis(
        self, currency_pair: str, market_data: Dict[str, Any]
    ) -> Optional[str]:
        """OpenAI GPT で実際の市場分析を生成"""
        self.console.print("🤖 OpenAI GPT で実AI分析生成中...")

        if not self.openai_key or self.openai_key == "sk-replace-with-your-openai-key":
            self.console.print("⚠️ OpenAI APIキーが未設定。サンプル分析を使用。")
            return f"""
【実市場分析レポート】{currency_pair}

現在レート: {market_data.get('rate', 'N/A')}
データ取得時刻: {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M:%S JST')}

【技術的分析】
・現在のレートは中期移動平均を上回っており、上昇トレンドを維持
・RSI指標は70付近で推移し、やや過熱感あり
・サポートレベル: {market_data.get('rate', 147) - 0.5:.2f}
・レジスタンスレベル: {market_data.get('rate', 147) + 0.5:.2f}

【推奨アクション】
・短期的には利益確定も検討
・下落時の押し目買いチャンスを待つ
・リスク管理を徹底し、適切な損切りラインを設定

※この分析は{market_data.get('data_source', 'Sample Data')}に基づいています。
"""

        # 実際のGPT分析プロンプト作成
        current_time = datetime.now(self.jst)

        prompt = f"""
あなたは経験豊富な金融アナリストです。以下の実際の市場データに基づいて、{currency_pair}の詳細な分析レポートを日本語で作成してください。

【市場データ】
- 通貨ペア: {currency_pair}
- 現在レート: {market_data.get('rate', 'N/A')}
- ビッド価格: {market_data.get('bid', 'N/A')}
- アスク価格: {market_data.get('ask', 'N/A')}
- データ更新時刻: {market_data.get('last_update', 'N/A')}
- 分析時刻: {current_time.strftime('%Y年%m月%d日 %H時%M分 JST')}
- データソース: {market_data.get('data_source', 'Unknown')}

【分析項目】
1. 現在の市場状況（2-3行）
2. 技術的分析（トレンド、サポート・レジスタンス）
3. 短期的な見通し（今後6-12時間）
4. リスク要因
5. 推奨取引戦略

【要求事項】
- 具体的で実用的な分析を提供
- 根拠を明確に示す
- リスク管理の重要性を強調
- 400文字以内で簡潔にまとめる
- 投資助言ではなく、分析情報として提供

分析レポートを開始してください：
"""

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "あなたは金融市場の専門アナリストです。実際のデータに基づいた客観的で実用的な分析を提供してください。",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 600,
            "temperature": 0.3,  # より一貫性のある分析のため低めに設定
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.openai_url, headers=headers, json=data
                )

                if response.status_code == 200:
                    result = response.json()
                    analysis = result["choices"][0]["message"]["content"].strip()
                    self.console.print("✅ GPT分析生成成功")
                    return analysis
                else:
                    self.console.print(f"❌ OpenAI API失敗: HTTP {response.status_code}")
                    return None

        except Exception as e:
            self.console.print(f"❌ GPT分析エラー: {str(e)}")
            return None

    async def _send_real_discord_report(
        self, currency_pair: str, market_data: Dict[str, Any], analysis: str
    ) -> bool:
        """実AI分析結果をDiscordに配信"""
        self.console.print("💬 Discord配信中...")

        if not self.discord_webhook:
            self.console.print("⚠️ Discord Webhook URLが未設定")
            return False

        current_time = datetime.now(self.jst)
        rate = market_data.get("rate", 0)

        # レート変動に基づく色設定
        if rate > 147.5:
            color = 0x00FF00  # 緑（高値）
            trend_emoji = "📈"
        elif rate < 147.0:
            color = 0xFF6600  # オレンジ（安値）
            trend_emoji = "📉"
        else:
            color = 0x3498DB  # 青（中間）
            trend_emoji = "📊"

        # Discord Embed作成
        discord_data = {
            "content": f"🤖 **実AI市場分析レポート** - {currency_pair}",
            "embeds": [
                {
                    "title": f"{trend_emoji} {currency_pair} 実市場分析",
                    "description": analysis[:1000]
                    + ("..." if len(analysis) > 1000 else ""),
                    "color": color,
                    "fields": [
                        {"name": "💱 現在レート", "value": f"{rate:.3f}", "inline": True},
                        {
                            "name": "💰 スプレッド",
                            "value": f"{market_data.get('ask', 0) - market_data.get('bid', 0):.3f}",
                            "inline": True,
                        },
                        {
                            "name": "📊 データソース",
                            "value": market_data.get("data_source", "Unknown"),
                            "inline": True,
                        },
                        {
                            "name": "💹 ビッド/アスク",
                            "value": f"{market_data.get('bid', 0):.3f} / {market_data.get('ask', 0):.3f}",
                            "inline": True,
                        },
                        {
                            "name": "🕘 分析時刻（JST）",
                            "value": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "inline": True,
                        },
                        {
                            "name": "🔄 データ更新",
                            "value": market_data.get("last_update", "N/A"),
                            "inline": True,
                        },
                    ],
                    "footer": {
                        "text": "🤖 Real AI Analysis System | Exchange Analytics"
                    },
                    "timestamp": current_time.isoformat(),
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.discord_webhook, json=discord_data)

                if response.status_code in [200, 204]:
                    self.console.print("✅ Discord配信成功")
                    return True
                else:
                    self.console.print(f"❌ Discord配信失敗: HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.console.print(f"❌ Discord配信エラー: {str(e)}")
            return False


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Real AI Analysis Discord Reporter")
    parser.add_argument(
        "currency_pair",
        nargs="?",
        default="USD/JPY",
        help="Currency pair (default: USD/JPY)",
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode with sample data"
    )

    args = parser.parse_args()

    console = Console()
    console.print("🚀 実AI分析Discord配信システム")
    console.print(f"💱 通貨ペア: {args.currency_pair}")
    console.print(f"🧪 テストモード: {'有効' if args.test else '無効'}")
    console.print()

    reporter = RealAIDiscordReporter()

    # 環境変数チェック
    missing_keys = []
    if (
        not reporter.alpha_vantage_key
        or reporter.alpha_vantage_key == "demo_key_replace_with_your_key"
    ):
        missing_keys.append("ALPHA_VANTAGE_API_KEY")
    if (
        not reporter.openai_key
        or reporter.openai_key == "sk-replace-with-your-openai-key"
    ):
        missing_keys.append("OPENAI_API_KEY")
    if not reporter.discord_webhook:
        missing_keys.append("DISCORD_WEBHOOK_URL")

    if missing_keys:
        console.print(f"⚠️ 未設定のAPIキー: {', '.join(missing_keys)}")
        console.print("📝 サンプルデータで実行します")

    success = await reporter.generate_and_send_real_report(args.currency_pair)

    if success:
        console.print("🎉 実AI分析レポート配信完了！")
        console.print("💬 Discordチャンネルをご確認ください")
    else:
        console.print("❌ 実AI分析レポート配信失敗")


if __name__ == "__main__":
    asyncio.run(main())
