"""
OpenAI API Client
OpenAI APIクライアント

設計書参照:
- インフラ・プラグイン設計_20250809.md

OpenAI ChatGPT APIを使用してAI分析レポートを生成するクライアント
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ...utils.logging_config import get_infrastructure_logger
from .base_client import APIError, BaseAPIClient

logger = get_infrastructure_logger()


class OpenAIClient(BaseAPIClient):
    """
    OpenAI APIクライアント

    責任:
    - ChatGPT APIとの通信
    - 市場分析レポートの生成
    - トークン使用量の管理
    - コスト最適化

    API仕様:
    - GPT-4, GPT-3.5-turbo対応
    - レート制限: モデルとプランに依存
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        初期化

        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル
            max_tokens: 最大トークン数
            temperature: 創造性パラメータ
            **kwargs: BaseAPIClientの引数
        """
        super().__init__(
            base_url="https://api.openai.com",
            api_key=api_key,
            rate_limit_calls=3000,  # Free tier: 3 RPM
            rate_limit_period=60,
            **kwargs,
        )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        logger.info(f"Initialized OpenAI client with model: {model}")

    def _get_auth_params(self) -> Dict[str, str]:
        """
        認証パラメータを取得
        OpenAIはヘッダーでの認証を使用

        Returns:
            Dict[str, str]: 空の辞書（ヘッダーで認証）
        """
        return {}

    def _get_default_headers(self) -> Dict[str, str]:
        """
        デフォルトヘッダーを取得（認証を含む）

        Returns:
            Dict[str, str]: ヘッダー辞書
        """
        headers = super()._get_default_headers()
        headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def generate_market_analysis(
        self,
        market_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
        currency_pairs: Optional[List[str]] = None,
        custom_prompt: Optional[str] = None,
        report_type: str = "daily_summary",
    ) -> Dict[str, Any]:
        """
        市場分析レポートを生成

        Args:
            market_data: 市場データ
            technical_data: テクニカル分析データ
            currency_pairs: 対象通貨ペア
            custom_prompt: カスタムプロンプト
            report_type: レポート種別

        Returns:
            Dict[str, Any]: 生成されたレポートデータ
        """
        try:
            logger.debug(f"Generating {report_type} market analysis")

            # プロンプトを構築
            prompt = self._build_analysis_prompt(
                market_data=market_data,
                technical_data=technical_data,
                currency_pairs=currency_pairs,
                custom_prompt=custom_prompt,
                report_type=report_type,
            )

            # ChatGPT APIを呼び出し
            response = await self._call_chat_completion(prompt)

            # レスポンスを解析
            analysis = self._parse_analysis_response(response, report_type)

            logger.info(f"Generated {report_type} analysis successfully")
            return analysis

        except Exception as e:
            logger.error(f"Failed to generate market analysis: {str(e)}")
            raise

    async def _call_chat_completion(
        self, prompt: str, system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ChatGPT Completion APIを呼び出し

        Args:
            prompt: ユーザープロンプト
            system_message: システムメッセージ

        Returns:
            Dict[str, Any]: APIレスポンス
        """
        messages = []

        # システムメッセージ
        if system_message:
            messages.append({"role": "system", "content": system_message})
        else:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "あなたは為替市場の専門アナリストです。"
                        "提供されたデータを基に、正確で洞察に富んだ市場分析を行ってください。"
                        "分析は客観的で、リスクと機会の両方を含めてください。"
                    ),
                }
            )

        # ユーザーメッセージ
        messages.append({"role": "user", "content": prompt})

        # APIリクエストデータ
        request_data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        }

        # API呼び出し
        response = await self.post("/v1/chat/completions", data=request_data)

        return response

    def _build_analysis_prompt(
        self,
        market_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]],
        currency_pairs: Optional[List[str]],
        custom_prompt: Optional[str],
        report_type: str,
    ) -> str:
        """
        分析用プロンプトを構築

        Args:
            market_data: 市場データ
            technical_data: テクニカルデータ
            currency_pairs: 通貨ペア
            custom_prompt: カスタムプロンプト
            report_type: レポート種別

        Returns:
            str: 構築されたプロンプト
        """
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._get_default_prompt(report_type)

        # 市場データの追加
        if market_data:
            prompt += "\n\n## 市場データ\n"
            for pair, data in market_data.items():
                if isinstance(data, dict) and "latest_rate" in data:
                    rate_info = data["latest_rate"]
                    prompt += f"- {pair}: {rate_info.rate}"
                    if hasattr(rate_info, "timestamp"):
                        prompt += f" (時刻: {rate_info.timestamp})"
                    prompt += "\n"

        # テクニカルデータの追加
        if technical_data:
            prompt += "\n\n## テクニカル分析データ\n"
            for indicator, value in technical_data.items():
                prompt += f"- {indicator}: {value}\n"

        # 対象通貨ペアの追加
        if currency_pairs:
            prompt += f"\n\n## 分析対象通貨ペア\n{', '.join(currency_pairs)}"

        prompt += f"\n\n現在の時刻: {datetime.utcnow().isoformat()}"

        return prompt

    def _get_default_prompt(self, report_type: str) -> str:
        """
        レポート種別に応じたデフォルトプロンプトを取得

        Args:
            report_type: レポート種別

        Returns:
            str: デフォルトプロンプト
        """
        prompts = {
            "daily_summary": (
                "以下のデータを基に日次市場サマリーレポートを作成してください。\n"
                "主要な価格変動、ボラティリティ、マーケットトレンドを分析し、"
                "明日の見通しを含めてください。"
            ),
            "weekly_analysis": (
                "以下のデータを基に週次分析レポートを作成してください。\n"
                "週間の価格パフォーマンス、重要なニュースイベントの影響、"
                "来週の展望を含めてください。"
            ),
            "technical_analysis": (
                "以下のデータを基にテクニカル分析レポートを作成してください。\n"
                "主要なテクニカル指標、サポート・レジスタンスレベル、"
                "チャートパターンを分析してください。"
            ),
            "fundamental_analysis": (
                "以下のデータを基にファンダメンタル分析レポートを作成してください。\n" "経済指標、中央銀行政策、地政学的要因を分析してください。"
            ),
            "market_outlook": (
                "以下のデータを基にマーケット展望レポートを作成してください。\n" "中期的なトレンド、リスク要因、投資機会を分析してください。"
            ),
        }

        return prompts.get(report_type, prompts["daily_summary"])

    def _parse_analysis_response(
        self, response: Dict[str, Any], report_type: str
    ) -> Dict[str, Any]:
        """
        分析レスポンスを解析

        Args:
            response: OpenAI APIレスポンス
            report_type: レポート種別

        Returns:
            Dict[str, Any]: 解析されたレポートデータ
        """
        try:
            # レスポンスから生成されたテキストを抽出
            choices = response.get("choices", [])
            if not choices:
                raise APIError("No choices in OpenAI response")

            generated_text = choices[0].get("message", {}).get("content", "")

            if not generated_text:
                raise APIError("No content in OpenAI response")

            # 使用量情報を取得
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # 構造化されたレポートデータを作成
            analysis = {
                "title": self._extract_title(generated_text, report_type),
                "content": generated_text,
                "market_summary": self._extract_market_summary(generated_text),
                "technical_analysis": self._extract_technical_analysis(generated_text),
                "fundamental_analysis": self._extract_fundamental_analysis(
                    generated_text
                ),
                "recommendations": self._extract_recommendations(generated_text),
                "confidence_score": self._calculate_confidence_score(generated_text),
                "model": self.model,
                "generation_time": datetime.utcnow().isoformat(),
                "token_usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
            }

            return analysis

        except Exception as e:
            logger.error(f"Failed to parse analysis response: {str(e)}")
            raise APIError(f"Failed to parse analysis response: {str(e)}")

    def _extract_title(self, text: str, report_type: str) -> str:
        """タイトルを抽出"""
        # 簡単な実装：最初の行または生成されたタイトル
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                return line[:100]  # 最大100文字

        # フォールバック
        return f"{report_type.replace('_', ' ').title()} - {datetime.now().strftime('%Y-%m-%d')}"

    def _extract_market_summary(self, text: str) -> str:
        """市場サマリーを抽出"""
        # 簡単な実装：最初の段落または最初の200文字
        paragraphs = text.split("\n\n")
        if paragraphs:
            return paragraphs[0][:500]
        return text[:500]

    def _extract_technical_analysis(self, text: str) -> Optional[str]:
        """テクニカル分析部分を抽出"""
        # テクニカル関連のキーワードを含む段落を探す
        technical_keywords = [
            "テクニカル",
            "移動平均",
            "RSI",
            "MACD",
            "サポート",
            "レジスタンス",
        ]

        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            if any(keyword in paragraph for keyword in technical_keywords):
                return paragraph[:500]

        return None

    def _extract_fundamental_analysis(self, text: str) -> Optional[str]:
        """ファンダメンタル分析部分を抽出"""
        # ファンダメンタル関連のキーワードを含む段落を探す
        fundamental_keywords = [
            "ファンダメンタル",
            "経済指標",
            "中央銀行",
            "金利",
            "インフレ",
            "GDP",
        ]

        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            if any(keyword in paragraph for keyword in fundamental_keywords):
                return paragraph[:500]

        return None

    def _extract_recommendations(self, text: str) -> Optional[str]:
        """推奨事項を抽出"""
        # 推奨関連のキーワードを含む段落を探す
        recommendation_keywords = ["推奨", "提案", "戦略", "アドバイス", "展望"]

        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            if any(keyword in paragraph for keyword in recommendation_keywords):
                return paragraph[:500]

        return None

    def _calculate_confidence_score(self, text: str) -> float:
        """信頼度スコアを計算"""
        # 簡単な実装：テキストの長さと品質に基づく
        length_score = min(len(text) / 1000, 1.0)  # 1000文字で最大スコア

        # 専門用語の数に基づくスコア
        technical_terms = [
            "分析",
            "トレンド",
            "サポート",
            "レジスタンス",
            "ボラティリティ",
            "流動性",
            "スプレッド",
            "経済指標",
            "中央銀行",
        ]

        term_count = sum(1 for term in technical_terms if term in text)
        term_score = min(term_count / len(technical_terms), 1.0)

        # 総合スコア
        confidence = length_score * 0.6 + term_score * 0.4

        return round(confidence, 2)

    async def test_connection(self) -> bool:
        """
        API接続をテスト

        Returns:
            bool: 接続成功時True
        """
        try:
            # 簡単なテストリクエスト
            test_prompt = "現在の為替市場について一言でコメントしてください。"
            response = await self._call_chat_completion(test_prompt)

            if response.get("choices"):
                logger.info("OpenAI connection test successful")
                return True
            else:
                logger.error("OpenAI connection test failed: No choices in response")
                return False

        except Exception as e:
            logger.error(f"OpenAI connection test failed: {str(e)}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """
        使用中のモデル情報を取得

        Returns:
            Dict[str, Any]: モデル情報
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "rate_limit": {
                "calls": self.rate_limit_calls,
                "period": self.rate_limit_period,
            },
        }
