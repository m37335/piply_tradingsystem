"""
Technical Calculator
テクニカル指標計算機能

責任:
- 既存テクニカル指標システムの活用
- 各時間足の指標計算
- 計算結果の保存と検証

設計書参照:
- CLIデータベース初期化システム実装仕様書_2025.md
- CLIデータベース初期化システム実装計画書_Phase3_分析処理_2025.md
"""

import asyncio
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.analysis.technical_indicators import TechnicalIndicatorsAnalyzer
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.multi_timeframe_technical_indicator_service import (
    MultiTimeframeTechnicalIndicatorService,
)


class TechnicalCalculator:
    """
    テクニカル指標計算クラス

    既存のテクニカル指標システムを活用して指標計算を行う機能を提供
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair: str = currency_pair
        self.session: Optional[AsyncSession] = None

        # 既存システムの活用
        self.technical_analyzer: TechnicalIndicatorsAnalyzer = (
            TechnicalIndicatorsAnalyzer()
        )
        self.multi_timeframe_service: Optional[
            MultiTimeframeTechnicalIndicatorService
        ] = None

    async def calculate_all_indicators(self) -> Dict[str, int]:
        """
        全テクニカル指標を計算

        Returns:
            Dict[str, int]: 各時間足の計算件数
        """
        results = {}

        for timeframe in ["5m", "1h", "4h", "1d"]:
            print(f"📊 {timeframe}時間足のテクニカル指標計算を開始...")
            count = await self.calculate_timeframe_indicators(timeframe)
            results[timeframe] = count
            print(f"✅ {timeframe}時間足指標計算完了: {count}件")

        return results

    async def calculate_timeframe_indicators(self, timeframe: str) -> int:
        """
        特定時間足の指標を計算

        Args:
            timeframe: 時間足

        Returns:
            int: 計算件数
        """
        try:
            # 既存のTechnicalIndicatorsCalculatorを使用
            from scripts.cron.technical_indicators_calculator import (
                TechnicalIndicatorsCalculator,
            )

            calculator = TechnicalIndicatorsCalculator()
            await calculator.initialize()

            # 全時間足の指標計算を実行（既存のメソッドを使用）
            count = await calculator.calculate_all_indicators()

            return count

        except Exception as e:
            print(f"❌ {timeframe}指標計算エラー: {e}")
            return 0

    async def _initialize_existing_systems(self) -> bool:
        """
        既存システムの初期化

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            # マルチタイムフレームサービスの初期化
            self.multi_timeframe_service = MultiTimeframeTechnicalIndicatorService(
                self.session
            )

            return True

        except Exception as e:
            print(f"❌ 既存システム初期化エラー: {e}")
            return False

    async def initialize(self) -> bool:
        """
        初期化処理

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            # セッションの初期化
            self.session = await get_async_session()

            # 既存システムの初期化
            await self._initialize_existing_systems()

            return True

        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False

    async def cleanup(self) -> None:
        """
        リソースのクリーンアップ
        """
        if self.session:
            await self.session.close()


async def main():
    """
    メイン実行関数
    """
    calculator = TechnicalCalculator()

    try:
        # 初期化
        if not await calculator.initialize():
            print("❌ 初期化に失敗しました")
            return 1

        # テクニカル指標計算実行
        results = await calculator.calculate_all_indicators()

        # 結果表示
        total_count = sum(results.values())
        print("\n📊 テクニカル指標計算結果:")
        for timeframe, count in results.items():
            print(f"   {timeframe}: {count}件")
        print(f"   合計: {total_count}件")

        if total_count > 0:
            print("🎉 テクニカル指標計算が正常に完了しました")
        else:
            print("ℹ️ 計算対象のデータがありませんでした")

    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return 1
    finally:
        await calculator.cleanup()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
