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
            # D1分析サマリー
            d1_summary = []
            if "D1_MA_LONG" in technical_data:
                ma_long = technical_data["D1_MA_LONG"].get("ma_long", "N/A")
                if isinstance(ma_long, (int, float)):
                    d1_summary.append(f"MA200: {ma_long:.4f}")

            if "D1_MA_MEDIUM" in technical_data:
                ma_medium = technical_data["D1_MA_MEDIUM"].get("ma_medium", "N/A")
                if isinstance(ma_medium, (int, float)):
                    d1_summary.append(f"MA50: {ma_medium:.4f}")

            if "D1_RSI_LONG" in technical_data:
                rsi_long = technical_data["D1_RSI_LONG"].get("current_value", "N/A")
                if isinstance(rsi_long, (int, float)):
                    d1_summary.append(f"RSI70: {rsi_long:.1f}")

            if "D1_MACD" in technical_data:
                macd_line = technical_data["D1_MACD"].get("macd_line", "N/A")
                if isinstance(macd_line, (int, float)):
                    d1_summary.append(f"MACD: {macd_line:.4f}")

            if "D1_BB" in technical_data:
                bb_upper = technical_data["D1_BB"].get("upper_band", "N/A")
                bb_lower = technical_data["D1_BB"].get("lower_band", "N/A")
                if isinstance(bb_upper, (int, float)) and isinstance(
                    bb_lower, (int, float)
                ):
                    d1_summary.append(
                        f"BB Upper: {bb_upper:.4f}, Lower: {bb_lower:.4f}"
                    )

            # フィボナッチ分析サマリー（D1）
            if "D1_FIB" in technical_data:
                d1_fib = technical_data["D1_FIB"]
                if "error" not in d1_fib:
                    swing_high = d1_fib.get("swing_high", "N/A")
                    swing_low = d1_fib.get("swing_low", "N/A")
                    current_position = d1_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        d1_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # H4分析サマリー
            h4_summary = []
            if "H4_MA_MEDIUM" in technical_data:
                h4_ma_medium = technical_data["H4_MA_MEDIUM"].get("ma_medium", "N/A")
                if isinstance(h4_ma_medium, (int, float)):
                    h4_summary.append(f"MA50: {h4_ma_medium:.4f}")

            if "H4_RSI_LONG" in technical_data:
                h4_rsi_long = technical_data["H4_RSI_LONG"].get("current_value", "N/A")
                if isinstance(h4_rsi_long, (int, float)):
                    h4_summary.append(f"RSI70: {h4_rsi_long:.1f}")

            # フィボナッチ分析サマリー（H4）
            if "H4_FIB" in technical_data:
                h4_fib = technical_data["H4_FIB"]
                if "error" not in h4_fib:
                    swing_high = h4_fib.get("swing_high", "N/A")
                    swing_low = h4_fib.get("swing_low", "N/A")
                    current_position = h4_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        h4_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # H1分析サマリー
            h1_summary = []
            if "H1_MA_SHORT" in technical_data:
                h1_ma_short = technical_data["H1_MA_SHORT"].get("ma_short", "N/A")
                if isinstance(h1_ma_short, (int, float)):
                    h1_summary.append(f"MA20: {h1_ma_short:.4f}")

            if "H1_RSI_LONG" in technical_data:
                h1_rsi_long = technical_data["H1_RSI_LONG"].get("current_value", "N/A")
                if isinstance(h1_rsi_long, (int, float)):
                    h1_summary.append(f"RSI70: {h1_rsi_long:.1f}")

            # フィボナッチ分析サマリー（H1）
            if "H1_FIB" in technical_data:
                h1_fib = technical_data["H1_FIB"]
                if "error" not in h1_fib:
                    swing_high = h1_fib.get("swing_high", "N/A")
                    swing_low = h1_fib.get("swing_low", "N/A")
                    current_position = h1_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        h1_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # M5分析サマリー
            m5_summary = []
            if "M5_MA_SHORT" in technical_data:
                m5_ma_short = technical_data["M5_MA_SHORT"].get("ma_short", "N/A")
                if isinstance(m5_ma_short, (int, float)):
                    m5_summary.append(f"MA20: {m5_ma_short:.4f}")

            if "M5_RSI_LONG" in technical_data:
                m5_rsi_long = technical_data["M5_RSI_LONG"].get("current_value", "N/A")
                if isinstance(m5_rsi_long, (int, float)):
                    m5_summary.append(f"RSI70: {m5_rsi_long:.1f}")

            # フィボナッチ分析サマリー（M5）
            if "M5_FIB" in technical_data:
                m5_fib = technical_data["M5_FIB"]
                if "error" not in m5_fib:
                    swing_high = m5_fib.get("swing_high", "N/A")
                    swing_low = m5_fib.get("swing_low", "N/A")
                    current_position = m5_fib.get("current_position", {})
                    if isinstance(swing_high, (int, float)) and isinstance(
                        swing_low, (int, float)
                    ):
                        position_info = ""
                        if isinstance(current_position, dict):
                            percentage = current_position.get("percentage", "N/A")
                            nearest_level = current_position.get("nearest_level", "N/A")
                            position_info = (
                                f" (現在位置: {percentage}%, 最寄り: {nearest_level})"
                            )
                        m5_summary.append(
                            f"Fib High: {swing_high:.4f}, "
                            f"Low: {swing_low:.4f}{position_info}"
                        )

            # 統合サマリー
            technical_summary = f"""
【テクニカルデータ詳細】
D1 (Daily): {', '.join(d1_summary) if d1_summary else 'データなし'}
H4 (4H): {', '.join(h4_summary) if h4_summary else 'データなし'}
H1 (1H): {', '.join(h1_summary) if h1_summary else 'データなし'}
M5 (5M): {', '.join(m5_summary) if m5_summary else 'データなし'}

**上記のテクニカルデータの具体的な数値を必ず使用して分析してください**
"""

        # 統合分析プロンプト作成
        prompt = f"""
あなたはプロFXトレーダーです。
通貨間の相関性とテクニカル指標を活用した統合分析に基づいて、USD/JPYの「負けないトレード」を目指した売買シナリオを作成してください。

**重要**: 以下に提供されるテクニカルデータの具体的な数値を必ず使用して分析してください。
「詳細なし」や「N/A」ではなく、実際の数値で具体的な分析を行ってください。

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

{correlation_data}

{technical_summary}

【指示】
与えられたデータを元に、以下の為替トレード売買シナリオ構築プロセスに従って、売買シナリオを作成してください：

為替トレード売買シナリオ構築プロセス
1. 大局認識（戦略フレームの決定）
時間軸：D1（日足）
・**移動平均線：SMA200・SMA50の傾きと位置関係**で「長期トレンド」を判定
SMA200 > 価格 → 長期下落圧力
SMA50がSMA200を下抜け → デッドクロス → 売り優勢
・**MACD（D1限定）**
MACD < 0 & デッドクロス → 下落バイアス
MACD > 0 & ゴールデンクロス → 上昇バイアス
・**RSI（長期：70/30）**
70以上 → 過熱買い圏
30以下 → 過熱売り圏
・**フィボナッチ（90日）**
現在値が 61.8% or 38.2% に位置 → 大局のサポレジを特定
・**MACD × RSI トレンド評価基準**
1. 強い上昇トレンド
   - MACD > 0（大きくプラス、上昇傾き）
   - RSI > 60〜70
   - 評価：上昇方向が強い、順張り買い有効
   - 戦略：押し目買い、ブレイク狙い
2. 弱い上昇トレンド
   - MACD > 0（小幅プラス）
   - RSI 50〜60
   - 評価：上昇優勢だが勢い不足、レンジ上抜け待ち
   - 戦略：小ロット買い、慎重に追随
3. 中立（レンジ）
   - MACD ≈ 0（±0.1以内）
   - RSI 45〜55
   - 評価：明確な方向感なし、もみ合い
   - 戦略：ノートレ or レンジ逆張り
4. 弱い下降トレンド
   - MACD < 0（小幅マイナス）
   - RSI 40〜45
   - 評価：下落寄りだが勢い不足、方向感待ち
   - 戦略：戻り売り準備、慎重に
5. 強い下降トレンド
   - MACD < 0（大きくマイナス、下降傾き）
   - RSI < 40〜30
   - 評価：下落方向が強い、順張り売り有効
   - 戦略：戻り売り、ブレイク狙い
6. 売られすぎ／買われすぎ局面
   - MACDの方向問わず
   - RSI > 70（買われすぎ） or RSI < 30（売られすぎ）
   - 評価：トレンド加速か反転の分岐点
   - 戦略：利確、逆張り短期狙い

👉 この段階で「基本は買い目線か売り目線か」を決定

2. 中期の方向性とシナリオ候補
時間軸：H4（4時間足）
・**SMA20・SMA50の位置関係**
SMA20 < SMA50 & 価格も下 → 下落トレンド確認
逆なら上昇トレンド
・**ボリンジャーバンド（20,2）**
バンドウォーク中 → トレンド継続
バンド収縮 → ブレイク待ち
・**RSI（14, 70/30）**
30割れ → 下落トレンド中の利確・反発候補
50下回り継続 → 弱気継続
・**フィボ（7日）**
38.2%戻し → 押し目 or 戻り目ゾーン
61.8%戻し → 最終反発ゾーン
👉 ここで「売りならどの戻りを叩くか／買いならどの押し目を拾うか」を決める

3. 戦術レベル（短期ゾーン特定）
時間軸：H1（1時間足）
・**直近高値・安値の水平ライン**を引く（サポレジ）
・**RSI（14）**でダイバージェンス有無をチェック
価格は安値更新してるのにRSIは下げてない → 反発サイン
・**ボリンジャーバンド**で±2σタッチ→反発かブレイク狙い
👉 H1で「ゾーン」を決める（例：147.60で売り、147.30割れで追随など）

4. 執行レベル（エントリー/イグジットの判断）
時間軸：M5（5分足）
・**エントリー条件（重要）**
戻り売り：H1で決めたレジスタンスゾーン到達 → M5で上ヒゲ＋陰線確認
押し目買い：サポートゾーン到達 → M5で下ヒゲ＋陽線確認
・**RSI短期（30以下・70以上）**で反発タイミングを精査
・**移動平均SMA20（M5）**を短期のトレンドガイドに使う
👉 ここで具体的にエントリーする

**重要**: 単純な価格到達ではなく、M5での具体的なローソク足パターン確認が必要

5. リスク管理（中期トレード重視）
・**損切り**：直近の高値/安値の外側に置く（15-20pips程度）
・**利確**：30-50pipsを基本とする中期トレード
・**RR比（リスクリワード）**1:2以上を目標
・**トレーリングストップ**：20pips程度の利益が出たら10pips程度に調整

6. 通貨相関で補強
USD/JPYをメインに、EUR/USD・GBP/USDでドルの強弱を確認
EUR/JPY・GBP/JPYで円の強弱をクロスチェック
👉 「ドルが弱いのか／円が強いのか」を切り分けてシナリオの信頼度を補強

7. 時間軸優先度分析（重要）
・**中短期（H4/H1）の現在の値動きを最優先**
・**長期（D1）は参考情報として扱う**
・**両者の関係性を分析**：
  - 一致している場合：強いトレンド
  - 乖離している場合：中短期優先、長期は参考
  - 中立の場合：レンジ相場
・**トレード判断**：
  - 中短期上昇 → 短期買い優先
  - 中短期下落 → 短期売り優先
  - 長期シナリオは参考情報として扱う

【出力形式】
売買シナリオ出力フォーマット
1. 大局認識（環境認識）
時間軸：日足（D1）・4時間足（H4）
トレンド方向（上昇／下降／レンジ）
**必ず提供されたテクニカルデータの具体的な数値を使用してください**
- MACD: 提供されたMACD値を明記
- SMA200/50の位置関係: 提供されたMA200、MA50の値と現在価格の関係を具体的に分析
- フィボナッチ主要レベル: 提供されたFib High/Lowの値を使用

2. 現在のテクニカル状況
**提供されたテクニカルデータの具体的な数値を必ず使用してください**
- RSI: 提供されたRSI値を明記し、状態を分析
- ボリンジャーバンド: 提供されたBB Upper/Lowerの値と現在価格の位置関係を具体的に分析
- 移動平均線との関係: 提供されたMA20、MA50、MA200の値と現在価格の関係を具体的に分析
- ローソク足パターン: 価格データから分析

3. 時間軸別分析（重要）
✅ 中短期（H4/H1）の現在の値動き
- 上昇/下落/中立の判断と具体的な根拠
- 連続陽線/陰線、SMA位置関係、RSI動向など

✅ 長期（D1）の将来シナリオ
- 上昇/下落/中立の可能性と具体的な根拠
- フィボナッチ、長期RSI、MA200/50との関係など

✅ 時間軸の関係性
- 一致/乖離/中立の判断
- トレード優先度の決定理由

✅ トレード判断
- 中短期の方向性に基づく具体的な方針
- 長期シナリオの参考としての扱い方

4. サポート & レジスタンス
**提供されたデータの具体的な数値を使用してください**
- 水平ライン: 直近高値・安値の具体的な価格
- 移動平均線: 提供されたMA20、MA50、MA200の具体的な価格
- フィボナッチレベル: 提供されたFib High/Lowから計算された具体的な価格
- 心理的節目: 147.00、148.00など

5. シナリオ分岐
シナリオ①（本命）：具体的な価格で記述
シナリオ②（サブ）：具体的な価格で記述
条件を「もし〜なら」で明確に書く

6. エントリーポイント
具体的な価格帯
根拠（提供されたテクニカルデータの具体的な数値を参照）

**M5（5分足）でのエントリー条件**
- 戻り売り：H1レジスタンスゾーン到達後、M5で上ヒゲ＋陰線確認
- 押し目買い：H1サポートゾーン到達後、M5で下ヒゲ＋陽線確認
- RSI短期（30以下・70以上）での反発タイミング確認
- M5 SMA20との位置関係確認
- 具体的なエントリータイミングの説明

7. 利確・損切り
利確目標：30-50pipsを基本とする中期トレード（具体的な価格とpips数を必ず明記）
損切りライン：15-20pips程度（具体的な価格とpips数を必ず明記）
リスクリワード比（RRR）：最低 1:2 を目標

8. 通貨相関チェック
USD/JPY と EUR/USD・GBP/USD の相関
クロス円（EUR/JPY・GBP/JPY）で JPY 強弱確認
→ シナリオの信頼度補強

【重要】
- 提供されたテクニカルデータの具体的な数値を必ず使用してください
- 「詳細なし」や「N/A」ではなく、実際の数値で分析してください
- 各指標の具体的な値と現在価格の関係を明確に説明してください

【制約】
・合計1000文字以内
・数値を明確に表示。ただし、小数点以下は3桁まで表示。価格（例：145.230）とpips数を必ず明記。
・実行可能な指示を優先
・エントリー条件は自然な文章で記述（箇条書き禁止）
・中期トレード（30-50pips）を基本とする
・損切りは15-20pips程度に設定
・**M5での具体的なローソク足パターン確認を必ず含める**
・単純な価格到達ではなく、M5でのエントリー条件を明確に説明
"""

        try:
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,  # 統合分析対応（トークン制限緩和）
                "temperature": 0.7,
            }

            # crontab環境でのネットワーク接続問題に対応
            timeout_config = httpx.Timeout(
                connect=10.0,  # 接続タイムアウト
                read=60.0,  # 読み取りタイムアウト
                write=10.0,  # 書き込みタイムアウト
                pool=10.0,  # プールタイムアウト
            )

            async with httpx.AsyncClient(
                timeout=timeout_config,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            ) as client:
                response = await client.post(
                    self.openai_url, headers=headers, json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    analysis = data["choices"][0]["message"]["content"].strip()
                    self.console.print("✅ 統合AI分析生成成功")
                    return analysis
                else:
                    self.console.print(f"❌ OpenAI APIエラー: {response.status_code}")
                    self.console.print(f"エラー詳細: {response.text}")
                    return None

        except httpx.ReadTimeout as e:
            self.console.print(f"⚠️ OpenAI APIタイムアウト: {str(e)}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)
        except httpx.ConnectTimeout as e:
            self.console.print(f"⚠️ OpenAI API接続タイムアウト: {str(e)}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)
        except httpx.RequestError as e:
            self.console.print(f"⚠️ OpenAI APIリクエストエラー: {str(e)}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)
        except Exception as e:
            error_details = traceback.format_exc()
            self.console.print(f"❌ 統合AI分析生成エラー: {str(e)}")
            self.console.print(f"詳細: {error_details}")
            self.console.print("📝 サンプル分析を生成します")
            return self._generate_sample_integrated_scenario(correlation_data)

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
・移動平均線: MA200 > MA50 > 現在価格 > MA20 (上昇トレンド継続)
・ボリンジャーバンド: バンド幅拡大中、価格中線付近で調整
・フィボナッチ: H1 38.2% (147.9338) が重要サポート

 エントリー戦略
・エントリーポイント: {current_rate - 0.20:.4f}
  📍 根拠: H1 Fib 38.2% + RSI反発 + MA20サポート + MACD上昇
  📍 計算: {current_rate:.4f} - 0.200 = {current_rate - 0.20:.4f}

・利確ポイント: {current_rate + 0.40:.4f} (+40pips)
  📍 根拠: H1 Fib 50% + ボリンジャーバンド上限
  📍 計算: {current_rate - 0.20:.4f} + 0.400 = {current_rate + 0.40:.4f}

・損切りポイント: {current_rate - 0.40:.4f} (-20pips)
  📍 根拠: H1 Fib 61.8% + MA20下抜け
  📍 計算: {current_rate - 0.20:.4f} - 0.200 = {current_rate - 0.40:.4f}

⚡ エントリー条件
{current_rate - 0.20:.4f}付近でH1サポートを確認後、M5（5分足）で下ヒゲ＋陽線パターンを確認。
RSIが50以下で反発を確認し、M5 SMA20がサポートとして機能していることを確認してからエントリー。
MACDが上昇トレンドを維持している状況でのみ実行してください。

🔄 代替案
・MACDデッドクロス: ショート転換
・ボリンジャーバンド収縮: ノートレード

⚠️ リスク管理
・最大損失: 20pips（中期トレード重視）
・撤退条件: RSI 70以上 or MACDデッドクロス
・注意点: ボリンジャーバンド収縮時は即座に撤退
・トレーリングストップ: 20pips利益で10pipsに調整

※サンプルシナリオ。実際の投資判断は慎重に行ってください。
        """.strip()
