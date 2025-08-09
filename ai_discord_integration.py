#!/usr/bin/env python3
"""
AI分析結果Discord配信スクリプト
Exchange Analytics System の AI分析結果を Discord に配信
"""

import asyncio
import json
import sys
from datetime import datetime
import pytz
from typing import Dict, Any

import httpx


class AIDiscordIntegration:
    """AI分析結果Discord配信クラス"""
    
    def __init__(self, api_key: str, webhook_url: str, api_base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.webhook_url = webhook_url
        self.api_base_url = api_base_url
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    async def generate_and_send_ai_analysis(self, currency_pair: str = "USD/JPY", analysis_period: str = "1d"):
        """AI分析レポートを生成してDiscordに送信"""
        print(f"🤖 AI分析レポート生成・配信開始...")
        print(f"📊 通貨ペア: {currency_pair}")
        print(f"⏰ 分析期間: {analysis_period}")
        
        try:
            # AI分析レポート生成
            report = await self._generate_ai_report(currency_pair, analysis_period)
            if not report:
                print("❌ AI分析レポート生成に失敗しました")
                return False
            
            # Discord通知送信
            success = await self._send_discord_notification(report, currency_pair)
            if success:
                print("✅ AI分析結果をDiscordに配信しました")
                return True
            else:
                print("❌ Discord配信に失敗しました")
                return False
                
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            return False
    
    async def _generate_ai_report(self, currency_pair: str, analysis_period: str) -> Dict[str, Any]:
        """AI分析レポートを生成"""
        print("📊 AI分析レポート生成中...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/ai-reports/generate",
                    headers=self.headers,
                    json={
                        "currency_pair": currency_pair,
                        "analysis_period": analysis_period
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ AI分析レポート生成完了: {data['data']['report_id']}")
                    return data['data']
                else:
                    print(f"❌ AI分析生成失敗: HTTP {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"❌ AI分析生成エラー: {str(e)}")
                return None
    
    async def _send_discord_notification(self, report: Dict[str, Any], currency_pair: str) -> bool:
        """Discord通知送信"""
        print("💬 Discord通知送信中...")
        
        # 分析結果の要約
        title = report.get('title', f'{currency_pair} AI分析レポート')
        content = report.get('content', '分析結果が利用できません')
        confidence = report.get('confidence_score', 0.0)
        model = report.get('model', 'AI')
        generated_at = report.get('generated_at', datetime.now(pytz.timezone("Asia/Tokyo")).isoformat())
        
        # 信頼度に基づく色設定
        if confidence >= 0.8:
            color = 0x00FF00  # 緑（高信頼度）
            confidence_emoji = "🟢"
        elif confidence >= 0.6:
            color = 0xFFFF00  # 黄（中信頼度）
            confidence_emoji = "🟡"
        else:
            color = 0xFF6600  # オレンジ（低信頼度）
            confidence_emoji = "🟠"
        
        # Discord Embed作成
        discord_data = {
            "content": f"🤖 **AI市場分析レポート** - {currency_pair}",
            "embeds": [{
                "title": f"📊 {title}",
                "description": content[:500] + ("..." if len(content) > 500 else ""),
                "color": color,
                "fields": [
                    {
                        "name": "💱 通貨ペア",
                        "value": currency_pair,
                        "inline": True
                    },
                    {
                        "name": f"{confidence_emoji} 信頼度",
                        "value": f"{confidence:.1%}",
                        "inline": True
                    },
                    {
                        "name": "🤖 AI モデル",
                        "value": model,
                        "inline": True
                    },
                    {
                        "name": "📈 分析要約",
                        "value": report.get('summary', '詳細分析をご確認ください'),
                        "inline": False
                    },
                    {
                        "name": "🕒 生成時刻",
                        "value": generated_at,
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Exchange Analytics AI Assistant"
                },
                "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat()
            }]
        }
        
        # Discord送信
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.webhook_url,
                    json=discord_data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 204]:
                    print("✅ Discord通知送信成功")
                    return True
                else:
                    print(f"❌ Discord送信失敗: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Discord送信エラー: {str(e)}")
                return False
    
    async def send_test_notification(self):
        """テスト通知送信"""
        print("🧪 テスト通知送信中...")
        
        test_data = {
            "content": "🧪 **AI分析テスト通知**",
            "embeds": [{
                "title": "📊 AI分析システム テスト",
                "description": "AI分析結果のDiscord配信機能をテスト中です",
                "color": 0x3498DB,
                "fields": [
                    {"name": "🤖 システム", "value": "Exchange Analytics", "inline": True},
                    {"name": "📡 機能", "value": "AI→Discord連携", "inline": True},
                    {"name": "✅ ステータス", "value": "テスト実行中", "inline": True}
                ],
                "footer": {"text": "AI Discord Integration Test"},
                "timestamp": datetime.now(pytz.timezone("Asia/Tokyo")).isoformat()
            }]
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.webhook_url, json=test_data, timeout=10.0)
                if response.status_code in [200, 204]:
                    print("✅ テスト通知送信成功")
                    return True
                else:
                    print(f"❌ テスト通知失敗: HTTP {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ テスト通知エラー: {str(e)}")
                return False


async def main():
    """メイン実行関数"""
    import os
    
    # 環境変数から設定取得
    api_key = os.getenv('DEFAULT_API_KEY', 'dev_api_key_12345')
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL が設定されていません")
        sys.exit(1)
    
    # インテグレーション初期化
    integration = AIDiscordIntegration(api_key, webhook_url)
    
    # コマンドライン引数処理
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # テスト通知
            await integration.send_test_notification()
            
        elif command == "analyze":
            # AI分析・配信
            currency_pair = sys.argv[2] if len(sys.argv) > 2 else "USD/JPY"
            analysis_period = sys.argv[3] if len(sys.argv) > 3 else "1d"
            await integration.generate_and_send_ai_analysis(currency_pair, analysis_period)
            
        else:
            print("❌ 無効なコマンド")
            print("使用法: python ai_discord_integration.py [test|analyze] [currency_pair] [period]")
    else:
        print("🤖 AI分析Discord配信ツール")
        print("使用法:")
        print("  python ai_discord_integration.py test                    # テスト通知")
        print("  python ai_discord_integration.py analyze                 # USD/JPY 1日分析")
        print("  python ai_discord_integration.py analyze EUR/USD 1w      # EUR/USD 1週間分析")


if __name__ == "__main__":
    asyncio.run(main())
