"""
ヘルスベースバランサー

ヘルス状態に基づいてロードバランシングを実装します。
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .load_balancer_config import LoadBalancerConfig, LoadBalancingStrategy


@dataclass
class HealthServer:
    """ヘルスサーバー"""
    id: str
    weight: int = 1
    health_score: float = 1.0
    response_time: float = 0.0
    error_rate: float = 0.0
    is_healthy: bool = True
    last_used: float = 0.0
    request_count: int = 0
    success_count: int = 0
    failure_count: int = 0


class HealthBasedBalancer:
    """ヘルスベースバランサー"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.servers: List[HealthServer] = []
        self.last_health_check = time.time()
    
    def add_server(self, server_id: str, weight: int = 1) -> None:
        """
        サーバーを追加
        
        Args:
            server_id: サーバーID
            weight: 重み
        """
        server = HealthServer(id=server_id, weight=weight)
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
    
    def get_next_server(self) -> Optional[HealthServer]:
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
        
        # ヘルススコアに基づいてサーバーを選択
        # ヘルススコアが高いサーバーを優先
        selected_server = max(healthy_servers, key=lambda s: s.health_score)
        
        # サーバーの使用情報を更新
        selected_server.last_used = time.time()
        selected_server.request_count += 1
        
        return selected_server
    
    def get_server_by_id(self, server_id: str) -> Optional[HealthServer]:
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
    
    def record_success(self, server_id: str, response_time: float) -> None:
        """
        成功を記録
        
        Args:
            server_id: サーバーID
            response_time: レスポンス時間
        """
        server = self.get_server_by_id(server_id)
        if server:
            server.success_count += 1
            server.response_time = (server.response_time + response_time) / 2
            self._update_health_score(server)
    
    def record_failure(self, server_id: str) -> None:
        """
        失敗を記録
        
        Args:
            server_id: サーバーID
        """
        server = self.get_server_by_id(server_id)
        if server:
            server.failure_count += 1
            self._update_health_score(server)
    
    def _update_health_score(self, server: HealthServer) -> None:
        """
        ヘルススコアを更新
        
        Args:
            server: サーバー
        """
        total_requests = server.success_count + server.failure_count
        
        if total_requests == 0:
            server.health_score = 1.0
            return
        
        # エラー率を計算
        server.error_rate = server.failure_count / total_requests
        
        # ヘルススコアを計算
        # エラー率が低く、レスポンス時間が短いほど高いスコア
        error_score = 1.0 - server.error_rate
        response_score = max(0.0, 1.0 - (server.response_time / 1000.0))  # 1秒を基準
        
        server.health_score = (error_score + response_score) / 2
        
        # ヘルススコアが低い場合は不健康としてマーク
        server.is_healthy = server.health_score >= 0.5
    
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
                server.health_score = 0.0
            else:
                # ヘルススコアに基づいてヘルス状態を更新
                server.is_healthy = server.health_score >= 0.5
        
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
        avg_health_score = sum(s.health_score for s in self.servers) / total_servers if total_servers > 0 else 0.0
        
        return {
            "total_servers": total_servers,
            "healthy_servers": healthy_servers,
            "unhealthy_servers": total_servers - healthy_servers,
            "total_requests": total_requests,
            "average_health_score": avg_health_score,
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
                "health_score": server.health_score,
                "response_time": server.response_time,
                "error_rate": server.error_rate,
                "is_healthy": server.is_healthy,
                "request_count": server.request_count,
                "success_count": server.success_count,
                "failure_count": server.failure_count,
                "last_used": server.last_used
            }
            for server in self.servers
        ]
    
    def reset_stats(self) -> None:
        """統計をリセット"""
        for server in self.servers:
            server.request_count = 0
            server.success_count = 0
            server.failure_count = 0
            server.last_used = 0.0
            server.health_score = 1.0
            server.response_time = 0.0
            server.error_rate = 0.0
            server.is_healthy = True
