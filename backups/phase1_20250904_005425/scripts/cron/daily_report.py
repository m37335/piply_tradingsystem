#!/usr/bin/env python3
"""
Daily Report Script for Cron
日次レポート送信スクリプト（継続処理システム統計対応版）
"""

import asyncio
import os
import re
import sys
from datetime import datetime, timedelta

import pytz

sys.path.append("/app")


def calculate_stats_from_logs():
    """継続処理システムのログから統計を計算（重複排除版）"""
    # 現在のシステム構成に合わせてログファイルを変更
    log_file = "/app/logs/simple_data_fetcher.log"
    integrated_ai_log = "/app/logs/integrated_ai_cron.log"
    jst = pytz.timezone("Asia/Tokyo")
    today = datetime.now(jst).date()

    stats = {
        "total_fetches": 0,
        "successful_fetches": 0,
        "failed_fetches": 0,
        "ai_analyses": 0,
        "discord_notifications": 0,
        "start_time": datetime.now(jst) - timedelta(hours=24),
    }

    # 重複排除用のセット
    processed_timestamps = set()

    try:
        # シンプルデータ取得システムのログから統計を計算
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                for line in f:
                    # 今日のログのみ処理
                    if str(today) in line:
                        # タイムスタンプを抽出
                        timestamp_match = re.search(
                            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line
                        )
                        if timestamp_match:
                            timestamp = timestamp_match.group(1)

                            # データ保存成功をカウント（重複排除）
                            if (
                                "Saved price data" in line
                                and timestamp not in processed_timestamps
                            ):
                                stats["successful_fetches"] += 1
                                stats["total_fetches"] += 1
                                processed_timestamps.add(timestamp)

                            # エラーをカウント（重複排除）
                            elif (
                                "ERROR" in line or "FAILED" in line
                            ) and timestamp not in processed_timestamps:
                                stats["failed_fetches"] += 1
                                stats["total_fetches"] += 1
                                processed_timestamps.add(timestamp)

                            # データ取得サイクル完了をカウント（重複排除）
                            elif (
                                "データ取得サイクル完了" in line
                                and timestamp not in processed_timestamps
                            ):
                                # 既にSaved price dataでカウント済みの場合はスキップ
                                pass

        # 統合AI分析のログから統計を計算
        if os.path.exists(integrated_ai_log):
            ai_analysis_count = 0
            discord_notification_count = 0

            with open(integrated_ai_log, "r") as f:
                for line in f:
                    # 統合AI分析成功をカウント
                    if "✅ 統合AI分析生成成功" in line:
                        ai_analysis_count += 1

                    # 統合AI分析のDiscord配信成功をカウント
                    elif "✅ 統合分析Discord配信成功" in line:
                        discord_notification_count += 1

            # 統合AI分析の統計を追加
            stats["ai_analyses"] = ai_analysis_count
            stats["discord_notifications"] = discord_notification_count

    except FileNotFoundError as e:
        print(f"Log file not found: {e}")
    except Exception as e:
        print(f"Error reading log file: {e}")

    # デバッグ情報を表示
    print("📊 統計計算結果（重複排除版）:")
    print(f"   - 総取得回数: {stats['total_fetches']}")
    print(f"   - 成功回数: {stats['successful_fetches']}")
    print(f"   - 失敗回数: {stats['failed_fetches']}")
    print(f"   - AI分析回数: {stats['ai_analyses']}")
    print(f"   - Discord通知: {stats['discord_notifications']}")
    print(f"   - 処理済みタイムスタンプ数: {len(processed_timestamps)}")
    print(f"   - 参照ログファイル: {log_file}")
    print(f"   - 参照AIログファイル: {integrated_ai_log}")

    return stats


async def main():
    try:
        # 継続処理システムのログから統計を計算
        stats = calculate_stats_from_logs()

        # Discord Webhook URL取得
        webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
        if not webhook_url:
            print("Discord webhook URL not configured")
            return

        import httpx

        # 成功率計算
        success_rate = 0
        if stats["total_fetches"] > 0:
            success_rate = (stats["successful_fetches"] / stats["total_fetches"]) * 100

        # 稼働時間計算
        runtime = datetime.now(pytz.timezone("Asia/Tokyo")) - stats["start_time"]

        # レポートデータ作成
        report_data = {
            "content": "📊 **日次レポート（継続処理システム統計）**",
            "embeds": [
                {
                    "title": "📈 Daily Data Scheduler Report",
                    "description": "過去24時間の継続処理システム統計",
                    "color": 0x00FF00,
                    "fields": [
                        {
                            "name": "📊 総取得回数",
                            "value": str(stats["total_fetches"]),
                            "inline": True,
                        },
                        {
                            "name": "✅ 成功回数",
                            "value": str(stats["successful_fetches"]),
                            "inline": True,
                        },
                        {
                            "name": "❌ 失敗回数",
                            "value": str(stats["failed_fetches"]),
                            "inline": True,
                        },
                        {
                            "name": "🤖 AI分析回数",
                            "value": str(stats["ai_analyses"]),
                            "inline": True,
                        },
                        {
                            "name": "💬 Discord通知",
                            "value": str(stats["discord_notifications"]),
                            "inline": True,
                        },
                        {
                            "name": "📈 成功率",
                            "value": f"{success_rate:.1f}%",
                            "inline": True,
                        },
                        {
                            "name": "⏱️ 稼働時間",
                            "value": str(runtime).split(".")[0],
                            "inline": False,
                        },
                    ],
                    "footer": {"text": "Continuous Processing System Daily Report"},
                    "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat(),
                }
            ],
        }

        # Discordに送信
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=report_data)
            if response.status_code == 204:
                print("Daily report sent successfully")
            else:
                print(f"Failed to send daily report: {response.status_code}")

    except Exception as e:
        print(f"Daily report error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
