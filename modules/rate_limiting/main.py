"""
レート制限管理システムのメインスクリプト

統合レート制限管理システムを提供します。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.rate_limiting.config.settings import RateLimitingSettings
from modules.rate_limiting.core.integrated_rate_limit_manager import IntegratedRateLimitManager

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RateLimitingService:
    """レート制限サービス"""
    
    def __init__(self, settings: RateLimitingSettings):
        self.settings = settings
        self.manager = IntegratedRateLimitManager(settings)
        self._running = False
    
    async def start(self) -> None:
        """サービスを開始"""
        if self._running:
            logger.warning("Rate limiting service is already running")
            return
        
        try:
            await self.manager.start()
            self._running = True
            logger.info("Rate limiting service started successfully")
        except Exception as e:
            logger.error(f"Failed to start rate limiting service: {e}")
            raise
    
    async def stop(self) -> None:
        """サービスを停止"""
        if not self._running:
            return
        
        try:
            await self.manager.stop()
            self._running = False
            logger.info("Rate limiting service stopped")
        except Exception as e:
            logger.error(f"Error stopping rate limiting service: {e}")
    
    async def add_provider(self, name: str, provider: any, weight: float = 1.0) -> None:
        """プロバイダーを追加"""
        self.manager.add_provider(name, provider, weight)
        logger.info(f"Provider {name} added with weight {weight}")
    
    async def add_alternative_provider(self, name: str, provider: any) -> None:
        """代替プロバイダーを追加"""
        self.manager.add_alternative_provider(name, provider)
        logger.info(f"Alternative provider {name} added")
    
    async def execute_request(self, request_func, cache_key: str, *args, **kwargs) -> any:
        """リクエストを実行"""
        return await self.manager.execute_request(request_func, cache_key, *args, **kwargs)
    
    async def get_stats(self) -> dict:
        """統計情報を取得"""
        return self.manager.get_stats()
    
    async def health_check(self) -> dict:
        """ヘルスチェック"""
        return await self.manager.health_check()
    
    async def reset_stats(self) -> None:
        """統計をリセット"""
        await self.manager.reset_stats()
        logger.info("Rate limiting stats reset")


async def main():
    """メイン関数"""
    service = None
    try:
        # 設定を読み込み
        settings = RateLimitingSettings.from_env()
        logger.info(f"Starting rate limiting service with settings: {settings.to_dict()}")
        
        # サービスを作成して開始
        service = RateLimitingService(settings)
        await service.start()
        
        # サービスを実行（実際の使用例）
        await _demo_usage(service)
        
    except KeyboardInterrupt:
        logger.info("Rate limiting service interrupted by user")
    except Exception as e:
        logger.error(f"Rate limiting service failed: {e}")
        sys.exit(1)
    finally:
        if service:
            await service.stop()


async def _demo_usage(service: RateLimitingService):
    """デモ使用例"""
    logger.info("Running demo usage...")
    
    # モックプロバイダーを追加
    class MockProvider:
        async def health_check(self):
            return True
        
        async def get_data(self, symbol: str):
            return {"symbol": symbol, "price": 150.0, "timestamp": "2024-01-01T00:00:00Z"}
    
    # プロバイダーを追加
    await service.add_provider("yahoo_finance", MockProvider(), 1.0)
    await service.add_alternative_provider("alpha_vantage", MockProvider())
    
    # リクエストを実行
    async def mock_request(provider, symbol: str):
        return await provider.get_data(symbol)
    
    try:
        result = await service.execute_request(
            mock_request,
            "AAPL_data",
            "AAPL"
        )
        logger.info(f"Request result: {result}")
        
        # 統計情報を取得
        stats = await service.get_stats()
        logger.info(f"Service stats: {stats}")
        
        # ヘルスチェック
        health = await service.health_check()
        logger.info(f"Service health: {health}")
        
    except Exception as e:
        logger.error(f"Demo usage failed: {e}")


async def health_check():
    """ヘルスチェック"""
    try:
        settings = RateLimitingSettings.from_env()
        service = RateLimitingService(settings)
        health = await service.health_check()
        print(f"Health check result: {health}")
        return health
    except Exception as e:
        print(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    asyncio.run(main())
