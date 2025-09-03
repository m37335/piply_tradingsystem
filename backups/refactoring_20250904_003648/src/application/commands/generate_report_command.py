"""
Generate Report Command
AI分析レポート生成コマンド

設計書参照:
- アプリケーション層設計_20250809.md

ChatGPT APIを使用してAI分析レポートを生成するコマンド
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ...utils.logging_config import get_application_logger
from .base import BaseCommand

logger = get_application_logger()


class ReportType(Enum):
    """レポート種別"""

    DAILY_SUMMARY = "daily_summary"  # 日次サマリー
    WEEKLY_ANALYSIS = "weekly_analysis"  # 週次分析
    MARKET_OUTLOOK = "market_outlook"  # マーケット展望
    TECHNICAL_ANALYSIS = "technical_analysis"  # テクニカル分析
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"  # ファンダメンタル分析
    CUSTOM = "custom"  # カスタムレポート


class ReportFormat(Enum):
    """レポート形式"""

    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PLAIN_TEXT = "plain_text"


class ReportLanguage(Enum):
    """レポート言語"""

    JAPANESE = "ja"
    ENGLISH = "en"


@dataclass
class GenerateReportCommand(BaseCommand):
    """
    AI分析レポート生成コマンド

    責任:
    - AI分析レポートの生成指示
    - レポートパラメータの管理とバリデーション
    - カスタムプロンプトの処理
    """

    # 必須フィールド
    report_date: date = None
    report_type: ReportType = ReportType.DAILY_SUMMARY
    currency_pairs: List[str] = None

    # オプションフィールド
    custom_prompt: Optional[str] = None
    force_regenerate: bool = False
    language: ReportLanguage = ReportLanguage.JAPANESE
    format: ReportFormat = ReportFormat.MARKDOWN
    include_charts: bool = True
    include_technical_indicators: bool = True
    analysis_period_days: int = 7
    temperature: float = 0.7  # ChatGPT temperature setting

    def __post_init__(self) -> None:
        """
        初期化後処理
        バリデーションとデフォルト値設定
        """
        if self.report_date is None:
            self.report_date = date.today()

        if self.currency_pairs is None:
            self.currency_pairs = []

        super().__post_init__()
        self.validate()

        # メタデータに追加情報を設定
        self.add_metadata("report_type", self.report_type.value)
        self.add_metadata("currency_pairs_count", len(self.currency_pairs))
        self.add_metadata("report_language", self.language.value)
        self.add_metadata("analysis_period_days", self.analysis_period_days)

    def validate(self) -> None:
        """
        コマンドのバリデーション

        Raises:
            ValueError: バリデーションエラー
        """
        super().validate()

        if not self.currency_pairs:
            raise ValueError("Currency pairs are required")

        if len(self.currency_pairs) > 10:
            raise ValueError("Too many currency pairs (max: 10)")

        # 通貨ペア形式の検証
        for pair in self.currency_pairs:
            if not isinstance(pair, str):
                raise ValueError(f"Currency pair must be string: {pair}")

            # USD/JPY or USDJPY 形式をサポート
            normalized = self._normalize_currency_pair(pair)
            if not normalized:
                raise ValueError(f"Invalid currency pair format: {pair}")

        # カスタムプロンプトの検証
        if self.custom_prompt and len(self.custom_prompt) > 5000:
            raise ValueError("Custom prompt too long (max: 5000 characters)")

        # レポート日付の検証
        if self.report_date > date.today():
            raise ValueError("Report date cannot be in the future")

        # 分析期間の検証
        if self.analysis_period_days <= 0 or self.analysis_period_days > 365:
            raise ValueError("Analysis period must be between 1 and 365 days")

        # Temperature値の検証
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

    def _normalize_currency_pair(self, pair: str) -> Optional[str]:
        """
        通貨ペアを正規化

        Args:
            pair: 通貨ペア文字列

        Returns:
            Optional[str]: 正規化された通貨ペア（USD/JPY形式）
        """
        try:
            if "/" in pair:
                parts = pair.split("/")
                if len(parts) == 2 and len(parts[0]) == 3 and len(parts[1]) == 3:
                    return f"{parts[0].upper()}/{parts[1].upper()}"
            else:
                if len(pair) == 6:
                    base = pair[:3].upper()
                    quote = pair[3:].upper()
                    return f"{base}/{quote}"
        except Exception:
            pass
        return None

    def get_normalized_currency_pairs(self) -> List[str]:
        """
        正規化された通貨ペアを取得

        Returns:
            List[str]: USD/JPY形式に正規化された通貨ペアリスト
        """
        return [self._normalize_currency_pair(pair) for pair in self.currency_pairs]

    def get_prompt_template(self) -> str:
        """
        レポートタイプに応じたプロンプトテンプレートを取得

        Returns:
            str: プロンプトテンプレート
        """
        templates = {
            ReportType.DAILY_SUMMARY: (
                "以下の通貨ペアについて、{report_date}の日次サマリーレポートを作成してください。"
                "主要な価格変動、ボラティリティ、マーケットトレンドを分析し、"
                "明日の見通しを含めてください。"
            ),
            ReportType.WEEKLY_ANALYSIS: (
                "以下の通貨ペアについて、{report_date}週の週次分析レポートを作成してください。"
                "週間の価格パフォーマンス、重要なニュースイベントの影響、"
                "来週の展望を含めてください。"
            ),
            ReportType.MARKET_OUTLOOK: (
                "以下の通貨ペアについて、{report_date}時点でのマーケット展望レポートを作成してください。"
                "中期的なトレンド、リスク要因、投資機会を分析してください。"
            ),
            ReportType.TECHNICAL_ANALYSIS: (
                "以下の通貨ペアについて、{report_date}時点でのテクニカル分析レポートを作成してください。"
                "主要なテクニカル指標、サポート・レジスタンスレベル、"
                "チャートパターンを分析してください。"
            ),
            ReportType.FUNDAMENTAL_ANALYSIS: (
                "以下の通貨ペアについて、{report_date}時点でのファンダメンタル分析レポートを作成してください。"
                "経済指標、中央銀行政策、地政学的要因を分析してください。"
            ),
            ReportType.CUSTOM: ("以下の通貨ペアについて、カスタム分析レポートを作成してください。"),
        }

        template = templates.get(self.report_type, templates[ReportType.DAILY_SUMMARY])
        return template.format(report_date=self.report_date.isoformat())

    def build_ai_prompt(self) -> str:
        """
        AI用の完全なプロンプトを構築

        Returns:
            str: AI用プロンプト
        """
        # 基本プロンプト
        if self.custom_prompt:
            prompt = self.custom_prompt
        else:
            prompt = self.get_prompt_template()

        # 通貨ペア情報を追加
        pairs_str = ", ".join(self.get_normalized_currency_pairs())
        prompt += f"\n\n対象通貨ペア: {pairs_str}"

        # 分析期間を追加
        prompt += f"\n分析期間: 過去{self.analysis_period_days}日間"

        # 言語指定
        if self.language == ReportLanguage.JAPANESE:
            prompt += "\n\n日本語で回答してください。"
        else:
            prompt += "\n\nPlease respond in English."

        # フォーマット指定
        if self.format == ReportFormat.MARKDOWN:
            prompt += "\nMarkdown形式で整理して出力してください。"
        elif self.format == ReportFormat.HTML:
            prompt += "\nHTML形式で整理して出力してください。"
        elif self.format == ReportFormat.JSON:
            prompt += "\nJSON形式で構造化して出力してください。"

        # テクニカル指標の含有指定
        if self.include_technical_indicators:
            prompt += "\n主要なテクニカル指標（移動平均、RSI、MACD等）を含めてください。"

        return prompt

    def get_estimated_tokens(self) -> int:
        """
        推定トークン数を計算

        Returns:
            int: 推定トークン数
        """
        prompt = self.build_ai_prompt()
        # 日本語は約2文字=1トークン、英語は約4文字=1トークン
        if self.language == ReportLanguage.JAPANESE:
            return len(prompt) // 2
        else:
            return len(prompt) // 4

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換

        Returns:
            Dict[str, Any]: コマンドの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "report_date": self.report_date.isoformat(),
                "report_type": self.report_type.value,
                "currency_pairs": self.currency_pairs,
                "normalized_pairs": self.get_normalized_currency_pairs(),
                "custom_prompt": self.custom_prompt,
                "force_regenerate": self.force_regenerate,
                "language": self.language.value,
                "format": self.format.value,
                "include_charts": self.include_charts,
                "include_technical_indicators": self.include_technical_indicators,
                "analysis_period_days": self.analysis_period_days,
                "temperature": self.temperature,
                "estimated_tokens": self.get_estimated_tokens(),
            }
        )
        return base_dict

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: コマンドの文字列表現
        """
        pairs_str = ", ".join(self.currency_pairs[:2])
        if len(self.currency_pairs) > 2:
            pairs_str += f" (+{len(self.currency_pairs) - 2} more)"

        return (
            f"GenerateReportCommand("
            f"type={self.report_type.value}, "
            f"date={self.report_date}, "
            f"pairs=[{pairs_str}])"
        )
