"""
シグナルパフォーマンス追跡器

プロトレーダー向け為替アラートシステム用のシグナルパフォーマンス追跡器
設計書参照: /app/note/2025-01-15_実装計画_Phase3_パフォーマンス最適化.yaml
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.entry_signal_model import EntrySignalModel
from src.infrastructure.database.models.signal_performance_model import (
    SignalPerformanceModel,
)


class SignalPerformanceTracker:
    """
    シグナルパフォーマンス追跡器

    責任:
    - シグナル生成から実行までの全過程追跡
    - 実際の取引結果記録
    - パフォーマンス統計自動計算
    - 成功/失敗分析

    特徴:
    - リアルタイム追跡
    - 自動統計計算
    - 詳細分析
    - 履歴管理
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"

    async def track_signal_execution(
        self,
        signal: EntrySignalModel,
        execution_price: float,
        execution_time: datetime,
        exit_price: Optional[float] = None,
        exit_time: Optional[datetime] = None,
        exit_reason: Optional[str] = None,
    ) -> SignalPerformanceModel:
        """
        シグナル実行を追跡

        Args:
            signal: エントリーシグナル
            execution_price: 実行価格
            execution_time: 実行時刻
            exit_price: 決済価格
            exit_time: 決済時刻
            exit_reason: 決済理由

        Returns:
            SignalPerformanceModel: パフォーマンスレコード
        """
        try:
            # パフォーマンスレコードを作成
            performance_record = SignalPerformanceModel.create_performance_record(
                signal_id=signal.id if hasattr(signal, "id") else None,
                currency_pair=signal.currency_pair,
                timeframe=signal.timeframe,
                entry_time=execution_time,
                exit_time=exit_time,
                entry_price=execution_price,
                exit_price=exit_price,
                signal_type=signal.signal_type,
                confidence_score=signal.confidence_score,
                exit_reason=exit_reason,
            )

            # 損益を計算
            if exit_price:
                pnl = self._calculate_pnl(
                    signal.signal_type, execution_price, exit_price
                )
                pnl_percentage = self._calculate_pnl_percentage(
                    signal.signal_type, execution_price, exit_price
                )

                performance_record.pnl = pnl
                performance_record.pnl_percentage = pnl_percentage

                # 保有時間を計算
                if exit_time:
                    duration = exit_time - execution_time
                    performance_record.duration_minutes = int(
                        duration.total_seconds() / 60
                    )

            # データベースに保存
            self.db_session.add(performance_record)
            await self.db_session.commit()

            return performance_record

        except Exception as e:
            print(f"Error tracking signal execution: {e}")
            await self.db_session.rollback()
            raise

    async def update_signal_performance(
        self,
        performance_id: int,
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
    ) -> Optional[SignalPerformanceModel]:
        """
        シグナルパフォーマンスを更新

        Args:
            performance_id: パフォーマンスID
            exit_price: 決済価格
            exit_time: 決済時刻
            exit_reason: 決済理由

        Returns:
            Optional[SignalPerformanceModel]: 更新されたパフォーマンスレコード
        """
        try:
            # パフォーマンスレコードを取得
            query = select(SignalPerformanceModel).where(
                SignalPerformanceModel.id == performance_id
            )
            result = await self.db_session.execute(query)
            performance_record = result.scalar_one_or_none()

            if not performance_record:
                return None

            # 決済情報を更新
            performance_record.exit_price = exit_price
            performance_record.exit_time = exit_time
            performance_record.exit_reason = exit_reason

            # 損益を計算
            pnl = self._calculate_pnl(
                performance_record.signal_type,
                performance_record.entry_price,
                exit_price,
            )
            pnl_percentage = self._calculate_pnl_percentage(
                performance_record.signal_type,
                performance_record.entry_price,
                exit_price,
            )

            performance_record.pnl = pnl
            performance_record.pnl_percentage = pnl_percentage

            # 保有時間を計算
            if performance_record.entry_time and exit_time:
                duration = exit_time - performance_record.entry_time
                performance_record.duration_minutes = int(duration.total_seconds() / 60)

            # 最大損益・最大損失を計算
            await self._calculate_max_profit_loss(performance_record)

            # ドローダウンを計算
            await self._calculate_drawdown(performance_record)

            # 更新時刻を設定
            performance_record.updated_at = datetime.utcnow()

            # データベースに保存
            await self.db_session.commit()

            return performance_record

        except Exception as e:
            print(f"Error updating signal performance: {e}")
            await self.db_session.rollback()
            return None

    def _calculate_pnl(
        self, signal_type: str, entry_price: float, exit_price: float
    ) -> float:
        """
        損益を計算

        Args:
            signal_type: シグナルタイプ
            entry_price: エントリー価格
            exit_price: 決済価格

        Returns:
            float: 損益
        """
        if signal_type == "BUY":
            return exit_price - entry_price
        elif signal_type == "SELL":
            return entry_price - exit_price
        else:
            return 0.0

    def _calculate_pnl_percentage(
        self, signal_type: str, entry_price: float, exit_price: float
    ) -> float:
        """
        損益率を計算

        Args:
            signal_type: シグナルタイプ
            entry_price: エントリー価格
            exit_price: 決済価格

        Returns:
            float: 損益率（%）
        """
        if entry_price <= 0:
            return 0.0

        pnl = self._calculate_pnl(signal_type, entry_price, exit_price)
        return (pnl / entry_price) * 100

    async def _calculate_max_profit_loss(
        self, performance_record: SignalPerformanceModel
    ) -> None:
        """
        最大損益・最大損失を計算

        Args:
            performance_record: パフォーマンスレコード
        """
        try:
            # 実際の実装では価格履歴から最大損益・最大損失を計算
            # ここでは簡易実装として現在の損益を使用
            if performance_record.pnl is not None:
                if performance_record.pnl > 0:
                    performance_record.max_profit = performance_record.pnl
                    performance_record.max_loss = 0.0
                else:
                    performance_record.max_profit = 0.0
                    performance_record.max_loss = abs(performance_record.pnl)

        except Exception as e:
            print(f"Error calculating max profit/loss: {e}")

    async def _calculate_drawdown(
        self, performance_record: SignalPerformanceModel
    ) -> None:
        """
        ドローダウンを計算

        Args:
            performance_record: パフォーマンスレコード
        """
        try:
            # 実際の実装では価格履歴からドローダウンを計算
            # ここでは簡易実装として最大損失率を使用
            if (
                performance_record.max_loss is not None
                and performance_record.entry_price
            ):
                drawdown = (
                    performance_record.max_loss / performance_record.entry_price
                ) * 100
                performance_record.drawdown = min(drawdown, 100.0)

        except Exception as e:
            print(f"Error calculating drawdown: {e}")

    async def get_performance_statistics(
        self,
        currency_pair: Optional[str] = None,
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        パフォーマンス統計を取得

        Args:
            currency_pair: 通貨ペア
            timeframe: タイムフレーム
            start_date: 開始日
            end_date: 終了日

        Returns:
            Dict[str, Any]: パフォーマンス統計
        """
        try:
            # クエリを構築
            query = select(SignalPerformanceModel).where(
                SignalPerformanceModel.exit_price.isnot(None)
            )

            if currency_pair:
                query = query.where(
                    SignalPerformanceModel.currency_pair == currency_pair
                )

            if timeframe:
                query = query.where(SignalPerformanceModel.timeframe == timeframe)

            if start_date:
                query = query.where(SignalPerformanceModel.entry_time >= start_date)

            if end_date:
                query = query.where(SignalPerformanceModel.entry_time <= end_date)

            result = await self.db_session.execute(query)
            performance_records = result.scalars().all()

            if not performance_records:
                return self._get_empty_statistics()

            # 統計を計算
            return self._calculate_statistics(performance_records)

        except Exception as e:
            print(f"Error getting performance statistics: {e}")
            return self._get_empty_statistics()

    def _calculate_statistics(
        self, performance_records: List[SignalPerformanceModel]
    ) -> Dict[str, Any]:
        """
        統計を計算

        Args:
            performance_records: パフォーマンスレコードリスト

        Returns:
            Dict[str, Any]: 統計結果
        """
        total_trades = len(performance_records)
        winning_trades = len([r for r in performance_records if r.pnl > 0])
        losing_trades = len([r for r in performance_records if r.pnl < 0])

        # 勝率
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

        # 損益統計
        total_pnl = sum(r.pnl for r in performance_records if r.pnl is not None)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        avg_pnl_percentage = (
            sum(
                r.pnl_percentage
                for r in performance_records
                if r.pnl_percentage is not None
            )
            / total_trades
            if total_trades > 0
            else 0
        )

        # 最大損益・最大損失
        max_profit = max(
            (r.pnl for r in performance_records if r.pnl is not None), default=0
        )
        max_loss = min(
            (r.pnl for r in performance_records if r.pnl is not None), default=0
        )

        # 平均保有時間
        avg_duration = (
            sum(
                r.duration_minutes
                for r in performance_records
                if r.duration_minutes is not None
            )
            / total_trades
            if total_trades > 0
            else 0
        )

        # 最大ドローダウン
        max_drawdown = max(
            (r.drawdown for r in performance_records if r.drawdown is not None),
            default=0,
        )

        # リスク調整後リターン（簡易計算）
        risk_adjusted_return = (
            avg_pnl_percentage / max_drawdown if max_drawdown > 0 else 0
        )

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "avg_pnl_percentage": avg_pnl_percentage,
            "max_profit": max_profit,
            "max_loss": max_loss,
            "avg_duration_minutes": avg_duration,
            "max_drawdown": max_drawdown,
            "risk_adjusted_return": risk_adjusted_return,
            "profit_factor": abs(max_profit / max_loss) if max_loss != 0 else 0,
        }

    def _get_empty_statistics(self) -> Dict[str, Any]:
        """
        空の統計を取得

        Returns:
            Dict[str, Any]: 空の統計
        """
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_pnl": 0.0,
            "avg_pnl_percentage": 0.0,
            "max_profit": 0.0,
            "max_loss": 0.0,
            "avg_duration_minutes": 0,
            "max_drawdown": 0.0,
            "risk_adjusted_return": 0.0,
            "profit_factor": 0.0,
        }

    async def get_performance_by_timeframe(
        self, currency_pair: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        タイムフレーム別パフォーマンスを取得

        Args:
            currency_pair: 通貨ペア
            days: 取得日数

        Returns:
            Dict[str, Any]: タイムフレーム別パフォーマンス
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            timeframes = ["M5", "M15", "H1", "H4", "D1"]
            timeframe_stats = {}

            for timeframe in timeframes:
                stats = await self.get_performance_statistics(
                    currency_pair=currency_pair,
                    timeframe=timeframe,
                    start_date=start_date,
                )
                timeframe_stats[timeframe] = stats

            return {
                "currency_pair": currency_pair,
                "period_days": days,
                "timeframe_statistics": timeframe_stats,
                "analysis_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error getting performance by timeframe: {e}")
            return {}

    async def get_performance_by_confidence(
        self, currency_pair: str, days: int = 30
    ) -> Dict[str, Any]:
        """
        信頼度別パフォーマンスを取得

        Args:
            currency_pair: 通貨ペア
            days: 取得日数

        Returns:
            Dict[str, Any]: 信頼度別パフォーマンス
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # 信頼度範囲を定義
            confidence_ranges = [
                (0, 30, "Low"),
                (31, 60, "Medium"),
                (61, 80, "High"),
                (81, 100, "Very High"),
            ]

            confidence_stats = {}

            for min_conf, max_conf, label in confidence_ranges:
                # 信頼度範囲でフィルタリング
                query = select(SignalPerformanceModel).where(
                    SignalPerformanceModel.currency_pair == currency_pair,
                    SignalPerformanceModel.entry_time >= start_date,
                    SignalPerformanceModel.confidence_score >= min_conf,
                    SignalPerformanceModel.confidence_score <= max_conf,
                    SignalPerformanceModel.exit_price.isnot(None),
                )

                result = await self.db_session.execute(query)
                performance_records = result.scalars().all()

                if performance_records:
                    stats = self._calculate_statistics(performance_records)
                    confidence_stats[label] = stats
                else:
                    confidence_stats[label] = self._get_empty_statistics()

            return {
                "currency_pair": currency_pair,
                "period_days": days,
                "confidence_statistics": confidence_stats,
                "analysis_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error getting performance by confidence: {e}")
            return {}

    async def export_performance_data(
        self,
        currency_pair: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        パフォーマンスデータをエクスポート

        Args:
            currency_pair: 通貨ペア
            start_date: 開始日
            end_date: 終了日

        Returns:
            List[Dict[str, Any]]: パフォーマンスデータ
        """
        try:
            query = select(SignalPerformanceModel)

            if currency_pair:
                query = query.where(
                    SignalPerformanceModel.currency_pair == currency_pair
                )

            if start_date:
                query = query.where(SignalPerformanceModel.entry_time >= start_date)

            if end_date:
                query = query.where(SignalPerformanceModel.entry_time <= end_date)

            result = await self.db_session.execute(query)
            performance_records = result.scalars().all()

            return [record.to_dict() for record in performance_records]

        except Exception as e:
            print(f"Error exporting performance data: {e}")
            return []
