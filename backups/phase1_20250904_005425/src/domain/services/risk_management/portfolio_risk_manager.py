"""
ポートフォリオリスク管理器

プロトレーダー向け為替アラートシステム用のポートフォリオリスク管理器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.infrastructure.database.models.entry_signal_model import EntrySignalModel
from src.infrastructure.database.models.risk_alert_model import RiskAlertModel


class PortfolioRiskManager:
    """
    ポートフォリオリスク管理器

    責任:
    - ポートフォリオ全体のリスク監視
    - 最大リスク制限の管理
    - ポジション分散の最適化
    - リスク警告の生成

    特徴:
    - リアルタイムリスク監視
    - 動的リスク制限
    - 分散最適化
    - 警告システム
    """

    def __init__(self):
        """
        初期化
        """
        # リスク設定
        self.max_portfolio_risk = 0.20  # 最大ポートフォリオリスク（20%）
        self.max_single_position_risk = 0.05  # 最大単一ポジションリスク（5%）
        self.max_correlation_risk = 0.15  # 最大相関リスク（15%）
        self.max_currency_exposure = 0.30  # 最大通貨エクスポージャー（30%）

        # リスク履歴
        self.risk_history = []

    def calculate_portfolio_risk(
        self,
        current_positions: List[Dict[str, Any]],
        account_balance: float,
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """
        ポートフォリオリスクを計算

        Args:
            current_positions: 現在のポジションリスト
            account_balance: アカウント残高
            correlation_matrix: 相関性行列

        Returns:
            Dict[str, Any]: ポートフォリオリスク分析結果
        """
        if not current_positions or account_balance <= 0:
            return {
                "total_risk": 0.0,
                "risk_percentage": 0.0,
                "risk_components": {},
                "risk_alerts": [],
                "is_within_limits": True,
            }

        # 各リスクコンポーネントを計算
        individual_risks = self._calculate_individual_risks(
            current_positions, account_balance
        )

        correlation_risk = self._calculate_correlation_risk(
            current_positions, correlation_matrix
        )

        currency_exposure = self._calculate_currency_exposure(current_positions)

        # 総リスクを計算
        total_risk = self._calculate_total_risk(
            individual_risks, correlation_risk, currency_exposure
        )

        # リスク警告を生成
        risk_alerts = self._generate_risk_alerts(
            total_risk, individual_risks, correlation_risk, currency_exposure
        )

        # リスク履歴を記録
        self._record_risk_calculation(
            total_risk, individual_risks, correlation_risk, currency_exposure
        )

        return {
            "total_risk": total_risk,
            "risk_percentage": (total_risk / account_balance) * 100,
            "risk_components": {
                "individual_risks": individual_risks,
                "correlation_risk": correlation_risk,
                "currency_exposure": currency_exposure,
            },
            "risk_alerts": risk_alerts,
            "is_within_limits": total_risk <= account_balance * self.max_portfolio_risk,
        }

    def _calculate_individual_risks(
        self, positions: List[Dict[str, Any]], account_balance: float
    ) -> Dict[str, Any]:
        """
        個別ポジションリスクを計算

        Args:
            positions: ポジションリスト
            account_balance: アカウント残高

        Returns:
            Dict[str, Any]: 個別リスク分析結果
        """
        individual_risks = {}
        total_individual_risk = 0.0

        for position in positions:
            currency_pair = position.get("currency_pair", "")
            risk_amount = position.get("risk_amount", 0.0)
            position_size = position.get("position_size", 0.0)

            risk_percentage = (
                (risk_amount / account_balance) * 100 if account_balance > 0 else 0
            )

            individual_risks[currency_pair] = {
                "risk_amount": risk_amount,
                "risk_percentage": risk_percentage,
                "position_size": position_size,
                "is_within_limit": risk_percentage
                <= self.max_single_position_risk * 100,
            }

            total_individual_risk += risk_amount

        return {
            "individual_risks": individual_risks,
            "total_individual_risk": total_individual_risk,
            "total_individual_risk_percentage": (
                (total_individual_risk / account_balance) * 100
                if account_balance > 0
                else 0
            ),
        }

    def _calculate_correlation_risk(
        self,
        positions: List[Dict[str, Any]],
        correlation_matrix: Optional[Dict[str, Dict[str, float]]],
    ) -> Dict[str, Any]:
        """
        相関リスクを計算

        Args:
            positions: ポジションリスト
            correlation_matrix: 相関性行列

        Returns:
            Dict[str, Any]: 相関リスク分析結果
        """
        if not correlation_matrix or len(positions) < 2:
            return {
                "correlation_risk": 0.0,
                "high_correlation_pairs": [],
                "risk_contribution": 0.0,
            }

        correlation_risk = 0.0
        high_correlation_pairs = []

        # 各ポジションペアの相関リスクを計算
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions):
                if i >= j:  # 重複を避ける
                    continue

                pair1 = pos1.get("currency_pair", "")
                pair2 = pos2.get("currency_pair", "")
                risk1 = pos1.get("risk_amount", 0.0)
                risk2 = pos2.get("risk_amount", 0.0)

                # 相関係数を取得
                correlation = self._get_correlation_value(
                    pair1, pair2, correlation_matrix
                )

                # 相関リスクを計算
                pair_correlation_risk = risk1 * risk2 * abs(correlation)
                correlation_risk += pair_correlation_risk

                # 高相関ペアを記録
                if abs(correlation) >= 0.8:
                    high_correlation_pairs.append(
                        {
                            "pair1": pair1,
                            "pair2": pair2,
                            "correlation": correlation,
                            "combined_risk": risk1 + risk2,
                        }
                    )

        return {
            "correlation_risk": correlation_risk,
            "high_correlation_pairs": high_correlation_pairs,
            "risk_contribution": correlation_risk,
        }

    def _calculate_currency_exposure(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        通貨エクスポージャーを計算

        Args:
            positions: ポジションリスト

        Returns:
            Dict[str, Any]: 通貨エクスポージャー分析結果
        """
        currency_exposures = {}
        total_exposure = 0.0

        for position in positions:
            currency_pair = position.get("currency_pair", "")
            position_size = position.get("position_size", 0.0)

            # 通貨ペアから基本通貨を抽出
            base_currency = (
                currency_pair.split("/")[0] if "/" in currency_pair else currency_pair
            )

            if base_currency not in currency_exposures:
                currency_exposures[base_currency] = 0.0

            currency_exposures[base_currency] += position_size
            total_exposure += position_size

        # エクスポージャー比率を計算
        exposure_ratios = {}
        for currency, exposure in currency_exposures.items():
            ratio = (exposure / total_exposure) * 100 if total_exposure > 0 else 0
            exposure_ratios[currency] = {
                "exposure": exposure,
                "ratio": ratio,
                "is_within_limit": ratio <= self.max_currency_exposure * 100,
            }

        return {
            "currency_exposures": exposure_ratios,
            "total_exposure": total_exposure,
            "max_exposure_currency": (
                max(exposure_ratios.items(), key=lambda x: x[1]["exposure"])[0]
                if exposure_ratios
                else None
            ),
        }

    def _calculate_total_risk(
        self,
        individual_risks: Dict[str, Any],
        correlation_risk: Dict[str, Any],
        currency_exposure: Dict[str, Any],
    ) -> float:
        """
        総リスクを計算

        Args:
            individual_risks: 個別リスク
            correlation_risk: 相関リスク
            currency_exposure: 通貨エクスポージャー

        Returns:
            float: 総リスク額
        """
        # 個別リスクの合計
        total_individual = individual_risks.get("total_individual_risk", 0.0)

        # 相関リスク
        correlation_risk_amount = correlation_risk.get("correlation_risk", 0.0)

        # 通貨エクスポージャーリスク（簡易計算）
        currency_risk = (
            currency_exposure.get("total_exposure", 0.0) * 0.1
        )  # 10%のリスク係数

        # 総リスク = 個別リスク + 相関リスク + 通貨リスク
        total_risk = total_individual + correlation_risk_amount + currency_risk

        return total_risk

    def _generate_risk_alerts(
        self,
        total_risk: float,
        individual_risks: Dict[str, Any],
        correlation_risk: Dict[str, Any],
        currency_exposure: Dict[str, Any],
    ) -> List[RiskAlertModel]:
        """
        リスク警告を生成

        Args:
            total_risk: 総リスク
            individual_risks: 個別リスク
            correlation_risk: 相関リスク
            currency_exposure: 通貨エクスポージャー

        Returns:
            List[RiskAlertModel]: リスク警告リスト
        """
        alerts = []

        # 総リスク警告
        if total_risk > 0:  # 実際の実装では適切な閾値を使用
            alert = RiskAlertModel.create_portfolio_risk_alert(
                currency_pair="PORTFOLIO",
                timestamp=datetime.utcnow(),
                timeframe="PORTFOLIO",
                total_risk=total_risk,
                alert_type="portfolio_risk",
                severity="MEDIUM",
                message=f"ポートフォリオリスク: {total_risk:.2f}",
                recommended_action="ポジションサイズの見直しを検討してください",
            )
            alerts.append(alert)

        # 個別ポジションリスク警告
        for currency_pair, risk_info in individual_risks.get(
            "individual_risks", {}
        ).items():
            if not risk_info.get("is_within_limit", True):
                alert = RiskAlertModel.create_portfolio_risk_alert(
                    currency_pair=currency_pair,
                    timestamp=datetime.utcnow(),
                    timeframe="PORTFOLIO",
                    total_risk=risk_info["risk_amount"],
                    alert_type="position_risk",
                    severity="HIGH",
                    message=f"高リスクポジション: {currency_pair} ({risk_info['risk_percentage']:.1f}%)",
                    recommended_action="ポジションサイズを削減してください",
                )
                alerts.append(alert)

        # 相関リスク警告
        high_correlation_pairs = correlation_risk.get("high_correlation_pairs", [])
        if len(high_correlation_pairs) >= 2:
            alert = RiskAlertModel.create_portfolio_risk_alert(
                currency_pair="CORRELATION",
                timestamp=datetime.utcnow(),
                timeframe="PORTFOLIO",
                total_risk=correlation_risk.get("correlation_risk", 0.0),
                alert_type="correlation_risk",
                severity="MEDIUM",
                message=f"高相関ポジション: {len(high_correlation_pairs)}ペア",
                recommended_action="ポジションの分散化を検討してください",
            )
            alerts.append(alert)

        return alerts

    def _get_correlation_value(
        self,
        pair1: str,
        pair2: str,
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> float:
        """
        相関値を取得

        Args:
            pair1: 通貨ペア1
            pair2: 通貨ペア2
            correlation_matrix: 相関性行列

        Returns:
            float: 相関値
        """
        try:
            if pair1 in correlation_matrix and pair2 in correlation_matrix[pair1]:
                return correlation_matrix[pair1][pair2]
            elif pair2 in correlation_matrix and pair1 in correlation_matrix[pair2]:
                return correlation_matrix[pair2][pair1]
            else:
                return 0.0
        except Exception as e:
            print(f"Error getting correlation value: {e}")
            return 0.0

    def _record_risk_calculation(
        self,
        total_risk: float,
        individual_risks: Dict[str, Any],
        correlation_risk: Dict[str, Any],
        currency_exposure: Dict[str, Any],
    ) -> None:
        """
        リスク計算結果を記録

        Args:
            total_risk: 総リスク
            individual_risks: 個別リスク
            correlation_risk: 相関リスク
            currency_exposure: 通貨エクスポージャー
        """
        record = {
            "timestamp": datetime.utcnow(),
            "total_risk": total_risk,
            "individual_risks": individual_risks,
            "correlation_risk": correlation_risk,
            "currency_exposure": currency_exposure,
            "settings": {
                "max_portfolio_risk": self.max_portfolio_risk,
                "max_single_position_risk": self.max_single_position_risk,
                "max_correlation_risk": self.max_correlation_risk,
                "max_currency_exposure": self.max_currency_exposure,
            },
        }

        self.risk_history.append(record)

        # 履歴を100件まで保持
        if len(self.risk_history) > 100:
            self.risk_history = self.risk_history[-100:]

    def get_risk_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        リスク統計を取得

        Args:
            days: 取得日数

        Returns:
            Dict[str, Any]: リスク統計
        """
        if not self.risk_history:
            return {
                "total_records": 0,
                "avg_total_risk": 0.0,
                "max_total_risk": 0.0,
                "risk_trend": "stable",
            }

        # 指定日数以内のレコードを取得
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_records = [
            record for record in self.risk_history if record["timestamp"] >= cutoff_date
        ]

        if not recent_records:
            return {
                "total_records": 0,
                "avg_total_risk": 0.0,
                "max_total_risk": 0.0,
                "risk_trend": "stable",
            }

        # 統計を計算
        total_risks = [record["total_risk"] for record in recent_records]
        avg_total_risk = sum(total_risks) / len(total_risks)
        max_total_risk = max(total_risks)

        # リスクトレンドを分析
        if len(total_risks) >= 2:
            first_half = sum(total_risks[: len(total_risks) // 2]) / (
                len(total_risks) // 2
            )
            second_half = sum(total_risks[len(total_risks) // 2 :]) / (
                len(total_risks) // 2
            )

            if second_half > first_half * 1.1:
                risk_trend = "increasing"
            elif second_half < first_half * 0.9:
                risk_trend = "decreasing"
            else:
                risk_trend = "stable"
        else:
            risk_trend = "stable"

        return {
            "total_records": len(recent_records),
            "avg_total_risk": avg_total_risk,
            "max_total_risk": max_total_risk,
            "risk_trend": risk_trend,
            "recent_risks": total_risks[-5:],  # 最新5件
        }

    def update_risk_settings(
        self,
        max_portfolio_risk: float = None,
        max_single_position_risk: float = None,
        max_correlation_risk: float = None,
        max_currency_exposure: float = None,
    ) -> None:
        """
        リスク設定を更新

        Args:
            max_portfolio_risk: 最大ポートフォリオリスク
            max_single_position_risk: 最大単一ポジションリスク
            max_correlation_risk: 最大相関リスク
            max_currency_exposure: 最大通貨エクスポージャー
        """
        if max_portfolio_risk is not None:
            self.max_portfolio_risk = max(0.0, min(1.0, max_portfolio_risk))

        if max_single_position_risk is not None:
            self.max_single_position_risk = max(0.0, min(1.0, max_single_position_risk))

        if max_correlation_risk is not None:
            self.max_correlation_risk = max(0.0, min(1.0, max_correlation_risk))

        if max_currency_exposure is not None:
            self.max_currency_exposure = max(0.0, min(1.0, max_currency_exposure))

    def get_risk_settings(self) -> Dict[str, Any]:
        """
        現在のリスク設定を取得

        Returns:
            Dict[str, Any]: リスク設定
        """
        return {
            "max_portfolio_risk": self.max_portfolio_risk,
            "max_single_position_risk": self.max_single_position_risk,
            "max_correlation_risk": self.max_correlation_risk,
            "max_currency_exposure": self.max_currency_exposure,
        }

    def clear_risk_history(self) -> None:
        """
        リスク履歴をクリア
        """
        self.risk_history = []

    def export_risk_history(self) -> List[Dict[str, Any]]:
        """
        リスク履歴をエクスポート

        Returns:
            List[Dict[str, Any]]: リスク履歴
        """
        return self.risk_history.copy()
