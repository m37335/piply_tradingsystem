"""
ロードバランサー設定

ロードバランサーの設定を管理します。
"""

from dataclasses import dataclass
from enum import Enum


class LoadBalancingStrategy(Enum):
    """ロードバランシング戦略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    HEALTH_BASED = "health_based"


@dataclass
class LoadBalancerConfig:
    """ロードバランサー設定"""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    health_check_interval: float = 30.0  # 秒
    server_timeout: float = 60.0  # 秒
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒
