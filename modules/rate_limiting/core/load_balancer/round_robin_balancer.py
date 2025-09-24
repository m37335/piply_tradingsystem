"""
ラウンドロビンバランサー

ラウンドロビン方式でロードバランシングを実装します。
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .load_balancer_config import LoadBalancerConfig, LoadBalancingStrategy


@dataclass
class Server:
    """サーバー"""
    id: str
    weight: int = 1
    is_healthy: bool = True
    last_used: float = 0.0
    request_count: int = 0


class RoundRobinBalancer:
    """ラウンドロビンバランサー"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: List[Server] = []
        self.current_index = 0
        self.last_health_check = time.time()
    
    def add_server(self, server_id: str, weight: int = 1) -> None:
        """
        サーバーを追加
        
        Args:
            server_id: サーバーID
            weight: 重み
        """
        server = Server(id=server_id, weight=weight)
        self.servers.append(server)
    
    def remove_server(self, server_id: str) -> bool:
        """
        サーバーを削除
        
        Args:
            server_id: サーバーID
            
        Returns:
            削除が成功したかどうか
        """
        for i, server in enumerate(self.servers):
            if server.id == server_id:
                del self.servers[i]
                return True
        return False
    
    def get_next_server(self) -> Optional[Server]:
        """
        次のサーバーを取得
        
        Returns:
            次のサーバー、またはNone
        """
        if not self.servers:
            return None
        
        # ヘルスチェックを実行
        self._health_check()
        
        # ヘルシーなサーバーのみを取得
        healthy_servers = [s for s in self.servers if s.is_healthy]
        
        if not healthy_servers:
            return None
        
        # ラウンドロビンでサーバーを選択
        server = healthy_servers[self.current_index % len(healthy_servers)]
        self.current_index = (self.current_index + 1) % len(healthy_servers)
        
        # サーバーの使用情報を更新
        server.last_used = time.time()
        server.request_count += 1
        
        return server
    
    def get_server_by_id(self, server_id: str) -> Optional[Server]:
        """
        IDでサーバーを取得
        
        Args:
            server_id: サーバーID
            
        Returns:
            サーバー、またはNone
        """
        for server in self.servers:
            if server.id == server_id:
                return server
        return None
    
    def mark_server_unhealthy(self, server_id: str) -> None:
        """
        サーバーを不健康としてマーク
        
        Args:
            server_id: サーバーID
        """
        server = self.get_server_by_id(server_id)
        if server:
            server.is_healthy = False
    
    def mark_server_healthy(self, server_id: str) -> None:
        """
        サーバーを健康としてマーク
        
        Args:
            server_id: サーバーID
        """
        server = self.get_server_by_id(server_id)
        if server:
            server.is_healthy = True
    
    def _health_check(self) -> None:
        """ヘルスチェックを実行"""
        now = time.time()
        
        # ヘルスチェック間隔をチェック
        if now - self.last_health_check < self.config.health_check_interval:
            return
        
        # 各サーバーのヘルスチェックを実行
        for server in self.servers:
            # 実際の実装では、サーバーにpingを送信してヘルスチェック
            # ここでは簡易実装
            if now - server.last_used > self.config.server_timeout:
                server.is_healthy = False
            else:
                server.is_healthy = True
        
        self.last_health_check = now
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        total_servers = len(self.servers)
        healthy_servers = sum(1 for s in self.servers if s.is_healthy)
        total_requests = sum(s.request_count for s in self.servers)
        
        return {
            "total_servers": total_servers,
            "healthy_servers": healthy_servers,
            "unhealthy_servers": total_servers - healthy_servers,
            "total_requests": total_requests,
            "current_index": self.current_index,
            "last_health_check": self.last_health_check
        }
    
    def get_server_stats(self) -> List[Dict[str, Any]]:
        """
        サーバー別の統計情報を取得
        
        Returns:
            サーバー統計のリスト
        """
        return [
            {
                "id": server.id,
                "weight": server.weight,
                "is_healthy": server.is_healthy,
                "request_count": server.request_count,
                "last_used": server.last_used
            }
            for server in self.servers
        ]
    
    def reset_stats(self) -> None:
        """統計をリセット"""
        for server in self.servers:
            server.request_count = 0
            server.last_used = 0.0
        self.current_index = 0
