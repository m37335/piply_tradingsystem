"""
メッセージフォーマッター

Discord通知用のメッセージフォーマットを管理するシステム。
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..core.scenario_manager import Scenario, Trade, ExitReason, TradeDirection
from ..core.snapshot_manager import TradeSnapshot, MarketSnapshot
from ..evaluation.daily_evaluator import DailyPerformance, WeeklyReport


class MessageTemplate(Enum):
    """メッセージテンプレート"""
    SCENARIO_CREATED = "scenario_created"
    ENTRY_SIGNAL = "entry_signal"
    EXIT_SIGNAL = "exit_signal"
    DAILY_REPORT = "daily_report"
    WEEKLY_REPORT = "weekly_report"
    ERROR_ALERT = "error_alert"


@dataclass
class MessageFormat:
    """メッセージフォーマット"""
    template: MessageTemplate
    title: str
    description: str
    color: int
    fields: List[Dict[str, Any]]
    footer: Optional[Dict[str, str]] = None
    timestamp: Optional[str] = None


class MessageFormatter:
    """メッセージフォーマッター"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # テンプレート設定
        self.templates = {
            MessageTemplate.SCENARIO_CREATED: {
                "title": "🟡 SCENARIO CREATED 🟡",
                "description": "**USD/JPY** | {strategy}",
                "color": 0xffff00,
                "icon": "🟡"
            },
            MessageTemplate.ENTRY_SIGNAL: {
                "title": "🟢 ENTRY SIGNAL 🟢",
                "description": "**USD/JPY** | {strategy}",
                "color": 0x00ff00,
                "icon": "🟢"
            },
            MessageTemplate.EXIT_SIGNAL: {
                "title": "🔴 EXIT SIGNAL 🔴",
                "description": "**USD/JPY** | {trade_id}",
                "color": 0xff0000,
                "icon": "🔴"
            },
            MessageTemplate.DAILY_REPORT: {
                "title": "📊 日次レポート",
                "description": "**{date}** のパフォーマンス",
                "color": 0x0099ff,
                "icon": "📊"
            },
            MessageTemplate.WEEKLY_REPORT: {
                "title": "📊 週次レポート",
                "description": "**{week_start} - {week_end}** のパフォーマンス",
                "color": 0x0099ff,
                "icon": "📊"
            },
            MessageTemplate.ERROR_ALERT: {
                "title": "🚨 ERROR ALERT 🚨",
                "description": "システムエラーが発生しました",
                "color": 0xff4500,
                "icon": "🚨"
            }
        }

    def format_scenario_created(self, scenario: Scenario) -> MessageFormat:
        """シナリオ作成メッセージのフォーマット"""
        template = self.templates[MessageTemplate.SCENARIO_CREATED]
        
        # フィールドの作成
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
        
        return MessageFormat(
            template=MessageTemplate.SCENARIO_CREATED,
            title=template["title"],
            description=template["description"].format(strategy=scenario.strategy),
            color=template["color"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def format_entry_signal(self, trade: Trade, scenario: Scenario, entry_snapshot: MarketSnapshot) -> MessageFormat:
        """エントリーシグナルメッセージのフォーマット"""
        template = self.templates[MessageTemplate.ENTRY_SIGNAL]
        
        # フィールドの作成
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
        
        return MessageFormat(
            template=MessageTemplate.ENTRY_SIGNAL,
            title=template["title"],
            description=template["description"].format(strategy=scenario.strategy),
            color=template["color"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def format_exit_signal(self, trade: Trade, exit_snapshot: MarketSnapshot) -> MessageFormat:
        """エグジットシグナルメッセージのフォーマット"""
        template = self.templates[MessageTemplate.EXIT_SIGNAL]
        
        # 損益の計算
        profit_loss_pips = trade.profit_loss_pips or 0
        profit_loss_percent = trade.profit_loss or 0
        
        # フィールドの作成
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
        
        return MessageFormat(
            template=MessageTemplate.EXIT_SIGNAL,
            title=template["title"],
            description=template["description"].format(trade_id=trade.id),
            color=template["color"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def format_daily_report(self, daily_performance: DailyPerformance) -> MessageFormat:
        """日次レポートメッセージのフォーマット"""
        template = self.templates[MessageTemplate.DAILY_REPORT]
        
        # フィールドの作成
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
        
        return MessageFormat(
            template=MessageTemplate.DAILY_REPORT,
            title=template["title"],
            description=template["description"].format(date=daily_performance.date.strftime('%Y年%m月%d日')),
            color=template["color"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def format_weekly_report(self, weekly_report: WeeklyReport) -> MessageFormat:
        """週次レポートメッセージのフォーマット"""
        template = self.templates[MessageTemplate.WEEKLY_REPORT]
        
        # フィールドの作成
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
        
        return MessageFormat(
            template=MessageTemplate.WEEKLY_REPORT,
            title=template["title"],
            description=template["description"].format(
                week_start=weekly_report.week_start.strftime('%Y年%m月%d日'),
                week_end=weekly_report.week_end.strftime('%Y年%m月%d日')
            ),
            color=template["color"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def format_error_alert(self, error_message: str, error_details: Optional[Dict[str, Any]] = None) -> MessageFormat:
        """エラーアラートメッセージのフォーマット"""
        template = self.templates[MessageTemplate.ERROR_ALERT]
        
        # フィールドの作成
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
        
        return MessageFormat(
            template=MessageTemplate.ERROR_ALERT,
            title=template["title"],
            description=template["description"],
            color=template["color"],
            fields=fields,
            footer={
                "text": "ルールベース売買システム",
                "icon_url": "https://cdn.discordapp.com/emojis/1234567890123456789.png"
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _calculate_pips(self, entry_price: float, target_price: float, direction: TradeDirection) -> float:
        """ピップス計算"""
        if direction == TradeDirection.BUY:
            return (target_price - entry_price) * 10000
        else:  # SELL
            return (entry_price - target_price) * 10000

    def get_template(self, template_type: MessageTemplate) -> Dict[str, Any]:
        """テンプレートの取得"""
        return self.templates.get(template_type, {})

    def update_template(self, template_type: MessageTemplate, template_data: Dict[str, Any]) -> None:
        """テンプレートの更新"""
        self.templates[template_type] = template_data
        self.logger.info(f"テンプレート更新: {template_type.value}")

    def list_templates(self) -> List[MessageTemplate]:
        """テンプレート一覧の取得"""
        return list(self.templates.keys())


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from ..core.scenario_manager import ScenarioManager, TradeDirection
    from ..core.rule_engine import EntrySignal, RuleResult
    from ..core.snapshot_manager import SnapshotManager
    
    formatter = MessageFormatter()
    scenario_manager = ScenarioManager()
    snapshot_manager = SnapshotManager()
    
    try:
        print("🧪 メッセージフォーマッターテスト...")
        
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
        
        # メッセージフォーマットのテスト
        if entry_snapshot:
            # シナリオ作成メッセージ
            scenario_format = formatter.format_scenario_created(scenario)
            print(f"✅ シナリオ作成メッセージフォーマット: {scenario_format.title}")
            
            # エントリーシグナルメッセージ
            entry_format = formatter.format_entry_signal(trade, scenario, entry_snapshot)
            print(f"✅ エントリーシグナルメッセージフォーマット: {entry_format.title}")
            
            # エラーアラートメッセージ
            error_format = formatter.format_error_alert("テストエラーメッセージ", {"test": "value"})
            print(f"✅ エラーアラートメッセージフォーマット: {error_format.title}")
        
        # テンプレート一覧の表示
        templates = formatter.list_templates()
        print(f"✅ 利用可能テンプレート: {[t.value for t in templates]}")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scenario_manager.close()
        await snapshot_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
