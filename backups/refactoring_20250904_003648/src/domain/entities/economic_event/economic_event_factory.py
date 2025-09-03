"""
経済イベントファクトリ
EconomicEventの作成を担当するファクトリクラス
"""

from datetime import datetime, time
from decimal import Decimal
from typing import Dict, Any, Optional, List
import pandas as pd

from .economic_event import EconomicEvent, Importance
from .economic_event_validator import EconomicEventValidator


class EconomicEventFactory:
    """経済イベントファクトリ"""
    
    def __init__(self, validator: Optional[EconomicEventValidator] = None):
        self.validator = validator or EconomicEventValidator()
    
    def create_from_dict(self, data: Dict[str, Any]) -> EconomicEvent:
        """
        辞書からEconomicEventを作成
        
        Args:
            data: イベントデータの辞書
            
        Returns:
            EconomicEvent: 作成されたEconomicEventインスタンス
        """
        # データの正規化
        normalized_data = self._normalize_data(data)
        
        # EconomicEventの作成
        event = EconomicEvent(**normalized_data)
        
        # バリデーション
        if not self.validator.validate(event):
            error_messages = self.validator.get_error_messages()
            raise ValueError(f"Invalid EconomicEvent data: {error_messages}")
        
        return event
    
    def create_from_investpy_data(self, row: pd.Series) -> EconomicEvent:
        """
        investpyのDataFrame行からEconomicEventを作成
        
        Args:
            row: investpyのDataFrameの1行
            
        Returns:
            EconomicEvent: 作成されたEconomicEventインスタンス
        """
        # investpyデータの変換
        data = self._convert_investpy_row(row)
        
        return self.create_from_dict(data)
    
    def create_from_dataframe(self, df: pd.DataFrame) -> List[EconomicEvent]:
        """
        DataFrameからEconomicEventのリストを作成
        
        Args:
            df: investpyのDataFrame
            
        Returns:
            List[EconomicEvent]: 作成されたEconomicEventインスタンスのリスト
        """
        events = []
        
        for _, row in df.iterrows():
            try:
                event = self.create_from_investpy_data(row)
                events.append(event)
            except Exception as e:
                # 個別の行でエラーが発生しても他の行は処理を続行
                print(f"Error creating event from row: {e}")
                continue
        
        return events
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データの正規化"""
        normalized = {}
        
        # 基本フィールドのマッピング
        field_mapping = {
            "event_id": ["event_id", "id", "eventId"],
            "date_utc": ["date_utc", "date", "date_utc"],
            "time_utc": ["time_utc", "time", "time_utc"],
            "country": ["country", "Country"],
            "zone": ["zone", "Zone"],
            "event_name": ["event_name", "eventName", "Event"],
            "importance": ["importance", "Importance"],
            "actual_value": ["actual_value", "actualValue", "Actual"],
            "forecast_value": ["forecast_value", "forecastValue", "Forecast"],
            "previous_value": ["previous_value", "previousValue", "Previous"],
            "currency": ["currency", "Currency"],
            "unit": ["unit", "Unit"],
            "category": ["category", "Category"]
        }
        
        for target_field, source_fields in field_mapping.items():
            for source_field in source_fields:
                if source_field in data and data[source_field] is not None:
                    normalized[target_field] = data[source_field]
                    break
        
        # 日付の処理
        if "date_utc" in normalized:
            normalized["date_utc"] = self._parse_date(normalized["date_utc"])
        
        # 時間の処理
        if "time_utc" in normalized:
            normalized["time_utc"] = self._parse_time(normalized["time_utc"])
        
        # 重要度の処理
        if "importance" in normalized:
            normalized["importance"] = self._parse_importance(normalized["importance"])
        
        # 数値の処理
        for field in ["actual_value", "forecast_value", "previous_value"]:
            if field in normalized:
                normalized[field] = self._parse_decimal(normalized[field])
        
        return normalized
    
    def _convert_investpy_row(self, row: pd.Series) -> Dict[str, Any]:
        """investpyの行データを変換"""
        data = {}
        
        # investpyの列名をマッピング（実際の列名に合わせて修正）
        column_mapping = {
            "date": "date_utc",
            "time": "time_utc",
            "zone": "country",  # zoneが国名として使用されている
            "event": "event_name",
            "importance": "importance",
            "actual": "actual_value",
            "forecast": "forecast_value",
            "previous": "previous_value",
            "currency": "currency"
        }
        
        for investpy_col, target_field in column_mapping.items():
            if investpy_col in row.index and pd.notna(row[investpy_col]):
                data[target_field] = row[investpy_col]
        
        # event_idの生成（一意性を保つため）
        if "event_name" in data and "date_utc" in data:
            data["event_id"] = (
                f"{data.get('country', 'unknown')}_{data['event_name']}_{data['date_utc']}"
            )
        
        # 国名の正規化
        if "country" in data:
            country_mapping = {
                "japan": "japan",
                "united states": "united states",
                "euro zone": "euro zone",
                "united kingdom": "united kingdom",
                "australia": "australia",
                "canada": "canada"
            }
            data["country"] = country_mapping.get(
                data["country"].lower(), data["country"].lower()
            )
        
        return data
    
    def _parse_date(self, date_value: Any) -> datetime:
        """日付の解析"""
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            # 複数の日付形式に対応
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_value}")
        else:
            raise ValueError(f"Invalid date type: {type(date_value)}")
    
    def _parse_time(self, time_value: Any) -> Optional[time]:
        """時間の解析"""
        if time_value is None:
            return None
        elif isinstance(time_value, time):
            return time_value
        elif isinstance(time_value, str):
            # 複数の時間形式に対応
            for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]:
                try:
                    return datetime.strptime(time_value, fmt).time()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse time: {time_value}")
        else:
            raise ValueError(f"Invalid time type: {type(time_value)}")
    
    def _parse_importance(self, importance_value: Any) -> Importance:
        """重要度の解析"""
        if isinstance(importance_value, Importance):
            return importance_value
        elif isinstance(importance_value, str):
            importance_str = importance_value.lower().strip()
            
            # 重要度のマッピング
            importance_mapping = {
                "high": Importance.HIGH,
                "medium": Importance.MEDIUM,
                "low": Importance.LOW,
                "3": Importance.HIGH,
                "2": Importance.MEDIUM,
                "1": Importance.LOW,
                "★★★": Importance.HIGH,
                "★★": Importance.MEDIUM,
                "★": Importance.LOW
            }
            
            if importance_str in importance_mapping:
                return importance_mapping[importance_str]
            else:
                # デフォルトはLOW
                return Importance.LOW
        else:
            # デフォルトはLOW
            return Importance.LOW
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Decimal値の解析"""
        if value is None or pd.isna(value):
            return None
        elif isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, str):
            # 文字列から数値を抽出
            import re
            numeric_match = re.search(
                r'[-+]?\d*\.?\d+', value
            )
            if numeric_match:
                return Decimal(numeric_match.group())
            else:
                return None
        else:
            return None
    
    def create_sample_event(self) -> EconomicEvent:
        """サンプルイベントの作成（テスト用）"""
        sample_data = {
            "event_id": "japan_cpi_2024-01-15",
            "date_utc": datetime(2024, 1, 15, 0, 0),
            "time_utc": time(8, 30),
            "country": "japan",
            "zone": "Asia/Tokyo",
            "event_name": "Consumer Price Index (CPI)",
            "importance": Importance.HIGH,
            "actual_value": Decimal("2.5"),
            "forecast_value": Decimal("2.3"),
            "previous_value": Decimal("2.1"),
            "currency": "JPY",
            "unit": "%",
            "category": "inflation"
        }
        
        return self.create_from_dict(sample_data)
