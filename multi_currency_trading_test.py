#!/usr/bin/env python3
"""
Multi-Currency Trading Strategy Test
USD/JPYメイン + 関連通貨ペア分析のテスト
"""

import asyncio
import sys
from datetime import datetime

import pytz

# プロジェクトパスを追加
sys.path.append("/app")

from rich.console import Console

from scripts.cron.real_ai_discord_v2 import RealAIDiscordReporter


async def main():
    """マルチ通貨トレード戦略テスト"""
    console = Console()
    console.print("🎯 Multi-Currency Trading Strategy Test 開始")
    console.print(
        f"⏰ 実行時刻: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
    )
    console.print()

    # 通貨ペア設定（ドル円メイン + 関連通貨）
    currency_pairs = [
        ("USD/JPY", "🎯 メイン売買対象"),
        ("EUR/USD", "📊 ドル分析データ"),
        ("GBP/USD", "📊 ドル分析データ"),
        ("EUR/JPY", "📊 クロス円分析データ"),
        ("GBP/JPY", "📊 クロス円分析データ"),
    ]

    reporter = RealAIDiscordReporter()

    try:
        for currency_pair, role in currency_pairs:
            console.print(f"📊 {currency_pair} 分析開始 ({role})")
            console.print("=" * 50)

            # データ取得
            market_data = await reporter._fetch_real_market_data(currency_pair)
            if not market_data:
                console.print(f"❌ {currency_pair}: データ取得失敗")
                continue

            # 戦略分析生成
            analysis = await reporter._generate_real_ai_analysis(
                currency_pair, market_data
            )
            if not analysis:
                console.print(f"❌ {currency_pair}: 分析生成失敗")
                continue

            # 結果表示
            console.print(f"✅ {currency_pair}: 分析完了")
            console.print("📋 分析結果:")
            console.print(f"[cyan]{analysis}[/cyan]")
            console.print()

            # 少し間隔をあける
            await asyncio.sleep(1)

        console.print("🎉 マルチ通貨戦略テスト完了")

    except Exception as e:
        console.print(f"❌ テストエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
