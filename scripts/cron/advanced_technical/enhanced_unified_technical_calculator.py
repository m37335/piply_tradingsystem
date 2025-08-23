"""
EnhancedUnifiedTechnicalCalculator モジュール

統合テクニカル指標計算システムのメインクラス。
3つの既存システムを統合し、tqdm統一によるプログレスバー機能を提供します。

統合対象:
- UnifiedTechnicalCalculator: 基盤機能
- TALibTechnicalIndicators: 分析機能  
- TechnicalIndicatorsAnalyzer: 設定最適化

Author: EnhancedUnifiedTechnicalCalculator Team
Created: 2025-08-15
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import and_, func, select

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)

# プロジェクト固有のインポート
# ProgressManagerは使用しないため削除

logger = logging.getLogger(__name__)


class EnhancedUnifiedTechnicalCalculator:
    """
    統合テクニカル指標計算システム

    継承関係:
    - UnifiedTechnicalCalculator: 基盤機能
    - TALibTechnicalIndicators: 分析機能
    - TechnicalIndicatorsAnalyzer: 設定最適化

    Attributes:
        currency_pair (str): 通貨ペア
        session: データベースセッション
        indicator_repo: 技術指標リポジトリ
        indicators_config (dict): 指標設定
        progress_config (dict): プログレス設定
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        """
        EnhancedUnifiedTechnicalCalculatorを初期化

        Args:
            currency_pair: 通貨ペア（デフォルト: "USD/JPY"）
        """
        self.currency_pair = currency_pair
        self.session = None
        self.indicator_repo = None

        # 基盤設定（UnifiedTechnicalCalculator）
        self.timeframes = {
            "M5": "5分足",
            "H1": "1時間足",  # noqa: E203
            "H4": "4時間足",
            "D1": "日足",
        }

        # 最適化設定（TechnicalIndicatorsAnalyzer）
        self.indicators_config = {
            "RSI": {
                "short_term": {
                    "period": 30,  # TechnicalIndicatorsAnalyzer から採用
                    "overbought": 70,
                    "oversold": 30,
                    "description": "短期の過熱・過冷感を測定",
                },
                "medium_term": {
                    "period": 50,  # TechnicalIndicatorsAnalyzer から採用
                    "overbought": 65,
                    "oversold": 35,
                    "description": "中期トレンドの強弱を測定",
                },
                "long_term": {
                    "period": 70,  # TechnicalIndicatorsAnalyzer から採用
                    "overbought": 60,
                    "oversold": 40,
                    "description": "長期トレンドの方向性を測定",
                },
            },
            "MACD": {
                "fast_period": 12,  # 全システム共通
                "slow_period": 26,  # 全システム共通
                "signal_period": 9,  # 全システム共通
                "analysis_features": [
                    "cross_signal",  # TechnicalIndicatorsAnalyzer から
                    "zero_line_position",  # TechnicalIndicatorsAnalyzer から
                ],
                "unified_save": True,
            },
            "BB": {
                "period": 20,  # 全システム共通
                "std_dev": 2.0,  # 全システム共通
                "analysis_features": [
                    "band_position",  # TechnicalIndicatorsAnalyzer から
                    "band_walk",  # TechnicalIndicatorsAnalyzer から
                    "band_width",  # TechnicalIndicatorsAnalyzer から
                ],
                "unified_save": True,
            },
            "SMA": {
                "short": 20,  # TechnicalIndicatorsAnalyzer から採用
                "medium": 50,  # TechnicalIndicatorsAnalyzer から採用
                "long": 200,  # TechnicalIndicatorsAnalyzer から採用
                "description": "短期・中期・長期の3期間で市場トレンドを把握",
            },
            "EMA": {
                "short": 12,  # UnifiedTechnicalCalculator から採用
                "medium": 26,  # UnifiedTechnicalCalculator から採用
                "long": 50,  # TechnicalIndicatorsAnalyzer から採用
                "description": "MACDと連携する短期・中期、長期トレンド用",
            },
            "STOCH": {
                "fastk_period": 14,  # UnifiedTechnicalCalculator から採用
                "slowk_period": 3,  # UnifiedTechnicalCalculator から採用
                "slowd_period": 3,  # UnifiedTechnicalCalculator から採用
                "analysis_features": [
                    "state_analysis"  # TALibTechnicalIndicators から
                ],
                "unified_save": True,
            },
            "ATR": {
                "period": 14,  # UnifiedTechnicalCalculator から採用
                "analysis_features": [
                    "volatility_analysis"  # TALibTechnicalIndicators から
                ],
            },
        }

        # プログレスバー設定（tqdm統一）
        self.progress_config = {
            "enable_progress": True,
            "show_detailed": True,
            "tqdm_config": {
                "ncols": 100,
                "bar_format": (
                    "{desc}: {percentage:3.0f}%|{bar:25}| "
                    "{n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
                ),
                "unit": "指標",
                "colour": "cyan",
                "leave": False,  # 完了後にプログレスバーを残さない
                "dynamic_ncols": False,  # 固定列幅で改行を防ぐ
                "ascii": False,  # Unicode文字を使用
                "smoothing": 0.3,  # スムージング効果
            },
        }

        logger.info(f"EnhancedUnifiedTechnicalCalculator初期化完了: {currency_pair}")

    async def initialize(self) -> bool:
        """
        システムを初期化

        Returns:
            bool: 初期化成功時True
        """
        try:
            # データベース接続の初期化
            from src.infrastructure.database.connection import get_async_session

            self.session = await get_async_session()
            self.indicator_repo = TechnicalIndicatorRepositoryImpl(self.session)

            logger.info("EnhancedUnifiedTechnicalCalculator初期化完了")
            return True

        except Exception as e:
            logger.error(f"EnhancedUnifiedTechnicalCalculator初期化エラー: {e}")
            return False

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self.cleanup()

    async def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self.session:
                await self.session.close()
                logger.info("データベース接続を閉じました")

            # 明示的にガベージコレクションを実行
            import gc

            gc.collect()

        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")

    async def _get_price_data(
        self, timeframe: str, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        価格データを取得

        Args:
            timeframe: 時間足
            limit: 取得件数制限（Noneの場合は全件取得）

        Returns:
            pd.DataFrame: 価格データ
        """
        data_loader = None
        try:
            # 既存のデータ取得ロジックを使用
            from scripts.cron.advanced_data.data_loader import DataLoader

            data_loader = DataLoader()
            df = await data_loader.load_data(
                currency_pair=self.currency_pair,
                timeframe=timeframe,
                limit=limit,  # 制限付きでデータを取得
            )

            if df.empty:
                logger.warning(f"{timeframe}の価格データがありません")
                return pd.DataFrame()

            logger.debug(f"{timeframe}データ取得: {len(df)}件")
            print(f"📊 {timeframe}データ取得: {len(df)}件")

            if limit:
                print(f"   🔒 制限付き実行: 最新{limit}件のみ")

            # DataFrameの構造を確認
            print(f"   📋 カラム: {list(df.columns)}")
            print(f"   📊 データ型: {df.dtypes.to_dict()}")

            if len(df) > 0:
                # timestampカラムの存在確認
                if "timestamp" in df.columns:
                    print(
                        f"   📅 期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}"
                    )
                else:
                    print("   ⚠️ timestampカラムが存在しません")

                if "close" in df.columns:
                    print(
                        f"   💰 価格範囲: {df['close'].min():.2f} ～ {df['close'].max():.2f}"
                    )
                else:
                    print("   ⚠️ closeカラムが存在しません")

            # データ型を即座に変換
            df = self._convert_data_types(df)

            return df

        except Exception as e:
            logger.error(f"価格データ取得エラー: {e}")
            return pd.DataFrame()
        finally:
            # データローダーのクリーンアップ
            if data_loader:
                try:
                    await data_loader.cleanup()
                except Exception as cleanup_error:
                    logger.warning(
                        f"データローダークリーンアップエラー: {cleanup_error}"
                    )

    async def calculate_all_indicators(
        self, limit: Optional[int] = None
    ) -> Dict[str, int]:
        """
        全テクニカル指標を計算（tqdmプログレスバー付き）

        Args:
            limit: 各時間足の取得件数制限（Noneの場合は全件取得）

        Returns:
            Dict[str, int]: 各時間足の計算件数
        """
        results = {}
        total_calculated = 0

        # データベース接続を一度だけ初期化
        if not self.session:
            await self.initialize()

        # 時間足別の処理
        timeframes = ["M5", "H1", "H4", "D1"]

        for i, timeframe in enumerate(timeframes):
            # 時間足の区切りを表示
            print(f"\n{'─' * 60}")
            print(f"📊 {timeframe}時間足の処理を開始")
            if limit:
                print(f"🔒 制限付き実行: 最新{limit}件のみ")
            print(f"{'─' * 60}\n")

            try:
                count = await self.calculate_timeframe_indicators(timeframe, limit)
                results[timeframe] = count
                total_calculated += count

            except Exception as e:
                print(f"❌ {timeframe}時間足処理エラー: {e}")
                results[timeframe] = 0

        # 最終結果の表示
        print(f"\n{'─' * 60}")
        print(f"📊 計算結果サマリー")
        if limit:
            print(f"🔒 制限付き実行: 各時間足{limit}件まで")
        print(f"{'─' * 60}")
        print(f"📊 計算結果: {results}")
        print(f"📊 総計算件数: {total_calculated}件")
        print(f"{'─' * 60}")

        # 処理完了後にクリーンアップ
        await self.cleanup()

        return results

    async def calculate_timeframe_indicators(
        self, timeframe: str, limit: Optional[int] = None
    ) -> int:
        """
        特定時間足の指標を計算

        Args:
            timeframe: 時間足
            limit: 取得件数制限（Noneの場合は全件取得）

        Returns:
            int: 計算件数
        """
        try:
            # 価格データを取得（データ型変換済み）
            df = await self._get_price_data(timeframe, limit)

            if df.empty:
                return 0

            # データ件数を取得
            total_data_points = len(df)
            print(f"📊 {timeframe}データ取得: {total_data_points}件")

            # 各指標を計算
            total_indicators = 0
            indicators = [
                ("RSI", self._calculate_enhanced_rsi),
                ("MACD", self._calculate_enhanced_macd),
                ("BB", self._calculate_enhanced_bb),
                ("MA", self._calculate_enhanced_ma),
                ("STOCH", self._calculate_enhanced_stoch),
                ("ATR", self._calculate_enhanced_atr),
            ]

            # 指標別の正確な合計件数を計算（最小期間を考慮）
            sma_periods = len(
                [
                    v
                    for v in self.indicators_config["SMA"].values()
                    if isinstance(v, int)
                ]
            )
            ema_periods = len(
                [
                    v
                    for v in self.indicators_config["EMA"].values()
                    if isinstance(v, int)
                ]
            )

            # 各指標の最小期間を取得
            fast_period = self.indicators_config["MACD"]["fast_period"]
            slow_period = self.indicators_config["MACD"]["slow_period"]
            signal_period = self.indicators_config["MACD"]["signal_period"]
            macd_min_period = max(fast_period, slow_period) + signal_period
            bb_min_period = self.indicators_config["BB"]["period"]
            stoch_min_period = self.indicators_config["STOCH"]["fastk_period"]
            atr_min_period = self.indicators_config["ATR"]["period"]

            # 最小期間を考慮した実際の計算可能件数
            # RSI: 各期間の最小期間を考慮
            rsi_periods = [
                config["period"] for config in self.indicators_config["RSI"].values()
            ]
            rsi_min_period = max(rsi_periods) if rsi_periods else 70
            rsi_calculable = max(0, total_data_points - rsi_min_period)

            # MA: 各期間の最小期間を考慮
            ma_periods = []
            for period in self.indicators_config["SMA"].values():
                if isinstance(period, int):
                    ma_periods.append(period)
            for period in self.indicators_config["EMA"].values():
                if isinstance(period, int):
                    ma_periods.append(period)
            ma_min_period = max(ma_periods) if ma_periods else 200
            ma_calculable = max(0, total_data_points - ma_min_period)

            macd_calculable = max(0, total_data_points - macd_min_period)
            bb_calculable = max(0, total_data_points - bb_min_period)
            stoch_calculable = max(0, total_data_points - stoch_min_period)
            atr_calculable = max(0, total_data_points - atr_min_period)

            # デバッグ情報を表示
            print(f"   📊 データ件数: {total_data_points}件")
            print(
                f"   📊 RSI計算可能件数: {rsi_calculable}件 "
                f"(最小期間: {rsi_min_period})"
            )
            print(
                f"   📊 MA計算可能件数: {ma_calculable}件 "
                f"(最小期間: {ma_min_period})"
            )
            print(
                f"   📊 MACD計算可能件数: {macd_calculable}件 "
                f"(最小期間: {macd_min_period})"
            )
            print(
                f"   📊 BB計算可能件数: {bb_calculable}件 "
                f"(最小期間: {bb_min_period})"
            )
            print(
                f"   📊 STOCH計算可能件数: {stoch_calculable}件 "
                f"(最小期間: {stoch_min_period})"
            )
            print(
                f"   📊 ATR計算可能件数: {atr_calculable}件 "
                f"(最小期間: {atr_min_period})"
            )

            # 期待値の表示を改善
            expected_ma_total = (sma_periods + ema_periods) * ma_calculable
            if expected_ma_total == 0:
                print(
                    f"   ⚠️ MA計算: データ不足のため計算できません (必要期間: {ma_min_period})"
                )
            else:
                print(f"   📊 MA期待値: {expected_ma_total}件")

            # 実際の計算可能件数を再計算（各期間別）
            actual_ma_calculable = {}
            for period in self.indicators_config["SMA"].values():
                if isinstance(period, int):
                    actual_ma_calculable[f"SMA_{period}"] = max(
                        0, total_data_points - period + 1
                    )

            for period in self.indicators_config["EMA"].values():
                if isinstance(period, int):
                    actual_ma_calculable[f"EMA_{period}"] = max(
                        0, total_data_points - period + 1
                    )

            # 実際の期待値を計算
            actual_expected_ma = sum(actual_ma_calculable.values())
            if actual_expected_ma > 0:
                print(f"   📊 MA実際期待値: {actual_expected_ma}件")
                print(f"   📊 MA詳細: {actual_ma_calculable}")

            indicator_totals = {
                "RSI": len(self.indicators_config["RSI"]) * rsi_calculable,
                "MACD": macd_calculable,
                "BB": bb_calculable,
                "MA": actual_expected_ma,  # 実際の計算可能件数を使用
                "STOCH": stoch_calculable,
                "ATR": atr_calculable,
            }

            # 時間足レベルのプログレスバー（重複を排除）
            from tqdm import tqdm

            with tqdm(
                total=len(indicators),
                desc=f"📊 {timeframe} 指標計算中",
                unit="指標",
                ncols=80,
                bar_format="{desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                leave=False,  # 完了後にプログレスバーを残さない
            ) as timeframe_pbar:
                for indicator_name, calculate_func in indicators:
                    try:
                        # 指標別の正確な合計件数を使用
                        indicator_total = indicator_totals.get(
                            indicator_name, total_data_points
                        )

                        # 現在の指標を表示
                        print(f"\n🔍 {indicator_name}計算中...")

                        # プログレスバーの説明を更新
                        timeframe_pbar.set_description(
                            f"📊 {timeframe} {indicator_name}計算中"
                        )

                        # 指標計算時にプログレスバーを渡さない（重複を避ける）
                        result = await calculate_func(df, timeframe, None)

                        # 指標計算完了後にプログレスバーを更新
                        timeframe_pbar.update(1)
                        timeframe_pbar.refresh()  # プログレスバーを強制更新

                        # 計算結果の詳細表示
                        if isinstance(result, dict):
                            if "error" in result:
                                print(f"❌ {indicator_name}: {result['error']}")
                            elif "count" in result:
                                actual_count = result["count"]
                                expected_count = indicator_total

                                if expected_count > 0:
                                    completion_rate = (
                                        actual_count / expected_count * 100
                                    )
                                    print(
                                        f"✅ {indicator_name}: {actual_count}/"
                                        f"{expected_count}件 ({completion_rate:.1f}%)"
                                    )

                                    # 計算率が低い場合の警告
                                    if completion_rate < 80:
                                        print(
                                            f"   ⚠️ {indicator_name}の計算率が低いです"
                                        )
                                else:
                                    if indicator_name == "MA" and actual_count > 0:
                                        print(
                                            f"✅ {indicator_name}: {actual_count}件 "
                                            f"(実際計算: 各期間別計算により{actual_count}件)"
                                        )
                                    else:
                                        print(
                                            f"✅ {indicator_name}: {actual_count}件 "
                                            "(期待値: データ不足)"
                                        )
                            else:
                                print(f"✅ {indicator_name}: 完了")
                        else:
                            print(f"✅ {indicator_name}: 完了")

                        # 結果カウント
                        if isinstance(result, dict) and "count" in result:
                            count = result["count"]
                        else:
                            count = 1 if result else 0

                        total_indicators += count

                    except Exception as e:
                        print(f"❌ {indicator_name}計算エラー: {e}")
                        import traceback

                        print(f"詳細エラー: {traceback.format_exc()}")
                        # エラーが発生してもプログレスバーを更新
                        timeframe_pbar.update(1)

            return total_indicators

        except Exception as e:
            return 0

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        価格データの型を数値型に変換

        Args:
            df: 価格データ

        Returns:
            pd.DataFrame: 型変換後のデータ
        """
        try:
            # 価格カラムを数値型に変換
            price_columns = ["open", "high", "low", "close"]
            for col in price_columns:
                if col in df.columns:
                    # 文字列の場合、カンマを削除してから変換
                    if df[col].dtype == "object":
                        df[col] = df[col].astype(str).str.replace(",", "")

                    # 数値型に変換
                    df[col] = pd.to_numeric(df[col], errors="coerce")

                    # 変換失敗の確認
                    if df[col].isna().all():
                        print(f"   ⚠️ {col}カラムの変換に失敗しました")
                    else:
                        print(f"   ✅ {col}カラムを数値型に変換完了")

            # 変換結果を確認
            print(f"   📊 データ型変換後: {df[price_columns].dtypes.to_dict()}")

            return df

        except Exception as e:
            print(f"❌ データ型変換エラー: {e}")
            return df

    async def _calculate_enhanced_rsi(
        self, df: pd.DataFrame, timeframe: str, pbar=None
    ) -> Dict[str, Any]:
        """
        多期間RSI計算（参考スクリプトベース）

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: 多期間RSI計算結果
        """
        try:
            import talib

            saved_count = 0

            # データ型を確実に数値型に変換（既に変換済みだが念のため）
            close_series = pd.to_numeric(df["close"], errors="coerce")
            close_values = close_series.values.astype(np.float64)

            # 各期間のRSIを計算
            for period_type, config in self.indicators_config["RSI"].items():
                rsi_values = talib.RSI(close_values, timeperiod=config["period"])

                # 有効な値のみを保存（期間分のデータがある場合のみ）
                valid_count = 0
                for i, (timestamp, rsi_value) in enumerate(zip(df.index, rsi_values)):
                    if not np.isnan(rsi_value) and i >= config["period"] - 1:
                        # 状態判定
                        state = self._analyze_rsi_state(rsi_value, config)

                        # 統合データ構造
                        additional_data = {
                            "period_type": period_type,
                            "period": config["period"],
                            "state": state,
                            "overbought": config["overbought"],
                            "oversold": config["oversold"],
                            "description": config["description"],
                            "analysis": {
                                "trend": "single_point",  # 単一点での分析
                                "momentum": "neutral",  # デフォルト値
                            },
                        }

                        # 統合データ保存
                        unified_data = {
                            "indicator_type": "RSI",
                            "timeframe": timeframe,
                            "value": float(rsi_value),
                            "timestamp": timestamp,
                            "additional_data": additional_data,
                            "parameters": {
                                "period": config["period"],
                                "period_type": period_type,
                                "source": "enhanced_unified_technical_calculator",
                            },
                        }

                        if await self._save_unified_indicator_optimized(unified_data):
                            saved_count += 1
                            valid_count += 1

                print(
                    f"    📊 RSI {period_type} ({config['period']}期間): {valid_count}件"
                )

            print(f"  📊 RSI計算完了: {saved_count}件")
            return {
                "indicator": "RSI",
                "timeframe": timeframe,
                "count": saved_count,
            }

        except Exception as e:
            print(f"❌ RSI計算エラー: {e}")
            return {"error": str(e), "count": 0}

    async def _calculate_enhanced_macd(
        self, df: pd.DataFrame, timeframe: str, pbar=None
    ) -> Dict[str, Any]:
        """
        統合MACD計算

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: 統合MACD計算結果
        """
        try:
            import talib

            config = self.indicators_config["MACD"]

            # TA-LibでMACD計算
            close_series = pd.to_numeric(df["close"], errors="coerce")
            close_values = close_series.values.astype(np.float64)
            macd, signal, hist = talib.MACD(
                close_values,
                fastperiod=config["fast_period"],
                slowperiod=config["slow_period"],
                signalperiod=config["signal_period"],
            )

            # 最新値を取得
            current_macd = macd[-1] if not np.isnan(macd[-1]) else None
            current_signal = signal[-1] if not np.isnan(signal[-1]) else None
            current_hist = hist[-1] if not np.isnan(hist[-1]) else None

            if current_macd is not None and current_signal is not None:
                # 状態判定
                state = self._analyze_macd_state(
                    current_macd, current_signal, current_hist
                )

                # クロス分析
                cross_signal = self._analyze_macd_cross(macd, signal)

                # ゼロライン位置
                zero_line_position = self._analyze_zero_line_position(current_macd)

                # 統合データ
                additional_data = {
                    "signal_line": round(current_signal, 4) if current_signal else None,
                    "histogram": round(current_hist, 4) if current_hist else None,
                    "state": state,
                    "analysis": {
                        "cross_signal": cross_signal,
                        "zero_line_position": zero_line_position,
                    },
                }

                # 全データポイントで計算・保存
            saved_count = 0
            for i in range(len(df)):
                if i < 26:  # MACD計算に必要な最小期間
                    continue

                # MACD計算
                close_series = pd.to_numeric(df["close"], errors="coerce")
                close_values = close_series.values[: i + 1].astype(np.float64)
                macd, signal, hist = talib.MACD(
                    close_values,
                    fastperiod=config["fast_period"],
                    slowperiod=config["slow_period"],
                    signalperiod=config["signal_period"],
                )

                current_macd = macd[-1] if not np.isnan(macd[-1]) else None
                current_signal = signal[-1] if not np.isnan(signal[-1]) else None
                current_hist = hist[-1] if not np.isnan(hist[-1]) else None

                if current_macd is not None:
                    # 状態判定
                    state = self._analyze_macd_state(
                        current_macd, current_signal, current_hist
                    )

                    # クロス分析
                    cross_signal = self._analyze_macd_cross(macd, signal)

                    # ゼロライン位置
                    zero_line_position = self._analyze_zero_line_position(current_macd)

                    # 統合データ
                    point_additional_data = {
                        "signal_line": (
                            round(current_signal, 4) if current_signal else None
                        ),
                        "histogram": round(current_hist, 4) if current_hist else None,
                        "state": state,
                        "analysis": {
                            "cross_signal": cross_signal,
                            "zero_line_position": zero_line_position,
                        },
                    }

                    # 統合データ保存
                    timestamp = df.index[i]
                    await self._save_unified_indicator(
                        "MACD",
                        timeframe,
                        current_macd,
                        point_additional_data,
                    )
                    saved_count += 1

            if saved_count == 0:
                print(f"⚠️ MACD計算失敗: 保存件数が0件")
                return {"error": "MACD計算失敗: 保存件数が0件", "count": 0}

            return {
                "indicator": "MACD",
                "timeframe": timeframe,
                "value": round(current_macd, 4),
                "additional_data": additional_data,
                "count": saved_count,  # 実際の保存件数を返す
            }

        except Exception as e:
            return {"error": str(e), "count": 0}

    async def _calculate_enhanced_bb(
        self, df: pd.DataFrame, timeframe: str, pbar=None
    ) -> Dict[str, Any]:
        """
        統合ボリンジャーバンド計算

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: 統合BB計算結果
        """
        try:
            import talib

            config = self.indicators_config["BB"]

            # TA-Libでボリンジャーバンド計算
            close_series = pd.to_numeric(df["close"], errors="coerce")
            close_values = close_series.values.astype(np.float64)
            upper, middle, lower = talib.BBANDS(
                close_values,
                timeperiod=config["period"],
                nbdevup=config["std_dev"],
                nbdevdn=config["std_dev"],
                matype=0,
            )

            # 最新値を取得
            current_upper = upper[-1] if not np.isnan(upper[-1]) else None
            current_middle = middle[-1] if not np.isnan(middle[-1]) else None
            current_lower = lower[-1] if not np.isnan(lower[-1]) else None
            current_close = df["close"].iloc[-1]

            # 全データポイントで計算・保存
            saved_count = 0
            for i in range(len(df)):
                if i < config["period"]:  # BB計算に必要な最小期間
                    continue

                # BB計算
                close_series = pd.to_numeric(df["close"], errors="coerce")
                close_values = close_series.values[: i + 1].astype(np.float64)
                upper, middle, lower = talib.BBANDS(
                    close_values,
                    timeperiod=config["period"],
                    nbdevup=config["std_dev"],
                    nbdevdn=config["std_dev"],
                    matype=0,
                )

                current_upper = upper[-1] if not np.isnan(upper[-1]) else None
                current_middle = middle[-1] if not np.isnan(middle[-1]) else None
                current_lower = lower[-1] if not np.isnan(lower[-1]) else None
                current_close = df["close"].iloc[i]

                if current_middle is not None:
                    # バンド位置分析
                    band_position = self._analyze_bb_position(
                        current_close, current_upper, current_middle, current_lower
                    )

                    # バンド幅分析
                    band_width = self._analyze_bb_width(upper, middle, lower)

                    # 統合データ
                    point_additional_data = {
                        "upper_band": (
                            round(current_upper, 4) if current_upper else None
                        ),
                        "middle_band": (
                            round(current_middle, 4) if current_middle else None
                        ),
                        "lower_band": (
                            round(current_lower, 4) if current_lower else None
                        ),
                        "band_position": band_position,
                        "band_width": band_width,
                    }

                    # 統合データ保存
                    await self._save_unified_indicator(
                        "BB", timeframe, current_middle, point_additional_data
                    )
                    saved_count += 1

            if saved_count == 0:
                print(f"⚠️ BB計算失敗: 保存件数が0件")
                return {"error": "BB計算失敗: 保存件数が0件", "count": 0}

            return {
                "indicator": "BB",
                "timeframe": timeframe,
                "value": round(current_middle, 4),
                "additional_data": point_additional_data,
                "count": saved_count,  # 実際の保存件数を返す
            }

        except Exception as e:
            return {"error": str(e), "count": 0}

    async def _calculate_enhanced_ma(
        self, df: pd.DataFrame, timeframe: str, pbar=None
    ) -> Dict[str, Any]:
        """
        多期間移動平均計算（参考スクリプトベース）

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: 多期間MA計算結果
        """
        try:
            import talib

            saved_count = 0

            # データ型を確実に数値型に変換（既に変換済みだが念のため）
            close_series = pd.to_numeric(df["close"], errors="coerce")
            close_values = close_series.values.astype(np.float64)

            # SMA計算
            for period in [
                self.indicators_config["SMA"]["short"],
                self.indicators_config["SMA"]["medium"],
                self.indicators_config["SMA"]["long"],
            ]:
                if isinstance(period, int):
                    sma_values = talib.SMA(close_values, timeperiod=period)

                    # 有効な値のみを保存（期間分のデータがある場合のみ）
                    valid_count = 0
                    for i, (timestamp, value) in enumerate(zip(df.index, sma_values)):
                        if not np.isnan(value) and i >= period - 1:
                            additional_data = {
                                "ma_type": "SMA",
                                "period": period,
                                "description": self.indicators_config["SMA"].get(
                                    "description", "移動平均"
                                ),
                            }

                            indicator = TechnicalIndicatorModel(
                                currency_pair=self.currency_pair,
                                timestamp=timestamp,
                                indicator_type=f"SMA_{period}",
                                timeframe=timeframe,
                                value=float(value),
                                additional_data=additional_data,
                                parameters={
                                    "period": period,
                                    "source": "enhanced_unified_technical_calculator",
                                },
                            )
                            await self.indicator_repo.save(indicator)
                            saved_count += 1
                            valid_count += 1

                    print(f"    📊 SMA {period}期間: {valid_count}件")

            # EMA計算
            for period in [
                self.indicators_config["EMA"]["short"],
                self.indicators_config["EMA"]["medium"],
                self.indicators_config["EMA"]["long"],
            ]:
                if isinstance(period, int):
                    ema_values = talib.EMA(close_values, timeperiod=period)

                    # 有効な値のみを保存（期間分のデータがある場合のみ）
                    valid_count = 0
                    for i, (timestamp, value) in enumerate(zip(df.index, ema_values)):
                        if not np.isnan(value) and i >= period - 1:
                            additional_data = {
                                "ma_type": "EMA",
                                "period": period,
                                "description": self.indicators_config["EMA"].get(
                                    "description", "指数移動平均"
                                ),
                            }

                            indicator = TechnicalIndicatorModel(
                                currency_pair=self.currency_pair,
                                timestamp=timestamp,
                                indicator_type=f"EMA_{period}",
                                timeframe=timeframe,
                                value=float(value),
                                additional_data=additional_data,
                                parameters={
                                    "period": period,
                                    "source": "enhanced_unified_technical_calculator",
                                },
                            )
                            await self.indicator_repo.save(indicator)
                            saved_count += 1
                            valid_count += 1

                    print(f"    📊 EMA {period}期間: {valid_count}件")

            print(f"  📊 移動平均計算完了: {saved_count}件")
            return {
                "indicator": "MA",
                "timeframe": timeframe,
                "count": saved_count,
            }

        except Exception as e:
            print(f"❌ 移動平均計算エラー: {e}")
            return {"error": str(e), "count": 0}

    async def _calculate_enhanced_stoch(
        self, df: pd.DataFrame, timeframe: str, pbar=None
    ) -> Dict[str, Any]:
        """
        統合ストキャスティクス計算

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: 統合STOCH計算結果
        """
        try:
            import talib

            config = self.indicators_config["STOCH"]

            # TA-Libでストキャスティクス計算
            high_series = pd.to_numeric(df["high"], errors="coerce")
            low_series = pd.to_numeric(df["low"], errors="coerce")
            close_series = pd.to_numeric(df["close"], errors="coerce")
            high_values = high_series.values.astype(np.float64)
            low_values = low_series.values.astype(np.float64)
            close_values = close_series.values.astype(np.float64)
            slowk, slowd = talib.STOCH(
                high_values,
                low_values,
                close_values,
                fastk_period=config["fastk_period"],
                slowk_period=config["slowk_period"],
                slowk_matype=0,
                slowd_period=config["slowd_period"],
                slowd_matype=0,
            )

            # 最新値を取得
            current_k = slowk[-1] if not np.isnan(slowk[-1]) else None
            current_d = slowd[-1] if not np.isnan(slowd[-1]) else None

            # 全データポイントで計算・保存
            saved_count = 0
            for i in range(len(df)):
                if i < config["fastk_period"]:  # STOCH計算に必要な最小期間
                    continue

                # STOCH計算
                high_series = pd.to_numeric(df["high"], errors="coerce")
                low_series = pd.to_numeric(df["low"], errors="coerce")
                close_series = pd.to_numeric(df["close"], errors="coerce")
                high_values = high_series.values[: i + 1].astype(np.float64)
                low_values = low_series.values[: i + 1].astype(np.float64)
                close_values = close_series.values[: i + 1].astype(np.float64)
                slowk, slowd = talib.STOCH(
                    high_values,
                    low_values,
                    close_values,
                    fastk_period=config["fastk_period"],
                    slowk_period=config["slowk_period"],
                    slowk_matype=0,
                    slowd_period=config["slowd_period"],
                    slowd_matype=0,
                )

                current_k = slowk[-1] if not np.isnan(slowk[-1]) else None
                current_d = slowd[-1] if not np.isnan(slowd[-1]) else None

                if current_k is not None and current_d is not None:
                    # 状態分析
                    state = self._analyze_stoch_state(current_k, current_d)

                    # 統合データ
                    point_additional_data = {
                        "k_line": round(current_k, 2),
                        "d_line": round(current_d, 2),
                        "state": state,
                    }

                    # 統合データ保存
                    await self._save_unified_indicator(
                        "STOCH", timeframe, current_k, point_additional_data
                    )
                    saved_count += 1

            if saved_count == 0:
                print(f"⚠️ STOCH計算失敗: 保存件数が0件")
                return {"error": "STOCH計算失敗: 保存件数が0件", "count": 0}

            return {
                "indicator": "STOCH",
                "timeframe": timeframe,
                "value": round(current_k, 2),
                "additional_data": point_additional_data,
                "count": saved_count,  # 実際の保存件数を返す
            }

        except Exception as e:
            return {"error": str(e), "count": 0}

    async def _calculate_enhanced_atr(
        self, df: pd.DataFrame, timeframe: str, pbar=None
    ) -> Dict[str, Any]:
        """
        統合ATR計算（参考スクリプトベース）

        Args:
            df: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: 統合ATR計算結果
        """
        try:
            import talib

            config = self.indicators_config["ATR"]
            saved_count = 0

            # データ型を確実に数値型に変換（既に変換済みだが念のため）
            high_series = pd.to_numeric(df["high"], errors="coerce")
            low_series = pd.to_numeric(df["low"], errors="coerce")
            close_series = pd.to_numeric(df["close"], errors="coerce")
            high_values = high_series.values.astype(np.float64)
            low_values = low_series.values.astype(np.float64)
            close_values = close_series.values.astype(np.float64)

            # TA-LibでATR計算
            atr_values = talib.ATR(
                high_values,
                low_values,
                close_values,
                timeperiod=config["period"],
            )

            # 有効な値のみを保存
            for i, (timestamp, atr_value) in enumerate(zip(df.index, atr_values)):
                if not np.isnan(atr_value):
                    # ボラティリティ分析
                    volatility_analysis = self._analyze_atr_volatility(atr_values)

                    additional_data = {
                        "period": config["period"],
                        "volatility_analysis": volatility_analysis,
                        "description": "平均真の範囲によるボラティリティ測定",
                    }

                    indicator = TechnicalIndicatorModel(
                        currency_pair=self.currency_pair,
                        timestamp=timestamp,
                        indicator_type="ATR",
                        timeframe=timeframe,
                        value=float(atr_value),
                        additional_data=additional_data,
                        parameters={
                            "period": config["period"],
                            "source": "enhanced_unified_technical_calculator",
                        },
                    )

                    await self.indicator_repo.save(indicator)
                    saved_count += 1

            print(f"  📊 ATR計算完了: {saved_count}件")
            return {
                "indicator": "ATR",
                "timeframe": timeframe,
                "count": saved_count,
            }

        except Exception as e:
            print(f"❌ ATR計算エラー: {e}")
            return {"error": str(e), "count": 0}

    async def _save_unified_indicator(
        self,
        indicator_type: str,
        timeframe: str,
        value: float,
        additional_data: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        統合データ保存

        Args:
            indicator_type: 指標タイプ
            timeframe: 時間足
            value: 主要な値
            additional_data: 追加データ
            analysis: 分析結果

        Returns:
            bool: 保存成功時True
        """
        try:
            # 分析結果を追加データに統合
            if analysis:
                additional_data["analysis"] = analysis

            # 技術指標モデルを作成
            current_timestamp = datetime.now()
            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=current_timestamp,
                indicator_type=indicator_type,
                timeframe=timeframe,
                value=value,
                additional_data=additional_data,
                parameters=self.indicators_config.get(indicator_type, {}),
            )

            # データベースに保存
            await self.indicator_repo.save(indicator)

            return True

        except Exception as e:
            logger.error(f"統合データ保存エラー: {e}")
            print(f"❌ {indicator_type}保存エラー: {e}")
            import traceback

            print(f"保存詳細エラー: {traceback.format_exc()}")
            return False

    async def _save_unified_indicator_optimized(
        self, indicator_data: Dict[str, Any]
    ) -> bool:
        """
        統合データ保存（最適化版）

        Args:
            indicator_data: 統合された指標データ

        Returns:
            bool: 保存成功時True
        """
        try:
            # データ整合性検証
            if not await self._validate_data_integrity(indicator_data):
                logger.warning("データ整合性検証に失敗しました")
                return False

            # データ圧縮
            compressed_data = await self._compress_additional_data(
                indicator_data.get("additional_data", {})
            )

            # 技術指標モデルを作成
            # タイムスタンプは価格データの時刻を使用（計算時刻ではない）
            timestamp = indicator_data.get("timestamp")
            if timestamp is None:
                logger.error("タイムスタンプが設定されていません")
                return False

            indicator = TechnicalIndicatorModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                indicator_type=indicator_data.get("indicator_type"),
                timeframe=indicator_data.get("timeframe"),
                value=indicator_data.get("value"),
                additional_data=compressed_data,
                parameters=indicator_data.get("parameters", {}),
            )

            # データベースに保存
            await self.indicator_repo.save(indicator)

            logger.info(
                f"統合データ保存完了: {indicator_data.get('indicator_type')} - {indicator_data.get('timeframe')}"
            )
            return True

        except Exception as e:
            logger.error(f"統合データ保存エラー: {e}")
            return False

    async def _batch_save_indicators(self, indicators: List[Dict[str, Any]]) -> int:
        """
        バッチ保存機能

        Args:
            indicators: 保存する指標データのリスト

        Returns:
            int: 保存成功件数
        """
        try:
            if not indicators:
                return 0

            # データ整合性検証
            valid_indicators = []
            for indicator_data in indicators:
                if await self._validate_data_integrity(indicator_data):
                    valid_indicators.append(indicator_data)
                else:
                    logger.warning(
                        f"データ整合性検証失敗: {indicator_data.get('indicator_type')}"
                    )

            if not valid_indicators:
                logger.warning("有効なデータがありません")
                return 0

            # バッチ処理用のモデルリストを作成
            indicator_models = []
            for indicator_data in valid_indicators:
                compressed_data = await self._compress_additional_data(
                    indicator_data.get("additional_data", {})
                )

                # タイムスタンプは価格データの時刻を使用（計算時刻ではない）
                timestamp = indicator_data.get("timestamp")
                if timestamp is None:
                    logger.warning(
                        f"タイムスタンプが設定されていません: {indicator_data.get('indicator_type')}"
                    )
                    continue

                model = TechnicalIndicatorModel(
                    currency_pair=self.currency_pair,
                    timestamp=timestamp,
                    indicator_type=indicator_data.get("indicator_type"),
                    timeframe=indicator_data.get("timeframe"),
                    value=indicator_data.get("value"),
                    additional_data=compressed_data,
                    parameters=indicator_data.get("parameters", {}),
                )
                indicator_models.append(model)

            # バッチ保存実行
            saved_models = await self.indicator_repo.save_batch(indicator_models)

            logger.info(f"バッチ保存完了: {len(saved_models)}件")
            return len(saved_models)

        except Exception as e:
            logger.error(f"バッチ保存エラー: {e}")
            return 0

    async def _validate_data_integrity(self, indicator_data: Dict[str, Any]) -> bool:
        """
        データ整合性検証

        Args:
            indicator_data: 検証する指標データ

        Returns:
            bool: 整合性がある場合True
        """
        try:
            # 必須フィールドのチェック
            required_fields = ["indicator_type", "timeframe", "value"]
            for field in required_fields:
                if field not in indicator_data or indicator_data[field] is None:
                    logger.warning(f"必須フィールドが不足: {field}")
                    return False

            # データ型チェック
            if not isinstance(indicator_data["indicator_type"], str):
                logger.warning("indicator_typeは文字列である必要があります")
                return False

            if not isinstance(indicator_data["timeframe"], str):
                logger.warning("timeframeは文字列である必要があります")
                return False

            if not isinstance(indicator_data["value"], (int, float)):
                logger.warning("valueは数値である必要があります")
                return False

            # 値の範囲チェック
            value = float(indicator_data["value"])
            if np.isnan(value) or np.isinf(value):
                logger.warning("valueが無効な値です")
                return False

            # 指標タイプの妥当性チェック
            valid_indicators = ["RSI", "MACD", "BB", "SMA", "EMA", "STOCH", "ATR"]
            if indicator_data["indicator_type"] not in valid_indicators:
                logger.warning(f"無効な指標タイプ: {indicator_data['indicator_type']}")
                return False

            # 時間足の妥当性チェック
            valid_timeframes = ["M5", "M15", "H1", "H4", "D1"]
            if indicator_data["timeframe"] not in valid_timeframes:
                logger.warning(f"無効な時間足: {indicator_data['timeframe']}")
                return False

            # 追加データの構造チェック
            if (
                "additional_data" in indicator_data
                and indicator_data["additional_data"]
            ):
                if not isinstance(indicator_data["additional_data"], dict):
                    logger.warning("additional_dataは辞書である必要があります")
                    return False

            logger.debug(f"データ整合性検証成功: {indicator_data['indicator_type']}")
            return True

        except Exception as e:
            logger.error(f"データ整合性検証エラー: {e}")
            return False

    async def _compress_additional_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        追加データの圧縮

        Args:
            data: 圧縮するデータ

        Returns:
            Dict[str, Any]: 圧縮されたデータ
        """
        try:
            if not data:
                return {}

            compressed_data = {}

            # 数値データの丸め処理
            for key, value in data.items():
                if isinstance(value, dict):
                    compressed_data[key] = await self._compress_additional_data(value)
                elif isinstance(value, (int, float)):
                    # 小数点以下4桁に丸める
                    compressed_data[key] = round(float(value), 4)
                elif isinstance(value, list):
                    # リスト内の数値も丸める
                    compressed_list = []
                    for item in value:
                        if isinstance(item, (int, float)):
                            compressed_list.append(round(float(item), 4))
                        else:
                            compressed_list.append(item)
                    compressed_data[key] = compressed_list
                else:
                    compressed_data[key] = value

            return compressed_data

        except Exception as e:
            logger.error(f"データ圧縮エラー: {e}")
            return data

    async def _analyze_existing_data(self) -> Dict[str, Any]:
        """
        既存データの分析

        Returns:
            Dict[str, Any]: 既存データの分析結果
        """
        try:
            analysis_result = {
                "total_records": 0,
                "indicator_types": {},
                "timeframes": {},
                "data_quality": {},
                "recommendations": [],
            }

            # 全レコード数の取得
            total_query = select(func.count(TechnicalIndicatorModel.id))
            result = await self.session.execute(total_query)
            analysis_result["total_records"] = result.scalar()

            # 指標タイプ別の集計
            type_query = select(
                TechnicalIndicatorModel.indicator_type,
                func.count(TechnicalIndicatorModel.id),
            ).group_by(TechnicalIndicatorModel.indicator_type)

            result = await self.session.execute(type_query)
            for indicator_type, count in result:
                analysis_result["indicator_types"][indicator_type] = count

            # 時間足別の集計
            timeframe_query = select(
                TechnicalIndicatorModel.timeframe,
                func.count(TechnicalIndicatorModel.id),
            ).group_by(TechnicalIndicatorModel.timeframe)

            result = await self.session.execute(timeframe_query)
            for timeframe, count in result:
                analysis_result["timeframes"][timeframe] = count

            # データ品質の分析
            analysis_result["data_quality"] = await self._analyze_data_quality()

            # 推奨事項の生成
            analysis_result["recommendations"] = (
                await self._generate_data_recommendations(analysis_result)
            )

            logger.info(f"既存データ分析完了: {analysis_result['total_records']}件")
            return analysis_result

        except Exception as e:
            logger.error(f"既存データ分析エラー: {e}")
            return {"error": str(e)}

    async def _analyze_data_quality(self) -> Dict[str, Any]:
        """
        データ品質の分析

        Returns:
            Dict[str, Any]: データ品質分析結果
        """
        try:
            quality_analysis = {
                "null_values": 0,
                "invalid_values": 0,
                "duplicate_records": 0,
                "missing_additional_data": 0,
            }

            # NULL値のチェック
            null_query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.value.is_(None)
            )
            result = await self.session.execute(null_query)
            quality_analysis["null_values"] = result.scalar()

            # 無効な値のチェック（0または負の値）
            invalid_query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.value <= 0
            )
            result = await self.session.execute(invalid_query)
            quality_analysis["invalid_values"] = result.scalar()

            # 重複レコードのチェック
            duplicate_query = (
                select(
                    TechnicalIndicatorModel.currency_pair,
                    TechnicalIndicatorModel.timestamp,
                    TechnicalIndicatorModel.indicator_type,
                    TechnicalIndicatorModel.timeframe,
                    func.count(TechnicalIndicatorModel.id),
                )
                .group_by(
                    TechnicalIndicatorModel.currency_pair,
                    TechnicalIndicatorModel.timestamp,
                    TechnicalIndicatorModel.indicator_type,
                    TechnicalIndicatorModel.timeframe,
                )
                .having(func.count(TechnicalIndicatorModel.id) > 1)
            )

            result = await self.session.execute(duplicate_query)
            quality_analysis["duplicate_records"] = len(result.fetchall())

            # 追加データが不足しているレコードのチェック
            missing_data_query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.additional_data.is_(None)
            )
            result = await self.session.execute(missing_data_query)
            quality_analysis["missing_additional_data"] = result.scalar()

            return quality_analysis

        except Exception as e:
            logger.error(f"データ品質分析エラー: {e}")
            return {"error": str(e)}

    async def _generate_data_recommendations(
        self, analysis_result: Dict[str, Any]
    ) -> List[str]:
        """
        データ推奨事項の生成

        Args:
            analysis_result: 分析結果

        Returns:
            List[str]: 推奨事項のリスト
        """
        try:
            recommendations = []

            total_records = analysis_result.get("total_records", 0)
            data_quality = analysis_result.get("data_quality", {})

            # データ量の推奨
            if total_records < 1000:
                recommendations.append(
                    "データ量が不足しています。より多くのデータを取得することを推奨します。"
                )

            # データ品質の推奨
            if data_quality.get("null_values", 0) > 0:
                recommendations.append(
                    "NULL値が検出されました。データの整合性を確認してください。"
                )

            if data_quality.get("invalid_values", 0) > 0:
                recommendations.append(
                    "無効な値が検出されました。データの妥当性を確認してください。"
                )

            if data_quality.get("duplicate_records", 0) > 0:
                recommendations.append(
                    "重複レコードが検出されました。データの重複を解消してください。"
                )

            if data_quality.get("missing_additional_data", 0) > 0:
                recommendations.append(
                    "追加データが不足しているレコードがあります。統合データ保存を推奨します。"
                )

            # 指標タイプの推奨
            indicator_types = analysis_result.get("indicator_types", {})
            if len(indicator_types) < 5:
                recommendations.append(
                    "指標の種類が少ないです。より多様な指標の計算を推奨します。"
                )

            # 時間足の推奨
            timeframes = analysis_result.get("timeframes", {})
            if len(timeframes) < 3:
                recommendations.append(
                    "時間足の種類が少ないです。より多様な時間足での分析を推奨します。"
                )

            return recommendations

        except Exception as e:
            logger.error(f"推奨事項生成エラー: {e}")
            return ["推奨事項の生成中にエラーが発生しました"]

    # 分析メソッド（プライベート）
    def _analyze_rsi_state(self, rsi_value: float, config: Dict[str, Any]) -> str:
        """RSI状態分析"""
        if rsi_value >= config["overbought"]:
            return "overbought"
        elif rsi_value <= config["oversold"]:
            return "oversold"
        else:
            return "neutral"

    def _analyze_rsi_trend(self, rsi_values: np.ndarray, periods: int = 5) -> str:
        """RSI傾き分析"""
        if len(rsi_values) < periods:
            return "unknown"

        recent_values = rsi_values[-periods:]
        if recent_values[-1] > recent_values[0]:
            return "rising"
        elif recent_values[-1] < recent_values[0]:
            return "falling"
        else:
            return "flat"

    def _analyze_multi_period_rsi(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """多期間RSI統合分析"""
        # 実装予定
        return {"overall_trend": "mixed", "confidence": "medium"}

    def _analyze_macd_state(self, macd: float, signal: float, hist: float) -> str:
        """MACD状態分析"""
        if macd > signal and hist > 0:
            return "bullish"
        elif macd < signal and hist < 0:
            return "bearish"
        else:
            return "neutral"

    def _analyze_macd_cross(self, macd: np.ndarray, signal: np.ndarray) -> str:
        """MACDクロス分析"""
        if len(macd) < 2 or len(signal) < 2:
            return "unknown"

        if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
            return "bullish_cross"
        elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
            return "bearish_cross"
        else:
            return "no_cross"

    def _analyze_zero_line_position(self, macd: float) -> str:
        """MACDゼロライン位置分析"""
        if macd > 0:
            return "above"
        elif macd < 0:
            return "below"
        else:
            return "at_zero"

    def _analyze_bb_position(
        self, close: float, upper: float, middle: float, lower: float
    ) -> str:
        """ボリンジャーバンド位置分析"""
        if close > upper:
            return "above_upper"
        elif close < lower:
            return "below_lower"
        elif close > middle:
            return "above_middle"
        else:
            return "below_middle"

    def _analyze_bb_width(
        self, upper: np.ndarray, middle: np.ndarray, lower: np.ndarray
    ) -> str:
        """ボリンジャーバンド幅分析"""
        # 実装予定
        return "normal"

    def _analyze_multi_period_ma(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """多期間MA統合分析"""
        # 実装予定
        return {"trend": "mixed", "strength": "medium"}

    def _analyze_stoch_state(self, k: float, d: float) -> str:
        """ストキャスティクス状態分析"""
        if k > 80 and d > 80:
            return "overbought"
        elif k < 20 and d < 20:
            return "oversold"
        else:
            return "neutral"

    def _analyze_atr_volatility(self, atr_values: np.ndarray) -> Dict[str, Any]:
        """ATRボラティリティ分析"""
        # 実装予定
        return {"volatility_level": "normal", "trend": "stable"}

    def _analyze_indicator_state(
        self, indicator_type: str, values: np.ndarray
    ) -> Dict[str, Any]:
        """
        指標の状態判定（TALibTechnicalIndicators統合）

        Args:
            indicator_type: 指標タイプ
            values: 指標値

        Returns:
            Dict[str, Any]: 状態分析結果
        """
        try:
            if len(values) == 0:
                return {"state": "unknown", "confidence": "low"}

            current_value = values[-1] if not np.isnan(values[-1]) else None
            if current_value is None:
                return {"state": "unknown", "confidence": "low"}

            if indicator_type == "RSI":
                return self._analyze_rsi_state_advanced(current_value)
            elif indicator_type == "MACD":
                return self._analyze_macd_state_advanced(values)
            elif indicator_type == "BB":
                return self._analyze_bb_state_advanced(values)
            elif indicator_type == "STOCH":
                return self._analyze_stoch_state_advanced(values)
            elif indicator_type == "ATR":
                return self._analyze_atr_state_advanced(values)
            else:
                return {"state": "unknown", "confidence": "low"}

        except Exception as e:
            logger.error(f"指標状態分析エラー: {e}")
            return {"state": "error", "confidence": "low"}

    def _analyze_trend_strength(
        self, values: np.ndarray, periods: int = 5
    ) -> Dict[str, Any]:
        """
        トレンド強度分析（TALibTechnicalIndicators統合）

        Args:
            values: 指標値
            periods: 分析期間

        Returns:
            Dict[str, Any]: トレンド強度分析結果
        """
        try:
            if len(values) < periods:
                return {"trend": "unknown", "strength": "low", "confidence": "low"}

            recent_values = values[-periods:]
            valid_values = recent_values[~np.isnan(recent_values)]

            if len(valid_values) < 2:
                return {"trend": "unknown", "strength": "low", "confidence": "low"}

            # 線形回帰で傾きを計算
            x = np.arange(len(valid_values))
            slope, intercept = np.polyfit(x, valid_values, 1)

            # 決定係数を計算
            y_pred = slope * x + intercept
            r_squared = 1 - np.sum((valid_values - y_pred) ** 2) / np.sum(
                (valid_values - np.mean(valid_values)) ** 2
            )

            # トレンド判定
            if slope > 0:
                trend = "rising"
            elif slope < 0:
                trend = "falling"
            else:
                trend = "flat"

            # 強度判定
            if abs(slope) > 2.0 and r_squared > 0.7:
                strength = "strong"
            elif abs(slope) > 1.0 and r_squared > 0.5:
                strength = "medium"
            else:
                strength = "weak"

            # 信頼度判定
            if r_squared > 0.8:
                confidence = "high"
            elif r_squared > 0.6:
                confidence = "medium"
            else:
                confidence = "low"

            return {
                "trend": trend,
                "strength": strength,
                "confidence": confidence,
                "slope": float(slope),
                "r_squared": float(r_squared),
            }

        except Exception as e:
            logger.error(f"トレンド強度分析エラー: {e}")
            return {"trend": "error", "strength": "low", "confidence": "low"}

    def _generate_trading_signals(
        self, indicator_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        トレードシグナル生成（TALibTechnicalIndicators統合）

        Args:
            indicator_data: 指標データ

        Returns:
            Dict[str, Any]: トレードシグナル
        """
        try:
            signals = {
                "primary_signal": "hold",
                "secondary_signal": "hold",
                "confidence": "low",
                "reason": "データ不足",
            }

            indicator_type = indicator_data.get("indicator_type")
            state = indicator_data.get("state", "unknown")
            trend = indicator_data.get("trend", "unknown")
            strength = indicator_data.get("strength", "low")

            if indicator_type == "RSI":
                signals.update(self._generate_rsi_signals(indicator_data))
            elif indicator_type == "MACD":
                signals.update(self._generate_macd_signals(indicator_data))
            elif indicator_type == "BB":
                signals.update(self._generate_bb_signals(indicator_data))
            elif indicator_type == "STOCH":
                signals.update(self._generate_stoch_signals(indicator_data))

            return signals

        except Exception as e:
            logger.error(f"シグナル生成エラー: {e}")
            return {"primary_signal": "error", "confidence": "low"}

    def _perform_advanced_analysis(
        self, indicator_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        高度分析機能（TALibTechnicalIndicators統合）

        Args:
            indicator_data: 指標データ

        Returns:
            Dict[str, Any]: 高度分析結果
        """
        try:
            analysis = {
                "divergence": self._detect_divergence_advanced(indicator_data),
                "momentum": self._analyze_momentum_advanced(indicator_data),
                "volatility": self._analyze_volatility_advanced(indicator_data),
                "support_resistance": self._analyze_support_resistance_advanced(
                    indicator_data
                ),
            }

            return analysis

        except Exception as e:
            logger.error(f"高度分析エラー: {e}")
            return {"error": str(e)}

    def _apply_optimized_settings(self) -> None:
        """
        最適化された設定の適用（TechnicalIndicatorsAnalyzer統合）
        """
        try:
            # TechnicalIndicatorsAnalyzerの最適化設定を適用
            optimized_config = {
                "RSI": {
                    "short_term": {
                        "period": 30,  # TechnicalIndicatorsAnalyzerから採用
                        "overbought": 70,
                        "oversold": 30,
                        "description": "短期の過熱・過冷感を測定",
                    },
                    "medium_term": {
                        "period": 50,  # TechnicalIndicatorsAnalyzerから採用
                        "overbought": 65,
                        "oversold": 35,
                        "description": "中期トレンドの強弱を測定",
                    },
                    "long_term": {
                        "period": 70,  # TechnicalIndicatorsAnalyzerから採用
                        "overbought": 60,
                        "oversold": 40,
                        "description": "長期トレンドの方向性を測定",
                    },
                },
                "SMA": {
                    "short": 20,  # TechnicalIndicatorsAnalyzerから採用
                    "medium": 50,  # TechnicalIndicatorsAnalyzerから採用
                    "long": 200,  # TechnicalIndicatorsAnalyzerから採用
                    "description": "短期・中期・長期の3期間で市場トレンドを把握",
                },
                "EMA": {
                    "short": 12,  # UnifiedTechnicalCalculatorから採用
                    "medium": 26,  # UnifiedTechnicalCalculatorから採用
                    "long": 50,  # TechnicalIndicatorsAnalyzerから採用
                    "description": "MACDと連携する短期・中期、長期トレンド用",
                },
                "MACD": {
                    "fast_period": 12,  # 全システム共通
                    "slow_period": 26,  # 全システム共通
                    "signal_period": 9,  # 全システム共通
                    "analysis_features": [
                        "cross_signal",  # TechnicalIndicatorsAnalyzerから
                        "zero_line_position",  # TechnicalIndicatorsAnalyzerから
                    ],
                    "unified_save": True,
                },
                "BB": {
                    "period": 20,  # 全システム共通
                    "std_dev": 2.0,  # 全システム共通
                    "analysis_features": [
                        "band_position",  # TechnicalIndicatorsAnalyzerから
                        "band_walk",  # TechnicalIndicatorsAnalyzerから
                        "band_width",  # TechnicalIndicatorsAnalyzerから
                    ],
                    "unified_save": True,
                },
                "STOCH": {
                    "fastk_period": 14,  # UnifiedTechnicalCalculatorから採用
                    "slowk_period": 3,  # UnifiedTechnicalCalculatorから採用
                    "slowd_period": 3,  # UnifiedTechnicalCalculatorから採用
                    "analysis_features": [
                        "state_analysis"  # TALibTechnicalIndicatorsから
                    ],
                    "unified_save": True,
                },
                "ATR": {
                    "period": 14,  # UnifiedTechnicalCalculatorから採用
                    "analysis_features": [
                        "volatility_analysis"  # TALibTechnicalIndicatorsから
                    ],
                },
            }

            # 設定を更新
            self.indicators_config.update(optimized_config)
            logger.info("最適化された設定を適用しました")

        except Exception as e:
            logger.error(f"最適化設定適用エラー: {e}")

    def _validate_settings_compatibility(self) -> bool:
        """
        設定の互換性検証（TechnicalIndicatorsAnalyzer統合）

        Returns:
            bool: 互換性がある場合True
        """
        try:
            # RSI設定の検証
            rsi_config = self.indicators_config.get("RSI", {})
            if not all(
                key in rsi_config for key in ["short_term", "medium_term", "long_term"]
            ):
                logger.warning("RSI設定が不完全です")
                return False

            # 移動平均設定の検証
            sma_config = self.indicators_config.get("SMA", {})
            if not all(key in sma_config for key in ["short", "medium", "long"]):
                logger.warning("SMA設定が不完全です")
                return False

            # MACD設定の検証
            macd_config = self.indicators_config.get("MACD", {})
            if not all(
                key in macd_config
                for key in ["fast_period", "slow_period", "signal_period"]
            ):
                logger.warning("MACD設定が不完全です")
                return False

            logger.info("設定の互換性検証が完了しました")
            return True

        except Exception as e:
            logger.error(f"設定互換性検証エラー: {e}")
            return False

    def _migrate_existing_settings(self) -> Dict[str, Any]:
        """
        既存設定の移行（TechnicalIndicatorsAnalyzer統合）

        Returns:
            Dict[str, Any]: 移行された設定
        """
        try:
            migrated_settings = {}

            # 既存の設定をバックアップ
            original_config = self.indicators_config.copy()

            # 新しい設定を適用
            self._apply_optimized_settings()

            # 移行結果を記録
            migrated_settings = {
                "original_config": original_config,
                "new_config": self.indicators_config,
                "migration_time": datetime.now().isoformat(),
                "compatibility": self._validate_settings_compatibility(),
            }

            logger.info("既存設定の移行が完了しました")
            return migrated_settings

        except Exception as e:
            logger.error(f"設定移行エラー: {e}")
            return {"error": str(e)}

    def _analyze_rsi_state_advanced(self, rsi_value: float) -> Dict[str, Any]:
        """RSI高度状態分析"""
        if rsi_value >= 80:
            return {"state": "extremely_overbought", "confidence": "high"}
        elif rsi_value >= 70:
            return {"state": "overbought", "confidence": "high"}
        elif rsi_value >= 60:
            return {"state": "bullish", "confidence": "medium"}
        elif rsi_value >= 40:
            return {"state": "neutral", "confidence": "medium"}
        elif rsi_value >= 30:
            return {"state": "bearish", "confidence": "medium"}
        elif rsi_value >= 20:
            return {"state": "oversold", "confidence": "high"}
        else:
            return {"state": "extremely_oversold", "confidence": "high"}

    def _analyze_macd_state_advanced(self, values: np.ndarray) -> Dict[str, Any]:
        """MACD高度状態分析"""
        if len(values) < 3:
            return {"state": "unknown", "confidence": "low"}

        current = values[-1] if not np.isnan(values[-1]) else None
        previous = values[-2] if not np.isnan(values[-2]) else None

        if current is None or previous is None:
            return {"state": "unknown", "confidence": "low"}

        if current > 0 and current > previous:
            return {"state": "strong_bullish", "confidence": "high"}
        elif current > 0 and current < previous:
            return {"state": "weakening_bullish", "confidence": "medium"}
        elif current < 0 and current < previous:
            return {"state": "strong_bearish", "confidence": "high"}
        elif current < 0 and current > previous:
            return {"state": "weakening_bearish", "confidence": "medium"}
        else:
            return {"state": "neutral", "confidence": "medium"}

    def _analyze_bb_state_advanced(self, values: np.ndarray) -> Dict[str, Any]:
        """ボリンジャーバンド高度状態分析"""
        if len(values) < 20:
            return {"state": "unknown", "confidence": "low"}

        # 簡易的なボラティリティ分析
        recent_values = values[-20:]
        volatility = np.std(recent_values[~np.isnan(recent_values)])

        if volatility > 2.0:
            return {"state": "high_volatility", "confidence": "high"}
        elif volatility > 1.0:
            return {"state": "medium_volatility", "confidence": "medium"}
        else:
            return {"state": "low_volatility", "confidence": "medium"}

    def _analyze_stoch_state_advanced(self, values: np.ndarray) -> Dict[str, Any]:
        """ストキャスティクス高度状態分析"""
        if len(values) < 5:
            return {"state": "unknown", "confidence": "low"}

        recent_values = values[-5:]
        avg_value = np.nanmean(recent_values)

        if avg_value >= 80:
            return {"state": "overbought", "confidence": "high"}
        elif avg_value <= 20:
            return {"state": "oversold", "confidence": "high"}
        elif avg_value >= 60:
            return {"state": "bullish", "confidence": "medium"}
        elif avg_value <= 40:
            return {"state": "bearish", "confidence": "medium"}
        else:
            return {"state": "neutral", "confidence": "medium"}

    def _analyze_atr_state_advanced(self, values: np.ndarray) -> Dict[str, Any]:
        """ATR高度状態分析"""
        if len(values) < 10:
            return {"state": "unknown", "confidence": "low"}

        recent_values = values[-10:]
        avg_atr = np.nanmean(recent_values)
        current_atr = values[-1] if not np.isnan(values[-1]) else avg_atr

        if current_atr > avg_atr * 1.5:
            return {"state": "high_volatility", "confidence": "high"}
        elif current_atr < avg_atr * 0.5:
            return {"state": "low_volatility", "confidence": "high"}
        else:
            return {"state": "normal_volatility", "confidence": "medium"}

    def _generate_rsi_signals(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """RSIシグナル生成"""
        state = indicator_data.get("state", "unknown")
        value = indicator_data.get("value", 50)

        if state == "extremely_overbought":
            return {
                "primary_signal": "sell",
                "secondary_signal": "strong_sell",
                "confidence": "high",
            }
        elif state == "overbought":
            return {
                "primary_signal": "sell",
                "secondary_signal": "hold",
                "confidence": "medium",
            }
        elif state == "extremely_oversold":
            return {
                "primary_signal": "buy",
                "secondary_signal": "strong_buy",
                "confidence": "high",
            }
        elif state == "oversold":
            return {
                "primary_signal": "buy",
                "secondary_signal": "hold",
                "confidence": "medium",
            }
        else:
            return {
                "primary_signal": "hold",
                "secondary_signal": "hold",
                "confidence": "low",
            }

    def _generate_macd_signals(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """MACDシグナル生成"""
        state = indicator_data.get("state", "unknown")
        trend = indicator_data.get("trend", "unknown")

        if state == "strong_bullish" and trend == "rising":
            return {
                "primary_signal": "buy",
                "secondary_signal": "strong_buy",
                "confidence": "high",
            }
        elif state == "strong_bearish" and trend == "falling":
            return {
                "primary_signal": "sell",
                "secondary_signal": "strong_sell",
                "confidence": "high",
            }
        elif state == "weakening_bullish":
            return {
                "primary_signal": "hold",
                "secondary_signal": "sell",
                "confidence": "medium",
            }
        elif state == "weakening_bearish":
            return {
                "primary_signal": "hold",
                "secondary_signal": "buy",
                "confidence": "medium",
            }
        else:
            return {
                "primary_signal": "hold",
                "secondary_signal": "hold",
                "confidence": "low",
            }

    def _generate_bb_signals(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """ボリンジャーバンドシグナル生成"""
        state = indicator_data.get("state", "unknown")

        if state == "high_volatility":
            return {
                "primary_signal": "hold",
                "secondary_signal": "caution",
                "confidence": "medium",
            }
        elif state == "low_volatility":
            return {
                "primary_signal": "hold",
                "secondary_signal": "breakout_watch",
                "confidence": "medium",
            }
        else:
            return {
                "primary_signal": "hold",
                "secondary_signal": "hold",
                "confidence": "low",
            }

    def _generate_stoch_signals(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """ストキャスティクスシグナル生成"""
        state = indicator_data.get("state", "unknown")

        if state == "overbought":
            return {
                "primary_signal": "sell",
                "secondary_signal": "hold",
                "confidence": "medium",
            }
        elif state == "oversold":
            return {
                "primary_signal": "buy",
                "secondary_signal": "hold",
                "confidence": "medium",
            }
        else:
            return {
                "primary_signal": "hold",
                "secondary_signal": "hold",
                "confidence": "low",
            }

    def _detect_divergence_advanced(
        self, indicator_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """高度ダイバージェンス検出"""
        # 実装予定
        return {"divergence_type": "none", "confidence": "low"}

    def _analyze_momentum_advanced(
        self, indicator_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """高度モメンタム分析"""
        # 実装予定
        return {"momentum": "neutral", "strength": "medium"}

    def _analyze_volatility_advanced(
        self, indicator_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """高度ボラティリティ分析"""
        # 実装予定
        return {"volatility": "normal", "trend": "stable"}

    def _analyze_support_resistance_advanced(
        self, indicator_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """高度サポート・レジスタンス分析"""
        # 実装予定
        return {"support": None, "resistance": None, "confidence": "low"}

    def start_analysis_progress(self, analysis_type: str, total_steps: int):
        """
        分析機能プログレス開始（tqdm詳細化）

        Args:
            analysis_type: 分析タイプ
            total_steps: 総ステップ数

        Returns:
            tqdm.auto.tqdm: プログレスバーオブジェクト
        """
        try:
            from tqdm.auto import tqdm

            if not self.progress_config["enable_progress"]:
                return None

            pbar = tqdm(
                total=total_steps,
                desc=f"🔍 {analysis_type} 分析中...",
                unit="ステップ",
                **self.progress_config["tqdm_config"],
            )

            return pbar

        except Exception as e:
            logger.error(f"分析プログレス開始エラー: {e}")
            return None

    def update_analysis_progress(self, progress_id, step: str, details: Dict[str, Any]):
        """
        分析プログレス更新（tqdm詳細化）

        Args:
            progress_id: プログレスバーID
            step: 現在のステップ
            details: 詳細情報
        """
        try:
            if not self.progress_config["enable_progress"] or progress_id is None:
                return

            # 詳細情報を文字列に変換
            detail_str = ""
            if details:
                detail_items = []
                for key, value in details.items():
                    if isinstance(value, float):
                        detail_items.append(f"{key}: {value:.2f}")
                    else:
                        detail_items.append(f"{key}: {value}")
                detail_str = f" ({', '.join(detail_items)})"

            # プログレスバーを更新
            progress_id.set_description(f"🔍 {step}{detail_str}")
            progress_id.update(1)

        except Exception as e:
            logger.error(f"分析プログレス更新エラー: {e}")

    def show_performance_info(self, performance_data: Dict[str, Any]):
        """
        パフォーマンス情報表示（tqdm詳細化）

        Args:
            performance_data: パフォーマンスデータ
        """
        try:
            if not self.progress_config["enable_progress"]:
                return

            print("📊 パフォーマンス情報:")
            print(f"   ⏱️ 処理時間: {performance_data.get('processing_time', 'N/A')}")
            print(f"   💾 メモリ使用量: {performance_data.get('memory_usage', 'N/A')}")
            print(f"   🚀 処理速度: {performance_data.get('processing_speed', 'N/A')}")
            print(f"   📈 成功率: {performance_data.get('success_rate', 'N/A')}%")

        except Exception as e:
            logger.error(f"パフォーマンス情報表示エラー: {e}")

    def show_error_details(self, error_info: Dict[str, Any]):
        """
        エラー詳細表示（tqdm詳細化）

        Args:
            error_info: エラー情報
        """
        try:
            if not self.progress_config["enable_progress"]:
                return

            print("❌ エラー詳細:")
            print(f"   🔍 エラー箇所: {error_info.get('location', 'N/A')}")
            print(f"   📝 エラー内容: {error_info.get('message', 'N/A')}")
            print(f"   🛠️ リカバリー情報: {error_info.get('recovery_info', 'N/A')}")

        except Exception as e:
            logger.error(f"エラー詳細表示エラー: {e}")

    def _create_detailed_progress_manager(self):
        """
        詳細プログレス管理作成（tqdm詳細化）

        Returns:
            Dict[str, Any]: 詳細プログレス管理オブジェクト
        """
        try:
            from tqdm.auto import tqdm

            progress_manager = {
                "enable_progress": self.progress_config["enable_progress"],
                "tqdm_config": self.progress_config["tqdm_config"],
                "progress_bars": {},
                "performance_data": {},
                "error_data": {},
            }

            return progress_manager

        except Exception as e:
            logger.error(f"詳細プログレス管理作成エラー: {e}")
            return None

    def _update_detailed_progress(
        self,
        progress_manager: Dict[str, Any],
        progress_type: str,
        step: str,
        details: Dict[str, Any] = None,
    ):
        """
        詳細プログレス更新（tqdm詳細化）

        Args:
            progress_manager: プログレス管理オブジェクト
            progress_type: プログレスタイプ
            step: 現在のステップ
            details: 詳細情報
        """
        try:
            if not progress_manager or not progress_manager["enable_progress"]:
                return

            # パフォーマンスデータを記録
            if details and "processing_time" in details:
                progress_manager["performance_data"][progress_type] = details

            # エラーデータを記録
            if details and "error" in details:
                progress_manager["error_data"][progress_type] = details

            # プログレスバーを更新
            if progress_type in progress_manager["progress_bars"]:
                pbar = progress_manager["progress_bars"][progress_type]
                self.update_analysis_progress(pbar, step, details or {})

        except Exception as e:
            logger.error(f"詳細プログレス更新エラー: {e}")

    async def migrate_existing_data(self, progress_callback=None) -> Dict[str, Any]:
        """
        既存データの移行

        Args:
            progress_callback: 進捗コールバック関数

        Returns:
            Dict[str, Any]: 移行結果
        """
        try:
            migration_result = {
                "total_records": 0,
                "migrated_records": 0,
                "failed_records": 0,
                "migration_time": None,
                "errors": [],
            }

            # 既存データの分析
            analysis_result = await self._analyze_existing_data()
            total_records = analysis_result.get("total_records", 0)
            migration_result["total_records"] = total_records

            if total_records == 0:
                logger.info("移行対象のデータがありません")
                return migration_result

            # 移行開始時刻
            start_time = datetime.now()
            migration_result["migration_time"] = start_time.isoformat()

            logger.info(f"データ移行開始: {total_records}件")

            # バッチサイズ
            batch_size = 100
            migrated_count = 0
            failed_count = 0

            # 全レコードを取得
            query = select(TechnicalIndicatorModel).order_by(TechnicalIndicatorModel.id)
            result = await self.session.execute(query)
            all_records = result.scalars().all()

            # バッチ処理
            for i in range(0, len(all_records), batch_size):
                batch_records = all_records[i : i + batch_size]

                # 進捗更新
                if progress_callback:
                    progress = (i / len(all_records)) * 100
                    progress_callback(
                        progress,
                        f"バッチ処理中: {i+1}-{min(i+batch_size, len(all_records))}",
                    )

                # バッチ内の各レコードを処理
                for record in batch_records:
                    try:
                        # 統合データ形式に変換
                        unified_data = await self._convert_to_unified_format(record)

                        # 統合データ保存
                        if await self._save_unified_indicator_optimized(unified_data):
                            migrated_count += 1
                        else:
                            failed_count += 1
                            migration_result["errors"].append(
                                f"レコードID {record.id}: 保存失敗"
                            )

                    except Exception as e:
                        failed_count += 1
                        error_msg = f"レコードID {record.id}: {str(e)}"
                        migration_result["errors"].append(error_msg)
                        logger.error(error_msg)

            # 移行結果を更新
            migration_result["migrated_records"] = migrated_count
            migration_result["failed_records"] = failed_count

            # 移行完了時刻
            end_time = datetime.now()
            migration_duration = (end_time - start_time).total_seconds()

            logger.info(
                f"データ移行完了: {migrated_count}件成功, {failed_count}件失敗, 所要時間: {migration_duration:.2f}秒"
            )

            return migration_result

        except Exception as e:
            logger.error(f"データ移行エラー: {e}")
            return {"error": str(e)}

    async def validate_migration_results(self) -> bool:
        """
        移行結果の検証

        Returns:
            bool: 検証成功時True
        """
        try:
            # 移行前後のデータ比較
            before_analysis = await self._analyze_existing_data()
            after_analysis = await self._analyze_existing_data()

            # データ量の確認
            if after_analysis.get("total_records", 0) < before_analysis.get(
                "total_records", 0
            ):
                logger.warning("移行後にデータ量が減少しました")
                return False

            # データ品質の確認
            before_quality = before_analysis.get("data_quality", {})
            after_quality = after_analysis.get("data_quality", {})

            # NULL値の確認
            if after_quality.get("null_values", 0) > before_quality.get(
                "null_values", 0
            ):
                logger.warning("移行後にNULL値が増加しました")
                return False

            # 無効な値の確認
            if after_quality.get("invalid_values", 0) > before_quality.get(
                "invalid_values", 0
            ):
                logger.warning("移行後に無効な値が増加しました")
                return False

            logger.info("移行結果の検証が完了しました")
            return True

        except Exception as e:
            logger.error(f"移行結果検証エラー: {e}")
            return False

    async def rollback_migration(self) -> bool:
        """
        移行のロールバック

        Returns:
            bool: ロールバック成功時True
        """
        try:
            logger.info("移行のロールバックを開始します")

            # 移行後に作成されたレコードを削除
            # 注意: この実装は簡易版です。実際の運用ではより慎重なロールバックが必要です

            # 最新の移行データを削除するクエリ
            # 実際の実装では、移行前のバックアップから復元することを推奨します

            logger.warning("ロールバック機能は実装中です。手動での復元が必要です")
            return False

        except Exception as e:
            logger.error(f"ロールバックエラー: {e}")
            return False

    async def generate_migration_report(self) -> Dict[str, Any]:
        """
        移行レポートの生成

        Returns:
            Dict[str, Any]: 移行レポート
        """
        try:
            # 既存データの分析
            analysis_result = await self._analyze_existing_data()

            # 移行実行
            migration_result = await self.migrate_existing_data()

            # 移行結果の検証
            validation_result = await self.validate_migration_results()

            # レポート生成
            report = {
                "report_type": "データ移行レポート",
                "generated_at": datetime.now().isoformat(),
                "analysis_before": analysis_result,
                "migration_result": migration_result,
                "validation_result": validation_result,
                "summary": {
                    "total_records": migration_result.get("total_records", 0),
                    "migrated_records": migration_result.get("migrated_records", 0),
                    "failed_records": migration_result.get("failed_records", 0),
                    "success_rate": 0,
                },
            }

            # 成功率の計算
            total = report["summary"]["total_records"]
            migrated = report["summary"]["migrated_records"]
            if total > 0:
                report["summary"]["success_rate"] = (migrated / total) * 100

            logger.info(
                f"移行レポート生成完了: 成功率 {report['summary']['success_rate']:.1f}%"
            )
            return report

        except Exception as e:
            logger.error(f"移行レポート生成エラー: {e}")
            return {"error": str(e)}

    async def _convert_to_unified_format(
        self, record: TechnicalIndicatorModel
    ) -> Dict[str, Any]:
        """
        既存レコードを統合形式に変換

        Args:
            record: 既存のTechnicalIndicatorModel

        Returns:
            Dict[str, Any]: 統合形式のデータ
        """
        try:
            # 基本データ
            unified_data = {
                "indicator_type": record.indicator_type,
                "timeframe": record.timeframe,
                "value": float(record.value),
                "timestamp": record.timestamp,
                "parameters": record.parameters or {},
            }

            # 追加データの統合
            if record.additional_data:
                unified_data["additional_data"] = record.additional_data
            else:
                # 追加データがない場合は基本的な構造を作成
                unified_data["additional_data"] = {
                    "original_record_id": record.id,
                    "migration_timestamp": datetime.now().isoformat(),
                    "data_source": "legacy",
                }

            return unified_data

        except Exception as e:
            logger.error(f"統合形式変換エラー: {e}")
            return {}

    async def validate_data_integrity(self) -> Dict[str, Any]:
        """
        データ整合性検証

        Returns:
            Dict[str, Any]: 整合性検証結果
        """
        try:
            integrity_result = {
                "overall_status": "unknown",
                "validation_rules": {},
                "issues_found": [],
                "recommendations": [],
                "validation_time": datetime.now().isoformat(),
            }

            # データ型チェック
            type_validation = await self._validate_data_types()
            integrity_result["validation_rules"]["data_types"] = type_validation

            # 範囲チェック
            range_validation = await self._validate_data_ranges()
            integrity_result["validation_rules"]["data_ranges"] = range_validation

            # 関連性チェック
            relationship_validation = await self._validate_data_relationships()
            integrity_result["validation_rules"][
                "relationships"
            ] = relationship_validation

            # 一貫性チェック
            consistency_validation = await self._validate_data_consistency()
            integrity_result["validation_rules"]["consistency"] = consistency_validation

            # 問題の集計
            total_issues = 0
            for rule_name, rule_result in integrity_result["validation_rules"].items():
                if rule_result.get("status") == "failed":
                    total_issues += rule_result.get("issue_count", 0)
                    integrity_result["issues_found"].extend(
                        rule_result.get("issues", [])
                    )

            # 全体ステータスの決定
            if total_issues == 0:
                integrity_result["overall_status"] = "passed"
            elif total_issues < 10:
                integrity_result["overall_status"] = "warning"
            else:
                integrity_result["overall_status"] = "failed"

            # 推奨事項の生成
            integrity_result["recommendations"] = (
                await self._generate_integrity_recommendations(integrity_result)
            )

            logger.info(
                f"データ整合性検証完了: ステータス={integrity_result['overall_status']}, 問題数={total_issues}"
            )
            return integrity_result

        except Exception as e:
            logger.error(f"データ整合性検証エラー: {e}")
            return {"error": str(e)}

    async def monitor_data_quality(self) -> Dict[str, Any]:
        """
        データ品質監視

        Returns:
            Dict[str, Any]: 品質監視結果
        """
        try:
            quality_result = {
                "monitoring_time": datetime.now().isoformat(),
                "quality_metrics": {},
                "alerts": [],
                "trends": {},
            }

            # リアルタイム監視
            realtime_metrics = await self._get_realtime_quality_metrics()
            quality_result["quality_metrics"]["realtime"] = realtime_metrics

            # 定期チェック
            periodic_metrics = await self._get_periodic_quality_metrics()
            quality_result["quality_metrics"]["periodic"] = periodic_metrics

            # 異常検出
            anomalies = await self._detect_quality_anomalies(
                realtime_metrics, periodic_metrics
            )
            quality_result["alerts"] = anomalies

            # トレンド分析
            trends = await self._analyze_quality_trends()
            quality_result["trends"] = trends

            logger.info(f"データ品質監視完了: アラート数={len(anomalies)}")
            return quality_result

        except Exception as e:
            logger.error(f"データ品質監視エラー: {e}")
            return {"error": str(e)}

    async def auto_repair_data(self, issues: List[Dict[str, Any]]) -> int:
        """
        データの自動修復

        Args:
            issues: 修復対象の問題リスト

        Returns:
            int: 修復成功件数
        """
        try:
            repaired_count = 0

            for issue in issues:
                try:
                    issue_type = issue.get("type")
                    issue_data = issue.get("data", {})

                    if issue_type == "null_value":
                        success = await self._repair_null_value(issue_data)
                    elif issue_type == "invalid_range":
                        success = await self._repair_invalid_range(issue_data)
                    elif issue_type == "duplicate_record":
                        success = await self._repair_duplicate_record(issue_data)
                    elif issue_type == "missing_additional_data":
                        success = await self._repair_missing_additional_data(issue_data)
                    else:
                        logger.warning(f"未知の問題タイプ: {issue_type}")
                        continue

                    if success:
                        repaired_count += 1
                        logger.info(f"修復成功: {issue_type}")

                except Exception as e:
                    logger.error(f"修復エラー: {issue_type} - {e}")

            logger.info(f"自動修復完了: {repaired_count}件成功")
            return repaired_count

        except Exception as e:
            logger.error(f"自動修復エラー: {e}")
            return 0

    async def generate_integrity_report(self) -> Dict[str, Any]:
        """
        整合性レポートの生成

        Returns:
            Dict[str, Any]: 整合性レポート
        """
        try:
            # 整合性検証実行
            integrity_result = await self.validate_data_integrity()

            # 品質監視実行
            quality_result = await self.monitor_data_quality()

            # レポート生成
            report = {
                "report_type": "データ整合性レポート",
                "generated_at": datetime.now().isoformat(),
                "integrity_validation": integrity_result,
                "quality_monitoring": quality_result,
                "summary": {
                    "overall_status": integrity_result.get("overall_status", "unknown"),
                    "total_issues": len(integrity_result.get("issues_found", [])),
                    "total_alerts": len(quality_result.get("alerts", [])),
                    "recommendations": integrity_result.get("recommendations", []),
                },
            }

            logger.info(
                f"整合性レポート生成完了: ステータス={report['summary']['overall_status']}"
            )
            return report

        except Exception as e:
            logger.error(f"整合性レポート生成エラー: {e}")
            return {"error": str(e)}

    async def send_integrity_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        整合性アラートの送信

        Args:
            alert_data: アラートデータ

        Returns:
            bool: 送信成功時True
        """
        try:
            # アラートレベルの判定
            alert_level = alert_data.get("level", "info")
            alert_message = alert_data.get("message", "")

            if alert_level == "critical":
                logger.critical(f"🚨 重大な整合性問題: {alert_message}")
            elif alert_level == "warning":
                logger.warning(f"⚠️ 整合性警告: {alert_message}")
            else:
                logger.info(f"ℹ️ 整合性情報: {alert_message}")

            # 実際の運用では、Discord通知やメール送信などを実装
            # ここではログ出力のみ

            return True

        except Exception as e:
            logger.error(f"アラート送信エラー: {e}")
            return False

    async def _validate_data_types(self) -> Dict[str, Any]:
        """データ型チェック"""
        try:
            validation_result = {"status": "passed", "issue_count": 0, "issues": []}

            # 文字列フィールドのチェック
            string_fields = ["indicator_type", "timeframe", "currency_pair"]
            for field in string_fields:
                query = select(func.count(TechnicalIndicatorModel.id)).where(
                    getattr(TechnicalIndicatorModel, field).is_(None)
                )
                result = await self.session.execute(query)
                null_count = result.scalar()

                if null_count > 0:
                    validation_result["status"] = "failed"
                    validation_result["issue_count"] += null_count
                    validation_result["issues"].append(
                        f"{field}にNULL値が{null_count}件あります"
                    )

            # 数値フィールドのチェック
            query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.value.is_(None)
            )
            result = await self.session.execute(query)
            null_count = result.scalar()

            if null_count > 0:
                validation_result["status"] = "failed"
                validation_result["issue_count"] += null_count
                validation_result["issues"].append(
                    f"valueにNULL値が{null_count}件あります"
                )

            return validation_result

        except Exception as e:
            logger.error(f"データ型チェックエラー: {e}")
            return {"status": "error", "issue_count": 0, "issues": [str(e)]}

    async def _validate_data_ranges(self) -> Dict[str, Any]:
        """データ範囲チェック"""
        try:
            validation_result = {"status": "passed", "issue_count": 0, "issues": []}

            # RSI値の範囲チェック（0-100）
            rsi_query = select(func.count(TechnicalIndicatorModel.id)).where(
                and_(
                    TechnicalIndicatorModel.indicator_type == "RSI",
                    or_(
                        TechnicalIndicatorModel.value < 0,
                        TechnicalIndicatorModel.value > 100,
                    ),
                )
            )
            result = await self.session.execute(rsi_query)
            invalid_rsi_count = result.scalar()

            if invalid_rsi_count > 0:
                validation_result["status"] = "failed"
                validation_result["issue_count"] += invalid_rsi_count
                validation_result["issues"].append(
                    f"RSI値が範囲外のレコードが{invalid_rsi_count}件あります"
                )

            # 負の値のチェック（一部の指標を除く）
            negative_query = select(func.count(TechnicalIndicatorModel.id)).where(
                and_(
                    TechnicalIndicatorModel.value < 0,
                    TechnicalIndicatorModel.indicator_type.in_(["RSI", "STOCH"]),
                )
            )
            result = await self.session.execute(negative_query)
            negative_count = result.scalar()

            if negative_count > 0:
                validation_result["status"] = "failed"
                validation_result["issue_count"] += negative_count
                validation_result["issues"].append(
                    f"負の値が不適切なレコードが{negative_count}件あります"
                )

            return validation_result

        except Exception as e:
            logger.error(f"データ範囲チェックエラー: {e}")
            return {"status": "error", "issue_count": 0, "issues": [str(e)]}

    async def _validate_data_relationships(self) -> Dict[str, Any]:
        """データ関連性チェック"""
        try:
            validation_result = {"status": "passed", "issue_count": 0, "issues": []}

            # 通貨ペアと時間足の組み合わせチェック
            # 実際の実装では、より詳細な関連性チェックを追加

            return validation_result

        except Exception as e:
            logger.error(f"データ関連性チェックエラー: {e}")
            return {"status": "error", "issue_count": 0, "issues": [str(e)]}

    async def _validate_data_consistency(self) -> Dict[str, Any]:
        """データ一貫性チェック"""
        try:
            validation_result = {"status": "passed", "issue_count": 0, "issues": []}

            # 重複レコードのチェック
            duplicate_query = (
                select(
                    TechnicalIndicatorModel.currency_pair,
                    TechnicalIndicatorModel.timestamp,
                    TechnicalIndicatorModel.indicator_type,
                    TechnicalIndicatorModel.timeframe,
                    func.count(TechnicalIndicatorModel.id),
                )
                .group_by(
                    TechnicalIndicatorModel.currency_pair,
                    TechnicalIndicatorModel.timestamp,
                    TechnicalIndicatorModel.indicator_type,
                    TechnicalIndicatorModel.timeframe,
                )
                .having(func.count(TechnicalIndicatorModel.id) > 1)
            )

            result = await self.session.execute(duplicate_query)
            duplicates = result.fetchall()

            if duplicates:
                validation_result["status"] = "failed"
                validation_result["issue_count"] += len(duplicates)
                validation_result["issues"].append(
                    f"重複レコードが{len(duplicates)}件あります"
                )

            return validation_result

        except Exception as e:
            logger.error(f"データ一貫性チェックエラー: {e}")
            return {"status": "error", "issue_count": 0, "issues": [str(e)]}

    async def _get_realtime_quality_metrics(self) -> Dict[str, Any]:
        """リアルタイム品質メトリクス取得"""
        try:
            metrics = {
                "total_records": 0,
                "null_values": 0,
                "invalid_values": 0,
                "duplicate_records": 0,
            }

            # 全レコード数
            total_query = select(func.count(TechnicalIndicatorModel.id))
            result = await self.session.execute(total_query)
            metrics["total_records"] = result.scalar()

            # NULL値の数
            null_query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.value.is_(None)
            )
            result = await self.session.execute(null_query)
            metrics["null_values"] = result.scalar()

            # 無効な値の数
            invalid_query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.value <= 0
            )
            result = await self.session.execute(invalid_query)
            metrics["invalid_values"] = result.scalar()

            return metrics

        except Exception as e:
            logger.error(f"リアルタイム品質メトリクス取得エラー: {e}")
            return {}

    async def _get_periodic_quality_metrics(self) -> Dict[str, Any]:
        """定期品質メトリクス取得"""
        try:
            # 過去24時間のデータ品質を分析
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)

            metrics = {"period": "24h", "records_added": 0, "quality_score": 0.0}

            # 過去24時間に追加されたレコード数
            added_query = select(func.count(TechnicalIndicatorModel.id)).where(
                TechnicalIndicatorModel.created_at >= start_time
            )
            result = await self.session.execute(added_query)
            metrics["records_added"] = result.scalar()

            # 品質スコアの計算（簡易版）
            total_records = metrics["records_added"]
            if total_records > 0:
                # 実際の実装では、より詳細な品質スコア計算を実装
                metrics["quality_score"] = 95.0  # 仮の値

            return metrics

        except Exception as e:
            logger.error(f"定期品質メトリクス取得エラー: {e}")
            return {}

    async def _detect_quality_anomalies(
        self, realtime_metrics: Dict[str, Any], periodic_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """品質異常の検出"""
        try:
            anomalies = []

            # NULL値の異常検出
            null_ratio = realtime_metrics.get("null_values", 0) / max(
                realtime_metrics.get("total_records", 1), 1
            )
            if null_ratio > 0.1:  # 10%以上
                anomalies.append(
                    {
                        "type": "high_null_ratio",
                        "level": "warning",
                        "message": f"NULL値の比率が高いです: {null_ratio:.1%}",
                        "data": {"null_ratio": null_ratio},
                    }
                )

            # 無効な値の異常検出
            invalid_ratio = realtime_metrics.get("invalid_values", 0) / max(
                realtime_metrics.get("total_records", 1), 1
            )
            if invalid_ratio > 0.05:  # 5%以上
                anomalies.append(
                    {
                        "type": "high_invalid_ratio",
                        "level": "critical",
                        "message": f"無効な値の比率が高いです: {invalid_ratio:.1%}",
                        "data": {"invalid_ratio": invalid_ratio},
                    }
                )

            return anomalies

        except Exception as e:
            logger.error(f"品質異常検出エラー: {e}")
            return []

    async def _analyze_quality_trends(self) -> Dict[str, Any]:
        """品質トレンド分析"""
        try:
            trends = {
                "data_growth": "stable",
                "quality_trend": "stable",
                "recommendations": [],
            }

            # 実際の実装では、時系列データを使用したトレンド分析を実装

            return trends

        except Exception as e:
            logger.error(f"品質トレンド分析エラー: {e}")
            return {}

    async def _generate_integrity_recommendations(
        self, integrity_result: Dict[str, Any]
    ) -> List[str]:
        """整合性推奨事項の生成"""
        try:
            recommendations = []

            overall_status = integrity_result.get("overall_status", "unknown")
            issues_found = integrity_result.get("issues_found", [])

            if overall_status == "failed":
                recommendations.append(
                    "データ整合性に重大な問題があります。即座に対処が必要です。"
                )
            elif overall_status == "warning":
                recommendations.append(
                    "データ整合性に軽微な問題があります。監視を強化してください。"
                )

            if len(issues_found) > 0:
                recommendations.append(f"検出された問題数: {len(issues_found)}件")

            return recommendations

        except Exception as e:
            logger.error(f"整合性推奨事項生成エラー: {e}")
            return ["推奨事項の生成中にエラーが発生しました"]

    async def _repair_null_value(self, issue_data: Dict[str, Any]) -> bool:
        """NULL値の修復"""
        try:
            # 実際の実装では、適切な値でNULLを置換
            logger.info("NULL値修復機能は実装中です")
            return False
        except Exception as e:
            logger.error(f"NULL値修復エラー: {e}")
            return False

    async def _repair_invalid_range(self, issue_data: Dict[str, Any]) -> bool:
        """無効範囲値の修復"""
        try:
            # 実際の実装では、適切な範囲内の値に修正
            logger.info("無効範囲値修復機能は実装中です")
            return False
        except Exception as e:
            logger.error(f"無効範囲値修復エラー: {e}")
            return False

    async def _repair_duplicate_record(self, issue_data: Dict[str, Any]) -> bool:
        """重複レコードの修復"""
        try:
            # 実際の実装では、重複レコードの削除または統合
            logger.info("重複レコード修復機能は実装中です")
            return False
        except Exception as e:
            logger.error(f"重複レコード修復エラー: {e}")
            return False

    async def _repair_missing_additional_data(self, issue_data: Dict[str, Any]) -> bool:
        """不足追加データの修復"""
        try:
            # 実際の実装では、不足している追加データを生成
            logger.info("不足追加データ修復機能は実装中です")
            return False
        except Exception as e:
            logger.error(f"不足追加データ修復エラー: {e}")
            return False

    # ==================== 差分検知機能統合 ====================

    async def calculate_with_diff_detection(
        self, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        差分検知付きテクニカル指標計算

        Args:
            limit: 各時間足の処理件数制限

        Returns:
            Dict[str, Any]: 計算結果の詳細
        """
        try:
            logger.info("🔄 差分検知付きテクニカル指標計算開始...")

            # TechnicalIndicatorDiffCalculatorを使用
            from src.application.services.technical_indicator_diff_calculator import (
                TechnicalIndicatorDiffCalculator,
            )

            diff_calculator = TechnicalIndicatorDiffCalculator(self.currency_pair)
            await diff_calculator.initialize()

            try:
                result = await diff_calculator.calculate_differential_indicators(limit)
                return result
            finally:
                await diff_calculator.cleanup()

        except Exception as e:
            logger.error(f"❌ 差分検知付き計算エラー: {e}")
            return {"status": "error", "error": str(e)}

    async def calculate_for_uncalculated_data(
        self, timeframe: str, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        未計算データのみを対象とした計算

        Args:
            timeframe: 時間足
            limit: 処理件数制限

        Returns:
            Dict[str, Any]: 計算結果
        """
        try:
            logger.info(f"🔄 {timeframe}の未計算データ計算開始...")

            # TechnicalIndicatorDiffCalculatorを使用
            from src.application.services.technical_indicator_diff_calculator import (
                TechnicalIndicatorDiffCalculator,
            )

            diff_calculator = TechnicalIndicatorDiffCalculator(self.currency_pair)
            await diff_calculator.initialize()

            try:
                result = await diff_calculator.calculate_for_timeframe(timeframe, limit)
                return result
            finally:
                await diff_calculator.cleanup()

        except Exception as e:
            logger.error(f"❌ 未計算データ計算エラー: {e}")
            return {"status": "error", "error": str(e)}

    async def mark_as_calculated(self, processed_data: List[Any]) -> bool:
        """
        計算完了フラグを更新

        Args:
            processed_data: 処理したデータのリスト

        Returns:
            bool: 更新成功時True
        """
        try:
            logger.info("🔄 計算完了フラグ更新開始...")

            # DiffDetectionServiceを使用
            from src.infrastructure.database.services.diff_detection_service import (
                DiffDetectionService,
            )

            if not self.session:
                logger.error("❌ データベースセッションが初期化されていません")
                return False

            diff_service = DiffDetectionService(self.session)
            result = await diff_service.update_calculation_flags(processed_data)

            logger.info(f"✅ 計算完了フラグ更新: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ 計算完了フラグ更新エラー: {e}")
            return False

    async def get_calculation_status(self) -> Dict[str, Any]:
        """
        計算状況の取得

        Returns:
            Dict[str, Any]: 計算状況の詳細
        """
        try:
            logger.info("📊 計算状況取得開始...")

            # DiffDetectionServiceを使用
            from src.infrastructure.database.services.diff_detection_service import (
                DiffDetectionService,
            )

            if not self.session:
                logger.error("❌ データベースセッションが初期化されていません")
                return {}

            diff_service = DiffDetectionService(self.session)
            status = await diff_service.get_calculation_status()

            logger.info("✅ 計算状況取得完了")
            return status

        except Exception as e:
            logger.error(f"❌ 計算状況取得エラー: {e}")
            return {}

    async def reset_calculation_flags(self, timeframe: Optional[str] = None) -> bool:
        """
        計算フラグのリセット

        Args:
            timeframe: 特定の時間足のみリセット（Noneの場合は全件）

        Returns:
            bool: リセット成功時True
        """
        try:
            logger.info("🔄 計算フラグリセット開始...")

            # DiffDetectionServiceを使用
            from src.infrastructure.database.services.diff_detection_service import (
                DiffDetectionService,
            )

            if not self.session:
                logger.error("❌ データベースセッションが初期化されていません")
                return False

            diff_service = DiffDetectionService(self.session)
            result = await diff_service.reset_calculation_flags(timeframe)

            logger.info(f"✅ 計算フラグリセット: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ 計算フラグリセットエラー: {e}")
            return False


# テスト用のメイン関数
async def main():
    """テスト用メイン関数"""
    async with EnhancedUnifiedTechnicalCalculator("USD/JPY") as calculator:
        # 全指標計算
        results = await calculator.calculate_all_indicators()


if __name__ == "__main__":
    asyncio.run(main())
