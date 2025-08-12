"""
フラッグパターン検出器

パターン12: フラッグパターンを検出するクラス
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class FlagPatternDetector:
    """フラッグパターン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_12()
        self.utils = PatternUtils()
        self.min_flag_length = 3  # フラッグの最小長さ
        self.max_flag_length = 15  # フラッグの最大長さ
        self.flag_angle_tolerance = 30  # フラッグ角度の許容誤差（度）

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        フラッグパターンを検出

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            検出結果の辞書、検出されない場合はNone
        """
        # データの妥当性チェック
        if not self._validate_data(multi_timeframe_data):
            return None

        # 各時間軸の条件をチェック
        conditions_met = {}

        # D1条件チェック
        d1_conditions = self._check_d1_conditions(multi_timeframe_data.get("D1", {}))
        conditions_met["D1"] = d1_conditions

        # H4条件チェック
        h4_conditions = self._check_h4_conditions(multi_timeframe_data.get("H4", {}))
        conditions_met["H4"] = h4_conditions

        # H1条件チェック
        h1_conditions = self._check_h1_conditions(multi_timeframe_data.get("H1", {}))
        conditions_met["H1"] = h1_conditions

        # M5条件チェック
        m5_conditions = self._check_m5_conditions(multi_timeframe_data.get("M5", {}))
        conditions_met["M5"] = m5_conditions

        # 全条件が満たされているかチェック
        all_conditions_met = all(conditions_met.values())

        if all_conditions_met:
            # 信頼度スコアを計算
            confidence_score = self._calculate_flag_pattern_confidence(conditions_met)

            # 検出結果を返す
            return {
                "pattern_number": self.pattern.pattern_number,
                "pattern_name": self.pattern.name,
                "priority": self.pattern.priority,
                "conditions_met": conditions_met,
                "confidence_score": confidence_score,
                "notification_title": self.pattern.notification_title,
                "notification_color": self.pattern.notification_color,
                "take_profit": self.pattern.take_profit,
                "stop_loss": self.pattern.stop_loss,
                "detected_at": pd.Timestamp.now(),
                "timeframe_data": multi_timeframe_data,
            }

        return None

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """データの妥当性をチェック"""
        required_timeframes = ["D1", "H4", "H1", "M5"]

        for timeframe in required_timeframes:
            if timeframe not in data:
                return False

            if not self.utils.validate_timeframe_data(data[timeframe]):
                return False

        return True

    def _check_d1_conditions(self, d1_data: Dict[str, Any]) -> bool:
        """D1時間軸の条件をチェック"""
        if not d1_data:
            return False

        price_data = d1_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # ブルフラッグまたはベアフラッグの検出
        return (self._detect_bull_flag(price_data) or 
                self._detect_bear_flag(price_data))

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        price_data = h4_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # ブルフラッグまたはベアフラッグの検出
        return (self._detect_bull_flag(price_data) or 
                self._detect_bear_flag(price_data))

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        price_data = h1_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # ブルフラッグまたはベアフラッグの検出
        return (self._detect_bull_flag(price_data) or 
                self._detect_bear_flag(price_data))

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        price_data = m5_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # ブルフラッグまたはベアフラッグの検出
        return (self._detect_bull_flag(price_data) or 
                self._detect_bear_flag(price_data))

    def _detect_bull_flag(self, price_data: pd.DataFrame) -> bool:
        """ブルフラッグ検出"""
        if len(price_data) < 20:
            return False

        # フラッグポールを識別
        pole_data = self._identify_flagpole(price_data)
        if not pole_data:
            return False

        # フラッグを識別
        flag_data = self._identify_flag(price_data, pole_data['end_index'])
        if not flag_data:
            return False

        # フラッグブレイクアウトを検証
        return self._validate_flag_breakout(price_data, flag_data)

    def _detect_bear_flag(self, price_data: pd.DataFrame) -> bool:
        """ベアフラッグ検出"""
        if len(price_data) < 20:
            return False

        # フラッグポールを識別（下降）
        pole_data = self._identify_flagpole(price_data, direction='down')
        if not pole_data:
            return False

        # フラッグを識別
        flag_data = self._identify_flag(price_data, pole_data['end_index'])
        if not flag_data:
            return False

        # フラッグブレイクアウトを検証
        return self._validate_flag_breakout(price_data, flag_data)

    def _identify_flagpole(self, price_data: pd.DataFrame, direction: str = 'up') -> Optional[Dict[str, Any]]:
        """フラッグポール識別"""
        if len(price_data) < 10:
            return None

        # 直線的な上昇/下降を検出
        for start_idx in range(len(price_data) - 10):
            end_idx = start_idx + 10
            
            # 価格の変化を計算
            start_price = price_data.iloc[start_idx]['close']
            end_price = price_data.iloc[end_idx]['close']
            price_change = end_price - start_price
            
            # 方向に応じてチェック
            if direction == 'up' and price_change > 0:
                # 上昇トレンドの直線性をチェック
                if self._is_linear_trend(price_data.iloc[start_idx:end_idx], 'up'):
                    return {
                        'start_index': start_idx,
                        'end_index': end_idx,
                        'start_price': start_price,
                        'end_price': end_price,
                        'direction': direction
                    }
            elif direction == 'down' and price_change < 0:
                # 下降トレンドの直線性をチェック
                if self._is_linear_trend(price_data.iloc[start_idx:end_idx], 'down'):
                    return {
                        'start_index': start_idx,
                        'end_index': end_idx,
                        'start_price': start_price,
                        'end_price': end_price,
                        'direction': direction
                    }

        return None

    def _identify_flag(self, price_data: pd.DataFrame, pole_end: int) -> Optional[Dict[str, Any]]:
        """フラッグ識別"""
        if pole_end >= len(price_data) - self.min_flag_length:
            return None

        # フラッグの開始位置
        flag_start = pole_end
        
        # フラッグの終了位置を探す
        flag_end = min(pole_end + self.max_flag_length, len(price_data) - 1)
        
        # フラッグの形状をチェック
        flag_data = price_data.iloc[flag_start:flag_end]
        
        if len(flag_data) < self.min_flag_length:
            return None

        # フラッグの角度を計算
        flag_angle = self._calculate_flag_angle(flag_data)
        
        # 角度が許容範囲内かチェック
        if abs(flag_angle) > self.flag_angle_tolerance:
            return None

        return {
            'start_index': flag_start,
            'end_index': flag_end,
            'angle': flag_angle,
            'length': len(flag_data)
        }

    def _is_linear_trend(self, data: pd.DataFrame, direction: str) -> bool:
        """直線トレンドかどうかをチェック"""
        if len(data) < 5:
            return False

        # 価格の変化率を計算
        prices = data['close'].values
        changes = []
        
        for i in range(1, len(prices)):
            change = (prices[i] - prices[i-1]) / prices[i-1]
            changes.append(change)

        # 方向に応じてチェック
        if direction == 'up':
            # 上昇トレンドの場合、大部分が正の変化
            positive_changes = sum(1 for c in changes if c > 0)
            return positive_changes >= len(changes) * 0.7
        else:
            # 下降トレンドの場合、大部分が負の変化
            negative_changes = sum(1 for c in changes if c < 0)
            return negative_changes >= len(changes) * 0.7

    def _calculate_flag_angle(self, flag_data: pd.DataFrame) -> float:
        """フラッグの角度を計算"""
        if len(flag_data) < 2:
            return 0.0

        # 線形回帰で角度を計算
        x = range(len(flag_data))
        y = flag_data['close'].values
        
        # 簡単な角度計算
        start_price = y[0]
        end_price = y[-1]
        price_change = end_price - start_price
        length = len(flag_data)
        
        if length == 0:
            return 0.0
        
        # 角度を度で計算（簡易版）
        angle = (price_change / start_price) * 100  # パーセンテージ変化
        
        return angle

    def _validate_flag_breakout(self, price_data: pd.DataFrame, flag_data: Dict) -> bool:
        """フラッグブレイクアウト検証"""
        flag_end = flag_data['end_index']
        
        if flag_end >= len(price_data):
            return False

        # ブレイクアウトの検証
        flag_high = price_data.iloc[flag_data['start_index']:flag_data['end_index']]['high'].max()
        flag_low = price_data.iloc[flag_data['start_index']:flag_data['end_index']]['low'].min()
        
        # ブレイクアウト後の価格をチェック
        breakout_price = price_data.iloc[flag_end]['close']
        
        # 上向きブレイクアウトまたは下向きブレイクアウトをチェック
        up_breakout = breakout_price > flag_high
        down_breakout = breakout_price < flag_low
        
        return up_breakout or down_breakout

    def _calculate_flag_pattern_confidence(self, conditions_met: Dict[str, bool]) -> float:
        """フラッグパターン信頼度計算"""
        base_confidence = 0.75  # 基本信頼度75%
        
        # 各時間軸の重み
        timeframe_weights = {
            "D1": 0.4,
            "H4": 0.3,
            "H1": 0.2,
            "M5": 0.1
        }
        
        # 条件を満たした時間軸の重み付き合計
        weighted_sum = sum(
            timeframe_weights[timeframe] 
            for timeframe, met in conditions_met.items() 
            if met
        )
        
        # 信頼度を計算
        confidence = base_confidence * weighted_sum
        
        # 信頼度を0.6-0.95の範囲に制限
        return max(0.6, min(0.95, confidence))
