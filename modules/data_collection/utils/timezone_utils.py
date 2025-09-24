#!/usr/bin/env python3
"""
タイムゾーン変換ユーティリティ

UTCとJSTの変換を行います。
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

# JSTタイムゾーン（UTC+9）
JST = timezone(timedelta(hours=9))
UTC = timezone.utc

logger = logging.getLogger(__name__)


class TimezoneUtils:
    """タイムゾーン変換ユーティリティクラス"""
    
    @staticmethod
    def utc_to_jst(utc_datetime: Union[datetime, str]) -> datetime:
        """UTC時刻をJST時刻に変換"""
        try:
            if isinstance(utc_datetime, str):
                # 文字列の場合はdatetimeに変換
                if utc_datetime.endswith('+00:00'):
                    utc_datetime = datetime.fromisoformat(utc_datetime.replace('+00:00', ''))
                    utc_datetime = utc_datetime.replace(tzinfo=UTC)
                else:
                    utc_datetime = datetime.fromisoformat(utc_datetime)
            
            # タイムゾーン情報がない場合はUTCとして扱う
            if utc_datetime.tzinfo is None:
                utc_datetime = utc_datetime.replace(tzinfo=UTC)
            
            # JSTに変換
            jst_datetime = utc_datetime.astimezone(JST)
            return jst_datetime
            
        except Exception as e:
            logger.error(f"UTC to JST conversion error: {e}")
            return utc_datetime
    
    @staticmethod
    def jst_to_utc(jst_datetime: Union[datetime, str]) -> datetime:
        """JST時刻をUTC時刻に変換"""
        try:
            if isinstance(jst_datetime, str):
                jst_datetime = datetime.fromisoformat(jst_datetime)
            
            # タイムゾーン情報がない場合はJSTとして扱う
            if jst_datetime.tzinfo is None:
                jst_datetime = jst_datetime.replace(tzinfo=JST)
            
            # UTCに変換
            utc_datetime = jst_datetime.astimezone(UTC)
            return utc_datetime
            
        except Exception as e:
            logger.error(f"JST to UTC conversion error: {e}")
            return jst_datetime
    
    @staticmethod
    def now_jst() -> datetime:
        """現在時刻をJSTで取得"""
        return datetime.now(JST)
    
    @staticmethod
    def now_utc() -> datetime:
        """現在時刻をUTCで取得"""
        return datetime.now(UTC)
    
    @staticmethod
    def format_jst(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """JST時刻をフォーマットして文字列で返す"""
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            
            jst_dt = dt.astimezone(JST)
            return jst_dt.strftime(format_str)
            
        except Exception as e:
            logger.error(f"JST formatting error: {e}")
            return str(dt)
    
    @staticmethod
    def format_utc(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """UTC時刻をフォーマットして文字列で返す"""
        try:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            
            return dt.strftime(format_str)
            
        except Exception as e:
            logger.error(f"UTC formatting error: {e}")
            return str(dt)
    
    @staticmethod
    def get_timezone_info() -> dict:
        """タイムゾーン情報を取得"""
        now_utc = TimezoneUtils.now_utc()
        now_jst = TimezoneUtils.now_jst()
        
        return {
            "utc_now": now_utc,
            "jst_now": now_jst,
            "utc_offset": "+00:00",
            "jst_offset": "+09:00",
            "timezone_difference": "9時間"
        }


# 便利な関数
def utc_to_jst(utc_datetime: Union[datetime, str]) -> datetime:
    """UTC時刻をJST時刻に変換（関数版）"""
    return TimezoneUtils.utc_to_jst(utc_datetime)


def jst_to_utc(jst_datetime: Union[datetime, str]) -> datetime:
    """JST時刻をUTC時刻に変換（関数版）"""
    return TimezoneUtils.jst_to_utc(jst_datetime)


def now_jst() -> datetime:
    """現在時刻をJSTで取得（関数版）"""
    return TimezoneUtils.now_jst()


def now_utc() -> datetime:
    """現在時刻をUTCで取得（関数版）"""
    return TimezoneUtils.now_utc()


def format_jst(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """JST時刻をフォーマットして文字列で返す（関数版）"""
    return TimezoneUtils.format_jst(dt, format_str)


def format_utc(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """UTC時刻をフォーマットして文字列で返す（関数版）"""
    return TimezoneUtils.format_utc(dt, format_str)


# テスト用
if __name__ == "__main__":
    # タイムゾーン情報を表示
    info = TimezoneUtils.get_timezone_info()
    print("🌏 タイムゾーン情報:")
    print(f"  UTC現在時刻: {info['utc_now']}")
    print(f"  JST現在時刻: {info['jst_now']}")
    print(f"  時差: {info['timezone_difference']}")
    
    # 変換テスト
    test_utc = datetime.now(UTC)
    test_jst = TimezoneUtils.utc_to_jst(test_utc)
    
    print(f"\n🔄 変換テスト:")
    print(f"  UTC: {test_utc}")
    print(f"  JST: {test_jst}")
    print(f"  JSTフォーマット: {TimezoneUtils.format_jst(test_utc)}")
