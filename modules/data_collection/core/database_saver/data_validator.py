"""
データ検証システム

データの品質と整合性を検証します。
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """検証結果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    quality_score: float  # 0.0 - 1.0
    validated_at: datetime


@dataclass
class ValidationRule:
    """検証ルール"""
    name: str
    description: str
    validator_func: callable
    is_critical: bool = True  # クリティカルなルールかどうか
    weight: float = 1.0  # 重み


class DataValidator:
    """データ検証システム"""
    
    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self._init_default_rules()
    
    def _init_default_rules(self) -> None:
        """デフォルトの検証ルールを初期化"""
        # 価格データの検証ルール
        self.add_rule(
            "price_positive",
            "価格は正の値である必要があります",
            self._validate_price_positive,
            is_critical=True,
            weight=2.0
        )
        
        self.add_rule(
            "high_ge_low",
            "高値は安値以上である必要があります",
            self._validate_high_ge_low,
            is_critical=True,
            weight=2.0
        )
        
        self.add_rule(
            "high_ge_open_close",
            "高値は始値と終値以上である必要があります",
            self._validate_high_ge_open_close,
            is_critical=True,
            weight=1.5
        )
        
        self.add_rule(
            "low_le_open_close",
            "安値は始値と終値以下である必要があります",
            self._validate_low_le_open_close,
            is_critical=True,
            weight=1.5
        )
        
        self.add_rule(
            "volume_positive",
            "出来高は0以上である必要があります",
            self._validate_volume_positive,
            is_critical=False,
            weight=1.0
        )
        
        self.add_rule(
            "timestamp_valid",
            "タイムスタンプは有効な日時である必要があります",
            self._validate_timestamp_valid,
            is_critical=True,
            weight=1.5
        )
        
        self.add_rule(
            "timestamp_sequential",
            "タイムスタンプは時系列順である必要があります",
            self._validate_timestamp_sequential,
            is_critical=False,
            weight=1.0
        )
        
        self.add_rule(
            "price_reasonable",
            "価格は合理的な範囲内である必要があります",
            self._validate_price_reasonable,
            is_critical=False,
            weight=1.0
        )
    
    def add_rule(
        self,
        name: str,
        description: str,
        validator_func: callable,
        is_critical: bool = True,
        weight: float = 1.0
    ) -> None:
        """
        検証ルールを追加
        
        Args:
            name: ルール名
            description: ルールの説明
            validator_func: 検証関数
            is_critical: クリティカルなルールかどうか
            weight: 重み
        """
        rule = ValidationRule(
            name=name,
            description=description,
            validator_func=validator_func,
            is_critical=is_critical,
            weight=weight
        )
        self.rules[name] = rule
    
    def remove_rule(self, name: str) -> bool:
        """
        検証ルールを削除
        
        Args:
            name: ルール名
            
        Returns:
            削除が成功したかどうか
        """
        if name in self.rules:
            del self.rules[name]
            return True
        return False
    
    def validate_single_record(self, record: Dict[str, Any]) -> ValidationResult:
        """
        単一レコードを検証
        
        Args:
            record: 検証するレコード
            
        Returns:
            検証結果
        """
        errors = []
        warnings = []
        total_weight = 0.0
        passed_weight = 0.0
        
        for rule_name, rule in self.rules.items():
            try:
                is_valid, message = rule.validator_func(record)
                total_weight += rule.weight
                
                if is_valid:
                    passed_weight += rule.weight
                else:
                    if rule.is_critical:
                        errors.append(f"{rule_name}: {message}")
                    else:
                        warnings.append(f"{rule_name}: {message}")
                        
            except Exception as e:
                logger.error(f"Validation rule {rule_name} failed: {e}")
                errors.append(f"{rule_name}: Validation error - {str(e)}")
                total_weight += rule.weight
        
        # 品質スコアを計算
        quality_score = passed_weight / total_weight if total_weight > 0 else 0.0
        
        # クリティカルなエラーがある場合は無効
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score,
            validated_at=datetime.now()
        )
    
    def validate_batch(self, records: List[Dict[str, Any]]) -> List[ValidationResult]:
        """
        バッチのレコードを検証
        
        Args:
            records: 検証するレコードのリスト
            
        Returns:
            検証結果のリスト
        """
        results = []
        for record in records:
            result = self.validate_single_record(record)
            results.append(result)
        return results
    
    def validate_with_context(
        self,
        record: Dict[str, Any],
        previous_record: Optional[Dict[str, Any]] = None,
        next_record: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        コンテキスト付きでレコードを検証
        
        Args:
            record: 検証するレコード
            previous_record: 前のレコード
            next_record: 次のレコード
            
        Returns:
            検証結果
        """
        # 基本的な検証
        result = self.validate_single_record(record)
        
        # コンテキストベースの検証を追加
        if previous_record:
            context_result = self._validate_with_previous(record, previous_record)
            result.errors.extend(context_result.errors)
            result.warnings.extend(context_result.warnings)
            result.quality_score = (result.quality_score + context_result.quality_score) / 2
        
        if next_record:
            context_result = self._validate_with_next(record, next_record)
            result.errors.extend(context_result.errors)
            result.warnings.extend(context_result.warnings)
            result.quality_score = (result.quality_score + context_result.quality_score) / 2
        
        # 最終的な有効性を再評価
        result.is_valid = len(result.errors) == 0
        
        return result
    
    def _validate_price_positive(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """価格が正の値かチェック"""
        price_fields = ['open', 'high', 'low', 'close']
        
        for field in price_fields:
            if field in record and record[field] is not None:
                if record[field] <= 0:
                    return False, f"{field} price must be positive, got {record[field]}"
        
        return True, "All prices are positive"
    
    def _validate_high_ge_low(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """高値が安値以上かチェック"""
        if 'high' in record and 'low' in record:
            if record['high'] is not None and record['low'] is not None:
                if record['high'] < record['low']:
                    return False, f"High ({record['high']}) must be >= Low ({record['low']})"
        
        return True, "High >= Low"
    
    def _validate_high_ge_open_close(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """高値が始値と終値以上かチェック"""
        if 'high' in record and record['high'] is not None:
            if 'open' in record and record['open'] is not None:
                if record['high'] < record['open']:
                    return False, f"High ({record['high']}) must be >= Open ({record['open']})"
            
            if 'close' in record and record['close'] is not None:
                if record['high'] < record['close']:
                    return False, f"High ({record['high']}) must be >= Close ({record['close']})"
        
        return True, "High >= Open and Close"
    
    def _validate_low_le_open_close(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """安値が始値と終値以下かチェック"""
        if 'low' in record and record['low'] is not None:
            if 'open' in record and record['open'] is not None:
                if record['low'] > record['open']:
                    return False, f"Low ({record['low']}) must be <= Open ({record['open']})"
            
            if 'close' in record and record['close'] is not None:
                if record['low'] > record['close']:
                    return False, f"Low ({record['low']}) must be <= Close ({record['close']})"
        
        return True, "Low <= Open and Close"
    
    def _validate_volume_positive(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """出来高が0以上かチェック"""
        if 'volume' in record and record['volume'] is not None:
            if record['volume'] < 0:
                return False, f"Volume must be >= 0, got {record['volume']}"
        
        return True, "Volume is non-negative"
    
    def _validate_timestamp_valid(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """タイムスタンプが有効かチェック"""
        if 'timestamp' in record and record['timestamp'] is not None:
            try:
                if isinstance(record['timestamp'], str):
                    datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                elif isinstance(record['timestamp'], datetime):
                    pass  # 既にdatetimeオブジェクト
                else:
                    return False, f"Invalid timestamp format: {type(record['timestamp'])}"
            except (ValueError, TypeError) as e:
                return False, f"Invalid timestamp: {e}"
        
        return True, "Timestamp is valid"
    
    def _validate_timestamp_sequential(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """タイムスタンプが時系列順かチェック（単一レコードでは常にTrue）"""
        return True, "Timestamp sequential check requires context"
    
    def _validate_price_reasonable(self, record: Dict[str, Any]) -> Tuple[bool, str]:
        """価格が合理的な範囲内かチェック"""
        price_fields = ['open', 'high', 'low', 'close']
        max_reasonable_price = 1000000  # 100万円
        min_reasonable_price = 0.01  # 1円
        
        for field in price_fields:
            if field in record and record[field] is not None:
                price = record[field]
                if price > max_reasonable_price:
                    return False, f"{field} price ({price}) seems unreasonably high"
                if price < min_reasonable_price:
                    return False, f"{field} price ({price}) seems unreasonably low"
        
        return True, "Prices are within reasonable range"
    
    def _validate_with_previous(
        self,
        record: Dict[str, Any],
        previous_record: Dict[str, Any]
    ) -> ValidationResult:
        """前のレコードとの比較検証"""
        errors = []
        warnings = []
        
        # タイムスタンプの時系列チェック
        if 'timestamp' in record and 'timestamp' in previous_record:
            try:
                current_ts = self._parse_timestamp(record['timestamp'])
                previous_ts = self._parse_timestamp(previous_record['timestamp'])
                
                if current_ts <= previous_ts:
                    errors.append(f"Timestamp must be after previous record: {current_ts} <= {previous_ts}")
                    
            except Exception as e:
                warnings.append(f"Could not compare timestamps: {e}")
        
        # 価格の急激な変動チェック
        if 'close' in record and 'close' in previous_record:
            try:
                current_close = record['close']
                previous_close = previous_record['close']
                
                if previous_close > 0:
                    change_ratio = abs(current_close - previous_close) / previous_close
                    if change_ratio > 0.5:  # 50%以上の変動
                        warnings.append(f"Large price change detected: {change_ratio:.2%}")
                        
            except Exception as e:
                warnings.append(f"Could not compare prices: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=1.0 if len(errors) == 0 else 0.5,
            validated_at=datetime.now()
        )
    
    def _validate_with_next(
        self,
        record: Dict[str, Any],
        next_record: Dict[str, Any]
    ) -> ValidationResult:
        """次のレコードとの比較検証"""
        errors = []
        warnings = []
        
        # タイムスタンプの時系列チェック
        if 'timestamp' in record and 'timestamp' in next_record:
            try:
                current_ts = self._parse_timestamp(record['timestamp'])
                next_ts = self._parse_timestamp(next_record['timestamp'])
                
                if current_ts >= next_ts:
                    errors.append(f"Timestamp must be before next record: {current_ts} >= {next_ts}")
                    
            except Exception as e:
                warnings.append(f"Could not compare timestamps: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            quality_score=1.0 if len(errors) == 0 else 0.5,
            validated_at=datetime.now()
        )
    
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """タイムスタンプをパース"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, any]:
        """
        検証結果のサマリーを取得
        
        Args:
            results: 検証結果のリスト
            
        Returns:
            サマリー情報
        """
        total_records = len(results)
        valid_records = sum(1 for r in results if r.is_valid)
        invalid_records = total_records - valid_records
        
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        avg_quality_score = sum(r.quality_score for r in results) / total_records if total_records > 0 else 0.0
        
        return {
            "total_records": total_records,
            "valid_records": valid_records,
            "invalid_records": invalid_records,
            "validation_rate": valid_records / total_records if total_records > 0 else 0.0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "average_quality_score": avg_quality_score,
        }
