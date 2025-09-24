#!/usr/bin/env python3
"""
階層的テクニカル指標計算器

運用方針に基づく3段階のテクニカル分析:
1. 大局判断（D1・H4）: トレンド方向の確定
2. 戦術判断（H1）: エントリーゾーンの特定
3. 執行判断（M5）: エントリータイミングの最適化
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

try:
    import talib
except ImportError:
    talib = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger(__name__)


class TechnicalIndicatorCalculator:
    """階層的テクニカル指標計算器"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # フィボナッチ設定
        self.fibonacci_config = {
            "trend_direction": {  # 大局判断（D1・H4）
                "1d": {
                    "swing_periods": [20, 50, 100],
                    "levels": [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0],
                    "extensions": [1.272, 1.414, 1.618, 2.0]
                },
                "4h": {
                    "swing_periods": [10, 20, 40],
                    "levels": [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0],
                    "extensions": [1.272, 1.414, 1.618]
                }
            },
            "zone_decision": {  # 戦術判断（H1）
                "1h": {
                    "swing_periods": [5, 10, 20],
                    "levels": [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0],
                    "extensions": [1.272, 1.414]
                }
            },
            "timing_execution": {  # 執行判断（M5）
                "5m": {
                    "swing_periods": [3, 5, 10],
                    "levels": [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0],
                    "extensions": [1.272]
                }
            }
        }
        
        # 運用方針に基づく指標設定
        self.indicator_config = {
            "trend_direction": {  # 大局判断（D1・H4）
                "timeframes": ["1d", "4h"],
                "indicators": {
                    "EMA_21": 21,
                    "EMA_55": 55,
                    "EMA_200": 200,
                    "MACD": (12, 26, 9),
                    "ATR_14": 14,
                    "RSI_14": 14
                }
            },
            "zone_decision": {  # 戦術判断（H1）
                "timeframes": ["1h"],
                "indicators": {
                    "EMA_21": 21,
                    "EMA_55": 55,
                    "MACD": (12, 26, 9),
                    "ATR_14": 14,
                    "RSI_14": 14,
                    "Bollinger": (20, 2.0),
                    "Stochastic": (14, 3, 3),
                    "Williams_R": 14
                }
            },
            "timing_execution": {  # 執行判断（M5）
                "timeframes": ["5m"],
                "indicators": {
                    "EMA_21": 21,
                    "RSI_14": 14,
                    "RSI_7": 7,
                    "Stochastic": (14, 3, 3),
                    "Williams_R": 14,
                    "ATR_14": 14,
                    "Volume_SMA_20": 20
                }
            },
            "trend_reinforcement": {  # トレンド補強（全時間足）
                "timeframes": ["5m", "15m", "1h", "4h", "1d"],
                "indicators": {
                    "EMA_21": 21,
                    "MACD": (12, 26, 9),
                    "ATR_14": 14,
                    "RSI_14": 14
                }
            }
        }
    
    def calculate_all_indicators(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """全時間足のテクニカル指標を計算"""
        self.logger.info("📊 階層的テクニカル指標計算開始")
        
        result = {}
        
        for timeframe, df in data.items():
            self.logger.info(f"⏰ {timeframe}足の指標計算中...")
            
            # データの基本チェック
            if not self._validate_data(df):
                self.logger.warning(f"⚠️ {timeframe}足のデータが無効です")
                continue
            
            # 指標計算
            df_with_indicators = self._calculate_timeframe_indicators(df, timeframe)
            result[timeframe] = df_with_indicators
            
            self.logger.info(f"✅ {timeframe}足: {len(df_with_indicators.columns)}個の指標を計算")
        
        self.logger.info("📊 階層的テクニカル指標計算完了")
        return result
    
    def _validate_data(self, df: pd.DataFrame) -> bool:
        """データの妥当性チェック"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        if df.empty:
            return False
        
        for col in required_columns:
            if col not in df.columns:
                self.logger.error(f"❌ 必須カラム '{col}' が見つかりません")
                return False
        
        # データ型をfloat64に変換（TA-Libの要求）
        for col in required_columns:
            if col in df.columns:
                df[col] = df[col].astype(np.float64)
        
        # データの基本統計チェック
        if df['close'].isna().all():
            self.logger.error("❌ 価格データが全てNaNです")
            return False
        
        # Volumeデータの可用性チェック
        self._check_volume_availability(df)
        
        return True
    
    def _check_volume_availability(self, df: pd.DataFrame) -> bool:
        """Volumeデータの可用性をチェック"""
        volume_available = not (df['volume'] == 0).all()
        
        if not volume_available:
            # Volumeデータが利用できない場合は警告を非表示（Yahoo Finance APIの制限）
            # self.logger.warning("⚠️ Volumeデータが利用できません（すべて0.0）")
            # Volume関連の指標を無効化
            df['volume_available'] = False
        else:
            df['volume_available'] = True
            self.logger.info("✅ Volumeデータが利用可能です")
        
        return volume_available
    
    def _calculate_timeframe_indicators(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """時間足別の指標計算"""
        df_result = df.copy()
        
        # 1. トレンド系指標
        df_result = self._calculate_trend_indicators(df_result)
        
        # 2. モメンタム系指標
        df_result = self._calculate_momentum_indicators(df_result)
        
        # 3. ボラティリティ系指標
        df_result = self._calculate_volatility_indicators(df_result)
        
        # 4. ボリューム系指標
        df_result = self._calculate_volume_indicators(df_result)
        
        # 5. フィボナッチ指標
        df_result = self._calculate_fibonacci_indicators(df_result, timeframe)
        
        # 6. 時間足固有の指標
        df_result = self._calculate_timeframe_specific_indicators(df_result, timeframe)
        
        # 7. ローソク足分析指標
        df_result = self._calculate_candle_analysis_indicators(df_result)
        
        return df_result
    
    def _calculate_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """トレンド系指標の計算"""
        try:
            # EMA (Exponential Moving Average)
            df['EMA_21'] = talib.EMA(df['close'], timeperiod=21)
            df['EMA_55'] = talib.EMA(df['close'], timeperiod=55)
            df['EMA_200'] = talib.EMA(df['close'], timeperiod=200)
            
            # SMA (Simple Moving Average)
            df['SMA_20'] = talib.SMA(df['close'], timeperiod=20)
            df['SMA_50'] = talib.SMA(df['close'], timeperiod=50)
            df['SMA_200'] = talib.SMA(df['close'], timeperiod=200)
            
            # MACD (Moving Average Convergence Divergence)
            macd, macd_signal, macd_hist = talib.MACD(
                df['close'], fastperiod=12, slowperiod=26, signalperiod=9
            )
            df['MACD'] = macd
            df['MACD_Signal'] = macd_signal
            df['MACD_Histogram'] = macd_hist
            
            # ADX (Average Directional Index)
            df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            df['ADXR'] = talib.ADXR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # トレンド方向の判定
            df['Trend_Direction'] = self._determine_trend_direction(df)
            
        except Exception as e:
            self.logger.error(f"❌ トレンド系指標計算エラー: {e}")
        
        return df
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """モメンタム系指標の計算"""
        try:
            # RSI (Relative Strength Index)
            df['RSI_14'] = talib.RSI(df['close'], timeperiod=14)
            df['RSI_21'] = talib.RSI(df['close'], timeperiod=21)
            df['RSI_7'] = talib.RSI(df['close'], timeperiod=7)
            
            # Stochastic Oscillator
            slowk, slowd = talib.STOCH(
                df['high'], df['low'], df['close'],
                fastk_period=14, slowk_period=3, slowd_period=3
            )
            df['Stochastic_K'] = slowk
            df['Stochastic_D'] = slowd
            
            # Williams %R
            df['Williams_R'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # モメンタム状態の判定
            df['Momentum_State'] = self._determine_momentum_state(df)
            
        except Exception as e:
            self.logger.error(f"❌ モメンタム系指標計算エラー: {e}")
        
        return df
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """ボラティリティ系指標の計算"""
        try:
            # ATR (Average True Range)
            df['ATR_14'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            df['ATR_21'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=21)
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
            )
            df['BB_Upper'] = bb_upper
            df['BB_Middle'] = bb_middle
            df['BB_Lower'] = bb_lower
            
            # Bollinger Band Position
            df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            # Bollinger Band Width
            df['bollinger_width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
            
            # ボラティリティ状態の判定
            df['Volatility_State'] = self._determine_volatility_state(df)
            
        except Exception as e:
            self.logger.error(f"❌ ボラティリティ系指標計算エラー: {e}")
        
        return df
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """ボリューム系指標の計算"""
        try:
            # Volume SMA
            df['Volume_SMA_20'] = df['volume'].rolling(window=20).mean()
            df['Volume_SMA_50'] = df['volume'].rolling(window=50).mean()
            
            # Volume Ratio (ゼロ除算を回避)
            df['Volume_Ratio'] = np.where(
                df['Volume_SMA_20'] != 0,
                df['volume'] / df['Volume_SMA_20'],
                1.0  # Volume_SMA_20が0の場合は1.0を返す
            )
            
            # OBV (On Balance Volume)
            df['OBV'] = talib.OBV(df['close'], df['volume'])
            
            # ボリューム状態の判定
            df['Volume_State'] = self._determine_volume_state(df)
            
        except Exception as e:
            self.logger.error(f"❌ ボリューム系指標計算エラー: {e}")
        
        return df
    
    def _calculate_fibonacci_indicators(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """フィボナッチ指標の計算"""
        try:
            # 時間足別のフィボナッチ設定を取得
            fib_config = self._get_fibonacci_config(timeframe)
            if not fib_config:
                return df
            
            # スイングポイントの特定
            swing_points = self._identify_swing_points(df, fib_config['swing_periods'])
            
            # フィボナッチレベルの計算
            fib_levels = self._calculate_fibonacci_levels(swing_points, fib_config['levels'])
            fib_extensions = self._calculate_fibonacci_extensions(swing_points, fib_config['extensions'])
            
            # データフレームに追加
            for level, value in fib_levels.items():
                df[f'Fib_{level}'] = value
            
            for ext, value in fib_extensions.items():
                df[f'Fib_Ext_{ext}'] = value
            
            # フィボナッチ位置の判定
            df['Fibonacci_Position'] = self._determine_fibonacci_position(df, fib_levels)
            
        except Exception as e:
            self.logger.error(f"❌ フィボナッチ指標計算エラー ({timeframe}): {e}")
        
        return df
    
    def _get_fibonacci_config(self, timeframe: str) -> Optional[Dict]:
        """時間足別のフィボナッチ設定を取得"""
        for analysis_type, configs in self.fibonacci_config.items():
            if timeframe in configs:
                return configs[timeframe]
        return None
    
    def _identify_swing_points(self, df: pd.DataFrame, swing_periods: List[int]) -> Dict:
        """スイングポイントの特定"""
        swing_points = {}
        
        for period in swing_periods:
            # ローカルハイ・ローを特定
            window = period * 2 + 1
            if window > len(df):
                continue
                
            highs = df['high'].rolling(window=window, center=True).max()
            lows = df['low'].rolling(window=window, center=True).min()
            
            # スイングハイ・ローの条件を緩和
            swing_highs = df[df['high'] >= highs * 0.999].dropna()  # 0.1%の許容誤差
            swing_lows = df[df['low'] <= lows * 1.001].dropna()     # 0.1%の許容誤差
            
            # 最低限のデータがあるかチェック
            if len(swing_highs) > 0 and len(swing_lows) > 0:
                swing_points[f'period_{period}'] = {
                    'swing_highs': swing_highs,
                    'swing_lows': swing_lows
                }
        
        return swing_points
    
    def _calculate_fibonacci_levels(self, swing_points: Dict, levels: List[float]) -> Dict:
        """フィボナッチレベルの計算"""
        fib_levels = {}
        
        # 最新のスイングポイントを使用
        latest_swing = None
        for period_key, points in swing_points.items():
            if not points['swing_highs'].empty and not points['swing_lows'].empty:
                latest_swing = points
                break
        
        if not latest_swing:
            return fib_levels
        
        # 最新のスイングハイ・ローを取得
        latest_high = latest_swing['swing_highs'].iloc[-1]['high']
        latest_low = latest_swing['swing_lows'].iloc[-1]['low']
        
        # フィボナッチレベルを計算
        diff = latest_high - latest_low
        for level in levels:
            fib_levels[level] = latest_high - (diff * level)
        
        return fib_levels
    
    def _calculate_fibonacci_extensions(self, swing_points: Dict, extensions: List[float]) -> Dict:
        """フィボナッチエクステンションの計算"""
        fib_extensions = {}
        
        # 最新のスイングポイントを使用
        latest_swing = None
        for period_key, points in swing_points.items():
            if not points['swing_highs'].empty and not points['swing_lows'].empty:
                latest_swing = points
                break
        
        if not latest_swing:
            return fib_extensions
        
        # 最新のスイングハイ・ローを取得
        latest_high = latest_swing['swing_highs'].iloc[-1]['high']
        latest_low = latest_swing['swing_lows'].iloc[-1]['low']
        
        # フィボナッチエクステンションを計算
        diff = latest_high - latest_low
        for ext in extensions:
            fib_extensions[ext] = latest_high + (diff * (ext - 1.0))
        
        return fib_extensions
    
    def _determine_fibonacci_position(self, df: pd.DataFrame, fib_levels: Dict) -> pd.Series:
        """フィボナッチ位置の判定"""
        if not fib_levels:
            return pd.Series('UNKNOWN', index=df.index)
        
        current_price = df['close']
        position = pd.Series('UNKNOWN', index=df.index)
        
        # フィボナッチレベルとの関係を判定
        for i, (level, price) in enumerate(sorted(fib_levels.items())):
            if i == 0:
                # 最初のレベル
                position[current_price >= price] = f'ABOVE_{level}'
            else:
                # 前のレベルとの間
                prev_level = sorted(fib_levels.items())[i-1][0]
                prev_price = sorted(fib_levels.items())[i-1][1]
                mask = (current_price >= price) & (current_price < prev_price)
                position[mask] = f'BETWEEN_{prev_level}_{level}'
        
        return position
    
    def _calculate_timeframe_specific_indicators(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """時間足固有の指標計算"""
        try:
            # 時間足別の特別な処理
            if timeframe in ["1d", "4h"]:  # 大局判断
                df = self._calculate_trend_direction_indicators(df)
            elif timeframe == "1h":  # 戦術判断
                df = self._calculate_zone_decision_indicators(df)
            elif timeframe == "5m":  # 執行判断
                df = self._calculate_timing_execution_indicators(df)
            
            # 全時間足共通のトレンド補強指標
            df = self._calculate_trend_reinforcement_indicators(df)
            
        except Exception as e:
            self.logger.error(f"❌ 時間足固有指標計算エラー ({timeframe}): {e}")
        
        return df
    
    def _calculate_trend_direction_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """大局判断指標の計算"""
        try:
            # 長期トレンドの強度
            df['Long_Trend_Strength'] = self._calculate_trend_strength(df, periods=[21, 55, 200])
            
            # トレンドの一貫性
            df['Trend_Consistency'] = self._calculate_trend_consistency(df)
            
        except Exception as e:
            self.logger.error(f"❌ 大局判断指標計算エラー: {e}")
        
        return df
    
    def _calculate_zone_decision_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """戦術判断指標の計算"""
        try:
            # エントリーゾーンの特定
            df['Entry_Zone'] = self._identify_entry_zones(df)
            
            # サポート・レジスタンスレベル
            df['Support_Level'] = self._calculate_support_level(df)
            df['Resistance_Level'] = self._calculate_resistance_level(df)
            
        except Exception as e:
            self.logger.error(f"❌ 戦術判断指標計算エラー: {e}")
        
        return df
    
    def _calculate_timing_execution_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """執行判断指標の計算"""
        try:
            # エントリータイミング
            df['Entry_Timing'] = self._identify_entry_timing(df)
            
            # 短期モメンタム
            df['Short_Momentum'] = self._calculate_short_momentum(df)
            
        except Exception as e:
            self.logger.error(f"❌ 執行判断指標計算エラー: {e}")
        
        return df
    
    def _calculate_trend_reinforcement_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """トレンド補強指標の計算"""
        try:
            # トレンドの補強度
            df['Trend_Reinforcement'] = self._calculate_trend_reinforcement_strength(df)
            
            # 逆張り条件の判定
            df['Counter_Trend_Condition'] = self._check_counter_trend_conditions(df)
            
        except Exception as e:
            self.logger.error(f"❌ トレンド補強指標計算エラー: {e}")
        
        return df
    
    # 判定ロジック
    def _determine_trend_direction(self, df: pd.DataFrame) -> pd.Series:
        """トレンド方向の判定"""
        conditions = [
            (df['EMA_21'] > df['EMA_55']) & (df['EMA_55'] > df['EMA_200']),  # 上昇
            (df['EMA_21'] < df['EMA_55']) & (df['EMA_55'] < df['EMA_200']),  # 下降
        ]
        choices = ['BULLISH', 'BEARISH']
        return pd.Series(np.select(conditions, choices, default='SIDEWAYS'), index=df.index)
    
    def _determine_momentum_state(self, df: pd.DataFrame) -> pd.Series:
        """モメンタム状態の判定"""
        conditions = [
            (df['RSI_14'] > 70) | (df['Stochastic_K'] > 80),  # オーバーボート
            (df['RSI_14'] < 30) | (df['Stochastic_K'] < 20),  # オーバーソール
        ]
        choices = ['OVERBOUGHT', 'OVERSOLD']
        return pd.Series(np.select(conditions, choices, default='NEUTRAL'), index=df.index)
    
    def _determine_volatility_state(self, df: pd.DataFrame) -> pd.Series:
        """ボラティリティ状態の判定"""
        atr_percentile = df['ATR_14'].rolling(window=50).rank(pct=True)
        conditions = [
            atr_percentile > 0.8,  # 高ボラティリティ
            atr_percentile < 0.2,  # 低ボラティリティ
        ]
        choices = ['HIGH', 'LOW']
        return pd.Series(np.select(conditions, choices, default='NORMAL'), index=df.index)
    
    def _determine_volume_state(self, df: pd.DataFrame) -> pd.Series:
        """ボリューム状態の判定"""
        conditions = [
            df['Volume_Ratio'] > 1.5,  # 高ボリューム
            df['Volume_Ratio'] < 0.5,  # 低ボリューム
        ]
        choices = ['HIGH', 'LOW']
        return pd.Series(np.select(conditions, choices, default='NORMAL'), index=df.index)
    
    # 補助メソッド
    def _calculate_trend_strength(self, df: pd.DataFrame, periods: List[int]) -> pd.Series:
        """トレンド強度の計算"""
        # 複数期間のEMAの傾きを計算
        trend_scores = []
        for period in periods:
            ema_col = f'EMA_{period}'
            if ema_col in df.columns:
                slope = df[ema_col].diff(5)  # 5期間の変化
                trend_scores.append(slope)
        
        if trend_scores:
            # 平均トレンド強度
            return pd.Series(np.mean(trend_scores, axis=0), index=df.index)
        else:
            return pd.Series(0, index=df.index)
    
    def _calculate_trend_consistency(self, df: pd.DataFrame) -> pd.Series:
        """トレンド一貫性の計算"""
        # EMA間の一貫性を計算
        ema_21_slope = df['EMA_21'].diff(5)
        ema_55_slope = df['EMA_55'].diff(5)
        ema_200_slope = df['EMA_200'].diff(5)
        
        # 符号の一致度を計算
        consistency = (
            (ema_21_slope * ema_55_slope > 0).astype(int) +
            (ema_21_slope * ema_200_slope > 0).astype(int) +
            (ema_55_slope * ema_200_slope > 0).astype(int)
        ) / 3
        
        return consistency
    
    def _identify_entry_zones(self, df: pd.DataFrame) -> pd.Series:
        """エントリーゾーンの特定"""
        # サポート・レジスタンスレベルとの関係
        conditions = [
            df['close'] < df['BB_Lower'],  # 売りゾーン
            df['close'] > df['BB_Upper'],  # 買いゾーン
        ]
        choices = ['SELL_ZONE', 'BUY_ZONE']
        return pd.Series(np.select(conditions, choices, default='NEUTRAL'), index=df.index)
    
    def _calculate_support_level(self, df: pd.DataFrame) -> pd.Series:
        """サポートレベルの計算"""
        # 過去20期間の最安値
        return df['low'].rolling(window=20).min()
    
    def _calculate_resistance_level(self, df: pd.DataFrame) -> pd.Series:
        """レジスタンスレベルの計算"""
        # 過去20期間の最高値
        return df['high'].rolling(window=20).max()
    
    def _identify_entry_timing(self, df: pd.DataFrame) -> pd.Series:
        """エントリータイミングの特定"""
        # RSIとStochasticの組み合わせ
        conditions = [
            (df['RSI_14'] < 30) & (df['Stochastic_K'] < 20),  # 買いタイミング
            (df['RSI_14'] > 70) & (df['Stochastic_K'] > 80),  # 売りタイミング
        ]
        choices = ['BUY_TIMING', 'SELL_TIMING']
        return pd.Series(np.select(conditions, choices, default='WAIT'), index=df.index)
    
    def _calculate_short_momentum(self, df: pd.DataFrame) -> pd.Series:
        """短期モメンタムの計算"""
        # RSI_7の変化率
        return df['RSI_7'].diff(3)
    
    def _calculate_trend_reinforcement_strength(self, df: pd.DataFrame) -> pd.Series:
        """トレンド補強強度の計算"""
        # MACDとEMAの組み合わせ
        macd_bullish = (df['MACD'] > df['MACD_Signal']) & (df['EMA_21'] > df['EMA_55'])
        macd_bearish = (df['MACD'] < df['MACD_Signal']) & (df['EMA_21'] < df['EMA_55'])
        
        conditions = [macd_bullish, macd_bearish]
        choices = [1, -1]
        return pd.Series(np.select(conditions, choices, default=0), index=df.index)
    
    def _check_counter_trend_conditions(self, df: pd.DataFrame) -> pd.Series:
        """逆張り条件のチェック"""
        # 上位足の反転サインが必要
        # ここでは簡易的な実装
        rsi_oversold = df['RSI_14'] < 30
        rsi_overbought = df['RSI_14'] > 70
        
        conditions = [rsi_oversold, rsi_overbought]
        choices = ['COUNTER_BUY', 'COUNTER_SELL']
        return pd.Series(np.select(conditions, choices, default='NONE'), index=df.index)
    
    def _calculate_candle_analysis_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """ローソク足分析指標の計算"""
        # ローソク足の基本情報
        df['candle_body'] = abs(df['close'] - df['open'])
        df['candle_upper_shadow'] = df['high'] - np.maximum(df['open'], df['close'])
        df['candle_lower_shadow'] = np.minimum(df['open'], df['close']) - df['low']
        df['candle_bullish'] = df['close'] > df['open']
        df['candle_bearish'] = df['close'] < df['open']
        
        # 前のローソク足との比較
        df['previous_candle_bullish'] = df['candle_bullish'].shift(1)
        df['previous_candle_bearish'] = df['candle_bearish'].shift(1)
        
        # エンガルフィングパターンの判定
        df['current_candle'] = df['close'] - df['open']
        df['previous_candle'] = df['current_candle'].shift(1)
        
        # ローソク足のサイズ分析
        df['candle_body_size'] = df['candle_body']
        df['average_body_size'] = df['candle_body'].rolling(window=20).mean()
        
        return df
    
    def get_analysis_summary(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """分析結果のサマリーを取得"""
        summary = {}
        
        for timeframe, df in data.items():
            if df.empty:
                continue
            
            latest = df.iloc[-1]
            
            summary[timeframe] = {
                'trend_direction': latest.get('Trend_Direction', 'UNKNOWN'),
                'momentum_state': latest.get('Momentum_State', 'UNKNOWN'),
                'volatility_state': latest.get('Volatility_State', 'UNKNOWN'),
                'volume_state': latest.get('Volume_State', 'UNKNOWN'),
                'rsi_14': latest.get('RSI_14', 0),
                'atr_14': latest.get('ATR_14', 0),
                'ema_21': latest.get('EMA_21', 0),
                'close': latest.get('close', 0),
                'timestamp': latest.name if hasattr(latest, 'name') else None
            }
        
        return summary
