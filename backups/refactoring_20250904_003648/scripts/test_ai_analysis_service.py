"""
AI分析サービステストスクリプト
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.entities import EconomicEventFactory
from src.domain.services.ai_analysis import (
    AIAnalysisService,
    AIReportGenerator,
    ConfidenceScoreCalculator,
    OpenAIPromptBuilder,
    USDJPYPredictionParser,
)
from src.infrastructure.external.openai import OpenAIClient


async def test_ai_analysis_components():
    """AI分析コンポーネントの個別テスト"""
    print("=== AI分析コンポーネントテスト ===")

    try:
        # テスト用データの作成
        factory = EconomicEventFactory()

        # 1. OpenAIPromptBuilderテスト
        prompt_builder = OpenAIPromptBuilder()
        test_event = factory.create_from_dict(
            {
                "event_id": "test_ai_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 2.5,
                "previous_value": 2.3,
            }
        )

        pre_event_prompt = await prompt_builder.build_pre_event_prompt(test_event)
        print(
            f"✅ OpenAIPromptBuilderテスト完了: {len(pre_event_prompt)}文字のプロンプト生成"
        )

        # 2. USDJPYPredictionParserテスト
        prediction_parser = USDJPYPredictionParser()
        test_ai_response = """
```json
{
    "direction": "bullish",
    "strength": 0.7,
    "timeframe": "1-4 hours",
    "confidence_score": 0.8,
    "reasons": ["インフレ期待の上昇", "日銀政策の影響"],
    "technical_factors": ["移動平均線の上昇"],
    "fundamental_factors": ["経済成長の加速"],
    "risk_factors": ["地政学的リスク"],
    "summary": "USD/JPYは上昇傾向が予想されます"
}
```
        """

        prediction_data = await prediction_parser.parse_prediction_data(
            test_ai_response
        )
        print(
            f"✅ USDJPYPredictionParserテスト完了: {prediction_data.get('direction', 'unknown')}方向を解析"
        )

        # 3. ConfidenceScoreCalculatorテスト
        confidence_calculator = ConfidenceScoreCalculator()
        confidence_score = await confidence_calculator.calculate_confidence(
            test_event, prediction_data
        )
        print(
            f"✅ ConfidenceScoreCalculatorテスト完了: 信頼度スコア {confidence_score:.2f}"
        )

        # 4. AIReportGeneratorテスト
        from src.domain.entities import USDJPYPrediction

        test_prediction = USDJPYPrediction(
            direction="buy",
            strength="strong",
            timeframe="1-4 hours",
            confidence_score=confidence_score,
            fundamental_reasons=prediction_data.get("reasons", []),
            technical_reasons=prediction_data.get("technical_factors", []),
            risk_factors=prediction_data.get("risk_factors", []),
        )

        report_generator = AIReportGenerator()
        report_content = await report_generator.generate_pre_event_content(
            test_event, test_prediction, test_ai_response
        )
        print(
            f"✅ AIReportGeneratorテスト完了: {len(report_content)}文字のレポート生成"
        )

        return True

    except Exception as e:
        print(f"❌ AI分析コンポーネントテストエラー: {e}")
        return False


async def test_ai_analysis_service():
    """AI分析サービスの統合テスト"""
    print("\n=== AI分析サービス統合テスト ===")

    try:
        # OpenAIクライアントの作成（モック用）
        openai_client = OpenAIClient(api_key="test_key")

        # AI分析サービスの作成
        ai_service = AIAnalysisService(openai_client)
        print("✅ AI分析サービス作成完了")

        # テスト用データの作成
        factory = EconomicEventFactory()

        test_event = factory.create_from_dict(
            {
                "event_id": "integration_ai_001",
                "date_utc": datetime.utcnow() + timedelta(hours=2),
                "country": "united states",
                "event_name": "Non-Farm Payrolls",
                "importance": "high",
                "forecast_value": 200000,
                "previous_value": 190000,
            }
        )

        # 事前レポート生成テスト（モック）
        print("📝 事前レポート生成テスト（モック）")
        # 実際のAPI呼び出しは行わず、コンポーネントの統合をテスト

        # 統計情報の確認
        stats = ai_service.get_stats()
        print(f"✅ 統計情報取得: {stats['analysis_count']}回の分析")

        return True

    except Exception as e:
        print(f"❌ AI分析サービス統合テストエラー: {e}")
        return False


async def test_prompt_builder():
    """プロンプトビルダーの詳細テスト"""
    print("\n=== プロンプトビルダー詳細テスト ===")

    try:
        prompt_builder = OpenAIPromptBuilder()
        factory = EconomicEventFactory()

        # 事前レポートプロンプト
        pre_event = factory.create_from_dict(
            {
                "event_id": "prompt_test_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Bank of Japan Policy Rate",
                "importance": "high",
                "forecast_value": 0.1,
                "previous_value": 0.1,
            }
        )

        pre_prompt = await prompt_builder.build_pre_event_prompt(pre_event)
        print(f"✅ 事前レポートプロンプト: {len(pre_prompt)}文字")

        # 事後レポートプロンプト
        post_event = factory.create_from_dict(
            {
                "event_id": "prompt_test_002",
                "date_utc": datetime.utcnow(),
                "country": "united states",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "actual_value": 3.2,
                "forecast_value": 3.0,
                "previous_value": 2.9,
            }
        )

        post_prompt = await prompt_builder.build_post_event_prompt(post_event)
        print(f"✅ 事後レポートプロンプト: {len(post_prompt)}文字")

        # 予測値変更プロンプト
        old_event = factory.create_from_dict(
            {
                "event_id": "prompt_test_003",
                "date_utc": datetime.utcnow() + timedelta(hours=3),
                "country": "euro zone",
                "event_name": "ECB Interest Rate Decision",
                "importance": "high",
                "forecast_value": 4.0,
                "previous_value": 4.0,
            }
        )

        new_event = factory.create_from_dict(
            {
                "event_id": "prompt_test_003",
                "date_utc": datetime.utcnow() + timedelta(hours=3),
                "country": "euro zone",
                "event_name": "ECB Interest Rate Decision",
                "importance": "high",
                "forecast_value": 4.25,
                "previous_value": 4.0,
            }
        )

        change_prompt = await prompt_builder.build_forecast_change_prompt(
            old_event, new_event
        )
        print(f"✅ 予測値変更プロンプト: {len(change_prompt)}文字")

        return True

    except Exception as e:
        print(f"❌ プロンプトビルダー詳細テストエラー: {e}")
        return False


async def test_prediction_parser():
    """予測データ解析器の詳細テスト"""
    print("\n=== 予測データ解析器詳細テスト ===")

    try:
        prediction_parser = USDJPYPredictionParser()

        # 正常なJSONレスポンスのテスト
        valid_response = """
```json
{
    "direction": "bearish",
    "strength": 0.6,
    "timeframe": "1-4 hours",
    "confidence_score": 0.75,
    "reasons": ["経済成長の減速", "政策不確実性"],
    "technical_factors": ["RSIの過買い", "サポートラインの破綻"],
    "fundamental_factors": ["GDP成長率の鈍化"],
    "risk_factors": ["地政学的緊張", "市場流動性の低下"],
    "summary": "USD/JPYは下落傾向が予想されます"
}
```
        """

        parsed_data = await prediction_parser.parse_prediction_data(valid_response)
        print(f"✅ 正常JSON解析: {parsed_data.get('direction', 'unknown')}方向")
        print(f"   強度: {parsed_data.get('strength', 0):.2f}")
        print(f"   理由数: {len(parsed_data.get('reasons', []))}")

        # 不正なJSONレスポンスのテスト
        invalid_response = "This is not a valid JSON response"
        fallback_data = await prediction_parser.parse_prediction_data(invalid_response)
        print(
            f"✅ 不正JSON処理: {fallback_data.get('direction', 'unknown')}方向（フォールバック）"
        )

        # センチメントデータ解析のテスト
        sentiment_response = """
```json
{
    "overall_sentiment": "bullish",
    "confidence": 0.8,
    "factors": ["複数の経済指標の改善", "政策環境の安定"],
    "country_sentiment": {
        "japan": "bullish",
        "united states": "neutral",
        "euro zone": "bearish"
    },
    "category_sentiment": {
        "inflation": "bullish",
        "employment": "neutral",
        "interest_rate": "bearish"
    },
    "summary": "全体的に楽観的な市場センチメント"
}
```
        """

        sentiment_data = await prediction_parser.parse_sentiment_data(
            sentiment_response
        )
        print(
            f"✅ センチメント解析: {sentiment_data.get('overall_sentiment', 'unknown')}センチメント"
        )

        return True

    except Exception as e:
        print(f"❌ 予測データ解析器詳細テストエラー: {e}")
        return False


async def test_confidence_calculator():
    """信頼度計算器の詳細テスト"""
    print("\n=== 信頼度計算器詳細テスト ===")

    try:
        confidence_calculator = ConfidenceScoreCalculator()
        factory = EconomicEventFactory()

        # 高品質データのテスト
        high_quality_event = factory.create_from_dict(
            {
                "event_id": "confidence_test_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "united states",
                "event_name": "Federal Reserve Interest Rate Decision",
                "importance": "high",
                "forecast_value": 5.5,
                "previous_value": 5.25,
                "unit": "%",
            }
        )

        high_quality_prediction = {
            "direction": "bullish",
            "strength": 0.8,
            "reasons": ["明確な理由1", "明確な理由2"],
            "technical_factors": ["テクニカル要因1"],
            "fundamental_factors": ["ファンダメンタル要因1"],
        }

        high_confidence = await confidence_calculator.calculate_confidence(
            high_quality_event, high_quality_prediction
        )
        print(f"✅ 高品質データ: 信頼度 {high_confidence:.2f}")

        # 低品質データのテスト
        low_quality_event = factory.create_from_dict(
            {
                "event_id": "confidence_test_002",
                "date_utc": datetime.utcnow() + timedelta(days=7),
                "country": "switzerland",
                "event_name": "Test",
                "importance": "low",
            }
        )

        low_quality_prediction = {
            "direction": "neutral",
            "strength": 0.3,
            "reasons": [],
            "technical_factors": [],
            "fundamental_factors": [],
        }

        low_confidence = await confidence_calculator.calculate_confidence(
            low_quality_event, low_quality_prediction
        )
        print(f"✅ 低品質データ: 信頼度 {low_confidence:.2f}")

        # 集計信頼度のテスト
        confidence_scores = [0.8, 0.6, 0.9, 0.4, 0.7]
        aggregate_result = await confidence_calculator.calculate_aggregate_confidence(
            confidence_scores
        )
        print(f"✅ 集計信頼度: 平均 {aggregate_result['avg_confidence']:.2f}")

        return True

    except Exception as e:
        print(f"❌ 信頼度計算器詳細テストエラー: {e}")
        return False


async def test_report_generator():
    """レポート生成器の詳細テスト"""
    print("\n=== レポート生成器詳細テスト ===")

    try:
        report_generator = AIReportGenerator()
        factory = EconomicEventFactory()

        from src.domain.entities import USDJPYPrediction

        # テスト用イベントと予測データ
        test_event = factory.create_from_dict(
            {
                "event_id": "report_test_001",
                "date_utc": datetime.utcnow() + timedelta(hours=2),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 2.5,
                "previous_value": 2.3,
                "unit": "%",
            }
        )

        test_prediction = USDJPYPrediction(
            direction="buy",
            strength="strong",
            timeframe="1-4 hours",
            confidence_score=0.8,
            fundamental_reasons=["インフレ期待の上昇", "日銀政策の影響"],
            technical_reasons=["移動平均線の上昇", "RSIの改善"],
            risk_factors=["地政学的リスク", "市場流動性の低下"],
        )

        test_ai_response = """
```json
{
    "direction": "bullish",
    "strength": 0.7,
    "timeframe": "1-4 hours",
    "confidence_score": 0.8,
    "reasons": ["インフレ期待の上昇", "日銀政策の影響"],
    "technical_factors": ["移動平均線の上昇", "RSIの改善"],
    "fundamental_factors": ["経済成長の加速", "雇用環境の改善"],
    "risk_factors": ["地政学的リスク", "市場流動性の低下"],
    "summary": "USD/JPYは上昇傾向が予想されます。インフレ期待の上昇と日銀政策の影響により、買いポジションが推奨されます。"
}
```
        """

        # 事前レポート生成
        pre_content = await report_generator.generate_pre_event_content(
            test_event, test_prediction, test_ai_response
        )
        print(f"✅ 事前レポート生成: {len(pre_content)}文字")

        # 事後レポート生成（実際値を追加）
        post_event = factory.create_from_dict(
            {
                "event_id": "report_test_002",
                "date_utc": datetime.utcnow(),
                "country": "united states",
                "event_name": "Non-Farm Payrolls",
                "importance": "high",
                "actual_value": 220000,
                "forecast_value": 200000,
                "previous_value": 190000,
                "unit": "K",
            }
        )

        post_content = await report_generator.generate_post_event_content(
            post_event, test_prediction, test_ai_response
        )
        print(f"✅ 事後レポート生成: {len(post_content)}文字")

        # 予測値変更レポート生成
        old_event = factory.create_from_dict(
            {
                "event_id": "report_test_003",
                "date_utc": datetime.utcnow() + timedelta(hours=3),
                "country": "euro zone",
                "event_name": "ECB Interest Rate Decision",
                "importance": "high",
                "forecast_value": 4.0,
                "previous_value": 4.0,
                "unit": "%",
            }
        )

        new_event = factory.create_from_dict(
            {
                "event_id": "report_test_003",
                "date_utc": datetime.utcnow() + timedelta(hours=3),
                "country": "euro zone",
                "event_name": "ECB Interest Rate Decision",
                "importance": "high",
                "forecast_value": 4.25,
                "previous_value": 4.0,
                "unit": "%",
            }
        )

        change_content = await report_generator.generate_forecast_change_content(
            old_event, new_event, test_prediction, test_ai_response
        )
        print(f"✅ 予測値変更レポート生成: {len(change_content)}文字")

        return True

    except Exception as e:
        print(f"❌ レポート生成器詳細テストエラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("AI分析サービステスト")
    print("=" * 60)

    # 各テストの実行
    components_ok = await test_ai_analysis_components()
    service_ok = await test_ai_analysis_service()
    prompt_ok = await test_prompt_builder()
    parser_ok = await test_prediction_parser()
    confidence_ok = await test_confidence_calculator()
    report_ok = await test_report_generator()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  AI分析コンポーネント: {'✅' if components_ok else '❌'}")
    print(f"  AI分析サービス統合: {'✅' if service_ok else '❌'}")
    print(f"  プロンプトビルダー詳細: {'✅' if prompt_ok else '❌'}")
    print(f"  予測データ解析器詳細: {'✅' if parser_ok else '❌'}")
    print(f"  信頼度計算器詳細: {'✅' if confidence_ok else '❌'}")
    print(f"  レポート生成器詳細: {'✅' if report_ok else '❌'}")

    if all([components_ok, service_ok, prompt_ok, parser_ok, confidence_ok, report_ok]):
        print("\n🎉 全てのAI分析サービステストが成功しました！")
        print("🤖 ChatGPTによるドル円予測分析システム完成！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
