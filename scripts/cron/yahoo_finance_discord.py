#!/usr/bin/env python3
"""
Yahoo Finance Discord Notification
Yahoo Finance データのDiscord配信スクリプト

機能:
- Yahoo Finance から最新データ取得
- 美しいDiscord Embed形式で配信
- 複数通貨ペア対応
- エラーハンドリング
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import pytz

# プロジェクトパスを追加
sys.path.append("/app")

from rich.console import Console

from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


class YahooFinanceDiscordNotifier:
    """Yahoo Finance Discord配信システム"""

    def __init__(self):
        self.console = Console()
        self.jst = pytz.timezone("Asia/Tokyo")
        self.yahoo_client = YahooFinanceClient()
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        if not self.webhook_url:
            self.console.print("❌ DISCORD_WEBHOOK_URL が設定されていません")

    async def send_currency_report(self, currency_pairs: List[str] = None) -> bool:
        """通貨レポートをDiscordに送信"""
        if currency_pairs is None:
            currency_pairs = ["USD/JPY", "EUR/USD", "GBP/USD", "AUD/USD", "EUR/JPY"]

        try:
            self.console.print(f"📊 {len(currency_pairs)}通貨ペアのレポート作成中...")

            # Yahoo Finance からデータ取得
            rates_data = await self.yahoo_client.get_multiple_rates(currency_pairs)

            if not rates_data.get("rates"):
                self.console.print("❌ データ取得失敗")
                return False

            # Discord Embed作成
            embed_data = await self._create_currency_embed(rates_data)

            # Discord送信
            success = await self._send_to_discord(embed_data)

            if success:
                self.console.print("✅ Discord配信成功")
                return True
            else:
                self.console.print("❌ Discord配信失敗")
                return False

        except Exception as e:
            self.console.print(f"❌ レポート送信エラー: {str(e)}")
            return False

    async def _create_currency_embed(self, rates_data: Dict) -> Dict:
        """通貨データからDiscord Embed作成"""
        current_time = datetime.now(self.jst)

        # 成功・失敗統計
        summary = rates_data.get("summary", {})
        successful = summary.get("successful", 0)
        total = summary.get("total", 0)

        # メイン説明文
        description = f"Yahoo Finance から{successful}/{total}通貨ペアのデータを取得"

        # フィールド作成
        fields = []

        for pair, data in rates_data.get("rates", {}).items():
            rate = data.get("rate")
            change = data.get("market_change", 0) or 0
            change_pct = data.get("market_change_percent", 0) or 0

            # 変動の色とアイコン
            if change > 0:
                trend_icon = "📈"
                change_text = f"+{change:.4f} (+{change_pct:.2f}%)"
            elif change < 0:
                trend_icon = "📉"
                change_text = f"{change:.4f} ({change_pct:.2f}%)"
            else:
                trend_icon = "➡️"
                change_text = "変動なし"

            field_value = f"""
{trend_icon} **{rate:.4f}**
{change_text}
高値: {data.get('day_high', 'N/A'):.4f} | 安値: {data.get('day_low', 'N/A'):.4f}
            """.strip()

            fields.append({"name": f"💱 {pair}", "value": field_value, "inline": True})

        # 統計フィールド
        fields.append(
            {
                "name": "📊 取得統計",
                "value": f"✅ 成功: {successful}件\n❌ 失敗: {summary.get('failed', 0)}件\n⏰ 時刻: {current_time.strftime('%H:%M:%S JST')}",
                "inline": True,
            }
        )

        # データソース情報
        fields.append(
            {
                "name": "🌐 データソース",
                "value": "Yahoo Finance\n🆓 無制限・リアルタイム",
                "inline": True,
            }
        )

        embed_data = {
            "content": "💱 **Yahoo Finance 為替レポート**",
            "embeds": [
                {
                    "title": "📊 Real-time Currency Exchange Report",
                    "description": description,
                    "color": 0x00FF88,  # 緑色
                    "fields": fields,
                    "footer": {"text": "Yahoo Finance | Exchange Analytics"},
                    "timestamp": current_time.isoformat(),
                }
            ],
        }

        return embed_data

    async def _send_to_discord(self, embed_data: Dict) -> bool:
        """Discord Webhookに送信"""
        if not self.webhook_url:
            return False

        try:
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=embed_data)

                if response.status_code == 204:
                    return True
                else:
                    self.console.print(f"❌ Discord送信失敗: HTTP {response.status_code}")
                    return False

        except Exception as e:
            self.console.print(f"❌ Discord送信エラー: {str(e)}")
            return False

    async def send_historical_analysis(self, currency_pair: str = "USD/JPY") -> bool:
        """履歴データ分析をDiscordに送信"""
        try:
            self.console.print(f"📈 {currency_pair} 履歴分析作成中...")

            # 履歴データ取得
            hist_data = await self.yahoo_client.get_historical_data(
                currency_pair, period="5d", interval="1d"
            )

            if hist_data is None or hist_data.empty:
                self.console.print("❌ 履歴データ取得失敗")
                return False

            # 簡易分析
            latest_close = hist_data["Close"].iloc[-1]
            previous_close = (
                hist_data["Close"].iloc[-2] if len(hist_data) > 1 else latest_close
            )
            change = latest_close - previous_close
            change_pct = (change / previous_close) * 100 if previous_close else 0

            # 5日間の統計
            period_high = hist_data["High"].max()
            period_low = hist_data["Low"].min()
            period_avg = hist_data["Close"].mean()

            # Discord Embed作成
            embed_data = {
                "content": f"📈 **{currency_pair} 履歴分析レポート**",
                "embeds": [
                    {
                        "title": f"📊 {currency_pair} Historical Analysis (5-Day)",
                        "description": f"Yahoo Finance 5日間履歴データ分析",
                        "color": 0x0099FF,  # 青色
                        "fields": [
                            {
                                "name": "💱 最新価格",
                                "value": f"**{latest_close:.4f}**\n{change:+.4f} ({change_pct:+.2f}%)",
                                "inline": True,
                            },
                            {
                                "name": "📊 5日間統計",
                                "value": f"高値: {period_high:.4f}\n安値: {period_low:.4f}\n平均: {period_avg:.4f}",
                                "inline": True,
                            },
                            {
                                "name": "📈 データ詳細",
                                "value": f"期間: 5日間\nデータ数: {len(hist_data)}件\nソース: Yahoo Finance",
                                "inline": True,
                            },
                        ],
                        "footer": {
                            "text": "Yahoo Finance Historical Analysis | Exchange Analytics"
                        },
                        "timestamp": datetime.now(self.jst).isoformat(),
                    }
                ],
            }

            # Discord送信
            success = await self._send_to_discord(embed_data)

            if success:
                self.console.print("✅ 履歴分析Discord配信成功")
                return True
            else:
                self.console.print("❌ 履歴分析Discord配信失敗")
                return False

        except Exception as e:
            self.console.print(f"❌ 履歴分析エラー: {str(e)}")
            return False


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Yahoo Finance Discord Notifier")
    parser.add_argument(
        "--type",
        choices=["rates", "historical", "test"],
        default="rates",
        help="配信タイプ",
    )
    parser.add_argument("--pair", default="USD/JPY", help="通貨ペア")
    parser.add_argument("--pairs", help="複数通貨ペア（カンマ区切り）")

    args = parser.parse_args()

    console = Console()
    console.print("💬 Yahoo Finance Discord配信開始")
    console.print(
        f"⏰ 実行時刻: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
    )
    console.print(f"📡 配信タイプ: {args.type}")
    console.print()

    notifier = YahooFinanceDiscordNotifier()

    try:
        if args.type == "rates":
            # 通貨レート配信
            pairs = args.pairs.split(",") if args.pairs else None
            success = await notifier.send_currency_report(pairs)

        elif args.type == "historical":
            # 履歴分析配信
            success = await notifier.send_historical_analysis(args.pair)

        elif args.type == "test":
            # テスト配信
            console.print("🧪 テスト配信実行...")
            success = await notifier.send_currency_report(["USD/JPY", "EUR/USD"])

        else:
            console.print("❌ 無効な配信タイプ")
            return

        if success:
            console.print("✅ Discord配信完了")
        else:
            console.print("❌ Discord配信失敗")
            sys.exit(1)

    except Exception as e:
        console.print(f"❌ 実行エラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
