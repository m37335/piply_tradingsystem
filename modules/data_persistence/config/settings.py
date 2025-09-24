"""
データ永続化設定

データベース接続と設定を管理します。
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
try:
    from dotenv import load_dotenv
    # .envファイルを読み込み
    load_dotenv()
except ImportError:
    pass  # dotenvが利用できない場合は環境変数を直接使用


@dataclass
class DatabaseConfig:
    """データベース設定"""

    host: str = "localhost"
    port: int = 5432
    database: str = "trading_system"
    username: str = "postgres"
    password: str = "Postgres_Secure_2025!"
    min_connections: int = 3  # 最適化: 最小接続数を削減
    max_connections: int = 15  # 最適化: 最大接続数を削減
    connection_timeout: int = 60

    @property
    def connection_string(self) -> str:
        """接続文字列を生成"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """環境変数から設定を読み込み"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "trading_system"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20")),
            connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "60")),
        )


@dataclass
class DataPersistenceSettings:
    """データ永続化設定"""

    database: DatabaseConfig
    enable_timescaledb: bool = True
    enable_compression: bool = True
    compression_interval: str = "7 days"
    retention_period: str = "1 year"

    @classmethod
    def from_env(cls) -> "DataPersistenceSettings":
        """環境変数から設定を読み込み"""
        return cls(
            database=DatabaseConfig.from_env(),
            enable_timescaledb=os.getenv("ENABLE_TIMESCALEDB", "true").lower()
            == "true",
            enable_compression=os.getenv("ENABLE_COMPRESSION", "true").lower()
            == "true",
            compression_interval=os.getenv("COMPRESSION_INTERVAL", "7 days"),
            retention_period=os.getenv("RETENTION_PERIOD", "1 year"),
        )
