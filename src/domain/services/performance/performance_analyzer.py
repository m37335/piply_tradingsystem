"""
統計分析機能

プロトレーダー向け為替アラートシステム用の統計分析機能
設計書参照: /app/note/2025-01-15_実装計画_Phase3_パフォーマンス最適化.yaml
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.signal_performance_model import (
    SignalPerformanceModel,
)


class PerformanceAnalyzer:
    """
    統計分析機能

    責任:
    - 勝率、平均損益、最大ドローダウンの計算
    - 時間軸別、指標別の分析
    - リスク調整後リターンの計算
    - 統計レポートの自動生成

    特徴:
    - 詳細統計計算
    - 多角度分析
    - リスク調整
    - レポート生成
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session

    async def analyze_performance(
        self,
        currency_pair: Optional[str] = None,
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        パフォーマンス分析を実行

        Args:
            currency_pair: 通貨ペア
            timeframe: タイムフレーム
            start_date: 開始日
            end_date: 終了日

        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # パフォーマンスデータを取得
            performance_data = await self._get_performance_data(
                currency_pair, timeframe, start_date, end_date
            )

            if not performance_data:
                return self._get_empty_analysis()

            # 基本統計を計算
            basic_stats = self._calculate_basic_statistics(performance_data)

            # リスク統計を計算
            risk_stats = self._calculate_risk_statistics(performance_data)

            # 時間軸別分析
            timeframe_analysis = await self._analyze_by_timeframe(
                currency_pair, start_date, end_date
            )

            # 指標別分析
            indicator_analysis = await self._analyze_by_indicators(
                currency_pair, start_date, end_date
            )

            # リスク調整後リターンを計算
            risk_adjusted_metrics = self._calculate_risk_adjusted_metrics(
                basic_stats, risk_stats
            )

            return {
                "analysis_period": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                },
                "currency_pair": currency_pair,
                "timeframe": timeframe,
                "basic_statistics": basic_stats,
                "risk_statistics": risk_stats,
                "risk_adjusted_metrics": risk_adjusted_metrics,
                "timeframe_analysis": timeframe_analysis,
                "indicator_analysis": indicator_analysis,
                "analysis_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error analyzing performance: {e}")
            return self._get_empty_analysis()

    async def _get_performance_data(
        self,
        currency_pair: Optional[str],
        timeframe: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> List[SignalPerformanceModel]:
        """
        パフォーマンスデータを取得

        Args:
            currency_pair: 通貨ペア
            timeframe: タイムフレーム
            start_date: 開始日
            end_date: 終了日

        Returns:
            List[SignalPerformanceModel]: パフォーマンスデータ
        """
        query = select(SignalPerformanceModel).where(
            SignalPerformanceModel.exit_price.isnot(None)
        )

        if currency_pair:
            query = query.where(SignalPerformanceModel.currency_pair == currency_pair)

        if timeframe:
            query = query.where(SignalPerformanceModel.timeframe == timeframe)

        if start_date:
            query = query.where(SignalPerformanceModel.entry_time >= start_date)

        if end_date:
            query = query.where(SignalPerformanceModel.entry_time <= end_date)

        result = await self.db_session.execute(query)
        return result.scalars().all()

    def _calculate_basic_statistics(
        self, performance_data: List[SignalPerformanceModel]
    ) -> Dict[str, Any]:
        """
        基本統計を計算

        Args:
            performance_data: パフォーマンスデータ

        Returns:
            Dict[str, Any]: 基本統計
        """
        if not performance_data:
            return {}

        # 取引数統計
        total_trades = len(performance_data)
        winning_trades = len([r for r in performance_data if r.pnl > 0])
        losing_trades = len([r for r in performance_data if r.pnl < 0])
        breakeven_trades = total_trades - winning_trades - losing_trades

        # 勝率
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        # 損益統計
        pnl_values = [r.pnl for r in performance_data if r.pnl is not None]
        pnl_percentages = [
            r.pnl_percentage for r in performance_data if r.pnl_percentage is not None
        ]

        total_pnl = sum(pnl_values)
        avg_pnl = np.mean(pnl_values) if pnl_values else 0
        avg_pnl_percentage = np.mean(pnl_percentages) if pnl_percentages else 0

        # 最大・最小値
        max_profit = max(pnl_values) if pnl_values else 0
        max_loss = min(pnl_values) if pnl_values else 0
        max_profit_percentage = max(pnl_percentages) if pnl_percentages else 0
        max_loss_percentage = min(pnl_percentages) if pnl_percentages else 0

        # 標準偏差
        pnl_std = np.std(pnl_values) if len(pnl_values) > 1 else 0
        pnl_percentage_std = np.std(pnl_percentages) if len(pnl_percentages) > 1 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "breakeven_trades": breakeven_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_pnl_percentage": avg_pnl_percentage,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "max_profit_percentage": max_profit_percentage,
            "max_loss_percentage": max_loss_percentage,
            "pnl_std": pnl_std,
            "pnl_percentage_std": pnl_percentage_std,
        }

    def _calculate_risk_statistics(
        self, performance_data: List[SignalPerformanceModel]
    ) -> Dict[str, Any]:
        """
        リスク統計を計算

        Args:
            performance_data: パフォーマンスデータ

        Returns:
            Dict[str, Any]: リスク統計
        """
        if not performance_data:
            return {}

        # ドローダウン統計
        drawdowns = [r.drawdown for r in performance_data if r.drawdown is not None]
        max_drawdown = max(drawdowns) if drawdowns else 0
        avg_drawdown = np.mean(drawdowns) if drawdowns else 0

        # 保有時間統計
        durations = [
            r.duration_minutes
            for r in performance_data
            if r.duration_minutes is not None
        ]
        avg_duration = np.mean(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        # 連続勝敗統計
        consecutive_stats = self._calculate_consecutive_stats(performance_data)

        # 最大損失期間
        max_loss_period = self._calculate_max_loss_period(performance_data)

        return {
            "max_drawdown": max_drawdown,
            "avg_drawdown": avg_drawdown,
            "avg_duration_minutes": avg_duration,
            "min_duration_minutes": min_duration,
            "max_duration_minutes": max_duration,
            "consecutive_stats": consecutive_stats,
            "max_loss_period": max_loss_period,
        }

    def _calculate_consecutive_stats(
        self, performance_data: List[SignalPerformanceModel]
    ) -> Dict[str, Any]:
        """
        連続勝敗統計を計算

        Args:
            performance_data: パフォーマンスデータ

        Returns:
            Dict[str, Any]: 連続勝敗統計
        """
        if not performance_data:
            return {}

        # 時系列順にソート
        sorted_data = sorted(performance_data, key=lambda x: x.entry_time)

        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_wins = 0
        current_losses = 0

        for record in sorted_data:
            if record.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, current_wins)
            elif record.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, current_losses)

        return {
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
        }

    def _calculate_max_loss_period(
        self, performance_data: List[SignalPerformanceModel]
    ) -> Dict[str, Any]:
        """
        最大損失期間を計算

        Args:
            performance_data: パフォーマンスデータ

        Returns:
            Dict[str, Any]: 最大損失期間
        """
        if not performance_data:
            return {}

        # 時系列順にソート
        sorted_data = sorted(performance_data, key=lambda x: x.entry_time)

        max_loss_period = 0
        current_loss_period = 0
        cumulative_loss = 0
        max_cumulative_loss = 0

        for record in sorted_data:
            if record.pnl < 0:
                current_loss_period += 1
                cumulative_loss += abs(record.pnl)
                max_cumulative_loss = max(max_cumulative_loss, cumulative_loss)
            else:
                max_loss_period = max(max_loss_period, current_loss_period)
                current_loss_period = 0
                cumulative_loss = 0

        return {
            "max_loss_period": max_loss_period,
            "max_cumulative_loss": max_cumulative_loss,
        }

    def _calculate_risk_adjusted_metrics(
        self, basic_stats: Dict[str, Any], risk_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        リスク調整後メトリクスを計算

        Args:
            basic_stats: 基本統計
            risk_stats: リスク統計

        Returns:
            Dict[str, Any]: リスク調整後メトリクス
        """
        avg_pnl_percentage = basic_stats.get("avg_pnl_percentage", 0)
        pnl_std = basic_stats.get("pnl_percentage_std", 0)
        max_drawdown = risk_stats.get("max_drawdown", 0)

        # シャープレシオ（簡易版）
        risk_free_rate = 0.02  # 2%の無リスク金利
        sharpe_ratio = (
            (avg_pnl_percentage - risk_free_rate) / pnl_std if pnl_std > 0 else 0
        )

        # ソルティノレシオ
        downside_returns = [r for r in [avg_pnl_percentage] if r < 0]
        downside_std = np.std(downside_returns) if downside_returns else 0
        sortino_ratio = (
            (avg_pnl_percentage - risk_free_rate) / downside_std
            if downside_std > 0
            else 0
        )

        # カルマーレシオ
        calmar_ratio = avg_pnl_percentage / max_drawdown if max_drawdown > 0 else 0

        # プロフィットファクター
        total_pnl = basic_stats.get("total_pnl", 0)
        max_loss = basic_stats.get("max_loss", 0)
        profit_factor = abs(total_pnl / max_loss) if max_loss != 0 else 0

        return {
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "calmar_ratio": calmar_ratio,
            "profit_factor": profit_factor,
            "risk_free_rate": risk_free_rate,
        }

    async def _analyze_by_timeframe(
        self,
        currency_pair: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Dict[str, Any]:
        """
        時間軸別分析を実行

        Args:
            currency_pair: 通貨ペア
            start_date: 開始日
            end_date: 終了日

        Returns:
            Dict[str, Any]: 時間軸別分析結果
        """
        timeframes = ["M5", "M15", "H1", "H4", "D1"]
        timeframe_analysis = {}

        for timeframe in timeframes:
            data = await self._get_performance_data(
                currency_pair, timeframe, start_date, end_date
            )

            if data:
                basic_stats = self._calculate_basic_statistics(data)
                risk_stats = self._calculate_risk_statistics(data)
                risk_adjusted = self._calculate_risk_adjusted_metrics(
                    basic_stats, risk_stats
                )

                timeframe_analysis[timeframe] = {
                    "basic_statistics": basic_stats,
                    "risk_statistics": risk_stats,
                    "risk_adjusted_metrics": risk_adjusted,
                }
            else:
                timeframe_analysis[timeframe] = self._get_empty_analysis()

        return timeframe_analysis

    async def _analyze_by_indicators(
        self,
        currency_pair: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> Dict[str, Any]:
        """
        指標別分析を実行

        Args:
            currency_pair: 通貨ペア
            start_date: 開始日
            end_date: 終了日

        Returns:
            Dict[str, Any]: 指標別分析結果
        """
        # 信頼度別分析
        confidence_ranges = [
            (0, 30, "Low"),
            (31, 60, "Medium"),
            (61, 80, "High"),
            (81, 100, "Very High"),
        ]

        indicator_analysis = {}

        for min_conf, max_conf, label in confidence_ranges:
            query = select(SignalPerformanceModel).where(
                SignalPerformanceModel.exit_price.isnot(None)
            )

            if currency_pair:
                query = query.where(
                    SignalPerformanceModel.currency_pair == currency_pair
                )

            if start_date:
                query = query.where(SignalPerformanceModel.entry_time >= start_date)

            if end_date:
                query = query.where(SignalPerformanceModel.entry_time <= end_date)

            query = query.where(
                SignalPerformanceModel.confidence_score >= min_conf,
                SignalPerformanceModel.confidence_score <= max_conf,
            )

            result = await self.db_session.execute(query)
            data = result.scalars().all()

            if data:
                basic_stats = self._calculate_basic_statistics(data)
                risk_stats = self._calculate_risk_statistics(data)
                risk_adjusted = self._calculate_risk_adjusted_metrics(
                    basic_stats, risk_stats
                )

                indicator_analysis[f"confidence_{label}"] = {
                    "basic_statistics": basic_stats,
                    "risk_statistics": risk_stats,
                    "risk_adjusted_metrics": risk_adjusted,
                }
            else:
                indicator_analysis[f"confidence_{label}"] = self._get_empty_analysis()

        return indicator_analysis

    def _get_empty_analysis(self) -> Dict[str, Any]:
        """
        空の分析結果を取得

        Returns:
            Dict[str, Any]: 空の分析結果
        """
        return {
            "basic_statistics": {},
            "risk_statistics": {},
            "risk_adjusted_metrics": {},
        }

    async def generate_performance_report(
        self,
        currency_pair: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        パフォーマンスレポートを生成

        Args:
            currency_pair: 通貨ペア
            start_date: 開始日
            end_date: 終了日

        Returns:
            Dict[str, Any]: パフォーマンスレポート
        """
        try:
            # 包括的な分析を実行
            analysis = await self.analyze_performance(
                currency_pair=currency_pair,
                start_date=start_date,
                end_date=end_date,
            )

            # レポート要約を生成
            summary = self._generate_report_summary(analysis)

            # 推奨事項を生成
            recommendations = self._generate_recommendations(analysis)

            return {
                "report_info": {
                    "currency_pair": currency_pair,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "generated_at": datetime.utcnow().isoformat(),
                },
                "summary": summary,
                "detailed_analysis": analysis,
                "recommendations": recommendations,
            }

        except Exception as e:
            print(f"Error generating performance report: {e}")
            return {}

    def _generate_report_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        レポート要約を生成

        Args:
            analysis: 分析結果

        Returns:
            Dict[str, Any]: レポート要約
        """
        basic_stats = analysis.get("basic_statistics", {})
        risk_stats = analysis.get("risk_statistics", {})
        risk_adjusted = analysis.get("risk_adjusted_metrics", {})

        return {
            "total_trades": basic_stats.get("total_trades", 0),
            "win_rate": basic_stats.get("win_rate", 0),
            "total_pnl": basic_stats.get("total_pnl", 0),
            "avg_pnl_percentage": basic_stats.get("avg_pnl_percentage", 0),
            "max_drawdown": risk_stats.get("max_drawdown", 0),
            "sharpe_ratio": risk_adjusted.get("sharpe_ratio", 0),
            "profit_factor": risk_adjusted.get("profit_factor", 0),
        }

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        推奨事項を生成

        Args:
            analysis: 分析結果

        Returns:
            List[str]: 推奨事項リスト
        """
        recommendations = []
        basic_stats = analysis.get("basic_statistics", {})
        risk_stats = analysis.get("risk_statistics", {})
        risk_adjusted = analysis.get("risk_adjusted_metrics", {})

        win_rate = basic_stats.get("win_rate", 0)
        avg_pnl_percentage = basic_stats.get("avg_pnl_percentage", 0)
        max_drawdown = risk_stats.get("max_drawdown", 0)
        sharpe_ratio = risk_adjusted.get("sharpe_ratio", 0)

        # 勝率に関する推奨
        if win_rate < 40:
            recommendations.append(
                "勝率が低いため、エントリー条件の見直しを検討してください"
            )
        elif win_rate > 70:
            recommendations.append(
                "勝率が高いため、リスク/リワード比の最適化を検討してください"
            )

        # 平均損益に関する推奨
        if avg_pnl_percentage < 0:
            recommendations.append(
                "平均損益がマイナスのため、戦略全体の見直しが必要です"
            )

        # ドローダウンに関する推奨
        if max_drawdown > 20:
            recommendations.append(
                "最大ドローダウンが大きいため、リスク管理の強化が必要です"
            )

        # シャープレシオに関する推奨
        if sharpe_ratio < 1.0:
            recommendations.append(
                "シャープレシオが低いため、リスク調整後リターンの改善を検討してください"
            )

        return recommendations
