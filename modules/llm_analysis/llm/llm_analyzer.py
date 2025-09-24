"""
階層的LLM分析エンジン

言語化処理、日誌生成、改善提案を統合した階層的LLM分析システム。
ルールベース売買システムの補助機能として、自然言語での分析・報告・提案を行う。
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from .language_processor import LanguageProcessor
from .journal_generator import JournalGenerator
from .improvement_advisor import ImprovementAdvisor


class LLMAnalyzer:
    """階層的LLM分析エンジン"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # サブコンポーネントの初期化
        self.language_processor = LanguageProcessor()
        self.journal_generator = JournalGenerator()
        self.improvement_advisor = ImprovementAdvisor()
        
        self.logger.info("✅ 階層的LLM分析エンジン初期化完了")
    
    async def analyze_trade_snapshot(self, snapshot: Dict) -> Dict:
        """
        トレードスナップの分析
        
        Args:
            snapshot: トレードスナップショットデータ
            
        Returns:
            分析結果の辞書
        """
        try:
            self.logger.info("🔍 トレードスナップ分析開始")
            
            # 言語化処理
            trade_description = self.language_processor.describe_trade_snapshot(snapshot)
            technical_description = self.language_processor.describe_technical_indicators(
                snapshot.get('technical_indicators', {})
            )
            
            # 分析結果の構築
            analysis_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_type": "trade_snapshot",
                "trade_id": snapshot.get('trade_id', 'unknown'),
                "descriptions": {
                    "trade_summary": trade_description,
                    "technical_analysis": technical_description
                },
                "metadata": {
                    "entry_price": snapshot.get('entry_price', 0),
                    "direction": snapshot.get('direction', 'UNKNOWN'),
                    "session": snapshot.get('session', 'UNKNOWN'),
                    "risk_percent": snapshot.get('risk_percent', 0)
                }
            }
            
            self.logger.info("✅ トレードスナップ分析完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ トレードスナップ分析エラー: {e}")
            return {
                "error": f"トレードスナップ分析中にエラーが発生しました: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_daily_analysis(self, daily_data: Dict) -> Dict:
        """
        日次分析の生成
        
        Args:
            daily_data: 日次データ
            
        Returns:
            日次分析結果の辞書
        """
        try:
            self.logger.info("📊 日次分析生成開始")
            
            trades = daily_data.get('trades', [])
            performance_metrics = daily_data.get('performance_metrics', {})
            market_conditions = daily_data.get('market_conditions', {})
            
            # 日次日誌の生成
            daily_journal = self.journal_generator.generate_daily_journal(trades)
            
            # パフォーマンスの言語化
            performance_description = self.language_processor.describe_performance(performance_metrics)
            
            # 市場状況の言語化
            market_description = self.language_processor.describe_market_conditions(market_conditions)
            
            # 改善提案の生成
            improvement_suggestions = self.improvement_advisor.suggest_rule_improvements(
                daily_data.get('rule_performance', {})
            )
            
            # 分析結果の構築
            analysis_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_type": "daily_analysis",
                "date": daily_data.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d')),
                "content": {
                    "daily_journal": daily_journal,
                    "performance_analysis": performance_description,
                    "market_conditions": market_description,
                    "improvement_suggestions": improvement_suggestions
                },
                "statistics": {
                    "total_trades": len(trades),
                    "win_rate": performance_metrics.get('win_rate', 0),
                    "total_profit": performance_metrics.get('total_profit', 0),
                    "adherence_score": performance_metrics.get('adherence_score', 0)
                }
            }
            
            self.logger.info("✅ 日次分析生成完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ 日次分析生成エラー: {e}")
            return {
                "error": f"日次分析生成中にエラーが発生しました: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_weekly_analysis(self, weekly_data: Dict) -> Dict:
        """
        週次分析の生成
        
        Args:
            weekly_data: 週次データ
            
        Returns:
            週次分析結果の辞書
        """
        try:
            self.logger.info("📈 週次分析生成開始")
            
            # 週次レポートの生成
            weekly_report = self.journal_generator.generate_weekly_report(weekly_data)
            
            # ルールパフォーマンス日誌の生成
            rule_performance_journal = self.journal_generator.generate_rule_performance_journal(
                weekly_data.get('rule_performance', {})
            )
            
            # 改善提案の生成
            improvement_suggestions = self.improvement_advisor.suggest_rule_improvements(
                weekly_data.get('rule_performance', {})
            )
            
            # パラメータ調整提案の生成
            parameter_suggestions = self.improvement_advisor.suggest_parameter_adjustments(
                weekly_data.get('backtest_results', {})
            )
            
            # 分析結果の構築
            analysis_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_type": "weekly_analysis",
                "week_start": weekly_data.get('start_date', ''),
                "week_end": weekly_data.get('end_date', ''),
                "content": {
                    "weekly_report": weekly_report,
                    "rule_performance_analysis": rule_performance_journal,
                    "improvement_suggestions": improvement_suggestions,
                    "parameter_adjustments": parameter_suggestions
                },
                "statistics": {
                    "total_trades": weekly_data.get('total_trades', 0),
                    "win_rate": weekly_data.get('win_rate', 0),
                    "total_profit": weekly_data.get('total_profit', 0),
                    "max_drawdown": weekly_data.get('max_drawdown', 0),
                    "adherence_score": weekly_data.get('adherence_score', 0)
                }
            }
            
            self.logger.info("✅ 週次分析生成完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ 週次分析生成エラー: {e}")
            return {
                "error": f"週次分析生成中にエラーが発生しました: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_monthly_analysis(self, monthly_data: Dict) -> Dict:
        """
        月次分析の生成
        
        Args:
            monthly_data: 月次データ
            
        Returns:
            月次分析結果の辞書
        """
        try:
            self.logger.info("📊 月次分析生成開始")
            
            # 月次レポートの生成
            monthly_report = self.journal_generator.generate_monthly_report(monthly_data)
            
            # 改善提案の生成
            improvement_suggestions = self.improvement_advisor.suggest_rule_improvements(
                monthly_data.get('rule_performance', {})
            )
            
            # リスク管理改善提案の生成
            risk_improvements = self.improvement_advisor.suggest_risk_management_improvements(
                monthly_data.get('risk_metrics', {})
            )
            
            # タイミング改善提案の生成
            timing_improvements = self.improvement_advisor.suggest_timing_improvements(
                monthly_data.get('timing_analysis', {})
            )
            
            # 分析結果の構築
            analysis_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_type": "monthly_analysis",
                "month": monthly_data.get('month', ''),
                "content": {
                    "monthly_report": monthly_report,
                    "improvement_suggestions": improvement_suggestions,
                    "risk_management_improvements": risk_improvements,
                    "timing_improvements": timing_improvements
                },
                "statistics": {
                    "total_trades": monthly_data.get('total_trades', 0),
                    "win_rate": monthly_data.get('win_rate', 0),
                    "total_profit": monthly_data.get('total_profit', 0),
                    "sharpe_ratio": monthly_data.get('sharpe_ratio', 0),
                    "max_drawdown": monthly_data.get('max_drawdown', 0),
                    "adherence_score": monthly_data.get('adherence_score', 0)
                }
            }
            
            self.logger.info("✅ 月次分析生成完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ 月次分析生成エラー: {e}")
            return {
                "error": f"月次分析生成中にエラーが発生しました: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def analyze_rule_evaluation(self, evaluation_data: Dict) -> Dict:
        """
        ルール評価結果の分析
        
        Args:
            evaluation_data: ルール評価データ
            
        Returns:
            ルール評価分析結果の辞書
        """
        try:
            self.logger.info("🔍 ルール評価分析開始")
            
            # ルール評価の言語化
            rule_description = self.language_processor.describe_rule_evaluation(evaluation_data)
            
            # 改善提案の生成
            improvement_suggestions = []
            if evaluation_data.get('score', 0) < 0.6:
                rule_name = evaluation_data.get('rule_name', 'unknown')
                improvement_suggestions.append(f"{rule_name}のスコアが低いため、条件の見直しを検討してください")
            
            # 分析結果の構築
            analysis_result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_type": "rule_evaluation",
                "rule_name": evaluation_data.get('rule_name', 'unknown'),
                "content": {
                    "rule_analysis": rule_description,
                    "improvement_suggestions": improvement_suggestions
                },
                "metrics": {
                    "score": evaluation_data.get('score', 0),
                    "conditions_met": len(evaluation_data.get('conditions_met', [])),
                    "conditions_failed": len(evaluation_data.get('conditions_failed', []))
                }
            }
            
            self.logger.info("✅ ルール評価分析完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ ルール評価分析エラー: {e}")
            return {
                "error": f"ルール評価分析中にエラーが発生しました: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def generate_comprehensive_report(self, comprehensive_data: Dict) -> Dict:
        """
        包括的レポートの生成
        
        Args:
            comprehensive_data: 包括的データ
            
        Returns:
            包括的レポートの辞書
        """
        try:
            self.logger.info("📋 包括的レポート生成開始")
            
            # 各分析の実行
            daily_analysis = await self.generate_daily_analysis(
                comprehensive_data.get('daily_data', {})
            )
            
            weekly_analysis = await self.generate_weekly_analysis(
                comprehensive_data.get('weekly_data', {})
            )
            
            monthly_analysis = await self.generate_monthly_analysis(
                comprehensive_data.get('monthly_data', {})
            )
            
            # 包括的レポートの構築
            comprehensive_report = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analysis_type": "comprehensive_report",
                "period": comprehensive_data.get('period', ''),
                "content": {
                    "daily_analysis": daily_analysis,
                    "weekly_analysis": weekly_analysis,
                    "monthly_analysis": monthly_analysis
                },
                "summary": {
                    "total_analyses": 3,
                    "successful_analyses": sum([
                        1 for analysis in [daily_analysis, weekly_analysis, monthly_analysis]
                        if 'error' not in analysis
                    ]),
                    "failed_analyses": sum([
                        1 for analysis in [daily_analysis, weekly_analysis, monthly_analysis]
                        if 'error' in analysis
                    ])
                }
            }
            
            self.logger.info("✅ 包括的レポート生成完了")
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"❌ 包括的レポート生成エラー: {e}")
            return {
                "error": f"包括的レポート生成中にエラーが発生しました: {e}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def get_analysis_capabilities(self) -> Dict:
        """
        分析機能の一覧取得
        
        Returns:
            分析機能の辞書
        """
        return {
            "capabilities": [
                "trade_snapshot_analysis",
                "daily_analysis",
                "weekly_analysis", 
                "monthly_analysis",
                "rule_evaluation_analysis",
                "comprehensive_report"
            ],
            "components": [
                "language_processor",
                "journal_generator",
                "improvement_advisor"
            ],
            "supported_languages": ["ja", "en"],
            "output_formats": ["text", "json", "structured"]
        }
    
    async def close(self):
        """リソースのクリーンアップ"""
        try:
            self.language_processor.close()
            self.journal_generator.close()
            self.improvement_advisor.close()
            self.logger.info("✅ 階層的LLM分析エンジン終了")
        except Exception as e:
            self.logger.error(f"❌ LLM分析エンジン終了エラー: {e}")
