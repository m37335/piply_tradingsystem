#!/usr/bin/env python3
"""
Integrated AI Discord Reporter - Main Script
通貨相関性を活用した統合AI分析Discord配信システム（モジュール化版）
"""

import argparse
import asyncio
import os
import sys
import traceback
from datetime import datetime

import pytz
from rich.console import Console

# 相対インポートの問題を回避するため、パスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from integrated.integrated_reporter import IntegratedAIDiscordReporter

from utils.config_manager import ConfigManager
from utils.error_handler import ErrorHandler


async def main():
    """メイン実行関数（モジュール化版）"""
    parser = argparse.ArgumentParser(
        description="Integrated AI Discord Reporter (Modularized)"
    )
    parser.add_argument(
        "--test", action="store_true", help="テストモード（Discordに送信しない）"
    )
    parser.add_argument(
        "--no-optimization", action="store_true", help="最適化機能を無効にする"
    )
    parser.add_argument(
        "--chart", action="store_true", help="H1チャートとH4チャートを生成する"
    )

    args = parser.parse_args()

    console = Console()
    config_manager = ConfigManager()
    error_handler = ErrorHandler()

    # 設定検証
    if not config_manager.validate_config():
        console.print("❌ 設定が不完全です。.envファイルを確認してください。")
        return

    reporter = IntegratedAIDiscordReporter()

    # 最適化コンポーネント初期化
    if not args.no_optimization:
        try:
            await reporter.initialize_optimization_components()
            console.print("🚀 最適化機能が有効です")
        except Exception as e:
            error_handler.log_error(e, "最適化機能初期化")
            console.print("📝 従来モードで実行します")
    else:
        console.print("📝 最適化機能を無効にして実行します")

    if args.test:
        console.print("🧪 テストモード: Discord配信をスキップ")
        # 通貨相関分析、テクニカル指標、AI分析まで実行
        correlation_data = (
            await reporter.correlation_analyzer.perform_integrated_analysis()
        )
        if "error" not in correlation_data:
            reporter.correlation_analyzer.display_correlation_analysis(correlation_data)

            # テクニカル指標取得
            technical_data = await reporter._fetch_technical_indicators("USD/JPY")

            # チャート生成（オプション）
            if args.chart:
                chart_file_path = await reporter._generate_h1_chart(
                    "USD/JPY", technical_data
                )
                if chart_file_path:
                    console.print(f"📊 チャート生成完了: {chart_file_path}")

            # 統合AI分析
            analysis = (
                await (
                    reporter.ai_strategy_generator.generate_integrated_analysis(
                        correlation_data, technical_data
                    )
                )
            )
            if analysis:
                console.print("📋 統合AI分析結果:")
                console.print(f"[cyan]{analysis}[/cyan]")
            else:
                console.print("⚠️ AI分析はスキップ（API制限のため）")

            console.print("✅ テスト完了")
        else:
            console.print("❌ AI分析生成失敗")
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
            config_manager = ConfigManager()
            discord_webhook = config_manager.discord_monitoring_webhook_url
            if discord_webhook:
                import httpx

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
