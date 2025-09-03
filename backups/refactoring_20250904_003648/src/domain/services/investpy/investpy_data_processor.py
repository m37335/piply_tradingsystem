"""
Investpyデータプロセッサー

取得した生データの処理とフィルタリング
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd

from src.infrastructure.config.investpy import InvestpyConfig


class InvestpyDataProcessor:
    """
    Investpyデータプロセッサー
    
    取得した生データの処理、変換、フィルタリングを行う
    """

    def __init__(self, config: InvestpyConfig):
        """
        初期化
        
        Args:
            config: Investpy設定
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生データの処理
        
        Args:
            df: 生のDataFrame
            
        Returns:
            pd.DataFrame: 処理済みのDataFrame
        """
        try:
            self.logger.info(f"データ処理開始: {len(df)}行")

            if df.empty:
                self.logger.warning("空のDataFrameが渡されました")
                return df

            # データのコピーを作成
            processed_df = df.copy()

            # 基本的なデータクリーニング
            processed_df = self._clean_data(processed_df)

            # カラム名の正規化
            processed_df = self._normalize_columns(processed_df)

            # データ型の変換
            processed_df = self._convert_data_types(processed_df)

            # イベントIDの生成
            processed_df = self._generate_event_ids(processed_df)

            # データの拡張
            processed_df = self._enrich_data(processed_df)

            # 重複の除去
            processed_df = self._remove_duplicates(processed_df)

            # 最大件数の制限
            if len(processed_df) > self.config.max_events:
                self.logger.warning(
                    f"データ件数が上限を超過: {len(processed_df)} > "
                    f"{self.config.max_events}"
                )
                processed_df = processed_df.head(self.config.max_events)

            self.logger.info(f"データ処理完了: {len(processed_df)}行")
            return processed_df

        except Exception as e:
            self.logger.error(f"データ処理エラー: {e}")
            raise

    def filter_by_criteria(
        self,
        df: pd.DataFrame,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_range: Optional[tuple] = None,
    ) -> pd.DataFrame:
        """
        条件によるフィルタリング
        
        Args:
            df: フィルタリング対象のDataFrame
            countries: 対象国リスト
            importances: 重要度リスト
            categories: カテゴリリスト
            date_range: 日付範囲（開始日, 終了日）
            
        Returns:
            pd.DataFrame: フィルタリング済みのDataFrame
        """
        try:
            filtered_df = df.copy()

            # 国による絞り込み
            if countries:
                country_mask = filtered_df["country"].str.lower().isin(
                    [c.lower() for c in countries]
                )
                filtered_df = filtered_df[country_mask]
                self.logger.debug(f"国フィルタ後: {len(filtered_df)}行")

            # 重要度による絞り込み
            if importances:
                importance_mask = filtered_df["importance"].str.lower().isin(
                    [i.lower() for i in importances]
                )
                filtered_df = filtered_df[importance_mask]
                self.logger.debug(f"重要度フィルタ後: {len(filtered_df)}行")

            # カテゴリによる絞り込み
            if categories:
                category_mask = filtered_df["category"].str.lower().isin(
                    [c.lower() for c in categories]
                )
                filtered_df = filtered_df[category_mask]
                self.logger.debug(f"カテゴリフィルタ後: {len(filtered_df)}行")

            # 日付範囲による絞り込み
            if date_range and len(date_range) == 2:
                start_date, end_date = date_range
                if "date" in filtered_df.columns:
                    date_mask = (
                        (filtered_df["date"] >= start_date) &
                        (filtered_df["date"] <= end_date)
                    )
                    filtered_df = filtered_df[date_mask]
                    self.logger.debug(f"日付フィルタ後: {len(filtered_df)}行")

            return filtered_df

        except Exception as e:
            self.logger.error(f"フィルタリングエラー: {e}")
            return df

    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データの拡張
        
        Args:
            df: 拡張対象のDataFrame
            
        Returns:
            pd.DataFrame: 拡張済みのDataFrame
        """
        return self._enrich_data(df)

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データクリーニング
        """
        try:
            # 空白文字の削除
            string_columns = df.select_dtypes(include=["object"]).columns
            for col in string_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

            # 不要な文字の除去
            if "event" in df.columns:
                df["event"] = df["event"].astype(str).str.replace(r"\s+", " ", regex=True)

            return df
        except Exception as e:
            self.logger.warning(f"データクリーニングエラー: {e}")
            return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        カラム名の正規化
        """
        # カラム名を小文字に変換し、スペースをアンダースコアに変換
        df.columns = df.columns.str.lower().str.replace(" ", "_")

        # よく使用される名前に統一
        column_mapping = {
            "time": "time_utc",
            "date": "date_utc",
            "actual": "actual_value",
            "forecast": "forecast_value",
            "previous": "previous_value",
        }

        df = df.rename(columns=column_mapping)
        return df

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データ型の変換
        """
        # 数値カラムの変換
        numeric_columns = [
            "actual_value", "forecast_value", "previous_value"
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 日付カラムの変換
        if "date_utc" in df.columns:
            df["date_utc"] = pd.to_datetime(df["date_utc"], errors="coerce")

        # 重要度の正規化
        if "importance" in df.columns:
            importance_mapping = {
                "low": "low",
                "medium": "medium", 
                "med": "medium",
                "high": "high",
                "hi": "high",
            }
            df["importance"] = (
                df["importance"]
                .str.lower()
                .map(importance_mapping)
                .fillna("low")
            )

        return df

    def _generate_event_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        イベントIDの生成
        """
        if "event_id" not in df.columns:
            # 複数のフィールドを組み合わせてユニークIDを生成
            df["event_id"] = (
                df.get("country", "").astype(str) + "_" +
                df.get("event", "").astype(str).str.replace(" ", "_") + "_" +
                df.get("date_utc", datetime.utcnow()).astype(str).str[:10]
            )
            
            # ハッシュ化してよりコンパクトなIDにする
            df["event_id"] = (
                df["event_id"]
                .apply(lambda x: str(hash(x))[-10:])
            )

        return df

    def _enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データの拡張
        """
        # カテゴリの推定
        if "category" not in df.columns and "event" in df.columns:
            df["category"] = df["event"].apply(self._categorize_event)

        # 通貨の推定
        if "currency" not in df.columns and "country" in df.columns:
            df["currency"] = df["country"].apply(self._get_currency_from_country)

        # ゾーンの推定
        if "zone" not in df.columns and "country" in df.columns:
            df["zone"] = df["country"].apply(self._get_zone_from_country)

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重複の除去
        """
        # イベントID、日付、国の組み合わせで重複を除去
        duplicate_columns = ["event_id"]
        if "date_utc" in df.columns:
            duplicate_columns.append("date_utc")
        if "country" in df.columns:
            duplicate_columns.append("country")

        initial_count = len(df)
        df = df.drop_duplicates(subset=duplicate_columns, keep="first")
        removed_count = initial_count - len(df)

        if removed_count > 0:
            self.logger.info(f"重複除去: {removed_count}行")

        return df

    def _categorize_event(self, event_name: str) -> str:
        """
        イベント名からカテゴリを推定
        """
        if not event_name or pd.isna(event_name):
            return "other"

        event_lower = str(event_name).lower()

        if any(keyword in event_lower for keyword in [
            "cpi", "inflation", "price", "pce"
        ]):
            return "inflation"
        elif any(keyword in event_lower for keyword in [
            "employment", "jobless", "unemployment", "nfp", "payroll"
        ]):
            return "employment"
        elif any(keyword in event_lower for keyword in [
            "rate", "interest", "fed", "boj", "ecb", "boe"
        ]):
            return "interest_rate"
        elif any(keyword in event_lower for keyword in [
            "gdp", "growth", "production", "manufacturing"
        ]):
            return "gdp"
        elif any(keyword in event_lower for keyword in [
            "trade", "balance", "export", "import"
        ]):
            return "trade"
        else:
            return "other"

    def _get_currency_from_country(self, country: str) -> str:
        """
        国名から通貨コードを取得
        """
        if not country or pd.isna(country):
            return ""

        country_lower = str(country).lower()
        currency_mapping = {
            "united states": "USD",
            "japan": "JPY",
            "euro zone": "EUR",
            "eurozone": "EUR",
            "united kingdom": "GBP",
            "australia": "AUD",
            "canada": "CAD",
            "switzerland": "CHF",
            "new zealand": "NZD",
        }

        return currency_mapping.get(country_lower, "")

    def _get_zone_from_country(self, country: str) -> str:
        """
        国名からゾーン（地域）を取得
        """
        if not country or pd.isna(country):
            return ""

        country_lower = str(country).lower()
        zone_mapping = {
            "united states": "North America",
            "japan": "Asia",
            "euro zone": "Europe",
            "eurozone": "Europe",
            "united kingdom": "Europe",
            "australia": "Oceania",
            "canada": "North America",
            "switzerland": "Europe",
            "new zealand": "Oceania",
        }

        return zone_mapping.get(country_lower, "Other")

    def get_processing_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        処理統計情報を取得
        
        Args:
            df: 統計対象のDataFrame
            
        Returns:
            Dict[str, Any]: 統計情報
        """
        if df.empty:
            return {"total_events": 0}

        stats = {
            "total_events": len(df),
            "countries": df.get("country", pd.Series()).nunique(),
            "importances": df.get("importance", pd.Series()).value_counts().to_dict(),
            "categories": df.get("category", pd.Series()).value_counts().to_dict(),
            "date_range": {
                "start": (
                    df.get("date_utc", pd.Series()).min()
                    if "date_utc" in df.columns else None
                ),
                "end": (
                    df.get("date_utc", pd.Series()).max()
                    if "date_utc" in df.columns else None
                ),
            },
        }

        return stats
