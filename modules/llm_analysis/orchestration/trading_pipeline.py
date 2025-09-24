"""
売買パイプライン統合システム

Yahoo Finance Stream API、ルールエンジン、シナリオ管理、Discord通知を統合した
完全自動化されたルールベース売買システム。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..providers.yahoo_finance_stream_client import (
    YahooFinanceStreamClient, 
    StreamType, 
    PriceData
)
from ..core.rule_engine import RuleBasedEngine, EntrySignal, TradeDirection
from ..core.scenario_manager import ScenarioManager, Scenario, ScenarioStatus
from ..core.data_preparator import LLMDataPreparator
from ..notification.discord_notifier import DiscordNotifier


@dataclass
class TradingConfig:
    """売買設定"""
    symbols: List[str]
    update_interval_seconds: int = 60
    max_scenarios: int = 10
    enable_notifications: bool = True
    enable_auto_trading: bool = False  # 現在は通知のみ


class TradingPipeline:
    """売買パイプライン統合システム"""
    
    def __init__(self, config: TradingConfig):
        """初期化"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # コンポーネントの初期化
        self.stream_client = YahooFinanceStreamClient()
        self.rule_engine = RuleBasedEngine()
        self.scenario_manager = ScenarioManager()
        self.data_preparator = LLMDataPreparator()
        self.discord_notifier = DiscordNotifier()
        
        # 状態管理
        self.is_running = False
        self.active_scenarios: Dict[str, Scenario] = {}
        self.last_prices: Dict[str, PriceData] = {}
        
    async def initialize(self) -> None:
        """システムの初期化"""
        try:
            self.logger.info("🚀 売買パイプライン初期化開始")
            
            # 各コンポーネントの初期化
            await self.stream_client.initialize()
            await self.data_preparator.initialize()
            await self.discord_notifier.initialize()
            
            # 価格更新コールバックの設定
            self.stream_client.add_callback(StreamType.PRICING, self._on_price_update)
            
            self.logger.info("✅ 売買パイプライン初期化完了")
            
        except Exception as e:
            self.logger.error(f"❌ 初期化エラー: {e}")
            raise
    
    async def start(self) -> None:
        """パイプラインの開始"""
        if self.is_running:
            self.logger.warning("⚠️ パイプラインは既に実行中です")
            return
        
        self.is_running = True
        self.logger.info("🔄 売買パイプライン開始")
        
        try:
            # 価格ストリームの開始
            await self.stream_client.start_price_stream(self.config.symbols)
            
        except Exception as e:
            self.logger.error(f"❌ パイプラインエラー: {e}")
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """パイプラインの停止"""
        self.is_running = False
        
        # ストリームの停止
        self.stream_client.stop_stream()
        
        # リソースのクリーンアップ
        await self.stream_client.close()
        await self.data_preparator.connection_manager.close()
        await self.discord_notifier.close()
        
        self.logger.info("🛑 売買パイプライン停止")
    
    async def _on_price_update(self, price_data: PriceData) -> None:
        """価格更新時のコールバック"""
        try:
            # 価格データの保存
            self.last_prices[price_data.instrument] = price_data
            
            self.logger.debug(f"📊 価格更新: {price_data.instrument} - {price_data.mid_price:.5f}")
            
            # ルール評価の実行
            await self._evaluate_rules(price_data)
            
            # アクティブシナリオの監視
            await self._monitor_scenarios(price_data)
            
        except Exception as e:
            self.logger.error(f"❌ 価格更新処理エラー: {e}")
    
    async def _evaluate_rules(self, price_data: PriceData) -> None:
        """ルール評価の実行"""
        try:
            # 分析データの準備
            analysis_data = await self.data_preparator.prepare_analysis_data(
                analysis_type='trend_direction',
                symbol='USDJPY=X'
            )
            
            if '1d' not in analysis_data['timeframes']:
                return
            
            d1_data = analysis_data['timeframes']['1d']
            if d1_data['data'] is None or d1_data['data'].empty:
                return
            
            latest = d1_data['data'].iloc[-1]
            
            # ルール条件の評価
            market_data = {
                'price': price_data.mid_price,
                'RSI_14': latest.get('RSI_14', 0),
                'EMA_200': latest.get('EMA_200', 0),
                'EMA_21': latest.get('EMA_21', 0),
                'EMA_55': latest.get('EMA_55', 0),
                'MACD': latest.get('MACD', 0),
                'MACD_Signal': latest.get('MACD_Signal', 0),
                'ATR_14': latest.get('ATR_14', 0)
            }
            
            evaluation = await self.rule_engine.evaluate_entry_conditions(
                symbol='USDJPY=X',
                analysis_type='trend_direction'
            )
            
            # エントリーシグナルの生成
            if evaluation and len(evaluation) > 0:
                for signal_data in evaluation:
                    if signal_data.get('conditions_met', False):
                        await self._create_scenario(signal_data, price_data, latest)
            
        except Exception as e:
            self.logger.error(f"❌ ルール評価エラー: {e}")
    
    async def _create_scenario(self, signal_data: Dict, price_data: PriceData, technical_data: Any) -> None:
        """シナリオの作成"""
        try:
            # エントリーシグナルの作成
            entry_signal = EntrySignal(
                symbol=price_data.instrument,
                direction=TradeDirection.BUY if signal_data.get('direction') == 'buy' else TradeDirection.SELL,
                entry_price=price_data.mid_price,
                stop_loss=price_data.mid_price - (technical_data.get('ATR_14', 0.5) * 1.0),
                take_profit_1=price_data.mid_price + (technical_data.get('ATR_14', 0.5) * 1.5),
                take_profit_2=price_data.mid_price + (technical_data.get('ATR_14', 0.5) * 2.5),
                take_profit_3=price_data.mid_price + (technical_data.get('ATR_14', 0.5) * 4.0),
                confidence=signal_data.get('confidence', 0.0),
                reasoning=signal_data.get('reasoning', ''),
                technical_indicators={
                    'RSI_14': technical_data.get('RSI_14', 0),
                    'EMA_200': technical_data.get('EMA_200', 0),
                    'MACD': technical_data.get('MACD', 0),
                    'ATR_14': technical_data.get('ATR_14', 0)
                }
            )
            
            # シナリオの作成
            scenario = await self.scenario_manager.create_scenario(entry_signal)
            self.active_scenarios[scenario.id] = scenario
            
            self.logger.info(f"✅ シナリオ作成: {scenario.id} - {scenario.strategy}")
            
            # Discord通知
            if self.config.enable_notifications:
                await self.discord_notifier.send_scenario_created(scenario)
            
        except Exception as e:
            self.logger.error(f"❌ シナリオ作成エラー: {e}")
    
    async def _monitor_scenarios(self, price_data: PriceData) -> None:
        """アクティブシナリオの監視"""
        try:
            for scenario_id, scenario in list(self.active_scenarios.items()):
                if scenario.status == ScenarioStatus.ARMED:
                    # エントリー条件の再評価
                    if await self._check_entry_conditions(scenario, price_data):
                        # エントリーシグナルの送信
                        await self._send_entry_signal(scenario, price_data)
                        scenario.status = ScenarioStatus.TRIGGERED
                        
                elif scenario.status == ScenarioStatus.TRIGGERED:
                    # エグジット条件の監視
                    await self._check_exit_conditions(scenario, price_data)
            
        except Exception as e:
            self.logger.error(f"❌ シナリオ監視エラー: {e}")
    
    async def _check_entry_conditions(self, scenario: Scenario, price_data: PriceData) -> bool:
        """エントリー条件のチェック"""
        # 簡易的な条件チェック（実際の実装ではより詳細な条件を評価）
        return True  # 仮実装
    
    async def _check_exit_conditions(self, scenario: Scenario, price_data: PriceData) -> None:
        """エグジット条件のチェック"""
        # 簡易的なエグジット条件チェック
        pass  # 仮実装
    
    async def _send_entry_signal(self, scenario: Scenario, price_data: PriceData) -> None:
        """エントリーシグナルの送信"""
        try:
            if self.config.enable_notifications:
                await self.discord_notifier.send_entry_signal({
                    'scenario_id': scenario.id,
                    'symbol': price_data.instrument,
                    'direction': scenario.direction.value,
                    'entry_price': price_data.mid_price,
                    'stop_loss': scenario.entry_signal.stop_loss,
                    'take_profit_1': scenario.entry_signal.take_profit_1,
                    'confidence': scenario.entry_signal.confidence
                })
            
            self.logger.info(f"📢 エントリーシグナル送信: {scenario.id}")
            
        except Exception as e:
            self.logger.error(f"❌ エントリーシグナル送信エラー: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """システムステータスの取得"""
        return {
            'is_running': self.is_running,
            'active_scenarios': len(self.active_scenarios),
            'last_prices': {k: v.mid_price for k, v in self.last_prices.items()},
            'stream_connected': self.stream_client.is_connected
        }


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    logging.basicConfig(level=logging.INFO)
    
    config = TradingConfig(
        symbols=['USD_JPY'],
        update_interval_seconds=60,
        enable_notifications=True
    )
    
    pipeline = TradingPipeline(config)
    
    try:
        # 初期化
        await pipeline.initialize()
        
        # パイプライン開始
        await pipeline.start()
        
    except KeyboardInterrupt:
        print("🛑 テスト中断")
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        await pipeline.stop()


if __name__ == "__main__":
    asyncio.run(main())
