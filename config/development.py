from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_ECHO = True
    LOG_LEVEL = "DEBUG"
