"""
AI分析サービス

ChatGPTを使用したドル円予測分析のメインサービス
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.domain.entities import EconomicEvent, AIReport, USDJPYPrediction
from src.infrastructure.external.openai import OpenAIClient
from .openai_prompt_builder import OpenAIPromptBuilder
from .usd_jpy_prediction_parser import USDJPYPredictionParser
from .confidence_score_calculator import ConfidenceScoreCalculator
from .ai_report_generator import AIReportGenerator


class AIAnalysisService:
    """
    AI分析サービス
    
    ChatGPTを使用したドル円予測分析を統合する
    """

    def __init__(
        self,
        openai_client: OpenAIClient,
        prompt_builder: Optional[OpenAIPromptBuilder] = None,
        prediction_parser: Optional[USDJPYPredictionParser] = None,
        confidence_calculator: Optional[ConfidenceScoreCalculator] = None,
        report_generator: Optional[AIReportGenerator] = None,
    ):
        """
        初期化
        
        Args:
            openai_client: OpenAIクライアント
            prompt_builder: プロンプトビルダー（オプション）
            prediction_parser: 予測データ解析器（オプション）
            confidence_calculator: 信頼度計算器（オプション）
            report_generator: レポート生成器（オプション）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.openai_client = openai_client
        
        # コンポーネントの初期化
        self.prompt_builder = prompt_builder or OpenAIPromptBuilder()
        self.prediction_parser = prediction_parser or USDJPYPredictionParser()
        self.confidence_calculator = confidence_calculator or ConfidenceScoreCalculator()
        self.report_generator = report_generator or AIReportGenerator()
        
        # 統計情報
        self._analysis_count = 0
        self._successful_analyses = 0
        self._total_confidence_score = 0.0

    async def generate_pre_event_report(self, event: EconomicEvent) -> AIReport:
        """
        イベント前のドル円予測レポート生成
        
        Args:
            event: 経済イベント
            
        Returns:
            AIReport: 生成されたAIレポート
        """
        try:
            self.logger.info(f"事前レポート生成開始: {event.event_id}")
            self._analysis_count += 1
            
            # プロンプトの構築
            prompt = await self.prompt_builder.build_pre_event_prompt(event)
            
            # OpenAI API呼び出し
            ai_response = await self.openai_client.generate_text(prompt)
            
            if not ai_response:
                raise Exception("OpenAI APIからの応答が空です")
            
            # 予測データの解析
            prediction_data = await self.prediction_parser.parse_prediction_data(ai_response)
            
            # 信頼度スコアの計算
            confidence_score = await self.confidence_calculator.calculate_confidence(
                event, prediction_data
            )
            
            # USD/JPY予測オブジェクトの作成
            usd_jpy_prediction = USDJPYPrediction(
                direction=prediction_data.get("direction", "neutral"),
                strength=prediction_data.get("strength", 0.0),
                timeframe=prediction_data.get("timeframe", "1-4 hours"),
                confidence_score=confidence_score,
                reasons=prediction_data.get("reasons", []),
                technical_factors=prediction_data.get("technical_factors", []),
                fundamental_factors=prediction_data.get("fundamental_factors", []),
                risk_factors=prediction_data.get("risk_factors", [])
            )
            
            # レポートの生成
            report_content = await self.report_generator.generate_pre_event_content(
                event, usd_jpy_prediction, ai_response
            )
            
            # AIReportオブジェクトの作成
            ai_report = AIReport(
                event_id=event.event_id,
                report_type="pre_event",
                report_content=report_content,
                usd_jpy_prediction=usd_jpy_prediction,
                confidence_score=confidence_score,
                generated_at=datetime.utcnow()
            )
            
            # 統計更新
            self._successful_analyses += 1
            self._total_confidence_score += confidence_score
            
            self.logger.info(
                f"事前レポート生成完了: {event.event_id}, "
                f"信頼度: {confidence_score:.2f}"
            )
            
            return ai_report

        except Exception as e:
            self.logger.error(f"事前レポート生成エラー: {e}")
            # エラー時のフォールバックレポート
            return await self._create_fallback_report(event, "pre_event", str(e))

    async def generate_post_event_report(self, event: EconomicEvent) -> AIReport:
        """
        イベント後のドル円分析レポート生成
        
        Args:
            event: 経済イベント
            
        Returns:
            AIReport: 生成されたAIレポート
        """
        try:
            self.logger.info(f"事後レポート生成開始: {event.event_id}")
            self._analysis_count += 1
            
            # プロンプトの構築
            prompt = await self.prompt_builder.build_post_event_prompt(event)
            
            # OpenAI API呼び出し
            ai_response = await self.openai_client.generate_text(prompt)
            
            if not ai_response:
                raise Exception("OpenAI APIからの応答が空です")
            
            # 予測データの解析
            prediction_data = await self.prediction_parser.parse_prediction_data(ai_response)
            
            # 信頼度スコアの計算
            confidence_score = await self.confidence_calculator.calculate_confidence(
                event, prediction_data
            )
            
            # USD/JPY予測オブジェクトの作成
            usd_jpy_prediction = USDJPYPrediction(
                direction=prediction_data.get("direction", "neutral"),
                strength=prediction_data.get("strength", 0.0),
                timeframe=prediction_data.get("timeframe", "1-4 hours"),
                confidence_score=confidence_score,
                reasons=prediction_data.get("reasons", []),
                technical_factors=prediction_data.get("technical_factors", []),
                fundamental_factors=prediction_data.get("fundamental_factors", []),
                risk_factors=prediction_data.get("risk_factors", [])
            )
            
            # レポートの生成
            report_content = await self.report_generator.generate_post_event_content(
                event, usd_jpy_prediction, ai_response
            )
            
            # AIReportオブジェクトの作成
            ai_report = AIReport(
                event_id=event.event_id,
                report_type="post_event",
                report_content=report_content,
                usd_jpy_prediction=usd_jpy_prediction,
                confidence_score=confidence_score,
                generated_at=datetime.utcnow()
            )
            
            # 統計更新
            self._successful_analyses += 1
            self._total_confidence_score += confidence_score
            
            self.logger.info(
                f"事後レポート生成完了: {event.event_id}, "
                f"信頼度: {confidence_score:.2f}"
            )
            
            return ai_report

        except Exception as e:
            self.logger.error(f"事後レポート生成エラー: {e}")
            # エラー時のフォールバックレポート
            return await self._create_fallback_report(event, "post_event", str(e))

    async def generate_forecast_change_report(
        self, old_event: EconomicEvent, new_event: EconomicEvent
    ) -> AIReport:
        """
        予測値変更時のドル円影響分析レポート生成
        
        Args:
            old_event: 変更前のイベント
            new_event: 変更後のイベント
            
        Returns:
            AIReport: 生成されたAIレポート
        """
        try:
            self.logger.info(f"予測値変更レポート生成開始: {new_event.event_id}")
            self._analysis_count += 1
            
            # プロンプトの構築
            prompt = await self.prompt_builder.build_forecast_change_prompt(
                old_event, new_event
            )
            
            # OpenAI API呼び出し
            ai_response = await self.openai_client.generate_text(prompt)
            
            if not ai_response:
                raise Exception("OpenAI APIからの応答が空です")
            
            # 予測データの解析
            prediction_data = await self.prediction_parser.parse_prediction_data(ai_response)
            
            # 信頼度スコアの計算
            confidence_score = await self.confidence_calculator.calculate_confidence(
                new_event, prediction_data
            )
            
            # USD/JPY予測オブジェクトの作成
            usd_jpy_prediction = USDJPYPrediction(
                direction=prediction_data.get("direction", "neutral"),
                strength=prediction_data.get("strength", 0.0),
                timeframe=prediction_data.get("timeframe", "1-4 hours"),
                confidence_score=confidence_score,
                reasons=prediction_data.get("reasons", []),
                technical_factors=prediction_data.get("technical_factors", []),
                fundamental_factors=prediction_data.get("fundamental_factors", []),
                risk_factors=prediction_data.get("risk_factors", [])
            )
            
            # レポートの生成
            report_content = await self.report_generator.generate_forecast_change_content(
                old_event, new_event, usd_jpy_prediction, ai_response
            )
            
            # AIReportオブジェクトの作成
            ai_report = AIReport(
                event_id=new_event.event_id,
                report_type="forecast_change",
                report_content=report_content,
                usd_jpy_prediction=usd_jpy_prediction,
                confidence_score=confidence_score,
                generated_at=datetime.utcnow()
            )
            
            # 統計更新
            self._successful_analyses += 1
            self._total_confidence_score += confidence_score
            
            self.logger.info(
                f"予測値変更レポート生成完了: {new_event.event_id}, "
                f"信頼度: {confidence_score:.2f}"
            )
            
            return ai_report

        except Exception as e:
            self.logger.error(f"予測値変更レポート生成エラー: {e}")
            # エラー時のフォールバックレポート
            return await self._create_fallback_report(new_event, "forecast_change", str(e))

    async def generate_bulk_reports(
        self, events: List[EconomicEvent], report_type: str = "pre_event"
    ) -> List[AIReport]:
        """
        複数イベントの一括レポート生成
        
        Args:
            events: 経済イベントリスト
            report_type: レポートタイプ
            
        Returns:
            List[AIReport]: 生成されたAIレポートのリスト
        """
        try:
            self.logger.info(f"一括レポート生成開始: {len(events)}件, タイプ: {report_type}")
            
            reports = []
            successful_count = 0
            
            for event in events:
                try:
                    if report_type == "pre_event":
                        report = await self.generate_pre_event_report(event)
                    elif report_type == "post_event":
                        report = await self.generate_post_event_report(event)
                    else:
                        self.logger.warning(f"不明なレポートタイプ: {report_type}")
                        continue
                    
                    reports.append(report)
                    successful_count += 1
                    
                except Exception as e:
                    self.logger.error(f"イベント {event.event_id} のレポート生成エラー: {e}")
                    # エラー時はスキップして続行
                    continue
            
            self.logger.info(
                f"一括レポート生成完了: {successful_count}/{len(events)}件成功"
            )
            
            return reports

        except Exception as e:
            self.logger.error(f"一括レポート生成エラー: {e}")
            return []

    async def analyze_market_sentiment(
        self, events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """
        市場センチメント分析
        
        Args:
            events: 経済イベントリスト
            
        Returns:
            Dict[str, Any]: センチメント分析結果
        """
        try:
            self.logger.info("市場センチメント分析開始")
            
            # 高重要度イベントのフィルタリング
            high_importance_events = [
                event for event in events
                if event.is_high_importance
            ]
            
            if not high_importance_events:
                return {"sentiment": "neutral", "confidence": 0.0, "factors": []}
            
            # センチメント分析用プロンプトの構築
            prompt = await self.prompt_builder.build_sentiment_analysis_prompt(
                high_importance_events
            )
            
            # OpenAI API呼び出し
            ai_response = await self.openai_client.generate_text(prompt)
            
            if not ai_response:
                raise Exception("OpenAI APIからの応答が空です")
            
            # センチメントデータの解析
            sentiment_data = await self.prediction_parser.parse_sentiment_data(ai_response)
            
            result = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "total_events_analyzed": len(high_importance_events),
                "sentiment": sentiment_data.get("overall_sentiment", "neutral"),
                "confidence": sentiment_data.get("confidence", 0.0),
                "factors": sentiment_data.get("factors", []),
                "country_sentiment": sentiment_data.get("country_sentiment", {}),
                "category_sentiment": sentiment_data.get("category_sentiment", {})
            }
            
            self.logger.info(f"市場センチメント分析完了: {result['sentiment']}")
            
            return result

        except Exception as e:
            self.logger.error(f"市場センチメント分析エラー: {e}")
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "sentiment": "neutral",
                "confidence": 0.0,
                "factors": []
            }

    async def _create_fallback_report(
        self, event: EconomicEvent, report_type: str, error_message: str
    ) -> AIReport:
        """フォールバックレポートの作成"""
        fallback_content = f"""
# エラーが発生しました

**イベント**: {event.event_name}
**国**: {event.country}
**重要度**: {event.importance.value}
**エラー**: {error_message}

申し訳ございませんが、AI分析中にエラーが発生しました。
手動での分析をお勧めします。
        """.strip()
        
        fallback_prediction = USDJPYPrediction(
            direction="neutral",
            strength=0.0,
            timeframe="1-4 hours",
            confidence_score=0.0,
            reasons=["分析エラーのため予測できません"],
            technical_factors=[],
            fundamental_factors=[],
            risk_factors=["AI分析エラー"]
        )
        
        return AIReport(
            event_id=event.event_id,
            report_type=report_type,
            report_content=fallback_content,
            usd_jpy_prediction=fallback_prediction,
            confidence_score=0.0,
            generated_at=datetime.utcnow()
        )

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        avg_confidence = (
            self._total_confidence_score / max(1, self._successful_analyses)
            if self._successful_analyses > 0 else 0
        )
        
        return {
            "service": "AIAnalysisService",
            "analysis_count": self._analysis_count,
            "successful_analyses": self._successful_analyses,
            "success_rate": self._successful_analyses / max(1, self._analysis_count),
            "avg_confidence_score": avg_confidence,
            "components": {
                "prompt_builder": self.prompt_builder.get_stats(),
                "prediction_parser": self.prediction_parser.get_stats(),
                "confidence_calculator": self.confidence_calculator.get_stats(),
                "report_generator": self.report_generator.get_stats(),
            }
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # OpenAIクライアントの確認
            openai_health = self.openai_client.health_check()
            
            # 各コンポーネントの確認
            prompt_builder_health = self.prompt_builder.health_check()
            prediction_parser_health = self.prediction_parser.health_check()
            confidence_calculator_health = self.confidence_calculator.health_check()
            report_generator_health = self.report_generator.health_check()
            
            return all([
                openai_health,
                prompt_builder_health,
                prediction_parser_health,
                confidence_calculator_health,
                report_generator_health,
            ])
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
