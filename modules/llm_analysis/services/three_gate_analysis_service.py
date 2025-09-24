#!/usr/bin/env python3
"""
三層ゲート分析サービス

データ収集完了イベントを監視し、三層ゲート式フィルタリングシステムを実行します。
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from ..core.three_gate_engine import ThreeGateEngine, ThreeGateResult
from ...data_persistence.core.database.connection_manager import DatabaseConnectionManager
from ..core.technical_calculator import TechnicalIndicatorCalculator
from ..notification.discord_notifier import DiscordNotifier, DiscordMessage, DiscordEmbed

logger = logging.getLogger(__name__)

# ログフォーマットを設定（モジュール名を非表示）
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
for handler in logging.getLogger().handlers:
    handler.setFormatter(formatter)


class ThreeGateAnalysisService:
    """三層ゲート分析サービス"""
    
    def __init__(self, engine: ThreeGateEngine, connection_manager: DatabaseConnectionManager):
        self.engine = engine
        self.connection_manager = connection_manager
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.discord_notifier = DiscordNotifier()
        self.logger = logging.getLogger(__name__)
        
        # 統計情報
        self.stats = {
            'total_events_processed': 0,
            'total_signals_generated': 0,
            'gate1_pass_count': 0,
            'gate2_pass_count': 0,
            'gate3_pass_count': 0,
            'last_analysis_time': None,
            'last_signal_time': None,
            'start_time': datetime.now(timezone.utc)
        }
    
    async def initialize(self):
        """サービスの初期化"""
        try:
            self.logger.info("🔧 三層ゲート分析サービス初期化開始")
            
            # テクニカル計算器は初期化不要（同期クラス）
            
            # Discord通知システムの初期化
            await self.discord_notifier.initialize()
            
            self.logger.info("✅ 三層ゲート分析サービス初期化完了")
            
        except Exception as e:
            self.logger.error(f"❌ サービス初期化エラー: {e}")
            raise
    
    def _log_service_statistics(self):
        """サービス統計情報の表示"""
        if self.stats['total_events_processed'] > 0:
            uptime = datetime.now(timezone.utc) - self.stats['start_time']
            uptime_hours = uptime.total_seconds() / 3600
            
            gate1_rate = (self.stats['gate1_pass_count'] / self.stats['total_events_processed']) * 100
            gate2_rate = (self.stats['gate2_pass_count'] / self.stats['gate1_pass_count']) * 100 if self.stats['gate1_pass_count'] > 0 else 0
            gate3_rate = (self.stats['gate3_pass_count'] / self.stats['gate2_pass_count']) * 100 if self.stats['gate2_pass_count'] > 0 else 0
            signal_rate = (self.stats['total_signals_generated'] / self.stats['total_events_processed']) * 100
            
            self.logger.info("📊 サービス統計情報:")
            self.logger.info(f"├── 稼働時間: {uptime_hours:.1f}時間")
            self.logger.info(f"├── 総イベント処理数: {self.stats['total_events_processed']:,}件")
            self.logger.info(f"├── GATE 1 通過率: {gate1_rate:.1f}% ({self.stats['gate1_pass_count']}/{self.stats['total_events_processed']})")
            self.logger.info(f"├── GATE 2 通過率: {gate2_rate:.1f}% ({self.stats['gate2_pass_count']}/{self.stats['gate1_pass_count']})")
            self.logger.info(f"├── GATE 3 通過率: {gate3_rate:.1f}% ({self.stats['gate3_pass_count']}/{self.stats['gate2_pass_count']})")
            self.logger.info(f"└── シグナル生成率: {signal_rate:.1f}% ({self.stats['total_signals_generated']}/{self.stats['total_events_processed']})")
    
    async def process_events(self):
        """イベントの処理"""
        try:
            # 未処理のイベントを取得
            events = await self._get_unprocessed_events()
            
            for event in events:
                await self._process_single_event(event)
                
        except Exception as e:
            self.logger.error(f"❌ イベント処理エラー: {e}")
    
    async def process_data_collection_event(self, symbol: str, new_data_count: int):
        """データ収集完了イベントの処理"""
        try:
            self.logger.info(f"🔄 データ収集完了イベント処理: {symbol} - {new_data_count}件")
            
            # 統計情報の更新
            self.stats['total_events_processed'] += 1
            
            # 新しいデータがある場合のみ分析を実行
            if new_data_count > 0:
                # 三層ゲート評価を実行
                await self._execute_three_gate_analysis(symbol)
            else:
                self.logger.debug("ℹ️ 新しいデータがないため、三層ゲート分析をスキップします")
                
        except Exception as e:
            self.logger.error(f"❌ データ収集完了イベント処理エラー: {e}")
    
    async def _execute_three_gate_analysis(self, symbol: str):
        """三層ゲート分析を実行"""
        try:
            self.logger.info(f"🚪 三層ゲート分析開始: {symbol}")
            
            # テクニカル指標を計算
            indicators = await self._calculate_technical_indicators(symbol)
            
            # 三層ゲート評価を実行
            if indicators is None:
                self.logger.warning(f"⚠️ テクニカル指標の計算に失敗: {symbol}")
                return
            result = await self.engine.evaluate(symbol, indicators)
            
            # 統計情報の更新
            self.stats['last_analysis_time'] = datetime.now(timezone.utc)
            
            if result:
                # シグナル生成の処理（データベース保存 + Discord通知）
                await self._handle_signal_generation(result)
                
                # 統計を更新
                self.stats['total_signals_generated'] += 1
                self.stats['last_signal_time'] = datetime.now(timezone.utc)
                
                # ゲート通過統計の更新
                if result.gate1 and result.gate1.valid:
                    self.stats['gate1_pass_count'] += 1
                if result.gate2 and result.gate2.valid:
                    self.stats['gate2_pass_count'] += 1
                if getattr(result, 'gate3', None) and result.gate3.valid:
                    self.stats['gate3_pass_count'] += 1
                
                self.logger.info(f"✅ 三層ゲート分析完了: {symbol} - {result.signal_type} (信頼度: {result.overall_confidence:.2f})")
            else:
                self.logger.debug(f"ℹ️ 三層ゲート分析: {symbol} - シグナル生成なし")
            
            # 50回ごとに統計情報を表示
            if self.stats['total_events_processed'] % 50 == 0:
                self._log_service_statistics()
                
        except Exception as e:
            self.logger.error(f"❌ 三層ゲート分析エラー: {e}")
    
    async def _get_unprocessed_events(self) -> List[Dict[str, Any]]:
        """未処理のイベントを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                result = await conn.fetch("""
                    SELECT id, event_type, symbol, event_data, created_at
                    FROM events 
                    WHERE event_type = 'data_collection_completed' 
                    AND processed = FALSE
                    ORDER BY created_at ASC
                    LIMIT 10
                """)
                
                events = []
                for row in result:
                    events.append({
                        'id': row['id'],
                        'event_type': row['event_type'],
                        'symbol': row['symbol'],
                        'event_data': json.loads(row['event_data']) if row['event_data'] else {},
                        'created_at': row['created_at']
                    })
                
                return events
                
        except Exception as e:
            self.logger.error(f"❌ イベント取得エラー: {e}")
            return []
    
    async def _process_single_event(self, event: Dict[str, Any]):
        """単一イベントの処理"""
        try:
            event_id = event['id']
            symbol = event['symbol']
            event_data = event['event_data']
            
            self.logger.info(f"🔄 イベント処理開始: {symbol} (ID: {event_id})")
            
            # テクニカル指標の計算
            technical_data = await self._calculate_technical_indicators(symbol)
            
            if not technical_data:
                self.logger.warning(f"⚠️ テクニカル指標の計算に失敗: {symbol}")
                await self._mark_event_processed(event_id, success=False)
                return
            
            # 三層ゲート評価の実行
            result = await self.engine.evaluate(symbol, technical_data)
            
            if result:
                # シグナル生成
                await self._handle_signal_generation(result)
                self.stats['total_signals_generated'] += 1
                self.stats['last_signal_time'] = datetime.now(timezone.utc)
                
                self.logger.info(f"🎯 シグナル生成: {symbol} - {result.signal_type} (信頼度: {result.overall_confidence:.2f})")
            else:
                self.logger.info(f"ℹ️ シグナル未生成: {symbol} - 条件未満")
            
            # 統計情報の更新
            self.stats['total_events_processed'] += 1
            self.stats['last_analysis_time'] = datetime.now(timezone.utc)
            
            # イベントを処理済みにマーク
            await self._mark_event_processed(event_id, success=True)
            
        except Exception as e:
            self.logger.error(f"❌ イベント処理エラー: {e}")
            await self._mark_event_processed(event['id'], success=False)
    
    async def _calculate_technical_indicators(self, symbol: str) -> Optional[Dict[str, Any]]:
        """テクニカル指標の計算"""
        try:
            # 各時間足のデータを取得
            timeframes = ['1d', '4h', '1h', '5m']
            all_data = {}
            
            for timeframe in timeframes:
                # 複数のデータポイントを取得（テクニカル指標計算に必要）
                data_list = await self._get_multiple_price_data(symbol, timeframe, limit=250)
                if data_list:
                    # DataFrameとして処理
                    df = pd.DataFrame(data_list)
                    indicators = self.technical_calculator.calculate_all_indicators({timeframe: df})
                    if timeframe in indicators:
                        # 最新の指標値を取得
                        latest_indicators = indicators[timeframe].iloc[-1].to_dict()
                        # 時間足プレフィックスを追加
                        for key, value in latest_indicators.items():
                            all_data[f"{timeframe}_{key}"] = value
            
            return all_data
            
        except Exception as e:
            self.logger.error(f"❌ テクニカル指標計算エラー: {e}")
            return None
    
    async def _get_multiple_price_data(self, symbol: str, timeframe: str, limit: int = 250) -> Optional[List[Dict[str, Any]]]:
        """複数の価格データを取得（テクニカル指標計算用）"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 最新の複数の価格データを取得（時系列順で取得）
                results = await conn.fetch("""
                    SELECT open, high, low, close, volume, timestamp
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = $2
                    ORDER BY timestamp DESC 
                    LIMIT $3
                """, symbol, timeframe, limit)
                
                # 時系列順に並び替え
                results = list(reversed(results))
                
                if results:
                    data_list = []
                    for result in results:
                        data_list.append({
                            'open': result['open'],
                            'high': result['high'],
                            'low': result['low'],
                            'close': result['close'],
                            'volume': result['volume'],
                            'timestamp': result['timestamp']
                        })
                    return data_list
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 複数価格データ取得エラー: {e}")
            return None

    async def _get_price_data(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """価格データの取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 最新の価格データを取得
                result = await conn.fetchrow("""
                    SELECT open, high, low, close, volume, timestamp
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = $2
                    ORDER BY timestamp DESC 
                    LIMIT 200
                """, symbol, timeframe)
                
                if result:
                    return {
                        'open': result['open'],
                        'high': result['high'],
                        'low': result['low'],
                        'close': result['close'],
                        'volume': result['volume'],
                        'timestamp': result['timestamp']
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 価格データ取得エラー: {e}")
            return None
    
    async def _handle_signal_generation(self, result: ThreeGateResult):
        """シグナル生成の処理"""
        try:
            # シグナル情報をデータベースに保存
            await self._save_signal_to_database(result)
            
            # Discord通知の送信（実装予定）
            await self._send_discord_notification(result)
            
        except Exception as e:
            self.logger.error(f"❌ シグナル処理エラー: {e}")
    
    async def _save_signal_to_database(self, result: ThreeGateResult):
        """シグナルをデータベースに保存"""
        try:
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO three_gate_signals (
                        symbol, signal_type, overall_confidence, entry_price, 
                        stop_loss, take_profit, gate1_pattern, gate1_confidence,
                        gate2_pattern, gate2_confidence, gate3_pattern, gate3_confidence,
                        created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """, 
                result.symbol,
                result.signal_type,
                result.overall_confidence,
                result.entry_price,
                result.stop_loss,
                json.dumps(result.take_profit),
                result.gate1.pattern,
                result.gate1.confidence,
                result.gate2.pattern,
                result.gate2.confidence,
                (result.gate3.pattern if getattr(result, 'gate3', None) else 'N/A'),
                (result.gate3.confidence if getattr(result, 'gate3', None) else 0.0),
                result.timestamp
                )
                
        except Exception as e:
            self.logger.error(f"❌ シグナル保存エラー: {e}")
    
    async def _send_discord_notification(self, result: ThreeGateResult):
        """Discord通知の送信"""
        try:
            # シグナル生成時のDiscord通知
            if result.signal_type in ['BUY', 'SELL']:
                # 埋め込みメッセージの作成
                embed = DiscordEmbed(
                    title=f"🎯 三層ゲートシグナル生成",
                    description=f"**{result.symbol}** で **{result.signal_type}** シグナルが生成されました",
                    color=0x00ff00 if result.signal_type == 'BUY' else 0xff0000,
                    fields=[
                        {
                            "name": "📊 信頼度",
                            "value": f"{result.overall_confidence:.2f}",
                            "inline": True
                        },
                        {
                            "name": "💰 エントリー価格",
                            "value": f"{result.entry_price:.5f}",
                            "inline": True
                        },
                        {
                            "name": "🛡️ ストップロス",
                            "value": f"{result.stop_loss:.5f}",
                            "inline": True
                        },
                        {
                            "name": "🎯 テイクプロフィット1",
                            "value": f"{result.take_profit[0]:.5f}" if result.take_profit else "N/A",
                            "inline": True
                        },
                        {
                            "name": "⚖️ リスク",
                            "value": f"{abs(result.entry_price - result.stop_loss):.5f}",
                            "inline": True
                        },
                        {
                            "name": "💎 リワード",
                            "value": f"{abs(result.take_profit[0] - result.entry_price):.5f}" if result.take_profit else "N/A",
                            "inline": True
                        },
                        {
                            "name": "📈 リスクリワード比",
                            "value": f"{abs(result.take_profit[0] - result.entry_price) / abs(result.entry_price - result.stop_loss):.2f}" if result.take_profit and abs(result.entry_price - result.stop_loss) > 0 else "N/A",
                            "inline": True
                        }
                    ],
                    footer={
                        "text": f"三層ゲートシステム | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} JST"
                    }
                )
                
                # メッセージの作成
                message = DiscordMessage(
                    content=f"🚨 **{result.signal_type}シグナル生成** 🚨",
                    embeds=[embed]
                )
                
                # Discord通知の送信
                success = await self.discord_notifier._send_message(message)
                
                if success:
                    self.logger.info(f"✅ Discord通知送信完了: {result.symbol} - {result.signal_type}")
                else:
                    self.logger.error(f"❌ Discord通知送信失敗: {result.symbol} - {result.signal_type}")
                    
        except Exception as e:
            self.logger.error(f"❌ Discord通知エラー: {e}")
    
    async def _mark_event_processed(self, event_id: int, success: bool):
        """イベントを処理済みにマーク"""
        try:
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    UPDATE events 
                    SET processed = TRUE, processed_at = NOW()
                    WHERE id = $1
                """, event_id)
                
        except Exception as e:
            self.logger.error(f"❌ イベントマークエラー: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # データベース接続の確認
            async with self.connection_manager.get_connection() as conn:
                await conn.fetchrow("SELECT 1")
            
            # テクニカル計算器は同期クラスのため、ヘルスチェック不要
            
            return {
                'healthy': True,
                'database_connected': True,
                'technical_calculator': 'available',
                'last_analysis': self.stats['last_analysis_time'],
                'total_events_processed': self.stats['total_events_processed']
            }
            
        except Exception as e:
            self.logger.error(f"❌ ヘルスチェックエラー: {e}")
            return {
                'healthy': False,
                'error': str(e)
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報の取得"""
        return {
            **self.stats,
            'uptime': datetime.now(timezone.utc) - (self.stats['last_analysis_time'] or datetime.now(timezone.utc)),
            'signal_generation_rate': (
                self.stats['total_signals_generated'] / self.stats['total_events_processed'] 
                if self.stats['total_events_processed'] > 0 else 0
            )
        }
    
    async def close(self):
        """サービスの終了"""
        try:
            self.logger.info("🔧 三層ゲート分析サービス終了")
            
            # TechnicalIndicatorCalculatorは同期クラスなのでcloseメソッドは不要
            
            self.logger.info("✅ 三層ゲート分析サービス終了完了")
            
        except Exception as e:
            self.logger.error(f"❌ サービス終了エラー: {e}")


# テスト用のメイン関数
if __name__ == "__main__":
    import asyncio
    
    async def test_service():
        """サービスのテスト"""
        from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
        from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
        from modules.data_persistence.config.settings import DatabaseConfig
        
        # データベース接続の初期化
        db_config = DatabaseConfig()
        connection_manager = DatabaseConnectionManager(
            connection_string=db_config.connection_string
        )
        await connection_manager.initialize()
        
        # エンジンの初期化
        engine = ThreeGateEngine()
        
        # サービスの初期化
        service = ThreeGateAnalysisService(engine, connection_manager)
        await service.initialize()
        
        # ヘルスチェック
        health = await service.health_check()
        print(f"ヘルスチェック: {health}")
        
        # 統計情報
        stats = await service.get_statistics()
        print(f"統計情報: {stats}")
        
        # 終了
        await service.close()
        await connection_manager.close()
    
    # テスト実行
    asyncio.run(test_service())
