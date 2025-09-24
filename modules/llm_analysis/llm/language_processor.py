"""
言語化処理システム

数値データを人間が理解しやすい自然言語に変換する。
ルールベース売買システムの補助機能として、テクニカル指標や
トレード結果を自然言語で説明する。
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json


class LanguageProcessor:
    """数値データの言語化処理"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("✅ 言語化処理システム初期化完了")
    
    def describe_trade_snapshot(self, snapshot: Dict) -> str:
        """
        トレードスナップの言語化
        
        Args:
            snapshot: トレードスナップショットデータ
            
        Returns:
            自然言語でのトレード説明
        """
        try:
            # 基本情報の抽出
            entry_price = snapshot.get('entry_price', 0)
            direction = snapshot.get('direction', 'UNKNOWN')
            rsi = snapshot.get('rsi', 0)
            macd = snapshot.get('macd', 0)
            ema_200 = snapshot.get('ema_200', 0)
            fibonacci_position = snapshot.get('fibonacci_position', 'NONE')
            session = snapshot.get('session', 'UNKNOWN')
            risk_percent = snapshot.get('risk_percent', 0)
            
            # 方向の日本語化
            direction_jp = "買い" if direction.upper() == "BUY" else "売り" if direction.upper() == "SELL" else "不明"
            
            # セッションの日本語化
            session_jp = {
                'Tokyo': '東京',
                'London': 'ロンドン', 
                'NewYork': 'ニューヨーク',
                'UNKNOWN': '不明'
            }.get(session, session)
            
            # フィボナッチ位置の日本語化
            fib_jp = {
                'NONE': 'フィボナッチレベル外',
                'Fib_0.236': 'フィボナッチ23.6%レベル',
                'Fib_0.382': 'フィボナッチ38.2%レベル',
                'Fib_0.5': 'フィボナッチ50%レベル',
                'Fib_0.618': 'フィボナッチ61.8%レベル',
                'Fib_0.786': 'フィボナッチ78.6%レベル',
                'Fib_1.0': 'フィボナッチ100%レベル',
                'Fib_1.272': 'フィボナッチ127.2%レベル',
                'Fib_1.618': 'フィボナッチ161.8%レベル'
            }.get(fibonacci_position, fibonacci_position)
            
            description = f"""
【トレード詳細】
エントリー価格: {entry_price:.5f}で{direction_jp}ポジションを開始。
RSI: {rsi:.1f}、MACD: {macd:.5f}、EMA200: {ema_200:.5f}。
{fib_jp}。
セッション: {session_jp}、リスク: {risk_percent:.1f}%。
"""
            
            return description.strip()
            
        except Exception as e:
            self.logger.error(f"❌ トレードスナップ言語化エラー: {e}")
            return f"トレードスナップの言語化中にエラーが発生しました: {e}"
    
    def describe_performance(self, metrics: Dict) -> str:
        """
        パフォーマンス指標の言語化
        
        Args:
            metrics: パフォーマンス指標データ
            
        Returns:
            自然言語でのパフォーマンス説明
        """
        try:
            win_rate = metrics.get('win_rate', 0)
            total_profit = metrics.get('total_profit', 0)
            max_drawdown = metrics.get('max_drawdown', 0)
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            adherence_score = metrics.get('adherence_score', 0)
            total_trades = metrics.get('total_trades', 0)
            
            # パフォーマンス評価
            if win_rate >= 70:
                win_rate_eval = "優秀"
            elif win_rate >= 60:
                win_rate_eval = "良好"
            elif win_rate >= 50:
                win_rate_eval = "普通"
            else:
                win_rate_eval = "改善必要"
            
            if adherence_score >= 90:
                adherence_eval = "優秀"
            elif adherence_score >= 80:
                adherence_eval = "良好"
            elif adherence_score >= 70:
                adherence_eval = "普通"
            else:
                adherence_eval = "改善必要"
            
            description = f"""
【パフォーマンス分析】
本日のパフォーマンス: 勝率{win_rate:.1f}%（{win_rate_eval}）、総利益{total_profit:.1f}pips。
最大ドローダウン: {max_drawdown:.2f}%、シャープレシオ: {sharpe_ratio:.2f}。
ルール遵守スコア: {adherence_score:.1f}/100（{adherence_eval}）。
総トレード数: {total_trades}件。
"""
            
            return description.strip()
            
        except Exception as e:
            self.logger.error(f"❌ パフォーマンス言語化エラー: {e}")
            return f"パフォーマンス指標の言語化中にエラーが発生しました: {e}"
    
    def describe_market_conditions(self, market_data: Dict) -> str:
        """
        市場状況の言語化
        
        Args:
            market_data: 市場データ
            
        Returns:
            自然言語での市場状況説明
        """
        try:
            current_price = market_data.get('current_price', 0)
            trend_direction = market_data.get('trend_direction', 'UNKNOWN')
            volatility = market_data.get('volatility', 'UNKNOWN')
            session = market_data.get('session', 'UNKNOWN')
            
            # トレンド方向の日本語化
            trend_jp = {
                'BULLISH': '上昇トレンド',
                'BEARISH': '下降トレンド',
                'SIDEWAYS': '横ばい',
                'UNKNOWN': '不明'
            }.get(trend_direction, trend_direction)
            
            # ボラティリティの日本語化
            vol_jp = {
                'HIGH': '高ボラティリティ',
                'MEDIUM': '中程度のボラティリティ',
                'LOW': '低ボラティリティ',
                'UNKNOWN': '不明'
            }.get(volatility, volatility)
            
            # セッションの日本語化
            session_jp = {
                'Tokyo': '東京セッション',
                'London': 'ロンドンセッション',
                'NewYork': 'ニューヨークセッション',
                'UNKNOWN': '不明'
            }.get(session, session)
            
            description = f"""
【市場状況】
現在価格: {current_price:.5f}
トレンド: {trend_jp}
ボラティリティ: {vol_jp}
アクティブセッション: {session_jp}
"""
            
            return description.strip()
            
        except Exception as e:
            self.logger.error(f"❌ 市場状況言語化エラー: {e}")
            return f"市場状況の言語化中にエラーが発生しました: {e}"
    
    def describe_technical_indicators(self, indicators: Dict) -> str:
        """
        テクニカル指標の言語化
        
        Args:
            indicators: テクニカル指標データ
            
        Returns:
            自然言語でのテクニカル指標説明
        """
        try:
            rsi = indicators.get('RSI_14', 0)
            macd = indicators.get('MACD', 0)
            macd_signal = indicators.get('MACD_Signal', 0)
            ema_21 = indicators.get('EMA_21', 0)
            ema_200 = indicators.get('EMA_200', 0)
            atr = indicators.get('ATR_14', 0)
            
            # RSIの評価
            if rsi <= 30:
                rsi_eval = "売られすぎ"
            elif rsi <= 40:
                rsi_eval = "やや売られすぎ"
            elif rsi >= 70:
                rsi_eval = "買われすぎ"
            elif rsi >= 60:
                rsi_eval = "やや買われすぎ"
            else:
                rsi_eval = "中立"
            
            # MACDの評価
            if macd > macd_signal:
                macd_eval = "上昇モメンタム"
            elif macd < macd_signal:
                macd_eval = "下降モメンタム"
            else:
                macd_eval = "中立"
            
            # EMAの評価
            if ema_21 > ema_200:
                ema_eval = "短期トレンド上昇"
            elif ema_21 < ema_200:
                ema_eval = "短期トレンド下降"
            else:
                ema_eval = "トレンド中立"
            
            description = f"""
【テクニカル指標】
RSI(14): {rsi:.1f}（{rsi_eval}）
MACD: {macd:.5f}（{macd_eval}）
EMA21: {ema_21:.5f}、EMA200: {ema_200:.5f}（{ema_eval}）
ATR(14): {atr:.5f}（ボラティリティ指標）
"""
            
            return description.strip()
            
        except Exception as e:
            self.logger.error(f"❌ テクニカル指標言語化エラー: {e}")
            return f"テクニカル指標の言語化中にエラーが発生しました: {e}"
    
    def describe_rule_evaluation(self, evaluation: Dict) -> str:
        """
        ルール評価結果の言語化
        
        Args:
            evaluation: ルール評価結果
            
        Returns:
            自然言語でのルール評価説明
        """
        try:
            rule_name = evaluation.get('rule_name', 'UNKNOWN')
            score = evaluation.get('score', 0)
            conditions_met = evaluation.get('conditions_met', [])
            conditions_failed = evaluation.get('conditions_failed', [])
            
            # ルール名の日本語化
            rule_jp = {
                'pullback_buy': '押し目買い',
                'breakout_buy': 'ブレイクアウト買い',
                'reversal_sell': '逆張り売り',
                'UNKNOWN': '不明'
            }.get(rule_name, rule_name)
            
            # スコアの評価
            if score >= 0.8:
                score_eval = "条件良好"
            elif score >= 0.6:
                score_eval = "条件普通"
            elif score >= 0.4:
                score_eval = "条件やや悪い"
            else:
                score_eval = "条件悪い"
            
            description = f"""
【ルール評価: {rule_jp}】
スコア: {score:.2f}（{score_eval}）
成立条件: {len(conditions_met)}個
未成立条件: {len(conditions_failed)}個
"""
            
            if conditions_met:
                description += f"\n成立条件: {', '.join(conditions_met)}"
            
            if conditions_failed:
                description += f"\n未成立条件: {', '.join(conditions_failed)}"
            
            return description.strip()
            
        except Exception as e:
            self.logger.error(f"❌ ルール評価言語化エラー: {e}")
            return f"ルール評価の言語化中にエラーが発生しました: {e}"
    
    def close(self):
        """リソースのクリーンアップ"""
        self.logger.info("言語化処理システム終了")
