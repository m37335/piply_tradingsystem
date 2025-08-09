#!/usr/bin/env python3
"""
OpenAI GPT 実AI分析テスト
Exchange Analytics System の実際のGPT分析機能

機能:
- 為替市場分析
- 技術的分析
- 市場予測
- APIキー検証
"""

import asyncio
import json
import os
import sys
from datetime import datetime
import pytz
from typing import Dict, Any, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class OpenAIAnalyzer:
    """OpenAI GPT分析クライアント"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.console = Console()
        
    async def test_connection(self) -> bool:
        """OpenAI API接続テスト"""
        self.console.print("🔍 OpenAI API接続テスト...")
        
        try:
            # シンプルなテキスト生成でテスト
            response = await self.generate_analysis("Test connection", "USD/JPY", {"rate": 147.69}, test_mode=True)
            
            if response and len(response) > 10:
                self.console.print("✅ OpenAI API接続成功！")
                return True
            else:
                self.console.print("❌ OpenAI API接続失敗")
                return False
                
        except Exception as e:
            self.console.print(f"❌ OpenAI API接続エラー: {str(e)}")
            return False
    
    async def generate_analysis(self, analysis_type: str, currency_pair: str, market_data: Dict[str, Any], test_mode: bool = False) -> Optional[str]:
        """AI分析生成"""
        
        if test_mode:
            prompt = "Say 'OpenAI connection test successful' in Japanese."
        else:
            prompt = self._create_analysis_prompt(analysis_type, currency_pair, market_data)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "あなたは金融市場の専門アナリストです。データに基づいた客観的な分析を提供してください。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    error_text = response.text
                    self.console.print(f"❌ OpenAI API request failed: HTTP {response.status_code}")
                    self.console.print(f"Error: {error_text}")
                    return None
                    
        except Exception as e:
            self.console.print(f"❌ OpenAI API request error: {str(e)}")
            return None
    
    def _create_analysis_prompt(self, analysis_type: str, currency_pair: str, market_data: Dict[str, Any]) -> str:
        """分析プロンプト作成"""
        
        current_time = datetime.now(pytz.timezone("Asia/Tokyo")).strftime("%Y年%m月%d日 %H:%M")
        
        if analysis_type == "technical":
            return f"""
{currency_pair}の技術的分析を行ってください。

現在の市場データ:
- 通貨ペア: {currency_pair}
- 現在レート: {market_data.get('rate', 'N/A')}
- 時刻: {current_time}
- 24時間変動: {market_data.get('change_24h', 'N/A')}%
- 出来高: {market_data.get('volume', 'N/A')}

以下の観点から分析してください:
1. トレンド分析（上昇/下降/横ばい）
2. サポート・レジスタンスレベル
3. 短期的な価格予想（今後6-12時間）
4. リスク要因
5. 推奨取引戦略

分析結果を日本語で、根拠とともに簡潔に提供してください。
"""
        
        elif analysis_type == "fundamental":
            return f"""
{currency_pair}のファンダメンタル分析を行ってください。

現在の市場状況:
- 通貨ペア: {currency_pair}
- 現在レート: {market_data.get('rate', 'N/A')}
- 分析時刻: {current_time}

以下の観点から分析してください:
1. 経済指標の影響
2. 金利政策の動向
3. 地政学的リスク
4. 市場センチメント
5. 中長期的な見通し

分析結果を日本語で、経済的根拠とともに提供してください。
"""
        
        elif analysis_type == "market_summary":
            return f"""
{currency_pair}の市場概況分析を行ってください。

現在の状況:
- 通貨ペア: {currency_pair}
- レート: {market_data.get('rate', 'N/A')}
- 時刻: {current_time}

以下の内容で簡潔にまとめてください:
1. 現在の市場状況（3行程度）
2. 主要な動向（2-3点）
3. 注目ポイント（2点程度）
4. 今後の見通し（短期・中期）

投資家向けの情報として、分かりやすく日本語で提供してください。
"""
        
        else:
            return f"""
{currency_pair}の総合的な市場分析を行ってください。

データ:
- 通貨ペア: {currency_pair}
- レート: {market_data.get('rate', 'N/A')}
- 時刻: {current_time}

技術的・ファンダメンタル両面から分析し、投資判断の参考となる情報を日本語で提供してください。
"""
    
    def display_analysis_result(self, analysis_type: str, currency_pair: str, analysis_text: str, market_data: Dict[str, Any]):
        """分析結果表示"""
        
        # 分析タイプ日本語化
        type_map = {
            "technical": "技術的分析",
            "fundamental": "ファンダメンタル分析", 
            "market_summary": "市場概況",
            "comprehensive": "総合分析"
        }
        
        type_jp = type_map.get(analysis_type, analysis_type)
        
        # 市場データパネル
        market_info = f"""[bold cyan]通貨ペア:[/bold cyan] {currency_pair}
[bold green]現在レート:[/bold green] {market_data.get('rate', 'N/A')}
[bold yellow]時刻:[/bold yellow] {datetime.now(pytz.timezone("Asia/Tokyo")).strftime('%Y-%m-%d %H:%M:%S')}
[bold blue]分析タイプ:[/bold blue] {type_jp}"""
        
        market_panel = Panel.fit(
            market_info,
            title="📊 Market Data",
            border_style="blue"
        )
        
        self.console.print(market_panel)
        self.console.print()
        
        # 分析結果パネル
        analysis_panel = Panel.fit(
            analysis_text,
            title=f"🤖 AI {type_jp}",
            border_style="green"
        )
        
        self.console.print(analysis_panel)


async def test_multiple_analysis_types(analyzer: OpenAIAnalyzer):
    """複数分析タイプテスト"""
    console = Console()
    
    # サンプル市場データ（Alpha Vantageから取得したような形式）
    market_data = {
        "rate": 147.69,
        "change_24h": "+0.25",
        "volume": "High",
        "bid": 147.69,
        "ask": 147.70
    }
    
    analysis_types = [
        ("technical", "技術的分析"),
        ("fundamental", "ファンダメンタル分析"),
        ("market_summary", "市場概況"),
        ("comprehensive", "総合分析")
    ]
    
    console.print("🤖 複数分析タイプテスト...")
    
    for analysis_type, type_name in analysis_types:
        console.print(f"\n🔍 {type_name}を実行中...")
        
        analysis_result = await analyzer.generate_analysis(analysis_type, "USD/JPY", market_data)
        
        if analysis_result:
            analyzer.display_analysis_result(analysis_type, "USD/JPY", analysis_result, market_data)
        else:
            console.print(f"❌ {type_name}の生成に失敗しました")
        
        console.print("\n" + "="*60)
        
        # API制限を考慮した間隔
        await asyncio.sleep(3)


async def test_with_real_market_data(analyzer: OpenAIAnalyzer):
    """実際の市場データでの分析テスト"""
    console = Console()
    
    # Alpha Vantageから実データを取得（簡易版）
    console.print("📊 実際の市場データ取得中...")
    
    alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not alpha_vantage_key or alpha_vantage_key == "demo_key_replace_with_your_key":
        console.print("⚠️ Alpha Vantage APIキーが設定されていません。サンプルデータを使用します。")
        market_data = {
            "rate": 147.69,
            "change_24h": "+0.25",
            "volume": "High"
        }
    else:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://www.alphavantage.co/query",
                    params={
                        "function": "CURRENCY_EXCHANGE_RATE",
                        "from_currency": "USD",
                        "to_currency": "JPY",
                        "apikey": alpha_vantage_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "Realtime Currency Exchange Rate" in data:
                        fx_data = data["Realtime Currency Exchange Rate"]
                        market_data = {
                            "rate": float(fx_data.get("5. Exchange Rate", 0)),
                            "bid": float(fx_data.get("8. Bid Price", 0)),
                            "ask": float(fx_data.get("9. Ask Price", 0)),
                            "last_update": fx_data.get("6. Last Refreshed", "N/A")
                        }
                        console.print("✅ 実際の市場データを取得しました")
                    else:
                        raise Exception("Invalid response format")
                else:
                    raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            console.print(f"⚠️ 市場データ取得失敗: {str(e)}. サンプルデータを使用します。")
            market_data = {
                "rate": 147.69,
                "change_24h": "+0.25",
                "volume": "High"
            }
    
    # 実データでのAI分析
    console.print("🤖 実データによるAI分析実行...")
    
    analysis_result = await analyzer.generate_analysis("comprehensive", "USD/JPY", market_data)
    
    if analysis_result:
        analyzer.display_analysis_result("comprehensive", "USD/JPY", analysis_result, market_data)
    else:
        console.print("❌ AI分析の生成に失敗しました")


async def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI GPT Analysis Test")
    parser.add_argument("--test", choices=["connection", "analysis", "multiple", "real", "all"], 
                       default="connection", help="Test type to run")
    parser.add_argument("--api-key", help="OpenAI API key (or use env var)")
    
    args = parser.parse_args()
    
    # APIキー取得
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == "sk-replace-with-your-openai-key":
        console = Console()
        console.print("❌ OpenAI APIキーが設定されていません")
        console.print("🔧 .envファイルのOPENAI_API_KEYを設定してください")
        console.print("📋 取得方法: https://platform.openai.com/api-keys")
        console.print("💡 形式: sk-...")
        sys.exit(1)
    
    analyzer = OpenAIAnalyzer(api_key)
    
    console = Console()
    console.print("🚀 OpenAI GPT Analysis テスト開始")
    console.print(f"🔑 APIキー: {api_key[:10]}{'*' * 10}")
    console.print(f"🧪 テストタイプ: {args.test}")
    console.print()
    
    if args.test == "connection":
        await analyzer.test_connection()
        
    elif args.test == "analysis":
        market_data = {"rate": 147.69, "change_24h": "+0.25"}
        analysis = await analyzer.generate_analysis("technical", "USD/JPY", market_data)
        if analysis:
            analyzer.display_analysis_result("technical", "USD/JPY", analysis, market_data)
            
    elif args.test == "multiple":
        await test_multiple_analysis_types(analyzer)
        
    elif args.test == "real":
        await test_with_real_market_data(analyzer)
        
    elif args.test == "all":
        # 接続テスト
        success = await analyzer.test_connection()
        if not success:
            console.print("❌ 接続テスト失敗。API設定を確認してください。")
            return
        
        console.print("\n" + "="*50)
        
        # 基本分析テスト
        market_data = {"rate": 147.69, "change_24h": "+0.25"}
        analysis = await analyzer.generate_analysis("market_summary", "USD/JPY", market_data)
        if analysis:
            analyzer.display_analysis_result("market_summary", "USD/JPY", analysis, market_data)
        
        console.print("\n📝 全テストの実行にはAPI制限を考慮してください")
        console.print("🔧 個別テスト: python test_openai.py --test multiple")
        console.print("🔧 実データテスト: python test_openai.py --test real")
    
    console.print("\n✅ OpenAI GPT Analysis テスト完了")


if __name__ == "__main__":
    asyncio.run(main())
