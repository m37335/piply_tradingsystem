"""
USD/JPY予測データ解析器

AI応答からドル円予測データを解析する
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional


class USDJPYPredictionParser:
    """
    USD/JPY予測データ解析器
    
    AI応答からドル円予測データを解析する
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 統計情報
        self._parse_count = 0
        self._successful_parses = 0

    async def parse_prediction_data(self, ai_response: str) -> Dict[str, Any]:
        """
        AI応答からドル円予測データを解析
        
        Args:
            ai_response: AIからの応答テキスト
            
        Returns:
            Dict[str, Any]: 解析された予測データ
        """
        try:
            self._parse_count += 1
            
            # JSONの抽出
            json_data = await self._extract_json_from_response(ai_response)
            
            if not json_data:
                self.logger.warning("JSONデータが見つかりませんでした")
                return self._get_default_prediction_data()
            
            # データの検証と正規化
            validated_data = await self._validate_and_normalize_data(json_data)
            
            self._successful_parses += 1
            
            return validated_data

        except Exception as e:
            self.logger.error(f"予測データ解析エラー: {e}")
            return self._get_default_prediction_data()

    async def parse_sentiment_data(self, ai_response: str) -> Dict[str, Any]:
        """
        センチメントデータの解析
        
        Args:
            ai_response: AIからの応答テキスト
            
        Returns:
            Dict[str, Any]: 解析されたセンチメントデータ
        """
        try:
            # JSONの抽出
            json_data = await self._extract_json_from_response(ai_response)
            
            if not json_data:
                return self._get_default_sentiment_data()
            
            # センチメントデータの検証
            validated_data = await self._validate_sentiment_data(json_data)
            
            return validated_data

        except Exception as e:
            self.logger.error(f"センチメントデータ解析エラー: {e}")
            return self._get_default_sentiment_data()

    async def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """レスポンスからJSONを抽出"""
        try:
            # JSONブロックの検索
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # 直接JSONの検索
            json_pattern = r'\{[^{}]*"direction"[^{}]*\}'
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            
            return None

        except Exception as e:
            self.logger.error(f"JSON抽出エラー: {e}")
            return None

    async def _validate_and_normalize_data(
        self, json_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """データの検証と正規化"""
        validated_data = {
            "direction": "neutral",
            "strength": 0.0,
            "timeframe": "1-4 hours",
            "confidence_score": 0.0,
            "reasons": [],
            "technical_factors": [],
            "fundamental_factors": [],
            "risk_factors": []
        }
        
        # 方向性の検証
        direction = json_data.get("direction", "").lower()
        if direction in ["bullish", "bearish", "neutral"]:
            validated_data["direction"] = direction
        
        # 強度の検証
        strength = json_data.get("strength", 0.0)
        if isinstance(strength, (int, float)) and 0.0 <= strength <= 1.0:
            validated_data["strength"] = float(strength)
        
        # 時間枠の検証
        timeframe = json_data.get("timeframe", "")
        if timeframe and isinstance(timeframe, str):
            validated_data["timeframe"] = timeframe
        
        # 信頼度の検証
        confidence = json_data.get("confidence_score", 0.0)
        if isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0:
            validated_data["confidence_score"] = float(confidence)
        
        # 理由の検証
        reasons = json_data.get("reasons", [])
        if isinstance(reasons, list):
            validated_data["reasons"] = [
                str(reason) for reason in reasons if reason
            ]
        
        # テクニカル要因の検証
        technical = json_data.get("technical_factors", [])
        if isinstance(technical, list):
            validated_data["technical_factors"] = [
                str(factor) for factor in technical if factor
            ]
        
        # ファンダメンタル要因の検証
        fundamental = json_data.get("fundamental_factors", [])
        if isinstance(fundamental, list):
            validated_data["fundamental_factors"] = [
                str(factor) for factor in fundamental if factor
            ]
        
        # リスク要因の検証
        risks = json_data.get("risk_factors", [])
        if isinstance(risks, list):
            validated_data["risk_factors"] = [
                str(risk) for risk in risks if risk
            ]
        
        return validated_data

    async def _validate_sentiment_data(
        self, json_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """センチメントデータの検証"""
        validated_data = {
            "overall_sentiment": "neutral",
            "confidence": 0.0,
            "factors": [],
            "country_sentiment": {},
            "category_sentiment": {}
        }
        
        # 全体的センチメントの検証
        sentiment = json_data.get("overall_sentiment", "").lower()
        if sentiment in ["bullish", "bearish", "neutral"]:
            validated_data["overall_sentiment"] = sentiment
        
        # 信頼度の検証
        confidence = json_data.get("confidence", 0.0)
        if isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0:
            validated_data["confidence"] = float(confidence)
        
        # 要因の検証
        factors = json_data.get("factors", [])
        if isinstance(factors, list):
            validated_data["factors"] = [
                str(factor) for factor in factors if factor
            ]
        
        # 国別センチメントの検証
        country_sentiment = json_data.get("country_sentiment", {})
        if isinstance(country_sentiment, dict):
            validated_data["country_sentiment"] = {
                country: sentiment.lower()
                for country, sentiment in country_sentiment.items()
                if sentiment.lower() in ["bullish", "bearish", "neutral"]
            }
        
        # カテゴリ別センチメントの検証
        category_sentiment = json_data.get("category_sentiment", {})
        if isinstance(category_sentiment, dict):
            validated_data["category_sentiment"] = {
                category: sentiment.lower()
                for category, sentiment in category_sentiment.items()
                if sentiment.lower() in ["bullish", "bearish", "neutral"]
            }
        
        return validated_data

    def _get_default_prediction_data(self) -> Dict[str, Any]:
        """デフォルト予測データ"""
        return {
            "direction": "neutral",
            "strength": 0.0,
            "timeframe": "1-4 hours",
            "confidence_score": 0.0,
            "reasons": ["データ解析エラーのため予測できません"],
            "technical_factors": [],
            "fundamental_factors": [],
            "risk_factors": ["解析エラー"]
        }

    def _get_default_sentiment_data(self) -> Dict[str, Any]:
        """デフォルトセンチメントデータ"""
        return {
            "overall_sentiment": "neutral",
            "confidence": 0.0,
            "factors": ["データ解析エラーのため分析できません"],
            "country_sentiment": {},
            "category_sentiment": {}
        }

    def extract_direction(self, text: str) -> str:
        """
        方向性の抽出
        
        Args:
            text: テキスト
            
        Returns:
            str: 抽出された方向性
        """
        text_lower = text.lower()
        
        if "bullish" in text_lower or "上昇" in text_lower or "押し上げ" in text_lower:
            return "bullish"
        elif "bearish" in text_lower or "下落" in text_lower or "押し下げ" in text_lower:
            return "bearish"
        else:
            return "neutral"

    def extract_strength(self, text: str) -> float:
        """
        強度の抽出
        
        Args:
            text: テキスト
            
        Returns:
            float: 抽出された強度
        """
        # 数値パターンの検索
        strength_patterns = [
            r'強度[：:]\s*([0-9]*\.?[0-9]+)',
            r'strength[：:]\s*([0-9]*\.?[0-9]+)',
            r'([0-9]*\.?[0-9]+)\s*の強度',
            r'強度\s*([0-9]*\.?[0-9]+)'
        ]
        
        for pattern in strength_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    strength = float(match.group(1))
                    return max(0.0, min(1.0, strength))  # 0.0-1.0の範囲に制限
                except ValueError:
                    continue
        
        # デフォルト値
        return 0.5

    def extract_reasons(self, text: str) -> List[str]:
        """
        理由の抽出
        
        Args:
            text: テキスト
            
        Returns:
            List[str]: 抽出された理由のリスト
        """
        reasons = []
        
        # 理由パターンの検索
        reason_patterns = [
            r'理由[：:]\s*(.+)',
            r'reasons[：:]\s*(.+)',
            r'根拠[：:]\s*(.+)',
            r'要因[：:]\s*(.+)'
        ]
        
        for pattern in reason_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                reason = match.strip()
                if reason and len(reason) > 5:  # 最小長チェック
                    reasons.append(reason)
        
        return reasons[:5]  # 最大5件まで

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "parser": "USDJPYPredictionParser",
            "parse_count": self._parse_count,
            "successful_parses": self._successful_parses,
            "success_rate": self._successful_parses / max(1, self._parse_count)
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な動作確認
            test_data = self._get_default_prediction_data()
            if not test_data or "direction" not in test_data:
                self.logger.error("デフォルト予測データが不適切です")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
