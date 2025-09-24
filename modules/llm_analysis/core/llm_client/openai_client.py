"""
OpenAIクライアント

OpenAI APIとの通信を管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

from .llm_client import LLMClient, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClient):
    """OpenAIクライアント"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
        self.client = None
    
    async def initialize(self) -> None:
        """クライアントを初期化"""
        try:
            # OpenAIクライアントの初期化（実際の実装ではopenaiライブラリを使用）
            self._initialized = True
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    async def close(self) -> None:
        """クライアントを閉じる"""
        self._initialized = False
        logger.info("OpenAI client closed")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        テキストを生成
        
        Args:
            request: LLMリクエスト
            
        Returns:
            LLMレスポンス
        """
        try:
            start_time = time.time()
            
            # 簡易実装（実際の実装ではOpenAI APIを呼び出し）
            content = f"Generated response for: {request.prompt[:50]}..."
            
            response_time = time.time() - start_time
            
            return LLMResponse(
                content=content,
                model=request.model,
                usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
                finish_reason="stop",
                response_time=response_time,
                timestamp=datetime.now(),
                metadata={"provider": "openai"}
            )
        
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # 簡単なリクエストでヘルスチェック
            test_request = LLMRequest(
                prompt="Hello",
                model=self.model,
                max_tokens=10
            )
            
            response = await self.generate(test_request)
            
            return {
                "status": "healthy" if response.content else "unhealthy",
                "provider": "openai",
                "model": self.model,
                "response_time": response.response_time
            }
        
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "provider": "openai",
                "model": self.model,
                "error": str(e)
            }
