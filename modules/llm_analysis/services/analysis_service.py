#!/usr/bin/env python3
"""
独立した分析サービス

イベントテーブルを監視して、データ収集完了イベントを受信した際に
テクニカル分析とパターン検出を実行します。
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig
from modules.llm_analysis.core.data_preparator import LLMDataPreparator
from modules.llm_analysis.core.rule_engine import RuleBasedEngine
from modules.llm_analysis.core.scenario_manager import ScenarioManager, EntrySignal, TradeDirection
from modules.llm_analysis.notification.discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)


class AnalysisService:
    """独立した分析サービス"""
    
    def __init__(self, symbol: str = "USDJPY=X"):
        self.symbol = symbol
        self.is_running = False
        
        # データベース接続
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        
        # 分析コンポーネント
        self.data_preparator = LLMDataPreparator()
        self.rule_engine = RuleBasedEngine()
        self.scenario_manager = ScenarioManager()
        self.discord_notifier = DiscordNotifier()
        
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。分析サービスを停止します...")
        asyncio.create_task(self.stop())
    
    async def initialize(self):
        """初期化"""
        logger.info("🚀 分析サービスを初期化中...")
        
        try:
            # データベース接続を初期化
            await self.connection_manager.initialize()
            
            # 分析コンポーネントを初期化
            await self.data_preparator.initialize()
            await self.rule_engine.initialize()
            await self.discord_notifier.initialize()
            
            logger.info("✅ 分析サービス初期化完了")
            
        except Exception as e:
            logger.error(f"❌ 分析サービス初期化エラー: {e}")
            raise
    
    async def start(self):
        """分析サービスを開始"""
        if self.is_running:
            logger.warning("⚠️ 分析サービスは既に実行中です")
            return
        
        self.is_running = True
        logger.info("🔄 分析サービス開始 - イベント監視中...")
        
        try:
            while self.is_running:
                try:
                    # 未処理のイベントを取得
                    events = await self._get_unprocessed_events()
                    
                    for event in events:
                        await self._process_event(event)
                    
                    # 5秒間隔でイベントをチェック
                    await asyncio.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ イベント処理エラー: {e}")
                    await asyncio.sleep(10)  # エラー時は10秒待機
                    
        except asyncio.CancelledError:
            logger.info("🛑 分析サービスが停止されました")
        except Exception as e:
            logger.error(f"❌ 分析サービスエラー: {e}")
        finally:
            self.is_running = False
    
    async def stop(self):
        """分析サービスを停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 分析サービスを停止中...")
        self.is_running = False
        
        try:
            await self.connection_manager.close()
            await self.discord_notifier.close()
            logger.info("✅ 分析サービス停止完了")
        except Exception as e:
            logger.error(f"❌ 分析サービス停止エラー: {e}")
    
    async def _get_unprocessed_events(self) -> List[Dict]:
        """未処理のイベントを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                events = await conn.fetch("""
                    SELECT id, event_type, symbol, event_data, created_at
                    FROM events 
                    WHERE event_type = 'data_collection_completed' 
                    AND processed = false 
                    AND symbol = $1
                    ORDER BY created_at
                    LIMIT 10
                """, self.symbol)
                
                return [dict(event) for event in events]
                
        except Exception as e:
            logger.error(f"❌ イベント取得エラー: {e}")
            return []
    
    async def _process_event(self, event: Dict):
        """イベントを処理"""
        try:
            event_id = event['id']
            event_data = json.loads(event['event_data'])
            
            logger.info(f"🔄 イベント処理開始: ID={event_id}, シンボル={event['symbol']}")
            
            # テクニカル分析の実行
            analysis_result = await self._perform_technical_analysis(event['symbol'])
            
            # シナリオの作成（条件合致時）
            if analysis_result and analysis_result.get('conditions_met', False):
                await self._create_scenarios(analysis_result)
            
            # イベントを処理済みにマーク
            await self._mark_event_processed(event_id)
            
            logger.info(f"✅ イベント処理完了: ID={event_id}")
            
        except Exception as e:
            logger.error(f"❌ イベント処理エラー: {e}")
            await self._mark_event_error(event['id'], str(e))
    
    async def _perform_technical_analysis(self, symbol: str) -> Optional[Dict]:
        """テクニカル分析を実行"""
        try:
            logger.info(f"🔍 テクニカル分析開始: {symbol}")
            
            # 分析データの準備
            analysis_data = await self.data_preparator.prepare_analysis_data(
                analysis_type='trend_direction',
                symbol=symbol
            )
            
            if not analysis_data or 'timeframes' not in analysis_data:
                logger.warning(f"⚠️ 分析データの準備に失敗: {symbol}")
                return None
            
            # ルール評価の実行
            evaluation = await self.rule_engine.evaluate_entry_conditions(
                symbol=symbol,
                analysis_type='trend_direction'
            )
            
            # 結果の解析
            conditions_met = False
            signals = []
            confidence = 0.0
            
            if evaluation and len(evaluation) > 0:
                for signal_data in evaluation:
                    if signal_data.get('conditions_met', False):
                        conditions_met = True
                        signals.append(signal_data)
                        confidence = max(confidence, signal_data.get('confidence', 0.0))
            
            result = {
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'conditions_met': conditions_met,
                'signals': signals,
                'confidence': confidence,
                'technical_summary': self._generate_technical_summary(signals)
            }
            
            logger.info(f"📊 分析完了: {symbol} - 条件合致: {conditions_met}, シグナル数: {len(signals)}")
            
            # 分析完了イベントを発行
            await self._publish_analysis_completed_event(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ テクニカル分析エラー: {e}")
            return None
    
    async def _create_scenarios(self, analysis_result: Dict):
        """シナリオを作成"""
        try:
            signals = analysis_result.get('signals', [])
            created_scenarios = []
            
            for signal_data in signals:
                # エントリーシグナルの作成
                entry_signal = EntrySignal(
                    direction=TradeDirection[signal_data['direction'].upper()],
                    strategy=signal_data['strategy_name'],
                    confidence=signal_data['confidence'],
                    entry_price=signal_data.get('entry_price', 0.0),
                    stop_loss=signal_data.get('stop_loss', 0.0),
                    take_profit_1=signal_data.get('take_profit_1', 0.0),
                    take_profit_2=signal_data.get('take_profit_2', 0.0),
                    take_profit_3=signal_data.get('take_profit_3', 0.0),
                    risk_reward_ratio=signal_data.get('risk_reward_ratio', 0.0),
                    max_hold_time=signal_data.get('max_hold_time', 240),
                    rule_results=signal_data.get('rule_results', {}),
                    technical_summary={"summary": analysis_result['technical_summary']},
                    created_at=datetime.now(timezone.utc)
                )
                
                # シナリオの作成
                scenario = await self.scenario_manager.create_scenario(
                    entry_signal=entry_signal,
                    symbol=analysis_result['symbol'],
                    expires_hours=8
                )
                
                created_scenarios.append(scenario.id)
                logger.info(f"✅ シナリオ作成: {scenario.id} - {scenario.strategy}")
                
                # Discord通知
                try:
                    await self.discord_notifier.send_scenario_created(scenario)
                except Exception as e:
                    logger.error(f"❌ Discord通知エラー: {e}")
                
                # シナリオ作成イベントを発行
                await self._publish_scenario_created_event(scenario)
            
            return created_scenarios
            
        except Exception as e:
            logger.error(f"❌ シナリオ作成エラー: {e}")
            return []
    
    def _generate_technical_summary(self, signals: List[Dict]) -> str:
        """テクニカルサマリーの生成"""
        try:
            summary_parts = []
            
            for signal in signals:
                strategy = signal.get('strategy_name', 'Unknown')
                direction = signal.get('direction', 'Unknown')
                confidence = signal.get('confidence', 0.0)
                
                summary_parts.append(f"{strategy}({direction}): {confidence:.1f}%")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"❌ テクニカルサマリー生成エラー: {e}")
            return "サマリー生成エラー"
    
    async def _publish_analysis_completed_event(self, analysis_result: Dict):
        """分析完了イベントを発行（即座に処理済みにマーク）"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # イベントを発行し、即座に処理済みにマーク
                await conn.execute("""
                    INSERT INTO events (event_type, symbol, event_data, processed, processed_at, created_at) 
                    VALUES ('technical_analysis_completed', $1, $2, true, NOW(), NOW())
                """, analysis_result['symbol'], json.dumps(analysis_result))
            
            logger.info(f"📢 分析完了イベントを発行（処理済み）: {analysis_result['symbol']}")
            
        except Exception as e:
            logger.error(f"❌ 分析完了イベント発行エラー: {e}")
    
    async def _publish_scenario_created_event(self, scenario):
        """シナリオ作成イベントを発行"""
        try:
            event_data = {
                "scenario_id": scenario.id,
                "strategy": scenario.strategy,
                "direction": scenario.direction.value,
                "status": scenario.status.value,
                "created_at": scenario.created_at.isoformat(),
                "expires_at": scenario.expires_at.isoformat()
            }
            
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO events (event_type, symbol, event_data, created_at) 
                    VALUES ('scenario_created', $1, $2, NOW())
                """, scenario.symbol, json.dumps(event_data))
            
            logger.info(f"📢 シナリオ作成イベントを発行: {scenario.id}")
            
        except Exception as e:
            logger.error(f"❌ シナリオ作成イベント発行エラー: {e}")
    
    async def _mark_event_processed(self, event_id: int):
        """イベントを処理済みにマーク"""
        try:
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    UPDATE events 
                    SET processed = true, processed_at = NOW() 
                    WHERE id = $1
                """, event_id)
        except Exception as e:
            logger.error(f"❌ イベント処理済みマークエラー: {e}")
    
    async def _mark_event_error(self, event_id: int, error_message: str):
        """イベントにエラーをマーク"""
        try:
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    UPDATE events 
                    SET error_message = $1, retry_count = retry_count + 1
                    WHERE id = $2
                """, error_message, event_id)
        except Exception as e:
            logger.error(f"❌ イベントエラーマークエラー: {e}")


# メイン関数
async def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    service = AnalysisService(symbol="USDJPY=X")
    
    try:
        # 初期化
        await service.initialize()
        
        # サービス開始
        await service.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 キーボード割り込みを受信しました")
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
