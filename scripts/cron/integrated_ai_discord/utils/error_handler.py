#!/usr/bin/env python3
"""
Error Handler Module
エラーハンドリング機能
"""

import traceback
from rich.console import Console


class ErrorHandler:
    """エラーハンドリングクラス"""

    def __init__(self):
        self.console = Console()

    def format_error_message(self, error: Exception, context: str = "") -> str:
        """エラーメッセージをフォーマット"""
        error_msg = f"❌ {context}エラー: {str(error)}"
        error_details = traceback.format_exc()
        
        # エラー詳細を追加（長すぎる場合は切り詰め）
        if len(error_details) > 3000:
            error_details = error_details[:3000] + "..."
        
        return f"{error_msg}\n詳細: {error_details}"

    def log_error(self, error: Exception, context: str = ""):
        """エラーをログ出力"""
        error_msg = self.format_error_message(error, context)
        self.console.print(error_msg)

    def handle_network_error(self, error: Exception, context: str = "") -> bool:
        """ネットワークエラーを処理"""
        error_msg = str(error).lower()
        
        if any(
            keyword in error_msg for keyword in ["timeout", "connection", "network"]
        ):
            self.console.print(f"⚠️ ネットワークエラー ({context}): {str(error)}")
            return True
        
        return False

    def handle_api_error(self, error: Exception, context: str = "") -> bool:
        """APIエラーを処理"""
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in ["api", "rate limit", "quota"]):
            self.console.print(f"⚠️ APIエラー ({context}): {str(error)}")
            return True
        
        return False

    def handle_database_error(self, error: Exception, context: str = "") -> bool:
        """データベースエラーを処理"""
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in ["database", "connection", "sql"]):
            self.console.print(f"⚠️ データベースエラー ({context}): {str(error)}")
            return True
        
        return False

    def create_error_notification(self, error: Exception, context: str = "") -> dict:
        """エラー通知用のデータを作成"""
        error_msg = self.format_error_message(error, context)
        
        return {
            "content": f"🚨 **{context}エラー**",
            "embeds": [
                {
                    "title": f"❌ {context} Error",
                    "description": f"```\n{error_msg[:4000]}\n```",
                    "color": 0xFF0000,
                }
            ],
        }
