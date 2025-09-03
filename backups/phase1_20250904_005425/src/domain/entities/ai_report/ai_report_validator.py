"""
AIレポートバリデーター
AIReportのバリデーション機能を提供
"""

from decimal import Decimal
from typing import List, Any
from dataclasses import dataclass

from .ai_report import AIReport, ReportType
from .usd_jpy_prediction import USDJPYPrediction


@dataclass
class ValidationError:
    """バリデーションエラー"""
    field: str
    message: str
    value: Any = None


class AIReportValidator:
    """AIレポートバリデーター"""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def validate(self, report: AIReport) -> bool:
        """
        AIレポートの完全なバリデーション
        
        Args:
            report: バリデーション対象のAIReport
            
        Returns:
            bool: バリデーション成功時True
        """
        self.errors.clear()
        
        # 必須フィールドの検証
        self._validate_required_fields(report)
        
        # データ型の検証
        self._validate_data_types(report)
        
        # 値の範囲検証
        self._validate_value_ranges(report)
        
        # ビジネスルールの検証
        self._validate_business_rules(report)
        
        return len(self.errors) == 0
    
    def _validate_required_fields(self, report: AIReport) -> None:
        """必須フィールドの検証"""
        if not report.report_content:
            self.errors.append(
                ValidationError("report_content", "report_contentは必須です")
            )
        
        if not report.summary:
            self.errors.append(
                ValidationError("summary", "summaryは必須です")
            )
    
    def _validate_data_types(self, report: AIReport) -> None:
        """データ型の検証"""
        if not isinstance(report.report_type, ReportType):
            self.errors.append(
                ValidationError(
                    "report_type", 
                    "report_typeはReportType列挙型である必要があります",
                    type(report.report_type)
                )
            )
        
        if not isinstance(report.report_content, str):
            self.errors.append(
                ValidationError(
                    "report_content", 
                    "report_contentは文字列である必要があります",
                    type(report.report_content)
                )
            )
        
        if not isinstance(report.summary, str):
            self.errors.append(
                ValidationError(
                    "summary", 
                    "summaryは文字列である必要があります",
                    type(report.summary)
                )
            )
        
        if not isinstance(report.confidence_score, Decimal):
            self.errors.append(
                ValidationError(
                    "confidence_score", 
                    "confidence_scoreはDecimalである必要があります",
                    type(report.confidence_score)
                )
            )
        
        if report.usd_jpy_prediction is not None:
            if not isinstance(report.usd_jpy_prediction, USDJPYPrediction):
                self.errors.append(
                    ValidationError(
                        "usd_jpy_prediction", 
                        "usd_jpy_predictionはUSDJPYPredictionである必要があります",
                        type(report.usd_jpy_prediction)
                    )
                )
    
    def _validate_value_ranges(self, report: AIReport) -> None:
        """値の範囲検証"""
        # 信頼度スコアの範囲
        if report.confidence_score < 0 or report.confidence_score > 1:
            self.errors.append(
                ValidationError(
                    "confidence_score", 
                    "confidence_scoreは0から1の範囲である必要があります",
                    report.confidence_score
                )
            )
        
        # レポート内容の長さ
        if len(report.report_content) < 10:
            self.errors.append(
                ValidationError(
                    "report_content", 
                    "report_contentは最低10文字である必要があります",
                    len(report.report_content)
                )
            )
        
        if len(report.report_content) > 10000:
            self.errors.append(
                ValidationError(
                    "report_content", 
                    "report_contentは最大10000文字である必要があります",
                    len(report.report_content)
                )
            )
        
        # サマリーの長さ
        if len(report.summary) < 5:
            self.errors.append(
                ValidationError(
                    "summary", 
                    "summaryは最低5文字である必要があります",
                    len(report.summary)
                )
            )
        
        if len(report.summary) > 500:
            self.errors.append(
                ValidationError(
                    "summary", 
                    "summaryは最大500文字である必要があります",
                    len(report.summary)
                )
            )
    
    def _validate_business_rules(self, report: AIReport) -> None:
        """ビジネスルールの検証"""
        # 高信頼度レポートには予測データが必要
        if report.is_high_confidence and not report.has_prediction:
            self.errors.append(
                ValidationError(
                    "usd_jpy_prediction", 
                    "高信頼度レポートにはドル円予測データが必要です"
                )
            )
        
        # 予測データがある場合は信頼度スコアが整合している必要がある
        if report.has_prediction:
            prediction_confidence = report.usd_jpy_prediction.confidence_score
            if abs(report.confidence_score - prediction_confidence) > 0.3:
                self.errors.append(
                    ValidationError(
                        "confidence_score", 
                        "レポートの信頼度と予測の信頼度が大きく異なります",
                        f"report: {report.confidence_score}, "
                        f"prediction: {prediction_confidence}"
                    )
                )
    
    def validate_for_notification(self, report: AIReport) -> bool:
        """
        通知対象としてのバリデーション
        
        Args:
            report: バリデーション対象のAIReport
            
        Returns:
            bool: 通知対象として妥当な場合True
        """
        self.errors.clear()
        
        # 基本バリデーション
        if not self.validate(report):
            return False
        
        # 通知条件の検証
        if not report.is_high_confidence:
            self.errors.append(
                ValidationError(
                    "confidence_score",
                    "通知対象は高信頼度である必要があります",
                    report.confidence_score
                )
            )
        
        if not report.has_prediction:
            self.errors.append(
                ValidationError(
                    "usd_jpy_prediction",
                    "通知対象にはドル円予測データが必要です"
                )
            )
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[ValidationError]:
        """バリデーションエラーを取得"""
        return self.errors.copy()
    
    def get_error_messages(self) -> List[str]:
        """バリデーションエラーメッセージを取得"""
        return [f"{error.field}: {error.message}" for error in self.errors]
    
    def has_errors(self) -> bool:
        """エラーがあるかどうか"""
        return len(self.errors) > 0
