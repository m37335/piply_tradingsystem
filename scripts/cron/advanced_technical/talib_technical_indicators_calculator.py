#!/usr/bin/env python3
"""
TA-Lib Technical Indicators Calculator
TA-Libを使用したテクニカル指標計算スクリプト

機能:
- TA-Libを使用した高精度指標計算
- 移動平均線を含む全指標対応
- 初回データ取得時と基本データ取得時の両方で使用
- 複数時間軸対応
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.talib_technical_indicator_service import (
    TALibTechnicalIndicatorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TALibTechnicalIndicatorsCalculator:
    """
    TA-Libテクニカル指標計算器

    責任:
    - TA-Libを使用したテクニカル指標計算
    - 複数時間軸対応
    - データベース保存
    - エラーハンドリング

    特徴:
    - TA-Libによる高精度計算
    - 移動平均線を含む全指標対応
    - 効率的なバッチ処理
    - 包括的なログ出力
    """

    def __init__(self):
        """初期化"""
        self.session = None
        self.indicator_service = None
        self.currency_pair = "USD/JPY"

        # 対応時間軸
        self.timeframes = {
            "M5": {"days": 7, "description": "5分足"},
            "H1": {"days": 30, "description": "1時間足"},
            "H4": {"days": 60, "description": "4時間足"},
            "D1": {"days": 365, "description": "日足"},
        }

        logger.info("Initialized TALib Technical Indicators Calculator")

    async def initialize(self):
        """初期化処理"""
        try:
            logger.info("🔄 初期化開始...")

            # データベースセッション初期化
            self.session = await get_async_session()

            # テクニカル指標サービス初期化
            self.indicator_service = TALibTechnicalIndicatorService(self.session)

            logger.info("✅ 初期化完了")

        except Exception as e:
            logger.error(f"❌ 初期化エラー: {e}")
            raise

    async def calculate_all_indicators(self):
        """全テクニカル指標を計算"""
        try:
            logger.info("=== TA-Libテクニカル指標計算開始 ===")

            total_indicators = 0
            timeframe_results = {}

            for timeframe, config in self.timeframes.items():
                logger.info(f"📊 {config['description']}テクニカル指標計算中...")

                # 各時間軸の指標を計算
                results = (
                    await self.indicator_service.calculate_and_save_all_indicators(
                        timeframe
                    )
                )

                timeframe_indicators = sum(results.values())
                timeframe_results[timeframe] = {
                    "calculated": timeframe_indicators,
                    "details": results,
                }

                total_indicators += timeframe_indicators

                logger.info(f"  ✅ {timeframe}完了: {timeframe_indicators}件")

                # 詳細ログ出力
                for indicator_type, count in results.items():
                    if count > 0:
                        logger.info(f"    📈 {indicator_type}: {count}件")

            # 総合結果ログ
            logger.info("=" * 60)
            logger.info("📊 TA-Libテクニカル指標計算完了")
            logger.info("=" * 60)
            logger.info(f"総計算件数: {total_indicators}件")

            for timeframe, result in timeframe_results.items():
                logger.info(f"{timeframe}: {result['calculated']}件")

            return {
                "total_indicators": total_indicators,
                "timeframe_results": timeframe_results,
                "calculation_time": datetime.now(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"❌ テクニカル指標計算エラー: {e}")
            return {
                "total_indicators": 0,
                "timeframe_results": {},
                "calculation_time": datetime.now(),
                "status": "error",
                "error": str(e),
            }

    async def calculate_single_timeframe(self, timeframe: str):
        """単一時間軸のテクニカル指標を計算"""
        try:
            if timeframe not in self.timeframes:
                logger.error(f"❌ 無効な時間軸: {timeframe}")
                return {"status": "error", "error": f"無効な時間軸: {timeframe}"}

            config = self.timeframes[timeframe]
            logger.info(f"📊 {config['description']}テクニカル指標計算中...")

            # 指定時間軸の指標を計算
            results = await self.indicator_service.calculate_and_save_all_indicators(
                timeframe
            )

            total_count = sum(results.values())

            logger.info(f"✅ {timeframe}完了: {total_count}件")

            # 詳細ログ出力
            for indicator_type, count in results.items():
                if count > 0:
                    logger.info(f"  📈 {indicator_type}: {count}件")

            return {
                "timeframe": timeframe,
                "total_indicators": total_count,
                "details": results,
                "calculation_time": datetime.now(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"❌ {timeframe}計算エラー: {e}")
            return {
                "timeframe": timeframe,
                "total_indicators": 0,
                "details": {},
                "calculation_time": datetime.now(),
                "status": "error",
                "error": str(e),
            }

    async def get_latest_indicators(self, timeframe: str = "M5", limit: int = 10):
        """最新のテクニカル指標を取得"""
        try:
            logger.info(f"📊 {timeframe}の最新指標を取得中...")

            indicators = (
                await self.indicator_service.get_latest_indicators_by_timeframe(
                    timeframe, limit
                )
            )

            logger.info(f"✅ {timeframe}の最新指標取得完了: {len(indicators)}種類")

            for indicator_type, data in indicators.items():
                if data:
                    latest = data[0]
                    logger.info(f"  📈 {indicator_type}: {latest['value']}")

            return indicators

        except Exception as e:
            logger.error(f"❌ 最新指標取得エラー: {e}")
            return {}

    async def cleanup(self):
        """クリーンアップ処理"""
        try:
            if self.session:
                await self.session.close()
                logger.info("✅ データベースセッションをクローズしました")

        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")


async def main():
    """メイン関数"""
    calculator = TALibTechnicalIndicatorsCalculator()

    try:
        # 初期化
        await calculator.initialize()

        # コマンドライン引数の処理
        if len(sys.argv) > 1:
            command = sys.argv[1]

            if command == "all":
                # 全時間軸の指標を計算
                result = await calculator.calculate_all_indicators()
                logger.info(f"計算結果: {result}")

            elif command == "timeframe" and len(sys.argv) > 2:
                # 指定時間軸の指標を計算
                timeframe = sys.argv[2]
                result = await calculator.calculate_single_timeframe(timeframe)
                logger.info(f"計算結果: {result}")

            elif command == "latest" and len(sys.argv) > 2:
                # 最新指標を取得
                timeframe = sys.argv[2]
                limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
                result = await calculator.get_latest_indicators(timeframe, limit)
                logger.info(f"取得結果: {result}")

            else:
                logger.error("❌ 無効なコマンド")
                logger.info("使用法:")
                logger.info("  python talib_technical_indicators_calculator.py all")
                logger.info(
                    "  python talib_technical_indicators_calculator.py timeframe M5"
                )
                logger.info(
                    "  python talib_technical_indicators_calculator.py latest M5 10"
                )

        else:
            # デフォルト: 全時間軸の指標を計算
            result = await calculator.calculate_all_indicators()
            logger.info(f"計算結果: {result}")

    except Exception as e:
        logger.error(f"❌ メイン処理エラー: {e}")
        raise

    finally:
        # クリーンアップ
        await calculator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
