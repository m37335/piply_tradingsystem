"""
ベースプロバイダー（Stream API専用設計）

外部API連携の共通インターフェースを定義するベースクラス。
Stream API専用の設計で、REST APIは使用しません。
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum


class ProviderType(Enum):
    """プロバイダータイプ（Stream API専用）"""
    STREAM = "stream"
    WEBSOCKET = "websocket"


class ConnectionStatus(Enum):
    """接続ステータス"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class ProviderConfig:
    """プロバイダー設定"""
    name: str
    type: ProviderType
    base_url: str
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5


@dataclass
class ProviderMetrics:
    """プロバイダーメトリクス"""
    connection_count: int = 0
    disconnection_count: int = 0
    error_count: int = 0
    last_connection_time: Optional[datetime] = None
    last_disconnection_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    total_messages_received: int = 0
    total_messages_sent: int = 0


class BaseProvider(ABC):
    """ベースプロバイダー"""

    def __init__(self, config: ProviderConfig):
        """初期化"""
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self.status = ConnectionStatus.DISCONNECTED
        self.metrics = ProviderMetrics()
        self.callbacks: List[Callable] = []
        self._lock = None

    @abstractmethod
    async def connect(self) -> bool:
        """接続"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """切断"""
        pass

    @abstractmethod
    async def send_message(self, message: Any) -> bool:
        """メッセージ送信"""
        pass

    @abstractmethod
    async def start_listening(self) -> None:
        """リスニング開始"""
        pass

    @abstractmethod
    async def stop_listening(self) -> None:
        """リスニング停止"""
        pass

    def add_callback(self, callback: Callable) -> None:
        """コールバックの追加"""
        self.callbacks.append(callback)
        self.logger.info(f"✅ コールバック追加: {callback.__name__}")

    def remove_callback(self, callback: Callable) -> None:
        """コールバックの削除"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            self.logger.info(f"✅ コールバック削除: {callback.__name__}")

    async def _notify_callbacks(self, data: Any) -> None:
        """コールバックの通知"""
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                self.logger.error(f"❌ コールバック実行エラー: {e}")

    def _update_status(self, status: ConnectionStatus) -> None:
        """ステータスの更新"""
        old_status = self.status
        self.status = status
        
        if status == ConnectionStatus.CONNECTED:
            self.metrics.connection_count += 1
            self.metrics.last_connection_time = datetime.now(timezone.utc)
        elif status == ConnectionStatus.DISCONNECTED:
            self.metrics.disconnection_count += 1
            self.metrics.last_disconnection_time = datetime.now(timezone.utc)
        elif status == ConnectionStatus.ERROR:
            self.metrics.error_count += 1
            self.metrics.last_error_time = datetime.now(timezone.utc)
        
        self.logger.info(f"📊 ステータス変更: {old_status.value} → {status.value}")

    def get_metrics(self) -> ProviderMetrics:
        """メトリクスの取得"""
        return self.metrics

    def is_connected(self) -> bool:
        """接続状態の確認"""
        return self.status == ConnectionStatus.CONNECTED

    def get_status(self) -> ConnectionStatus:
        """ステータスの取得"""
        return self.status

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        return {
            "provider_name": self.config.name,
            "provider_type": self.config.type.value,
            "status": self.status.value,
            "is_connected": self.is_connected(),
            "metrics": {
                "connection_count": self.metrics.connection_count,
                "disconnection_count": self.metrics.disconnection_count,
                "error_count": self.metrics.error_count,
                "total_messages_received": self.metrics.total_messages_received,
                "total_messages_sent": self.metrics.total_messages_sent
            },
            "last_connection_time": self.metrics.last_connection_time.isoformat() if self.metrics.last_connection_time else None,
            "last_disconnection_time": self.metrics.last_disconnection_time.isoformat() if self.metrics.last_disconnection_time else None,
            "last_error_time": self.metrics.last_error_time.isoformat() if self.metrics.last_error_time else None
        }

    async def close(self):
        """リソースのクリーンアップ"""
        await self.disconnect()
        self.logger.info(f"{self.config.name} provider closed")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from datetime import datetime, timezone
    
    # テスト用のプロバイダー設定
    config = ProviderConfig(
        name="test_provider",
        type=ProviderType.STREAM,
        base_url="https://api.example.com",
        timeout=30,
        retry_attempts=3,
        retry_delay=5,
        auto_reconnect=True,
        max_reconnect_attempts=5
    )
    
    # テスト用のプロバイダークラス
    class TestProvider(BaseProvider):
        async def connect(self) -> bool:
            self._update_status(ConnectionStatus.CONNECTED)
            return True
        
        async def disconnect(self) -> bool:
            self._update_status(ConnectionStatus.DISCONNECTED)
            return True
        
        async def send_message(self, message: Any) -> bool:
            self.metrics.total_messages_sent += 1
            return True
        
        async def start_listening(self) -> None:
            pass
        
        async def stop_listening(self) -> None:
            pass
    
    provider = TestProvider(config)
    
    try:
        print("🧪 ベースプロバイダーテスト...")
        
        # 接続
        success = await provider.connect()
        print(f"✅ 接続: {'成功' if success else '失敗'}")
        
        # ステータス確認
        print(f"✅ ステータス: {provider.get_status().value}")
        print(f"✅ 接続状態: {provider.is_connected()}")
        
        # メッセージ送信
        success = await provider.send_message("test message")
        print(f"✅ メッセージ送信: {'成功' if success else '失敗'}")
        
        # ヘルスチェック
        health = await provider.health_check()
        print(f"✅ ヘルスチェック:")
        print(f"   プロバイダー名: {health['provider_name']}")
        print(f"   プロバイダータイプ: {health['provider_type']}")
        print(f"   ステータス: {health['status']}")
        print(f"   接続状態: {health['is_connected']}")
        print(f"   接続回数: {health['metrics']['connection_count']}")
        print(f"   送信メッセージ数: {health['metrics']['total_messages_sent']}")
        
        # 切断
        success = await provider.disconnect()
        print(f"✅ 切断: {'成功' if success else '失敗'}")
        
        print("🎉 ベースプロバイダーテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await provider.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
