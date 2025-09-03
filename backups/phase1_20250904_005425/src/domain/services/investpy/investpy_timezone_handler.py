"""
Investpyタイムゾーンハンドラー

タイムゾーンの変換と処理
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pytz

import pandas as pd

from src.infrastructure.config.investpy import TimezoneConfig


class InvestpyTimezoneHandler:
    """
    Investpyタイムゾーンハンドラー
    
    タイムゾーンの変換、夏時間の処理を行う
    """

    def __init__(self, config: TimezoneConfig):
        """
        初期化
        
        Args:
            config: タイムゾーン設定
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # よく使用されるタイムゾーンをキャッシュ
        self._timezone_cache = {}
        self._load_common_timezones()

    def convert_to_utc(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        UTC変換
        
        Args:
            df: 変換対象のDataFrame
            
        Returns:
            pd.DataFrame: UTC変換済みのDataFrame
        """
        try:
            if df.empty:
                return df

            processed_df = df.copy()

            # 日付カラムがある場合の処理
            if "date_utc" in processed_df.columns:
                processed_df = self._convert_datetime_to_utc(processed_df)

            # 時間カラムがある場合の処理
            if "time_utc" in processed_df.columns:
                processed_df = self._process_time_column(processed_df)

            self.logger.debug("UTC変換完了")
            return processed_df

        except Exception as e:
            self.logger.error(f"UTC変換エラー: {e}")
            return df

    def convert_to_jst(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        JST変換
        
        Args:
            df: 変換対象のDataFrame
            
        Returns:
            pd.DataFrame: JST変換済みのDataFrame
        """
        try:
            if df.empty:
                return df

            processed_df = df.copy()

            # UTC -> JST変換
            if "date_utc" in processed_df.columns:
                jst_tz = self._get_timezone("Asia/Tokyo")
                date_series = pd.to_datetime(processed_df["date_utc"])
                
                # タイムゾーン情報がある場合とない場合を分けて処理
                if date_series.dt.tz is None:
                    processed_df["date_jst"] = (
                        date_series
                        .dt.tz_localize("UTC")
                        .dt.tz_convert(jst_tz)
                    )
                else:
                    processed_df["date_jst"] = (
                        date_series.dt.tz_convert(jst_tz)
                    )

            self.logger.debug("JST変換完了")
            return processed_df

        except Exception as e:
            self.logger.error(f"JST変換エラー: {e}")
            return df

    def convert_to_display_timezone(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        表示用タイムゾーンに変換
        
        Args:
            df: 変換対象のDataFrame
            
        Returns:
            pd.DataFrame: 表示用タイムゾーン変換済みのDataFrame
        """
        try:
            if df.empty:
                return df

            processed_df = df.copy()
            display_tz = self._get_timezone(self.config.display_timezone)

            if "date_utc" in processed_df.columns:
                processed_df["date_display"] = (
                    pd.to_datetime(processed_df["date_utc"])
                    .dt.tz_localize("UTC")
                    .dt.tz_convert(display_tz)
                )

            return processed_df

        except Exception as e:
            self.logger.error(f"表示用タイムゾーン変換エラー: {e}")
            return df

    def handle_dst(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        夏時間処理
        
        Args:
            df: 処理対象のDataFrame
            
        Returns:
            pd.DataFrame: 夏時間処理済みのDataFrame
        """
        try:
            if not self.config.dst_handling or df.empty:
                return df

            processed_df = df.copy()

            # 夏時間の影響を受ける国の処理
            dst_countries = [
                "united states", "euro zone", "united kingdom", "canada"
            ]

            if "country" in processed_df.columns:
                for country in dst_countries:
                    country_mask = (
                        processed_df["country"].str.lower() == country.lower()
                    )
                    if country_mask.any():
                        processed_df.loc[country_mask] = (
                            self._apply_dst_correction(
                                processed_df.loc[country_mask], country
                            )
                        )

            return processed_df

        except Exception as e:
            self.logger.error(f"夏時間処理エラー: {e}")
            return df

    def get_timezone_info(self, country: str) -> Dict[str, Any]:
        """
        国のタイムゾーン情報を取得
        
        Args:
            country: 国名
            
        Returns:
            Dict[str, Any]: タイムゾーン情報
        """
        timezone_mapping = {
            "united states": {
                "timezone": "America/New_York",
                "name": "Eastern Time",
                "offset_utc": -5,
                "dst": True,
            },
            "japan": {
                "timezone": "Asia/Tokyo",
                "name": "Japan Standard Time",
                "offset_utc": 9,
                "dst": False,
            },
            "euro zone": {
                "timezone": "Europe/Frankfurt",
                "name": "Central European Time",
                "offset_utc": 1,
                "dst": True,
            },
            "united kingdom": {
                "timezone": "Europe/London",
                "name": "Greenwich Mean Time",
                "offset_utc": 0,
                "dst": True,
            },
            "australia": {
                "timezone": "Australia/Sydney",
                "name": "Australian Eastern Time",
                "offset_utc": 10,
                "dst": True,
            },
            "canada": {
                "timezone": "America/Toronto",
                "name": "Eastern Time",
                "offset_utc": -5,
                "dst": True,
            },
        }

        return timezone_mapping.get(
            country.lower(),
            {
                "timezone": "UTC",
                "name": "Coordinated Universal Time",
                "offset_utc": 0,
                "dst": False,
            },
        )

    def _convert_datetime_to_utc(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        日時をUTCに変換
        """
        processed_df = df.copy()

        # 既にUTCの場合はそのまま
        if processed_df["date_utc"].dt.tz is not None:
            processed_df["date_utc"] = (
                processed_df["date_utc"].dt.tz_convert("UTC")
            )
        else:
            # タイムゾーン情報がない場合、デフォルトタイムゾーンを適用
            default_tz = self._get_timezone(self.config.default_timezone)
            processed_df["date_utc"] = (
                processed_df["date_utc"]
                .dt.tz_localize(default_tz)
                .dt.tz_convert("UTC")
            )

        return processed_df

    def _process_time_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        時間カラムの処理
        """
        processed_df = df.copy()

        # 時間が文字列の場合、適切な形式に変換
        if processed_df["time_utc"].dtype == "object":
            processed_df["time_utc"] = pd.to_datetime(
                processed_df["time_utc"], format="%H:%M", errors="coerce"
            ).dt.time

        return processed_df

    def _apply_dst_correction(
        self, df: pd.DataFrame, country: str
    ) -> pd.DataFrame:
        """
        夏時間補正を適用
        """
        processed_df = df.copy()
        timezone_info = self.get_timezone_info(country)

        if not timezone_info["dst"]:
            return processed_df

        # 夏時間期間の判定と補正
        # 簡易実装：3月最終日曜日～10月最終日曜日を夏時間とする
        if "date_utc" in processed_df.columns:
            dates = pd.to_datetime(processed_df["date_utc"])
            
            # 月による簡易判定
            dst_mask = (dates.dt.month >= 3) & (dates.dt.month <= 10)
            
            # 夏時間期間のデータは1時間早める
            if dst_mask.any():
                processed_df.loc[dst_mask, "date_utc"] = (
                    processed_df.loc[dst_mask, "date_utc"] - pd.Timedelta(hours=1)
                )

        return processed_df

    def _get_timezone(self, timezone_str: str) -> pytz.BaseTzInfo:
        """
        タイムゾーンオブジェクトを取得（キャッシュ使用）
        """
        if timezone_str not in self._timezone_cache:
            try:
                if timezone_str in ["GMT", "UTC"]:
                    self._timezone_cache[timezone_str] = pytz.UTC
                else:
                    self._timezone_cache[timezone_str] = pytz.timezone(
                        timezone_str
                    )
            except pytz.exceptions.UnknownTimeZoneError:
                self.logger.warning(
                    f"不明なタイムゾーン: {timezone_str}, UTCを使用"
                )
                self._timezone_cache[timezone_str] = pytz.UTC

        return self._timezone_cache[timezone_str]

    def _load_common_timezones(self):
        """
        よく使用されるタイムゾーンを事前にロード
        """
        common_timezones = [
            "UTC",
            "Asia/Tokyo",
            "America/New_York",
            "Europe/London",
            "Europe/Frankfurt",
            "Australia/Sydney",
            "America/Toronto",
        ]

        for tz_str in common_timezones:
            self._get_timezone(tz_str)

    def convert_timestamp_to_utc(
        self, timestamp: datetime, source_timezone: str
    ) -> datetime:
        """
        単一のタイムスタンプをUTCに変換
        
        Args:
            timestamp: 変換対象のタイムスタンプ
            source_timezone: 元のタイムゾーン
            
        Returns:
            datetime: UTC変換済みのタイムスタンプ
        """
        try:
            source_tz = self._get_timezone(source_timezone)
            
            # タイムゾーン情報がない場合は追加
            if timestamp.tzinfo is None:
                localized_timestamp = source_tz.localize(timestamp)
            else:
                localized_timestamp = timestamp.astimezone(source_tz)
            
            # UTCに変換
            utc_timestamp = localized_timestamp.astimezone(pytz.UTC)
            
            return utc_timestamp.replace(tzinfo=None)  # naiveなdatetimeとして返す
            
        except Exception as e:
            self.logger.error(f"タイムスタンプ変換エラー: {e}")
            return timestamp

    def format_for_display(
        self, timestamp: datetime, timezone_str: Optional[str] = None
    ) -> str:
        """
        表示用にタイムスタンプをフォーマット
        
        Args:
            timestamp: フォーマット対象のタイムスタンプ
            timezone_str: 表示用タイムゾーン（デフォルトは設定値）
            
        Returns:
            str: フォーマット済みの文字列
        """
        try:
            display_tz_str = timezone_str or self.config.display_timezone
            display_tz = self._get_timezone(display_tz_str)
            
            # UTCとして扱ってから表示用タイムゾーンに変換
            if timestamp.tzinfo is None:
                utc_timestamp = pytz.UTC.localize(timestamp)
            else:
                utc_timestamp = timestamp.astimezone(pytz.UTC)
            
            display_timestamp = utc_timestamp.astimezone(display_tz)
            
            return display_timestamp.strftime(self.config.datetime_format)
            
        except Exception as e:
            self.logger.error(f"表示フォーマットエラー: {e}")
            return str(timestamp)

    def get_handler_stats(self) -> Dict[str, Any]:
        """
        ハンドラー統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            "handler": "InvestpyTimezoneHandler",
            "config": {
                "default_timezone": self.config.default_timezone,
                "display_timezone": self.config.display_timezone,
                "dst_handling": self.config.dst_handling,
            },
            "cached_timezones": list(self._timezone_cache.keys()),
            "supported_timezones": self.config.supported_timezones,
        }
