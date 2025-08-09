from .base import BaseConfig


class TestingConfig(BaseConfig):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    REDIS_URL = "redis://localhost:6379/1"
