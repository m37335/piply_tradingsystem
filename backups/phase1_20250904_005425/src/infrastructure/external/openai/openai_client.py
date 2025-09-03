"""
OpenAIクライアント
OpenAI APIを使用したAI分析機能を提供
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .openai_error_handler import OpenAIErrorHandler
from .openai_prompt_manager import OpenAIPromptManager


class OpenAIClient:
    """OpenAI APIクライアント"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        max_tokens: int = 2000,
        temperature: float = 0.3,
        timeout: int = 60,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(self.__class__.__name__)

        # API設定
        self.base_url = "https://api.openai.com/v1"
        self.chat_endpoint = f"{self.base_url}/chat/completions"

        # コンポーネント
        self.prompt_manager = OpenAIPromptManager()
        self.error_handler = OpenAIErrorHandler()

        # セッション管理
        self._session: Optional[ClientSession] = None
        self._request_count = 0
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        await self.disconnect()

    async def connect(self) -> bool:
        """HTTPセッションを開始"""
        try:
            timeout = ClientTimeout(total=self.timeout)
            self._session = ClientSession(timeout=timeout)
            self.logger.info("OpenAI client session started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start OpenAI session: {e}")
            return False

    async def disconnect(self) -> None:
        """HTTPセッションを終了"""
        try:
            if self._session:
                await self._session.close()
                self._session = None
                self.logger.info("OpenAI client session closed")
        except Exception as e:
            self.logger.error(f"Error closing OpenAI session: {e}")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        """
        OpenAI APIを使用してレスポンスを生成

        Args:
            messages: メッセージのリスト
            system_prompt: システムプロンプト
            max_tokens: 最大トークン数
            temperature: 温度パラメータ

        Returns:
            Optional[str]: 生成されたレスポンス
        """
        if not self._session:
            self.logger.error("OpenAI session not initialized")
            return None

        # パラメータの設定
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature

        # システムプロンプトを追加
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        # ペイロードの構築
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # GPT-4o-mini以降でresponse_formatをサポート
        if self.model in ["gpt-4o", "gpt-4o-mini"]:
            payload["response_format"] = {"type": "json_object"}

        # リクエストの実行
        for attempt in range(self.max_retries):
            try:
                async with self._session.post(
                    self.chat_endpoint,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._request_count += 1

                        # トークン使用量を更新
                        usage = data.get("usage", {})
                        self._token_usage["prompt_tokens"] += usage.get(
                            "prompt_tokens", 0
                        )
                        self._token_usage["completion_tokens"] += usage.get(
                            "completion_tokens", 0
                        )
                        self._token_usage["total_tokens"] += usage.get(
                            "total_tokens", 0
                        )

                        # レスポンスを取得
                        choices = data.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            self.logger.info(
                                f"Generated response with {len(content)} characters"
                            )
                            return content
                        else:
                            self.logger.error("No choices in OpenAI response")
                            return None

                    elif response.status == 429:
                        # レート制限
                        retry_after = int(
                            response.headers.get("Retry-After", self.retry_delay)
                        )
                        self.logger.warning(
                            f"Rate limited, retrying after {retry_after} seconds"
                        )
                        await asyncio.sleep(retry_after)
                        continue

                    elif response.status == 401:
                        # 認証エラー
                        self.logger.error("OpenAI API authentication failed")
                        return None

                    elif response.status == 400:
                        # リクエストエラー
                        error_data = await response.json()
                        error_message = error_data.get("error", {}).get(
                            "message", "Unknown error"
                        )
                        self.logger.error(f"OpenAI API request error: {error_message}")
                        return None

                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"OpenAI API error: {response.status} - {error_text}"
                        )
                        return None

            except ClientError as e:
                self.logger.error(f"Network error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return None

        return None

    async def analyze_economic_event(
        self, event_data: Dict[str, Any], analysis_type: str = "pre_event"
    ) -> Optional[Dict[str, Any]]:
        """
        経済イベントのAI分析を実行

        Args:
            event_data: イベントデータ
            analysis_type: 分析タイプ（pre_event, post_event, forecast_change）

        Returns:
            Optional[Dict[str, Any]]: 分析結果
        """
        try:
            # プロンプトを生成
            prompt = self.prompt_manager.create_economic_analysis_prompt(
                event_data, analysis_type
            )

            # システムプロンプト
            system_prompt = self.prompt_manager.get_system_prompt(analysis_type)

            # API呼び出し
            response = await self.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
            )

            if not response:
                return None

            # レスポンスをパース
            try:
                # JSONパースを試行
                result = json.loads(response)
                self.logger.info(f"Successfully analyzed {analysis_type} event")
                return result
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse AI response: {e}")
                self.logger.error(f"Raw response: {response}")

                # JSONの修復を試行
                try:
                    cleaned_response = self._clean_json_response(response)
                    result = json.loads(cleaned_response)
                    self.logger.info(
                        f"Successfully parsed cleaned JSON for {analysis_type} event"
                    )
                    return result
                except Exception as clean_error:
                    self.logger.error(
                        f"Failed to clean and parse response: {clean_error}"
                    )
                    return None

        except Exception as e:
            self.logger.error(f"Error analyzing economic event: {e}")
            return None

    async def generate_usd_jpy_prediction(
        self,
        event_data: Dict[str, Any],
        market_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        USD/JPY予測を生成

        Args:
            event_data: イベントデータ
            market_context: 市場コンテキスト

        Returns:
            Optional[Dict[str, Any]]: 予測結果
        """
        try:
            # プロンプトを生成
            prompt = self.prompt_manager.create_usd_jpy_prediction_prompt(
                event_data, market_context
            )

            # システムプロンプト
            system_prompt = self.prompt_manager.get_usd_jpy_system_prompt()

            # API呼び出し
            response = await self.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                temperature=0.2,  # 予測では低い温度を使用
            )

            if not response:
                return None

            # レスポンスをパース
            try:
                result = json.loads(response)
                self.logger.info("Successfully generated USD/JPY prediction")
                return result
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse prediction response: {e}")
                self.logger.error(f"Raw response: {response}")

                # JSONの修復を試行
                try:
                    cleaned_response = self._clean_json_response(response)
                    result = json.loads(cleaned_response)
                    self.logger.info(
                        "Successfully parsed cleaned JSON for USD/JPY prediction"
                    )
                    return result
                except Exception as clean_error:
                    self.logger.error(
                        f"Failed to clean and parse prediction response: {clean_error}"
                    )
                    return None

        except Exception as e:
            self.logger.error(f"Error generating USD/JPY prediction: {e}")
            return None

    async def generate_ai_report(
        self,
        event_data: Dict[str, Any],
        prediction_data: Optional[Dict[str, Any]] = None,
        report_type: str = "pre_event",
    ) -> Optional[Dict[str, Any]]:
        """
        AIレポートを生成

        Args:
            event_data: イベントデータ
            prediction_data: 予測データ
            report_type: レポートタイプ

        Returns:
            Optional[Dict[str, Any]]: レポートデータ
        """
        try:
            # プロンプトを生成
            prompt = self.prompt_manager.create_report_generation_prompt(
                event_data, prediction_data, report_type
            )

            # システムプロンプト
            system_prompt = self.prompt_manager.get_report_system_prompt()

            # API呼び出し
            response = await self.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt,
                max_tokens=3000,  # レポートは長めに
            )

            if not response:
                return None

            # レスポンスをパース
            try:
                result = json.loads(response)
                self.logger.info(f"Successfully generated {report_type} report")
                return result
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse report response: {e}")
                return None

        except Exception as e:
            self.logger.error(f"Error generating AI report: {e}")
            return None

    async def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功時True
        """
        try:
            if not self._session:
                return False

            # 簡単なテストプロンプト
            test_prompt = "Hello, this is a test message. Please respond with 'OK'."

            response = await self.generate_response(
                messages=[{"role": "user", "content": test_prompt}], max_tokens=10
            )

            return response is not None and "OK" in response

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        使用統計を取得

        Returns:
            Dict[str, Any]: 使用統計
        """
        return {
            "request_count": self._request_count,
            "token_usage": self._token_usage.copy(),
            "model": self.model,
            "estimated_cost": self._calculate_estimated_cost(),
        }

    def _calculate_estimated_cost(self) -> float:
        """推定コストを計算"""
        # GPT-4の料金（概算）
        prompt_cost_per_1k = 0.03  # $0.03 per 1K prompt tokens
        completion_cost_per_1k = 0.06  # $0.06 per 1K completion tokens

        prompt_cost = (self._token_usage["prompt_tokens"] / 1000) * prompt_cost_per_1k
        completion_cost = (
            self._token_usage["completion_tokens"] / 1000
        ) * completion_cost_per_1k

        return prompt_cost + completion_cost

    def reset_usage_stats(self) -> None:
        """使用統計をリセット"""
        self._request_count = 0
        self._token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
        self.logger.info("OpenAI usage stats reset")

    def _clean_json_response(self, response: str) -> str:
        """JSONレスポンスを清掃"""
        try:
            # 一般的なJSON修復処理
            cleaned = response.strip()

            # 文字列の終端がない場合の修復
            if cleaned.count('"') % 2 == 1:
                # 奇数個の引用符がある場合、最後に引用符を追加
                cleaned += '"'

            # 不完全な配列の修復
            if cleaned.count("[") > cleaned.count("]"):
                cleaned += "]" * (cleaned.count("[") - cleaned.count("]"))

            # 不完全なオブジェクトの修復
            if cleaned.count("{") > cleaned.count("}"):
                cleaned += "}" * (cleaned.count("{") - cleaned.count("}"))

            # 末尾のカンマを削除
            import re

            cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

            return cleaned
        except Exception as e:
            self.logger.error(f"Error cleaning JSON response: {e}")
            return response
