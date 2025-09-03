"""
動的ストップロス調整器

プロトレーダー向け為替アラートシステム用の動的ストップロス調整器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)


class DynamicStopLossAdjuster:
    """
    動的ストップロス調整器

    責任:
    - ATRに基づくストップロス幅計算
    - サポート/レジスタンスレベル考慮
    - ボラティリティ変化に応じた調整
    - 調整履歴記録

    特徴:
    - 動的幅調整
    - レベルベース調整
    - ボラティリティ対応
    - 履歴追跡
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
        self.atr_multiplier = 2.0  # ATRの2倍
        self.min_stop_distance = 0.001  # 最小0.1%
        self.max_stop_distance = 0.05  # 最大5%
        self.adjustment_threshold = 0.02  # 2%以上の価格変動で調整

    async def calculate_dynamic_stop_loss(
        self,
        entry_price: float,
        signal_type: str,
        timeframe: str = "H1",
        volatility_level: str = "normal",
    ) -> Dict[str, Any]:
        """
        動的ストップロス計算

        Args:
            entry_price: エントリー価格
            signal_type: シグナルタイプ（"BUY" or "SELL"）
            timeframe: タイムフレーム
            volatility_level: ボラティリティレベル

        Returns:
            Dict[str, Any]: 動的ストップロス計算結果
        """
        try:
            # ATRベースの基本ストップロス幅を計算
            atr_based_stop = await self._calculate_atr_based_stop(
                entry_price, signal_type, timeframe
            )

            # サポート/レジスタンスレベルを考慮
            level_based_stop = await self._calculate_level_based_stop(
                entry_price, signal_type, timeframe
            )

            # ボラティリティ調整を適用
            volatility_adjustment = self._calculate_volatility_adjustment(
                volatility_level
            )

            # 最終ストップロスを決定
            final_stop_loss = self._determine_final_stop_loss(
                atr_based_stop, level_based_stop, volatility_adjustment, signal_type
            )

            # 調整履歴を作成
            adjustment_history = self._create_adjustment_history(
                entry_price, atr_based_stop, level_based_stop, final_stop_loss
            )

            return {
                "entry_price": entry_price,
                "signal_type": signal_type,
                "timeframe": timeframe,
                "atr_based_stop": atr_based_stop,
                "level_based_stop": level_based_stop,
                "volatility_adjustment": volatility_adjustment,
                "final_stop_loss": final_stop_loss,
                "stop_distance": abs(entry_price - final_stop_loss),
                "stop_distance_percentage": abs(entry_price - final_stop_loss)
                / entry_price
                * 100,
                "adjustment_history": adjustment_history,
                "timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error calculating dynamic stop loss: {e}")
            return {}

    async def _calculate_atr_based_stop(
        self, entry_price: float, signal_type: str, timeframe: str
    ) -> Dict[str, Any]:
        """
        ATRベースのストップロス計算

        Args:
            entry_price: エントリー価格
            signal_type: シグナルタイプ
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: ATRベースストップロス結果
        """
        try:
            # ATRデータを取得
            atr_data = await self._get_atr_data(timeframe, periods=10)

            if not atr_data:
                return {"stop_price": 0, "atr_value": 0, "method": "default"}

            current_atr = atr_data[-1]

            # ATRベースのストップロス幅を計算
            stop_distance = current_atr * self.atr_multiplier

            # 最小・最大制限を適用
            stop_distance = max(stop_distance, entry_price * self.min_stop_distance)
            stop_distance = min(stop_distance, entry_price * self.max_stop_distance)

            # シグナルタイプに応じてストップロス価格を計算
            if signal_type == "BUY":
                stop_price = entry_price - stop_distance
            else:  # SELL
                stop_price = entry_price + stop_distance

            return {
                "stop_price": stop_price,
                "atr_value": current_atr,
                "stop_distance": stop_distance,
                "method": "atr_based",
            }

        except Exception as e:
            print(f"Error calculating ATR-based stop: {e}")
            return {"stop_price": 0, "atr_value": 0, "method": "default"}

    async def _calculate_level_based_stop(
        self, entry_price: float, signal_type: str, timeframe: str
    ) -> Dict[str, Any]:
        """
        サポート/レジスタンスレベルベースのストップロス計算

        Args:
            entry_price: エントリー価格
            signal_type: シグナルタイプ
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: レベルベースストップロス結果
        """
        try:
            # サポート/レジスタンスレベルを取得
            support_resistance = await self._get_support_resistance_levels(timeframe)

            if not support_resistance:
                return {"stop_price": 0, "method": "default"}

            # エントリー価格に最も近いレベルを見つける
            nearest_level = self._find_nearest_level(
                entry_price, support_resistance, signal_type
            )

            if nearest_level:
                # レベルに小さなマージンを追加
                margin = entry_price * 0.001  # 0.1%マージン

                if signal_type == "BUY":
                    stop_price = nearest_level - margin
                else:  # SELL
                    stop_price = nearest_level + margin

                return {
                    "stop_price": stop_price,
                    "level_price": nearest_level,
                    "method": "level_based",
                }

            return {"stop_price": 0, "method": "default"}

        except Exception as e:
            print(f"Error calculating level-based stop: {e}")
            return {"stop_price": 0, "method": "default"}

    def _calculate_volatility_adjustment(self, volatility_level: str) -> float:
        """
        ボラティリティ調整係数を計算

        Args:
            volatility_level: ボラティリティレベル

        Returns:
            float: 調整係数
        """
        adjustment_map = {
            "low": 0.8,  # 低ボラティリティ時は狭める
            "normal": 1.0,  # 通常時は調整なし
            "high": 1.3,  # 高ボラティリティ時は広げる
            "extreme": 1.5,  # 極端なボラティリティ時は大幅に広げる
        }

        return adjustment_map.get(volatility_level, 1.0)

    def _determine_final_stop_loss(
        self,
        atr_based_stop: Dict[str, Any],
        level_based_stop: Dict[str, Any],
        volatility_adjustment: float,
        signal_type: str,
    ) -> float:
        """
        最終ストップロスを決定

        Args:
            atr_based_stop: ATRベースストップロス
            level_based_stop: レベルベースストップロス
            volatility_adjustment: ボラティリティ調整係数
            signal_type: シグナルタイプ

        Returns:
            float: 最終ストップロス価格
        """
        # レベルベースのストップロスが利用可能な場合を優先
        if level_based_stop.get("stop_price", 0) > 0:
            base_stop = level_based_stop["stop_price"]
        else:
            base_stop = atr_based_stop.get("stop_price", 0)

        if base_stop <= 0:
            # デフォルトストップロス
            default_distance = 0.005  # 0.5%
            if signal_type == "BUY":
                return 150.000 * (1 - default_distance)  # 仮の価格
            else:
                return 150.000 * (1 + default_distance)  # 仮の価格

        # ボラティリティ調整を適用
        if signal_type == "BUY":
            # 買いの場合、ストップロスを下に調整
            adjusted_stop = base_stop - (
                abs(base_stop - 150.000) * (volatility_adjustment - 1)
            )
        else:
            # 売りの場合、ストップロスを上に調整
            adjusted_stop = base_stop + (
                abs(base_stop - 150.000) * (volatility_adjustment - 1)
            )

        return adjusted_stop

    def _create_adjustment_history(
        self,
        entry_price: float,
        atr_based_stop: Dict[str, Any],
        level_based_stop: Dict[str, Any],
        final_stop_loss: float,
    ) -> List[Dict[str, Any]]:
        """
        調整履歴を作成

        Args:
            entry_price: エントリー価格
            atr_based_stop: ATRベースストップロス
            level_based_stop: レベルベースストップロス
            final_stop_loss: 最終ストップロス

        Returns:
            List[Dict[str, Any]]: 調整履歴
        """
        history = []

        # ATRベース調整
        if atr_based_stop.get("stop_price", 0) > 0:
            history.append(
                {
                    "method": "ATR-based",
                    "stop_price": atr_based_stop["stop_price"],
                    "distance": abs(entry_price - atr_based_stop["stop_price"]),
                    "atr_value": atr_based_stop.get("atr_value", 0),
                    "timestamp": datetime.utcnow(),
                }
            )

        # レベルベース調整
        if level_based_stop.get("stop_price", 0) > 0:
            history.append(
                {
                    "method": "Level-based",
                    "stop_price": level_based_stop["stop_price"],
                    "distance": abs(entry_price - level_based_stop["stop_price"]),
                    "level_price": level_based_stop.get("level_price", 0),
                    "timestamp": datetime.utcnow(),
                }
            )

        # 最終調整
        history.append(
            {
                "method": "Final",
                "stop_price": final_stop_loss,
                "distance": abs(entry_price - final_stop_loss),
                "timestamp": datetime.utcnow(),
            }
        )

        return history

    async def _get_atr_data(self, timeframe: str, periods: int) -> List[float]:
        """
        ATRデータを取得

        Args:
            timeframe: タイムフレーム
            periods: 取得期間数

        Returns:
            List[float]: ATRデータ
        """
        try:
            query = (
                select(TechnicalIndicatorModel.value)
                .where(
                    TechnicalIndicatorModel.currency_pair == self.currency_pair,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.indicator_type == "ATR",
                )
                .order_by(TechnicalIndicatorModel.timestamp.desc())
                .limit(periods)
            )

            result = await self.db_session.execute(query)
            atr_values = [float(value) for value in result.scalars().all()]

            return atr_values[::-1]  # 時系列順に並び替え

        except Exception as e:
            print(f"Error getting ATR data: {e}")
            return []

    async def _get_support_resistance_levels(self, timeframe: str) -> List[float]:
        """
        サポート/レジスタンスレベルを取得

        Args:
            timeframe: タイムフレーム

        Returns:
            List[float]: サポート/レジスタンスレベル
        """
        try:
            # 過去の価格データからレベルを計算（簡易実装）
            # 実際の実装ではピボットポイントやフィボナッチレベルを使用

            # 仮のレベル（実際の実装では動的に計算）
            levels = [
                149.500,  # サポート1
                149.800,  # サポート2
                150.200,  # レジスタンス1
                150.500,  # レジスタンス2
            ]

            return levels

        except Exception as e:
            print(f"Error getting support/resistance levels: {e}")
            return []

    def _find_nearest_level(
        self, entry_price: float, levels: List[float], signal_type: str
    ) -> Optional[float]:
        """
        エントリー価格に最も近いレベルを見つける

        Args:
            entry_price: エントリー価格
            levels: レベルリスト
            signal_type: シグナルタイプ

        Returns:
            Optional[float]: 最も近いレベル
        """
        if not levels:
            return None

        # シグナルタイプに応じて適切なレベルを選択
        if signal_type == "BUY":
            # 買いの場合、エントリー価格より下のレベル（サポート）
            valid_levels = [level for level in levels if level < entry_price]
        else:  # SELL
            # 売りの場合、エントリー価格より上のレベル（レジスタンス）
            valid_levels = [level for level in levels if level > entry_price]

        if not valid_levels:
            return None

        # 最も近いレベルを見つける
        nearest_level = min(valid_levels, key=lambda x: abs(x - entry_price))

        return nearest_level

    async def adjust_existing_stop_loss(
        self,
        current_stop_loss: float,
        current_price: float,
        signal_type: str,
        timeframe: str = "H1",
    ) -> Dict[str, Any]:
        """
        既存のストップロスを調整

        Args:
            current_stop_loss: 現在のストップロス
            current_price: 現在価格
            signal_type: シグナルタイプ
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: 調整結果
        """
        try:
            # 価格変動を計算
            price_change = abs(current_price - current_stop_loss) / current_stop_loss

            # 調整が必要かチェック
            if price_change < self.adjustment_threshold:
                return {
                    "should_adjust": False,
                    "reason": "価格変動が調整閾値を下回っています",
                    "current_stop_loss": current_stop_loss,
                    "price_change": price_change,
                }

            # 新しいストップロスを計算
            new_stop_calculation = await self.calculate_dynamic_stop_loss(
                current_price, signal_type, timeframe
            )

            if not new_stop_calculation:
                return {
                    "should_adjust": False,
                    "reason": "新しいストップロス計算に失敗しました",
                    "current_stop_loss": current_stop_loss,
                }

            new_stop_loss = new_stop_calculation["final_stop_loss"]

            # 調整方向を判定
            if signal_type == "BUY":
                should_adjust = (
                    new_stop_loss > current_stop_loss
                )  # 買いの場合、上に調整
            else:
                should_adjust = (
                    new_stop_loss < current_stop_loss
                )  # 売りの場合、下に調整

            return {
                "should_adjust": should_adjust,
                "current_stop_loss": current_stop_loss,
                "new_stop_loss": new_stop_loss,
                "adjustment_amount": abs(new_stop_loss - current_stop_loss),
                "price_change": price_change,
                "reason": (
                    "ボラティリティ変化による調整" if should_adjust else "調整不要"
                ),
                "calculation_details": new_stop_calculation,
            }

        except Exception as e:
            print(f"Error adjusting existing stop loss: {e}")
            return {
                "should_adjust": False,
                "reason": f"調整処理でエラーが発生しました: {e}",
                "current_stop_loss": current_stop_loss,
            }

    def update_settings(
        self,
        atr_multiplier: float = None,
        min_stop_distance: float = None,
        max_stop_distance: float = None,
        adjustment_threshold: float = None,
    ) -> None:
        """
        設定を更新

        Args:
            atr_multiplier: ATR倍率
            min_stop_distance: 最小ストップロス距離
            max_stop_distance: 最大ストップロス距離
            adjustment_threshold: 調整閾値
        """
        if atr_multiplier is not None:
            self.atr_multiplier = atr_multiplier

        if min_stop_distance is not None:
            self.min_stop_distance = min_stop_distance

        if max_stop_distance is not None:
            self.max_stop_distance = max_stop_distance

        if adjustment_threshold is not None:
            self.adjustment_threshold = adjustment_threshold

    def get_settings(self) -> Dict[str, float]:
        """
        現在の設定を取得

        Returns:
            Dict[str, float]: 設定
        """
        return {
            "atr_multiplier": self.atr_multiplier,
            "min_stop_distance": self.min_stop_distance,
            "max_stop_distance": self.max_stop_distance,
            "adjustment_threshold": self.adjustment_threshold,
        }
