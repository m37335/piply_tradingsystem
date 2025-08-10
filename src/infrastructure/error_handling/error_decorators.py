#!/usr/bin/env python3
"""
エラーハンドリング用デコレータ
"""

import asyncio
import functools
from typing import Optional, Dict, Any, Callable
from src.infrastructure.error_handling.error_recovery_manager import (
    ErrorRecoveryManager, ErrorType
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


def handle_errors(error_type: ErrorType, context: Optional[Dict] = None):
    """
    エラーハンドリングデコレータ
    
    Args:
        error_type: エラーの種類
        context: エラーコンテキスト
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # エラーハンドリングマネージャーを取得
                error_manager = _get_error_manager_from_args(args)
                if error_manager:
                    await error_manager.handle_error(
                        error_type=error_type,
                        error_message=str(e),
                        context=context or {},
                        exception=e
                    )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # エラーハンドリングマネージャーを取得
                error_manager = _get_error_manager_from_args(args)
                if error_manager:
                    # 非同期関数を同期的に実行
                    asyncio.create_task(
                        error_manager.handle_error(
                            error_type=error_type,
                            error_message=str(e),
                            context=context or {},
                            exception=e
                        )
                    )
                raise
        
        # 関数が非同期かどうかを判定
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                  error_type: ErrorType = ErrorType.DATA_FETCH):
    """
    エラー時にリトライするデコレータ
    
    Args:
        max_retries: 最大リトライ回数
        delay: リトライ間隔（秒）
        error_type: エラーの種類
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"操作が失敗しました (試行 {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        await asyncio.sleep(delay * (attempt + 1))  # 指数バックオフ
                    else:
                        logger.error(f"最大リトライ回数に達しました: {e}")
                        
                        # エラーハンドリングマネージャーに通知
                        error_manager = _get_error_manager_from_args(args)
                        if error_manager:
                            await error_manager.handle_error(
                                error_type=error_type,
                                error_message=str(e),
                                context={"max_retries": max_retries, "attempts": attempt + 1},
                                exception=e
                            )
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"操作が失敗しました (試行 {attempt + 1}/{max_retries + 1}): {e}"
                        )
                        time.sleep(delay * (attempt + 1))  # 指数バックオフ
                    else:
                        logger.error(f"最大リトライ回数に達しました: {e}")
                        
                        # エラーハンドリングマネージャーに通知
                        error_manager = _get_error_manager_from_args(args)
                        if error_manager:
                            asyncio.create_task(
                                error_manager.handle_error(
                                    error_type=error_type,
                                    error_message=str(e),
                                    context={"max_retries": max_retries, "attempts": attempt + 1},
                                    exception=e
                                )
                            )
            
            raise last_exception
        
        # 関数が非同期かどうかを判定
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def circuit_breaker(failure_threshold: int = 5, recovery_timeout: float = 60.0,
                   error_type: ErrorType = ErrorType.API_CONNECTION):
    """
    サーキットブレーカーデコレータ
    
    Args:
        failure_threshold: 失敗閾値
        recovery_timeout: 復旧タイムアウト（秒）
        error_type: エラーの種類
    """
    def decorator(func: Callable):
        import time
        # サーキットブレーカーの状態
        failure_count = 0
        last_failure_time = None
        state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal failure_count, last_failure_time, state
            
            # サーキットブレーカーの状態をチェック
            if state == "OPEN":
                if time.time() - last_failure_time > recovery_timeout:
                    state = "HALF_OPEN"
                    logger.info("サーキットブレーカーがHALF_OPEN状態になりました")
                else:
                    raise Exception("サーキットブレーカーがOPEN状態です")
            
            try:
                result = await func(*args, **kwargs)
                
                # 成功した場合
                if state == "HALF_OPEN":
                    state = "CLOSED"
                    failure_count = 0
                    logger.info("サーキットブレーカーがCLOSED状態に復旧しました")
                
                return result
                
            except Exception as e:
                failure_count += 1
                last_failure_time = time.time()
                
                if failure_count >= failure_threshold:
                    state = "OPEN"
                    logger.error(f"サーキットブレーカーがOPEN状態になりました: {e}")
                    
                    # エラーハンドリングマネージャーに通知
                    error_manager = _get_error_manager_from_args(args)
                    if error_manager:
                        await error_manager.handle_error(
                            error_type=error_type,
                            error_message=f"サーキットブレーカーがトリガーされました: {e}",
                            context={"failure_count": failure_count, "state": state},
                            exception=e
                        )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal failure_count, last_failure_time, state
            
            # サーキットブレーカーの状態をチェック
            if state == "OPEN":
                if time.time() - last_failure_time > recovery_timeout:
                    state = "HALF_OPEN"
                    logger.info("サーキットブレーカーがHALF_OPEN状態になりました")
                else:
                    raise Exception("サーキットブレーカーがOPEN状態です")
            
            try:
                result = func(*args, **kwargs)
                
                # 成功した場合
                if state == "HALF_OPEN":
                    state = "CLOSED"
                    failure_count = 0
                    logger.info("サーキットブレーカーがCLOSED状態に復旧しました")
                
                return result
                
            except Exception as e:
                failure_count += 1
                last_failure_time = time.time()
                
                if failure_count >= failure_threshold:
                    state = "OPEN"
                    logger.error(f"サーキットブレーカーがOPEN状態になりました: {e}")
                    
                    # エラーハンドリングマネージャーに通知
                    error_manager = _get_error_manager_from_args(args)
                    if error_manager:
                        asyncio.create_task(
                            error_manager.handle_error(
                                error_type=error_type,
                                error_message=f"サーキットブレーカーがトリガーされました: {e}",
                                context={"failure_count": failure_count, "state": state},
                                exception=e
                            )
                        )
                
                raise
        
        # 関数が非同期かどうかを判定
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def timeout_handler(timeout_seconds: float = 30.0, 
                   error_type: ErrorType = ErrorType.DATA_FETCH):
    """
    タイムアウトハンドラーデコレータ
    
    Args:
        timeout_seconds: タイムアウト時間（秒）
        error_type: エラーの種類
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError as e:
                error_message = f"操作がタイムアウトしました ({timeout_seconds}秒)"
                logger.error(error_message)
                
                # エラーハンドリングマネージャーに通知
                error_manager = _get_error_manager_from_args(args)
                if error_manager:
                    await error_manager.handle_error(
                        error_type=error_type,
                        error_message=error_message,
                        context={"timeout_seconds": timeout_seconds},
                        exception=e
                    )
                
                raise TimeoutError(error_message)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler_signal(signum, frame):
                raise TimeoutError(f"操作がタイムアウトしました ({timeout_seconds}秒)")
            
            # シグナルハンドラーを設定
            old_handler = signal.signal(signal.SIGALRM, timeout_handler_signal)
            signal.alarm(int(timeout_seconds))
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # アラームをキャンセル
                return result
            except TimeoutError as e:
                logger.error(str(e))
                
                # エラーハンドリングマネージャーに通知
                error_manager = _get_error_manager_from_args(args)
                if error_manager:
                    asyncio.create_task(
                        error_manager.handle_error(
                            error_type=error_type,
                            error_message=str(e),
                            context={"timeout_seconds": timeout_seconds},
                            exception=e
                        )
                    )
                
                raise
            finally:
                signal.signal(signal.SIGALRM, old_handler)
                signal.alarm(0)
        
        # 関数が非同期かどうかを判定
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _get_error_manager_from_args(args: tuple) -> Optional[ErrorRecoveryManager]:
    """引数からエラーハンドリングマネージャーを取得"""
    for arg in args:
        if hasattr(arg, 'error_manager'):
            return arg.error_manager
        elif isinstance(arg, ErrorRecoveryManager):
            return arg
    return None


# 使用例のデコレータ
def database_operation(func: Callable):
    """データベース操作用のエラーハンドリングデコレータ"""
    return handle_errors(ErrorType.DATABASE_CONNECTION, {"operation": "database"})(func)


def api_operation(func: Callable):
    """API操作用のエラーハンドリングデコレータ"""
    return handle_errors(ErrorType.API_CONNECTION, {"operation": "api"})(func)


def data_fetch_operation(func: Callable):
    """データ取得用のエラーハンドリングデコレータ"""
    return handle_errors(ErrorType.DATA_FETCH, {"operation": "data_fetch"})(func)


def pattern_detection_operation(func: Callable):
    """パターン検出用のエラーハンドリングデコレータ"""
    return handle_errors(ErrorType.PATTERN_DETECTION, {"operation": "pattern_detection"})(func)
