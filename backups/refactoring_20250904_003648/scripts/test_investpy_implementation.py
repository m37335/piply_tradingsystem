#!/usr/bin/env python3
"""
investpy実装テストスクリプト
実装した機能の動作確認を行う
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.domain.entities.economic_event import (
    EconomicEventValidator, EconomicEventFactory
)
from src.domain.entities.ai_report import (
    AIReport, USDJPYPrediction, AIReportValidator
)
from src.infrastructure.external.investpy import (
    InvestpyClient, InvestpyErrorHandler, InvestpyRateLimiter
)


async def test_economic_event_entities():
    """経済イベントエンティティのテスト"""
    print("=== 経済イベントエンティティテスト ===")
    
    # ファクトリのテスト
    factory = EconomicEventFactory()
    
    # サンプルイベントの作成
    sample_event = factory.create_sample_event()
    print(f"サンプルイベント作成: {sample_event}")
    
    # バリデーションのテスト
    validator = EconomicEventValidator()
    is_valid = validator.validate(sample_event)
    print(f"バリデーション結果: {is_valid}")
    
    if not is_valid:
        print("バリデーションエラー:")
        for error in validator.get_errors():
            print(f"  - {error.field}: {error.message}")
    
    # プロパティのテスト
    print(f"高重要度: {sample_event.is_high_importance}")
    print(f"今後のイベント: {sample_event.is_upcoming}")
    print(f"サプライズ率: {sample_event.surprise_percentage}")
    
    print()


async def test_ai_report_entities():
    """AIレポートエンティティのテスト"""
    print("=== AIレポートエンティティテスト ===")
    
    # USDJPYPredictionの作成
    prediction = USDJPYPrediction(
        direction="buy",
        strength="strong",
        target_price=150.50,
        confidence_score=0.8
    )
    prediction.add_fundamental_reason("日本銀行の金融政策変更")
    prediction.add_technical_reason("ドル円の上昇トレンド継続")
    
    print(f"予測作成: {prediction}")
    print(f"予測サマリー: {prediction.get_summary()}")
    print(f"買い方向: {prediction.is_bullish}")
    print(f"高信頼度: {prediction.is_high_confidence}")
    
    # AIReportの作成
    report = AIReport(
        event_id=1,
        report_type="pre_event",
        report_content="日本CPI発表前のドル円分析レポート",
        summary="ドル円は上昇傾向を維持",
        usd_jpy_prediction=prediction,
        confidence_score=0.8
    )
    
    print(f"レポート作成: {report}")
    print(f"レポートサマリー: {report.prediction_summary}")
    
    # バリデーションのテスト
    validator = AIReportValidator()
    is_valid = validator.validate(report)
    print(f"バリデーション結果: {is_valid}")
    
    print()


async def test_investpy_client():
    """investpyクライアントのテスト"""
    print("=== investpyクライアントテスト ===")
    
    # クライアントの作成
    error_handler = InvestpyErrorHandler()
    rate_limiter = InvestpyRateLimiter(max_requests_per_minute=10)
    client = InvestpyClient(error_handler, rate_limiter)
    
    try:
        # 接続テスト
        print("接続テスト中...")
        is_connected = await client.test_connection()
        print(f"接続テスト結果: {is_connected}")
        
        if is_connected:
            # 今日のイベント取得テスト
            print("今日のイベント取得中...")
            df = await client.get_today_events(["japan"])
            print(f"取得件数: {len(df)}")
            
            if not df.empty:
                print("取得データ例:")
                print(df.head(3))
                
                # DataFrame情報の取得
                info = client.get_dataframe_info(df)
                print(f"DataFrame情報: {info}")
        
    except Exception as e:
        print(f"investpyクライアントテストエラー: {e}")
        print("investpyライブラリがインストールされていない可能性があります")
    
    print()


async def test_integration():
    """統合テスト"""
    print("=== 統合テスト ===")
    
    try:
        # investpyクライアントでデータ取得
        client = InvestpyClient()
        df = await client.get_today_events(["japan"])
        
        if not df.empty:
            # ファクトリでエンティティ作成
            factory = EconomicEventFactory()
            events = factory.create_from_dataframe(df)
            
            print(f"作成されたエンティティ数: {len(events)}")
            
            if events:
                # 最初のイベントを詳細表示
                first_event = events[0]
                print(f"最初のイベント: {first_event}")
                
                # バリデーション
                validator = EconomicEventValidator()
                is_valid = validator.validate(first_event)
                print(f"バリデーション結果: {is_valid}")
        
    except Exception as e:
        print(f"統合テストエラー: {e}")
    
    print()


async def main():
    """メイン関数"""
    print("investpy経済カレンダーシステム 実装テスト")
    print("=" * 50)
    
    # 各テストの実行
    await test_economic_event_entities()
    await test_ai_report_entities()
    await test_investpy_client()
    await test_integration()
    
    print("テスト完了")


if __name__ == "__main__":
    asyncio.run(main())
