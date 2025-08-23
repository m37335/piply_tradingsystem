"""
ポジションサイズ計算器

プロトレーダー向け為替アラートシステム用のポジションサイズ計算器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)


class PositionSizeCalculator:
    """
    ポジションサイズ計算器

    責任:
    - アカウント残高に基づくリスク計算
    - ボラティリティに応じたサイズ調整
    - 最大リスク制限の適用
    - 推奨ポジションサイズの提示

    特徴:
    - 動的リスク計算
    - ボラティリティ調整
    - 複数通貨ペア対応
    - リスクシミュレーション
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"

        # デフォルト設定
        self.default_risk_per_trade = 0.02  # 2% per trade
        self.max_risk_per_trade = 0.05  # 5% max per trade
        self.max_portfolio_risk = 0.20  # 20% max portfolio risk
        self.min_position_size = 0.01  # 1% min position size

    async def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        confidence_score: int,
        volatility_level: str = "normal",
        current_positions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        ポジションサイズ計算

        Args:
            account_balance: アカウント残高
            entry_price: エントリー価格
            stop_loss: ストップロス価格
            confidence_score: 信頼度スコア（0-100）
            volatility_level: ボラティリティレベル
            current_positions: 現在のポジションリスト

        Returns:
            Dict[str, Any]: ポジションサイズ計算結果
        """
        try:
            # リスク額を計算
            risk_amount = self._calculate_risk_amount(account_balance, confidence_score)

            # 価格リスクを計算
            price_risk = self._calculate_price_risk(entry_price, stop_loss)

            # 基本ポジションサイズを計算
            base_position_size = risk_amount / price_risk if price_risk > 0 else 0

            # ボラティリティ調整を適用
            volatility_adjustment = self._calculate_volatility_adjustment(
                volatility_level
            )
            adjusted_position_size = base_position_size * volatility_adjustment

            # 最大リスク制限を適用
            max_position_size = self._calculate_max_position_size(
                account_balance, price_risk
            )
            final_position_size = min(adjusted_position_size, max_position_size)

            # 最小ポジションサイズ制限を適用
            min_position_size = self._calculate_min_position_size(account_balance)
            if final_position_size < min_position_size:
                final_position_size = 0  # 最小サイズ未満の場合は取引しない

            # ポートフォリオリスクチェック
            portfolio_risk_check = self._check_portfolio_risk(
                final_position_size, price_risk, current_positions, account_balance
            )

            # 推奨アクションを決定
            recommended_action = self._determine_recommended_action(
                final_position_size, portfolio_risk_check, confidence_score
            )

            return {
                "account_balance": account_balance,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "risk_amount": risk_amount,
                "price_risk": price_risk,
                "base_position_size": base_position_size,
                "volatility_adjustment": volatility_adjustment,
                "adjusted_position_size": adjusted_position_size,
                "max_position_size": max_position_size,
                "final_position_size": final_position_size,
                "position_size_percentage": (
                    (final_position_size / account_balance) * 100
                    if account_balance > 0
                    else 0
                ),
                "portfolio_risk_check": portfolio_risk_check,
                "recommended_action": recommended_action,
                "confidence_score": confidence_score,
                "volatility_level": volatility_level,
                "timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return {}

    def _calculate_risk_amount(
        self, account_balance: float, confidence_score: int
    ) -> float:
        """
        リスク額を計算

        Args:
            account_balance: アカウント残高
            confidence_score: 信頼度スコア

        Returns:
            float: リスク額
        """
        # 信頼度に基づくリスク調整
        if confidence_score >= 80:
            risk_multiplier = 1.0  # 高信頼度
        elif confidence_score >= 60:
            risk_multiplier = 0.8  # 中信頼度
        else:
            risk_multiplier = 0.5  # 低信頼度

        # 基本リスク額
        base_risk_amount = account_balance * self.default_risk_per_trade

        # 信頼度調整後のリスク額
        adjusted_risk_amount = base_risk_amount * risk_multiplier

        # 最大リスク制限を適用
        max_risk_amount = account_balance * self.max_risk_per_trade

        return min(adjusted_risk_amount, max_risk_amount)

    def _calculate_price_risk(self, entry_price: float, stop_loss: float) -> float:
        """
        価格リスクを計算

        Args:
            entry_price: エントリー価格
            stop_loss: ストップロス価格

        Returns:
            float: 価格リスク（1ロットあたりの損失額）
        """
        # USD/JPYの場合、1ロット = 100,000通貨
        lot_size = 100000

        # 価格差を計算
        price_difference = abs(entry_price - stop_loss)

        # 1ロットあたりの損失額を計算
        risk_per_lot = price_difference * lot_size

        return risk_per_lot

    def _calculate_volatility_adjustment(self, volatility_level: str) -> float:
        """
        ボラティリティ調整を計算

        Args:
            volatility_level: ボラティリティレベル

        Returns:
            float: 調整係数
        """
        adjustment_map = {
            "low": 1.2,  # 低ボラティリティ時はサイズを増やす
            "normal": 1.0,  # 通常時は調整なし
            "high": 0.7,  # 高ボラティリティ時はサイズを減らす
            "extreme": 0.5,  # 極端なボラティリティ時は大幅に減らす
        }

        return adjustment_map.get(volatility_level, 1.0)

    def _calculate_max_position_size(
        self, account_balance: float, price_risk: float
    ) -> float:
        """
        最大ポジションサイズを計算

        Args:
            account_balance: アカウント残高
            price_risk: 価格リスク

        Returns:
            float: 最大ポジションサイズ
        """
        if price_risk <= 0:
            return 0

        # 最大リスク額
        max_risk_amount = account_balance * self.max_risk_per_trade

        # 最大ポジションサイズ
        max_position_size = max_risk_amount / price_risk

        return max_position_size

    def _calculate_min_position_size(self, account_balance: float) -> float:
        """
        最小ポジションサイズを計算

        Args:
            account_balance: アカウント残高

        Returns:
            float: 最小ポジションサイズ
        """
        return account_balance * self.min_position_size

    def _check_portfolio_risk(
        self,
        position_size: float,
        price_risk: float,
        current_positions: List[Dict[str, Any]],
        account_balance: float,
    ) -> Dict[str, Any]:
        """
        ポートフォリオリスクチェック

        Args:
            position_size: ポジションサイズ
            price_risk: 価格リスク
            current_positions: 現在のポジションリスト
            account_balance: アカウント残高

        Returns:
            Dict[str, Any]: ポートフォリオリスクチェック結果
        """
        if not current_positions:
            current_positions = []

        # 現在のポジションの総リスクを計算
        current_risk = sum(pos.get("risk_amount", 0) for pos in current_positions)

        # 新規ポジションのリスク
        new_position_risk = position_size * price_risk

        # 総リスク
        total_risk = current_risk + new_position_risk

        # ポートフォリオリスク率
        portfolio_risk_ratio = (
            total_risk / account_balance if account_balance > 0 else 0
        )

        # リスク制限チェック
        is_within_limit = portfolio_risk_ratio <= self.max_portfolio_risk

        return {
            "current_risk": current_risk,
            "new_position_risk": new_position_risk,
            "total_risk": total_risk,
            "portfolio_risk_ratio": portfolio_risk_ratio,
            "max_portfolio_risk": self.max_portfolio_risk,
            "is_within_limit": is_within_limit,
            "risk_margin": self.max_portfolio_risk - portfolio_risk_ratio,
        }

    def _determine_recommended_action(
        self,
        position_size: float,
        portfolio_risk_check: Dict[str, Any],
        confidence_score: int,
    ) -> str:
        """
        推奨アクションを決定

        Args:
            position_size: ポジションサイズ
            portfolio_risk_check: ポートフォリオリスクチェック結果
            confidence_score: 信頼度スコア

        Returns:
            str: 推奨アクション
        """
        if position_size <= 0:
            return "取引しない（最小サイズ未満）"

        if not portfolio_risk_check.get("is_within_limit", True):
            return "取引しない（ポートフォリオリスク制限超過）"

        if confidence_score >= 80:
            return "即座にエントリー推奨"
        elif confidence_score >= 60:
            return "確認後にエントリー"
        else:
            return "様子見推奨"

    async def calculate_optimal_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence_score: int,
        volatility_level: str = "normal",
    ) -> Dict[str, Any]:
        """
        最適ポジションサイズ計算（リスク/リワード比考慮）

        Args:
            account_balance: アカウント残高
            entry_price: エントリー価格
            stop_loss: ストップロス価格
            take_profit: 利益確定価格
            confidence_score: 信頼度スコア
            volatility_level: ボラティリティレベル

        Returns:
            Dict[str, Any]: 最適ポジションサイズ計算結果
        """
        try:
            # 基本ポジションサイズを計算
            base_calculation = await self.calculate_position_size(
                account_balance,
                entry_price,
                stop_loss,
                confidence_score,
                volatility_level,
            )

            if not base_calculation:
                return {}

            # リスク/リワード比を計算
            risk_reward_ratio = self._calculate_risk_reward_ratio(
                entry_price, stop_loss, take_profit
            )

            # リスク/リワード比に基づく調整
            rr_adjustment = self._calculate_rr_adjustment(risk_reward_ratio)

            # 調整後のポジションサイズ
            adjusted_size = base_calculation["final_position_size"] * rr_adjustment

            # 結果を更新
            base_calculation.update(
                {
                    "take_profit": take_profit,
                    "risk_reward_ratio": risk_reward_ratio,
                    "rr_adjustment": rr_adjustment,
                    "optimal_position_size": adjusted_size,
                    "optimal_position_size_percentage": (
                        (adjusted_size / account_balance) * 100
                        if account_balance > 0
                        else 0
                    ),
                }
            )

            return base_calculation

        except Exception as e:
            print(f"Error calculating optimal position size: {e}")
            return {}

    def _calculate_risk_reward_ratio(
        self, entry_price: float, stop_loss: float, take_profit: float
    ) -> float:
        """
        リスク/リワード比を計算

        Args:
            entry_price: エントリー価格
            stop_loss: ストップロス価格
            take_profit: 利益確定価格

        Returns:
            float: リスク/リワード比
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)

        if risk <= 0:
            return 0

        return reward / risk

    def _calculate_rr_adjustment(self, risk_reward_ratio: float) -> float:
        """
        リスク/リワード比に基づく調整係数を計算

        Args:
            risk_reward_ratio: リスク/リワード比

        Returns:
            float: 調整係数
        """
        if risk_reward_ratio >= 3.0:
            return 1.2  # 高リスク/リワード比
        elif risk_reward_ratio >= 2.0:
            return 1.1  # 良好なリスク/リワード比
        elif risk_reward_ratio >= 1.5:
            return 1.0  # 標準的なリスク/リワード比
        elif risk_reward_ratio >= 1.0:
            return 0.8  # 低リスク/リワード比
        else:
            return 0.5  # 非常に低いリスク/リワード比

    async def simulate_position_scenarios(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence_score: int,
    ) -> List[Dict[str, Any]]:
        """
        ポジションシナリオシミュレーション

        Args:
            account_balance: アカウント残高
            entry_price: エントリー価格
            stop_loss: ストップロス価格
            take_profit: 利益確定価格
            confidence_score: 信頼度スコア

        Returns:
            List[Dict[str, Any]]: シミュレーション結果
        """
        scenarios = []

        # 異なるボラティリティレベルでのシミュレーション
        volatility_levels = ["low", "normal", "high", "extreme"]

        for volatility in volatility_levels:
            scenario = await self.calculate_optimal_position_size(
                account_balance,
                entry_price,
                stop_loss,
                take_profit,
                confidence_score,
                volatility,
            )

            if scenario:
                scenarios.append(
                    {
                        "volatility_level": volatility,
                        "position_size": scenario.get("optimal_position_size", 0),
                        "position_size_percentage": scenario.get(
                            "optimal_position_size_percentage", 0
                        ),
                        "risk_amount": scenario.get("risk_amount", 0),
                        "risk_reward_ratio": scenario.get("risk_reward_ratio", 0),
                        "recommended_action": scenario.get("recommended_action", ""),
                    }
                )

        return scenarios

    def update_risk_settings(
        self,
        risk_per_trade: float = None,
        max_risk_per_trade: float = None,
        max_portfolio_risk: float = None,
        min_position_size: float = None,
    ) -> None:
        """
        リスク設定を更新

        Args:
            risk_per_trade: 取引あたりのリスク率
            max_risk_per_trade: 取引あたりの最大リスク率
            max_portfolio_risk: ポートフォリオ最大リスク率
            min_position_size: 最小ポジションサイズ率
        """
        if risk_per_trade is not None:
            self.default_risk_per_trade = risk_per_trade

        if max_risk_per_trade is not None:
            self.max_risk_per_trade = max_risk_per_trade

        if max_portfolio_risk is not None:
            self.max_portfolio_risk = max_portfolio_risk

        if min_position_size is not None:
            self.min_position_size = min_position_size

    def get_risk_settings(self) -> Dict[str, float]:
        """
        現在のリスク設定を取得

        Returns:
            Dict[str, float]: リスク設定
        """
        return {
            "default_risk_per_trade": self.default_risk_per_trade,
            "max_risk_per_trade": self.max_risk_per_trade,
            "max_portfolio_risk": self.max_portfolio_risk,
            "min_position_size": self.min_position_size,
        }
