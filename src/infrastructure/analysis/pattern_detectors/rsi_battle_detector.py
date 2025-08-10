"""
RSI50ライン攻防検出器

パターン5: RSI50ライン攻防の検出ロジック
"""

from typing import Any, Dict, Optional

from src.domain.entities.notification_pattern import NotificationPattern
from src.utils.pattern_utils import PatternUtils


class RSIBattleDetector:
    """RSI50ライン攻防検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_5()
        self.utils = PatternUtils()

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        RSI50ライン攻防を検出

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            検出結果の辞書、検出されない場合はNone
        """
        try:
            # 各時間軸の条件をチェック
            d1_condition = self._check_d1_condition(multi_timeframe_data.get("D1", {}))
            h4_condition = self._check_h4_condition(multi_timeframe_data.get("H4", {}))
            h1_condition = self._check_h1_condition(multi_timeframe_data.get("H1", {}))
            m5_condition = self._check_m5_condition(multi_timeframe_data.get("M5", {}))

            # 全ての条件が満たされているかチェック
            if all([d1_condition, h4_condition, h1_condition, m5_condition]):
                return self._create_detection_result(
                    multi_timeframe_data,
                    d1_condition,
                    h4_condition,
                    h1_condition,
                    m5_condition,
                )

            return None

        except Exception as e:
            print(f"RSI50ライン攻防検出エラー: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _check_d1_condition(self, d1_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        D1時間軸の条件をチェック
        RSI 45-55 かつ MACD ゼロライン付近
        """
        if d1_data is None:
            return None

        indicators = d1_data.get("indicators", {})
        rsi_data = indicators.get("rsi", {})
        macd_data = indicators.get("macd", {})

        if rsi_data is None or macd_data is None:
            return None

        current_rsi = rsi_data.get("current_value", 0)
        macd_series = macd_data.get("macd", [])
        signal_series = macd_data.get("signal", [])

        if (
            macd_series is None
            or signal_series is None
            or len(macd_series) == 0
            or len(signal_series) == 0
        ):
            return None

        current_macd = (
            macd_series.iloc[-1] if hasattr(macd_series, "iloc") else macd_series[-1]
        )
        current_signal = (
            signal_series.iloc[-1]
            if hasattr(signal_series, "iloc")
            else signal_series[-1]
        )

        # RSI 45-55の範囲内かチェック
        rsi_in_range = 45 <= current_rsi <= 55

        # MACDがゼロライン付近かチェック（±0.1の範囲）
        macd_near_zero = abs(current_macd) <= 0.1 and abs(current_signal) <= 0.1

        if rsi_in_range and macd_near_zero:
            return {
                "rsi_value": current_rsi,
                "macd_value": current_macd,
                "signal_value": current_signal,
                "condition_met": True,
            }

        return None

    def _check_h4_condition(self, h4_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        H4時間軸の条件をチェック
        RSI 45-55 かつ ボリンジャーバンド ミドル付近
        """
        if h4_data is None:
            return None

        indicators = h4_data.get("indicators", {})
        rsi_data = indicators.get("rsi", {})
        bb_data = indicators.get("bollinger_bands", {})

        if rsi_data is None or bb_data is None:
            return None

        current_rsi = rsi_data.get("current_value", 0)
        price_data = h4_data.get("price_data", {})
        close_prices = price_data.get("Close", [])

        if close_prices is None or len(close_prices) == 0:
            return None

        current_price = (
            close_prices.iloc[-1] if hasattr(close_prices, "iloc") else close_prices[-1]
        )
        bb_middle = bb_data.get("middle", [])

        if bb_middle is None or len(bb_middle) == 0:
            return None

        current_bb_middle = (
            bb_middle.iloc[-1] if hasattr(bb_middle, "iloc") else bb_middle[-1]
        )

        # RSI 45-55の範囲内かチェック
        rsi_in_range = 45 <= current_rsi <= 55

        # 価格がボリンジャーバンドミドル付近かチェック（±0.1%の範囲）
        price_near_middle = (
            abs(current_price - current_bb_middle) / current_bb_middle <= 0.001
        )

        if rsi_in_range and price_near_middle:
            return {
                "rsi_value": current_rsi,
                "current_price": current_price,
                "bb_middle": current_bb_middle,
                "condition_met": True,
            }

        return None

    def _check_h1_condition(self, h1_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        H1時間軸の条件をチェック
        RSI 45-55 かつ 価格変動増加
        """
        if h1_data is None:
            return None

        indicators = h1_data.get("indicators", {})
        rsi_data = indicators.get("rsi", {})
        price_data = h1_data.get("price_data", {})

        if rsi_data is None or price_data is None:
            return None

        current_rsi = rsi_data.get("current_value", 0)
        close_prices = price_data.get("Close", [])

        if close_prices is None or len(close_prices) < 20:
            return None

        # 価格変動性を計算（過去20期間の標準偏差）
        recent_prices = (
            close_prices[-20:] if hasattr(close_prices, "iloc") else close_prices[-20:]
        )
        price_volatility = self.utils.calculate_volatility(recent_prices)

        # RSI 45-55の範囲内かチェック
        rsi_in_range = 45 <= current_rsi <= 55

        # 価格変動が増加しているかチェック（過去の平均より高い）
        price_list = (
            recent_prices.tolist()
            if hasattr(recent_prices, "tolist")
            else list(recent_prices)
        )
        # 価格変化率の標準偏差を計算（calculate_volatilityと同じ尺度）
        price_changes = []
        for i in range(1, len(price_list)):
            if price_list[i - 1] > 0:
                change = (price_list[i] - price_list[i - 1]) / price_list[i - 1]
                price_changes.append(change)

        if len(price_changes) > 0:
            avg_change_std = sum(price_changes) / len(price_changes)
            volatility_increased = price_volatility > abs(avg_change_std) * 1.2
        else:
            volatility_increased = False

        if rsi_in_range and volatility_increased:
            return {
                "rsi_value": current_rsi,
                "volatility": price_volatility,
                "avg_volatility": (
                    abs(avg_change_std) if len(price_changes) > 0 else 0.0
                ),
                "condition_met": True,
            }

        return None

    def _check_m5_condition(self, m5_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        M5時間軸の条件をチェック
        RSI 50 ライン 攻防
        """
        if m5_data is None:
            return None

        indicators = m5_data.get("indicators", {})
        rsi_data = indicators.get("rsi", {})

        if rsi_data is None:
            return None

        current_rsi = rsi_data.get("current_value", 0)
        rsi_series = rsi_data.get("series", [])

        if rsi_series is None or len(rsi_series) < 10:
            return None

        # RSIが50ライン付近で攻防しているかチェック
        recent_rsi = (
            rsi_series[-10:] if hasattr(rsi_series, "iloc") else rsi_series[-10:]
        )

        # RSIが50の±5の範囲内で変動しているかチェック
        rsi_values = (
            recent_rsi.tolist() if hasattr(recent_rsi, "tolist") else list(recent_rsi)
        )
        rsi_near_50 = all(45 <= rsi <= 55 for rsi in rsi_values)

        # RSIが50を跨いでいるかチェック（攻防の証拠）
        first_half = rsi_values[:5]
        second_half = rsi_values[-5:]
        rsi_crosses_50 = any(rsi < 50 for rsi in first_half) and any(
            rsi > 50 for rsi in second_half
        )

        if rsi_near_50 and rsi_crosses_50:
            rsi_values_list = (
                rsi_values if isinstance(rsi_values, list) else list(rsi_values)
            )
            return {
                "rsi_value": current_rsi,
                "rsi_range": f"{min(rsi_values_list):.1f}-{max(rsi_values_list):.1f}",
                "condition_met": True,
            }

        return None

    def _create_detection_result(
        self,
        multi_timeframe_data: Dict[str, Any],
        d1_condition: Dict[str, Any],
        h4_condition: Dict[str, Any],
        h1_condition: Dict[str, Any],
        m5_condition: Dict[str, Any],
    ) -> Dict[str, Any]:
        """検出結果を作成"""
        from datetime import datetime

        current_time = datetime.now().isoformat()

        # 信頼度スコアを計算
        confidence_score = self._calculate_confidence_score(
            d1_condition, h4_condition, h1_condition, m5_condition
        )

        return {
            "pattern_number": 5,
            "pattern_name": "RSI50ライン攻防",
            "priority": self.pattern.priority,
            "confidence_score": confidence_score,
            "detection_time": current_time,
            "notification_title": "🔄 RSI50ライン攻防！",
            "notification_color": "0xFFA500",  # オレンジ色
            "strategy": "様子見推奨",
            "entry_condition": "方向性確定後",
            "d1_analysis": d1_condition,
            "h4_analysis": h4_condition,
            "h1_analysis": h1_condition,
            "m5_analysis": m5_condition,
            "description": "トレンド継続/転換の分岐点でRSI50ライン攻防中",
        }

    def _calculate_confidence_score(
        self,
        d1_condition: Dict[str, Any],
        h4_condition: Dict[str, Any],
        h1_condition: Dict[str, Any],
        m5_condition: Dict[str, Any],
    ) -> float:
        """信頼度スコアを計算"""
        base_score = 0.6  # 基本スコア（低優先度パターン）

        # 各時間軸の条件に基づいてスコアを調整
        if d1_condition and d1_condition.get("condition_met"):
            base_score += 0.1

        if h4_condition and h4_condition.get("condition_met"):
            base_score += 0.1

        if h1_condition and h1_condition.get("condition_met"):
            base_score += 0.1

        if m5_condition and m5_condition.get("condition_met"):
            base_score += 0.1

        return min(base_score, 1.0)  # 最大1.0に制限

    def get_detector_info(self) -> Dict[str, Any]:
        """検出器情報を取得"""
        return {
            "name": "RSI50ライン攻防検出器",
            "pattern_number": 5,
            "description": "RSI 45-55の範囲でトレンド継続/転換の分岐を検出",
            "priority": self.pattern.priority,
            "conditions": {
                "D1": "RSI 45-55 かつ MACD ゼロライン付近",
                "H4": "RSI 45-55 かつ ボリンジャーバンド ミドル付近",
                "H1": "RSI 45-55 かつ 価格変動増加",
                "M5": "RSI 50 ライン 攻防",
            },
        }
