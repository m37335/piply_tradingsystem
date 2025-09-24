"""
LLM分析モジュールのメインスクリプト

LLM分析サービスを提供します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.llm_analysis.config.settings import (
    AnalysisFrequency,
    AnalysisType,
    LLMAnalysisSettings,
)
from modules.llm_analysis.core.llm_analysis_service import LLMAnalysisService

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMAnalysisMain:
    """LLM分析メイン"""

    def __init__(self, settings: LLMAnalysisSettings):
        self.settings = settings
        self.service = LLMAnalysisService(settings)
        self._running = False

    async def start(self) -> None:
        """サービスを開始"""
        if self._running:
            logger.warning("LLM analysis main is already running")
            return

        try:
            await self.service.start()
            self._running = True
            logger.info("LLM analysis main started successfully")
        except Exception as e:
            logger.error(f"Failed to start LLM analysis main: {e}")
            raise

    async def stop(self) -> None:
        """サービスを停止"""
        if not self._running:
            return

        try:
            await self.service.stop()
            self._running = False
            logger.info("LLM analysis main stopped")
        except Exception as e:
            logger.error(f"Error stopping LLM analysis main: {e}")

    async def analyze_on_demand(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: str,
        start_date: str = None,
        end_date: str = None,
    ) -> dict:
        """オンデマンド分析を実行"""
        try:
            # 分析タイプを変換
            analysis_type_enum = AnalysisType(analysis_type)

            # 日付を変換
            start_dt = None
            end_dt = None
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)

            # 分析を実行
            result = await self.service.analyze_on_demand(
                symbol=symbol,
                timeframe=timeframe,
                analysis_type=analysis_type_enum,
                start_date=start_dt,
                end_date=end_dt,
            )

            return result

        except Exception as e:
            logger.error(f"On-demand analysis failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_analysis_history(
        self, symbol: str, timeframe: str, analysis_type: str = None, limit: int = 100
    ) -> list:
        """分析履歴を取得"""
        try:
            analysis_type_enum = None
            if analysis_type:
                analysis_type_enum = AnalysisType(analysis_type)

            history = await self.service.get_analysis_history(
                symbol=symbol,
                timeframe=timeframe,
                analysis_type=analysis_type_enum,
                limit=limit,
            )

            return history

        except Exception as e:
            logger.error(f"Failed to get analysis history: {e}")
            return []

    async def get_analysis_summary(self) -> dict:
        """分析サマリーを取得"""
        return await self.service.get_analysis_summary()

    async def health_check(self) -> dict:
        """ヘルスチェック"""
        return await self.service.health_check()


async def main():
    """メイン関数"""
    service = None
    try:
        # 設定を読み込み
        settings = LLMAnalysisSettings.from_env()
        logger.info(f"Starting LLM analysis with settings: {settings.to_dict()}")

        # サービスを作成して開始
        service = LLMAnalysisMain(settings)
        await service.start()

        # サービスを実行（実際の使用例）
        await _demo_usage(service)

    except KeyboardInterrupt:
        logger.info("LLM analysis interrupted by user")
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        sys.exit(1)
    finally:
        if service:
            await service.stop()


async def _demo_usage(service: LLMAnalysisMain):
    """デモ使用例"""
    logger.info("Running demo usage...")

    # オンデマンド分析を実行
    result = await service.analyze_on_demand(
        symbol="AAPL", timeframe="1h", analysis_type="market_sentiment"
    )

    logger.info(f"Analysis result: {result}")

    # 分析履歴を取得
    history = await service.get_analysis_history(
        symbol="AAPL", timeframe="1h", analysis_type="market_sentiment", limit=10
    )

    logger.info(f"Analysis history: {len(history)} records")

    # 分析サマリーを取得
    summary = await service.get_analysis_summary()
    logger.info(f"Analysis summary: {summary}")

    # ヘルスチェック
    health = await service.health_check()
    logger.info(f"Service health: {health}")


async def analyze_on_demand(
    symbol: str,
    timeframe: str,
    analysis_type: str,
    start_date: str = None,
    end_date: str = None,
):
    """オンデマンド分析"""
    try:
        settings = LLMAnalysisSettings.from_env()
        service = LLMAnalysisMain(settings)
        result = await service.analyze_on_demand(
            symbol=symbol,
            timeframe=timeframe,
            analysis_type=analysis_type,
            start_date=start_date,
            end_date=end_date,
        )
        print(f"Analysis result: {result}")
        return result
    except Exception as e:
        print(f"Analysis failed: {e}")
        return {"success": False, "error": str(e)}


async def get_analysis_history(
    symbol: str, timeframe: str, analysis_type: str = None, limit: int = 100
):
    """分析履歴取得"""
    try:
        settings = LLMAnalysisSettings.from_env()
        service = LLMAnalysisMain(settings)
        history = await service.get_analysis_history(
            symbol=symbol, timeframe=timeframe, analysis_type=analysis_type, limit=limit
        )
        print(f"Analysis history: {len(history)} records")
        return history
    except Exception as e:
        print(f"Failed to get analysis history: {e}")
        return []


async def get_analysis_summary():
    """分析サマリー取得"""
    try:
        settings = LLMAnalysisSettings.from_env()
        service = LLMAnalysisMain(settings)
        summary = await service.get_analysis_summary()
        print(f"Analysis summary: {summary}")
        return summary
    except Exception as e:
        print(f"Failed to get analysis summary: {e}")
        return {"error": str(e)}


async def health_check():
    """ヘルスチェック"""
    try:
        settings = LLMAnalysisSettings.from_env()
        service = LLMAnalysisMain(settings)
        health = await service.health_check()
        print(f"Health check result: {health}")
        return health
    except Exception as e:
        print(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
