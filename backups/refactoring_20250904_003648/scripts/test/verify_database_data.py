"""
データベース価格データ検証スクリプト

USD/JPYの価格データが正常かどうかを詳しく検証する
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DatabaseDataVerifier:
    """データベースデータ検証器"""

    def __init__(self):
        self.test_periods = [7, 30, 90, 365]

    async def verify_database_data(self) -> Dict:
        """データベースデータの詳細検証"""
        logger.info("=== データベース価格データ検証開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 基本データ情報
            basic_info = await self._get_basic_data_info()

            # 各期間でのデータ検証
            period_verifications = {}
            for period in self.test_periods:
                logger.info(f"期間 {period}日 での検証:")
                verification = await self._verify_period_data(period)
                period_verifications[f"{period}days"] = verification

            # 異常値検出
            anomaly_detection = await self._detect_anomalies()

            # データ品質評価
            quality_assessment = self._assess_data_quality(
                basic_info, period_verifications
            )

            # データベース接続終了
            await db_manager.close()

            return {
                "basic_info": basic_info,
                "period_verifications": period_verifications,
                "anomaly_detection": anomaly_detection,
                "quality_assessment": quality_assessment,
                "verification_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"データベース検証エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _get_basic_data_info(self) -> Dict:
        """基本データ情報の取得"""
        try:
            async with db_manager.get_session() as session:
                # 総レコード数
                count_query = text(
                    """
                    SELECT COUNT(*) as total_count
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    """
                )
                count_result = await session.execute(count_query)
                total_count = count_result.scalar()

                # 日付範囲
                date_range_query = text(
                    """
                    SELECT
                        MIN(timestamp) as earliest_date,
                        MAX(timestamp) as latest_date
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    """
                )
                date_result = await session.execute(date_range_query)
                date_row = date_result.fetchone()
                earliest_date = date_row[0] if date_row else None
                latest_date = date_row[1] if date_row else None

                # 通貨ペア別レコード数
                currency_query = text(
                    """
                    SELECT currency_pair, COUNT(*) as count
                    FROM price_data
                    GROUP BY currency_pair
                    ORDER BY count DESC
                    """
                )
                currency_result = await session.execute(currency_query)
                currency_counts = {row[0]: row[1] for row in currency_result.fetchall()}

                # 最新の数件のデータ
                recent_query = text(
                    """
                    SELECT
                        timestamp,
                        currency_pair,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT 10
                    """
                )
                recent_result = await session.execute(recent_query)
                recent_data = [
                    {
                        "timestamp": row[0],
                        "currency_pair": row[1],
                        "open": float(row[2]),
                        "high": float(row[3]),
                        "low": float(row[4]),
                        "close": float(row[5]),
                        "volume": float(row[6]) if row[6] else 0,
                    }
                    for row in recent_result.fetchall()
                ]

                return {
                    "total_records": total_count,
                    "date_range": {
                        "earliest": earliest_date,
                        "latest": latest_date,
                        "span_days": (
                            (
                                datetime.fromisoformat(latest_date)
                                - datetime.fromisoformat(earliest_date)
                            ).days
                            if earliest_date and latest_date
                            else 0
                        ),
                    },
                    "currency_distribution": currency_counts,
                    "recent_data": recent_data,
                }

        except Exception as e:
            logger.error(f"基本データ情報取得エラー: {e}")
            return {"error": str(e)}

    async def _verify_period_data(self, days: int) -> Dict:
        """特定期間でのデータ検証"""
        try:
            async with db_manager.get_session() as session:
                # 指定期間のデータ取得
                query = text(
                    """
                    SELECT
                        timestamp,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT :days
                    """
                )

                result = await session.execute(query, {"days": days})
                rows = result.fetchall()

                if not rows:
                    return {"error": f"期間{days}日のデータが見つかりません"}

                # DataFrameに変換
                data = pd.DataFrame(
                    rows,
                    columns=["timestamp", "open", "high", "low", "close", "volume"],
                )
                data = data.sort_values("timestamp").reset_index(drop=True)

                # 基本統計
                price_stats = {
                    "open": {
                        "min": float(data["open"].min()),
                        "max": float(data["open"].max()),
                        "mean": float(data["open"].mean()),
                        "std": float(data["open"].std()),
                        "unique_values": int(data["open"].nunique()),
                    },
                    "high": {
                        "min": float(data["high"].min()),
                        "max": float(data["high"].max()),
                        "mean": float(data["high"].mean()),
                        "std": float(data["high"].std()),
                        "unique_values": int(data["high"].nunique()),
                    },
                    "low": {
                        "min": float(data["low"].min()),
                        "max": float(data["low"].max()),
                        "mean": float(data["low"].mean()),
                        "std": float(data["low"].std()),
                        "unique_values": int(data["low"].nunique()),
                    },
                    "close": {
                        "min": float(data["close"].min()),
                        "max": float(data["close"].max()),
                        "mean": float(data["close"].mean()),
                        "std": float(data["close"].std()),
                        "unique_values": int(data["close"].nunique()),
                    },
                }

                # 価格変動分析
                price_changes = self._analyze_price_changes(data)

                # データの一貫性チェック
                consistency_checks = self._check_data_consistency(data)

                # 時系列分析
                time_series_analysis = self._analyze_time_series(data)

                return {
                    "data_points": len(data),
                    "date_range": {
                        "start": data["timestamp"].iloc[0],
                        "end": data["timestamp"].iloc[-1],
                    },
                    "price_statistics": price_stats,
                    "price_changes": price_changes,
                    "consistency_checks": consistency_checks,
                    "time_series_analysis": time_series_analysis,
                }

        except Exception as e:
            logger.error(f"期間{days}日検証エラー: {e}")
            return {"error": str(e)}

    def _analyze_price_changes(self, data: pd.DataFrame) -> Dict:
        """価格変動の分析"""
        try:
            analysis = {}

            # 日次変動
            if len(data) > 1:
                close_changes = data["close"].diff().dropna()
                analysis["daily_changes"] = {
                    "mean_change": float(close_changes.mean()),
                    "std_change": float(close_changes.std()),
                    "min_change": float(close_changes.min()),
                    "max_change": float(close_changes.max()),
                    "positive_changes": int((close_changes > 0).sum()),
                    "negative_changes": int((close_changes < 0).sum()),
                    "zero_changes": int((close_changes == 0).sum()),
                }

                # 変動率
                close_returns = data["close"].pct_change().dropna()
                analysis["daily_returns"] = {
                    "mean_return": float(close_returns.mean()),
                    "std_return": float(close_returns.std()),
                    "min_return": float(close_returns.min()),
                    "max_return": float(close_returns.max()),
                }

            # 価格範囲の分析
            price_ranges = data["high"] - data["low"]
            analysis["price_ranges"] = {
                "mean_range": float(price_ranges.mean()),
                "std_range": float(price_ranges.std()),
                "min_range": float(price_ranges.min()),
                "max_range": float(price_ranges.max()),
            }

            return analysis

        except Exception as e:
            logger.error(f"価格変動分析エラー: {e}")
            return {"error": str(e)}

    def _check_data_consistency(self, data: pd.DataFrame) -> Dict:
        """データの一貫性チェック"""
        try:
            checks = {}

            # 価格の論理的関係チェック
            high_low_consistent = (data["high"] >= data["low"]).all()
            high_open_consistent = (data["high"] >= data["open"]).all()
            high_close_consistent = (data["high"] >= data["close"]).all()
            low_open_consistent = (data["low"] <= data["open"]).all()
            low_close_consistent = (data["low"] <= data["close"]).all()

            checks["price_logic"] = {
                "high_ge_low": high_low_consistent,
                "high_ge_open": high_open_consistent,
                "high_ge_close": high_close_consistent,
                "low_le_open": low_open_consistent,
                "low_le_close": low_close_consistent,
                "all_consistent": all(
                    [
                        high_low_consistent,
                        high_open_consistent,
                        high_close_consistent,
                        low_open_consistent,
                        low_close_consistent,
                    ]
                ),
            }

            # ゼロ値チェック
            zero_checks = {
                "zero_open": int((data["open"] == 0).sum()),
                "zero_high": int((data["high"] == 0).sum()),
                "zero_low": int((data["low"] == 0).sum()),
                "zero_close": int((data["close"] == 0).sum()),
                "zero_volume": int((data["volume"] == 0).sum()),
            }
            checks["zero_values"] = zero_checks

            # 欠損値チェック
            missing_checks = {
                "missing_open": int(data["open"].isna().sum()),
                "missing_high": int(data["high"].isna().sum()),
                "missing_low": int(data["low"].isna().sum()),
                "missing_close": int(data["close"].isna().sum()),
                "missing_volume": int(data["volume"].isna().sum()),
            }
            checks["missing_values"] = missing_checks

            # 重複データチェック
            duplicate_checks = {
                "duplicate_timestamps": int(data["timestamp"].duplicated().sum()),
                "duplicate_open": int(data["open"].duplicated().sum()),
                "duplicate_high": int(data["high"].duplicated().sum()),
                "duplicate_low": int(data["low"].duplicated().sum()),
                "duplicate_close": int(data["close"].duplicated().sum()),
            }
            checks["duplicates"] = duplicate_checks

            return checks

        except Exception as e:
            logger.error(f"データ一貫性チェックエラー: {e}")
            return {"error": str(e)}

    def _analyze_time_series(self, data: pd.DataFrame) -> Dict:
        """時系列分析"""
        try:
            analysis = {}

            # 時系列の連続性
            timestamps = pd.to_datetime(data["timestamp"])
            time_diffs = timestamps.diff().dropna()

            analysis["time_continuity"] = {
                "total_periods": len(timestamps),
                "time_diffs": {
                    "mean": str(time_diffs.mean()),
                    "std": str(time_diffs.std()),
                    "min": str(time_diffs.min()),
                    "max": str(time_diffs.max()),
                },
            }

            # 価格の時系列パターン
            if len(data) > 10:
                # 移動平均
                ma_5 = data["close"].rolling(5).mean()
                ma_10 = data["close"].rolling(10).mean()

                analysis["moving_averages"] = {
                    "ma_5_range": {
                        "min": float(ma_5.min()),
                        "max": float(ma_5.max()),
                        "std": float(ma_5.std()),
                    },
                    "ma_10_range": {
                        "min": float(ma_10.min()),
                        "max": float(ma_10.max()),
                        "std": float(ma_10.std()),
                    },
                }

            return analysis

        except Exception as e:
            logger.error(f"時系列分析エラー: {e}")
            return {"error": str(e)}

    async def _detect_anomalies(self) -> Dict:
        """異常値の検出"""
        try:
            async with db_manager.get_session() as session:
                # 異常に大きな価格変動
                anomaly_query = text(
                    """
                    SELECT
                        timestamp,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        ABS(close_price - LAG(close_price) OVER (ORDER BY timestamp)) as price_change
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT 100
                    """
                )

                result = await session.execute(anomaly_query)
                rows = result.fetchall()

                if not rows:
                    return {"error": "異常値検出用データが見つかりません"}

                # 異常値の特定
                anomalies = []
                for row in rows:
                    if row[5] and row[5] > 1.0:  # 1円以上の変動
                        anomalies.append(
                            {
                                "timestamp": row[0],
                                "open": float(row[1]),
                                "high": float(row[2]),
                                "low": float(row[3]),
                                "close": float(row[4]),
                                "price_change": float(row[5]),
                            }
                        )

                return {
                    "large_price_changes": anomalies,
                    "anomaly_count": len(anomalies),
                }

        except Exception as e:
            logger.error(f"異常値検出エラー: {e}")
            return {"error": str(e)}

    def _assess_data_quality(
        self, basic_info: Dict, period_verifications: Dict
    ) -> Dict:
        """データ品質の総合評価"""
        try:
            assessment = {"overall_score": 0, "issues": [], "recommendations": []}

            score = 0
            max_score = 100

            # 基本データ量の評価
            total_records = basic_info.get("total_records", 0)
            if total_records > 10000:
                score += 20
            elif total_records > 1000:
                score += 15
            elif total_records > 100:
                score += 10
            else:
                assessment["issues"].append("データ量が不足しています")
                assessment["recommendations"].append("より多くのデータを収集してください")

            # 日付範囲の評価
            date_range = basic_info.get("date_range", {})
            span_days = date_range.get("span_days", 0)
            if span_days > 365:
                score += 20
            elif span_days > 90:
                score += 15
            elif span_days > 30:
                score += 10
            else:
                assessment["issues"].append("データ期間が短すぎます")
                assessment["recommendations"].append("より長期間のデータを収集してください")

            # 価格変動の評価
            for period_key, verification in period_verifications.items():
                if "error" not in verification:
                    price_stats = verification.get("price_statistics", {})
                    close_stats = price_stats.get("close", {})
                    unique_values = close_stats.get("unique_values", 0)

                    if unique_values < 2:
                        assessment["issues"].append(f"{period_key}: 価格変動がありません")
                        assessment["recommendations"].append(
                            f"{period_key}: より変動のあるデータが必要です"
                        )
                    else:
                        score += 10

            # データ一貫性の評価
            for period_key, verification in period_verifications.items():
                if "error" not in verification:
                    consistency = verification.get("consistency_checks", {})
                    price_logic = consistency.get("price_logic", {})

                    if price_logic.get("all_consistent", False):
                        score += 10
                    else:
                        assessment["issues"].append(f"{period_key}: 価格データの論理的不整合があります")
                        assessment["recommendations"].append(
                            f"{period_key}: データの整合性を確認してください"
                        )

            assessment["overall_score"] = min(score, max_score)

            # 総合評価
            if assessment["overall_score"] >= 80:
                assessment["grade"] = "A"
                assessment["summary"] = "データ品質は良好です"
            elif assessment["overall_score"] >= 60:
                assessment["grade"] = "B"
                assessment["summary"] = "データ品質は中程度です"
            elif assessment["overall_score"] >= 40:
                assessment["grade"] = "C"
                assessment["summary"] = "データ品質に問題があります"
            else:
                assessment["grade"] = "D"
                assessment["summary"] = "データ品質が非常に悪いです"

            return assessment

        except Exception as e:
            logger.error(f"データ品質評価エラー: {e}")
            return {"error": str(e)}


async def main():
    """メイン関数"""
    verifier = DatabaseDataVerifier()
    results = await verifier.verify_database_data()

    if "error" in results:
        print(f"\n❌ 検証エラー: {results['error']}")
        return

    print("\n=== データベース価格データ検証結果 ===")

    # 基本情報
    basic_info = results.get("basic_info", {})
    print(f"\n📊 基本情報:")
    print(f"  総レコード数: {basic_info.get('total_records', 0):,}")

    date_range = basic_info.get("date_range", {})
    print(
        f"  日付範囲: {date_range.get('earliest', 'N/A')} ～ {date_range.get('latest', 'N/A')}"
    )
    print(f"  期間: {date_range.get('span_days', 0)}日")

    currency_dist = basic_info.get("currency_distribution", {})
    print(f"  通貨ペア分布:")
    for currency, count in currency_dist.items():
        print(f"    {currency}: {count:,}件")

    # 最新データ
    recent_data = basic_info.get("recent_data", [])
    if recent_data:
        print(f"\n📈 最新データ（上位5件）:")
        for i, data in enumerate(recent_data[:5]):
            print(
                f"  {i+1}. {data['timestamp']}: O:{data['open']:.2f} H:{data['high']:.2f} L:{data['low']:.2f} C:{data['close']:.2f}"
            )

    # 期間別検証
    period_verifications = results.get("period_verifications", {})
    print(f"\n🔍 期間別検証:")

    for period_key, verification in period_verifications.items():
        if "error" in verification:
            print(f"\n  {period_key}: ❌ {verification['error']}")
            continue

        print(f"\n  {period_key}:")
        print(f"    データポイント: {verification.get('data_points', 0)}件")

        price_stats = verification.get("price_statistics", {})
        close_stats = price_stats.get("close", {})
        print(
            f"    終値範囲: {close_stats.get('min', 0):.2f} - {close_stats.get('max', 0):.2f}"
        )
        print(f"    終値平均: {close_stats.get('mean', 0):.2f}")
        print(f"    終値標準偏差: {close_stats.get('std', 0):.4f}")
        print(f"    終値ユニーク値: {close_stats.get('unique_values', 0)}")

        # 価格変動
        price_changes = verification.get("price_changes", {})
        daily_changes = price_changes.get("daily_changes", {})
        if daily_changes:
            print(
                f"    日次変動: 平均{daily_changes.get('mean_change', 0):.4f}, 標準偏差{daily_changes.get('std_change', 0):.4f}"
            )
            print(
                f"    変動方向: +{daily_changes.get('positive_changes', 0)} -{daily_changes.get('negative_changes', 0)} ={daily_changes.get('zero_changes', 0)}"
            )

        # 一貫性チェック
        consistency = verification.get("consistency_checks", {})
        price_logic = consistency.get("price_logic", {})
        print(f"    価格論理: {'✅' if price_logic.get('all_consistent', False) else '❌'}")

        zero_values = consistency.get("zero_values", {})
        if any(zero_values.values()):
            print(f"    ゼロ値: {zero_values}")

    # 異常値検出
    anomaly_detection = results.get("anomaly_detection", {})
    print(f"\n🚨 異常値検出:")
    print(f"  大きな価格変動: {anomaly_detection.get('anomaly_count', 0)}件")

    large_changes = anomaly_detection.get("large_price_changes", [])
    if large_changes:
        print(f"  異常変動詳細（上位3件）:")
        for i, change in enumerate(large_changes[:3]):
            print(f"    {i+1}. {change['timestamp']}: {change['price_change']:.2f}円変動")

    # データ品質評価
    quality_assessment = results.get("quality_assessment", {})
    print(f"\n📋 データ品質評価:")
    print(f"  総合スコア: {quality_assessment.get('overall_score', 0)}/100")
    print(f"  グレード: {quality_assessment.get('grade', 'N/A')}")
    print(f"  評価: {quality_assessment.get('summary', 'N/A')}")

    issues = quality_assessment.get("issues", [])
    if issues:
        print(f"  問題点:")
        for issue in issues:
            print(f"    ❌ {issue}")

    recommendations = quality_assessment.get("recommendations", [])
    if recommendations:
        print(f"  推奨事項:")
        for rec in recommendations:
            print(f"    💡 {rec}")


if __name__ == "__main__":
    asyncio.run(main())
