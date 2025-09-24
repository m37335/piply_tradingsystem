"""
Yahoo Finance Stream Client（OANDA代替）

OANDAの認証問題を回避し、Yahoo Finance APIを使用してリアルタイムデータを取得するクライアント。
認証不要で即座に使用可能。
"""

import asyncio
import logging
import yfinance as yf
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

from ..core.scenario_manager import Scenario, Trade, ExitReason, TradeDirection
from ..core.rule_engine import RuleBasedEngine, EntrySignal
from ..notification.discord_notifier import DiscordNotifier


class StreamType(Enum):
    """ストリームタイプ"""
    PRICING = "pricing"
    TRANSACTIONS = "transactions"
    ACCOUNT = "account"


@dataclass
class PriceData:
    """価格データ"""
    instrument: str
    time: datetime
    bid: float
    ask: float
    status: str
    spread: float
    mid_price: float


@dataclass
class TransactionData:
    """取引データ（Yahoo Financeでは使用しない）"""
    transaction_id: str
    type: str
    instrument: str
    units: int
    price: float
    time: datetime


class YahooFinanceStreamClient:
    """Yahoo Finance Stream Client（OANDA代替）"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.callbacks: Dict[str, List[Callable]] = {
            StreamType.PRICING.value: [],
            StreamType.TRANSACTIONS.value: [],
            StreamType.ACCOUNT.value: []
        }
        
        # ルールエンジンとDiscord通知
        self.rule_engine: Optional[RuleBasedEngine] = None
        self.discord_notifier: Optional[DiscordNotifier] = None
        
        # 接続状態
        self.is_connected = False
        self.is_running = False
        
        # シンボルマッピング
        self.symbol_mapping = {
            'USD_JPY': 'USDJPY=X',
            'EUR_JPY': 'EURJPY=X',
            'GBP_JPY': 'GBPJPY=X',
            'AUD_JPY': 'AUDJPY=X',
            'USD_CHF': 'USDCHF=X',
            'EUR_USD': 'EURUSD=X',
            'GBP_USD': 'GBPUSD=X',
            'AUD_USD': 'AUDUSD=X'
        }

    async def initialize(self) -> None:
        """初期化（認証不要）"""
        try:
            # ルールエンジンとDiscord通知の初期化
            self.rule_engine = RuleBasedEngine()
            self.discord_notifier = DiscordNotifier()
            await self.discord_notifier.initialize()
            
            self.logger.info("✅ Yahoo Finance Stream APIクライアント初期化完了（認証不要）")
            
        except Exception as e:
            self.logger.error(f"❌ 初期化エラー: {e}")
            raise

    def add_callback(self, stream_type: StreamType, callback: Callable) -> None:
        """コールバックの追加"""
        if stream_type.value not in self.callbacks:
            self.callbacks[stream_type.value] = []
        self.callbacks[stream_type.value].append(callback)
        self.logger.info(f"✅ コールバック追加: {stream_type.value}")

    async def start_price_stream(self, instruments: List[str]) -> None:
        """
        価格ストリームの開始
        
        Args:
            instruments: 監視する通貨ペアのリスト
        """
        if self.is_running:
            self.logger.warning("⚠️ 価格ストリームは既に実行中です")
            return
        
        self.is_running = True
        self.is_connected = True
        
        self.logger.info(f"🔄 価格ストリーム開始: {instruments}")
        
        try:
            while self.is_running:
                for instrument in instruments:
                    try:
                        # Yahoo Financeシンボルに変換
                        yahoo_symbol = self.symbol_mapping.get(instrument, f"{instrument}=X")
                        
                        # 価格データ取得
                        ticker = yf.Ticker(yahoo_symbol)
                        info = ticker.info
                        
                        if info and 'regularMarketPrice' in info:
                            # 価格データの作成
                            current_price = info.get('regularMarketPrice', 0)
                            bid = info.get('bid', current_price - 0.001)
                            ask = info.get('ask', current_price + 0.001)
                            
                            price_data = PriceData(
                                instrument=instrument,
                                time=datetime.now(timezone.utc),
                                bid=bid,
                                ask=ask,
                                status='tradeable',
                                spread=ask - bid,
                                mid_price=(bid + ask) / 2
                            )
                            
                            # コールバックの実行
                            for callback in self.callbacks[StreamType.PRICING.value]:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(price_data)
                                    else:
                                        callback(price_data)
                                except Exception as e:
                                    self.logger.error(f"❌ コールバックエラー: {e}")
                            
                            self.logger.debug(f"📊 価格更新: {instrument} - {price_data.mid_price:.5f}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ 価格取得エラー {instrument}: {e}")
                
                # 60秒間隔で更新
                await asyncio.sleep(60)
                
        except Exception as e:
            self.logger.error(f"❌ ストリームエラー: {e}")
            self.is_connected = False
        finally:
            self.is_running = False

    async def start_trade_stream(self) -> None:
        """トレードストリームの開始（Yahoo Financeでは使用しない）"""
        self.logger.warning("⚠️ Yahoo Financeではトレードストリームは使用できません")

    async def start_account_stream(self) -> None:
        """アカウントストリームの開始（Yahoo Financeでは使用しない）"""
        self.logger.warning("⚠️ Yahoo Financeではアカウントストリームは使用できません")

    def stop_stream(self) -> None:
        """ストリームの停止"""
        self.is_running = False
        self.is_connected = False
        self.logger.info("🛑 ストリーム停止")

    async def get_current_price(self, instrument: str) -> Optional[PriceData]:
        """現在価格の取得"""
        try:
            yahoo_symbol = self.symbol_mapping.get(instrument, f"{instrument}=X")
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                current_price = info.get('regularMarketPrice', 0)
                bid = info.get('bid', current_price - 0.001)
                ask = info.get('ask', current_price + 0.001)
                
                return PriceData(
                    instrument=instrument,
                    time=datetime.now(timezone.utc),
                    bid=bid,
                    ask=ask,
                    status='tradeable',
                    spread=ask - bid,
                    mid_price=(bid + ask) / 2
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ 現在価格取得エラー {instrument}: {e}")
            return None

    async def close(self) -> None:
        """リソースのクリーンアップ"""
        self.stop_stream()
        
        if self.discord_notifier:
            await self.discord_notifier.close()
        
        self.logger.info("✅ Yahoo Finance Stream APIクライアント終了")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    logging.basicConfig(level=logging.INFO)
    
    client = YahooFinanceStreamClient()
    
    try:
        # 初期化
        await client.initialize()
        
        # コールバックの設定
        def price_callback(price_data: PriceData):
            print(f"📊 価格更新: {price_data.instrument} - {price_data.mid_price:.5f}")
        
        client.add_callback(StreamType.PRICING, price_callback)
        
        # ストリーム開始
        await client.start_price_stream(['USD_JPY', 'EUR_JPY'])
        
    except KeyboardInterrupt:
        print("🛑 テスト中断")
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
