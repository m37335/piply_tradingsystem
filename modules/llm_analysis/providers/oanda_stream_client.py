"""
OANDA Stream API連携（REST API不使用設計）

リアルタイム価格データ取得・売買タイミング通知を行うOANDA Stream APIクライアント。
REST APIは使用せず、Stream APIのみでリアルタイムデータを取得します。
"""

import logging
import asyncio
import aiohttp
import json
import ssl
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, asdict
from enum import Enum
import os
from dotenv import load_dotenv

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
    """取引データ"""
    transaction_id: str
    type: str
    instrument: str
    units: int
    price: float
    time: datetime
    account_id: str
    order_id: Optional[str] = None
    trade_id: Optional[str] = None


@dataclass
class AccountData:
    """アカウントデータ"""
    account_id: str
    balance: float
    unrealized_pl: float
    realized_pl: float
    margin_used: float
    margin_available: float
    open_trades: int
    open_orders: int
    time: datetime


class OANDAStreamClient:
    """OANDA Stream API連携クライアント"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._lock = None
        
        # 環境変数の読み込み
        load_dotenv()
        
        # OANDA設定
        self.account_id = os.getenv('OANDA_ACCOUNT_ID')
        self.access_token = os.getenv('OANDA_ACCESS_TOKEN')
        self.environment = os.getenv('OANDA_ENVIRONMENT', 'practice')  # practice/live
        
        # API URL設定
        if self.environment == 'live':
            self.base_url = "https://api-fxtrade.oanda.com"
            self.stream_url = "https://stream-fxtrade.oanda.com"
        else:
            self.base_url = "https://api-fxpractice.oanda.com"
            self.stream_url = "https://stream-fxpractice.oanda.com"
        
        # セッション
        self.session: Optional[aiohttp.ClientSession] = None
        
        # ストリーム管理
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.stream_callbacks: Dict[str, List[Callable]] = {
            StreamType.PRICING.value: [],
            StreamType.TRANSACTIONS.value: [],
            StreamType.ACCOUNT.value: []
        }
        
        # ルールエンジンとDiscord通知
        self.rule_engine: Optional[RuleBasedEngine] = None
        self.discord_notifier: Optional[DiscordNotifier] = None
        
        # 接続状態
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # 秒

    async def initialize(self) -> None:
        """初期化（Stream APIのみ、REST API不使用設計）"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if self.session is None:
                # SSL設定
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # セッション作成
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=30, connect=10)
                
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers={
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    }
                )
                
                # ルールエンジンとDiscord通知の初期化
                self.rule_engine = RuleBasedEngine()
                self.discord_notifier = DiscordNotifier()
                await self.discord_notifier.initialize()
                
                self.logger.info("✅ OANDA Stream APIクライアント初期化完了（REST API不使用設計）")

    async def start_price_stream(self, instruments: List[str]) -> None:
        """
        価格ストリームの開始
        
        Args:
            instruments: 監視する通貨ペアのリスト
        """
        if not self.account_id or not self.access_token:
            self.logger.error("❌ OANDA認証情報が設定されていません")
            return
        
        try:
            await self.initialize()
            
            # ストリームURLの構築
            instruments_str = ','.join(instruments)
            stream_url = f"{self.stream_url}/v3/accounts/{self.account_id}/pricing/stream"
            params = {
                'instruments': instruments_str,
                'snapshot': 'true'
            }
            
            self.logger.info(f"📡 価格ストリーム開始: {instruments_str}")
            
            # ストリームタスクの開始
            task = asyncio.create_task(self._handle_price_stream(stream_url, params))
            self.active_streams[StreamType.PRICING.value] = task
            
            self.is_connected = True
            self.reconnect_attempts = 0
            
        except Exception as e:
            self.logger.error(f"❌ 価格ストリーム開始エラー: {e}")
            await self._handle_reconnect()

    async def start_transaction_stream(self) -> None:
        """取引ストリームの開始"""
        if not self.account_id or not self.access_token:
            self.logger.error("❌ OANDA認証情報が設定されていません")
            return
        
        try:
            await self.initialize()
            
            # ストリームURLの構築
            stream_url = f"{self.stream_url}/v3/accounts/{self.account_id}/transactions/stream"
            
            self.logger.info("📡 取引ストリーム開始")
            
            # ストリームタスクの開始
            task = asyncio.create_task(self._handle_transaction_stream(stream_url))
            self.active_streams[StreamType.TRANSACTIONS.value] = task
            
        except Exception as e:
            self.logger.error(f"❌ 取引ストリーム開始エラー: {e}")

    async def start_account_stream(self) -> None:
        """アカウントストリームの開始"""
        if not self.account_id or not self.access_token:
            self.logger.error("❌ OANDA認証情報が設定されていません")
            return
        
        try:
            await self.initialize()
            
            # ストリームURLの構築
            stream_url = f"{self.stream_url}/v3/accounts/{self.account_id}/account/stream"
            
            self.logger.info("📡 アカウントストリーム開始")
            
            # ストリームタスクの開始
            task = asyncio.create_task(self._handle_account_stream(stream_url))
            self.active_streams[StreamType.ACCOUNT.value] = task
            
        except Exception as e:
            self.logger.error(f"❌ アカウントストリーム開始エラー: {e}")

    async def _handle_price_stream(self, stream_url: str, params: Dict[str, str]) -> None:
        """価格ストリームの処理"""
        while True:
            try:
                async with self.session.get(stream_url, params=params) as response:
                    if response.status != 200:
                        self.logger.error(f"❌ 価格ストリーム接続エラー: {response.status}")
                        await self._handle_reconnect()
                        return
                    
                    self.logger.info("✅ 価格ストリーム接続成功")
                    
                    async for line in response.content:
                        if line:
                            try:
                                # JSONデータの解析
                                data = json.loads(line.decode('utf-8'))
                                
                                # 価格データの処理
                                if 'type' in data and data['type'] == 'PRICE':
                                    price_data = self._parse_price_data(data)
                                    if price_data:
                                        await self._process_price_data(price_data)
                                
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"⚠️ JSON解析エラー: {e}")
                                continue
                            except Exception as e:
                                self.logger.error(f"❌ 価格データ処理エラー: {e}")
                                continue
                                
            except asyncio.CancelledError:
                self.logger.info("📡 価格ストリーム停止")
                break
            except Exception as e:
                self.logger.error(f"❌ 価格ストリームエラー: {e}")
                await self._handle_reconnect()
                await asyncio.sleep(self.reconnect_delay)

    async def _handle_transaction_stream(self, stream_url: str) -> None:
        """取引ストリームの処理"""
        while True:
            try:
                async with self.session.get(stream_url) as response:
                    if response.status != 200:
                        self.logger.error(f"❌ 取引ストリーム接続エラー: {response.status}")
                        return
                    
                    self.logger.info("✅ 取引ストリーム接続成功")
                    
                    async for line in response.content:
                        if line:
                            try:
                                # JSONデータの解析
                                data = json.loads(line.decode('utf-8'))
                                
                                # 取引データの処理
                                if 'transaction' in data:
                                    transaction_data = self._parse_transaction_data(data['transaction'])
                                    if transaction_data:
                                        await self._process_transaction_data(transaction_data)
                                
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"⚠️ JSON解析エラー: {e}")
                                continue
                            except Exception as e:
                                self.logger.error(f"❌ 取引データ処理エラー: {e}")
                                continue
                                
            except asyncio.CancelledError:
                self.logger.info("📡 取引ストリーム停止")
                break
            except Exception as e:
                self.logger.error(f"❌ 取引ストリームエラー: {e}")
                await asyncio.sleep(self.reconnect_delay)

    async def _handle_account_stream(self, stream_url: str) -> None:
        """アカウントストリームの処理"""
        while True:
            try:
                async with self.session.get(stream_url) as response:
                    if response.status != 200:
                        self.logger.error(f"❌ アカウントストリーム接続エラー: {response.status}")
                        return
                    
                    self.logger.info("✅ アカウントストリーム接続成功")
                    
                    async for line in response.content:
                        if line:
                            try:
                                # JSONデータの解析
                                data = json.loads(line.decode('utf-8'))
                                
                                # アカウントデータの処理
                                if 'account' in data:
                                    account_data = self._parse_account_data(data['account'])
                                    if account_data:
                                        await self._process_account_data(account_data)
                                
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"⚠️ JSON解析エラー: {e}")
                                continue
                            except Exception as e:
                                self.logger.error(f"❌ アカウントデータ処理エラー: {e}")
                                continue
                                
            except asyncio.CancelledError:
                self.logger.info("📡 アカウントストリーム停止")
                break
            except Exception as e:
                self.logger.error(f"❌ アカウントストリームエラー: {e}")
                await asyncio.sleep(self.reconnect_delay)

    def _parse_price_data(self, data: Dict[str, Any]) -> Optional[PriceData]:
        """価格データの解析"""
        try:
            return PriceData(
                instrument=data.get('instrument', ''),
                time=datetime.fromisoformat(data.get('time', '').replace('Z', '+00:00')),
                bid=float(data.get('bids', [{}])[0].get('price', 0)),
                ask=float(data.get('asks', [{}])[0].get('price', 0)),
                status=data.get('status', ''),
                spread=0.0,  # 計算で求める
                mid_price=0.0  # 計算で求める
            )
        except Exception as e:
            self.logger.error(f"❌ 価格データ解析エラー: {e}")
            return None

    def _parse_transaction_data(self, data: Dict[str, Any]) -> Optional[TransactionData]:
        """取引データの解析"""
        try:
            return TransactionData(
                transaction_id=data.get('id', ''),
                type=data.get('type', ''),
                instrument=data.get('instrument', ''),
                units=int(data.get('units', 0)),
                price=float(data.get('price', 0)),
                time=datetime.fromisoformat(data.get('time', '').replace('Z', '+00:00')),
                account_id=data.get('accountID', ''),
                order_id=data.get('orderID'),
                trade_id=data.get('tradeID')
            )
        except Exception as e:
            self.logger.error(f"❌ 取引データ解析エラー: {e}")
            return None

    def _parse_account_data(self, data: Dict[str, Any]) -> Optional[AccountData]:
        """アカウントデータの解析"""
        try:
            return AccountData(
                account_id=data.get('id', ''),
                balance=float(data.get('balance', 0)),
                unrealized_pl=float(data.get('unrealizedPL', 0)),
                realized_pl=float(data.get('realizedPL', 0)),
                margin_used=float(data.get('marginUsed', 0)),
                margin_available=float(data.get('marginAvailable', 0)),
                open_trades=int(data.get('openTradeCount', 0)),
                open_orders=int(data.get('openOrderCount', 0)),
                time=datetime.fromisoformat(data.get('timestamp', '').replace('Z', '+00:00'))
            )
        except Exception as e:
            self.logger.error(f"❌ アカウントデータ解析エラー: {e}")
            return None

    async def _process_price_data(self, price_data: PriceData) -> None:
        """価格データの処理"""
        # スプレッドとミッドプライスの計算
        price_data.spread = price_data.ask - price_data.bid
        price_data.mid_price = (price_data.bid + price_data.ask) / 2
        
        # コールバックの実行
        for callback in self.stream_callbacks[StreamType.PRICING.value]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(price_data)
                else:
                    callback(price_data)
            except Exception as e:
                self.logger.error(f"❌ 価格データコールバックエラー: {e}")
        
        # ルールエンジンでの判定
        if self.rule_engine:
            await self._evaluate_trading_rules(price_data)

    async def _process_transaction_data(self, transaction_data: TransactionData) -> None:
        """取引データの処理"""
        # コールバックの実行
        for callback in self.stream_callbacks[StreamType.TRANSACTIONS.value]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(transaction_data)
                else:
                    callback(transaction_data)
            except Exception as e:
                self.logger.error(f"❌ 取引データコールバックエラー: {e}")
        
        # 取引通知の送信
        if self.discord_notifier:
            await self._send_transaction_notification(transaction_data)

    async def _process_account_data(self, account_data: AccountData) -> None:
        """アカウントデータの処理"""
        # コールバックの実行
        for callback in self.stream_callbacks[StreamType.ACCOUNT.value]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(account_data)
                else:
                    callback(account_data)
            except Exception as e:
                self.logger.error(f"❌ アカウントデータコールバックエラー: {e}")

    async def _evaluate_trading_rules(self, price_data: PriceData) -> None:
        """取引ルールの評価"""
        try:
            # ルールエンジンでの判定
            evaluation_result = await self.rule_engine.evaluate_entry_conditions({
                'instrument': price_data.instrument,
                'price': price_data.mid_price,
                'bid': price_data.bid,
                'ask': price_data.ask,
                'spread': price_data.spread,
                'timestamp': price_data.time
            })
            
            # エントリーシグナルの生成
            if evaluation_result.get('should_enter', False):
                entry_signal = EntrySignal(
                    direction=TradeDirection.BUY if evaluation_result.get('direction') == 'BUY' else TradeDirection.SELL,
                    strategy=evaluation_result.get('strategy', 'unknown'),
                    confidence=evaluation_result.get('confidence', 0.0),
                    entry_price=price_data.mid_price,
                    stop_loss=evaluation_result.get('stop_loss', 0.0),
                    take_profit_1=evaluation_result.get('take_profit_1', 0.0),
                    take_profit_2=evaluation_result.get('take_profit_2', 0.0),
                    take_profit_3=evaluation_result.get('take_profit_3', 0.0),
                    risk_reward_ratio=evaluation_result.get('risk_reward_ratio', 0.0),
                    max_hold_time=evaluation_result.get('max_hold_time', 240),
                    rule_results=evaluation_result.get('rule_results', []),
                    technical_summary=evaluation_result.get('technical_summary', {}),
                    created_at=datetime.now(timezone.utc)
                )
                
                # シナリオの作成と通知
                await self._create_and_notify_scenario(entry_signal, price_data)
                
        except Exception as e:
            self.logger.error(f"❌ 取引ルール評価エラー: {e}")

    async def _create_and_notify_scenario(self, entry_signal: EntrySignal, price_data: PriceData) -> None:
        """シナリオの作成と通知"""
        try:
            # シナリオの作成（実際の実装ではScenarioManagerを使用）
            # ここでは簡易的な実装
            
            # Discord通知の送信
            if self.discord_notifier:
                # エントリーシグナル通知の送信
                await self.discord_notifier.send_entry_signal(
                    trade=None,  # 実際の実装では適切なTradeオブジェクト
                    scenario=None,  # 実際の実装では適切なScenarioオブジェクト
                    entry_snapshot=None  # 実際の実装では適切なMarketSnapshotオブジェクト
                )
                
        except Exception as e:
            self.logger.error(f"❌ シナリオ作成・通知エラー: {e}")

    async def _send_transaction_notification(self, transaction_data: TransactionData) -> None:
        """取引通知の送信"""
        try:
            if self.discord_notifier:
                # 取引完了通知の送信
                await self.discord_notifier.send_error_alert(
                    f"取引完了: {transaction_data.type}",
                    {
                        'instrument': transaction_data.instrument,
                        'units': transaction_data.units,
                        'price': transaction_data.price,
                        'time': transaction_data.time.isoformat()
                    }
                )
                
        except Exception as e:
            self.logger.error(f"❌ 取引通知送信エラー: {e}")

    async def _handle_reconnect(self) -> None:
        """再接続処理"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.error("❌ 最大再接続試行回数に達しました")
            return
        
        self.reconnect_attempts += 1
        self.is_connected = False
        
        self.logger.warning(f"⚠️ 再接続試行 {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        # 既存のストリームを停止
        await self.stop_all_streams()
        
        # 再接続待機
        await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)

    def add_callback(self, stream_type: StreamType, callback: Callable) -> None:
        """コールバックの追加"""
        self.stream_callbacks[stream_type.value].append(callback)
        self.logger.info(f"✅ コールバック追加: {stream_type.value}")

    def remove_callback(self, stream_type: StreamType, callback: Callable) -> None:
        """コールバックの削除"""
        if callback in self.stream_callbacks[stream_type.value]:
            self.stream_callbacks[stream_type.value].remove(callback)
            self.logger.info(f"✅ コールバック削除: {stream_type.value}")

    async def stop_stream(self, stream_type: StreamType) -> None:
        """ストリームの停止"""
        if stream_type.value in self.active_streams:
            task = self.active_streams[stream_type.value]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            del self.active_streams[stream_type.value]
            self.logger.info(f"✅ ストリーム停止: {stream_type.value}")

    async def stop_all_streams(self) -> None:
        """全ストリームの停止"""
        for stream_type in list(self.active_streams.keys()):
            await self.stop_stream(StreamType(stream_type))
        self.is_connected = False
        self.logger.info("✅ 全ストリーム停止")

    async def close(self):
        """リソースのクリーンアップ"""
        await self.stop_all_streams()
        
        if self.session:
            await self.session.close()
            self.session = None
        
        if self.discord_notifier:
            await self.discord_notifier.close()
        
        self.logger.info("OANDAStreamClient closed")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    client = OANDAStreamClient()
    
    try:
        print("🧪 OANDA Stream API連携テスト...")
        
        # 初期化
        await client.initialize()
        print("✅ OANDA Stream APIクライアント初期化完了")
        
        # 設定の確認
        print(f"✅ アカウントID: {client.account_id}")
        print(f"✅ 環境: {client.environment}")
        print(f"✅ ベースURL: {client.base_url}")
        print(f"✅ ストリームURL: {client.stream_url}")
        
        # コールバックの追加
        def price_callback(price_data: PriceData):
            print(f"📊 価格更新: {price_data.instrument} - Bid: {price_data.bid}, Ask: {price_data.ask}")
        
        client.add_callback(StreamType.PRICING, price_callback)
        
        # 価格ストリームの開始（テスト用）
        # await client.start_price_stream(['USD_JPY'])
        
        print("🎉 OANDA Stream API連携テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
