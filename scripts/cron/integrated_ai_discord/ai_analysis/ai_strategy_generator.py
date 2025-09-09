#!/usr/bin/env python3
"""
AI Strategy Generator Module
統合相関分析に基づくAI売買シナリオ生成
"""

import traceback
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from rich.console import Console


class AIStrategyGenerator:
    """AI戦略生成クラス"""

    def __init__(self, openai_key: str, jst_timezone):
        self.openai_key = openai_key
        self.jst = jst_timezone
        self.console = Console()
        self.openai_url = "https://api.openai.com/v1/chat/completions"

    async def generate_integrated_analysis(
        self,
        correlation_data: Dict[str, Any],
        technical_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """統合相関分析に基づくAI売買シナリオ生成"""
        self.console.print("🤖 統合AI戦略分析生成中...")

        if not self.openai_key or self.openai_key == "your_openai_api_key":
            self.console.print("⚠️ OpenAI APIキーが未設定。サンプル分析を使用。")
            return self._generate_sample_integrated_scenario(correlation_data)

        # 現在時刻
        current_time = datetime.now(self.jst).strftime("%Y年%m月%d日 %H:%M JST")

        # 相関データ抽出
        usdjpy_forecast = correlation_data.get("usdjpy_forecast", {})
        usd_analysis = correlation_data.get("usd_analysis", {})
        jpy_analysis = correlation_data.get("jpy_analysis", {})
        currency_data = correlation_data.get("currency_data", {})

        # 各通貨ペアの状況
        usdjpy_data = currency_data.get("USD/JPY", {})
        eurusd_data = currency_data.get("EUR/USD", {})
        gbpusd_data = currency_data.get("GBP/USD", {})
        eurjpy_data = currency_data.get("EUR/JPY", {})
        gbpjpy_data = currency_data.get("GBP/JPY", {})

        # 現在レート取得
        current_rate = usdjpy_data.get("rate", 0)
        day_high = usdjpy_data.get("day_high", current_rate)
        day_low = usdjpy_data.get("day_low", current_rate)

        # テクニカル指標データを文字列化（プロンプト用に簡潔化）
        technical_summary = ""
        if technical_data:

            # 詳細テクニカルサマリーを作成
            technical_summary = self._create_detailed_technical_summary(technical_data)

        # 統合分析プロンプト作成
        prompt = f"""
あなたはプロFXトレーダーです。
通貨相関とテクニカル指標を統合して、USD/JPYの「負けないトレード」を目指した売買シナリオを作成してください。  

【必須条件】  
- 提供された数値データを必ず用いること（N/Aや詳細なしは禁止）。  
- 大局 → 戦術 → 執行 → リスク管理の順で一貫した分析を行うこと。  
- 出力は必ず番号付きリスト（1〜9）。

以下のデータを基に、指示に従ってUSD/JPYの包括的なテクニカル分析を含む売買シナリオを分析してください。

【データ】
分析時刻: {current_time}
現在レート: {current_rate:.4f}
日中高値: {day_high:.4f}
日中安値: {day_low:.4f}
EUR/USD: {eurusd_data.get('rate', 'N/A')} \
({eurusd_data.get('market_change_percent', 'N/A')}%)
GBP/USD: {gbpusd_data.get('rate', 'N/A')} \
({gbpusd_data.get('market_change_percent', 'N/A')}%)
EUR/JPY: {eurjpy_data.get('rate', 'N/A')} \
({eurjpy_data.get('market_change_percent', 'N/A')}%)
GBP/JPY: {gbpjpy_data.get('rate', 'N/A')} \
({gbpjpy_data.get('market_change_percent', 'N/A')}%)

USD分析: {usd_analysis.get('direction', 'N/A')} \
(信頼度{usd_analysis.get('confidence', 'N/A')}%)
JPY分析: {jpy_analysis.get('direction', 'N/A')} \
(信頼度{jpy_analysis.get('confidence', 'N/A')}%)
統合予測: {usdjpy_forecast.get('forecast_direction', 'N/A')} \
(信頼度{usdjpy_forecast.get('forecast_confidence', 'N/A')}%)

テクニカル分析: {usdjpy_forecast.get('technical_bias', {}).get('trend_type', 'N/A')} \
(MACD: {usdjpy_forecast.get('technical_bias', {}).get('macd_value', 'N/A')}, \
RSI: {usdjpy_forecast.get('technical_bias', {}).get('rsi_value', 'N/A')})

{technical_summary}

**上記のテクニカルデータの具体的な数値を必ず使用して分析してください**

【目的】
一日のトレードで 6%の利益達成 を最優先目標とする。
勝率と再現性を重視し、最も実現性の高いシナリオを構築する。
大局 → 戦術 → 執行 → リスク管理 の順で一貫したロジックを維持する。

1. 大局認識（D1・H4）
SMA・MACDを最優先指標とする。
RSI・ADX・ATRは補強指標として使用。
大局方向（上昇/下降/レンジ）を明確に判定。
大局方向と一致するシナリオを「優先シナリオ」として提示し、逆方向は「補助シナリオ」として補足する。

2. 戦術レベル（H1）
サポート＆レジスタンスは必ず現在価格から±50pips以内を選ぶこと。それ以外の水準は提示してはならない。
フィボナッチ38.2%・50%・61.8%・78.6%を重視。
MA20・MA50・ボリンジャーバンド下限/上限との合流点を優先する。
RSI30-50で反発 → ロング条件。
RSI50以下で割れ → ショート条件。

3. 執行レベル（M5）
ローソク足パターン（包み足・ピンバー）で反発/突破を確認。
RSI短期の反転、ATR/ADXでトレンド強度を確認。
条件が揃わない場合はエントリーを見送る。

4. リスク管理
損切り：必ず15〜20pipsに設定する。
利確：必ず40〜50pipsの範囲に設定する。
→ これによりリスクリワード比は必ず1:2以上になる。
利確・損切りを提示した後にRR比を計算し、明示する。
トレード回数：1日2〜3回以内。

5. 通貨相関
USD/JPY基軸。
EUR/USD・GBP/USDとの逆相関を確認。
相関は補助的に扱い、優先はテクニカル分析。

6. 出力形式
出力は必ず番号付きリスト（1〜9）で提示すること。
1. 大局認識：方向性と根拠（優先シナリオを明示）
2. テクニカル状況：MACD・RSI・ATR・ADXの値と解釈
3. サポート&レジスタンス：現在価格から±50pips以内の水準を提示
4. 押し目分析：反発/突破の可能性と根拠
5. ロングシナリオ（優先/補助を明示）：エントリー価格・利確（40〜50pips）・損切り（15〜20pips）・RR比・根拠
6. ショートシナリオ（優先/補助を明示）：エントリー価格・利確（40〜50pips）・損切り（15〜20pips）・RR比・根拠
7. 6%利益達成可能性：
   ・口座残高を円建てで想定し、残高×6%＝必要利益（円）を算出すること
   ・1ロット=1万通貨の場合と1ロット=10万通貨の場合の両方を仮定し、それぞれ必要pips数やロット数を計算すること
   ・必ずレバレッジ25倍を考慮した具体例を含めること
8. 直近の値動き予測：現在価格から上昇しやすいのか、下落しやすいのかを短期足の指標から推定し、簡潔に示すこと
9. 結論：現時点で最も実行可能性が高い方向（ロング or ショート）を一つ選び、理由を添えて提示すること。
   ・優先シナリオ＝推奨シナリオ
   ・補助シナリオ＝条件が揃った場合のみ検討する

【数値表記ルール】
・価格は必ず小数点第3位まで表示する（例：147.000）。
・必ず価格とpips数を明記すること。
・フィボナッチは時間足を明示し、具体的な数値を使用すること。
・数値は下3桁程度に簡略化する（例：MACD=0.089, RSI=50.5）。
・中期トレード（40-50pips利確、15-20pips損切り）を基本とする。
・ショートシナリオでは「価格差の符号」と「損益の符号」が逆になるため、括弧内で両方を表記すること。
  例：
  - ロングTP：価格差 +40.0 pips ／ 損益 +40 pips
  - ロングSL：価格差 -20.0 pips ／ 損益 -20 pips
  - ショートTP：価格差 -40.0 pips ／ 損益 +40 pips
  - ショートSL：価格差 +20.0 pips ／ 損益 -20 pips

【制約】
・合計1000文字以内。
・実行可能な指示を優先する。

"""

        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }

            # プロンプトの長さを確認
            prompt_length = len(prompt)
            self.console.print(f"🔍 プロンプト長: {prompt_length}文字")

            # プロンプト内容をファイルに出力（デバッグ用）
            with open("/tmp/current_prompt.txt", "w", encoding="utf-8") as f:
                f.write(prompt)
            self.console.print(
                "🔍 プロンプト内容を /tmp/current_prompt.txt に出力しました"
            )

            # GPT-4oのChat Completions API設定
            payload = {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,  # GPT-4oではmax_tokensを使用
                "temperature": 0.7,  # GPT-4oではtemperatureを設定可能
                "stop": ["<END>"],  # ストップシーケンスを設定
            }

            # crontab環境でのネットワーク接続問題に対応
            timeout_config = httpx.Timeout(
                connect=10.0,  # 接続タイムアウト
                read=120.0,  # 読み取りタイムアウト（GPT-5対応で延長）
                write=10.0,  # 書き込みタイムアウト
                pool=10.0,  # プールタイムアウト
            )

            # 自動リトライ機能（finish_reason: "length"対策）
            token_limits = [1500, 2000, 2500]  # GPT-4o用のトークン制限

            async with httpx.AsyncClient(
                timeout=timeout_config,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            ) as client:
                for i, max_tokens in enumerate(token_limits):
                    # トークン制限を更新
                    payload["max_tokens"] = max_tokens
                    self.console.print(
                        f"🔄 試行 {i+1}/{len(token_limits)}: max_tokens={max_tokens}"
                    )

                    response = await client.post(
                        self.openai_url, headers=headers, json=payload
                    )

                    if response.status_code == 200:
                        data = response.json()
                        self.console.print(f"🔍 GPT-4o応答データ: {data}")

                        # Chat Completions APIの応答形式
                        choice = data.get("choices", [{}])[0]
                        finish_reason = choice.get("finish_reason", "unknown")
                        analysis = choice.get("message", {}).get("content", "").strip()

                        self.console.print(f"📝 finish_reason: {finish_reason}")
                        self.console.print(f"📝 分析結果の長さ: {len(analysis)}文字")

                        if finish_reason == "length":
                            self.console.print(
                                "⚠️ トークン制限に達しました。再試行します..."
                            )
                            continue  # 次のトークン制限で再試行
                        elif len(analysis) == 0:
                            error_msg = (
                                f"⚠️ GPT-4o応答が空です。finish_reason: {finish_reason}"
                            )
                            self.console.print(error_msg)
                            return f"エラー: {error_msg}"
                        else:
                            self.console.print("✅ 統合AI分析生成成功")
                            return analysis
                    else:
                        self.console.print(
                            f"❌ OpenAI APIエラー: {response.status_code}"
                        )
                        self.console.print(f"エラー詳細: {response.text}")
                        return f"エラー: OpenAI APIエラー {response.status_code}"

                # すべての試行でlengthが返された場合
                return "エラー: 出力が長すぎます。max_tokensをさらに増やしてください。"

        except httpx.ReadTimeout as e:
            error_msg = f"⚠️ OpenAI APIタイムアウト: {str(e)}"
            self.console.print(error_msg)
            return f"エラー: {error_msg}"
        except httpx.ConnectTimeout as e:
            error_msg = f"⚠️ OpenAI API接続タイムアウト: {str(e)}"
            self.console.print(error_msg)
            return f"エラー: {error_msg}"
        except httpx.RequestError as e:
            error_msg = f"⚠️ OpenAI APIリクエストエラー: {str(e)}"
            self.console.print(error_msg)
            return f"エラー: {error_msg}"
        except Exception as e:
            error_details = traceback.format_exc()
            error_msg = f"❌ 統合AI分析生成エラー: {str(e)}"
            self.console.print(error_msg)
            self.console.print(f"詳細: {error_details}")
            return f"エラー: {error_msg}"

    def _create_detailed_technical_summary(self, technical_data: Dict[str, Any]) -> str:
        """各時間足の全指標を詳細にサマリー化"""
        summary_parts = []

        for timeframe in ["D1", "H4", "H1", "M5"]:
            tf_summary = self._extract_timeframe_details(technical_data, timeframe)
            if tf_summary:
                summary_parts.append(
                    f"{timeframe} ({self._get_timeframe_name(timeframe)}): {tf_summary}"
                )

        return f"""
【テクニカルデータ詳細】
{chr(10).join(summary_parts) if summary_parts else 'データなし'}

**上記のテクニカルデータの具体的な数値を必ず使用して分析してください**
"""

    def _get_timeframe_name(self, timeframe: str) -> str:
        """時間足の日本語名を取得"""
        names = {"D1": "Daily", "H4": "4H", "H1": "1H", "M5": "5M"}
        return names.get(timeframe, timeframe)

    def _extract_timeframe_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """特定時間足の詳細情報を抽出"""
        details = []

        # MACD詳細
        macd_details = self._extract_macd_details(technical_data, timeframe)
        if macd_details:
            details.append(macd_details)

        # RSI詳細
        rsi_details = self._extract_rsi_details(technical_data, timeframe)
        if rsi_details:
            details.append(rsi_details)

        # ボリンジャーバンド詳細
        bb_details = self._extract_bb_details(technical_data, timeframe)
        if bb_details:
            details.append(bb_details)

        # 移動平均線詳細
        ma_details = self._extract_ma_details(technical_data, timeframe)
        if ma_details:
            details.append(ma_details)

        # ATR/ADX詳細
        atr_adx_details = self._extract_atr_adx_details(technical_data, timeframe)
        if atr_adx_details:
            details.append(atr_adx_details)

        # フィボナッチ詳細
        fib_details = self._extract_fib_details(technical_data, timeframe)
        if fib_details:
            details.append(fib_details)

        return ", ".join(details) if details else None

    def _extract_macd_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """MACDの詳細情報を抽出"""
        macd_key = f"{timeframe}_MACD"
        if macd_key not in technical_data:
            return None

        macd_data = technical_data[macd_key]
        if "error" in macd_data:
            return None

        macd_line = macd_data.get("macd_line")
        signal_line = macd_data.get("signal_line")
        histogram = macd_data.get("histogram")

        if macd_line is None or signal_line is None:
            return None

        # クロス状態の判定
        cross_status = ""
        if histogram is not None:
            if histogram > 0:
                cross_status = "（ゴールデンクロス）"
            elif histogram < 0:
                cross_status = "（デッドクロス）"
            else:
                cross_status = "（クロス中）"

        # トレンド方向の判定
        trend_direction = ""
        if macd_line > signal_line:
            trend_direction = "上昇"
        elif macd_line < signal_line:
            trend_direction = "下降"
        else:
            trend_direction = "中立"

        histogram_str = f"{histogram:.4f}" if histogram is not None else "N/A"
        return (
            f"MACD: {macd_line:.4f}, シグナル: {signal_line:.4f}, "
            f"ヒストグラム: {histogram_str}, {trend_direction}{cross_status}"
        )

    def _extract_rsi_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """RSIの詳細情報を抽出"""
        rsi_key = f"{timeframe}_RSI_LONG"
        if rsi_key not in technical_data:
            return None

        rsi_data = technical_data[rsi_key]
        if "error" in rsi_data:
            return None

        current_value = rsi_data.get("current_value")
        if current_value is None:
            return None

        # 過買い/過売り判定
        status = ""
        if current_value >= 70:
            status = "（過買い）"
        elif current_value <= 30:
            status = "（過売り）"
        elif current_value > 50:
            status = "（強気）"
        elif current_value < 50:
            status = "（弱気）"
        else:
            status = "（中立）"

        return f"RSI: {current_value:.1f}{status}"

    def _extract_bb_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """ボリンジャーバンドの詳細情報を抽出"""
        bb_key = f"{timeframe}_BB"
        if bb_key not in technical_data:
            return None

        bb_data = technical_data[bb_key]
        if "error" in bb_data:
            return None

        upper_band = bb_data.get("upper_band")
        lower_band = bb_data.get("lower_band")
        middle_band = bb_data.get("middle_band")

        if upper_band is None or lower_band is None or middle_band is None:
            return None

        # バンド幅の計算
        band_width = upper_band - lower_band

        return (
            f"BB: 上限{upper_band:.4f}, 中線{middle_band:.4f}, "
            f"下限{lower_band:.4f}, 幅{band_width:.4f}"
        )

    def _extract_ma_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """移動平均線の詳細情報を抽出"""
        ma_details = []

        # 短期MA
        ma_short_key = f"{timeframe}_MA_SHORT"
        if ma_short_key in technical_data:
            ma_short = technical_data[ma_short_key].get("ma_short")
            if ma_short is not None:
                ma_details.append(f"MA20: {ma_short:.4f}")

        # 中期MA
        ma_medium_key = f"{timeframe}_MA_MEDIUM"
        if ma_medium_key in technical_data:
            ma_medium = technical_data[ma_medium_key].get("ma_medium")
            if ma_medium is not None:
                ma_details.append(f"MA50: {ma_medium:.4f}")

        # 長期MA
        ma_long_key = f"{timeframe}_MA_LONG"
        if ma_long_key in technical_data:
            ma_long = technical_data[ma_long_key].get("ma_long")
            if ma_long is not None:
                ma_details.append(f"MA200: {ma_long:.4f}")

        return ", ".join(ma_details) if ma_details else None

    def _extract_atr_adx_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """ATR/ADXの詳細情報を抽出"""
        details = []

        # ATR
        atr_key = f"{timeframe}_ATR"
        if atr_key in technical_data:
            atr_value = technical_data[atr_key].get("current_value")
            if atr_value is not None:
                details.append(f"ATR(14): {atr_value:.4f}")

        # ADX
        adx_key = f"{timeframe}_ADX"
        if adx_key in technical_data:
            adx_value = technical_data[adx_key].get("current_value")
            if adx_value is not None:
                # トレンド強度の判定
                strength = ""
                if adx_value >= 25:
                    strength = "（強いトレンド）"
                elif adx_value >= 20:
                    strength = "（中程度のトレンド）"
                else:
                    strength = "（弱いトレンド）"
                details.append(f"ADX(14): {adx_value:.1f}{strength}")

        return ", ".join(details) if details else None

    def _extract_fib_details(
        self, technical_data: Dict[str, Any], timeframe: str
    ) -> str:
        """フィボナッチの詳細情報を抽出"""
        fib_key = f"{timeframe}_FIB"
        if fib_key not in technical_data:
            return None

        fib_data = technical_data[fib_key]
        if "error" in fib_data:
            return None

        swing_high = fib_data.get("swing_high")
        swing_low = fib_data.get("swing_low")
        current_position = fib_data.get("current_position", {})
        levels = fib_data.get("levels", {})

        if swing_high is None or swing_low is None:
            return None

        # フィボナッチレベルの詳細情報
        fib_levels = []
        if isinstance(levels, dict):
            # レベルを順序付きで表示
            level_order = [
                "0.0%",
                "23.6%",
                "38.2%",
                "50.0%",
                "61.8%",
                "78.6%",
                "100.0%",
            ]
            for level in level_order:
                if level in levels:
                    price = levels[level]
                    fib_levels.append(f"{level}={price:.4f}")

        # 現在位置の情報
        position_info = ""
        if isinstance(current_position, dict):
            percentage = current_position.get("percentage", "N/A")
            nearest_level = current_position.get("nearest_level", "N/A")
            position_info = f" (現在位置: {percentage}%, 最寄り: {nearest_level})"

        # フィボナッチレベルの情報を組み立て
        fib_info = f"Fib: 高値{swing_high:.4f}, 安値{swing_low:.4f}"
        if fib_levels:
            fib_info += f", レベル: {', '.join(fib_levels)}"
        fib_info += position_info

        return fib_info

    def _generate_sample_integrated_scenario(
        self, correlation_data: Dict[str, Any]
    ) -> str:
        """サンプル統合シナリオ生成（OpenAI APIキー未設定時）"""
        usdjpy_forecast = correlation_data.get("usdjpy_forecast", {})
        usd_analysis = correlation_data.get("usd_analysis", {})
        jpy_analysis = correlation_data.get("jpy_analysis", {})

        current_rate = usdjpy_forecast.get("current_rate", 0)
        strategy_bias = usdjpy_forecast.get("strategy_bias", "NEUTRAL")
        forecast_confidence = usdjpy_forecast.get("forecast_confidence", 0)

        # テクニカル分析結果を取得
        technical_bias = usdjpy_forecast.get("technical_bias", {})
        technical_trend = technical_bias.get("trend_type", "N/A")
        macd_value = technical_bias.get("macd_value", "N/A")
        rsi_value = technical_bias.get("rsi_value", "N/A")

        return f"""
🎯 基本バイアス: {strategy_bias} (信頼度{forecast_confidence}%)

 市場環境
USD/JPY: {current_rate:.4f} (0.00%)
USD強弱: {usd_analysis.get('direction', 'N/A')} ({usd_analysis.get('confidence', 'N/A')}%)
JPY強弱: {jpy_analysis.get('direction', 'N/A')} ({jpy_analysis.get('confidence', 'N/A')}%)

📊 テクニカル分析
・テクニカル評価: {technical_trend}
・MACD: {macd_value} (MACDライン上昇中、シグナルライン追従、ヒストグラム拡大)
・RSI: {rsi_value} (中立)、過熱感なし、反発余地あり
・ATR(14): 0.0234 (中程度のボラティリティ)、トレンド継続可能
・ADX(14): 28.5 (強いトレンド)、方向性明確
・移動平均線: MA200 > MA50 > 現在価格 > MA20 (上昇トレンド継続)
・ボリンジャーバンド: バンド幅拡大中、価格中線付近で調整
・フィボナッチ: H1 38.2% (147.9338) が重要サポート

 エントリー戦略
・大局認識: D1上昇バイアス（MACD: 0.089）+ H4弱気継続（RSI: 46.5）
・戦術レベル: H1 Fib 50%レベル(147.960)での反発を狙う
  📍 根拠: 現在価格147.394から近いH1 Fib 50%レベルでの押し目買い
  📍 ATR(14): 0.023で適度なボラティリティ確保
  📍 ADX(14): 28.5で強いトレンド継続中

・エントリーポイント: 147.200 (押し目買い)
  📍 根拠: H1 Fib 50%レベル + MA20サポート + RSI反発 + MACD上昇
  📍 エントリー条件: 147.200到達後、M5で下ヒゲ＋陽線確認

・利確ポイント: 147.700 (+50pips)
  📍 根拠: H1 Fib 38.2%レベル(148.237) + ボリンジャーバンド上限(148.737)
  📍 計算: 147.200 + 0.500 = 147.700
  📍 pips計算: 147.700 - 147.200 = 0.500 = 50pips

・損切りポイント: 147.000 (-20pips)
  📍 根拠: H1 Fib 61.8%レベル(147.680) + MA20サポート(147.747)
  📍 計算: 147.200 - 0.200 = 147.000
  📍 pips計算: 147.200 - 147.000 = 0.200 = 20pips
  📍 リスクリワード比: 1:2.5 (20pipsリスク vs 50pipsリターン)

⚡ エントリー条件
・147.200到達後、M5（5分足）で下ヒゲ＋陽線パターンを確認
・M5 RSIが50以下で売り圧力を確認（現在48.0）
・H1 SMA20がサポートとして機能していることを確認
・ATR(14)が0.020以上でボラティリティを確保（現在0.023）
・ADX(14)が25以上でトレンド強度を確認（現在28.5）
・MACDが上昇トレンドを維持していることを確認（現在0.089）

🔄 代替案
・MACDデッドクロス: ショート転換
・ボリンジャーバンド収縮: ノートレード

⚠️ リスク管理
・最大損失: 20pips（中期トレード重視）
・撤退条件: RSI 70以上 or MACDデッドクロス or ADX(14) 20未満
・注意点: ボリンジャーバンド収縮時 or ATR(14)急低下時は即座に撤退
・トレーリングストップ: 20pips利益で10pipsに調整
・押し目分析: H1 Fib 50%(147.960)、61.8%(148.360)、78.6%(148.760)での反発ポイント
・ATR(14)分析: 0.023で適度なボラティリティ、急低下時は撤退
・ADX(14)分析: 28.5で強いトレンド、20未満でレンジ相場に注意

※サンプルシナリオ。実際の投資判断は慎重に行ってください。
        """.strip()
