#!/usr/bin/env python3
"""
4時間足データ取得スクリプト
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def fetch_4h_data():
    """4時間足データを取得して最新20件を表示"""
    try:
        print("📊 4時間足データ取得中...")
        
        # Yahoo Financeから4時間足データを取得
        ticker = yf.Ticker('USDJPY=X')
        hist = ticker.history(period='60d', interval='4h')
        
        if hist.empty:
            print("❌ データが取得できませんでした")
            return
        
        print(f"✅ 取得データ件数: {len(hist)}件")
        print(f"📅 期間: {hist.index[0]} ～ {hist.index[-1]}")
        print(f"💰 最新価格: {hist['Close'].iloc[-1]:.4f}")
        
        print("\n📈 最新20件の4時間足データ:")
        print("=" * 80)
        
        # 最新20件を取得
        latest_20 = hist.tail(20)
        
        for i, (timestamp, row) in enumerate(latest_20.iterrows(), 1):
            print(f"{i:2d}. {timestamp}: O={row['Open']:.4f}, H={row['High']:.4f}, L={row['Low']:.4f}, C={row['Close']:.4f}")
        
        print("=" * 80)
        print(f"✅ 4時間足データ取得完了: {len(latest_20)}件表示")
        
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    fetch_4h_data()
