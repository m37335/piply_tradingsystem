#!/usr/bin/env python3
"""
経済指標自動取得・Discord配信スクリプト
モックデータを使用して経済カレンダーデータを取得し、Discordに配信
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_economic_calendar():
    """経済カレンダーデータの取得（キャッシュ対応）"""
    try:
        # キャッシュマネージャーを初期化
        from scripts.cron.economic_calendar_cache_manager import (
            EconomicCalendarCacheManager,
        )

        cache_manager = EconomicCalendarCacheManager()
        await cache_manager.initialize()

        try:
            # 今日と明日の日付を取得
            today = datetime.now()
            tomorrow = today + timedelta(days=1)

            from_date = today.strftime("%d/%m/%Y")
            to_date = tomorrow.strftime("%d/%m/%Y")

            logger.info(f"📅 経済カレンダー取得開始: {from_date} - {to_date}")

            # キャッシュから取得を試行
            countries = ["japan", "united states", "euro zone", "united kingdom"]
            importances = ["high", "medium"]

            cached_events = await cache_manager.get_cached_economic_events(
                from_date, to_date, countries, importances, "daily"
            )

            if cached_events:
                logger.info(f"✅ キャッシュから経済指標取得: {len(cached_events)}件")
                return cached_events

            # キャッシュにない場合はAPIから取得
            logger.info("🔄 キャッシュにないため、APIから取得します")

            import investpy
            import pandas as pd

            # investpyで直接データ取得
            df = investpy.economic_calendar(
                from_date=from_date,
                to_date=to_date,
                countries=countries,
                importances=importances,
            )

            if df.empty:
                logger.warning("📊 取得された経済指標データが空です")
                fallback_data = await _get_fallback_mock_data()

                # フォールバックデータもキャッシュに保存
                await cache_manager.save_economic_events_cache(
                    fallback_data, from_date, to_date, countries, importances, "daily"
                )
                return fallback_data

            logger.info(f"📊 実際の経済指標取得: {len(df)}件")

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
                    logger.warning(f"⚠️ イベントデータ変換エラー: {e}")
                    continue

            # 取得したデータをキャッシュに保存
            await cache_manager.save_economic_events_cache(
                event_dicts, from_date, to_date, countries, importances, "daily"
            )

            return event_dicts

        finally:
            await cache_manager.close()

    except Exception as e:
        logger.error(f"❌ 経済カレンダー取得エラー: {e}")
        # エラー時はモックデータをフォールバック
        logger.info("🔄 モックデータにフォールバック")
        return await _get_fallback_mock_data()


async def _get_fallback_mock_data():
    """フォールバック用のモックデータ"""
    today = datetime.now()
    mock_events = [
        {
            "date": today.strftime("%Y-%m-%d"),
            "time": "08:30",
            "country": "japan",
            "event": "Consumer Price Index (CPI) y/y",
            "importance": "high",
            "currency": "JPY",
            "actual": 2.8,
            "forecast": 2.5,
            "previous": 2.3,
        },
        {
            "date": today.strftime("%Y-%m-%d"),
            "time": "12:30",
            "country": "united states",
            "event": "Non-Farm Payrolls",
            "importance": "high",
            "currency": "USD",
            "actual": 210000,
            "forecast": 185000,
            "previous": 180000,
        },
        {
            "date": today.strftime("%Y-%m-%d"),
            "time": "14:00",
            "country": "euro zone",
            "event": "ECB Interest Rate Decision",
            "importance": "high",
            "currency": "EUR",
            "actual": 4.50,
            "forecast": 4.25,
            "previous": 4.25,
        },
    ]
    return mock_events


async def send_economic_indicators_to_discord(events: List[Dict[str, Any]]):
    """経済指標をDiscordに配信"""
    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            logger.error("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        async with DiscordClient(webhook_url) as discord_client:
            logger.info("💬 Discord配信開始")

            # 重要度の高いイベントを優先
            high_importance_events = [
                e for e in events if e.get("importance") == "high"
            ]
            medium_importance_events = [
                e for e in events if e.get("importance") == "medium"
            ]

            # 高重要度イベントを配信
            for event in high_importance_events:
                try:
                    # イベントデータをDiscord用に変換
                    event_date = event.get("date", "")
                    event_time = event.get("time", "")

                    # 日付と時刻を組み合わせてdatetimeオブジェクトを作成
                    if event_date and event_time:
                        try:
                            # 日付と時刻を組み合わせてJSTのdatetimeを作成
                            datetime_str = f"{event_date} {event_time}"
                            event_datetime = datetime.strptime(
                                datetime_str, "%Y-%m-%d %H:%M"
                            )
                            # JSTとして扱い、ISO形式に変換
                            event_datetime_iso = event_datetime.isoformat()
                        except ValueError:
                            # パースに失敗した場合は現在時刻を使用
                            event_datetime_iso = datetime.now().isoformat()
                    else:
                        event_datetime_iso = datetime.now().isoformat()

                    discord_event_data = {
                        "event_id": f"event_{datetime.now().timestamp()}",
                        "date_utc": event_datetime_iso,
                        "country": event.get("country", ""),
                        "event_name": event.get("event", ""),
                        "importance": event.get("importance", "medium"),
                        "actual_value": event.get("actual"),
                        "forecast_value": event.get("forecast"),
                        "previous_value": event.get("previous"),
                        "currency": event.get("currency", ""),
                        "unit": "",
                    }

                    # 発表済みの場合はactual_announcement、未発表の場合はnew_event
                    notification_type = (
                        "actual_announcement" if event.get("actual") else "new_event"
                    )

                    success = await discord_client.send_economic_event_notification(
                        discord_event_data, notification_type
                    )

                    if success:
                        logger.info(
                            f"✅ 高重要度イベント配信成功: {event.get('event', '')}"
                        )
                    else:
                        logger.error(
                            f"❌ 高重要度イベント配信失敗: {event.get('event', '')}"
                        )

                    # レート制限を避けるため待機
                    await asyncio.sleep(2)

                except Exception as e:
                    logger.error(f"❌ イベント配信エラー: {e}")
                    continue

            # 中重要度イベントをまとめて配信
            if medium_importance_events:
                try:
                    # サマリー通知を作成
                    summary_fields = []
                    for event in medium_importance_events[:5]:  # 最大5件まで
                        event_name = (
                            event.get("event", "")[:30] + "..."
                            if len(event.get("event", "")) > 30
                            else event.get("event", "")
                        )
                        country = event.get("country", "")
                        time = event.get("time", "")

                        summary_fields.append(
                            {
                                "name": f"🇯🇵 {country.title()}",
                                "value": f"{event_name}\n⏰ {time}",
                                "inline": True,
                            }
                        )

                    success = await discord_client.send_embed(
                        title="📊 本日の経済指標サマリー",
                        description="中重要度の経済指標一覧",
                        color=0x0099FF,
                        fields=summary_fields,
                        footer={"text": "経済カレンダーシステム • 自動配信"},
                        timestamp=datetime.now(),
                    )

                    if success:
                        logger.info(
                            f"✅ 中重要度イベントサマリー配信成功: {len(medium_importance_events)}件"
                        )
                    else:
                        logger.error("❌ 中重要度イベントサマリー配信失敗")

                except Exception as e:
                    logger.error(f"❌ サマリー配信エラー: {e}")

            logger.info("✅ Discord配信完了")
            return True

    except Exception as e:
        logger.error(f"❌ Discord配信エラー: {e}")
        return False


async def generate_ai_analysis_for_events(events: List[Dict[str, Any]]):
    """経済指標に対する段階的AI分析を生成"""
    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            return False

        # 発表済みの高重要度イベントに対してAI分析を生成
        announced_high_events = [
            e
            for e in events
            if e.get("importance") == "high" and e.get("actual") is not None
        ]

        if not announced_high_events:
            logger.info("ℹ️ AI分析対象の発表済み高重要度イベントなし")
            return True

        async with DiscordClient(webhook_url) as discord_client:
            for event in announced_high_events[:3]:  # 最大3件まで
                try:
                    # 1. 基本分析（即座配信）
                    basic_analysis = generate_basic_economic_analysis(event)

                    ai_report_data = {
                        "event_id": f"ai_analysis_{datetime.now().timestamp()}",
                        "event_name": event.get("event", ""),
                        "country": event.get("country", ""),
                        "date_utc": event.get("date", ""),
                        "report_type": "post_event",
                        "report_content": basic_analysis,
                        "usd_jpy_prediction": {
                            "direction": (
                                "bullish"
                                if event.get("actual", 0) > event.get("forecast", 0)
                                else "bearish"
                            ),
                            "strength": (
                                "strong"
                                if abs(
                                    event.get("actual", 0) - event.get("forecast", 0)
                                )
                                > 0.1
                                else "medium"
                            ),
                            "confidence_score": 0.75,
                            "reasons": generate_analysis_reasons(event),
                            "timeframe": "1-4時間",
                            "target_price": "148.50-150.00",
                        },
                        "confidence_score": 0.75,
                    }

                    success = await discord_client.send_ai_report_notification(
                        ai_report_data
                    )

                    if success:
                        logger.info(f"✅ 基本分析配信成功: {event.get('event', '')}")
                    else:
                        logger.error(f"❌ 基本分析配信失敗: {event.get('event', '')}")

                    # レート制限を避けるため待機
                    await asyncio.sleep(3)

                    # 2. 詳細専門分析（5分後配信）
                    detailed_analysis = generate_detailed_expert_analysis(event)
                    if detailed_analysis:
                        detailed_success = await send_detailed_analysis(
                            discord_client, event, detailed_analysis
                        )
                        if detailed_success:
                            logger.info(
                                f"✅ 詳細分析配信成功: {event.get('event', '')}"
                            )

                    await asyncio.sleep(3)

                    # 3. 投資戦略分析（10分後配信）
                    strategy_analysis = generate_investment_strategy_analysis(event)
                    if strategy_analysis:
                        strategy_success = await send_strategy_analysis(
                            discord_client, event, strategy_analysis
                        )
                        if strategy_success:
                            logger.info(
                                f"✅ 戦略分析配信成功: {event.get('event', '')}"
                            )

                    await asyncio.sleep(3)

                except Exception as e:
                    logger.error(f"❌ AI分析生成エラー: {e}")
                    continue

        return True

    except Exception as e:
        logger.error(f"❌ AI分析生成エラー: {e}")
        return False


def generate_basic_economic_analysis(event: Dict[str, Any]) -> str:
    """経済指標の基本分析を生成（エコノミスト記事形式）"""
    country = event.get("country", "").title()
    event_name = event.get("event", "")
    actual = event.get("actual")
    forecast = event.get("forecast")
    previous = event.get("previous")
    currency = event.get("currency", "")

    # サプライズ度の計算
    surprise = 0
    if forecast and actual:
        try:
            if isinstance(actual, (int, float)) and isinstance(forecast, (int, float)):
                if forecast != 0:
                    surprise = ((actual - forecast) / abs(forecast)) * 100
        except Exception:
            pass

    # 文章形式の分析を生成
    analysis_parts = []

    # 1. ヘッドライン
    analysis_parts.append(f"📊 **{country} {event_name} - 経済分析レポート**")
    analysis_parts.append("")

    # 2. 基本情報
    analysis_parts.append(
        f"**発表結果**: {country}の{event_name}は{actual}{currency}で発表されました。市場予想の{forecast}{currency}を{actual - forecast if actual and forecast else 0}{currency}上回る結果となり、"
    )

    if abs(surprise) > 15:
        analysis_parts.append("市場に大きなサプライズを与えました。")
    elif abs(surprise) > 10:
        analysis_parts.append("市場予想を大きく上回る結果でした。")
    elif abs(surprise) > 5:
        analysis_parts.append("市場予想を上回る結果でした。")
    else:
        analysis_parts.append("市場予想に近い結果でした。")

    # 3. 経済学的背景
    analysis_parts.append("")
    analysis_parts.append("**経済学的背景**")

    if "CPI" in event_name or "物価" in event_name:
        analysis_parts.append(
            f"{country}の消費者物価指数（CPI）は、経済全体の価格水準を測定する最も重要な指標の一つです。この指標は中央銀行が金融政策を決定する際の核心的な判断材料として機能しており、インフレ率の動向を正確に把握することで、経済の健全性と購買力の変化を評価することができます。"
        )
    elif "GDP" in event_name or "国内総生産" in event_name:
        analysis_parts.append(
            f"{country}の国内総生産（GDP）は、一国の経済活動の総合的な尺度として機能します。この指標は景気循環の判断基準として極めて重要であり、企業の業績動向や雇用情勢に密接に関連しているため、経済全体の健康状態を評価する上で不可欠な指標となっています。"
        )
    elif "雇用" in event_name or "Payroll" in event_name:
        analysis_parts.append(
            f"{country}の雇用統計は、経済の健全性を示す最も信頼性の高い指標の一つです。雇用情勢は消費動向と賃金上昇圧力に直接的な影響を与えるため、中央銀行が金融政策を決定する際の重要な判断材料として機能します。"
        )
    elif "金利" in event_name or "Rate" in event_name:
        analysis_parts.append(
            f"{country}の政策金利は、金融政策の中心的な手段として機能します。この金利は経済活動とインフレ率を調整する重要な役割を果たし、為替レートに直接的な影響を与えるため、国際金融市場において最も注目される指標の一つです。"
        )
    else:
        analysis_parts.append(
            f"{country}の{event_name}は、経済の健全性を示す重要な指標として市場が注目しています。この指標は政策当局の判断材料として機能し、経済全体の動向を評価する上で重要な役割を果たします。"
        )

    # 4. 政策への影響
    analysis_parts.append("")
    analysis_parts.append("**政策への影響**")

    if surprise > 10:
        analysis_parts.append(
            f"今回の結果を受けて、{country}の中央銀行は金融引き締め強化の可能性が高まっています。金利上昇サイクルの継続が期待され、量的緩和の縮小も加速する可能性があります。政策当局は、インフレ圧力の継続を懸念し、より積極的な政策対応を検討する可能性があります。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"今回の結果は、{country}の中央銀行が段階的な金融引き締めを継続することを示唆しています。政策当局は慎重な政策運営を継続し、データ依存的な政策判断を行うことが予想されます。今後の経済指標の動向が、政策変更のタイミングを決定する重要な要素となります。"
        )
    elif surprise < -10:
        analysis_parts.append(
            f"今回の結果を受けて、{country}の中央銀行は金融緩和継続の可能性が高まっています。金利据え置き期間の延長が期待され、必要に応じて追加緩和策の検討も行われる可能性があります。政策当局は、経済の下振れリスクを重視し、より緩和的な政策スタンスを維持することが予想されます。"
        )
    elif surprise < -5:
        analysis_parts.append(
            f"今回の結果は、{country}の中央銀行が金融緩和継続の可能性を示唆しています。政策当局は慎重な政策運営を継続し、追加データの監視を強化することが予想されます。経済の回復力に対する懸念が高まっており、政策変更のタイミングは慎重に判断されることになります。"
        )
    else:
        analysis_parts.append(
            f"今回の結果は、{country}の中央銀行が現行政策を継続することを示唆しています。政策変更の可能性は低く、追加データの監視を継続することが予想されます。経済は安定した成長軌道を維持しており、政策当局は現状の政策スタンスを維持することが適切と判断されるでしょう。"
        )

    # 5. 市場への影響
    analysis_parts.append("")
    analysis_parts.append("**市場への影響**")

    if surprise > 10:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して強い上昇圧力をもたらすことが予想されます。短期的なボラティリティの増加が見込まれ、リスク資産への資金流入が加速する可能性があります。投資家は、より積極的なリスクテイクを選択し、成長関連資産への投資を増加させることが予想されます。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して中程度の上昇圧力をもたらすことが予想されます。段階的な価格調整が進行し、慎重な市場環境が続くことが予想されます。投資家は、リスクとリターンのバランスを考慮した投資判断を行うことが重要となります。"
        )
    elif surprise < -10:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して強い下落圧力をもたらすことが予想されます。リスク回避需要の増加が見込まれ、安全資産への資金流入が加速する可能性があります。投資家は、より保守的な投資戦略を選択し、リスク管理を重視することが予想されます。"
        )
    elif surprise < -5:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して中程度の下落圧力をもたらすことが予想されます。慎重な市場環境が続き、リスク回避の動きが強まることが予想されます。投資家は、リスク管理を重視した投資判断を行うことが重要となります。"
        )
    else:
        analysis_parts.append(
            f"今回の結果は、市場への影響は限定的であることが予想されます。既存のトレンドが継続し、安定した市場環境が維持されることが予想されます。投資家は、現状の投資戦略を継続し、追加の経済指標の発表を待つことが適切と判断されるでしょう。"
        )

    return "\n".join(analysis_parts)


def generate_detailed_expert_analysis(event: Dict[str, Any]) -> str:
    """経済専門家による詳細分析を生成（エコノミスト記事形式）"""
    country = event.get("country", "").title()
    event_name = event.get("event", "")
    actual = event.get("actual")
    forecast = event.get("forecast")

    # サプライズ度の計算
    surprise = 0
    if forecast and actual:
        try:
            if isinstance(actual, (int, float)) and isinstance(forecast, (int, float)):
                if forecast != 0:
                    surprise = ((actual - forecast) / abs(forecast)) * 100
        except Exception:
            pass

    analysis_parts = []

    # 1. マクロ経済学的背景
    analysis_parts.append(f"🎓 **{country} {event_name} - 専門経済分析**")
    analysis_parts.append("")
    analysis_parts.append("**マクロ経済学的背景**")

    if "CPI" in event_name or "物価" in event_name:
        analysis_parts.append(
            f"今回の{country}の消費者物価指数の動向は、フィリップス曲線理論の観点から分析する必要があります。この理論によれば、インフレ率と失業率の間には短期的なトレードオフ関係が存在し、現在の雇用情勢を考慮すると、インフレ圧力の持続性について慎重な評価が必要です。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "また、貨幣数量説の観点から見ると、マネーサプライと物価水準の関係性が重要となります。中央銀行の金融政策が物価水準に与える影響を理解することで、今後のインフレ動向をより正確に予測することが可能になります。さらに、期待インフレ理論の観点から、市場参加者の将来予想が現在の物価動向に与える影響も考慮する必要があります。"
        )
    elif "GDP" in event_name or "国内総生産" in event_name:
        analysis_parts.append(
            f"今回の{country}の国内総生産の動向は、経済成長理論の観点から分析する必要があります。長期的な成長要因として、労働力、資本、技術進歩の貢献度を評価することで、持続可能な成長パスの可能性を判断することができます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "景気循環理論の観点からは、短期的な変動要因として、在庫投資、設備投資、消費動向の変化を分析する必要があります。これらの要因の相互作用を理解することで、現在の経済局面と今後の見通しをより正確に評価することが可能になります。さらに、生産性理論の観点から、労働生産性の変化が経済成長に与える影響も重要な分析要素となります。"
        )
    elif "雇用" in event_name or "Payroll" in event_name:
        analysis_parts.append(
            f"今回の{country}の雇用統計は、労働市場理論の観点から分析する必要があります。労働需給のバランスが賃金上昇圧力に与える影響を理解することで、インフレ動向と経済成長の持続性を評価することができます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "賃金理論の観点からは、現在の賃金上昇圧力が企業の収益性と雇用創出に与える影響を分析する必要があります。また、労働参加率の変化が潜在成長率に与える影響も重要な分析要素となります。これらの要因を総合的に評価することで、労働市場の健全性と経済全体の見通しをより正確に判断することが可能になります。"
        )
    elif "金利" in event_name or "Rate" in event_name:
        analysis_parts.append(
            f"今回の{country}の政策金利決定は、金融政策理論の観点から分析する必要があります。金利と経済活動の関係性を理解することで、政策効果の波及経路とタイムラグを評価することができます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "流動性選好理論の観点からは、金利と貨幣需要の関係性が重要となります。市場参加者の流動性選好の変化が金利水準に与える影響を理解することで、金融市場の動向をより正確に予測することが可能になります。さらに、期待理論の観点から、将来金利予想が現在の市場動向に与える影響も考慮する必要があります。"
        )

    # 2. 国際金融市場への影響
    analysis_parts.append("")
    analysis_parts.append("**国際金融市場への影響**")

    if surprise > 10:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して強い上昇圧力をもたらすことが予想されます。国際金融市場において、為替レートは2-3%の上昇が予想され、国際資本フローの加速が見込まれます。リスクプレミアムの縮小傾向が続くことで、より積極的なリスクテイクが促進される可能性があります。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"国際投資家の観点からは、{country}の経済指標の改善が投資魅力の向上につながる可能性があります。特に、機関投資家の資産配分において、{country}資産の比率増加が期待されます。また、ヘッジファンドの戦略においても、{country}通貨の強気ポジション構築が加速する可能性があります。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して中程度の上昇圧力をもたらすことが予想されます。国際金融市場において、為替レートは1-2%の上昇が予想され、段階的な国際資本フローの流入が見込まれます。リスクプレミアムは安定傾向を維持し、市場の安定性が確保されることが予想されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"国際投資家の観点からは、{country}の経済指標の改善が投資判断にプラスの影響を与える可能性があります。ただし、他の経済指標との総合的な評価が重要となり、段階的な投資判断が行われることが予想されます。"
        )
    elif surprise < -10:
        analysis_parts.append(
            f"今回の結果は、{country}の通貨に対して強い下落圧力をもたらすことが予想されます。国際金融市場において、為替レートは2-3%の下落が予想され、国際資本フローの流出が加速する可能性があります。リスクプレミアムの拡大傾向が続くことで、より保守的な投資戦略が選択されることが予想されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"国際投資家の観点からは、{country}の経済指標の悪化が投資魅力の低下につながる可能性があります。特に、機関投資家の資産配分において、{country}資産の比率減少が期待されます。また、ヘッジファンドの戦略においても、{country}通貨の弱気ポジション構築が加速する可能性があります。"
        )
    else:
        analysis_parts.append(
            f"今回の結果は、国際金融市場への影響は限定的であることが予想されます。為替レートの変動は小幅にとどまり、国際資本フローも安定した流れを維持することが予想されます。リスクプレミアムに大きな変化はなく、市場の安定性が確保されることが予想されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"国際投資家の観点からは、{country}の経済指標は既存の投資判断に大きな影響を与えることはないと予想されます。他の経済指標との総合的な評価が重要となり、現状の投資戦略が継続されることが予想されます。"
        )

    # 3. 政策当局の対応予測
    analysis_parts.append("")
    analysis_parts.append("**政策当局の対応予測**")

    if surprise > 10:
        analysis_parts.append(
            f"今回の結果を受けて、{country}の中央銀行は積極的な金融引き締め強化を検討する可能性があります。インフレ圧力の継続を懸念し、より積極的な政策対応が必要と判断される可能性があります。政府においても、財政政策の調整を検討する可能性があり、経済の過熱を抑制するための政策パッケージが検討されることが予想されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "規制当局においては、金融安定性の監視を強化することが予想されます。特に、金融機関の健全性と市場の安定性を確保するための追加的な規制措置が検討される可能性があります。政策当局全体として、経済の持続可能な成長を確保するための包括的な政策対応が行われることが予想されます。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"今回の結果を受けて、{country}の中央銀行は段階的な金融引き締めを継続することが予想されます。経済の改善傾向を確認しつつ、慎重な政策運営を継続することが適切と判断されるでしょう。政府においても、現行の財政政策を継続し、経済の安定成長を支援することが予想されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "規制当局においては、通常の監視体制を維持することが予想されます。市場の安定性を確保しつつ、経済の健全な発展を支援するための規制環境を維持することが重要となります。政策当局全体として、データ依存的な政策判断を行い、経済の状況に応じた柔軟な対応を継続することが予想されます。"
        )
    else:
        analysis_parts.append(
            f"今回の結果を受けて、{country}の中央銀行は現行政策を継続することが予想されます。経済の安定性を確認しつつ、政策変更の必要性は低いと判断されるでしょう。政府においても、現行の財政政策を継続し、経済の安定成長を支援することが予想されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "規制当局においては、安定した監視体制を維持することが予想されます。市場の安定性を確保しつつ、経済の健全な発展を支援するための規制環境を維持することが重要となります。政策当局全体として、現状の政策スタンスを維持し、経済の安定性を確保することが予想されます。"
        )

    return "\n".join(analysis_parts)


def generate_investment_strategy_analysis(event: Dict[str, Any]) -> str:
    """投資戦略分析を生成（エコノミスト記事形式）"""
    country = event.get("country", "").title()
    event_name = event.get("event", "")
    actual = event.get("actual")
    forecast = event.get("forecast")

    # サプライズ度の計算
    surprise = 0
    if forecast and actual:
        try:
            if isinstance(actual, (int, float)) and isinstance(forecast, (int, float)):
                if forecast != 0:
                    surprise = ((actual - forecast) / abs(forecast)) * 100
        except Exception:
            pass

    analysis_parts = []

    # 1. 短期戦略（1-4時間）
    analysis_parts.append(f"📈 **{country} {event_name} - 投資戦略分析**")
    analysis_parts.append("")
    analysis_parts.append("**短期戦略（1-4時間）**")

    if surprise > 10:
        analysis_parts.append(
            f"今回の{country}の{event_name}の結果を受けて、短期戦略として強気ポジションの構築を推奨します。市場の反応を考慮すると、即座の行動が必要であり、USD/JPYにおいて148.00をストップロスとして設定した強気ポジションの構築が適切と判断されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "利益確定については、149.50-150.00の範囲で段階的な決済を行うことを推奨します。市場のボラティリティを考慮し、リスク管理を重視した取引戦略が重要となります。特に、短期的な価格変動に備えて、適切なポジションサイズの設定が不可欠です。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"今回の{country}の{event_name}の結果を受けて、短期戦略として中程度の強気ポジションの構築を推奨します。市場の反応を考慮すると、慎重な行動が必要であり、USD/JPYにおいて148.20をストップロスとして設定した中程度の強気ポジションが適切と判断されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "利益確定については、149.00-149.50の範囲で決済を行うことを推奨します。市場の安定性を考慮し、リスクとリターンのバランスを重視した取引戦略が重要となります。段階的な利益確定により、リスク管理を徹底することが重要です。"
        )
    elif surprise < -10:
        analysis_parts.append(
            f"今回の{country}の{event_name}の結果を受けて、短期戦略として弱気ポジションの構築を推奨します。市場の反応を考慮すると、即座の行動が必要であり、USD/JPYにおいて148.80をストップロスとして設定した弱気ポジションの構築が適切と判断されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "利益確定については、147.50-148.00の範囲で段階的な決済を行うことを推奨します。市場のボラティリティを考慮し、リスク管理を重視した取引戦略が重要となります。特に、短期的な価格変動に備えて、適切なポジションサイズの設定が不可欠です。"
        )
    else:
        analysis_parts.append(
            f"今回の{country}の{event_name}の結果を受けて、短期戦略として様子見の継続を推奨します。市場の反応を考慮すると、明確な方向性を待つことが適切と判断されます。既存ポジションの維持を基本とし、追加の経済指標の発表を待つことが重要となります。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "利益確定については、明確な方向性が確認されるまで待機することを推奨します。市場の安定性を考慮し、リスク管理を重視した投資判断が重要となります。段階的な情報収集により、より適切な投資判断を行うことが重要です。"
        )

    # 2. 中期戦略（1-7日）
    analysis_parts.append("")
    analysis_parts.append("**中期戦略（1-7日）**")

    if surprise > 10:
        analysis_parts.append(
            f"中期戦略として、強気ポジションの拡大を推奨します。今回の{country}の{event_name}の結果は、経済の改善傾向を示しており、今後1週間において強気ポジションの拡大が適切と判断されます。次回の経済指標の発表を監視し、継続的な改善傾向を確認することが重要となります。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "ポートフォリオ戦略としては、リスク資産の比率増加を推奨します。経済の改善傾向を考慮し、より積極的なリスクテイクが適切と判断されます。ただし、リスク管理を重視し、適切な分散投資を維持することが重要です。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"中期戦略として、段階的な強気ポジションの構築を推奨します。今回の{country}の{event_name}の結果は、経済の改善傾向を示しており、今後1週間において段階的な強気ポジションの構築が適切と判断されます。政策当局の発言を監視し、政策動向の変化を確認することが重要となります。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "ポートフォリオ戦略としては、バランスの取れた構成を推奨します。経済の改善傾向を考慮しつつ、リスク管理を重視した投資判断が適切と判断されます。適切な分散投資を維持し、リスクとリターンのバランスを重視することが重要です。"
        )
    else:
        analysis_parts.append(
            f"中期戦略として、現状維持を推奨します。今回の{country}の{event_name}の結果は、経済の安定性を示しており、今後1週間において現状の投資戦略の継続が適切と判断されます。追加データの監視を継続し、経済動向の変化を確認することが重要となります。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            "ポートフォリオ戦略としては、現行構成の継続を推奨します。経済の安定性を考慮し、現状の投資戦略の継続が適切と判断されます。適切な分散投資を維持し、リスク管理を重視した投資判断が重要です。"
        )

    # 3. 長期戦略（1-4週間）
    analysis_parts.append("")
    analysis_parts.append("**長期戦略（1-4週間）**")

    if surprise > 10:
        analysis_parts.append(
            f"長期戦略として、上昇トレンドの確立可能性を考慮した投資戦略を推奨します。今回の{country}の{event_name}の結果は、経済の根本的な改善を示しており、今後1-4週間において上昇トレンドの確立が期待されます。投資機会としては、金融・輸出関連セクターへの投資が適切と判断されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"リスク分散戦略としては、地域分散の見直しを推奨します。{country}の経済改善を考慮し、より積極的な地域分散が適切と判断されます。ただし、グローバルな経済動向を考慮し、適切なリスク管理を維持することが重要です。"
        )
    elif surprise > 5:
        analysis_parts.append(
            f"長期戦略として、緩やかな上昇トレンドを考慮した投資戦略を推奨します。今回の{country}の{event_name}の結果は、経済の改善傾向を示しており、今後1-4週間において緩やかな上昇トレンドが期待されます。投資機会としては、景気敏感セクターへの投資が適切と判断されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"リスク分散戦略としては、セクター分散の調整を推奨します。{country}の経済改善を考慮し、より積極的なセクター分散が適切と判断されます。ただし、リスク管理を重視し、適切な分散投資を維持することが重要です。"
        )
    else:
        analysis_parts.append(
            f"長期戦略として、既存トレンドの継続を考慮した投資戦略を推奨します。今回の{country}の{event_name}の結果は、経済の安定性を示しており、今後1-4週間において既存トレンドの継続が期待されます。投資機会としては、防御的セクターへの投資が適切と判断されます。"
        )
        analysis_parts.append("")
        analysis_parts.append(
            f"リスク分散戦略としては、現行分散の維持を推奨します。{country}の経済安定性を考慮し、現状の分散投資戦略の継続が適切と判断されます。リスク管理を重視し、安定した投資戦略を維持することが重要です。"
        )

    return "\n".join(analysis_parts)


async def send_detailed_analysis(
    discord_client, event: Dict[str, Any], analysis: str
) -> bool:
    """詳細分析をDiscordに送信"""
    try:
        # 分析を複数のメッセージに分割
        messages = split_long_message(analysis, 1900)  # Discord制限を考慮

        for i, message in enumerate(messages):
            title = (
                f"🎓 専門分析 ({i+1}/{len(messages)})"
                if len(messages) > 1
                else "🎓 専門分析"
            )

            success = await discord_client.send_embed(
                title=title,
                description=message,
                color=0x0099FF,
                footer={"text": "経済専門家による詳細分析"},
                timestamp=datetime.now(),
            )

            if not success:
                return False

            # 複数メッセージの場合は待機
            if len(messages) > 1:
                await asyncio.sleep(2)

        return True

    except Exception as e:
        logger.error(f"❌ 詳細分析送信エラー: {e}")
        return False


async def send_strategy_analysis(
    discord_client, event: Dict[str, Any], analysis: str
) -> bool:
    """投資戦略分析をDiscordに送信"""
    try:
        success = await discord_client.send_embed(
            title="📈 投資戦略分析",
            description=analysis,
            color=0x00C851,
            footer={"text": "投資戦略専門家による分析"},
            timestamp=datetime.now(),
        )

        return success

    except Exception as e:
        logger.error(f"❌ 戦略分析送信エラー: {e}")
        return False


def split_long_message(message: str, max_length: int) -> List[str]:
    """長いメッセージを分割"""
    if len(message) <= max_length:
        return [message]

    parts = []
    current_part = ""

    for line in message.split("\n"):
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + "\n"
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = line + "\n"

    if current_part:
        parts.append(current_part.strip())

    return parts


def generate_analysis_reasons(event: Dict[str, Any]) -> List[str]:
    """分析理由を生成"""
    reasons = []

    country = event.get("country", "").title()
    event_name = event.get("event", "")
    actual = event.get("actual")
    forecast = event.get("forecast")

    # 基本理由
    reasons.append(f"{country}の{event_name}の結果")

    # サプライズ度に応じた理由
    if actual and forecast:
        try:
            surprise = ((actual - forecast) / abs(forecast)) * 100
            if abs(surprise) > 10:
                reasons.append("市場予想との大幅な乖離")
            else:
                reasons.append("市場予想との乖離")
        except:
            reasons.append("市場予想との乖離")

    # 経済指標別の理由
    if "CPI" in event_name or "物価" in event_name:
        reasons.append("インフレ圧力への影響")
        reasons.append("中央銀行政策への影響")
    elif "GDP" in event_name or "国内総生産" in event_name:
        reasons.append("経済成長への影響")
        reasons.append("企業業績への影響")
    elif "雇用" in event_name or "Payroll" in event_name:
        reasons.append("雇用市場への影響")
        reasons.append("消費動向への影響")
    elif "金利" in event_name or "Rate" in event_name:
        reasons.append("金融政策への影響")
        reasons.append("金利動向への影響")
    else:
        reasons.append("経済指標の重要性")
        reasons.append("市場心理への影響")

    return reasons


async def main():
    """メイン関数"""
    logger.info("🚀 経済指標自動配信開始")

    try:
        # 1. 経済カレンダーデータの取得
        events = await fetch_economic_calendar()

        if not events:
            logger.warning("⚠️ 取得した経済指標がありません")
            return

        # 2. Discord配信
        discord_success = await send_economic_indicators_to_discord(events)

        # 3. AI分析生成・配信
        ai_success = await generate_ai_analysis_for_events(events)

        logger.info("🎉 経済指標自動配信完了")

    except Exception as e:
        logger.error(f"❌ 経済指標自動配信エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
