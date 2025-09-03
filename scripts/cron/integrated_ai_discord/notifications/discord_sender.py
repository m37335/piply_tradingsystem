#!/usr/bin/env python3
"""
Discord Sender Module
統合分析結果をDiscordに送信する機能
"""

import httpx
import os
from datetime import datetime
from typing import Any, Dict, Optional
from rich.console import Console


class DiscordSender:
    """Discord送信クラス"""

    def __init__(self, discord_webhook: str, jst_timezone):
        self.discord_webhook = discord_webhook
        self.jst = jst_timezone
        self.console = Console()

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
        
        # テクニカル分析結果を取得
        technical_bias = usdjpy_forecast.get("technical_bias", {})
        technical_trend = technical_bias.get("trend_type", "N/A")
        macd_value = technical_bias.get("macd_value", "N/A")
        rsi_value = technical_bias.get("rsi_value", "N/A")
        timeframe_priority = usdjpy_forecast.get("timeframe_priority", "N/A")

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
            {
                "name": "📊 テクニカル",
                "value": f"**{technical_trend}**",
                "inline": True,
            },
            {
                "name": "📈 MACD",
                "value": f"**{macd_value}**",
                "inline": True,
            },
            {
                "name": "📉 RSI",
                "value": f"**{rsi_value}**",
                "inline": True,
            },
            {
                "name": "🎯 時間軸優先度",
                "value": f"**{timeframe_priority}**",
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

    async def send_error_notification(self, error_msg: str) -> bool:
        """エラー通知をDiscordに送信"""
        try:
            if not self.discord_webhook:
                return False

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
                response = await client.post(self.discord_webhook, json=embed_data)
                if response.status_code == 204:
                    self.console.print("✅ エラー通知をDiscordに送信しました")
                    return True
                else:
                    self.console.print(f"❌ エラー通知送信失敗: {response.status_code}")
                    return False

        except Exception as e:
            self.console.print(f"⚠️ エラー通知送信失敗: {str(e)}")
            return False

    async def send_chart_to_discord(self, chart_file_path: str, currency_pair: str) -> bool:
        """チャート画像をDiscordに送信"""
        try:
            if not self.discord_webhook:
                self.console.print("⚠️ Discord Webhook URLが未設定")
                return False

            if not os.path.exists(chart_file_path):
                self.console.print(f"⚠️ チャートファイルが見つかりません: {chart_file_path}")
                return False

            self.console.print(f"📊 {currency_pair} チャートDiscord配信中...")

            # ファイルサイズを確認（Discordの制限: 8MB）
            file_size = os.path.getsize(chart_file_path)
            if file_size > 8 * 1024 * 1024:  # 8MB
                self.console.print(f"⚠️ ファイルサイズが大きすぎます: {file_size / 1024 / 1024:.2f}MB")
                return False

            # ファイル名を取得
            file_name = os.path.basename(chart_file_path)

            # ファイルを読み込み
            with open(chart_file_path, 'rb') as f:
                files = {
                    'file': (file_name, f, 'image/png')
                }

                # メッセージデータ
                data = {
                    'content': f"📊 **{currency_pair} H1チャート** - {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M JST')}"
                }

                # Discordに送信
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.discord_webhook,
                        data=data,
                        files=files
                    )

                    if response.status_code in [200, 204]:
                        self.console.print(f"✅ {currency_pair} チャートDiscord配信成功")
                        return True
                    else:
                        self.console.print(f"❌ チャート配信失敗: {response.status_code}")
                        self.console.print(f"レスポンス: {response.text}")
                        return False

        except Exception as e:
            self.console.print(f"❌ チャート配信エラー: {str(e)}")
            return False
