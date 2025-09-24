"""
改善提案システム

パフォーマンス分析結果に基づく改善案の提示を行う。
ルールベース売買システムの補助機能として、データドリブンな
改善提案を生成する。
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import statistics


class ImprovementAdvisor:
    """改善提案の生成"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ 改善提案システム初期化完了")
    
    def suggest_rule_improvements(self, performance_data: Dict) -> List[str]:
        """
        ルール改善提案の生成
        
        Args:
            performance_data: パフォーマンスデータ
            
        Returns:
            改善提案のリスト
        """
        try:
            suggestions = []
            
            # ルール別パフォーマンス分析
            for rule_name, rule_data in performance_data.get('rules', {}).items():
                win_rate = rule_data.get('win_rate', 0)
                total_trades = rule_data.get('total_trades', 0)
                avg_profit = rule_data.get('avg_profit', 0)
                false_positive_rate = rule_data.get('false_positive_rate', 0)
                
                # ルール名の日本語化
                rule_jp = {
                    'pullback_buy': '押し目買いルール',
                    'breakout_buy': 'ブレイクアウト買いルール',
                    'reversal_sell': '逆張り売りルール'
                }.get(rule_name, rule_name)
                
                # 勝率が低い場合の提案
                if win_rate < 0.6 and total_trades >= 10:
                    if rule_name == 'pullback_buy':
                        suggestions.append(f"{rule_jp}の勝率が{win_rate:.1%}と低いため、RSI閾値を40から35に下げることを検討してください")
                    elif rule_name == 'breakout_buy':
                        suggestions.append(f"{rule_jp}の勝率が{win_rate:.1%}と低いため、ボリューム条件を追加することを検討してください")
                    elif rule_name == 'reversal_sell':
                        suggestions.append(f"{rule_jp}の勝率が{win_rate:.1%}と低いため、RSI閾値を70から75に上げることを検討してください")
                
                # 偽陽性率が高い場合の提案
                if false_positive_rate > 0.25:
                    suggestions.append(f"{rule_jp}の偽陽性率が{false_positive_rate:.1%}と高いため、追加の確認条件を設けることを検討してください")
                
                # 平均利益が低い場合の提案
                if avg_profit < 0:
                    suggestions.append(f"{rule_jp}の平均利益がマイナスのため、エグジット条件の見直しを検討してください")
            
            # 全体的なパフォーマンス分析
            overall_win_rate = performance_data.get('overall_win_rate', 0)
            max_drawdown = performance_data.get('max_drawdown', 0)
            total_trades = performance_data.get('total_trades', 0)
            
            if overall_win_rate < 0.5:
                suggestions.append("全体的な勝率が50%を下回っているため、エントリー条件の厳格化を検討してください")
            
            if max_drawdown > 0.05:
                suggestions.append(f"最大ドローダウンが{max_drawdown:.1%}と大きいため、ストップロスをATR*1.0からATR*0.8に縮小することを検討してください")
            
            if total_trades < 20:
                suggestions.append("トレード数が少ないため、より多くのデータ収集期間を設けることを検討してください")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ ルール改善提案生成エラー: {e}")
            return [f"ルール改善提案の生成中にエラーが発生しました: {e}"]
    
    def suggest_parameter_adjustments(self, backtest_results: Dict) -> Dict:
        """
        パラメータ調整提案の生成
        
        Args:
            backtest_results: バックテスト結果
            
        Returns:
            パラメータ調整提案の辞書
        """
        try:
            suggestions = {}
            
            # RSI閾値の最適化提案
            rsi_analysis = self._analyze_rsi_performance(backtest_results)
            if rsi_analysis:
                suggestions['rsi_threshold'] = rsi_analysis
            
            # ATR倍率の最適化提案
            atr_analysis = self._analyze_atr_performance(backtest_results)
            if atr_analysis:
                suggestions['atr_multiplier'] = atr_analysis
            
            # EMA期間の最適化提案
            ema_analysis = self._analyze_ema_performance(backtest_results)
            if ema_analysis:
                suggestions['ema_periods'] = ema_analysis
            
            # 保有時間の最適化提案
            hold_time_analysis = self._analyze_hold_time_performance(backtest_results)
            if hold_time_analysis:
                suggestions['hold_time'] = hold_time_analysis
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ パラメータ調整提案生成エラー: {e}")
            return {"error": f"パラメータ調整提案の生成中にエラーが発生しました: {e}"}
    
    def suggest_risk_management_improvements(self, risk_metrics: Dict) -> List[str]:
        """
        リスク管理改善提案の生成
        
        Args:
            risk_metrics: リスク指標データ
            
        Returns:
            リスク管理改善提案のリスト
        """
        try:
            suggestions = []
            
            max_drawdown = risk_metrics.get('max_drawdown', 0)
            var_95 = risk_metrics.get('var_95', 0)
            sharpe_ratio = risk_metrics.get('sharpe_ratio', 0)
            max_consecutive_losses = risk_metrics.get('max_consecutive_losses', 0)
            avg_risk_per_trade = risk_metrics.get('avg_risk_per_trade', 0)
            
            # 最大ドローダウンの改善提案
            if max_drawdown > 0.1:
                suggestions.append(f"最大ドローダウンが{max_drawdown:.1%}と大きいため、ポジションサイズを現在の80%に縮小することを検討してください")
            
            # VaRの改善提案
            if var_95 > 0.05:
                suggestions.append(f"95%VaRが{var_95:.1%}と大きいため、相関リスクの管理を強化することを検討してください")
            
            # シャープレシオの改善提案
            if sharpe_ratio < 1.0:
                suggestions.append(f"シャープレシオが{sharpe_ratio:.2f}と低いため、リスクリワード比の改善を検討してください")
            
            # 連続損失の改善提案
            if max_consecutive_losses > 5:
                suggestions.append(f"最大連続損失が{max_consecutive_losses}回と多いため、エントリー条件の厳格化を検討してください")
            
            # トレード当たりリスクの改善提案
            if avg_risk_per_trade > 0.02:
                suggestions.append(f"トレード当たり平均リスクが{avg_risk_per_trade:.1%}と大きいため、リスク制限の厳格化を検討してください")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ リスク管理改善提案生成エラー: {e}")
            return [f"リスク管理改善提案の生成中にエラーが発生しました: {e}"]
    
    def suggest_timing_improvements(self, timing_analysis: Dict) -> List[str]:
        """
        タイミング改善提案の生成
        
        Args:
            timing_analysis: タイミング分析データ
            
        Returns:
            タイミング改善提案のリスト
        """
        try:
            suggestions = []
            
            session_performance = timing_analysis.get('session_performance', {})
            hour_performance = timing_analysis.get('hour_performance', {})
            
            # セッション別パフォーマンス分析
            for session, performance in session_performance.items():
                win_rate = performance.get('win_rate', 0)
                total_trades = performance.get('total_trades', 0)
                
                if total_trades >= 5:  # 十分なデータがある場合のみ
                    session_jp = {
                        'Tokyo': '東京セッション',
                        'London': 'ロンドンセッション',
                        'NewYork': 'ニューヨークセッション'
                    }.get(session, session)
                    
                    if win_rate < 0.5:
                        suggestions.append(f"{session_jp}の勝率が{win_rate:.1%}と低いため、この時間帯のトレードを避けることを検討してください")
                    elif win_rate > 0.7:
                        suggestions.append(f"{session_jp}の勝率が{win_rate:.1%}と高いため、この時間帯のトレード機会を増やすことを検討してください")
            
            # 時間帯別パフォーマンス分析
            best_hours = []
            worst_hours = []
            
            for hour, performance in hour_performance.items():
                win_rate = performance.get('win_rate', 0)
                total_trades = performance.get('total_trades', 0)
                
                if total_trades >= 3:  # 最低限のデータがある場合
                    if win_rate > 0.7:
                        best_hours.append(f"{hour}時台")
                    elif win_rate < 0.4:
                        worst_hours.append(f"{hour}時台")
            
            if best_hours:
                suggestions.append(f"勝率の高い時間帯（{', '.join(best_hours)}）でのトレード機会を増やすことを検討してください")
            
            if worst_hours:
                suggestions.append(f"勝率の低い時間帯（{', '.join(worst_hours)}）でのトレードを避けることを検討してください")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"❌ タイミング改善提案生成エラー: {e}")
            return [f"タイミング改善提案の生成中にエラーが発生しました: {e}"]
    
    def _analyze_rsi_performance(self, backtest_results: Dict) -> Optional[Dict]:
        """RSIパフォーマンス分析"""
        try:
            rsi_tests = backtest_results.get('rsi_tests', {})
            if not rsi_tests:
                return None
            
            best_threshold = None
            best_score = -1
            
            for threshold, results in rsi_tests.items():
                win_rate = results.get('win_rate', 0)
                sharpe_ratio = results.get('sharpe_ratio', 0)
                total_trades = results.get('total_trades', 0)
                
                if total_trades >= 10:  # 十分なデータがある場合のみ
                    # 複合スコアの計算（勝率とシャープレシオの重み付き平均）
                    score = win_rate * 0.6 + min(sharpe_ratio, 3.0) / 3.0 * 0.4
                    
                    if score > best_score:
                        best_score = score
                        best_threshold = threshold
            
            if best_threshold and best_threshold != 40:  # デフォルト値と異なる場合
                return {
                    "current": 40,
                    "suggested": best_threshold,
                    "reason": f"過去のデータ分析により、RSI閾値{best_threshold}でより高いパフォーマンスが期待される",
                    "confidence": min(best_score, 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ RSI分析エラー: {e}")
            return None
    
    def _analyze_atr_performance(self, backtest_results: Dict) -> Optional[Dict]:
        """ATRパフォーマンス分析"""
        try:
            atr_tests = backtest_results.get('atr_tests', {})
            if not atr_tests:
                return None
            
            best_multiplier = None
            best_score = -1
            
            for multiplier, results in atr_tests.items():
                win_rate = results.get('win_rate', 0)
                avg_profit = results.get('avg_profit', 0)
                max_drawdown = results.get('max_drawdown', 0)
                total_trades = results.get('total_trades', 0)
                
                if total_trades >= 10:  # 十分なデータがある場合のみ
                    # 複合スコアの計算
                    score = win_rate * 0.4 + min(avg_profit / 100, 1.0) * 0.3 + (1 - min(max_drawdown, 0.2) / 0.2) * 0.3
                    
                    if score > best_score:
                        best_score = score
                        best_multiplier = multiplier
            
            if best_multiplier and best_multiplier != 1.5:  # デフォルト値と異なる場合
                return {
                    "current": 1.5,
                    "suggested": best_multiplier,
                    "reason": f"リスクリワード比の改善により、ATR倍率{best_multiplier}でより良い結果が期待される",
                    "confidence": min(best_score, 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ ATR分析エラー: {e}")
            return None
    
    def _analyze_ema_performance(self, backtest_results: Dict) -> Optional[Dict]:
        """EMAパフォーマンス分析"""
        try:
            ema_tests = backtest_results.get('ema_tests', {})
            if not ema_tests:
                return None
            
            best_periods = None
            best_score = -1
            
            for periods, results in ema_tests.items():
                win_rate = results.get('win_rate', 0)
                sharpe_ratio = results.get('sharpe_ratio', 0)
                total_trades = results.get('total_trades', 0)
                
                if total_trades >= 10:  # 十分なデータがある場合のみ
                    # 複合スコアの計算
                    score = win_rate * 0.5 + min(sharpe_ratio, 3.0) / 3.0 * 0.5
                    
                    if score > best_score:
                        best_score = score
                        best_periods = periods
            
            if best_periods and best_periods != (21, 200):  # デフォルト値と異なる場合
                return {
                    "current": (21, 200),
                    "suggested": best_periods,
                    "reason": f"トレンド識別の精度向上により、EMA期間{best_periods}でより良い結果が期待される",
                    "confidence": min(best_score, 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ EMA分析エラー: {e}")
            return None
    
    def _analyze_hold_time_performance(self, backtest_results: Dict) -> Optional[Dict]:
        """保有時間パフォーマンス分析"""
        try:
            hold_time_tests = backtest_results.get('hold_time_tests', {})
            if not hold_time_tests:
                return None
            
            best_hold_time = None
            best_score = -1
            
            for hold_time, results in hold_time_tests.items():
                win_rate = results.get('win_rate', 0)
                avg_profit = results.get('avg_profit', 0)
                total_trades = results.get('total_trades', 0)
                
                if total_trades >= 10:  # 十分なデータがある場合のみ
                    # 複合スコアの計算
                    score = win_rate * 0.6 + min(avg_profit / 100, 1.0) * 0.4
                    
                    if score > best_score:
                        best_score = score
                        best_hold_time = hold_time
            
            if best_hold_time and best_hold_time != 120:  # デフォルト値と異なる場合
                return {
                    "current": 120,
                    "suggested": best_hold_time,
                    "reason": f"最適な保有時間の分析により、{best_hold_time}分でより良い結果が期待される",
                    "confidence": min(best_score, 1.0)
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 保有時間分析エラー: {e}")
            return None
    
    def close(self):
        """リソースのクリーンアップ"""
        self.logger.info("改善提案システム終了")
