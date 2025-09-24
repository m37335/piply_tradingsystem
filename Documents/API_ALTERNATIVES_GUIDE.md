# OANDA代替API・データソースガイド

## 📋 目次

1. [OANDAプロコース制限の対処法](#1-oandaプロコース制限の対処法)
2. [代替API・データソース](#2-代替apiデータソース)
3. [Yahoo Finance API（推奨）](#3-yahoo-finance-api推奨)
4. [Alpha Vantage API](#4-alpha-vantage-api)
5. [システム統合方法](#5-システム統合方法)

---

## 1. OANDAプロコース制限の対処法

### 1.1 問題の原因
- OANDAのAPI機能がプロコース（上位口座）に限定されている
- デモ口座では一部のAPI機能が利用できない
- リアルタイムストリーミングが制限されている可能性

### 1.2 対処法
1. **OANDAサポートに問い合わせ**
   - デモ口座でのAPI利用可否を確認
   - プロコースへの移行条件を確認

2. **代替データソースの利用**
   - 無料のAPIサービスを使用
   - 既存のYahoo Finance APIを活用

---

## 2. 代替API・データソース

### 2.1 無料APIサービス

| サービス | 料金 | リアルタイム | 制限 | 推奨度 |
|---------|------|-------------|------|--------|
| Yahoo Finance | 無料 | 15分遅延 | 制限あり | ⭐⭐⭐⭐⭐ |
| Alpha Vantage | 無料 | リアルタイム | 5req/min | ⭐⭐⭐⭐ |
| IEX Cloud | 無料 | リアルタイム | 50万req/月 | ⭐⭐⭐ |
| Polygon.io | 無料 | リアルタイム | 5req/min | ⭐⭐⭐ |

### 2.2 有料APIサービス

| サービス | 料金 | リアルタイム | 制限 | 推奨度 |
|---------|------|-------------|------|--------|
| OANDA | 有料 | リアルタイム | 制限なし | ⭐⭐⭐⭐⭐ |
| Interactive Brokers | 有料 | リアルタイム | 制限なし | ⭐⭐⭐⭐ |
| FXCM | 有料 | リアルタイム | 制限なし | ⭐⭐⭐ |

---

## 3. Yahoo Finance API（推奨）

### 3.1 特徴
- **完全無料**: 料金なし
- **高品質データ**: 信頼性の高い価格データ
- **簡単統合**: 既存システムとの統合が容易
- **制限**: 15分遅延、レート制限あり

### 3.2 実装例

```python
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class YahooFinanceProvider:
    def __init__(self):
        self.symbols = {
            'USDJPY': 'USDJPY=X',
            'EURJPY': 'EURJPY=X',
            'GBPJPY': 'GBPJPY=X'
        }
    
    def get_current_price(self, symbol: str) -> dict:
        """現在価格の取得"""
        try:
            ticker = yf.Ticker(self.symbols.get(symbol, symbol))
            info = ticker.info
            return {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', 0),
                'bid': info.get('bid', 0),
                'ask': info.get('ask', 0),
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"価格取得エラー: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = '1d') -> pd.DataFrame:
        """履歴データの取得"""
        try:
            ticker = yf.Ticker(self.symbols.get(symbol, symbol))
            data = ticker.history(period=period)
            return data
        except Exception as e:
            print(f"履歴データ取得エラー: {e}")
            return pd.DataFrame()
```

### 3.3 リアルタイム監視

```python
import asyncio
import time

class YahooFinanceStream:
    def __init__(self, symbols: list, interval: int = 60):
        self.symbols = symbols
        self.interval = interval
        self.provider = YahooFinanceProvider()
        self.callbacks = []
    
    def add_callback(self, callback):
        """コールバックの追加"""
        self.callbacks.append(callback)
    
    async def start_monitoring(self):
        """監視開始"""
        while True:
            for symbol in self.symbols:
                try:
                    price_data = self.provider.get_current_price(symbol)
                    if price_data:
                        # コールバックの実行
                        for callback in self.callbacks:
                            await callback(price_data)
                except Exception as e:
                    print(f"監視エラー: {e}")
            
            await asyncio.sleep(self.interval)
```

---

## 4. Alpha Vantage API

### 4.1 特徴
- **無料プラン**: 5リクエスト/分
- **リアルタイム**: リアルタイムデータ
- **豊富なデータ**: FX、株式、暗号通貨

### 4.2 実装例

```python
import requests
import time

class AlphaVantageProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.last_request_time = 0
        self.min_interval = 12  # 5req/min = 12秒間隔
    
    def _rate_limit(self):
        """レート制限"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_fx_rate(self, from_currency: str, to_currency: str) -> dict:
        """為替レートの取得"""
        self._rate_limit()
        
        params = {
            'function': 'CURRENCY_EXCHANGE_RATE',
            'from_currency': from_currency,
            'to_currency': to_currency,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Realtime Currency Exchange Rate' in data:
                rate_data = data['Realtime Currency Exchange Rate']
                return {
                    'from_currency': rate_data['1. From_Currency Code'],
                    'to_currency': rate_data['3. To_Currency Code'],
                    'rate': float(rate_data['5. Exchange Rate']),
                    'timestamp': rate_data['6. Last Refreshed']
                }
        except Exception as e:
            print(f"Alpha Vantage API エラー: {e}")
        
        return None
```

---

## 5. システム統合方法

### 5.1 既存システムとの統合

```python
# modules/llm_analysis/providers/yahoo_finance_stream.py
import asyncio
from typing import List, Callable
from datetime import datetime
import yfinance as yf

class YahooFinanceStreamProvider:
    """Yahoo Finance Stream Provider"""
    
    def __init__(self):
        self.symbols = ['USDJPY=X', 'EURJPY=X', 'GBPJPY=X']
        self.callbacks = []
        self.is_running = False
    
    def add_callback(self, callback: Callable):
        """コールバックの追加"""
        self.callbacks.append(callback)
    
    async def start_stream(self):
        """ストリーム開始"""
        self.is_running = True
        while self.is_running:
            for symbol in self.symbols:
                try:
                    # 価格データの取得
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    price_data = {
                        'instrument': symbol,
                        'time': datetime.now(),
                        'bid': info.get('bid', 0),
                        'ask': info.get('ask', 0),
                        'status': 'tradeable',
                        'spread': info.get('ask', 0) - info.get('bid', 0),
                        'mid_price': (info.get('bid', 0) + info.get('ask', 0)) / 2
                    }
                    
                    # コールバックの実行
                    for callback in self.callbacks:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(price_data)
                        else:
                            callback(price_data)
                            
                except Exception as e:
                    print(f"価格取得エラー {symbol}: {e}")
            
            # 60秒間隔で更新
            await asyncio.sleep(60)
    
    def stop_stream(self):
        """ストリーム停止"""
        self.is_running = False
```

### 5.2 OANDAクライアントの修正

```python
# modules/llm_analysis/providers/hybrid_stream_client.py
from .oanda_stream_client import OANDAStreamClient
from .yahoo_finance_stream import YahooFinanceStreamProvider

class HybridStreamClient:
    """ハイブリッドストリームクライアント"""
    
    def __init__(self):
        self.oanda_client = OANDAStreamClient()
        self.yahoo_client = YahooFinanceStreamProvider()
        self.use_oanda = False
    
    async def initialize(self):
        """初期化"""
        # OANDAの接続テスト
        try:
            await self.oanda_client.initialize()
            # アカウント情報の取得テスト
            account_info = await self.oanda_client.get_account_info()
            if account_info:
                self.use_oanda = True
                print("✅ OANDA接続成功")
            else:
                print("⚠️ OANDA接続失敗、Yahoo Financeを使用")
        except Exception as e:
            print(f"⚠️ OANDA接続エラー: {e}")
            print("📊 Yahoo Financeを使用")
    
    async def start_price_stream(self, instruments: List[str]):
        """価格ストリームの開始"""
        if self.use_oanda:
            await self.oanda_client.start_price_stream(instruments)
        else:
            # Yahoo Financeのシンボルに変換
            yahoo_symbols = [self._convert_to_yahoo_symbol(inst) for inst in instruments]
            await self.yahoo_client.start_stream()
    
    def _convert_to_yahoo_symbol(self, oanda_symbol: str) -> str:
        """OANDAシンボルをYahoo Financeシンボルに変換"""
        symbol_map = {
            'USD_JPY': 'USDJPY=X',
            'EUR_JPY': 'EURJPY=X',
            'GBP_JPY': 'GBPJPY=X'
        }
        return symbol_map.get(oanda_symbol, f"{oanda_symbol}=X")
```

---

## 6. 推奨実装手順

### 6.1 段階的移行

1. **Phase 1: Yahoo Finance統合**
   - 既存のYahoo Finance APIを活用
   - リアルタイム監視機能の実装
   - システム統合テスト

2. **Phase 2: ハイブリッドシステム**
   - OANDAとYahoo Financeの自動切り替え
   - フォールバック機能の実装
   - パフォーマンス最適化

3. **Phase 3: OANDA本格運用**
   - プロコースへの移行
   - 本番環境での運用
   - 高度な機能の活用

### 6.2 即座に実装可能な解決策

```bash
# 1. Yahoo Finance統合の実装
cd /app
python -c "
import asyncio
import yfinance as yf
from datetime import datetime

async def test_yahoo_finance():
    print('🧪 Yahoo Finance API テスト')
    
    # USD/JPYの現在価格取得
    ticker = yf.Ticker('USDJPY=X')
    info = ticker.info
    
    print(f'✅ USD/JPY 現在価格: {info.get(\"regularMarketPrice\", \"N/A\")}')
    print(f'✅ Bid: {info.get(\"bid\", \"N/A\")}')
    print(f'✅ Ask: {info.get(\"ask\", \"N/A\")}')
    print(f'✅ 最終更新: {info.get(\"regularMarketTime\", \"N/A\")}')
    
    # 履歴データの取得
    hist = ticker.history(period='1d')
    if not hist.empty:
        latest = hist.iloc[-1]
        print(f'✅ 最新データ: {latest[\"Close\"]:.5f}')

asyncio.run(test_yahoo_finance())
"
```

---

## 7. まとめ

### 7.1 推奨アプローチ
1. **短期**: Yahoo Finance APIを活用したシステム統合
2. **中期**: ハイブリッドシステムの構築
3. **長期**: OANDAプロコースへの移行

### 7.2 メリット
- **即座に実装可能**: 既存のYahoo Finance APIを活用
- **コスト効率**: 無料で高品質なデータを取得
- **柔軟性**: 複数のデータソースに対応
- **信頼性**: フォールバック機能による安定性

このアプローチにより、OANDAのプロコース制限を回避しながら、システムの開発とテストを継続できます。
