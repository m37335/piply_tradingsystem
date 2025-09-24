"""
OANDA Stream API連携のテスト（REST API不使用設計）

OANDA Stream API連携の動作確認を行う。
REST APIは使用せず、Stream APIのみでテストします。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Any

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.providers.oanda_stream_client import OANDAStreamClient, StreamType, PriceData
from modules.llm_analysis.providers.yahoo_finance_stream_client import YahooFinanceStreamClient
from modules.llm_analysis.providers.base_provider import BaseProvider, ProviderType, ConnectionStatus, ProviderConfig


async def test_oanda_rest_client():
    """OANDA REST APIクライアントのテスト（無効化）"""
    print("⚠️ REST APIは使用しない設計のため、このテストはスキップされます")
    return


async def test_oanda_stream_client():
    """OANDA Stream APIクライアントのテスト"""
    print("\n🧪 OANDA Stream APIクライアントテスト")
    
    client = OANDAStreamClient()
    
    try:
        # 初期化
        await client.initialize()
        print("✅ OANDA Stream APIクライアント初期化完了")
        
        # 設定の確認
        print(f"✅ アカウントID: {client.account_id}")
        print(f"✅ 環境: {client.environment}")
        print(f"✅ ベースURL: {client.base_url}")
        print(f"✅ ストリームURL: {client.stream_url}")
        
        # コールバックの追加
        def price_callback(price_data: PriceData):
            print(f"📊 価格更新: {price_data.instrument} - Bid: {price_data.bid}, Ask: {price_data.ask}")
        
        client.add_callback(StreamType.PRICING, price_callback)
        print("✅ 価格コールバック追加完了")
        
        # ストリームの開始（実際の接続は行わない）
        print("✅ ストリーム設定完了（実際の接続はテスト環境では行いません）")
        
        print("🎉 OANDA Stream APIクライアントテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


async def test_base_provider():
    """ベースプロバイダーのテスト"""
    print("\n🧪 ベースプロバイダーテスト")
    
    # テスト用のプロバイダー設定
    config = ProviderConfig(
        name="test_provider",
        type=ProviderType.STREAM,
        base_url="https://api.example.com",
        timeout=30,
        retry_attempts=3,
        retry_delay=5,
        auto_reconnect=True,
        max_reconnect_attempts=5
    )
    
    # テスト用のプロバイダークラス
    class TestProvider(BaseProvider):
        async def connect(self) -> bool:
            self._update_status(ConnectionStatus.CONNECTED)
            return True
        
        async def disconnect(self) -> bool:
            self._update_status(ConnectionStatus.DISCONNECTED)
            return True
        
        async def send_message(self, message: Any) -> bool:
            self.metrics.total_messages_sent += 1
            return True
        
        async def start_listening(self) -> None:
            pass
        
        async def stop_listening(self) -> None:
            pass
    
    provider = TestProvider(config)
    
    try:
        # 接続
        success = await provider.connect()
        print(f"✅ 接続: {'成功' if success else '失敗'}")
        
        # ステータス確認
        print(f"✅ ステータス: {provider.get_status().value}")
        print(f"✅ 接続状態: {provider.is_connected()}")
        
        # メッセージ送信
        success = await provider.send_message("test message")
        print(f"✅ メッセージ送信: {'成功' if success else '失敗'}")
        
        # ヘルスチェック
        health = await provider.health_check()
        print(f"✅ ヘルスチェック:")
        print(f"   プロバイダー名: {health['provider_name']}")
        print(f"   プロバイダータイプ: {health['provider_type']}")
        print(f"   ステータス: {health['status']}")
        print(f"   接続状態: {health['is_connected']}")
        print(f"   接続回数: {health['metrics']['connection_count']}")
        print(f"   送信メッセージ数: {health['metrics']['total_messages_sent']}")
        
        # 切断
        success = await provider.disconnect()
        print(f"✅ 切断: {'成功' if success else '失敗'}")
        
        print("🎉 ベースプロバイダーテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await provider.close()


async def test_order_creation():
    """注文作成のテスト（無効化）"""
    print("\n⚠️ REST APIは使用しない設計のため、注文作成テストはスキップされます")
    return


async def test_integration_flow():
    """統合フローテスト（Yahoo Finance代替）"""
    print("\n🧪 統合フローテスト（Yahoo Finance代替）")
    
    # Yahoo Finance Stream Clientを使用
    stream_client = YahooFinanceStreamClient()
    
    try:
        # Streamクライアントの初期化
        await stream_client.initialize()
        print("✅ Yahoo Finance Streamクライアント初期化完了")
        
        # ストリームコールバックの設定
        def price_callback(price_data: PriceData):
            print(f"📊 リアルタイム価格: {price_data.instrument} - {price_data.mid_price:.5f}")
        
        stream_client.add_callback(StreamType.PRICING, price_callback)
        print("✅ ストリームコールバック設定完了")
        
        # 現在価格の取得テスト
        usd_jpy_price = await stream_client.get_current_price('USD_JPY')
        if usd_jpy_price:
            print(f"✅ USD/JPY現在価格: {usd_jpy_price.mid_price:.5f}")
        
        print("🎉 統合フローテスト完了（Yahoo Finance代替）")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await stream_client.close()


async def main():
    """メイン関数（Stream APIのみ）"""
    print("🚀 OANDA Stream API連携テスト開始（REST API不使用設計）")
    
    # OANDA REST APIクライアントテスト（スキップ）
    await test_oanda_rest_client()
    
    # OANDA Stream APIクライアントテスト
    await test_oanda_stream_client()
    
    # ベースプロバイダーテスト
    await test_base_provider()
    
    # 注文作成テスト（スキップ）
    await test_order_creation()
    
    # 統合フローテスト
    await test_integration_flow()
    
    print("\n🎉 全てのテストが完了しました！（Stream APIのみ）")


if __name__ == "__main__":
    asyncio.run(main())
