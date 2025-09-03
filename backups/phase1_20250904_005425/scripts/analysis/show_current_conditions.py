#!/usr/bin/env python3
"""
現在の条件設定出力スクリプト

RSIエントリー検出器の現在の条件設定を表示します
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv

load_dotenv()


async def show_current_conditions():
    """現在の条件設定を表示"""
    print("=" * 80)
    print("📋 現在のRSIエントリー検出器条件設定")
    print("=" * 80)

    print("\n🔍 1. RSIエントリー検出器の条件...")
    
    # RSIエントリー検出器ファイルを読み込み
    rsi_detector_path = "src/domain/services/alert_engine/rsi_entry_detector.py"
    
    if os.path.exists(rsi_detector_path):
        with open(rsi_detector_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        print("✅ RSIエントリー検出器ファイル: 確認済み")
        
        # 条件を抽出
        if "買いシグナル条件:" in content:
            print("\n📊 買いシグナル条件:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "買いシグナル条件:" in line:
                    j = i + 1
                    while j < len(lines) and lines[j].strip().startswith('-'):
                        print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        if "売りシグナル条件:" in content:
            print("\n📊 売りシグナル条件:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "売りシグナル条件:" in line:
                    j = i + 1
                    while j < len(lines) and lines[j].strip().startswith('-'):
                        print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        # 実際の条件チェックメソッドを確認
        print("\n🔍 2. 実際の条件チェックロジック...")
        
        if "def _check_buy_conditions" in content:
            print("✅ 買い条件チェックメソッド:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "def _check_buy_conditions" in line:
                    j = i + 1
                    while j < len(lines) and "return" not in lines[j]:
                        if "rsi <" in lines[j] or "current_price >" in lines[j] or "ema_12 >" in lines[j]:
                            print(f"   {lines[j].strip()}")
                        j += 1
                    # return文を表示
                    while j < len(lines) and "return" in lines[j]:
                        print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        if "def _check_sell_conditions" in content:
            print("✅ 売り条件チェックメソッド:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "def _check_sell_conditions" in line:
                    j = i + 1
                    while j < len(lines) and "return" not in lines[j]:
                        if "rsi >" in lines[j] or "current_price <" in lines[j] or "ema_12 <" in lines[j]:
                            print(f"   {lines[j].strip()}")
                        j += 1
                    # return文を表示
                    while j < len(lines) and "return" in lines[j]:
                        print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        # 信頼度スコア計算を確認
        print("\n🔍 3. 信頼度スコア計算...")
        
        if "RSIスコア" in content:
            print("✅ RSIスコア計算:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "RSIスコア" in line:
                    j = i + 1
                    while j < len(lines) and j < i + 10:
                        if "rsi <" in lines[j] or "rsi >" in lines[j]:
                            print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        if "EMAスコア" in content:
            print("✅ EMAスコア計算:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "EMAスコア" in line:
                    j = i + 1
                    while j < len(lines) and j < i + 10:
                        if "ema_12 >" in lines[j] or "ema_12 <" in lines[j]:
                            print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        # ボラティリティ条件を確認
        print("\n🔍 4. ボラティリティ条件...")
        
        if "def _is_volatility_normal" in content:
            print("✅ ボラティリティ条件:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "def _is_volatility_normal" in line:
                    j = i + 1
                    while j < len(lines) and "return" not in lines[j]:
                        if "0.01 <=" in lines[j] or "0.10" in lines[j]:
                            print(f"   {lines[j].strip()}")
                        j += 1
                    # return文を表示
                    while j < len(lines) and "return" in lines[j]:
                        print(f"   {lines[j].strip()}")
                        j += 1
                    break
        
        print("\n🔍 5. 更新履歴...")
        print("✅ 最新の更新内容:")
        print("   📊 MACDヒストグラム → EMAの傾きに変更")
        print("   📊 買い条件: RSI < 45（大幅緩和）")
        print("   📊 売り条件: RSI > 55（大幅緩和）")
        print("   📊 データ可用性: 100%（EMAは常に利用可能）")
        
        print("\n🎯 6. 条件設定のまとめ...")
        print("✅ 現在の条件設定:")
        print("   買いシグナル:")
        print("     • RSI < 45（過売り圏）")
        print("     • 価格 > SMA20（上昇トレンド）")
        print("     • EMA12 > EMA26（上昇モメンタム）")
        print("     • ATR: 0.01-0.10（適正ボラティリティ）")
        print("")
        print("   売りシグナル:")
        print("     • RSI > 55（過買い圏）")
        print("     • 価格 < SMA20（下降トレンド）")
        print("     • EMA12 < EMA26（下降モメンタム）")
        print("     • ATR: 0.01-0.10（適正ボラティリティ）")
        
    else:
        print(f"❌ RSIエントリー検出器ファイルが見つかりません: {rsi_detector_path}")


if __name__ == "__main__":
    asyncio.run(show_current_conditions())
