#!/usr/bin/env python3
"""
三層ゲート式フィルタリングエンジン

市場環境を段階的にフィルタリングし、高品質なシグナルを生成します。
"""

import sys
import os
import asyncio
import decimal
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import pytz

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.llm_analysis.core.pattern_loader import PatternLoader
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.llm_analysis.core.performance_monitor import performance_monitor, measure_async_time

logger = logging.getLogger(__name__)

# ログフォーマットを設定（モジュール名を非表示）
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
for handler in logging.getLogger().handlers:
    handler.setFormatter(formatter)


@dataclass
class GateResult:
    """ゲート結果のデータクラス"""
    valid: bool
    pattern: str
    confidence: float
    passed_conditions: List[str]
    failed_conditions: List[str]
    additional_data: Dict[str, Any]
    timestamp: datetime
    gate1_environment: Optional[str] = None


@dataclass
class ThreeGateResult:
    """三層ゲート最終結果のデータクラス"""
    symbol: str
    gate1: GateResult
    gate2: GateResult
    gate3: GateResult
    overall_confidence: float
    signal_type: str
    entry_price: float
    stop_loss: float
    take_profit: List[float]
    timestamp: datetime


class ConditionEvaluator:
    """条件評価クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _get_indicator_value(self, indicators: Dict[str, Any], indicator_name: str, timeframe: str) -> Any:
        """時間足プレフィックスを考慮した指標値の取得"""
        # 1. 時間足プレフィックス付きで検索
        prefixed_name = f"{timeframe}_{indicator_name}"
        if prefixed_name in indicators:
            value = indicators[prefixed_name]
            # DataFrameの場合は最新の値を取得
            if hasattr(value, 'iloc') and hasattr(value, 'columns'):
                if indicator_name in value.columns:
                    latest_value = value[indicator_name].iloc[-1]
                    self.logger.debug(f"指標 {indicator_name} を {timeframe} 時間足で発見: {prefixed_name} = {latest_value}")
                    return latest_value
            else:
                self.logger.debug(f"指標 {indicator_name} を {timeframe} 時間足で発見: {prefixed_name} = {value}")
                return value
        
        # 2. 元の名前で検索
        if indicator_name in indicators:
            value = indicators[indicator_name]
            # DataFrameの場合は最新の値を取得
            if hasattr(value, 'iloc') and hasattr(value, 'columns'):
                if indicator_name in value.columns:
                    latest_value = value[indicator_name].iloc[-1]
                    self.logger.debug(f"指標 {indicator_name} を元の名前で発見: {latest_value}")
                    return latest_value
            else:
                self.logger.debug(f"指標 {indicator_name} を元の名前で発見: {value}")
                return value
        
        # 3. 他の時間足で検索（フォールバック）
        timeframes = ['1d', '4h', '1h', '5m']
        for tf in timeframes:
            if tf != timeframe:
                fallback_name = f"{tf}_{indicator_name}"
                if fallback_name in indicators:
                    value = indicators[fallback_name]
                    # DataFrameの場合は最新の値を取得
                    if hasattr(value, 'iloc') and hasattr(value, 'columns'):
                        if indicator_name in value.columns:
                            latest_value = value[indicator_name].iloc[-1]
                            self.logger.debug(f"指標 {indicator_name} を {tf} 時間足で発見: {fallback_name} = {latest_value}")
                            return latest_value
                    else:
                        self.logger.debug(f"指標 {indicator_name} を {tf} 時間足で発見: {fallback_name} = {value}")
                        return value
        
        self.logger.warning(f"指標 {indicator_name} が見つかりません (時間足: {timeframe})")
        return None
    
    async def evaluate_condition(self, indicators: Dict[str, Any], condition: Dict[str, Any]) -> float:
        """
        個別条件の評価
        
        Args:
            indicators: テクニカル指標の辞書
            condition: 条件設定の辞書
            
        Returns:
            条件の適合度スコア（0.0-1.0）
        """
        try:
            indicator_name = condition.get('indicator')
            operator = condition.get('operator')
            reference = condition.get('reference')
            value = condition.get('value')
            timeframe = condition.get('timeframe', '1d')
            
            # 指標値の取得（時間足プレフィックスを考慮）
            if indicator_name is None:
                return 0.0
            indicator_value = self._get_indicator_value(indicators, indicator_name, timeframe)
            if indicator_value is None:
                self.logger.warning(f"指標が見つかりません: {indicator_name} (時間足: {timeframe})")
                return 0.0
            
            # 参照値の取得（時間足プレフィックスを考慮）
            if reference:
                reference_value = self._get_indicator_value(indicators, reference, timeframe)
                if reference_value is None and value is not None:
                    reference_value = value
            elif value is not None:
                reference_value = value
            else:
                self.logger.warning(f"参照値が見つかりません: {reference}")
                return 0.0
            
            if reference_value is None:
                return 0.0
            
            # 演算子による評価
            if operator in ['>', '<', '>=', '<=', '==', '!=']:
                return self._evaluate_comparison(indicator_value, operator, reference_value, condition)
            elif operator in ['between', 'not_between']:
                return self._evaluate_range(indicator_value, operator, reference_value)
            elif operator in ['all_above', 'all_below', 'any_above', 'any_below']:
                return self._evaluate_logical(indicator_value, operator, reference_value, condition)
            elif operator in ['near', 'engulfs', 'breaks', 'oscillates_around']:
                return self._evaluate_special(indicator_value, operator, reference_value, condition)
            else:
                self.logger.warning(f"未対応の演算子: {operator}")
                return 0.0
                
        except Exception as e:
            self.logger.error(f"条件評価エラー: {condition.get('name', 'unknown')} - {e}")
            import traceback
            self.logger.error(f"詳細エラー: {traceback.format_exc()}")
            return 0.0
    
    def _evaluate_comparison(self, value: float, operator: str, reference: float, condition: Optional[Dict[str, Any]] = None) -> float:
        """比較演算子の評価"""
        try:
            # 安全な型変換
            if value is None or (isinstance(value, float) and (value != value)):  # NaN チェック
                return 0.0
            if reference is None or (isinstance(reference, float) and (reference != reference)):  # NaN チェック
                return 0.0
            
            # 数値型に変換
            value = float(value)
            reference = float(reference)
            
            # multiplierパラメータの処理
            if condition and 'multiplier' in condition:
                reference = reference * condition['multiplier']
            
            if operator == '>':
                return 1.0 if value > reference else 0.0
            elif operator == '<':
                return 1.0 if value < reference else 0.0
            elif operator == '>=':
                return 1.0 if value >= reference else 0.0
            elif operator == '<=':
                return 1.0 if value <= reference else 0.0
            elif operator == '==':
                return 1.0 if abs(value - reference) < 0.001 else 0.0
            elif operator == '!=':
                return 1.0 if abs(value - reference) >= 0.001 else 0.0
            elif operator == 'was_consistently_below':
                # 過去の値が一貫して基準値より下にあるかチェック
                return 1.0 if value < reference else 0.0
            elif operator == 'was_consistently_above':
                # 過去の値が一貫して基準値より上にあるかチェック
                return 1.0 if value > reference else 0.0
            elif operator == 'oscillates_around':
                # 値が基準値の周りで振動しているかチェック（簡易実装）
                return 1.0 if abs(value - reference) / reference < 0.05 else 0.0
            else:
                return 0.0
                
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            self.logger.warning(f"比較評価エラー: value={value}, reference={reference}, operator={operator}, error={e}")
            return 0.0
    
    def _evaluate_range(self, value: float, operator: str, reference: List[float]) -> float:
        """範囲演算子の評価"""
        if not isinstance(reference, list) or len(reference) != 2:
            return 0.0
        
        min_val, max_val = reference
        in_range = min_val <= value <= max_val
        
        if operator == 'between':
            return 1.0 if in_range else 0.0
        elif operator == 'not_between':
            return 1.0 if not in_range else 0.0
        else:
            return 0.0
    
    def _evaluate_logical(self, value: Any, operator: str, reference: Any, condition: Dict[str, Any]) -> float:
        """論理演算子の評価"""
        try:
            periods = condition.get('periods', 1)
            
            if not isinstance(value, list):
                value = [value]
            
            # 安全な型変換
            reference = float(reference) if reference is not None else 0.0
            
            # 配列の要素を安全に変換
            safe_values = []
            for v in value[-periods:]:
                if v is None or (isinstance(v, float) and (v != v)):  # NaN チェック
                    continue
                try:
                    safe_values.append(float(v))
                except (ValueError, TypeError, decimal.InvalidOperation):
                    continue
            
            if not safe_values:
                return 0.0
            
            if operator == 'all_above':
                return 1.0 if all(v > reference for v in safe_values) else 0.0
            elif operator == 'all_below':
                return 1.0 if all(v < reference for v in safe_values) else 0.0
            elif operator == 'any_above':
                return 1.0 if any(v > reference for v in safe_values) else 0.0
            elif operator == 'any_below':
                return 1.0 if any(v < reference for v in safe_values) else 0.0
            else:
                return 0.0
                
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            self.logger.warning(f"論理評価エラー: value={value}, reference={reference}, operator={operator}, error={e}")
            return 0.0
    
    def _evaluate_special(self, value: Any, operator: str, reference: Any, condition: Dict[str, Any]) -> float:
        """特殊演算子の評価"""
        if operator == 'near':
            if value is None or reference is None:
                return 0.0
            tolerance = condition.get('tolerance', 0.01)
            return 1.0 if abs(value - reference) <= tolerance * reference else 0.0
        elif operator == 'engulfs':
            # 包み込みパターンの評価
            if value is None or reference is None:
                return 0.0
            try:
                # 現在のローソク足が前のローソク足を包み込むかチェック
                current_body = abs(value)
                previous_body = abs(reference)
                return 1.0 if current_body > previous_body * 1.1 else 0.0
            except (TypeError, ValueError):
                return 0.0
        elif operator == 'breaks':
            # ブレイクアウトの評価（簡易版）
            return 1.0 if value > reference else 0.0
        elif operator == 'oscillates_around':
            # 振動の評価（簡易版）
            lookback_periods = condition.get('lookback_periods', 10)
            if isinstance(value, list) and len(value) >= lookback_periods:
                recent_values = value[-lookback_periods:]
                above_count = sum(1 for v in recent_values if v > reference)
                below_count = sum(1 for v in recent_values if v < reference)
                return 1.0 if above_count > 0 and below_count > 0 else 0.0
            return 0.0
        else:
            return 0.0


class ThreeGateEngine:
    """三層ゲート式フィルタリングエンジン"""
    
    def __init__(self):
        self.pattern_loader = PatternLoader(config_dir="/app/modules/llm_analysis/config")
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.condition_evaluator = ConditionEvaluator()
        self.logger = logging.getLogger(__name__)
        self.jst = pytz.timezone('Asia/Tokyo')
        
        # 統計情報
        self.stats = {
            'total_evaluations': 0,
            'gate1_passed': 0,
            'gate2_passed': 0,
            'gate3_passed': 0,
            'signals_generated': 0,
            'start_time': datetime.now(timezone.utc),
            'total_evaluation_time': 0.0,
        }
        
        # シグナル間隔制限（最後のシグナル生成時刻を記録）
        self.last_signal_time = None
        self.min_signal_interval = timedelta(minutes=15)  # 15分間隔制限
        # テスト用: 環境変数でシグナル間隔制限を無効化
        self.force_signal_on_test = os.getenv('FORCE_SIGNAL_ON_TEST', '0') == '1'
        
        # リスク管理設定
        self.min_risk_pips = 3.0  # 最小リスク幅（pips）
        self.atr_multiplier_min = 0.8  # ATR最小倍率
        self.atr_multiplier_max = 2.0  # ATR最大倍率
        self.buffer_pips = 2.0  # サポレジからのバッファ（pips）
        self.take_profit_ratios = [2.0, 3.0, 4.0]  # TP倍率（R倍）
    
    def _get_jst_time(self) -> str:
        """現在時刻を日本時間で取得"""
        jst_now = datetime.now(self.jst)
        return jst_now.strftime('%Y-%m-%d %H:%M:%S JST')
    
    def _get_indicator_value(self, indicators: Dict[str, Any], indicator_name: str, timeframe: str) -> Any:
        """時間足プレフィックスを考慮した指標値の取得"""
        # 1. 時間足プレフィックス付きで検索
        prefixed_name = f"{timeframe}_{indicator_name}"
        if prefixed_name in indicators:
            self.logger.debug(f"指標 {indicator_name} を {timeframe} 時間足で発見: {prefixed_name} = {indicators[prefixed_name]}")
            return indicators[prefixed_name]
        
        # 2. 元の名前で検索
        if indicator_name in indicators:
            self.logger.debug(f"指標 {indicator_name} を元の名前で発見: {indicators[indicator_name]}")
            return indicators[indicator_name]
        
        # 3. 他の時間足で検索（フォールバック）
        timeframes = ['1d', '4h', '1h', '5m']
        for tf in timeframes:
            if tf != timeframe:
                fallback_name = f"{tf}_{indicator_name}"
                if fallback_name in indicators:
                    self.logger.debug(f"指標 {indicator_name} を {tf} 時間足で発見: {fallback_name} = {indicators[fallback_name]}")
                    return indicators[fallback_name]
        
        self.logger.warning(f"指標 {indicator_name} が見つかりません (時間足: {timeframe})")
        return None
    
    def _extract_support_resistance_levels(self, data: Dict[str, Any]) -> Dict[str, List[float]]:
        """サポート・レジスタンスレベルを抽出"""
        levels = {'support': [], 'resistance': []}
        
        # ボリンジャーバンドをサポレジ候補として使用
        for timeframe in ['1h', '4h', '1d']:
            bb_upper = self._get_indicator_value(data, 'BB_Upper', timeframe)
            bb_lower = self._get_indicator_value(data, 'BB_Lower', timeframe)
            bb_middle = self._get_indicator_value(data, 'BB_Middle', timeframe)
            
            if bb_upper and bb_lower and bb_middle:
                levels['resistance'].extend([bb_upper, bb_middle])
                levels['support'].extend([bb_lower, bb_middle])
        
        # 移動平均線をサポレジ候補として使用
        for timeframe in ['1h', '4h', '1d']:
            for ma in ['EMA_21', 'EMA_50', 'EMA_200']:
                ma_value = self._get_indicator_value(data, ma, timeframe)
                if ma_value:
                    levels['support'].append(ma_value)
                    levels['resistance'].append(ma_value)
        
        return levels
    
    def _extract_fibonacci_levels(self, data: Dict[str, Any]) -> Dict[str, List[float]]:
        """フィボナッチレベルを抽出"""
        levels = {'retracement': [], 'extension': []}
        
        for timeframe in ['1h', '4h', '1d']:
            # フィボナッチリトレースメント
            for fib in ['Fib_0.236', 'Fib_0.382', 'Fib_0.5', 'Fib_0.618', 'Fib_0.786']:
                fib_value = self._get_indicator_value(data, fib, timeframe)
                if fib_value:
                    levels['retracement'].append(fib_value)
            
            # フィボナッチエクステンション
            for fib in ['Fib_1.272', 'Fib_1.414', 'Fib_1.618', 'Fib_2.0']:
                fib_value = self._get_indicator_value(data, fib, timeframe)
                if fib_value:
                    levels['extension'].append(fib_value)
        
        return levels
    
    def _find_nearest_level(self, price: float, levels: List[float], direction: str, buffer_pips: float) -> Optional[float]:
        """指定方向で最も近いレベルを検索（バッファ付き）"""
        if not levels:
            return None
        
        buffer = buffer_pips * 0.0001  # pips to price
        
        if direction == 'above':
            # 価格より上で最も近いレベル
            candidates = [level for level in levels if level > price + buffer]
            return min(candidates) if candidates else None
        elif direction == 'below':
            # 価格より下で最も近いレベル
            candidates = [level for level in levels if level < price - buffer]
            return max(candidates) if candidates else None
        
        return None
    
    def _log_signal_generation(self, result: ThreeGateResult):
        """シグナル生成時の特別表示"""
        # シグナルタイプに応じたアイコン
        signal_icon = "🟢" if result.signal_type == "BUY" else "🔴"
        
        self.logger.info("=" * 60)
        self.logger.info(f"🎉 {signal_icon} シグナル生成！ {signal_icon}")
        self.logger.info("=" * 60)
        self.logger.info(f"📊 基本情報:")
        self.logger.info(f"├── シンボル: {result.symbol}")
        self.logger.info(f"├── タイプ: {result.signal_type}")
        self.logger.info(f"├── 信頼度: {result.overall_confidence:.2f} ({self._get_confidence_level(result.overall_confidence)})")
        self.logger.info(f"└── 生成時刻: {self._get_jst_time()}")
        
        # リスクリワード比の計算
        risk = abs(result.entry_price - result.stop_loss)
        reward = abs(result.take_profit[0] - result.entry_price) if result.take_profit else 0
        rr_ratio = reward / risk if risk > 0 else 0
        
        # pips換算（USDJPY想定：0.01 = 1 pip）
        risk_pips = risk * 10000
        reward_pips = reward * 10000
        
        self.logger.info(f"💰 取引情報:")
        self.logger.info(f"├── エントリー価格: {result.entry_price:.5f}")
        self.logger.info(f"├── ストップロス: {result.stop_loss:.5f}")
        self.logger.info(f"├── リスク: {risk:.5f} ({risk_pips:.1f} pips)")
        self.logger.info(f"└── テイクプロフィット: {', '.join([f'{tp:.5f}' for tp in result.take_profit])}")
        
        self.logger.info(f"🎯 パターン根拠:")
        self.logger.info(f"├── GATE 1: {self._translate_pattern_name(result.gate1.pattern)} (信頼度: {result.gate1.confidence:.2f})")
        self.logger.info(f"├── GATE 2: {self._translate_pattern_name(result.gate2.pattern)} (信頼度: {result.gate2.confidence:.2f})")
        if result.gate3 and result.gate3.pattern:
            self.logger.info(f"└── GATE 3: {self._translate_pattern_name(result.gate3.pattern)} (信頼度: {result.gate3.confidence:.2f})")
        else:
            self.logger.info(f"└── GATE 3: 未評価")
        
        self.logger.info(f"📈 リスク分析:")
        self.logger.info(f"├── リスク: {risk:.5f} ({risk_pips:.1f} pips)")
        self.logger.info(f"├── リワード: {reward:.5f} ({reward_pips:.1f} pips)")
        self.logger.info(f"└── リスクリワード比: 1:{rr_ratio:.2f}")
        
        self.logger.info("=" * 60)
    
    def _get_confidence_level(self, confidence: float) -> str:
        """信頼度レベルを文字列で返す"""
        if confidence >= 0.9:
            return "非常に高い"
        elif confidence >= 0.8:
            return "高い"
        elif confidence >= 0.7:
            return "中程度"
        elif confidence >= 0.6:
            return "低い"
        else:
            return "非常に低い"
    
    def _translate_pattern_name(self, pattern: str) -> str:
        """パターン名を日本語に翻訳"""
        translations = {
            # GATE 1 - 環境認識パターン
            'trending_market_uptrend': '確度の高い上昇トレンド相場',
            'trending_market_downtrend': '確度の高い下降トレンド相場',
            'trend_reversal_uptrend': '上昇トレンド転換の初動',
            'trend_reversal_downtrend': '下降トレンド転換の初動',
            'ranging_market': '明確なレンジ相場',
            'trending_market': 'トレンド相場',
            'trend_reversal': 'トレンド転換',
            
            # GATE 2 - シナリオ選定パターン
            'pullback_setup': '押し目・戻りセットアップ',
            'breakout_setup': 'ブレイクアウト準備完了',
            'range_boundary': 'レンジ上限・下限到達',
            'pullback_buy': '押し目買い',
            'rally_sell': '戻り売り',
            'uptrend_breakout': '上昇ブレイクアウト',
            'downtrend_breakout': '下降ブレイクアウト',
            'breakout_setup_direct': 'ブレイクアウト準備完了',
            'uptrend_pullback': '上昇トレンド押し目',
            'downtrend_pullback': '下降トレンド戻り',
            
            # GATE 3 - トリガーパターン
            'price_action_reversal': 'プライスアクション反転確認',
            'momentum_confirmation': 'モメンタム確認',
            'uptrend_reversal': '上昇転換シグナル',
            'downtrend_reversal': '下降転換シグナル',
            'engulfing_pattern': '包み足パターン',
            'pinbar_pattern': 'ピンバーパターン',
            'uptrend_pinbar': '上昇ピンバー',
            'downtrend_pinbar': '下降ピンバー',
            'uptrend_engulfing': '上昇包み足',
            'downtrend_engulfing': '下降包み足',
            'uptrend_momentum': '上昇モメンタム',
            'downtrend_momentum': '下降モメンタム',
            
            # 条件名の翻訳
            'price_above_ema200': '価格がEMA200上',
            'price_below_ema200': '価格がEMA200下',
            'recent_closes_consistent': '最近の終値一貫性',
            'strong_trend_adx': '強いトレンド（ADX）',
            'recent_break_above': '最近の上抜け',
            'recent_break_below': '最近の下抜け',
            'macd_bullish': 'MACD強気',
            'macd_bearish': 'MACD弱気',
            'weak_trend_adx': '弱いトレンド（ADX）',
            'consistently_weak_trend': '一貫して弱いトレンド',
            'bollinger_compression': 'ボリンジャー圧縮',
            'price_near_bands': '価格がバンド近辺',
            'bearish_candle': '弱気ローソク足',
            'rsi_overbought_decline': 'RSI過買い圏下落',
            'momentum_bearish': 'モメンタム弱気',
            'strong_candle': '強いローソク足',
            'engulfs_previous': '前足を包み込む',
            'rsi_oversold_recovery': 'RSI過売り圏回復',
            'macd_bullish': 'MACD強気',
            'stochastic_bullish': 'ストキャス強気',
            'rsi_overbought_decline': 'RSI過買い圏下落',
            'stochastic_bearish': 'ストキャス弱気',
            
            # その他
            'no_valid_pattern': '有効なパターンなし',
            'no_valid_scenario': '有効なシナリオなし',
            'no_valid_trigger': '有効なトリガーなし'
        }
        
        return translations.get(pattern, pattern)
    
    def _translate_condition_name(self, condition_name: str) -> str:
        """条件名を日本語に翻訳"""
        translations = {
            # 価格関連
            'price_above_ema200': '価格がEMA200上',
            'price_below_ema200': '価格がEMA200下',
            'price_near_bands': '価格がバンド近辺',
            'price_oscillation': '価格の振動',
            
            # トレンド関連
            'recent_closes_consistent': '最近の終値一貫性',
            'strong_trend_adx': '強いトレンド（ADX）',
            'weak_trend_adx': '弱いトレンド（ADX）',
            'consistently_weak_trend': '一貫して弱いトレンド',
            'recent_break_above': '最近の上抜け',
            'recent_break_below': '最近の下抜け',
            
            # モメンタム関連
            'macd_bullish': 'MACD強気',
            'macd_bearish': 'MACD弱気',
            'momentum_bearish': 'モメンタム弱気',
            'rsi_oversold_recovery': 'RSI過売り圏回復',
            'rsi_overbought_decline': 'RSI過買い圏下落',
            'stochastic_bullish': 'ストキャス強気',
            'stochastic_bearish': 'ストキャス弱気',
            
            # ボリンジャーバンド関連
            'bollinger_compression': 'ボリンジャー圧縮',
            'price_near_bands': '価格がバンド近辺',
            
            # ローソク足関連
            'bearish_candle': '弱気ローソク足',
            'bullish_candle': '強気ローソク足',
            'strong_candle': '強いローソク足',
            'engulfs_previous': '前足を包み込む',
            'long_lower_shadow': '長い下ヒゲ',
            'long_upper_shadow': '長い上ヒゲ',
            'small_upper_shadow': '短い上ヒゲ',
            'small_lower_shadow': '短い下ヒゲ',
            'near_support': 'サポート近辺',
            'near_resistance': 'レジスタンス近辺',
            'current_bullish': '現在足強気',
            'current_bearish': '現在足弱気',
            'previous_bullish': '前足強気',
            'previous_bearish': '前足弱気',
            
            # その他
            'in_pullback_zone': '押し目ゾーン内',
            'in_retracement_zone': '戻りゾーン内',
            'not_overheated': '過熱していない',
            'rsi_not_extreme': 'RSI極値でない',
            'near_resistance': 'レジスタンス近辺',
            'near_support': 'サポート近辺'
        }
        
        return translations.get(condition_name, condition_name)
    
    def _show_progress(self, current_gate: int, total_gates: int = 3):
        """進捗表示"""
        progress = "█" * current_gate + "░" * (total_gates - current_gate)
        self.logger.info(f"🚀 三層ゲート分析進行中... [{progress}] GATE {current_gate}/{total_gates}")
    
    def _log_statistics(self):
        """統計情報の表示"""
        if self.stats['total_evaluations'] > 0:
            gate1_rate = (self.stats['gate1_passed'] / self.stats['total_evaluations']) * 100
            gate2_rate = (self.stats['gate2_passed'] / self.stats['gate1_passed']) * 100 if self.stats['gate1_passed'] > 0 else 0
            gate3_rate = (self.stats['gate3_passed'] / self.stats['gate2_passed']) * 100 if self.stats['gate2_passed'] > 0 else 0
            signal_rate = (self.stats['signals_generated'] / self.stats['total_evaluations']) * 100
            
            # 稼働時間の計算
            uptime = datetime.now(timezone.utc) - self.stats.get('start_time', datetime.now(timezone.utc))
            uptime_hours = uptime.total_seconds() / 3600
            
            # パフォーマンス指標
            avg_evaluation_time = self.stats.get('total_evaluation_time', 0) / max(self.stats['total_evaluations'], 1)
            
            self.logger.info("📊 リアルタイム分析統計:")
            self.logger.info(f"├── 稼働時間: {uptime_hours:.1f}時間")
            self.logger.info(f"├── 総評価回数: {self.stats['total_evaluations']:,}回")
            self.logger.info(f"├── 平均処理時間: {avg_evaluation_time:.3f}秒")
            self.logger.info(f"├── GATE 1 通過率: {gate1_rate:.1f}% ({self.stats['gate1_passed']}/{self.stats['total_evaluations']})")
            self.logger.info(f"├── GATE 2 通過率: {gate2_rate:.1f}% ({self.stats['gate2_passed']}/{self.stats['gate1_passed']})")
            self.logger.info(f"├── GATE 3 通過率: {gate3_rate:.1f}% ({self.stats['gate3_passed']}/{self.stats['gate2_passed']})")
            self.logger.info(f"└── シグナル生成率: {signal_rate:.1f}% ({self.stats['signals_generated']}/{self.stats['total_evaluations']})")
            
            # パフォーマンス警告
            self._check_performance_warnings(avg_evaluation_time, signal_rate, gate1_rate, gate2_rate, gate3_rate)
    
    def _check_signal_interval(self) -> bool:
        """シグナル間隔制限のチェック"""
        if self.force_signal_on_test:
            self.logger.info("🧪 テストモード: シグナル間隔制限を無効化しています")
            return True
        if self.last_signal_time is None:
            return True  # 初回は制限なし
        
        current_time = datetime.now(timezone.utc)
        time_since_last_signal = current_time - self.last_signal_time
        
        if time_since_last_signal < self.min_signal_interval:
            remaining_time = self.min_signal_interval - time_since_last_signal
            self.logger.warning(f"⏰ シグナル間隔制限: あと {remaining_time.total_seconds()/60:.1f}分待機が必要")
            return False
        
        return True
    
    def _check_performance_warnings(self, avg_evaluation_time: float, signal_rate: float, 
                                  gate1_rate: float, gate2_rate: float, gate3_rate: float):
        """パフォーマンス警告のチェック"""
        warnings = []
        
        # 処理時間の警告
        if avg_evaluation_time > 0.5:
            warnings.append(f"⚠️ 処理時間が長いです: {avg_evaluation_time:.3f}秒")
        elif avg_evaluation_time > 0.3:
            warnings.append(f"ℹ️ 処理時間がやや長いです: {avg_evaluation_time:.3f}秒")
        
        # シグナル生成率の警告
        if signal_rate < 0.5:
            warnings.append(f"⚠️ シグナル生成率が非常に低いです: {signal_rate:.1f}%")
        elif signal_rate < 1.0:
            warnings.append(f"ℹ️ シグナル生成率が低いです: {signal_rate:.1f}%")
        
        # ゲート通過率の警告
        if gate1_rate < 20:
            warnings.append(f"⚠️ GATE 1通過率が非常に低いです: {gate1_rate:.1f}%")
        elif gate1_rate < 30:
            warnings.append(f"ℹ️ GATE 1通過率が低いです: {gate1_rate:.1f}%")
        
        if gate2_rate < 10:
            warnings.append(f"⚠️ GATE 2通過率が非常に低いです: {gate2_rate:.1f}%")
        elif gate2_rate < 20:
            warnings.append(f"ℹ️ GATE 2通過率が低いです: {gate2_rate:.1f}%")
        
        if gate3_rate < 5:
            warnings.append(f"⚠️ GATE 3通過率が非常に低いです: {gate3_rate:.1f}%")
        elif gate3_rate < 10:
            warnings.append(f"ℹ️ GATE 3通過率が低いです: {gate3_rate:.1f}%")
        
        # 警告の表示
        for warning in warnings:
            if "⚠️" in warning:
                self.logger.warning(warning)
            else:
                self.logger.info(warning)
        
        # 推奨アクションの表示
        if warnings:
            self.logger.info("💡 推奨アクション:")
            if any("処理時間" in w for w in warnings):
                self.logger.info("   - パターン条件の簡素化を検討")
                self.logger.info("   - 不要な指標計算の削除を検討")
            if any("シグナル生成率" in w for w in warnings):
                self.logger.info("   - 信頼度閾値の調整を検討")
                self.logger.info("   - パターン条件の緩和を検討")
            if any("GATE" in w for w in warnings):
                self.logger.info("   - ゲート条件の見直しを検討")
                self.logger.info("   - 市場環境の変化を確認")
    
    def _log_gate_result(self, gate_num: int, result: GateResult, gate_name: str = ""):
        """ゲート結果の階層化ログ出力"""
        if result.valid:
            self.logger.info(f"✅ GATE {gate_num}: {result.pattern} - 信頼度: {result.confidence:.2f}")
            if result.passed_conditions:
                self.logger.info(f"   📋 合格条件: {', '.join(result.passed_conditions)}")
            self._log_condition_details(f"GATE {gate_num}", result)
        else:
            self.logger.info(f"❌ GATE {gate_num}: 不合格 - 信頼度: {result.confidence:.2f}")
            self._log_failed_gate_details(f"GATE {gate_num}", result)
    
    def _log_evaluation_summary(self, symbol: str, results: list):
        """評価結果のサマリー表示"""
        self.logger.info(f"🚪 三層ゲート評価開始: {symbol} [{self._get_jst_time()}]")
        
        # 階層化された結果表示
        for i, (gate_name, result) in enumerate(results, 1):
            if result and result.valid:
                self.logger.info(f"├── GATE {i}: {gate_name}")
                pattern_display = self._translate_pattern_name(result.pattern)
                self.logger.info(f"│   ├── ✅ {pattern_display} - 信頼度: {result.confidence:.2f}")
                if result.passed_conditions:
                    self.logger.info(f"│   └── 📋 合格条件: {', '.join(result.passed_conditions)}")
            else:
                self.logger.info(f"├── GATE {i}: {gate_name}")
                confidence = result.confidence if result else 0.0
                self.logger.info(f"│   └── ❌ 不合格 - 信頼度: {confidence:.2f}")
                # 不合格の詳細を表示
                if result:
                    self._log_failed_gate_details(f"GATE {i}", result)
        
        # 最終結果
        if all(result and result.valid for _, result in results):
            self.logger.info("└── 📊 最終結果: シグナル生成")
        else:
            self.logger.info("└── 📊 最終結果: シグナル生成なし")

    @measure_async_time('total_evaluation_time')
    async def evaluate(self, symbol: str, data: Dict[str, Any]) -> Optional[ThreeGateResult]:
        """
        三層ゲートによる評価
        
        Args:
            symbol: 通貨ペアシンボル
            data: 市場データ
            
        Returns:
            三層ゲート評価結果（すべてのゲートを通過した場合のみ）
        """
        try:
            start_time = datetime.now(timezone.utc)
            
            # 統計情報の更新
            self.stats['total_evaluations'] += 1
            
            # 100回ごとに統計情報を表示
            if self.stats['total_evaluations'] % 100 == 0:
                self._log_statistics()
            
            # GATE 1: 環境認識
            self._show_progress(1)
            gate1_result = await self._evaluate_gate1(symbol, data)
            if not gate1_result.valid:
                self._log_evaluation_summary(symbol, [("環境認識ゲート", gate1_result)])
                return None
            
            self.stats['gate1_passed'] += 1
            
            # GATE 2: シナリオ選定
            self._show_progress(2)
            gate2_result = await self._evaluate_gate2(symbol, data, gate1_result)
            if not gate2_result.valid:
                self._log_evaluation_summary(symbol, [
                    ("環境認識ゲート", gate1_result),
                    ("シナリオ選定ゲート", gate2_result)
                ])
                return None
            
            self.stats['gate2_passed'] += 1
            
            # GATE 3: トリガー
            self._show_progress(3)
            gate3_result = await self._evaluate_gate3(symbol, data, gate2_result)
            if not gate3_result.valid:
                self._log_evaluation_summary(symbol, [
                    ("環境認識ゲート", gate1_result),
                    ("シナリオ選定ゲート", gate2_result),
                    ("トリガーゲート", gate3_result)
                ])
                return None
            
            self.stats['gate3_passed'] += 1
            
            # シグナル間隔制限のチェック
            if not self._check_signal_interval():
                self.logger.info("⏰ シグナル間隔制限により、シグナル生成をスキップ")
                return None
            
            # 最終結果の生成
            overall_confidence = (gate1_result.confidence + gate2_result.confidence + gate3_result.confidence) / 3.0
            
            # エントリー価格を先に計算
            entry_price = self._calculate_entry_price(data, gate1_result, gate2_result)
            
            result = ThreeGateResult(
                symbol=symbol,
                gate1=gate1_result,
                gate2=gate2_result,
                gate3=gate3_result,
                overall_confidence=overall_confidence,
                signal_type=self._determine_signal_type(gate1_result, gate2_result, gate3_result),
                entry_price=entry_price,
                stop_loss=self._calculate_stop_loss(data, gate1_result, gate2_result, entry_price),
                take_profit=self._calculate_take_profit(data, gate1_result, gate2_result, entry_price),
                timestamp=datetime.now(timezone.utc)
            )
            
            # 統計情報の更新
            self.stats['signals_generated'] += 1
            self.last_signal_time = datetime.now(timezone.utc)  # シグナル間隔制限用
            
            # 評価時間の記録
            evaluation_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.stats['total_evaluation_time'] += evaluation_time
            
            # 成功時の特別表示
            self._log_signal_generation(result)
            return result
            
        except Exception as e:
            # 評価時間の記録（エラー時も）
            evaluation_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.stats['total_evaluation_time'] += evaluation_time
            
            self.logger.error(f"❌ 三層ゲート評価エラー: {e}")
            return None
    
    @measure_async_time('gate1_evaluation_time')
    async def _evaluate_gate1(self, symbol: str, data: Dict[str, Any]) -> GateResult:
        """GATE 1: 環境認識の評価"""
        try:
            self.logger.info(f"GATE 1 パターン設定読み込み開始")
            patterns = self.pattern_loader.load_gate_patterns(1)
            self.logger.info(f"GATE 1 パターン設定読み込み完了: {len(patterns.get('patterns', {}))}個のパターン")
            
            for pattern_name, pattern_config in patterns.get('patterns', {}).items():
                self.logger.info(f"GATE 1 パターン評価: {pattern_name}")
                
                # パターンの種類に応じて評価
                if 'bullish_trend' in pattern_config:
                    result = await self._evaluate_pattern_variant(
                        pattern_name, pattern_config['bullish_trend'], data, 'bullish'
                    )
                    self.logger.info(f"GATE 1 パターン結果: {pattern_name} (bullish) - 有効: {result.valid}, 信頼度: {result.confidence:.2f}")
                    # 最後に評価されたパターンの条件詳細を保存
                    self._last_condition_details = result.additional_data.get('condition_details', {})
                    if result.valid:
                        return result
                
                if 'bearish_trend' in pattern_config:
                    result = await self._evaluate_pattern_variant(
                        pattern_name, pattern_config['bearish_trend'], data, 'bearish'
                    )
                    self.logger.info(f"GATE 1 パターン結果: {pattern_name} (bearish) - 有効: {result.valid}, 信頼度: {result.confidence:.2f}")
                    # 最後に評価されたパターンの条件詳細を保存
                    self._last_condition_details = result.additional_data.get('condition_details', {})
                    if result.valid:
                        return result
                
                if 'uptrend_reversal' in pattern_config:
                    result = await self._evaluate_pattern_variant(
                        pattern_name, pattern_config['uptrend_reversal'], data, 'uptrend_reversal'
                    )
                    self.logger.info(f"GATE 1 パターン結果: {pattern_name} (uptrend_reversal) - 有効: {result.valid}, 信頼度: {result.confidence:.2f}")
                    # 最後に評価されたパターンの条件詳細を保存
                    self._last_condition_details = result.additional_data.get('condition_details', {})
                    if result.valid:
                        return result
                
                if 'downtrend_reversal' in pattern_config:
                    result = await self._evaluate_pattern_variant(
                        pattern_name, pattern_config['downtrend_reversal'], data, 'downtrend_reversal'
                    )
                    self.logger.info(f"GATE 1 パターン結果: {pattern_name} (downtrend_reversal) - 有効: {result.valid}, 信頼度: {result.confidence:.2f}")
                    # 最後に評価されたパターンの条件詳細を保存
                    self._last_condition_details = result.additional_data.get('condition_details', {})
                    if result.valid:
                        return result
                
                if 'conditions' in pattern_config:
                    result = await self._evaluate_pattern_variant(
                        pattern_name, pattern_config, data, 'neutral'
                    )
                    self.logger.info(f"GATE 1 パターン結果: {pattern_name} (neutral) - 有効: {result.valid}, 信頼度: {result.confidence:.2f}")
                    # 最後に評価されたパターンの条件詳細を保存
                    self._last_condition_details = result.additional_data.get('condition_details', {})
                    if result.valid:
                        return result
            
            # どのパターンも合格しなかった場合
            # 最後に評価されたパターンの条件詳細を保持
            last_condition_details = {}
            if hasattr(self, '_last_condition_details'):
                last_condition_details = self._last_condition_details
            
            return GateResult(
                valid=False,
                pattern="no_valid_pattern",
                confidence=0.0,
                passed_conditions=[],
                failed_conditions=[],
                additional_data={'condition_details': last_condition_details},
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"GATE 1 評価エラー: {e}")
            return GateResult(
                valid=False,
                pattern="error",
                confidence=0.0,
                passed_conditions=[],
                failed_conditions=[],
                additional_data={'error': str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    @measure_async_time('gate2_evaluation_time')
    async def _evaluate_gate2(self, symbol: str, data: Dict[str, Any], gate1_result: GateResult) -> GateResult:
        """GATE 2: シナリオ選定の評価"""
        try:
            patterns = self.pattern_loader.load_gate_patterns(2)
            
            # GATE 1の結果に基づいて有効なシナリオを特定
            valid_scenarios = self._get_valid_scenarios_for_environment(gate1_result.pattern, patterns)
            
            # 評価されたシナリオの詳細情報を保存
            evaluated_scenarios = []
            last_condition_details = {}
            
            for scenario_name in valid_scenarios:
                if scenario_name in patterns.get('patterns', {}):
                    scenario_config = patterns['patterns'][scenario_name]
                    result = await self._evaluate_scenario(scenario_name, scenario_config, data, gate1_result)
                    
                    # シナリオの評価結果を記録
                    scenario_info = {
                        'name': scenario_name,
                        'valid': result.valid,
                        'confidence': result.confidence,
                        'passed_conditions': result.passed_conditions,
                        'failed_conditions': result.failed_conditions,
                        'condition_details': result.additional_data.get('condition_details', {})
                    }
                    evaluated_scenarios.append(scenario_info)
                    
                    # 最後に評価されたシナリオの条件詳細を保存
                    last_condition_details = result.additional_data.get('condition_details', {})
                    
                    if result.valid:
                        # 環境情報をadditional_dataに追加
                        result.additional_data['gate1_environment'] = gate1_result.pattern
                        return result
            
            # どのシナリオも合格しなかった場合
            return GateResult(
                valid=False,
                pattern="no_valid_scenario",
                confidence=0.0,
                passed_conditions=[],
                failed_conditions=[],
                additional_data={
                    'evaluated_scenarios': evaluated_scenarios,
                    'condition_details': last_condition_details,
                    'total_scenarios_evaluated': len(evaluated_scenarios)
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"GATE 2 評価エラー: {e}")
            return GateResult(
                valid=False,
                pattern="error",
                confidence=0.0,
                passed_conditions=[],
                failed_conditions=[],
                additional_data={'error': str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    @measure_async_time('gate3_evaluation_time')
    async def _evaluate_gate3(self, symbol: str, data: Dict[str, Any], gate2_result: GateResult) -> GateResult:
        """GATE 3: トリガーの評価"""
        try:
            patterns = self.pattern_loader.load_gate_patterns(3)
            self.logger.info(f"GATE 3 パターン数: {len(patterns.get('patterns', {}))}")
            
            # GATE 1の結果から環境を取得
            gate1_environment = gate2_result.additional_data.get('gate1_environment', None)
            if not gate1_environment:
                # gate2_resultから環境を推測（fallback）
                gate1_environment = "trending_market (bearish)"  # デフォルト
                self.logger.warning(f"GATE 1環境情報が見つかりません。デフォルト使用: {gate1_environment}")
            
            for pattern_name, pattern_config in patterns.get('patterns', {}).items():
                # 環境制限をチェック
                allowed_environments = pattern_config.get('allowed_environments', [])
                if allowed_environments and gate1_environment not in allowed_environments:
                    self.logger.info(f"GATE 3 パターンスキップ: {pattern_name} - 環境制限 ({gate1_environment} not in {allowed_environments})")
                    continue
                
                self.logger.info(f"GATE 3 パターン評価: {pattern_name}")
                result = await self._evaluate_pattern_variant(
                    pattern_name, pattern_config, data, 'trigger'
                )
                self.logger.info(f"GATE 3 パターン結果: {pattern_name} - 有効: {result.valid}, 信頼度: {result.confidence:.2f}")
                if result.valid:
                    return result
            
            # どのトリガーも合格しなかった場合
            return GateResult(
                valid=False,
                pattern="no_valid_trigger",
                confidence=0.0,
                passed_conditions=[],
                failed_conditions=[],
                additional_data={},
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"GATE 3 評価エラー: {e}")
            return GateResult(
                valid=False,
                pattern="error",
                confidence=0.0,
                passed_conditions=[],
                failed_conditions=[],
                additional_data={'error': str(e)},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def _evaluate_pattern_variant(self, pattern_name: str, pattern_config: Dict[str, Any], 
                                      data: Dict[str, Any], variant: str) -> GateResult:
        """パターンバリアントの評価"""
        conditions = pattern_config.get('conditions', [])
        confidence_config = pattern_config.get('confidence_calculation', {})
        min_confidence = confidence_config.get('min_confidence', 0.6)
        required_conditions = pattern_config.get('required_conditions', [])  # 必須条件
        
        passed_conditions = []
        failed_conditions = []
        condition_details = {}  # 条件の詳細情報を保存
        total_score = 0.0
        total_weight = 0.0
        
        for condition in conditions:
            try:
                condition_name = condition.get('name', 'unknown')
                translated_name = self._translate_condition_name(condition_name)
                self.logger.info(f"条件評価開始: {translated_name}")
                score = await self.condition_evaluator.evaluate_condition(data, condition)
                weight = condition.get('weight', 1.0)
                
                self.logger.info(f"条件評価結果: {translated_name} - スコア: {score:.2f}, 重み: {weight}")
                
                total_score += score * weight
                total_weight += weight
                
                # 条件の詳細情報を作成
                condition_detail = self._create_condition_detail(condition, data, score)
                condition_name = condition['name']
                translated_name = self._translate_condition_name(condition_name)
                condition_details[translated_name] = condition_detail
                
                self.logger.info(f"条件詳細作成: {translated_name} - {condition_detail}")
                
                if score >= 0.5:  # 50%以上で合格とみなす
                    passed_conditions.append(translated_name)
                else:
                    failed_conditions.append(translated_name)
                    
            except Exception as e:
                condition_name = condition.get('name', 'unknown')
                translated_name = self._translate_condition_name(condition_name)
                self.logger.warning(f"条件評価エラー: {translated_name} - {e}")
                failed_conditions.append(translated_name)
                condition_details[translated_name] = f"エラー: {e}"
        
        confidence = total_score / total_weight if total_weight > 0 else 0.0
        
        # 必須条件のチェック
        required_conditions_met = True
        if required_conditions:
            for required_condition in required_conditions:
                if required_condition not in passed_conditions:
                    required_conditions_met = False
                    self.logger.warning(f"必須条件 '{required_condition}' が不合格")
                    break
        
        valid = confidence >= min_confidence and required_conditions_met
        
        self.logger.info(f"GateResult作成前 - condition_details: {condition_details}")
        
        result = GateResult(
            valid=valid,
            pattern=f"{pattern_name}_{variant}",
            confidence=confidence,
            passed_conditions=passed_conditions,
            failed_conditions=failed_conditions,
            additional_data={
                **pattern_config.get('additional_data', {}),
                'condition_details': condition_details
            },
            timestamp=datetime.now(timezone.utc)
        )
        
        self.logger.info(f"GateResult作成後 - additional_data: {result.additional_data}")
        
        return result
    
    async def _evaluate_scenario(self, scenario_name: str, scenario_config: Dict[str, Any], 
                               data: Dict[str, Any], gate1_result: GateResult) -> GateResult:
        """シナリオの評価"""
        # 環境条件による分岐処理
        environment_conditions = scenario_config.get('environment_conditions', {})
        
        if environment_conditions:
            # 環境に応じたシナリオバリアントを評価
            for env_name, env_config in environment_conditions.items():
                if self._matches_environment(env_name, gate1_result.pattern):
                    result = await self._evaluate_pattern_variant(
                        scenario_name, env_config, data, env_name
                    )
                    if result.valid:
                        return result
        else:
            # 直接的な条件評価
            return await self._evaluate_pattern_variant(scenario_name, scenario_config, data, 'direct')
        
        return GateResult(
            valid=False,
            pattern=f"{scenario_name}_no_match",
            confidence=0.0,
            passed_conditions=[],
            failed_conditions=[],
            additional_data={},
            timestamp=datetime.now(timezone.utc)
        )
    
    def _get_valid_scenarios_for_environment(self, environment: str, patterns: Dict[str, Any]) -> List[str]:
        """環境に応じた有効なシナリオを取得"""
        environment_mapping = patterns.get('environment_mapping', {})
        
        # 環境名の正規化（_bullish, _bearish を除去）
        normalized_env = environment.replace('_bullish', '').replace('_bearish', '')
        
        if normalized_env in environment_mapping:
            return environment_mapping[normalized_env]
        
        # デフォルトのマッピング
        default_mapping = {
            'trending_market': ['pullback_setup', 'breakout_setup'],
            'trend_reversal': ['first_pullback'],
            'ranging_market': ['range_boundary']
        }
        
        return default_mapping.get(normalized_env, [])
    
    def _create_condition_detail(self, condition: Dict[str, Any], data: Dict[str, Any], score: float) -> str:
        """条件の詳細情報を作成"""
        try:
            indicator_name = condition.get('indicator')
            operator = condition.get('operator')
            reference = condition.get('reference')
            value = condition.get('value')
            timeframe = condition.get('timeframe', '1d')
            
            # 指標値の取得（時間足プレフィックスを考慮）
            if indicator_name is None:
                return "N/A"
            indicator_value = self._get_indicator_value(data, indicator_name, timeframe)
            if indicator_value is None:
                indicator_value = 'N/A'
            
            # 参照値の取得（時間足プレフィックスを考慮）
            if reference:
                reference_value = self._get_indicator_value(data, reference, timeframe)
                if reference_value is None and value is not None:
                    reference_value = value
            elif value is not None:
                reference_value = value
            else:
                reference_value = 'N/A'
            
            # multiplierの処理
            if 'multiplier' in condition:
                if isinstance(reference_value, (int, float)):
                    reference_value = reference_value * condition['multiplier']
            
            # 条件の詳細文字列を作成
            if operator in ['>', '<', '>=', '<=', '==', '!=']:
                detail = f"{indicator_name}({indicator_value}) {operator} {reference_value}"
            elif operator in ['between', 'not_between']:
                detail = f"{indicator_name}({indicator_value}) {operator} {reference_value}"
            elif operator == 'near':
                tolerance = condition.get('tolerance', 0.01)
                detail = f"{indicator_name}({indicator_value}) near {reference_value} (±{tolerance})"
            else:
                detail = f"{indicator_name}({indicator_value}) {operator} {reference_value}"
            
            # スコアを追加
            detail += f" [スコア: {score:.2f}]"
            
            return detail
            
        except Exception as e:
            return f"条件詳細作成エラー: {e}"
    
    def _log_condition_details(self, gate_name: str, gate_result: GateResult):
        """条件の詳細情報をログ出力"""
        condition_details = gate_result.additional_data.get('condition_details', {})
        
        if condition_details:
            self.logger.info(f"   🔍 {gate_name} 条件詳細:")
            for condition_name, detail in condition_details.items():
                if condition_name in gate_result.passed_conditions:
                    self.logger.info(f"      ✅ {condition_name}: {detail}")
                else:
                    self.logger.info(f"      ❌ {condition_name}: {detail}")
    
    def _log_failed_gate_details(self, gate_name: str, result: GateResult):
        """不合格ゲートの詳細情報をログ出力"""
        self.logger.info(f"   🔍 {gate_name} 不合格詳細:")
        
        # GATE 2の特別処理：評価されたシナリオの詳細表示
        if gate_name == "GATE 2" and 'evaluated_scenarios' in result.additional_data:
            evaluated_scenarios = result.additional_data['evaluated_scenarios']
            total_scenarios = result.additional_data.get('total_scenarios_evaluated', 0)
            
            self.logger.info(f"      📋 評価されたシナリオ数: {total_scenarios}")
            
            for i, scenario in enumerate(evaluated_scenarios, 1):
                scenario_name_jp = self._translate_pattern_name(scenario['name'])
                status_icon = "✅" if scenario['valid'] else "❌"
                self.logger.info(f"      {i}. {status_icon} {scenario_name_jp} (信頼度: {scenario['confidence']:.2f})")
                
                # 各シナリオの条件詳細を表示
                if scenario['condition_details']:
                    self.logger.info(f"         📊 条件詳細:")
                    for condition_name, detail in scenario['condition_details'].items():
                        condition_status = "✅" if condition_name in scenario['passed_conditions'] else "❌"
                        self.logger.info(f"            {condition_status} {condition_name}: {detail}")
                
                # 合格/不合格条件の要約
                if scenario['passed_conditions']:
                    self.logger.info(f"         ✅ 合格条件: {', '.join(scenario['passed_conditions'])}")
                if scenario['failed_conditions']:
                    self.logger.info(f"         ❌ 不合格条件: {', '.join(scenario['failed_conditions'])}")
                
                self.logger.info("")  # 空行で区切り
        
        # 通常の失敗条件表示
        elif result.failed_conditions:
            self.logger.info(f"      ❌ 失敗条件: {', '.join(result.failed_conditions)}")
        
        # 通常の合格条件表示
        if result.passed_conditions:
            self.logger.info(f"      ✅ 合格条件: {', '.join(result.passed_conditions)}")
        
        # 条件の詳細情報を表示（GATE 2以外の場合）
        if gate_name != "GATE 2":
            condition_details = result.additional_data.get('condition_details', {})
            if condition_details:
                self.logger.info(f"      📊 条件詳細:")
                for condition_name, detail in condition_details.items():
                    status = "✅" if condition_name in result.passed_conditions else "❌"
                    self.logger.info(f"         {status} {condition_name}: {detail}")
            else:
                self.logger.info(f"      📊 条件詳細: 詳細情報なし")
        
        # パターン名の詳細表示
        if result.pattern and result.pattern not in ["no_valid_pattern", "no_valid_scenario", "no_valid_trigger"]:
            self.logger.info(f"      🎯 評価されたパターン: {self._translate_pattern_name(result.pattern)}")
            self.logger.info(f"      📈 信頼度: {result.confidence:.2f}")
        
        # 推奨アクションの表示
        self._log_recommended_actions(gate_name, result)
    
    def _log_recommended_actions(self, gate_name: str, result: GateResult):
        """推奨アクションの表示"""
        self.logger.info(f"      💡 推奨アクション:")
        
        if gate_name == "GATE 1":
            if "trending_market" in result.pattern:
                self.logger.info(f"         - より強いトレンドを待つ")
                self.logger.info(f"         - ADX値の上昇を確認")
            elif "trend_reversal" in result.pattern:
                self.logger.info(f"         - 転換シグナルの強化を待つ")
                self.logger.info(f"         - MACDの明確な転換を確認")
            elif "ranging_market" in result.pattern:
                self.logger.info(f"         - レンジ相場の継続を確認")
                self.logger.info(f"         - ブレイクアウトを待つ")
        
        elif gate_name == "GATE 2":
            if "pullback" in result.pattern:
                self.logger.info(f"         - より深い押し目を待つ")
                self.logger.info(f"         - RSIの過熱度を確認")
            elif "breakout" in result.pattern:
                self.logger.info(f"         - より強い圧縮を待つ")
                self.logger.info(f"         - ボリンジャーバンドの収束を確認")
        
        elif gate_name == "GATE 3":
            self.logger.info(f"         - より明確なトリガーを待つ")
            self.logger.info(f"         - 価格アクションの確認")
    
    def _matches_environment(self, env_name: str, pattern: str) -> bool:
        """環境名とパターンの一致チェック"""
        env_mapping = {
            'trending_bull': 'trending_market_bullish',
            'trending_bear': 'trending_market_bearish',
            'trend_reversal': 'trend_reversal',
            'ranging_market': 'ranging_market'
        }
        
        expected_pattern = env_mapping.get(env_name)
        return bool(expected_pattern and expected_pattern in pattern)
    
    def _determine_signal_type(self, gate1: GateResult, gate2: GateResult, gate3: Optional[GateResult]) -> str:
        """シグナルタイプの決定"""
        # GATE 1の環境に基づく基本判定
        if 'bullish' in gate1.pattern:
            return 'BUY'
        elif 'bearish' in gate1.pattern:
            return 'SELL'
        elif 'neutral' in gate1.pattern or 'ranging' in gate1.pattern:
            # レンジ相場の場合は、GATE 3のパターンと価格アクションで判定
            return self._determine_ranging_signal_type(gate1, gate2, gate3)
        else:
            return 'NEUTRAL'
    
    def _determine_ranging_signal_type(self, gate1: GateResult, gate2: GateResult, gate3: Optional[GateResult]) -> str:
        """レンジ相場でのシグナルタイプ決定"""
        # GATE 3が未提供の場合はゲート2から推定（安全ガード）
        if gate3 is None or not getattr(gate3, 'pattern', None):
            # 簡易推定：range_boundary → NEUTRAL（方向未確定）、breakout_setup → BUY（仮）
            if 'breakout' in gate2.pattern:
                return 'BUY'
            return 'NEUTRAL'

        # GATE 3のパターンに基づく判定
        if gate3 and gate3.pattern:
            if 'price_action_reversal' in gate3.pattern:
                # 価格アクション反転パターンの場合、RSIとMACDで方向を決定
                return self._determine_reversal_direction(gate1, gate2, gate3)
            elif 'momentum_confirmation' in gate3.pattern:
                # モメンタム確認パターンの場合、MACDで方向を決定
                return self._determine_momentum_direction(gate1, gate2, gate3)
        
        return 'NEUTRAL'
    
    def _determine_reversal_direction(self, gate1: GateResult, gate2: GateResult, gate3: Optional[GateResult]) -> str:
        """反転パターンでの方向決定"""
        if not gate3:
            return 'NEUTRAL'
            
        # 現在の価格とEMA21の関係で判定
        # 実際のデータはgate3のadditional_dataから取得する必要がある
        # 簡易的な判定として、GATE 2のシナリオに基づく
        if 'range_boundary' in gate2.pattern:
            # レンジ境界での反転は、現在の価格位置で判定
            # 実際の実装では、より詳細な価格分析が必要
            return 'BUY'  # デフォルトでBUY（後で改善）
        return 'NEUTRAL'
    
    def _determine_momentum_direction(self, gate1: GateResult, gate2: GateResult, gate3: Optional[GateResult]) -> str:
        """モメンタムパターンでの方向決定"""
        if not gate3:
            return 'NEUTRAL'
            
        # MACDの方向性で判定
        # 実際の実装では、MACDの値を取得して判定
        return 'BUY'  # デフォルトでBUY（後で改善）
    
    def _calculate_entry_price(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult) -> float:
        """エントリー価格の計算（現在価格ベース）"""
        # 時間足プレフィックス付きのclose価格を取得
        current_price = 0.0
        for timeframe in ['5m', '1h', '4h', '1d']:
            close_key = f'{timeframe}_close'
            if close_key in data:
                current_price = data[close_key]
                break
        
        # フォールバック：プレフィックスなしのclose
        if current_price == 0.0:
            current_price = data.get('close', 0.0)
        
        # 現在価格をそのままエントリー価格として使用
        return current_price
    
    def _calculate_stop_loss(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult, entry_price: float) -> float:
        """ストップロスの計算（ATR下限＋サポレジ/Fib/MA/BBスナップ）"""
        # ATR値を取得（複数時間足で試行）
        atr = None
        for timeframe in ['1h', '4h', '5m', '1d']:
            atr = self._get_indicator_value(data, 'ATR_14', timeframe)
            if atr and atr > 0:
                self.logger.info(f"ATR取得成功: {timeframe}足 ATR_14 = {atr:.6f}")
                break
        
        if not atr or atr <= 0:
            atr = 0.01
            self.logger.warning(f"ATR取得失敗、デフォルト値使用: {atr}")
        
        # シグナルタイプを判定
        signal_type = self._determine_signal_type(gate1, gate2, None)
        
        # ATR下限を計算
        min_risk_atr = atr * self.atr_multiplier_min
        min_risk_price = self.min_risk_pips * 0.0001  # pips to price
        atr_based_distance = max(min_risk_atr, min_risk_price)
        
        self.logger.info(f"リスク管理計算: ATR={atr:.6f}, ATR下限={min_risk_atr:.6f}, 最小pips={min_risk_price:.6f}, 採用距離={atr_based_distance:.6f}")
        
        # レベル抽出
        sr_levels = self._extract_support_resistance_levels(data)
        fib_levels = self._extract_fibonacci_levels(data)
        
        if signal_type == 'BUY':
            # 買いの場合：エントリー価格より下のサポートレベルを検索
            support_candidates = sr_levels['support'] + fib_levels['retracement']
            nearest_support = self._find_nearest_level(entry_price, support_candidates, 'below', self.buffer_pips)
            
            if nearest_support:
                # サポートレベルからバッファ分下にSLを設定
                buffer_price = self.buffer_pips * 0.0001
                support_sl = nearest_support - buffer_price
                # ATR下限との比較
                atr_sl = entry_price - atr_based_distance
                return max(support_sl, atr_sl)  # より保守的な方（価格に近い方）
            else:
                # フォールバック：ATRベース
                return entry_price - atr_based_distance
                
        elif signal_type == 'SELL':
            # 売りの場合：エントリー価格より上のレジスタンスレベルを検索
            resistance_candidates = sr_levels['resistance'] + fib_levels['extension']
            nearest_resistance = self._find_nearest_level(entry_price, resistance_candidates, 'above', self.buffer_pips)
            
            if nearest_resistance:
                # レジスタンスレベルからバッファ分上にSLを設定
                buffer_price = self.buffer_pips * 0.0001
                resistance_sl = nearest_resistance + buffer_price
                # ATR下限との比較
                atr_sl = entry_price + atr_based_distance
                return min(resistance_sl, atr_sl)  # より保守的な方（価格に近い方）
            else:
                # フォールバック：ATRベース
                return entry_price + atr_based_distance
        else:
            # NEUTRALの場合はデフォルトで買い方向
            return entry_price - atr_based_distance
    
    def _calculate_take_profit(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult, entry_price: float) -> List[float]:
        """テイクプロフィットの計算（ATR下限＋サポレジ/Fib/MA/BBスナップ）"""
        # ATR値を取得（複数時間足で試行）
        atr = None
        for timeframe in ['1h', '4h', '5m', '1d']:
            atr = self._get_indicator_value(data, 'ATR_14', timeframe)
            if atr and atr > 0:
                break
        
        if not atr or atr <= 0:
            atr = 0.01
        
        # シグナルタイプを判定
        signal_type = self._determine_signal_type(gate1, gate2, None)
        
        # レベル抽出
        sr_levels = self._extract_support_resistance_levels(data)
        fib_levels = self._extract_fibonacci_levels(data)
        
        take_profits = []
        
        if signal_type == 'BUY':
            # 買いの場合：エントリー価格より上のレジスタンスレベルを検索
            resistance_candidates = sr_levels['resistance'] + fib_levels['extension']
            
            # 各R倍率でTPを計算
            for ratio in self.take_profit_ratios:
                atr_tp = entry_price + (atr * ratio)
                
                # 近くのレジスタンスレベルを検索
                nearest_resistance = self._find_nearest_level(entry_price, resistance_candidates, 'above', 0)
                
                if nearest_resistance and abs(nearest_resistance - atr_tp) < atr * 0.5:
                    # レジスタンスレベルが近い場合は、そこからバッファ分下に設定
                    buffer_price = self.buffer_pips * 0.0001
                    tp_price = nearest_resistance - buffer_price
                else:
                    # フォールバック：ATRベース
                    tp_price = atr_tp
                
                take_profits.append(tp_price)
                
        elif signal_type == 'SELL':
            # 売りの場合：エントリー価格より下のサポートレベルを検索
            support_candidates = sr_levels['support'] + fib_levels['retracement']
            
            # 各R倍率でTPを計算
            for ratio in self.take_profit_ratios:
                atr_tp = entry_price - (atr * ratio)
                
                # 近くのサポートレベルを検索
                nearest_support = self._find_nearest_level(entry_price, support_candidates, 'below', 0)
                
                if nearest_support and abs(nearest_support - atr_tp) < atr * 0.5:
                    # サポートレベルが近い場合は、そこからバッファ分上に設定
                    buffer_price = self.buffer_pips * 0.0001
                    tp_price = nearest_support + buffer_price
                else:
                    # フォールバック：ATRベース
                    tp_price = atr_tp
                
                take_profits.append(tp_price)
        else:
            # NEUTRALの場合はデフォルトで買い方向
            for ratio in self.take_profit_ratios:
                take_profits.append(entry_price + (atr * ratio))
        
        return take_profits
        


# テスト用のメイン関数
if __name__ == "__main__":
    import asyncio
    
    async def test_three_gate_engine():
        """ThreeGateEngineのテスト"""
        # ログレベルを設定
        logging.basicConfig(level=logging.INFO)
        
        engine = ThreeGateEngine()
        
        # テスト用のデータ（より現実的な値）
        test_data = {
            'close': 150.0,
            'EMA_200': 148.0,  # 価格がEMA_200より上（上昇トレンド）
            'ADX': 30.0,       # 強いトレンド
            'MACD': 0.1,
            'MACD_Signal': 0.05,  # MACD > MACD_Signal
            'ATR_14': 0.5,
            'EMA_21': 149.0,
            'EMA_55': 147.0,
            'RSI_14': 45.0,    # 30-70の範囲内
            'Stochastic_14': 60.0,  # 過熱感なし
            'Volume_Ratio': 1.2,
            'Bollinger_Bands_Upper': 152.0,
            'Bollinger_Bands_Lower': 148.0,
            'Bollinger_Bands_Middle': 150.0,
            'bollinger_width': 0.02,  # ボリンジャーバンド幅（圧縮状態）
            'historical_min_width': 0.025,  # 過去最小幅
            'range_high': 152.0,  # レンジ上限
            'range_low': 148.0,   # レンジ下限
            'scenario_support': 149.0,  # シナリオサポート
            'scenario_resistance': 151.0,  # シナリオレジスタンス
            'scenario_level': 151.0,  # シナリオレベル
            'candle_lower_shadow': 0.5,  # ローソク足下ヒゲ
            'candle_upper_shadow': 0.2,  # ローソク足上ヒゲ
            'candle_body': 0.3,  # ローソク足実体
            'candle_bullish': True,  # 陽線
            'candle_bearish': False,  # 陰線
            'previous_candle_bullish': False,  # 前足陽線
            'previous_candle_bearish': True,  # 前足陰線
            'current_candle': 'bullish',  # 現在の足
            'previous_candle': 'bearish'  # 前の足
        }
        
        print("🔍 テストデータ:")
        for key, value in test_data.items():
            print(f"   {key}: {value}")
        print()
        
        result = await engine.evaluate("USDJPY=X", test_data)
        
        if result:
            print(f"✅ 三層ゲート合格: {result.signal_type}")
            print(f"   総合信頼度: {result.overall_confidence:.2f}")
            print(f"   GATE 1: {result.gate1.pattern} ({result.gate1.confidence:.2f})")
            print(f"   GATE 2: {result.gate2.pattern} ({result.gate2.confidence:.2f})")
            if result.gate3 and result.gate3.pattern:
                print(f"   GATE 3: {result.gate3.pattern} ({result.gate3.confidence:.2f})")
            else:
                print(f"   GATE 3: 未評価")
        else:
            print("❌ 三層ゲート不合格")
            print("詳細な原因を確認するため、各ゲートの結果を個別に確認します...")
            
            # 各ゲートの個別テスト
            print("\n🔍 GATE 1 個別テスト:")
            gate1_result = await engine._evaluate_gate1("USDJPY=X", test_data)
            print(f"   結果: {gate1_result.valid}")
            print(f"   パターン: {gate1_result.pattern}")
            print(f"   信頼度: {gate1_result.confidence:.2f}")
            print(f"   合格条件: {gate1_result.passed_conditions}")
            print(f"   不合格条件: {gate1_result.failed_conditions}")
            
            if gate1_result.valid:
                print("\n🔍 GATE 2 個別テスト:")
                gate2_result = await engine._evaluate_gate2("USDJPY=X", test_data, gate1_result)
                print(f"   結果: {gate2_result.valid}")
                print(f"   パターン: {gate2_result.pattern}")
                print(f"   信頼度: {gate2_result.confidence:.2f}")
                print(f"   合格条件: {gate2_result.passed_conditions}")
                print(f"   不合格条件: {gate2_result.failed_conditions}")
                
                if gate2_result.valid:
                    print("\n🔍 GATE 3 個別テスト:")
                    gate3_result = await engine._evaluate_gate3("USDJPY=X", test_data, gate2_result)
                    print(f"   結果: {gate3_result.valid}")
                    print(f"   パターン: {gate3_result.pattern}")
                    print(f"   信頼度: {gate3_result.confidence:.2f}")
                    print(f"   合格条件: {gate3_result.passed_conditions}")
                    print(f"   不合格条件: {gate3_result.failed_conditions}")
    
    # テスト実行
    asyncio.run(test_three_gate_engine())
