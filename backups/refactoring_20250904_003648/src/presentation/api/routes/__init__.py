"""
API Routes Package
API ルーターパッケージ

設計書参照:
- プレゼンテーション層設計_20250809.md

Exchange Analytics API の全ルーターを管理
"""

from . import ai_reports, alerts, analysis, health, plugins, rates

__all__ = ["health", "rates", "analysis", "ai_reports", "alerts", "plugins"]
