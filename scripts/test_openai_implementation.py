#!/usr/bin/env python3
"""
OpenAIクライアントテストスクリプト
OpenAI APIクライアントの動作確認を行う
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.infrastructure.external.openai import (
    OpenAIClient, OpenAIPromptManager, OpenAIErrorHandler
)


async def test_prompt_manager():
    """プロンプトマネージャーのテスト"""
    print("=== プロンプトマネージャーテスト ===")
    
    try:
        prompt_manager = OpenAIPromptManager()
        
        # テスト用イベントデータ
        test_event = {
            "event_name": "Consumer Price Index (CPI)",
            "country": "United States",
            "importance": "high",
            "date_utc": datetime.utcnow(),
            "forecast_value": 3.2,
            "previous_value": 3.1,
            "actual_value": 3.3,
            "currency": "USD",
            "unit": "%"
        }
        
        print("✅ プロンプトマネージャー作成完了")
        
        # システムプロンプトのテスト
        print("\n--- システムプロンプトテスト ---")
        system_prompts = [
            prompt_manager.get_system_prompt("pre_event"),
            prompt_manager.get_system_prompt("post_event"),
            prompt_manager.get_system_prompt("forecast_change"),
            prompt_manager.get_usd_jpy_system_prompt(),
            prompt_manager.get_report_system_prompt()
        ]
        
        for i, prompt in enumerate(system_prompts):
            print(f"  システムプロンプト {i+1}: {'✅' if prompt else '❌'}")
        
        # 経済分析プロンプトのテスト
        print("\n--- 経済分析プロンプトテスト ---")
        analysis_prompts = [
            prompt_manager.create_economic_analysis_prompt(test_event, "pre_event"),
            prompt_manager.create_economic_analysis_prompt(test_event, "post_event")
        ]
        
        for i, prompt in enumerate(analysis_prompts):
            print(f"  分析プロンプト {i+1}: {'✅' if prompt else '❌'}")
        
        # USD/JPY予測プロンプトのテスト
        print("\n--- USD/JPY予測プロンプトテスト ---")
        market_context = {
            "current_usd_jpy": 150.50,
            "market_sentiment": "bullish",
            "recent_events": ["Fed meeting", "BOJ policy decision"]
        }
        
        prediction_prompt = prompt_manager.create_usd_jpy_prediction_prompt(
            test_event, market_context
        )
        print(f"  予測プロンプト: {'✅' if prediction_prompt else '❌'}")
        
        # レポート生成プロンプトのテスト
        print("\n--- レポート生成プロンプトテスト ---")
        report_prompt = prompt_manager.create_report_generation_prompt(
            test_event, {"direction": "buy", "strength": "moderate"}, "pre_event"
        )
        print(f"  レポートプロンプト: {'✅' if report_prompt else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ プロンプトマネージャーテストエラー: {e}")
        return False
    
    print()


async def test_error_handler():
    """エラーハンドラーのテスト"""
    print("=== エラーハンドラーテスト ===")
    
    try:
        error_handler = OpenAIErrorHandler()
        
        print("✅ エラーハンドラー作成完了")
        
        # エラー処理のテスト
        print("\n--- エラー処理テスト ---")
        
        # テスト用エラー
        test_errors = [
            Exception("Connection timeout"),
            Exception("Rate limit exceeded"),
            Exception("API key invalid"),
            Exception("Server error 500")
        ]
        
        for i, error in enumerate(test_errors):
            error_info = error_handler.handle_error(error, {"test": True})
            print(f"  エラー処理 {i+1}: {'✅' if error_info else '❌'}")
        
        # リトライ判定のテスト
        print("\n--- リトライ判定テスト ---")
        for error in test_errors:
            should_retry = error_handler.should_retry(error)
            retry_delay = error_handler.get_retry_delay(error, 1)
            print(f"  リトライ判定: {'✅' if should_retry is not None else '❌'}")
            print(f"  リトライ遅延: {retry_delay}秒")
        
        # エラーサマリーのテスト
        print("\n--- エラーサマリーテスト ---")
        summary = error_handler.get_error_summary()
        print(f"  エラーサマリー: {summary}")
        
        # 健全性チェックのテスト
        print("\n--- 健全性チェックテスト ---")
        is_healthy = error_handler.is_healthy()
        print(f"  システム健全性: {'✅' if is_healthy else '❌'}")
        
        # レート制限状態のテスト
        print("\n--- レート制限状態テスト ---")
        rate_limit_status = error_handler.get_rate_limit_status()
        print(f"  レート制限状態: {rate_limit_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ エラーハンドラーテストエラー: {e}")
        return False
    
    print()


async def test_openai_client():
    """OpenAIクライアントのテスト"""
    print("=== OpenAIクライアントテスト ===")
    
    try:
        # APIキーの確認
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY環境変数が設定されていません。")
            print("   テストをスキップします。")
            return True
        
        # クライアントの作成
        client = OpenAIClient(
            api_key=api_key,
            model="gpt-4",
            max_tokens=100,
            temperature=0.1
        )
        
        print("✅ OpenAIクライアント作成完了")
        
        # 接続テスト
        print("\n--- 接続テスト ---")
        connected = await client.connect()
        if not connected:
            print("❌ OpenAIクライアントの接続に失敗しました")
            return False
        
        print("✅ OpenAIクライアント接続完了")
        
        # 基本的なレスポンス生成テスト
        print("\n--- 基本レスポンス生成テスト ---")
        test_messages = [{"role": "user", "content": "Hello, please respond with 'OK'."}]
        
        response = await client.generate_response(
            messages=test_messages,
            max_tokens=10
        )
        
        if response and "OK" in response:
            print("✅ 基本レスポンス生成: 成功")
        else:
            print("❌ 基本レスポンス生成: 失敗")
            print(f"   レスポンス: {response}")
        
        # 使用統計のテスト
        print("\n--- 使用統計テスト ---")
        usage_stats = client.get_usage_stats()
        print(f"  使用統計: {usage_stats}")
        
        # 接続切断
        await client.disconnect()
        print("✅ OpenAIクライアント接続切断完了")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAIクライアントテストエラー: {e}")
        return False
    
    print()


async def test_integration():
    """統合テスト"""
    print("=== 統合テスト ===")
    
    try:
        # APIキーの確認
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY環境変数が設定されていません。")
            print("   統合テストをスキップします。")
            return True
        
        # クライアントの作成
        client = OpenAIClient(api_key=api_key, max_tokens=200)
        
        print("✅ 統合テスト用クライアント作成完了")
        
        # 接続
        await client.connect()
        
        # テスト用イベントデータ
        test_event = {
            "event_name": "Non-Farm Payrolls",
            "country": "United States",
            "importance": "high",
            "date_utc": datetime.utcnow(),
            "forecast_value": 180000,
            "previous_value": 175000,
            "actual_value": 185000,
            "currency": "USD",
            "unit": "jobs"
        }
        
        # 経済イベント分析のテスト
        print("\n--- 経済イベント分析テスト ---")
        analysis_result = await client.analyze_economic_event(
            test_event, "pre_event"
        )
        
        if analysis_result:
            print("✅ 経済イベント分析: 成功")
            print(f"   結果: {analysis_result}")
        else:
            print("❌ 経済イベント分析: 失敗")
        
        # USD/JPY予測のテスト
        print("\n--- USD/JPY予測テスト ---")
        market_context = {"current_usd_jpy": 150.50}
        
        prediction_result = await client.generate_usd_jpy_prediction(
            test_event, market_context
        )
        
        if prediction_result:
            print("✅ USD/JPY予測: 成功")
            print(f"   結果: {prediction_result}")
        else:
            print("❌ USD/JPY予測: 失敗")
        
        # AIレポート生成のテスト
        print("\n--- AIレポート生成テスト ---")
        report_result = await client.generate_ai_report(
            test_event, prediction_result, "pre_event"
        )
        
        if report_result:
            print("✅ AIレポート生成: 成功")
            print(f"   結果: {report_result}")
        else:
            print("❌ AIレポート生成: 失敗")
        
        # 最終統計
        print("\n--- 最終統計 ---")
        final_stats = client.get_usage_stats()
        print(f"  最終使用統計: {final_stats}")
        
        # 接続切断
        await client.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")
        return False
    
    print()


async def main():
    """メイン関数"""
    print("investpy経済カレンダーシステム OpenAIクライアントテスト")
    print("=" * 60)
    
    # 各テストの実行
    prompt_ok = await test_prompt_manager()
    error_ok = await test_error_handler()
    client_ok = await test_openai_client()
    integration_ok = await test_integration()
    
    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  プロンプトマネージャー: {'✅' if prompt_ok else '❌'}")
    print(f"  エラーハンドラー: {'✅' if error_ok else '❌'}")
    print(f"  OpenAIクライアント: {'✅' if client_ok else '❌'}")
    print(f"  統合テスト: {'✅' if integration_ok else '❌'}")
    
    if all([prompt_ok, error_ok, client_ok, integration_ok]):
        print("\n🎉 全てのOpenAIテストが成功しました！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")
    
    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
