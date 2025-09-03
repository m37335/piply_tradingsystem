"""
データベース設定
データベース接続と設定を管理
"""

import os
import logging
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """データベース設定クラス"""
    
    # 接続情報
    host: str = "localhost"
    port: int = 5432
    database: str = "economic_calendar"
    username: str = "postgres"
    password: str = ""
    
    # 接続プール設定
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # その他設定
    echo: bool = False
    echo_pool: bool = False
    connect_timeout: int = 10
    
    def __post_init__(self):
        """環境変数から設定を読み込み"""
        self.host = os.getenv("DB_HOST", self.host)
        self.port = int(os.getenv("DB_PORT", str(self.port)))
        self.database = os.getenv("DB_NAME", self.database)
        self.username = os.getenv("DB_USER", self.username)
        self.password = os.getenv("DB_PASSWORD", self.password)
        
        # プール設定
        self.pool_size = int(os.getenv("DB_POOL_SIZE", str(self.pool_size)))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", str(self.max_overflow)))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", str(self.pool_timeout)))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", str(self.pool_recycle)))
        
        # デバッグ設定
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        self.echo_pool = os.getenv("DB_ECHO_POOL", "false").lower() == "true"
        
        # 接続タイムアウト
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", str(self.connect_timeout)))
    
    @property
    def database_url(self) -> str:
        """データベースURL（パスワードをエンコード）"""
        encoded_password = quote_plus(self.password) if self.password else ""
        if encoded_password:
            return f"postgresql://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.database}"
    
    @property
    def async_database_url(self) -> str:
        """非同期データベースURL"""
        encoded_password = quote_plus(self.password) if self.password else ""
        if encoded_password:
            return f"postgresql+asyncpg://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"postgresql+asyncpg://{self.username}@{self.host}:{self.port}/{self.database}"
    
    def get_sqlalchemy_config(self) -> Dict[str, Any]:
        """SQLAlchemy設定辞書を取得"""
        return {
            "url": self.database_url,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,  # 接続の健全性チェック
            "connect_args": {
                "connect_timeout": self.connect_timeout,
                "application_name": "investpy_economic_calendar"
            }
        }
    
    def get_async_sqlalchemy_config(self) -> Dict[str, Any]:
        """非同期SQLAlchemy設定辞書を取得"""
        return {
            "url": self.async_database_url,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
            "connect_args": {
                "server_settings": {
                    "application_name": "investpy_economic_calendar_async"
                }
            }
        }
    
    def validate(self) -> bool:
        """設定の妥当性をチェック"""
        if not self.host:
            logging.error("Database host is required")
            return False
        
        if not self.database:
            logging.error("Database name is required")
            return False
        
        if not self.username:
            logging.error("Database username is required")
            return False
        
        if self.port <= 0 or self.port > 65535:
            logging.error(f"Invalid database port: {self.port}")
            return False
        
        if self.pool_size <= 0:
            logging.error(f"Invalid pool size: {self.pool_size}")
            return False
        
        return True
    
    def __str__(self) -> str:
        """文字列表現（パスワードは隠蔽）"""
        return (
            f"DatabaseConfig("
            f"host='{self.host}', "
            f"port={self.port}, "
            f"database='{self.database}', "
            f"username='{self.username}', "
            f"password={'***' if self.password else 'None'}, "
            f"pool_size={self.pool_size}"
            f")"
        )
