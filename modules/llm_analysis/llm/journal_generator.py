"""
日誌生成システム

トレード履歴の自然言語での記録・要約を生成する。
ルールベース売買システムの補助機能として、日次・週次・月次の
トレード日誌を自動生成する。
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import json


class JournalGenerator:
    """トレード日誌の生成"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ 日誌生成システム初期化完了")
    
    def generate_daily_journal(self, trades: List[Dict], date: Optional[datetime] = None) -> str:
        """
        日次トレード日誌の生成
        
        Args:
            trades: トレードデータのリスト
            date: 対象日（Noneの場合は今日）
            
        Returns:
            日次トレード日誌の自然言語テキスト
        """
        try:
            if date is None:
                date = datetime.now(timezone.utc)
            
            # トレード統計の計算
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.get('profit', 0) > 0]
            losing_trades = [t for t in trades if t.get('profit', 0) <= 0]
            
            win_count = len(winning_trades)
            loss_count = len(losing_trades)
            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
            
            total_profit = sum(t.get('profit', 0) for t in trades)
            total_pips = sum(t.get('pips', 0) for t in trades)
            
            # 最大利益・最大損失
            max_profit = max((t.get('profit', 0) for t in trades), default=0)
            max_loss = min((t.get('profit', 0) for t in trades), default=0)
            
            # 平均保有時間
            hold_times = [t.get('hold_time_minutes', 0) for t in trades if t.get('hold_time_minutes')]
            avg_hold_time = sum(hold_times) / len(hold_times) if hold_times else 0
            
            # パフォーマンス評価
            if win_rate >= 70:
                performance_eval = "優秀"
            elif win_rate >= 60:
                performance_eval = "良好"
            elif win_rate >= 50:
                performance_eval = "普通"
            else:
                performance_eval = "改善必要"
            
            # 日誌の生成
            journal = f"""
【{date.strftime('%Y年%m月%d日')} トレード日誌】

📊 基本統計:
総トレード数: {total_trades}件
成功トレード: {win_count}件
失敗トレード: {loss_count}件
勝率: {win_rate:.1f}%（{performance_eval}）

💰 損益:
総利益: {total_profit:.2f}円
総pips: {total_pips:.1f}pips
最大利益: {max_profit:.2f}円
最大損失: {max_loss:.2f}円

⏰ 時間分析:
平均保有時間: {avg_hold_time:.0f}分

📈 主要なトレード:
{self._format_trade_summaries(trades[:5])}

💡 今日の学び:
{self._generate_insights(trades)}
"""
            
            return journal.strip()
            
        except Exception as e:
            self.logger.error(f"❌ 日次日誌生成エラー: {e}")
            return f"日次日誌の生成中にエラーが発生しました: {e}"
    
    def generate_rule_performance_journal(self, rule_performance: Dict) -> str:
        """
        ルールパフォーマンス日誌の生成
        
        Args:
            rule_performance: ルールパフォーマンスデータ
            
        Returns:
            ルールパフォーマンス日誌の自然言語テキスト
        """
        try:
            journal = f"""
【ルールパフォーマンス分析】

📋 ルール別パフォーマンス:
"""
            
            for rule_name, performance in rule_performance.items():
                win_rate = performance.get('win_rate', 0)
                total_trades = performance.get('total_trades', 0)
                total_profit = performance.get('total_profit', 0)
                avg_hold_time = performance.get('avg_hold_time', 0)
                
                # ルール名の日本語化
                rule_jp = {
                    'pullback_buy': '押し目買いルール',
                    'breakout_buy': 'ブレイクアウト買いルール',
                    'reversal_sell': '逆張り売りルール'
                }.get(rule_name, rule_name)
                
                # パフォーマンス評価
                if win_rate >= 70:
                    eval_text = "優秀"
                elif win_rate >= 60:
                    eval_text = "良好"
                elif win_rate >= 50:
                    eval_text = "普通"
                else:
                    eval_text = "改善必要"
                
                journal += f"""
{rule_jp}:
  勝率: {win_rate:.1f}%（{eval_text}）
  総トレード数: {total_trades}件
  総利益: {total_profit:.2f}円
  平均保有時間: {avg_hold_time:.0f}分
"""
            
            journal += f"""

🔍 改善点:
{self._generate_improvement_suggestions(rule_performance)}
"""
            
            return journal.strip()
            
        except Exception as e:
            self.logger.error(f"❌ ルールパフォーマンス日誌生成エラー: {e}")
            return f"ルールパフォーマンス日誌の生成中にエラーが発生しました: {e}"
    
    def generate_weekly_report(self, weekly_data: Dict) -> str:
        """
        週次レポートの生成
        
        Args:
            weekly_data: 週次データ
            
        Returns:
            週次レポートの自然言語テキスト
        """
        try:
            start_date = weekly_data.get('start_date', datetime.now(timezone.utc))
            end_date = weekly_data.get('end_date', datetime.now(timezone.utc))
            total_trades = weekly_data.get('total_trades', 0)
            win_rate = weekly_data.get('win_rate', 0)
            total_profit = weekly_data.get('total_profit', 0)
            max_drawdown = weekly_data.get('max_drawdown', 0)
            adherence_score = weekly_data.get('adherence_score', 0)
            
            # 週次評価
            if win_rate >= 70 and adherence_score >= 90:
                week_eval = "優秀な週"
            elif win_rate >= 60 and adherence_score >= 80:
                week_eval = "良好な週"
            elif win_rate >= 50 and adherence_score >= 70:
                week_eval = "普通の週"
            else:
                week_eval = "改善が必要な週"
            
            report = f"""
【週次トレードレポート】
期間: {start_date.strftime('%Y年%m月%d日')} ～ {end_date.strftime('%Y年%m月%d日')}

📊 週次サマリー:
総トレード数: {total_trades}件
勝率: {win_rate:.1f}%
総利益: {total_profit:.2f}円
最大ドローダウン: {max_drawdown:.2f}%
ルール遵守スコア: {adherence_score:.1f}/100

📈 週次評価: {week_eval}

💡 来週への改善提案:
{self._generate_weekly_insights(weekly_data)}
"""
            
            return report.strip()
            
        except Exception as e:
            self.logger.error(f"❌ 週次レポート生成エラー: {e}")
            return f"週次レポートの生成中にエラーが発生しました: {e}"
    
    def generate_monthly_report(self, monthly_data: Dict) -> str:
        """
        月次レポートの生成
        
        Args:
            monthly_data: 月次データ
            
        Returns:
            月次レポートの自然言語テキスト
        """
        try:
            month = monthly_data.get('month', datetime.now(timezone.utc).strftime('%Y年%m月'))
            total_trades = monthly_data.get('total_trades', 0)
            win_rate = monthly_data.get('win_rate', 0)
            total_profit = monthly_data.get('total_profit', 0)
            sharpe_ratio = monthly_data.get('sharpe_ratio', 0)
            max_drawdown = monthly_data.get('max_drawdown', 0)
            adherence_score = monthly_data.get('adherence_score', 0)
            
            # 月次評価
            if win_rate >= 70 and sharpe_ratio >= 2.0:
                month_eval = "優秀な月"
            elif win_rate >= 60 and sharpe_ratio >= 1.5:
                month_eval = "良好な月"
            elif win_rate >= 50 and sharpe_ratio >= 1.0:
                month_eval = "普通の月"
            else:
                month_eval = "改善が必要な月"
            
            report = f"""
【月次トレードレポート】
対象月: {month}

📊 月次サマリー:
総トレード数: {total_trades}件
勝率: {win_rate:.1f}%
総利益: {total_profit:.2f}円
シャープレシオ: {sharpe_ratio:.2f}
最大ドローダウン: {max_drawdown:.2f}%
ルール遵守スコア: {adherence_score:.1f}/100

📈 月次評価: {month_eval}

🎯 来月への戦略:
{self._generate_monthly_insights(monthly_data)}
"""
            
            return report.strip()
            
        except Exception as e:
            self.logger.error(f"❌ 月次レポート生成エラー: {e}")
            return f"月次レポートの生成中にエラーが発生しました: {e}"
    
    def _format_trade_summaries(self, trades: List[Dict]) -> str:
        """トレードサマリーのフォーマット"""
        if not trades:
            return "トレードなし"
        
        summaries = []
        for i, trade in enumerate(trades[:5], 1):
            direction = trade.get('direction', 'UNKNOWN')
            direction_jp = "買い" if direction.upper() == "BUY" else "売り" if direction.upper() == "SELL" else "不明"
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            profit = trade.get('profit', 0)
            hold_time = trade.get('hold_time_minutes', 0)
            
            summaries.append(f"{i}. {direction_jp} @ {entry_price:.5f} → {exit_price:.5f} ({profit:+.2f}円, {hold_time}分)")
        
        return "\n".join(summaries)
    
    def _generate_insights(self, trades: List[Dict]) -> str:
        """トレードからの洞察生成"""
        if not trades:
            return "トレードデータが不足しています。"
        
        insights = []
        
        # 勝率分析
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        win_rate = len(winning_trades) / len(trades) * 100
        
        if win_rate >= 70:
            insights.append("勝率が高く、ルールが適切に機能しています。")
        elif win_rate < 50:
            insights.append("勝率が低いため、エントリー条件の見直しが必要です。")
        
        # 保有時間分析
        hold_times = [t.get('hold_time_minutes', 0) for t in trades if t.get('hold_time_minutes')]
        if hold_times:
            avg_hold = sum(hold_times) / len(hold_times)
            if avg_hold > 180:
                insights.append("平均保有時間が長いため、エグジット条件の最適化を検討してください。")
            elif avg_hold < 30:
                insights.append("平均保有時間が短いため、エントリー条件の精度向上を検討してください。")
        
        # 利益分析
        profits = [t.get('profit', 0) for t in trades]
        if profits:
            max_profit = max(profits)
            max_loss = min(profits)
            if abs(max_loss) > max_profit * 2:
                insights.append("最大損失が最大利益の2倍を超えています。リスク管理の強化が必要です。")
        
        return "\n".join(insights) if insights else "特に問題は見つかりませんでした。"
    
    def _generate_improvement_suggestions(self, rule_performance: Dict) -> str:
        """改善提案の生成"""
        suggestions = []
        
        for rule_name, performance in rule_performance.items():
            win_rate = performance.get('win_rate', 0)
            total_trades = performance.get('total_trades', 0)
            
            if total_trades < 5:
                suggestions.append(f"{rule_name}のトレード数が少ないため、より多くのデータ収集が必要です。")
            elif win_rate < 60:
                suggestions.append(f"{rule_name}の勝率が低いため、パラメータの調整を検討してください。")
        
        return "\n".join(suggestions) if suggestions else "現在のルールは適切に機能しています。"
    
    def _generate_weekly_insights(self, weekly_data: Dict) -> str:
        """週次洞察の生成"""
        insights = []
        
        win_rate = weekly_data.get('win_rate', 0)
        adherence_score = weekly_data.get('adherence_score', 0)
        
        if win_rate < 50:
            insights.append("勝率向上のため、エントリー条件の厳格化を検討してください。")
        
        if adherence_score < 80:
            insights.append("ルール遵守率向上のため、トレード前の条件確認を徹底してください。")
        
        return "\n".join(insights) if insights else "来週も現在の戦略を継続してください。"
    
    def _generate_monthly_insights(self, monthly_data: Dict) -> str:
        """月次洞察の生成"""
        insights = []
        
        sharpe_ratio = monthly_data.get('sharpe_ratio', 0)
        max_drawdown = monthly_data.get('max_drawdown', 0)
        
        if sharpe_ratio < 1.0:
            insights.append("シャープレシオ向上のため、リスクリワード比の改善を検討してください。")
        
        if max_drawdown > 0.1:
            insights.append("最大ドローダウンが大きいため、ポジションサイズの調整を検討してください。")
        
        return "\n".join(insights) if insights else "来月も現在の戦略を継続し、さらなる改善を目指してください。"
    
    def close(self):
        """リソースのクリーンアップ"""
        self.logger.info("日誌生成システム終了")
