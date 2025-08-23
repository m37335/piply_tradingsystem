"""
パターン15 V3 バッファ付き極値検出デバッグスクリプト

バッファ付き極値検出の詳細分析とデバッグ
"""

import asyncio
import logging
from typing import Dict

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector_v3 import (
    SupportResistanceDetectorV3,
)
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15V3BufferedPeaksDebugger:
    """パターン15 V3 バッファ付き極値検出デバッガー"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]

    async def debug_buffered_peaks(self) -> Dict:
        """バッファ付き極値検出の詳細デバッグ"""
        logger.info("=== パターン15 V3 バッファ付き極値検出デバッグ開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            results = {}
            for timeframe in self.timeframes:
                logger.info(f"デバッグ時間足: {timeframe}")
                result = await self._debug_single_timeframe(timeframe)
                results[timeframe] = result

            # データベース接続終了
            await db_manager.close()

            return results

        except Exception as e:
            logger.error(f"バッファ付き極値検出デバッグエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _debug_single_timeframe(self, timeframe: str) -> Dict:
        """単一時間足のバッファ付き極値検出デバッグ"""
        try:
            # データ取得
            data = await self._fetch_market_data(100)  # 100件のデータ
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"  取得データ: {len(data)}件")

            # デテクター作成
            detector = SupportResistanceDetectorV3(timeframe)

            # バッファ付き極値検出の詳細分析
            debug_result = self._analyze_buffered_peaks_detailed(
                data, detector, timeframe
            )

            return {
                "timeframe": timeframe,
                "data_points": len(data),
                "debug_analysis": debug_result,
            }

        except Exception as e:
            logger.error(f"時間足デバッグエラー: {e}")
            return {"error": str(e)}

    def _analyze_buffered_peaks_detailed(
        self, data: pd.DataFrame, detector: SupportResistanceDetectorV3, timeframe: str
    ) -> Dict:
        """バッファ付き極値検出の詳細分析"""
        try:
            analysis = {}

            # 時間足別パラメータ
            analysis["timeframe_parameters"] = {
                "timeframe": timeframe,
                "min_peaks": detector.min_peaks,
                "analysis_period": detector.analysis_period,
                "buffer_percentile": detector.buffer_percentile,
                "min_line_strength": detector.min_line_strength,
                "max_angle": detector.max_angle,
                "price_tolerance": detector.price_tolerance,
            }

            # 価格データの基本統計
            high_prices = data["High"].values
            low_prices = data["Low"].values

            analysis["price_statistics"] = {
                "high_prices": {
                    "min": np.min(high_prices),
                    "max": np.max(high_prices),
                    "mean": np.mean(high_prices),
                    "std": np.std(high_prices),
                    "percentiles": {
                        "10": np.percentile(high_prices, 10),
                        "25": np.percentile(high_prices, 25),
                        "50": np.percentile(high_prices, 50),
                        "75": np.percentile(high_prices, 75),
                        "90": np.percentile(high_prices, 90),
                    },
                },
                "low_prices": {
                    "min": np.min(low_prices),
                    "max": np.max(low_prices),
                    "mean": np.mean(low_prices),
                    "std": np.std(low_prices),
                    "percentiles": {
                        "10": np.percentile(low_prices, 10),
                        "25": np.percentile(low_prices, 25),
                        "50": np.percentile(low_prices, 50),
                        "75": np.percentile(low_prices, 75),
                        "90": np.percentile(low_prices, 90),
                    },
                },
            }

            # レジスタンスライン用のバッファ付き極大値検出
            resistance_peaks = self._debug_find_buffered_peaks(
                high_prices, "max", detector
            )
            analysis["resistance_peaks"] = resistance_peaks

            # サポートライン用のバッファ付き極小値検出
            support_troughs = self._debug_find_buffered_peaks(
                low_prices, "min", detector
            )
            analysis["support_troughs"] = support_troughs

            # バッファゾーンの可視化
            analysis["buffer_zones"] = self._analyze_buffer_zones(
                high_prices, low_prices, detector
            )

            return analysis

        except Exception as e:
            logger.error(f"バッファ付き極値詳細分析エラー: {e}")
            return {"error": str(e)}

    def _debug_find_buffered_peaks(
        self, prices: np.ndarray, peak_type: str, detector: SupportResistanceDetectorV3
    ) -> Dict:
        """バッファ付き極値検出の詳細デバッグ"""
        try:
            debug_info = {}

            if peak_type == "max":
                # 上位N%の価格帯をバッファとして定義
                threshold = np.percentile(prices, 100 - detector.buffer_percentile)
                debug_info["threshold"] = threshold
                debug_info["threshold_percentile"] = 100 - detector.buffer_percentile

                # find_peaksでの検出
                peaks, properties = find_peaks(prices, height=threshold, distance=1)
                debug_info["find_peaks_result"] = {
                    "peaks": peaks.tolist(),
                    "peak_count": len(peaks),
                    "properties": properties,
                }

                # フォールバック処理
                if len(peaks) == 0:
                    sorted_indices = np.argsort(prices)[::-1]
                    fallback_peaks = sorted_indices[: detector.min_peaks]
                    debug_info["fallback_peaks"] = {
                        "peaks": fallback_peaks.tolist(),
                        "peak_count": len(fallback_peaks),
                        "triggered": True,
                        "reason": "find_peaks returned 0 peaks",
                    }
                    final_peaks = fallback_peaks
                else:
                    debug_info["fallback_peaks"] = {
                        "triggered": False,
                        "reason": "find_peaks returned peaks",
                    }
                    final_peaks = peaks

            else:  # min
                # 下位N%の価格帯をバッファとして定義
                threshold = np.percentile(prices, detector.buffer_percentile)
                debug_info["threshold"] = threshold
                debug_info["threshold_percentile"] = detector.buffer_percentile

                # find_peaksでの検出（負の値で検出）
                peaks, properties = find_peaks(-prices, height=-threshold, distance=1)
                debug_info["find_peaks_result"] = {
                    "peaks": peaks.tolist(),
                    "peak_count": len(peaks),
                    "properties": properties,
                }

                # フォールバック処理
                if len(peaks) == 0:
                    sorted_indices = np.argsort(prices)
                    fallback_peaks = sorted_indices[: detector.min_peaks]
                    debug_info["fallback_peaks"] = {
                        "peaks": fallback_peaks.tolist(),
                        "peak_count": len(fallback_peaks),
                        "triggered": True,
                        "reason": "find_peaks returned 0 peaks",
                    }
                    final_peaks = fallback_peaks
                else:
                    debug_info["fallback_peaks"] = {
                        "triggered": False,
                        "reason": "find_peaks returned peaks",
                    }
                    final_peaks = peaks

            # 最終結果
            debug_info["final_result"] = {
                "peaks": final_peaks.tolist(),
                "peak_count": len(final_peaks),
                "peak_prices": [prices[i] for i in final_peaks],
                "meets_minimum": len(final_peaks) >= detector.min_peaks,
            }

            # バッファゾーン内の価格ポイント数
            if peak_type == "max":
                buffer_zone_points = np.sum(prices >= threshold)
            else:
                buffer_zone_points = np.sum(prices <= threshold)

            debug_info["buffer_zone_analysis"] = {
                "buffer_zone_points": int(buffer_zone_points),
                "buffer_zone_percentage": (buffer_zone_points / len(prices)) * 100,
                "total_points": len(prices),
            }

            return debug_info

        except Exception as e:
            logger.error(f"バッファ付き極値検出デバッグエラー: {e}")
            return {"error": str(e)}

    def _analyze_buffer_zones(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        detector: SupportResistanceDetectorV3,
    ) -> Dict:
        """バッファゾーンの分析"""
        try:
            analysis = {}

            # レジスタンス用バッファゾーン
            resistance_threshold = np.percentile(
                high_prices, 100 - detector.buffer_percentile
            )
            resistance_zone_points = high_prices >= resistance_threshold
            resistance_zone_indices = np.where(resistance_zone_points)[0]

            analysis["resistance_buffer_zone"] = {
                "threshold": resistance_threshold,
                "threshold_percentile": 100 - detector.buffer_percentile,
                "zone_points": int(np.sum(resistance_zone_points)),
                "zone_percentage": (np.sum(resistance_zone_points) / len(high_prices))
                * 100,
                "zone_indices": resistance_zone_indices.tolist()[:10],  # 最初の10個
                "zone_prices": high_prices[resistance_zone_points][
                    :10
                ].tolist(),  # 最初の10個
            }

            # サポート用バッファゾーン
            support_threshold = np.percentile(low_prices, detector.buffer_percentile)
            support_zone_points = low_prices <= support_threshold
            support_zone_indices = np.where(support_zone_points)[0]

            analysis["support_buffer_zone"] = {
                "threshold": support_threshold,
                "threshold_percentile": detector.buffer_percentile,
                "zone_points": int(np.sum(support_zone_points)),
                "zone_percentage": (np.sum(support_zone_points) / len(low_prices))
                * 100,
                "zone_indices": support_zone_indices.tolist()[:10],  # 最初の10個
                "zone_prices": low_prices[support_zone_points][:10].tolist(),  # 最初の10個
            }

            return analysis

        except Exception as e:
            logger.error(f"バッファゾーン分析エラー: {e}")
            return {"error": str(e)}

    async def _fetch_market_data(self, limit: int) -> pd.DataFrame:
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
                    LIMIT :limit
                """
                )

                result = await session.execute(query, {"limit": limit})
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
    debugger = Pattern15V3BufferedPeaksDebugger()
    results = await debugger.debug_buffered_peaks()

    if "error" in results:
        print(f"\n❌ デバッグエラー: {results['error']}")
        return

    print("\n=== パターン15 V3 バッファ付き極値検出デバッグ結果 ===")

    for timeframe, result in results.items():
        if "error" in result:
            print(f"\n❌ {timeframe}: {result['error']}")
            continue

        print(f"\n📊 {timeframe} ({result['data_points']}件):")

        debug_analysis = result.get("debug_analysis", {})

        # 時間足別パラメータ
        tf_params = debug_analysis.get("timeframe_parameters", {})
        print(f"  ⚙️ 時間足別パラメータ:")
        print(f"    時間足: {tf_params.get('timeframe')}")
        print(f"    最小ピーク数: {tf_params.get('min_peaks')}")
        print(f"    分析期間: {tf_params.get('analysis_period')}ポイント")
        print(f"    バッファ百分位: {tf_params.get('buffer_percentile')}%")
        print(f"    最小ライン強度: {tf_params.get('min_line_strength')}")
        print(f"    最大角度: {tf_params.get('max_angle')}度")
        print(f"    価格許容誤差: {tf_params.get('price_tolerance'):.3f}")

        # 価格統計
        price_stats = debug_analysis.get("price_statistics", {})
        if price_stats:
            print(f"  📈 価格統計:")

            high_stats = price_stats.get("high_prices", {})
            print(f"    高値:")
            print(f"      最小: {high_stats.get('min', 0):.5f}")
            print(f"      最大: {high_stats.get('max', 0):.5f}")
            print(f"      平均: {high_stats.get('mean', 0):.5f}")
            print(f"      標準偏差: {high_stats.get('std', 0):.5f}")

            high_percentiles = high_stats.get("percentiles", {})
            print(f"      百分位:")
            print(f"        10%: {high_percentiles.get('10', 0):.5f}")
            print(f"        25%: {high_percentiles.get('25', 0):.5f}")
            print(f"        50%: {high_percentiles.get('50', 0):.5f}")
            print(f"        75%: {high_percentiles.get('75', 0):.5f}")
            print(f"        90%: {high_percentiles.get('90', 0):.5f}")

            low_stats = price_stats.get("low_prices", {})
            print(f"    安値:")
            print(f"      最小: {low_stats.get('min', 0):.5f}")
            print(f"      最大: {low_stats.get('max', 0):.5f}")
            print(f"      平均: {low_stats.get('mean', 0):.5f}")
            print(f"      標準偏差: {low_stats.get('std', 0):.5f}")

            low_percentiles = low_stats.get("percentiles", {})
            print(f"      百分位:")
            print(f"        10%: {low_percentiles.get('10', 0):.5f}")
            print(f"        25%: {low_percentiles.get('25', 0):.5f}")
            print(f"        50%: {low_percentiles.get('50', 0):.5f}")
            print(f"        75%: {low_percentiles.get('75', 0):.5f}")
            print(f"        90%: {low_percentiles.get('90', 0):.5f}")

        # レジスタンスピーク
        resistance_peaks = debug_analysis.get("resistance_peaks", {})
        if resistance_peaks:
            print(f"  🔺 レジスタンスピーク検出:")
            print(
                f"    閾値: {resistance_peaks.get('threshold', 0):.5f} (上位{resistance_peaks.get('threshold_percentile', 0)}%)"
            )

            find_peaks_result = resistance_peaks.get("find_peaks_result", {})
            print(f"    find_peaks結果:")
            print(f"      ピーク数: {find_peaks_result.get('peak_count', 0)}")
            print(f"      ピークインデックス: {find_peaks_result.get('peaks', [])[:5]}")

            fallback_peaks = resistance_peaks.get("fallback_peaks", {})
            if fallback_peaks.get("triggered", False):
                print(f"    ⚠️ フォールバック処理:")
                print(f"      理由: {fallback_peaks.get('reason', '')}")
                print(f"      ピーク数: {fallback_peaks.get('peak_count', 0)}")
                print(f"      ピークインデックス: {fallback_peaks.get('peaks', [])[:5]}")

            final_result = resistance_peaks.get("final_result", {})
            print(f"    最終結果:")
            print(f"      ピーク数: {final_result.get('peak_count', 0)}")
            print(
                f"      最小要件満足: {'✅' if final_result.get('meets_minimum', False) else '❌'}"
            )
            print(f"      ピーク価格: {final_result.get('peak_prices', [])[:5]}")

            buffer_zone = resistance_peaks.get("buffer_zone_analysis", {})
            print(f"    バッファゾーン:")
            print(f"      ゾーン内ポイント数: {buffer_zone.get('buffer_zone_points', 0)}")
            print(f"      ゾーン割合: {buffer_zone.get('buffer_zone_percentage', 0):.1f}%")

        # サポートボトム
        support_troughs = debug_analysis.get("support_troughs", {})
        if support_troughs:
            print(f"  🔻 サポートボトム検出:")
            print(
                f"    閾値: {support_troughs.get('threshold', 0):.5f} (下位{support_troughs.get('threshold_percentile', 0)}%)"
            )

            find_peaks_result = support_troughs.get("find_peaks_result", {})
            print(f"    find_peaks結果:")
            print(f"      ボトム数: {find_peaks_result.get('peak_count', 0)}")
            print(f"      ボトムインデックス: {find_peaks_result.get('peaks', [])[:5]}")

            fallback_peaks = support_troughs.get("fallback_peaks", {})
            if fallback_peaks.get("triggered", False):
                print(f"    ⚠️ フォールバック処理:")
                print(f"      理由: {fallback_peaks.get('reason', '')}")
                print(f"      ボトム数: {fallback_peaks.get('peak_count', 0)}")
                print(f"      ボトムインデックス: {fallback_peaks.get('peaks', [])[:5]}")

            final_result = support_troughs.get("final_result", {})
            print(f"    最終結果:")
            print(f"      ボトム数: {final_result.get('peak_count', 0)}")
            print(
                f"      最小要件満足: {'✅' if final_result.get('meets_minimum', False) else '❌'}"
            )
            print(f"      ボトム価格: {final_result.get('peak_prices', [])[:5]}")

            buffer_zone = support_troughs.get("buffer_zone_analysis", {})
            print(f"    バッファゾーン:")
            print(f"      ゾーン内ポイント数: {buffer_zone.get('buffer_zone_points', 0)}")
            print(f"      ゾーン割合: {buffer_zone.get('buffer_zone_percentage', 0):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
