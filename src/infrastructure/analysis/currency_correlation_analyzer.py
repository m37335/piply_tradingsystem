#!/usr/bin/env python3
"""
Currency Correlation Analyzer
通貨間相関性を活用したUSD/JPY統合分析システム
"""

import asyncio
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz
from rich.console import Console

# プロジェクトパス追加
sys.path.append("/app")
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class CurrencyCorrelationAnalyzer:
    """通貨間相関分析器"""

    def __init__(self):
        self.console = Console()
        self.yahoo_client = YahooFinanceClient()
        self.jst = pytz.timezone("Asia/Tokyo")

        # 分析対象通貨ペア設定
        self.currency_groups = {
            "main": ["USD/JPY"],  # メイン売買対象
            "usd_strength": ["EUR/USD", "GBP/USD"],  # USD強弱分析
            "jpy_strength": ["EUR/JPY", "GBP/JPY"],  # JPY強弱分析
        }

    async def fetch_all_currency_data(self) -> Dict[str, Dict[str, Any]]:
        """全通貨ペアのデータを一括取得"""
        self.console.print("📊 通貨相関分析用データ取得中...")

        all_pairs = []
        for group_pairs in self.currency_groups.values():
            all_pairs.extend(group_pairs)

        currency_data = {}

        for pair in all_pairs:
            try:
                rates_data = await self.yahoo_client.get_multiple_rates([pair])
                if rates_data and "rates" in rates_data and pair in rates_data["rates"]:
                    currency_data[pair] = rates_data["rates"][pair]
                    self.console.print(f"✅ {pair}: {currency_data[pair]['rate']:.4f}")
                else:
                    self.console.print(f"❌ {pair}: データ取得失敗")
                    currency_data[pair] = None
            except Exception as e:
                self.console.print(f"❌ {pair}: エラー - {str(e)}")
                currency_data[pair] = None

        return currency_data

    def analyze_usd_strength(
        self, currency_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """USD強弱分析"""
        usd_analysis = {
            "strength_score": 0,
            "direction": "neutral",
            "confidence": 0,
            "supporting_pairs": [],
            "conflicting_pairs": [],
            "summary": "",
        }

        try:
            # EUR/USD分析（下落=USD強い）
            eur_usd = currency_data.get("EUR/USD")
            if eur_usd:
                eur_usd_change = eur_usd.get("market_change_percent", 0)
                if eur_usd_change < -0.1:  # 0.1%以上下落
                    usd_analysis["strength_score"] += 1
                    usd_analysis["supporting_pairs"].append(
                        f"EUR/USD下落({eur_usd_change:+.2f}%)"
                    )
                elif eur_usd_change > 0.1:  # 0.1%以上上昇
                    usd_analysis["strength_score"] -= 1
                    usd_analysis["conflicting_pairs"].append(
                        f"EUR/USD上昇({eur_usd_change:+.2f}%)"
                    )

            # GBP/USD分析（下落=USD強い）
            gbp_usd = currency_data.get("GBP/USD")
            if gbp_usd:
                gbp_usd_change = gbp_usd.get("market_change_percent", 0)
                if gbp_usd_change < -0.1:
                    usd_analysis["strength_score"] += 1
                    usd_analysis["supporting_pairs"].append(
                        f"GBP/USD下落({gbp_usd_change:+.2f}%)"
                    )
                elif gbp_usd_change > 0.1:
                    usd_analysis["strength_score"] -= 1
                    usd_analysis["conflicting_pairs"].append(
                        f"GBP/USD上昇({gbp_usd_change:+.2f}%)"
                    )

            # USD強弱判定
            if usd_analysis["strength_score"] >= 1:
                usd_analysis["direction"] = "strong"
                usd_analysis["confidence"] = min(
                    usd_analysis["strength_score"] * 50, 100
                )
            elif usd_analysis["strength_score"] <= -1:
                usd_analysis["direction"] = "weak"
                usd_analysis["confidence"] = min(
                    abs(usd_analysis["strength_score"]) * 50, 100
                )

            # サマリー作成
            if usd_analysis["direction"] == "strong":
                usd_analysis["summary"] = (
                    f"USD強い(スコア:{usd_analysis['strength_score']}) → USD/JPY上昇期待"
                )
            elif usd_analysis["direction"] == "weak":
                usd_analysis["summary"] = (
                    f"USD弱い(スコア:{usd_analysis['strength_score']}) → USD/JPY下落懸念"
                )
            else:
                usd_analysis["summary"] = "USD中立 → USD/JPY方向性不明"

        except Exception as e:
            logger.error(f"USD強弱分析エラー: {str(e)}")
            usd_analysis["summary"] = "USD分析エラー"

        return usd_analysis

    def analyze_jpy_strength(
        self, currency_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """JPY強弱分析"""
        jpy_analysis = {
            "strength_score": 0,
            "direction": "neutral",
            "confidence": 0,
            "supporting_pairs": [],
            "conflicting_pairs": [],
            "summary": "",
        }

        try:
            # EUR/JPY分析（下落=JPY強い）
            eur_jpy = currency_data.get("EUR/JPY")
            if eur_jpy:
                eur_jpy_change = eur_jpy.get("market_change_percent", 0)
                if eur_jpy_change < -0.1:  # 0.1%以上下落
                    jpy_analysis["strength_score"] += 1
                    jpy_analysis["supporting_pairs"].append(
                        f"EUR/JPY下落({eur_jpy_change:+.2f}%)"
                    )
                elif eur_jpy_change > 0.1:  # 0.1%以上上昇
                    jpy_analysis["strength_score"] -= 1
                    jpy_analysis["conflicting_pairs"].append(
                        f"EUR/JPY上昇({eur_jpy_change:+.2f}%)"
                    )

            # GBP/JPY分析（下落=JPY強い）
            gbp_jpy = currency_data.get("GBP/JPY")
            if gbp_jpy:
                gbp_jpy_change = gbp_jpy.get("market_change_percent", 0)
                if gbp_jpy_change < -0.1:
                    jpy_analysis["strength_score"] += 1
                    jpy_analysis["supporting_pairs"].append(
                        f"GBP/JPY下落({gbp_jpy_change:+.2f}%)"
                    )
                elif gbp_jpy_change > 0.1:
                    jpy_analysis["strength_score"] -= 1
                    jpy_analysis["conflicting_pairs"].append(
                        f"GBP/JPY上昇({gbp_jpy_change:+.2f}%)"
                    )

            # JPY強弱判定
            if jpy_analysis["strength_score"] >= 1:
                jpy_analysis["direction"] = "strong"
                jpy_analysis["confidence"] = min(
                    jpy_analysis["strength_score"] * 50, 100
                )
            elif jpy_analysis["strength_score"] <= -1:
                jpy_analysis["direction"] = "weak"
                jpy_analysis["confidence"] = min(
                    abs(jpy_analysis["strength_score"]) * 50, 100
                )

            # サマリー作成
            if jpy_analysis["direction"] == "strong":
                jpy_analysis["summary"] = (
                    f"JPY強い(スコア:{jpy_analysis['strength_score']}) → USD/JPY下落圧力"
                )
            elif jpy_analysis["direction"] == "weak":
                jpy_analysis["summary"] = (
                    f"JPY弱い(スコア:{jpy_analysis['strength_score']}) → USD/JPY上昇支援"
                )
            else:
                jpy_analysis["summary"] = "JPY中立 → USD/JPY方向性への影響軽微"

        except Exception as e:
            logger.error(f"JPY強弱分析エラー: {str(e)}")
            jpy_analysis["summary"] = "JPY分析エラー"

        return jpy_analysis

    def generate_integrated_usdjpy_forecast(
        self,
        usdjpy_data: Dict[str, Any],
        usd_analysis: Dict[str, Any],
        jpy_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """USD/JPY統合予測分析"""

        current_rate = usdjpy_data.get("rate", 0) if usdjpy_data else 0
        current_change = (
            usdjpy_data.get("market_change_percent", 0) if usdjpy_data else 0
        )

        # 相関分析による方向性予測
        correlation_score = 0
        forecast_factors = []

        # USD強弱の影響
        if usd_analysis["direction"] == "strong":
            correlation_score += usd_analysis["confidence"] / 100
            forecast_factors.append(f"USD強化要因({usd_analysis['confidence']}%)")
        elif usd_analysis["direction"] == "weak":
            correlation_score -= usd_analysis["confidence"] / 100
            forecast_factors.append(f"USD弱化要因({usd_analysis['confidence']}%)")

        # JPY強弱の影響（逆相関）
        if jpy_analysis["direction"] == "strong":
            correlation_score -= jpy_analysis["confidence"] / 100
            forecast_factors.append(f"JPY強化要因({jpy_analysis['confidence']}%)")
        elif jpy_analysis["direction"] == "weak":
            correlation_score += jpy_analysis["confidence"] / 100
            forecast_factors.append(f"JPY弱化要因({jpy_analysis['confidence']}%)")

        # 予測方向性決定
        if correlation_score > 0.3:
            forecast_direction = "上昇期待"
            forecast_confidence = min(int(abs(correlation_score) * 100), 90)
            strategy_bias = "LONG"
        elif correlation_score < -0.3:
            forecast_direction = "下落懸念"
            forecast_confidence = min(int(abs(correlation_score) * 100), 90)
            strategy_bias = "SHORT"
        else:
            forecast_direction = "レンジ予想"
            forecast_confidence = 30
            strategy_bias = "NEUTRAL"

        # 現在のトレンドとの整合性チェック
        trend_alignment = "unknown"
        if current_change > 0 and strategy_bias == "LONG":
            trend_alignment = "順行"
        elif current_change < 0 and strategy_bias == "SHORT":
            trend_alignment = "順行"
        elif (current_change > 0 and strategy_bias == "SHORT") or (
            current_change < 0 and strategy_bias == "LONG"
        ):
            trend_alignment = "逆行"
        else:
            trend_alignment = "中立"

        return {
            "current_rate": current_rate,
            "current_change_percent": current_change,
            "correlation_score": correlation_score,
            "forecast_direction": forecast_direction,
            "forecast_confidence": forecast_confidence,
            "strategy_bias": strategy_bias,
            "trend_alignment": trend_alignment,
            "forecast_factors": forecast_factors,
            "summary": f"相関分析: {forecast_direction} (信頼度{forecast_confidence}%) - {trend_alignment}",
        }

    async def perform_integrated_analysis(self) -> Dict[str, Any]:
        """統合通貨相関分析の実行"""
        self.console.print("🔄 統合通貨相関分析開始...")

        try:
            # 全通貨データ取得
            currency_data = await self.fetch_all_currency_data()

            # USD強弱分析
            usd_analysis = self.analyze_usd_strength(currency_data)

            # JPY強弱分析
            jpy_analysis = self.analyze_jpy_strength(currency_data)

            # USD/JPY統合予測
            usdjpy_data = currency_data.get("USD/JPY")
            integrated_forecast = self.generate_integrated_usdjpy_forecast(
                usdjpy_data, usd_analysis, jpy_analysis
            )

            # 統合分析結果
            integrated_analysis = {
                "timestamp": datetime.now(self.jst).isoformat(),
                "currency_data": currency_data,
                "usd_analysis": usd_analysis,
                "jpy_analysis": jpy_analysis,
                "usdjpy_forecast": integrated_forecast,
                "analysis_type": "Integrated Currency Correlation Analysis",
            }

            self.console.print("✅ 統合通貨相関分析完了")
            return integrated_analysis

        except Exception as e:
            logger.error(f"統合分析エラー: {str(e)}")
            self.console.print(f"❌ 統合分析エラー: {str(e)}")
            return {"error": str(e)}

    def display_correlation_analysis(self, analysis: Dict[str, Any]) -> None:
        """相関分析結果の表示"""
        if "error" in analysis:
            self.console.print(f"❌ 分析エラー: {analysis['error']}")
            return

        from rich.panel import Panel
        from rich.table import Table

        # USD/JPY現状
        usdjpy_forecast = analysis["usdjpy_forecast"]
        current_rate = usdjpy_forecast["current_rate"]
        current_change = usdjpy_forecast["current_change_percent"]

        # USD分析結果テーブル
        usd_table = Table(title="💵 USD強弱分析", show_header=True)
        usd_table.add_column("項目", style="cyan")
        usd_table.add_column("結果", style="yellow")

        usd_analysis = analysis["usd_analysis"]
        usd_table.add_row("方向性", usd_analysis["direction"])
        usd_table.add_row("信頼度", f"{usd_analysis['confidence']}%")
        usd_table.add_row(
            "サポート要因", ", ".join(usd_analysis["supporting_pairs"]) or "なし"
        )
        usd_table.add_row(
            "リスク要因", ", ".join(usd_analysis["conflicting_pairs"]) or "なし"
        )

        # JPY分析結果テーブル
        jpy_table = Table(title="💴 JPY強弱分析", show_header=True)
        jpy_table.add_column("項目", style="cyan")
        jpy_table.add_column("結果", style="yellow")

        jpy_analysis = analysis["jpy_analysis"]
        jpy_table.add_row("方向性", jpy_analysis["direction"])
        jpy_table.add_row("信頼度", f"{jpy_analysis['confidence']}%")
        jpy_table.add_row(
            "サポート要因", ", ".join(jpy_analysis["supporting_pairs"]) or "なし"
        )
        jpy_table.add_row(
            "リスク要因", ", ".join(jpy_analysis["conflicting_pairs"]) or "なし"
        )

        # 統合予測テーブル
        forecast_table = Table(title="🎯 USD/JPY統合予測", show_header=True)
        forecast_table.add_column("項目", style="cyan")
        forecast_table.add_column("結果", style="green")

        forecast_table.add_row("現在レート", f"{current_rate:.4f}")
        forecast_table.add_row("現在変動", f"{current_change:+.2f}%")
        forecast_table.add_row("予測方向", usdjpy_forecast["forecast_direction"])
        forecast_table.add_row(
            "予測信頼度", f"{usdjpy_forecast['forecast_confidence']}%"
        )
        forecast_table.add_row("戦略バイアス", usdjpy_forecast["strategy_bias"])
        forecast_table.add_row("トレンド整合", usdjpy_forecast["trend_alignment"])

        # 表示
        self.console.print(usd_table)
        self.console.print()
        self.console.print(jpy_table)
        self.console.print()
        self.console.print(forecast_table)
        self.console.print()

        # 統合サマリー
        summary_text = f"""
📊 **統合分析サマリー**

• USD分析: {usd_analysis['summary']}
• JPY分析: {jpy_analysis['summary']}
• 統合予測: {usdjpy_forecast['summary']}

🎯 **相関要因**: {', '.join(usdjpy_forecast['forecast_factors'])}
        """.strip()

        self.console.print(
            Panel(
                summary_text,
                title="🔍 Currency Correlation Analysis",
                border_style="blue",
            )
        )


async def main():
    """テスト実行"""
    analyzer = CurrencyCorrelationAnalyzer()
    analysis = await analyzer.perform_integrated_analysis()
    analyzer.display_correlation_analysis(analysis)


if __name__ == "__main__":
    asyncio.run(main())
