"""
LLMクライアント

LLM APIとの通信を管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """LLMリクエスト"""
    prompt: str
    model: str
    max_tokens: int = 1000
    temperature: float = 0.7
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class LLMResponse:
    """LLMレスポンス"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMClient(ABC):
    """LLMクライアントの基底クラス"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """クライアントを初期化"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """クライアントを閉じる"""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """テキストを生成"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        pass
