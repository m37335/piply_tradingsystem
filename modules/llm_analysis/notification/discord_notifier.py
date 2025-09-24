"""
Discord配信システム

シナリオ作成・エントリー・エグジット通知をDiscordで配信するシステム。
"""

import logging
import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import os
from dotenv import load_dotenv

from ..core.scenario_manager import Scenario, Trade, ExitReason, TradeDirection
from ..core.snapshot_manager import TradeSnapshot, MarketSnapshot
from ..evaluation.daily_evaluator import DailyPerformance, WeeklyReport


class NotificationType(Enum):
    """通知タイプ"""
    SCENARIO_CREATED = "scenario_created"
    RULE_EVALUATION = "rule_evaluation"
    ENTRY_SIGNAL = "entry_signal"
    EXIT_SIGNAL = "exit_signal"
    DAILY_REPORT = "daily_report"
    WEEKLY_REPORT = "weekly_report"
    ERROR_ALERT = "error_alert"


@dataclass
class DiscordEmbed:
    """Discord埋め込みメッセージ"""
    title: str
    description: str
    color: int
    fields: List[Dict[str, Any]]
    footer: Optional[Dict[str, str]] = None
    timestamp: Optional[str] = None
    thumbnail: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, str]] = None


@dataclass
class DiscordMessage:
    """Discordメッセージ"""
    content: Optional[str] = None
    embeds: Optional[List[DiscordEmbed]] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class DiscordNotifier:
    """Discord配信システム"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._lock = None
        
        # 環境変数の読み込み
        load_dotenv()
        
        # Discord設定
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        self.channel_id = os.getenv('DISCORD_CHANNEL_ID')
        self.bot_token = os.getenv('DISCORD_BOT_TOKEN')
        
        # 通知設定
        self.notification_settings = {
            "scenario_created": True,
            "rule_evaluation": True,
            "entry_signals": True,
            "exit_signals": True,
            "daily_reports": True,
            "weekly_reports": True,
            "error_alerts": True
        }
        
        # メッセージ設定
        self.message_settings = {
            "embed_color_scenario": 0xffff00,  # 黄（シナリオ作成）
            "embed_color_entry": 0x00ff00,     # 緑（エントリー）
            "embed_color_exit": 0xff0000,      # 赤（エグジット）
            "embed_color_report": 0x0099ff,    # 青（レポート）
            "embed_color_error": 0xff4500,     # オレンジ（エラー）
            "include_technical_details": True,
            "include_risk_metrics": True,
            "thread_creation": True
        }
        
        # セッション
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """初期化"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if self.session is None:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30)
                )
                self.logger.info("✅ Discord配信システム初期化完了")

    async def send_scenario_created(self, scenario: Scenario) -> bool:
        """
        シナリオ作成通知の送信
        
        Args:
            scenario: 作成されたシナリオ
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["scenario_created"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_scenario_created_message(scenario)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ シナリオ作成通知送信完了: {scenario.id}")
            else:
                self.logger.error(f"❌ シナリオ作成通知送信失敗: {scenario.id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ シナリオ作成通知送信エラー: {e}")
            return False

    async def send_entry_signal(self, trade: Trade, scenario: Scenario, entry_snapshot: MarketSnapshot) -> bool:
        """
        エントリーシグナル通知の送信
        
        Args:
            trade: エントリートレード
            scenario: シナリオ
            entry_snapshot: エントリー時のスナップショット
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["entry_signals"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_entry_signal_message(trade, scenario, entry_snapshot)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ エントリーシグナル通知送信完了: {trade.id}")
            else:
                self.logger.error(f"❌ エントリーシグナル通知送信失敗: {trade.id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ エントリーシグナル通知送信エラー: {e}")
            return False

    async def send_exit_signal(self, trade: Trade, exit_snapshot: MarketSnapshot) -> bool:
        """
        エグジットシグナル通知の送信
        
        Args:
            trade: エグジットトレード
            exit_snapshot: エグジット時のスナップショット
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["exit_signals"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_exit_signal_message(trade, exit_snapshot)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ エグジットシグナル通知送信完了: {trade.id}")
            else:
                self.logger.error(f"❌ エグジットシグナル通知送信失敗: {trade.id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ エグジットシグナル通知送信エラー: {e}")
            return False

    async def send_rule_evaluation_results(self, symbol: str, signals: List[Dict], analysis_time: datetime) -> bool:
        """
        ルール評価結果通知の送信
        
        Args:
            symbol: 通貨ペア
            signals: エントリーシグナルリスト
            analysis_time: 分析時刻
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["rule_evaluation"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_rule_evaluation_message(symbol, signals, analysis_time)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ ルール評価結果通知送信完了: {symbol} ({len(signals)}個のシグナル)")
            else:
                self.logger.error(f"❌ ルール評価結果通知送信失敗: {symbol}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ ルール評価結果通知送信エラー: {e}")
            return False

    async def send_daily_report(self, daily_performance: DailyPerformance) -> bool:
        """
        日次レポート通知の送信
        
        Args:
            daily_performance: 日次パフォーマンス
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["daily_reports"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_daily_report_message(daily_performance)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ 日次レポート通知送信完了: {daily_performance.date.date()}")
            else:
                self.logger.error(f"❌ 日次レポート通知送信失敗: {daily_performance.date.date()}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 日次レポート通知送信エラー: {e}")
            return False

    async def send_weekly_report(self, weekly_report: WeeklyReport) -> bool:
        """
        週次レポート通知の送信
        
        Args:
            weekly_report: 週次レポート
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["weekly_reports"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_weekly_report_message(weekly_report)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ 週次レポート通知送信完了: {weekly_report.week_start.date()}")
            else:
                self.logger.error(f"❌ 週次レポート通知送信失敗: {weekly_report.week_start.date()}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 週次レポート通知送信エラー: {e}")
            return False

    async def send_error_alert(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        エラーアラート通知の送信
        
        Args:
            error_message: エラーメッセージ
            error_details: エラー詳細
        
        Returns:
            送信成功可否
        """
        if not self.notification_settings["error_alerts"]:
            return True
        
        try:
            await self.initialize()
            
            # メッセージの作成
            message = self._create_error_alert_message(error_message, error_details)
            
            # 送信
            success = await self._send_message(message)
            
            if success:
                self.logger.info(f"✅ エラーアラート通知送信完了: {error_message[:50]}...")
            else:
                self.logger.error(f"❌ エラーアラート通知送信失敗: {error_message[:50]}...")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ エラーアラート通知送信エラー: {e}")
            return False

    def _create_scenario_created_message(self, scenario: Scenario) -> DiscordMessage:
        """シナリオ作成メッセージの作成"""
        # 埋め込みフィールドの作成
        fields = [
            {
                "name": "🎯 シナリオID",
                "value": f"`{scenario.id}`",
                "inline": True
            },
            {
                "name": "📋 戦略",
                "value": f"`{scenario.strategy}`",
                "inline": True
            },
            {
                "name": "⏱️ 有効期限",
                "value": f"<t:{int(scenario.expires_at.timestamp())}:R>",
                "inline": True
            },
            {
                "name": "📊 方向",
                "value": f"`{scenario.direction.value}`",
                "inline": True
            },
            {
                "name": "🎯 エントリー価格",
                "value": f"`{scenario.entry_conditions.get('entry_price', 'N/A')}`",
                "inline": True
            },
            {
                "name": "🛑 ストップロス",
                "value": f"`{scenario.entry_conditions.get('stop_loss', 'N/A')}`",
                "inline": True
            }
        ]
        
        # テイクプロフィットの追加
        for i, tp in enumerate(['take_profit_1', 'take_profit_2', 'take_profit_3'], 1):
            if tp in scenario.entry_conditions:
                fields.append({
                    "name": f"💰 TP{i}",
                    "value": f"`{scenario.entry_conditions[tp]}`",
                    "inline": True
                })
        
        # テクニカル状況の追加
        if self.message_settings["include_technical_details"]:
            technical_summary = scenario.entry_conditions.get("technical_summary", {})
            if technical_summary:
                tech_text = "\n".join([f"**{tf}**: {data}" for tf, data in technical_summary.items()])
                fields.append({
                    "name": "🔍 テクニカル状況",
                    "value": tech_text[:1024],  # Discord制限
                    "inline": False
                })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="🟡 SCENARIO CREATED 🟡",
            description=f"**USD/JPY** | {scenario.strategy}",
            color=self.message_settings["embed_color_scenario"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return DiscordMessage(
            content="新しい売買シナリオが作成されました！",
            embeds=[embed]
        )

    def _create_rule_evaluation_message(self, symbol: str, signals: List[Dict], analysis_time: datetime) -> DiscordMessage:
        """ルール評価結果メッセージの作成"""
        # 埋め込みフィールドの作成
        fields = []
        
        for i, signal in enumerate(signals[:5]):  # 最大5個のシグナルを表示
            signal_text = (
                f"**{signal['strategy']}** | {signal['direction']}\n"
                f"確率: `{signal['confidence']*100:.1f}%` | "
                f"時間足: `{signal['timeframe']}`\n"
                f"エントリー: `{signal['entry_price']}` | "
                f"SL: `{signal['stop_loss']}` | "
                f"TP: `{signal['take_profit']}`"
            )
            
            fields.append({
                "name": f"📊 シグナル {i+1}",
                "value": signal_text,
                "inline": False
            })
        
        if len(signals) > 5:
            fields.append({
                "name": "📈 その他",
                "value": f"他に {len(signals) - 5} 個のシグナルがあります",
                "inline": False
            })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="🔍 ルール評価結果",
            description=f"**{symbol}** | {analysis_time.strftime('%H:%M:%S')} JST",
            color=self.message_settings["embed_color_scenario"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=analysis_time.isoformat()
        )
        
        return DiscordMessage(
            content=f"ルール評価完了！{len(signals)}個のエントリーシグナルを検出しました。",
            embeds=[embed]
        )

    def _create_entry_signal_message(self, trade: Trade, scenario: Scenario, entry_snapshot: MarketSnapshot) -> DiscordMessage:
        """エントリーシグナルメッセージの作成"""
        # 埋め込みフィールドの作成
        fields = [
            {
                "name": "🎯 エントリー",
                "value": f"`{trade.direction.value}` @ `{trade.entry_price}`",
                "inline": True
            },
            {
                "name": "🛑 SL",
                "value": f"`{trade.stop_loss}` ({self._calculate_pips(trade.entry_price, trade.stop_loss, trade.direction)} pips)",
                "inline": True
            },
            {
                "name": "💰 TP1",
                "value": f"`{trade.take_profit_1}` ({self._calculate_pips(trade.entry_price, trade.take_profit_1, trade.direction)} pips)",
                "inline": True
            },
            {
                "name": "💰 TP2",
                "value": f"`{trade.take_profit_2}` ({self._calculate_pips(trade.entry_price, trade.take_profit_2, trade.direction)} pips)",
                "inline": True
            },
            {
                "name": "💰 TP3",
                "value": f"`{trade.take_profit_3}` ({self._calculate_pips(trade.entry_price, trade.take_profit_3, trade.direction)} pips)",
                "inline": True
            },
            {
                "name": "📊 確率",
                "value": f"`{scenario.entry_conditions.get('confidence', 0)*100:.1f}%`",
                "inline": True
            },
            {
                "name": "⏱️ 最大保有",
                "value": f"`{scenario.entry_conditions.get('max_hold_time', 240)}分`",
                "inline": True
            },
            {
                "name": "🎯 シナリオID",
                "value": f"`{scenario.id}`",
                "inline": True
            },
            {
                "name": "📈 RR",
                "value": f"`{scenario.entry_conditions.get('risk_reward_ratio', 0):.2f}`",
                "inline": True
            }
        ]
        
        # テクニカル状況の追加
        if self.message_settings["include_technical_details"]:
            technical_indicators = entry_snapshot.technical_indicators
            if technical_indicators:
                tech_text = ""
                for timeframe, indicators in technical_indicators.items():
                    tech_text += f"**{timeframe}**: "
                    tech_items = []
                    if indicators.get("rsi_14"):
                        tech_items.append(f"RSI: {indicators['rsi_14']:.1f}")
                    if indicators.get("ema_21"):
                        tech_items.append(f"EMA21: {indicators['ema_21']:.3f}")
                    if indicators.get("macd"):
                        tech_items.append(f"MACD: {indicators['macd']:.5f}")
                    tech_text += ", ".join(tech_items) + "\n"
                
                if tech_text:
                    fields.append({
                        "name": "🔍 テクニカル状況",
                        "value": tech_text[:1024],
                        "inline": False
                    })
        
        # リスク指標の追加
        if self.message_settings["include_risk_metrics"]:
            risk_metrics = entry_snapshot.risk_metrics
            if risk_metrics:
                risk_text = f"**日次トレード数**: {risk_metrics.get('daily_trades', 0)}/5\n"
                risk_text += f"**日次リスク**: {risk_metrics.get('daily_risk_percent', 0):.1f}%/3.0%\n"
                risk_text += f"**相関リスク**: {risk_metrics.get('correlation_risk', 0):.1f}"
                
                fields.append({
                    "name": "⚠️ リスク指標",
                    "value": risk_text,
                    "inline": False
                })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="🟢 ENTRY SIGNAL 🟢",
            description=f"**USD/JPY** | {scenario.strategy}",
            color=self.message_settings["embed_color_entry"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return DiscordMessage(
            content="🚨 **エントリーシグナル発生！** 🚨",
            embeds=[embed]
        )

    def _create_exit_signal_message(self, trade: Trade, exit_snapshot: MarketSnapshot) -> DiscordMessage:
        """エグジットシグナルメッセージの作成"""
        # 損益の計算
        profit_loss_pips = trade.profit_loss_pips or 0
        profit_loss_percent = trade.profit_loss or 0
        
        # 埋め込みフィールドの作成
        fields = [
            {
                "name": "💰 エグジット",
                "value": f"`{trade.exit_price}`",
                "inline": True
            },
            {
                "name": "📈 P&L",
                "value": f"`{profit_loss_pips:+.1f} pips` ({profit_loss_percent:+.2f}%)",
                "inline": True
            },
            {
                "name": "⏱️ 保有時間",
                "value": f"`{trade.hold_time_minutes}分`",
                "inline": True
            },
            {
                "name": "🎯 エグジット理由",
                "value": f"`{trade.exit_reason.value if trade.exit_reason else 'N/A'}`",
                "inline": True
            },
            {
                "name": "📊 遵守スコア",
                "value": f"`{trade.adherence_score or 0}/100`",
                "inline": True
            },
            {
                "name": "🏷️ 違反タグ",
                "value": f"`{', '.join(trade.violation_tags) if trade.violation_tags else 'なし'}`",
                "inline": True
            }
        ]
        
        # テクニカル状況の追加
        if self.message_settings["include_technical_details"]:
            technical_indicators = exit_snapshot.technical_indicators
            if technical_indicators:
                tech_text = ""
                for timeframe, indicators in technical_indicators.items():
                    tech_text += f"**{timeframe}**: "
                    tech_items = []
                    if indicators.get("rsi_14"):
                        tech_items.append(f"RSI: {indicators['rsi_14']:.1f}")
                    if indicators.get("ema_21"):
                        tech_items.append(f"EMA21: {indicators['ema_21']:.3f}")
                    tech_text += ", ".join(tech_items) + "\n"
                
                if tech_text:
                    fields.append({
                        "name": "🔍 エグジット時テクニカル",
                        "value": tech_text[:1024],
                        "inline": False
                    })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="🔴 EXIT SIGNAL 🔴",
            description=f"**USD/JPY** | {trade.id}",
            color=self.message_settings["embed_color_exit"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # 損益に応じたメッセージ
        if profit_loss_pips > 0:
            content = f"🎉 **利益確定！** +{profit_loss_pips:.1f}ピップス 🎉"
        elif profit_loss_pips < 0:
            content = f"😞 **損失確定** {profit_loss_pips:.1f}ピップス 😞"
        else:
            content = "🤝 **ブレイクイーブン** 0.0ピップス 🤝"
        
        return DiscordMessage(
            content=content,
            embeds=[embed]
        )

    def _create_daily_report_message(self, daily_performance: DailyPerformance) -> DiscordMessage:
        """日次レポートメッセージの作成"""
        # 埋め込みフィールドの作成
        fields = [
            {
                "name": "📊 総トレード数",
                "value": f"`{daily_performance.total_trades}`",
                "inline": True
            },
            {
                "name": "🎯 勝率",
                "value": f"`{daily_performance.win_rate:.1%}`",
                "inline": True
            },
            {
                "name": "💰 総利益",
                "value": f"`{daily_performance.total_profit_pips:+.1f} pips`",
                "inline": True
            },
            {
                "name": "📈 プロフィットファクター",
                "value": f"`{daily_performance.profit_factor:.2f}`",
                "inline": True
            },
            {
                "name": "📉 最大ドローダウン",
                "value": f"`{daily_performance.max_drawdown:.1f} pips`",
                "inline": True
            },
            {
                "name": "⏱️ 平均保有時間",
                "value": f"`{daily_performance.average_hold_time_minutes:.1f}分`",
                "inline": True
            },
            {
                "name": "📊 平均遵守スコア",
                "value": f"`{daily_performance.adherence_score_avg:.1f}/100`",
                "inline": True
            },
            {
                "name": "📈 日次リターン",
                "value": f"`{daily_performance.daily_return_percent:+.2f}%`",
                "inline": True
            }
        ]
        
        # 戦略別パフォーマンスの追加
        if daily_performance.strategy_performance:
            strategy_text = ""
            for strategy, performance in daily_performance.strategy_performance.items():
                strategy_text += f"**{strategy}**: {performance['trades']}トレード, 勝率{performance['win_rate']:.1%}\n"
            
            if strategy_text:
                fields.append({
                    "name": "📋 戦略別パフォーマンス",
                    "value": strategy_text[:1024],
                    "inline": False
                })
        
        # 違反分析の追加
        if daily_performance.violation_summary:
            violation_text = ""
            for violation, count in daily_performance.violation_summary.items():
                violation_text += f"**{violation}**: {count}件\n"
            
            if violation_text:
                fields.append({
                    "name": "⚠️ 違反分析",
                    "value": violation_text[:1024],
                    "inline": False
                })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="📊 日次レポート",
            description=f"**{daily_performance.date.strftime('%Y年%m月%d日')}** のパフォーマンス",
            color=self.message_settings["embed_color_report"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return DiscordMessage(
            content="📈 **日次パフォーマンスレポート** 📈",
            embeds=[embed]
        )

    def _create_weekly_report_message(self, weekly_report: WeeklyReport) -> DiscordMessage:
        """週次レポートメッセージの作成"""
        # 埋め込みフィールドの作成
        fields = [
            {
                "name": "📅 期間",
                "value": f"`{weekly_report.week_start.strftime('%m/%d')} - {weekly_report.week_end.strftime('%m/%d')}`",
                "inline": True
            },
            {
                "name": "📊 総トレード数",
                "value": f"`{weekly_report.total_trades}`",
                "inline": True
            },
            {
                "name": "🎯 週間勝率",
                "value": f"`{weekly_report.overall_performance.win_rate:.1%}`",
                "inline": True
            },
            {
                "name": "💰 週間総利益",
                "value": f"`{weekly_report.overall_performance.total_profit_pips:+.1f} pips`",
                "inline": True
            },
            {
                "name": "📈 週間プロフィットファクター",
                "value": f"`{weekly_report.overall_performance.profit_factor:.2f}`",
                "inline": True
            },
            {
                "name": "📊 平均遵守スコア",
                "value": f"`{weekly_report.overall_performance.adherence_score_avg:.1f}/100`",
                "inline": True
            }
        ]
        
        # 改善提案の追加
        if weekly_report.improvement_suggestions:
            suggestions_text = ""
            for suggestion in weekly_report.improvement_suggestions[:3]:  # 最初の3件のみ
                suggestions_text += f"**{suggestion.title}**: {suggestion.description[:100]}...\n"
            
            if suggestions_text:
                fields.append({
                    "name": "💡 改善提案",
                    "value": suggestions_text[:1024],
                    "inline": False
                })
        
        # ルールパフォーマンス分析の追加
        if weekly_report.rule_performance_analysis.get("most_effective_strategy"):
            most_effective = weekly_report.rule_performance_analysis["most_effective_strategy"]
            least_effective = weekly_report.rule_performance_analysis.get("least_effective_strategy")
            
            rule_text = f"**最も効果的**: {most_effective['name']} (効果性: {most_effective['effectiveness']:.2f})\n"
            if least_effective:
                rule_text += f"**改善が必要**: {least_effective['name']} (効果性: {least_effective['effectiveness']:.2f})"
            
            fields.append({
                "name": "📋 ルールパフォーマンス分析",
                "value": rule_text,
                "inline": False
            })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="📊 週次レポート",
            description=f"**{weekly_report.week_start.strftime('%Y年%m月%d日')} - {weekly_report.week_end.strftime('%Y年%m月%d日')}** のパフォーマンス",
            color=self.message_settings["embed_color_report"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return DiscordMessage(
            content="📈 **週次パフォーマンスレポート** 📈",
            embeds=[embed]
        )

    def _create_error_alert_message(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> DiscordMessage:
        """エラーアラートメッセージの作成"""
        # 埋め込みフィールドの作成
        fields = [
            {
                "name": "🚨 エラーメッセージ",
                "value": f"```{error_message[:1000]}```",
                "inline": False
            }
        ]
        
        # エラー詳細の追加
        if error_details:
            details_text = ""
            for key, value in error_details.items():
                details_text += f"**{key}**: {value}\n"
            
            if details_text:
                fields.append({
                    "name": "📋 エラー詳細",
                    "value": details_text[:1024],
                    "inline": False
                })
        
        # 埋め込みメッセージの作成
        embed = DiscordEmbed(
            title="🚨 ERROR ALERT 🚨",
            description="システムエラーが発生しました",
            color=self.message_settings["embed_color_error"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        return DiscordMessage(
            content="🚨 **システムエラー発生！** 🚨",
            embeds=[embed]
        )

    def _calculate_pips(self, entry_price: float, target_price: float, direction: TradeDirection) -> float:
        """ピップス計算"""
        if direction == TradeDirection.BUY:
            return (target_price - entry_price) * 10000
        else:  # SELL
            return (entry_price - target_price) * 10000

    async def _send_message(self, message: DiscordMessage) -> bool:
        """Discordメッセージの送信"""
        if not self.webhook_url:
            self.logger.warning("Discord webhook URLが設定されていません")
            return False
        
        try:
            # メッセージデータの構築
            data = {}
            
            if message.content:
                data["content"] = message.content
            
            if message.embeds:
                data["embeds"] = [asdict(embed) for embed in message.embeds]
            
            if message.username:
                data["username"] = message.username
            
            if message.avatar_url:
                data["avatar_url"] = message.avatar_url
            
            # HTTPリクエストの送信
            async with self.session.post(
                self.webhook_url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 204:
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Discord送信エラー: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Discord送信エラー: {e}")
            return False

    async def close(self):
        """リソースのクリーンアップ"""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("DiscordNotifier closed")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from ..core.scenario_manager import ScenarioManager, TradeDirection
    from ..core.rule_engine import EntrySignal, RuleResult
    from ..core.snapshot_manager import SnapshotManager
    
    notifier = DiscordNotifier()
    scenario_manager = ScenarioManager()
    snapshot_manager = SnapshotManager()
    
    try:
        print("🧪 Discord配信システムテスト...")
        
        # ダミーのエントリーシグナルとシナリオを作成
        dummy_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="pullback_buy",
            confidence=0.85,
            entry_price=147.123,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=2.5,
            max_hold_time=240,
            rule_results=[
                RuleResult("RSI_14 <= 40", True, 0.9, "RSI: 38.5 ≤ 40", {}),
                RuleResult("price > EMA_200", True, 0.8, "Price: 147.123 > EMA_200: 146.800", {})
            ],
            technical_summary={"1h": {"price": 147.123, "rsi_14": 38.5}},
            created_at=datetime.now(timezone.utc)
        )
        
        # シナリオとトレードの作成
        scenario = await scenario_manager.create_scenario(dummy_signal)
        await scenario_manager.arm_scenario(scenario.id)
        await scenario_manager.trigger_scenario(scenario.id, 147.125)
        trade = await scenario_manager.enter_scenario(scenario.id, 147.125)
        
        # エントリースナップの保存
        entry_snapshot_id = await snapshot_manager.save_entry_snapshot(scenario, trade)
        entry_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
        entry_snapshot = entry_snapshots[0] if entry_snapshots else None
        
        # シナリオ作成通知の送信
        if entry_snapshot:
            success = await notifier.send_scenario_created(scenario)
            print(f"✅ シナリオ作成通知: {'成功' if success else '失敗'}")
            
            # エントリーシグナル通知の送信
            success = await notifier.send_entry_signal(trade, scenario, entry_snapshot)
            print(f"✅ エントリーシグナル通知: {'成功' if success else '失敗'}")
        
        # エラーアラート通知の送信
        success = await notifier.send_error_alert("テストエラーメッセージ", {"test": "value"})
        print(f"✅ エラーアラート通知: {'成功' if success else '失敗'}")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notifier.close()
        await scenario_manager.close()
        await snapshot_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
