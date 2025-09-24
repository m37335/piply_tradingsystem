"""
スケジューラーモジュールのメインスクリプト

タスクスケジューリングサービスを提供します。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.scheduler.config.settings import SchedulerSettings
from modules.scheduler.core.scheduler_service import SchedulerService

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SchedulerMain:
    """スケジューラーメイン"""
    
    def __init__(self, settings: SchedulerSettings):
        self.settings = settings
        self.service = SchedulerService(settings)
        self._running = False
    
    async def start(self) -> None:
        """サービスを開始"""
        if self._running:
            logger.warning("Scheduler main is already running")
            return
        
        try:
            await self.service.start()
            self._running = True
            logger.info("Scheduler main started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler main: {e}")
            raise
    
    async def stop(self) -> None:
        """サービスを停止"""
        if not self._running:
            return
        
        try:
            await self.service.stop()
            self._running = False
            logger.info("Scheduler main stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler main: {e}")
    
    async def get_status(self) -> dict:
        """ステータスを取得"""
        return await self.service.get_scheduler_stats()
    
    async def health_check(self) -> dict:
        """ヘルスチェック"""
        return await self.service.health_check()
    
    async def trigger_task(self, task_name: str) -> dict:
        """タスクを手動実行"""
        return await self.service.trigger_manual_task(task_name)
    
    async def get_task_history(self, task_name: str = None, limit: int = 100) -> list:
        """タスク履歴を取得"""
        return await self.service.get_task_history(task_name, limit)


async def main():
    """メイン関数"""
    scheduler = None
    try:
        # 設定を読み込み
        settings = SchedulerSettings.from_env()
        logger.info(f"Starting scheduler with settings: {settings.to_dict()}")
        
        # スケジューラーを作成して開始
        scheduler = SchedulerMain(settings)
        await scheduler.start()
        
        # サービスを実行（実際の使用例）
        await _demo_usage(scheduler)
        
    except KeyboardInterrupt:
        logger.info("Scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")
        sys.exit(1)
    finally:
        if scheduler:
            await scheduler.stop()


async def _demo_usage(scheduler: SchedulerMain):
    """デモ使用例"""
    logger.info("Running demo usage...")
    
    # カスタムタスクをスケジュール
    async def demo_task():
        logger.info("Demo task executed")
        return "demo_result"
    
    # タスクをスケジュール
    await scheduler.service.schedule_custom_task(
        name="demo_task",
        func=demo_task,
        interval_seconds=30,  # 30秒間隔
        priority=1  # 低優先度
    )
    
    # ステータスを取得
    status = await scheduler.get_status()
    logger.info(f"Scheduler status: {status}")
    
    # ヘルスチェック
    health = await scheduler.health_check()
    logger.info(f"Scheduler health: {health}")
    
    # 市場状況を取得
    market_status = await scheduler.service.get_market_status()
    logger.info(f"Market status: {market_status}")
    
    # タスク履歴を取得
    history = await scheduler.get_task_history(limit=10)
    logger.info(f"Task history: {history}")
    
    # 手動でタスクを実行
    result = await scheduler.trigger_task("demo_task")
    logger.info(f"Manual task result: {result}")


async def health_check():
    """ヘルスチェック"""
    try:
        settings = SchedulerSettings.from_env()
        scheduler = SchedulerMain(settings)
        health = await scheduler.health_check()
        print(f"Health check result: {health}")
        return health
    except Exception as e:
        print(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def get_status():
    """ステータス取得"""
    try:
        settings = SchedulerSettings.from_env()
        scheduler = SchedulerMain(settings)
        status = await scheduler.get_status()
        print(f"Status: {status}")
        return status
    except Exception as e:
        print(f"Status check failed: {e}")
        return {"error": str(e)}


async def trigger_task(task_name: str):
    """タスク手動実行"""
    try:
        settings = SchedulerSettings.from_env()
        scheduler = SchedulerMain(settings)
        result = await scheduler.trigger_task(task_name)
        print(f"Task result: {result}")
        return result
    except Exception as e:
        print(f"Task execution failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
