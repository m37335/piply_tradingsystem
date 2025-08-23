#!/usr/bin/env python3
"""
週次経済指標自動取得・Discord配信スクリプト
毎週日曜日に1週間分の経済指標を取得して、まとめて配信
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_weekly_economic_calendar():
    """1週間分の経済カレンダーデータの取得（キャッシュ対応）"""
    try:
        # キャッシュマネージャーを初期化
        from scripts.cron.economic_calendar_cache_manager import (
            EconomicCalendarCacheManager,
        )

        cache_manager = EconomicCalendarCacheManager()
        await cache_manager.initialize()

        try:
            # 翌週の月曜日から日曜日までの日付を計算
            today = datetime.now()

            # 翌週の月曜日を計算
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            next_monday = today + timedelta(days=days_until_monday)

            # 翌週の日曜日を計算
            next_sunday = next_monday + timedelta(days=6)

            from_date = next_monday.strftime("%d/%m/%Y")
            to_date = next_sunday.strftime("%d/%m/%Y")

            logger.info(
                f"📅 週次経済カレンダー取得開始: {from_date} - {to_date} "
                f"({next_monday.strftime('%Y-%m-%d')} - {next_sunday.strftime('%Y-%m-%d')})"
            )

            # キャッシュから取得を試行
            countries = [
                "japan",
                "united states",
                "euro zone",
                "united kingdom",
                "canada",
                "australia",
            ]
            importances = ["high", "medium"]

            cached_events = await cache_manager.get_cached_weekly_events(
                from_date, countries, importances
            )

            if cached_events:
                logger.info(
                    f"✅ キャッシュから週次経済指標取得: {len(cached_events)}件"
                )
                return cached_events

            # キャッシュにない場合はAPIから取得
            logger.info("🔄 キャッシュにないため、APIから取得します")

            import investpy
            import pandas as pd

            # investpyで1週間分のデータ取得
            df = investpy.economic_calendar(
                from_date=from_date,
                to_date=to_date,
                countries=countries,
                importances=importances,
            )

            if df.empty:
                logger.warning("📊 取得された週次経済指標データが空です")
                fallback_data = await _get_weekly_fallback_mock_data()

                # フォールバックデータもキャッシュに保存
                await cache_manager.save_weekly_events_cache(
                    fallback_data, from_date, countries, importances
                )
                return fallback_data

            logger.info(f"📊 実際の週次経済指標取得: {len(df)}件")

            # DataFrameを辞書形式に変換
            event_dicts = []
            for _, row in df.iterrows():
                try:
                    # 日付と時刻の処理
                    date_str = str(row.get("date", ""))
                    time_str = str(row.get("time", ""))

                    # 実際値、予測値、前回値の処理
                    actual = row.get("actual")
                    forecast = row.get("forecast")
                    previous = row.get("previous")

                    # 数値変換
                    if (
                        pd.notna(actual)
                        and str(actual).replace(".", "").replace("-", "").isdigit()
                    ):
                        actual = float(actual)
                    else:
                        actual = None

                    if (
                        pd.notna(forecast)
                        and str(forecast).replace(".", "").replace("-", "").isdigit()
                    ):
                        forecast = float(forecast)
                    else:
                        forecast = None

                    if (
                        pd.notna(previous)
                        and str(previous).replace(".", "").replace("-", "").isdigit()
                    ):
                        previous = float(previous)
                    else:
                        previous = None

                    event_dict = {
                        "date": date_str,
                        "time": time_str,
                        "country": str(row.get("zone", "")).lower(),
                        "event": str(row.get("event", "")),
                        "importance": str(row.get("importance", "medium")).lower(),
                        "currency": "",  # investpyには通貨情報がない場合が多い
                        "actual": actual,
                        "forecast": forecast,
                        "previous": previous,
                    }
                    event_dicts.append(event_dict)

                except Exception as e:
                    logger.warning(f"⚠️ 週次イベントデータ変換エラー: {e}")
                    continue

            # 取得したデータをキャッシュに保存
            await cache_manager.save_weekly_events_cache(
                event_dicts, from_date, countries, importances
            )

            return event_dicts

        finally:
            await cache_manager.close()

    except Exception as e:
        logger.error(f"❌ 週次経済カレンダー取得エラー: {e}")
        # エラー時はモックデータをフォールバック
        logger.info("🔄 週次モックデータにフォールバック")
        return await _get_weekly_fallback_mock_data()


async def _get_weekly_fallback_mock_data():
    """週次フォールバック用のモックデータ"""
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()) % 7)

    mock_events = []

    # 1週間分のサンプルデータを生成
    for day_offset in range(7):
        event_date = next_monday + timedelta(days=day_offset)

        # 各日に2-3個のイベントを追加
        daily_events = [
            {
                "date": event_date.strftime("%Y-%m-%d"),
                "time": "08:30",
                "country": "japan",
                "event": f"Consumer Price Index (CPI) - {event_date.strftime('%A')}",
                "importance": "high",
                "currency": "JPY",
                "actual": None,
                "forecast": 2.5,
                "previous": 2.3,
            },
            {
                "date": event_date.strftime("%Y-%m-%d"),
                "time": "14:00",
                "country": "united states",
                "event": f"Industrial Production - {event_date.strftime('%A')}",
                "importance": "medium",
                "currency": "USD",
                "actual": None,
                "forecast": 0.8,
                "previous": 0.5,
            },
        ]

        # 重要度の高いイベントを特定の曜日に追加
        if event_date.weekday() == 0:  # 月曜日
            daily_events.append(
                {
                    "date": event_date.strftime("%Y-%m-%d"),
                    "time": "12:30",
                    "country": "united states",
                    "event": "Non-Farm Payrolls",
                    "importance": "high",
                    "currency": "USD",
                    "actual": None,
                    "forecast": 185000,
                    "previous": 180000,
                }
            )
        elif event_date.weekday() == 3:  # 木曜日
            daily_events.append(
                {
                    "date": event_date.strftime("%Y-%m-%d"),
                    "time": "21:00",
                    "country": "euro zone",
                    "event": "ECB Interest Rate Decision",
                    "importance": "high",
                    "currency": "EUR",
                    "actual": None,
                    "forecast": 4.25,
                    "previous": 4.25,
                }
            )

        mock_events.extend(daily_events)

    return mock_events


async def send_weekly_economic_indicators_to_discord(events: List[Dict[str, Any]]):
    """週次経済指標をDiscordに配信"""
    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            logger.error("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        async with DiscordClient(webhook_url) as discord_client:
            logger.info("💬 週次Discord配信開始")

            # 日別にイベントをグループ化
            events_by_date = {}
            for event in events:
                date = event.get("date", "")
                if date not in events_by_date:
                    events_by_date[date] = []
                events_by_date[date].append(event)

            # 週次サマリーの送信
            await send_weekly_summary(discord_client, events, events_by_date)
            await asyncio.sleep(5)  # レート制限対策: 5秒待機

            # 日別詳細の送信
            for date, daily_events in sorted(events_by_date.items()):
                await send_daily_events_summary(discord_client, date, daily_events)
                await asyncio.sleep(4)  # レート制限対策: 4秒待機

            # 高重要度イベントの特別配信
            high_importance_events = [
                e for e in events if e.get("importance") == "high"
            ]
            if high_importance_events:
                await send_high_importance_events(
                    discord_client, high_importance_events
                )

        logger.info("✅ 週次Discord配信完了")
        return True

    except Exception as e:
        logger.error(f"❌ 週次Discord配信エラー: {e}")
        return False


async def send_weekly_summary(discord_client, events, events_by_date):
    """週次サマリーの送信"""
    try:
        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
        next_sunday = next_monday + timedelta(days=6)

        # 統計情報の計算
        total_events = len(events)
        high_importance = len([e for e in events if e.get("importance") == "high"])
        medium_importance = len([e for e in events if e.get("importance") == "medium"])

        # 国別統計
        country_stats = {}
        for event in events:
            country = event.get("country", "").title()
            if country not in country_stats:
                country_stats[country] = 0
            country_stats[country] += 1

        # サマリーメッセージの作成
        description = (
            f"📅 **{next_monday.strftime('%Y年%m月%d日')} - {next_sunday.strftime('%m月%d日')}の週**\n\n"
            f"📊 **総イベント数**: {total_events}件\n"
            f"🔴 **高重要度**: {high_importance}件\n"
            f"🟡 **中重要度**: {medium_importance}件\n"
            f"📆 **実施日数**: {len(events_by_date)}日間\n\n"
            f"🌍 **国別内訳**:\n"
        )

        for country, count in sorted(
            country_stats.items(), key=lambda x: x[1], reverse=True
        ):
            if country and count > 0:
                description += f"• {country}: {count}件\n"

        success = await discord_client.send_embed(
            title="📅 週次経済指標サマリー",
            description=description,
            color=0x0099FF,
            footer={"text": "経済カレンダーシステム • 週次レポート"},
            timestamp=datetime.now(),
        )

        if success:
            logger.info("✅ 週次サマリー配信成功")
        else:
            logger.error("❌ 週次サマリー配信失敗")

    except Exception as e:
        logger.error(f"❌ 週次サマリー送信エラー: {e}")


async def send_daily_events_summary(discord_client, date, daily_events):
    """日別イベントサマリーの送信"""
    try:
        # 日付のパース
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_display = date_obj.strftime("%Y年%m月%d日 (%A)")
        except:
            date_display = date

        # 重要度別に分類
        high_events = [e for e in daily_events if e.get("importance") == "high"]
        medium_events = [e for e in daily_events if e.get("importance") == "medium"]

        fields = []

        # 高重要度イベント
        if high_events:
            high_list = []
            for event in high_events[:5]:  # 最大5件
                event_name = (
                    event.get("event", "")[:40] + "..."
                    if len(event.get("event", "")) > 40
                    else event.get("event", "")
                )
                country = event.get("country", "").title()
                time = event.get("time", "")
                high_list.append(f"🔴 {country}: {event_name} ({time})")

            fields.append(
                {
                    "name": "🔴 高重要度イベント",
                    "value": "\n".join(high_list) if high_list else "なし",
                    "inline": False,
                }
            )

        # 中重要度イベント
        if medium_events:
            medium_list = []
            for event in medium_events[:5]:  # 最大5件
                event_name = (
                    event.get("event", "")[:40] + "..."
                    if len(event.get("event", "")) > 40
                    else event.get("event", "")
                )
                country = event.get("country", "").title()
                time = event.get("time", "")
                medium_list.append(f"🟡 {country}: {event_name} ({time})")

            fields.append(
                {
                    "name": "🟡 中重要度イベント",
                    "value": "\n".join(medium_list) if medium_list else "なし",
                    "inline": False,
                }
            )

        if not fields:
            fields.append(
                {
                    "name": "📊 イベント",
                    "value": "この日は主要な経済指標の発表予定はありません",
                    "inline": False,
                }
            )

        success = await discord_client.send_embed(
            title=f"📆 {date_display}",
            description=f"この日の経済指標: {len(daily_events)}件",
            color=0x00C851 if high_events else 0xFFA500,
            fields=fields,
            footer={"text": "経済カレンダーシステム • 日別詳細"},
            timestamp=datetime.now(),
        )

        if success:
            logger.info(f"✅ 日別サマリー配信成功: {date}")
        else:
            logger.error(f"❌ 日別サマリー配信失敗: {date}")

    except Exception as e:
        logger.error(f"❌ 日別サマリー送信エラー: {e}")


async def send_high_importance_events(discord_client, high_events):
    """高重要度イベントの特別配信"""
    try:
        if not high_events:
            return

        description = "今週の特に注目すべき高重要度経済指標です。\nUSD/JPYへの影響が大きいと予想されます。\n\n"

        fields = []

        for i, event in enumerate(high_events[:8]):  # 最大8件
            event_name = event.get("event", "")
            country = event.get("country", "").title()
            date = event.get("date", "")
            time = event.get("time", "")
            forecast = event.get("forecast")
            previous = event.get("previous")

            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                date_display = date_obj.strftime("%m/%d (%a)")
            except:
                date_display = date

            value = f"📅 {date_display} {time}\n"
            if forecast is not None:
                value += f"予測: {forecast}\n"
            if previous is not None:
                value += f"前回: {previous}"

            fields.append(
                {"name": f"🔴 {country}: {event_name}", "value": value, "inline": True}
            )

        success = await discord_client.send_embed(
            title="🚨 今週の注目経済指標",
            description=description,
            color=0xFF0000,
            fields=fields,
            footer={"text": "経済カレンダーシステム • 高重要度特集"},
            timestamp=datetime.now(),
        )

        if success:
            logger.info(f"✅ 高重要度イベント配信成功: {len(high_events)}件")
        else:
            logger.error("❌ 高重要度イベント配信失敗")

    except Exception as e:
        logger.error(f"❌ 高重要度イベント送信エラー: {e}")


async def generate_weekly_ai_analysis_preview(events: List[Dict[str, Any]]):
    """週次AI分析プレビューの生成"""
    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            return False

        # 高重要度イベントのみを対象
        high_importance_events = [e for e in events if e.get("importance") == "high"]

        if not high_importance_events:
            logger.info("ℹ️ 週次AI分析対象の高重要度イベントなし")
            return True

        async with DiscordClient(webhook_url) as discord_client:
            for event in high_importance_events[:3]:  # 最大3件
                try:
                    # 週次AI分析プレビューの生成
                    preview_analysis = generate_weekly_event_preview(event)

                    success = await discord_client.send_embed(
                        title="🤖 週次AI分析プレビュー",
                        description=preview_analysis,
                        color=0x9C27B0,
                        footer={"text": "経済専門家による週次分析プレビュー"},
                        timestamp=datetime.now(),
                    )

                    if success:
                        logger.info(
                            f"✅ 週次AI分析プレビュー配信成功: {event.get('event', '')}"
                        )
                    else:
                        logger.error(
                            f"❌ 週次AI分析プレビュー配信失敗: {event.get('event', '')}"
                        )

                    await asyncio.sleep(5)  # レート制限対策: 5秒待機

                except Exception as e:
                    logger.error(f"❌ 週次AI分析プレビュー生成エラー: {e}")
                    continue

        return True

    except Exception as e:
        logger.error(f"❌ 週次AI分析プレビュー生成エラー: {e}")
        return False


def generate_weekly_event_preview(event: Dict[str, Any]) -> str:
    """週次イベントプレビューの生成"""
    country = event.get("country", "").title()
    event_name = event.get("event", "")
    date = event.get("date", "")
    time = event.get("time", "")
    forecast = event.get("forecast")
    previous = event.get("previous")

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_display = date_obj.strftime("%Y年%m月%d日 (%A)")
    except:
        date_display = date

    preview_parts = []

    # 基本情報
    preview_parts.append(f"📊 **{country} {event_name}**")
    preview_parts.append(f"📅 **発表予定**: {date_display} {time}")
    preview_parts.append("")

    # 予測値と前回値
    if forecast is not None or previous is not None:
        preview_parts.append("**数値情報**")
        if forecast is not None:
            preview_parts.append(f"• 市場予想: {forecast}")
        if previous is not None:
            preview_parts.append(f"• 前回値: {previous}")
        preview_parts.append("")

    # 簡易分析
    preview_parts.append("**週次展望**")

    if "CPI" in event_name or "物価" in event_name:
        preview_parts.append(
            f"{country}の消費者物価指数は、中央銀行の金融政策判断に重要な影響を与える指標です。今週の発表では、インフレ動向と政策金利の方向性に注目が集まります。USD/JPYへの影響は、市場予想との乖離度によって決まると予想されます。"
        )
    elif "GDP" in event_name or "国内総生産" in event_name:
        preview_parts.append(
            f"{country}の国内総生産は、経済の健全性を示す最重要指標です。今週の発表では、経済成長の持続性と将来見通しが焦点となります。好調な結果は{country}通貨の上昇要因となり、USD/JPYにも影響を与える可能性があります。"
        )
    elif "雇用" in event_name or "Payroll" in event_name:
        preview_parts.append(
            f"{country}の雇用統計は、経済活動と消費動向を反映する重要な指標です。今週の発表では、労働市場の健全性と賃金上昇圧力に注目が集まります。強い雇用データは金融政策の引き締め期待を高め、USD/JPYの動向に影響を与えると予想されます。"
        )
    elif "金利" in event_name or "Rate" in event_name:
        preview_parts.append(
            f"{country}の政策金利決定は、為替市場に直接的な影響を与える最重要イベントです。今週の発表では、政策変更の有無とともに、将来の政策方針に関するガイダンスが注目されます。USD/JPYは金利差の変化に敏感に反応すると予想されます。"
        )
    else:
        preview_parts.append(
            f"{country}の{event_name}は、経済の健全性を示す重要な指標として市場が注目しています。今週の発表では、経済動向の変化と政策当局の判断に与える影響が焦点となります。USD/JPYへの影響は、市場予想との乖離と他の経済指標との相関によって決まると予想されます。"
        )

    preview_parts.append("")
    preview_parts.append("**注目ポイント**")
    preview_parts.append("• 市場予想との乖離度")
    preview_parts.append("• 政策当局への影響")
    preview_parts.append("• USD/JPYへの波及効果")

    return "\n".join(preview_parts)


async def main():
    """メイン実行関数"""
    logger.info("🚀 週次経済指標自動配信開始")

    try:
        # 1週間分の経済指標データを取得
        events = await fetch_weekly_economic_calendar()

        if not events:
            logger.warning("⚠️ 取得した週次経済指標がありません")
            return

        # Discordに配信
        discord_success = await send_weekly_economic_indicators_to_discord(events)

        # AI分析プレビューの生成と配信
        ai_success = await generate_weekly_ai_analysis_preview(events)

        if discord_success and ai_success:
            logger.info("🎉 週次経済指標自動配信完了")
        else:
            logger.warning("⚠️ 週次配信の一部が失敗しました")

    except Exception as e:
        logger.error(f"❌ 週次経済指標自動配信エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
