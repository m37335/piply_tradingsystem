"""
TA-Lib線形回帰機能の詳細デバッグ

TA-LibのLINEARREG、LINEARREG_SLOPE、LINEARREG_INTERCEPTが
どのようなデータを元に計算しているかを詳しく調べる
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
import talib
from sqlalchemy import text

from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TALibLinearRegressionDebugger:
    """TA-Lib線形回帰デバッガー"""

    def __init__(self):
        self.test_periods = [14, 20, 30, 50]

    async def debug_talib_linear_regression(self) -> Dict:
        """TA-Lib線形回帰の詳細デバッグ"""
        logger.info("=== TA-Lib線形回帰詳細デバッグ開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # テストデータ取得（1ヶ月分）
            data = await self._fetch_market_data(30)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"取得データ: {len(data)}件")

            # 各期間での線形回帰詳細分析
            results = {}
            for period in self.test_periods:
                logger.info(f"期間 {period} での分析:")
                result = self._analyze_linear_regression_period(data, period)
                results[f"period_{period}"] = result

            # データベース接続終了
            await db_manager.close()

            return {
                "results": results,
                "analysis_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"TA-Lib線形回帰デバッグエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    def _analyze_linear_regression_period(self, data: pd.DataFrame, period: int) -> Dict:
        """特定期間での線形回帰詳細分析"""
        try:
            analysis = {}

            # 価格データの準備
            high_prices = data['High'].values
            low_prices = data['Low'].values
            close_prices = data['Close'].values

            # 高値での線形回帰分析
            high_analysis = self._analyze_single_linear_regression(
                high_prices, period, "high"
            )
            analysis["high_prices"] = high_analysis

            # 安値での線形回帰分析
            low_analysis = self._analyze_single_linear_regression(
                low_prices, period, "low"
            )
            analysis["low_prices"] = low_analysis

            # 終値での線形回帰分析
            close_analysis = self._analyze_single_linear_regression(
                close_prices, period, "close"
            )
            analysis["close_prices"] = close_analysis

            return analysis

        except Exception as e:
            logger.error(f"期間 {period} 分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_single_linear_regression(self, prices: np.ndarray, period: int, price_type: str) -> Dict:
        """単一価格系列での線形回帰詳細分析"""
        try:
            analysis = {}

            # TA-Lib線形回帰の計算
            linear_reg = talib.LINEARREG(prices, timeperiod=period)
            slope = talib.LINEARREG_SLOPE(prices, timeperiod=period)
            intercept = talib.LINEARREG_INTERCEPT(prices, timeperiod=period)

            # 基本統計
            analysis["basic_stats"] = {
                "total_points": len(prices),
                "period": period,
                "price_type": price_type,
                "price_range": {
                    "min": float(np.min(prices)),
                    "max": float(np.max(prices)),
                    "mean": float(np.mean(prices)),
                    "std": float(np.std(prices))
                }
            }

            # 線形回帰結果の統計
            valid_reg = linear_reg[~np.isnan(linear_reg)]
            valid_slope = slope[~np.isnan(slope)]
            valid_intercept = intercept[~np.isnan(intercept)]

            analysis["regression_stats"] = {
                "valid_points": len(valid_reg),
                "nan_points": len(prices) - len(valid_reg),
                "regression_range": {
                    "min": float(np.min(valid_reg)) if len(valid_reg) > 0 else None,
                    "max": float(np.max(valid_reg)) if len(valid_reg) > 0 else None,
                    "mean": float(np.mean(valid_reg)) if len(valid_reg) > 0 else None,
                    "std": float(np.std(valid_reg)) if len(valid_reg) > 0 else None
                },
                "slope_stats": {
                    "min": float(np.min(valid_slope)) if len(valid_slope) > 0 else None,
                    "max": float(np.max(valid_slope)) if len(valid_slope) > 0 else None,
                    "mean": float(np.mean(valid_slope)) if len(valid_slope) > 0 else None,
                    "std": float(np.std(valid_slope)) if len(valid_slope) > 0 else None
                },
                "intercept_stats": {
                    "min": float(np.min(valid_intercept)) if len(valid_intercept) > 0 else None,
                    "max": float(np.max(valid_intercept)) if len(valid_intercept) > 0 else None,
                    "mean": float(np.mean(valid_intercept)) if len(valid_intercept) > 0 else None,
                    "std": float(np.std(valid_intercept)) if len(valid_intercept) > 0 else None
                }
            }

            # 最新の値の詳細分析
            if len(valid_reg) > 0:
                latest_idx = len(valid_reg) - 1
                latest_analysis = self._analyze_latest_values(
                    prices, linear_reg, slope, intercept, period, latest_idx
                )
                analysis["latest_analysis"] = latest_analysis

            # 線形回帰の計算原理の説明
            analysis["calculation_explanation"] = self._explain_linear_regression_calculation(
                prices, period
            )

            return analysis

        except Exception as e:
            logger.error(f"単一線形回帰分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_latest_values(self, prices: np.ndarray, linear_reg: np.ndarray, 
                             slope: np.ndarray, intercept: np.ndarray, 
                             period: int, latest_idx: int) -> Dict:
        """最新値の詳細分析"""
        try:
            analysis = {}

            # 最新の線形回帰値
            latest_reg = linear_reg[latest_idx]
            latest_slope = slope[latest_idx]
            latest_intercept = intercept[latest_idx]
            latest_price = prices[latest_idx]

            # 線形回帰に使用されたデータポイント
            start_idx = max(0, latest_idx - period + 1)
            end_idx = latest_idx + 1
            regression_data = prices[start_idx:end_idx]
            regression_indices = np.arange(start_idx, end_idx)

            analysis["latest_values"] = {
                "latest_price": float(latest_price),
                "latest_regression": float(latest_reg),
                "latest_slope": float(latest_slope),
                "latest_intercept": float(latest_intercept),
                "data_points_used": len(regression_data),
                "start_index": start_idx,
                "end_index": end_idx,
                "regression_data": {
                    "prices": regression_data.tolist(),
                    "indices": regression_indices.tolist()
                }
            }

            # 手動計算との比較
            manual_calculation = self._manual_linear_regression(regression_data, regression_indices)
            analysis["manual_calculation"] = manual_calculation

            # 計算の検証
            verification = self._verify_calculation(
                latest_reg, latest_slope, latest_intercept, 
                regression_data, regression_indices
            )
            analysis["verification"] = verification

            return analysis

        except Exception as e:
            logger.error(f"最新値分析エラー: {e}")
            return {"error": str(e)}

    def _manual_linear_regression(self, y_values: np.ndarray, x_values: np.ndarray) -> Dict:
        """手動での線形回帰計算"""
        try:
            # 最小二乗法による線形回帰
            n = len(x_values)
            if n < 2:
                return {"error": "データポイントが不足"}

            # 平均値
            x_mean = np.mean(x_values)
            y_mean = np.mean(y_values)

            # 傾きの計算: slope = Σ((x - x_mean) * (y - y_mean)) / Σ((x - x_mean)²)
            numerator = np.sum((x_values - x_mean) * (y_values - y_mean))
            denominator = np.sum((x_values - x_mean) ** 2)

            if denominator == 0:
                return {"error": "分母が0（水平線）"}

            slope = numerator / denominator

            # 切片の計算: intercept = y_mean - slope * x_mean
            intercept = y_mean - slope * x_mean

            # 決定係数（R²）の計算
            y_pred = slope * x_values + intercept
            ss_res = np.sum((y_values - y_pred) ** 2)
            ss_tot = np.sum((y_values - y_mean) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

            return {
                "slope": float(slope),
                "intercept": float(intercept),
                "r_squared": float(r_squared),
                "x_mean": float(x_mean),
                "y_mean": float(y_mean),
                "numerator": float(numerator),
                "denominator": float(denominator)
            }

        except Exception as e:
            logger.error(f"手動線形回帰計算エラー: {e}")
            return {"error": str(e)}

    def _verify_calculation(self, ta_reg: float, ta_slope: float, ta_intercept: float,
                          y_values: np.ndarray, x_values: np.ndarray) -> Dict:
        """TA-Lib計算の検証"""
        try:
            # 手動計算
            manual = self._manual_linear_regression(y_values, x_values)
            
            if "error" in manual:
                return {"error": manual["error"]}

            # 比較
            slope_diff = abs(ta_slope - manual["slope"])
            intercept_diff = abs(ta_intercept - manual["intercept"])

            # 最新点での予測値
            latest_x = x_values[-1]
            ta_prediction = ta_slope * latest_x + ta_intercept
            manual_prediction = manual["slope"] * latest_x + manual["intercept"]

            return {
                "slope_comparison": {
                    "ta_lib": float(ta_slope),
                    "manual": float(manual["slope"]),
                    "difference": float(slope_diff),
                    "match": slope_diff < 1e-10
                },
                "intercept_comparison": {
                    "ta_lib": float(ta_intercept),
                    "manual": float(manual["intercept"]),
                    "difference": float(intercept_diff),
                    "match": intercept_diff < 1e-10
                },
                "prediction_comparison": {
                    "ta_lib": float(ta_prediction),
                    "manual": float(manual_prediction),
                    "ta_reg_value": float(ta_reg),
                    "difference": float(abs(ta_prediction - ta_reg))
                },
                "r_squared": float(manual["r_squared"])
            }

        except Exception as e:
            logger.error(f"計算検証エラー: {e}")
            return {"error": str(e)}

    def _explain_linear_regression_calculation(self, prices: np.ndarray, period: int) -> Dict:
        """線形回帰計算原理の説明"""
        try:
            explanation = {
                "method": "移動ウィンドウ線形回帰",
                "window_size": period,
                "calculation_process": [
                    "1. 各時点で、過去period個のデータポイントを使用",
                    "2. 最小二乗法による線形回帰: y = ax + b",
                    "3. x軸: データポイントのインデックス（0, 1, 2, ...）",
                    "4. y軸: 価格データ（High, Low, Close）",
                    "5. 各時点で新しい線形回帰値を計算",
                    "6. 最初の(period-1)個のポイントはNaN（データ不足）"
                ],
                "formula": {
                    "slope": "a = Σ((x - x_mean) * (y - y_mean)) / Σ((x - x_mean)²)",
                    "intercept": "b = y_mean - a * x_mean",
                    "prediction": "y_pred = a * x + b"
                },
                "example": {
                    "period_14": "過去14個のデータポイントで線形回帰",
                    "period_20": "過去20個のデータポイントで線形回帰",
                    "period_30": "過去30個のデータポイントで線形回帰",
                    "period_50": "過去50個のデータポイントで線形回帰"
                }
            }

            return explanation

        except Exception as e:
            logger.error(f"説明生成エラー: {e}")
            return {"error": str(e)}

    async def _fetch_market_data(self, days: int) -> pd.DataFrame:
        """市場データ取得"""
        try:
            async with db_manager.get_session() as session:
                query = text(
                    """
                    SELECT 
                        timestamp as Date,
                        open_price as Open,
                        high_price as High,
                        low_price as Low,
                        close_price as Close,
                        volume as Volume
                    FROM price_data 
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT :days
                    """
                )

                result = await session.execute(query, {"days": days})
                rows = result.fetchall()

                if not rows:
                    return pd.DataFrame()

                data = pd.DataFrame(
                    rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
                )

                data = data.sort_values("Date").reset_index(drop=True)
                return data

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return pd.DataFrame()


async def main():
    """メイン関数"""
    debugger = TALibLinearRegressionDebugger()
    results = await debugger.debug_talib_linear_regression()
    
    if "error" in results:
        print(f"\n❌ デバッグエラー: {results['error']}")
        return
    
    print("\n=== TA-Lib線形回帰詳細デバッグ結果 ===")
    
    results_data = results.get("results", {})
    
    for period_key, period_data in results_data.items():
        print(f"\n📊 {period_key}:")
        
        for price_type, analysis in period_data.items():
            print(f"\n  {price_type.upper()}価格:")
            
            # 基本統計
            basic_stats = analysis.get("basic_stats", {})
            print(f"    データポイント数: {basic_stats.get('total_points', 0)}")
            print(f"    価格範囲: {basic_stats.get('price_range', {}).get('min', 0):.2f} - {basic_stats.get('price_range', {}).get('max', 0):.2f}")
            
            # 回帰統計
            reg_stats = analysis.get("regression_stats", {})
            print(f"    有効ポイント: {reg_stats.get('valid_points', 0)}")
            print(f"    NaNポイント: {reg_stats.get('nan_points', 0)}")
            
            # 最新分析
            latest_analysis = analysis.get("latest_analysis", {})
            if latest_analysis:
                latest_values = latest_analysis.get("latest_values", {})
                print(f"    最新価格: {latest_values.get('latest_price', 0):.2f}")
                print(f"    最新回帰値: {latest_values.get('latest_regression', 0):.2f}")
                print(f"    最新傾き: {latest_values.get('latest_slope', 0):.6f}")
                print(f"    最新切片: {latest_values.get('latest_intercept', 0):.2f}")
                print(f"    使用データポイント: {latest_values.get('data_points_used', 0)}")
                
                # 手動計算との比較
                manual_calc = latest_analysis.get("manual_calculation", {})
                if "error" not in manual_calc:
                    print(f"    手動計算傾き: {manual_calc.get('slope', 0):.6f}")
                    print(f"    手動計算切片: {manual_calc.get('intercept', 0):.2f}")
                    print(f"    決定係数R²: {manual_calc.get('r_squared', 0):.3f}")
                
                # 検証結果
                verification = latest_analysis.get("verification", {})
                if "error" not in verification:
                    slope_comp = verification.get("slope_comparison", {})
                    intercept_comp = verification.get("intercept_comparison", {})
                    
                    print(f"    傾き一致: {slope_comp.get('match', False)}")
                    print(f"    切片一致: {intercept_comp.get('match', False)}")
    
    # 計算原理の説明
    print(f"\n📚 計算原理:")
    first_period = list(results_data.values())[0]
    first_price_type = list(first_period.values())[0]
    explanation = first_price_type.get("calculation_explanation", {})
    
    print(f"  方法: {explanation.get('method', 'N/A')}")
    print(f"  ウィンドウサイズ: {explanation.get('window_size', 'N/A')}")
    print(f"  計算プロセス:")
    for step in explanation.get("calculation_process", []):
        print(f"    {step}")
    
    print(f"  数式:")
    formulas = explanation.get("formula", {})
    for name, formula in formulas.items():
        print(f"    {name}: {formula}")


if __name__ == "__main__":
    asyncio.run(main())
