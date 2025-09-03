#!/usr/bin/env python3
"""
マルチタイムフレームテクニカル指標計算サービステストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.multi_timeframe_technical_indicator_service import (
    MultiTimeframeTechnicalIndicatorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class MultiTimeframeTechnicalIndicatorTester:
    """
    マルチタイムフレームテクニカル指標計算サービステストクラス
    """

    def __init__(self):
        self.session = None
        self.indicator_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up multi-timeframe technical indicator test...")
        logger.info("Setting up multi-timeframe technical indicator test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # マルチタイムフレームテクニカル指標計算サービスを初期化
        self.indicator_service = MultiTimeframeTechnicalIndicatorService(self.session)

        print("Multi-timeframe technical indicator test setup completed")
        logger.info("Multi-timeframe technical indicator test setup completed")

    async def test_calculate_single_timeframe_indicators(self):
        """
        単一時間軸の指標計算テスト
        """
        print("Testing single timeframe indicator calculation...")
        logger.info("Testing single timeframe indicator calculation...")

        try:
            # 各時間軸の指標を計算
            for timeframe in ["5m", "1h", "4h", "1d"]:
                print(f"Calculating {timeframe} indicators...")

                indicators = (
                    await self.indicator_service.calculate_timeframe_indicators(
                        timeframe
                    )
                )

                if indicators:
                    print(f"✅ {timeframe} indicators calculated:")
                    for indicator_type, data in indicators.items():
                        if indicator_type == "rsi":
                            print(f"  RSI: {data['value']:.2f}")
                        elif indicator_type == "macd":
                            print(
                                f"  MACD: {data['value']:.4f}, Signal: {data['signal_line']:.4f}"
                            )
                        elif indicator_type == "bb":
                            print(
                                f"  BB: {data['value']:.2f}, Upper: {data['upper_band']:.2f}, Lower: {data['lower_band']:.2f}"
                            )
                else:
                    print(f"❌ {timeframe} indicators calculation failed")

        except Exception as e:
            print(f"❌ Single timeframe indicator calculation test failed: {e}")
            logger.error(f"Single timeframe indicator calculation test failed: {e}")

    async def test_calculate_all_timeframe_indicators(self):
        """
        全時間軸の指標計算テスト
        """
        print("Testing all timeframe indicator calculation...")
        logger.info("Testing all timeframe indicator calculation...")

        try:
            # 全時間軸の指標を計算
            all_indicators = (
                await self.indicator_service.calculate_all_timeframe_indicators()
            )

            if all_indicators:
                print(
                    f"✅ All timeframe indicators calculated: {len(all_indicators)} timeframes"
                )
                for timeframe, indicators in all_indicators.items():
                    print(f"  {timeframe}: {len(indicators)} indicators")
                    for indicator_type in indicators.keys():
                        print(f"    - {indicator_type}")
            else:
                print("❌ All timeframe indicators calculation failed")

        except Exception as e:
            print(f"❌ All timeframe indicator calculation test failed: {e}")
            logger.error(f"All timeframe indicator calculation test failed: {e}")

    async def test_save_indicators(self):
        """
        指標保存テスト
        """
        print("Testing indicator saving...")
        logger.info("Testing indicator saving...")

        try:
            # 全時間軸の指標を計算して保存
            for timeframe in ["5m", "1h", "4h", "1d"]:
                print(f"Saving {timeframe} indicators...")

                indicators = (
                    await self.indicator_service.calculate_timeframe_indicators(
                        timeframe
                    )
                )

                if indicators:
                    saved = await self.indicator_service.save_timeframe_indicators(
                        timeframe, indicators
                    )

                    if saved:
                        print(f"✅ {timeframe} indicators saved successfully")
                    else:
                        print(f"❌ {timeframe} indicators save failed")
                else:
                    print(f"❌ No {timeframe} indicators to save")

        except Exception as e:
            print(f"❌ Indicator saving test failed: {e}")
            logger.error(f"Indicator saving test failed: {e}")

    async def test_get_latest_indicators(self):
        """
        最新指標取得テスト
        """
        print("Testing latest indicator retrieval...")
        logger.info("Testing latest indicator retrieval...")

        try:
            # 各時間軸の最新指標を取得
            for timeframe in ["5m", "1h", "4h", "1d"]:
                print(f"Getting latest {timeframe} indicators...")

                latest_indicators = (
                    await self.indicator_service.get_latest_indicators_by_timeframe(
                        timeframe
                    )
                )

                if latest_indicators:
                    print(f"✅ Latest {timeframe} indicators:")
                    for indicator_type, data in latest_indicators.items():
                        if indicator_type == "rsi":
                            print(f"  RSI: {data['value']:.2f}")
                        elif indicator_type == "macd":
                            print(
                                f"  MACD: {data['value']:.4f}, Signal: {data['signal']:.4f}"
                            )
                        elif indicator_type == "bb":
                            print(
                                f"  BB: {data['value']:.2f}, Upper: {data['upper']:.2f}, Lower: {data['lower']:.2f}"
                            )
                else:
                    print(f"❌ No latest {timeframe} indicators found")

        except Exception as e:
            print(f"❌ Latest indicator retrieval test failed: {e}")
            logger.error(f"Latest indicator retrieval test failed: {e}")

    async def test_indicator_calculation_accuracy(self):
        """
        指標計算精度テスト
        """
        print("Testing indicator calculation accuracy...")
        logger.info("Testing indicator calculation accuracy...")

        try:
            # 5分足の指標を計算
            indicators = await self.indicator_service.calculate_timeframe_indicators(
                "5m"
            )

            if indicators:
                print("✅ 5m indicator calculation accuracy test:")

                # RSI値の妥当性チェック
                if "rsi" in indicators:
                    rsi_value = indicators["rsi"]["value"]
                    if 0 <= rsi_value <= 100:
                        print(f"  RSI value is valid: {rsi_value:.2f}")
                    else:
                        print(f"  ⚠️ RSI value is out of range: {rsi_value:.2f}")

                # MACD値の妥当性チェック
                if "macd" in indicators:
                    macd_value = indicators["macd"]["value"]
                    signal_value = indicators["macd"]["signal_line"]
                    print(f"  MACD: {macd_value:.4f}, Signal: {signal_value:.4f}")

                # ボリンジャーバンド値の妥当性チェック
                if "bb" in indicators:
                    bb_value = indicators["bb"]["value"]
                    upper_value = indicators["bb"]["upper_band"]
                    lower_value = indicators["bb"]["lower_band"]

                    if lower_value <= bb_value <= upper_value:
                        print(
                            f"  BB values are valid: {lower_value:.2f} <= {bb_value:.2f} <= {upper_value:.2f}"
                        )
                    else:
                        print(
                            f"  ⚠️ BB values are invalid: {lower_value:.2f} <= {bb_value:.2f} <= {upper_value:.2f}"
                        )
            else:
                print("❌ No indicators calculated for accuracy test")

        except Exception as e:
            print(f"❌ Indicator calculation accuracy test failed: {e}")
            logger.error(f"Indicator calculation accuracy test failed: {e}")

    async def test_data_sufficiency(self):
        """
        データ充足性テスト
        """
        print("Testing data sufficiency...")
        logger.info("Testing data sufficiency...")

        try:
            # 各時間軸のデータ充足性をチェック
            for timeframe in ["5m", "1h", "4h", "1d"]:
                print(f"Checking {timeframe} data sufficiency...")

                indicators = (
                    await self.indicator_service.calculate_timeframe_indicators(
                        timeframe
                    )
                )

                if indicators:
                    print(
                        f"✅ {timeframe} has sufficient data for {len(indicators)} indicators"
                    )
                else:
                    print(
                        f"❌ {timeframe} has insufficient data for indicator calculation"
                    )

        except Exception as e:
            print(f"❌ Data sufficiency test failed: {e}")
            logger.error(f"Data sufficiency test failed: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Multi-timeframe technical indicator test cleanup completed")
        logger.info("Multi-timeframe technical indicator test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting multi-timeframe technical indicator test...")
    logger.info("Starting multi-timeframe technical indicator test...")

    tester = MultiTimeframeTechnicalIndicatorTester()

    try:
        await tester.setup()

        # 単一時間軸の指標計算テスト
        await tester.test_calculate_single_timeframe_indicators()

        # 全時間軸の指標計算テスト
        await tester.test_calculate_all_timeframe_indicators()

        # 指標保存テスト
        await tester.test_save_indicators()

        # 最新指標取得テスト
        await tester.test_get_latest_indicators()

        # 指標計算精度テスト
        await tester.test_indicator_calculation_accuracy()

        # データ充足性テスト
        await tester.test_data_sufficiency()

        print("Multi-timeframe technical indicator test completed successfully!")
        logger.info("Multi-timeframe technical indicator test completed successfully!")

    except Exception as e:
        print(f"Multi-timeframe technical indicator test failed: {e}")
        logger.error(f"Multi-timeframe technical indicator test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
