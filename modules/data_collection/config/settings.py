"""
データ収集設定

データ収集に関する設定を管理します。
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
try:
    from dotenv import load_dotenv
    # .envファイルを読み込み
    load_dotenv()
except ImportError:
    pass  # dotenvが利用できない場合は環境変数を直接使用


class TimeFrame(Enum):
    """時間フレーム"""

    M5 = "5m"  # 5分足（メイン対象）
    M15 = "15m"  # 15分足
    H1 = "1h"  # 1時間足
    H4 = "4h"  # 4時間足
    D1 = "1d"  # 日足


class DataCollectionMode(Enum):
    """データ収集モード"""

    BACKFILL = "backfill"
    CONTINUOUS = "continuous"
    MANUAL = "manual"


@dataclass
class YahooFinanceConfig:
    """Yahoo Finance設定"""

    rate_limit_per_second: float = 10.0
    burst_capacity: int = 50
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    @classmethod
    def from_env(cls) -> "YahooFinanceConfig":
        """環境変数から設定を読み込み"""
        return cls(
            rate_limit_per_second=float(os.getenv("YAHOO_FINANCE_RATE_LIMIT", "10.0")),
            burst_capacity=int(os.getenv("YAHOO_FINANCE_BURST_CAPACITY", "50")),
            timeout_seconds=int(os.getenv("YAHOO_FINANCE_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("YAHOO_FINANCE_RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=float(os.getenv("YAHOO_FINANCE_RETRY_DELAY", "1.0")),
            user_agent=os.getenv("YAHOO_FINANCE_USER_AGENT", cls().user_agent),
        )


@dataclass
class DatabaseConfig:
    """データベース設定"""

    host: str = "localhost"
    port: int = 5432
    database: str = "trading_system"
    username: str = "postgres"
    password: str = "Postgres_Secure_2025!"
    min_connections: int = 5
    max_connections: int = 20

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
        )


@dataclass
class CollectionConfig:
    """収集設定"""

    symbols: List[str]
    timeframes: List[TimeFrame]
    mode: DataCollectionMode
    batch_size: int = 100
    max_workers: int = 5
    collection_interval_seconds: int = 300  # 5分

    @classmethod
    def from_env(cls) -> "CollectionConfig":
        """環境変数から設定を読み込み"""
        symbols_str = os.getenv("COLLECTION_SYMBOLS", "USDJPY=X")
        symbols = [s.strip() for s in symbols_str.split(",")]

        timeframes_str = os.getenv("COLLECTION_TIMEFRAMES", "5m,15m,1h,4h,1d")
        timeframes = [TimeFrame(tf.strip()) for tf in timeframes_str.split(",")]

        mode_str = os.getenv("COLLECTION_MODE", "continuous")
        mode = DataCollectionMode(mode_str)

        return cls(
            symbols=symbols,
            timeframes=timeframes,
            mode=mode,
            batch_size=int(os.getenv("DATA_COLLECTION_BATCH_SIZE", "100")),
            max_workers=int(os.getenv("DATA_COLLECTION_MAX_WORKERS", "5")),
            collection_interval_seconds=int(
                os.getenv("DATA_COLLECTION_INTERVAL", "300")
            ),
        )


@dataclass
class DataCollectionSettings:
    """データ収集設定"""

    yahoo_finance: YahooFinanceConfig
    database: DatabaseConfig
    collection: CollectionConfig
    log_level: str = "INFO"
    enable_quality_checks: bool = True
    quality_threshold: float = 0.95

    @classmethod
    def from_env(cls) -> "DataCollectionSettings":
        """環境変数から設定を読み込み"""
        return cls(
            yahoo_finance=YahooFinanceConfig.from_env(),
            database=DatabaseConfig.from_env(),
            collection=CollectionConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_quality_checks=os.getenv("ENABLE_QUALITY_CHECKS", "true").lower()
            == "true",
            quality_threshold=float(os.getenv("QUALITY_THRESHOLD", "0.95")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書に変換"""
        return {
            "yahoo_finance": {
                "rate_limit_per_second": self.yahoo_finance.rate_limit_per_second,
                "burst_capacity": self.yahoo_finance.burst_capacity,
                "timeout_seconds": self.yahoo_finance.timeout_seconds,
                "retry_attempts": self.yahoo_finance.retry_attempts,
                "retry_delay_seconds": self.yahoo_finance.retry_delay_seconds,
            },
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "min_connections": self.database.min_connections,
                "max_connections": self.database.max_connections,
            },
            "collection": {
                "symbols": self.collection.symbols,
                "timeframes": [tf.value for tf in self.collection.timeframes],
                "mode": self.collection.mode.value,
                "batch_size": self.collection.batch_size,
                "max_workers": self.collection.max_workers,
                "collection_interval_seconds": self.collection.collection_interval_seconds,
            },
            "log_level": self.log_level,
            "enable_quality_checks": self.enable_quality_checks,
            "quality_threshold": self.quality_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataCollectionSettings":
        """辞書から設定を作成"""
        yahoo_finance = YahooFinanceConfig(**data["yahoo_finance"])
        database = DatabaseConfig(**data["database"])

        collection_data = data["collection"]
        timeframes = [TimeFrame(tf) for tf in collection_data["timeframes"]]
        mode = DataCollectionMode(collection_data["mode"])
        collection = CollectionConfig(
            symbols=collection_data["symbols"],
            timeframes=timeframes,
            mode=mode,
            batch_size=collection_data["batch_size"],
            max_workers=collection_data["max_workers"],
            collection_interval_seconds=collection_data["collection_interval_seconds"],
        )

        return cls(
            yahoo_finance=yahoo_finance,
            database=database,
            collection=collection,
            log_level=data["log_level"],
            enable_quality_checks=data["enable_quality_checks"],
            quality_threshold=data["quality_threshold"],
        )
