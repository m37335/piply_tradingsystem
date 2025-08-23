"""
investpyエラーハンドラー
investpyライブラリのエラー処理を担当
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class InvestpyErrorHandler:
    """investpyエラーハンドラー"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_count = 0
        self.last_error_time: Optional[datetime] = None
        self.error_history: list = []
    
    def handle_error(self, error: Exception) -> None:
        """
        エラーの処理
        
        Args:
            error: 発生したエラー
        """
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        error_info = {
            "timestamp": self.last_error_time,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_count": self.error_count
        }
        
        self.error_history.append(error_info)
        
        # エラーログの出力
        self.logger.error(
            f"Investpy error #{self.error_count}: {type(error).__name__}: {error}"
        )
        
        # エラータイプに応じた処理
        if isinstance(error, ConnectionError):
            self._handle_connection_error(error)
        elif isinstance(error, ValueError):
            self._handle_value_error(error)
        elif isinstance(error, TimeoutError):
            self._handle_timeout_error(error)
        else:
            self._handle_generic_error(error)
    
    def _handle_connection_error(self, error: ConnectionError) -> None:
        """接続エラーの処理"""
        self.logger.warning("Connection error detected. Retry recommended.")
        
        # 接続エラーの場合は少し待機を推奨
        wait_time = min(self.error_count * 5, 60)  # 最大60秒
        self.logger.info(f"Recommended wait time: {wait_time} seconds")
    
    def _handle_value_error(self, error: ValueError) -> None:
        """値エラーの処理"""
        self.logger.warning("Value error detected. Check input parameters.")
        
        # パラメータの検証を推奨
        if "date" in str(error).lower():
            self.logger.info("Check date format (DD/MM/YYYY)")
        elif "country" in str(error).lower():
            self.logger.info("Check country name format")
    
    def _handle_timeout_error(self, error: TimeoutError) -> None:
        """タイムアウトエラーの処理"""
        self.logger.warning("Timeout error detected. Network issue possible.")
        
        # ネットワーク問題の可能性
        self.logger.info("Check network connection and try again")
    
    def _handle_generic_error(self, error: Exception) -> None:
        """汎用エラーの処理"""
        self.logger.warning("Generic error detected. Check error details.")
    
    def should_retry(self, max_retries: int = 3) -> bool:
        """
        リトライすべきかどうかを判定
        
        Args:
            max_retries: 最大リトライ回数
            
        Returns:
            bool: リトライすべき場合True
        """
        if self.error_count >= max_retries:
            return False
        
        # 最後のエラーから一定時間経過しているかチェック
        if self.last_error_time:
            time_since_last_error = datetime.now() - self.last_error_time
            if time_since_last_error < timedelta(minutes=5):
                return False
        
        return True
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        エラーサマリーを取得
        
        Returns:
            Dict[str, Any]: エラーサマリー
        """
        return {
            "total_errors": self.error_count,
            "last_error_time": (
                self.last_error_time.isoformat() if self.last_error_time else None
            ),
            "recent_errors": self.error_history[-5:] if self.error_history else []
        }
    
    def reset_error_count(self) -> None:
        """エラーカウントをリセット"""
        self.error_count = 0
        self.last_error_time = None
        self.logger.info("Error count reset")
    
    def is_healthy(self) -> bool:
        """
        システムが健全かどうかを判定
        
        Returns:
            bool: 健全な場合True
        """
        # エラーが多すぎる場合は不健全
        if self.error_count > 10:
            return False
        
        # 最近のエラーが多すぎる場合は不健全
        recent_errors = [
            error for error in self.error_history
            if error["timestamp"] > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_errors) > 5:
            return False
        
        return True
