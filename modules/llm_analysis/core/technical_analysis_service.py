#!/usr/bin/env python3
"""
テクニカル分析サービス

データ収集完了後にテクニカル分析を実行し、シナリオ作成の判定を行います。
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from ..core.data_preparator import LLMDataPreparator
from ..core.rule_engine import RuleBasedEngine
from ..core.scenario_manager import ScenarioManager, EntrySignal, TradeDirection
from ..notification.discord_notifier import DiscordNotifier

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析結果"""
    symbol: str
    timestamp: datetime
    analysis_type: str
    conditions_met: bool
    signals: List[Dict[str, Any]]
    technical_summary: str
    confidence: float


class TechnicalAnalysisService:
    """テクニカル分析サービス"""
    
    def __init__(self):
        self.data_preparator = LLMDataPreparator()
        self.rule_engine = RuleBasedEngine()
        self.scenario_manager = ScenarioManager()
        self.discord_notifier = DiscordNotifier()
        
        # コールバック関数
        self.analysis_callbacks: List[Callable] = []
        self.scenario_callbacks: List[Callable] = []
        
        self.is_initialized = False
    
    async def initialize(self):
        """初期化"""
        if self.is_initialized:
            return
        
        logger.info("🚀 テクニカル分析サービスを初期化中...")
        
        try:
            # 各コンポーネントを初期化
            await self.data_preparator.initialize()
            await self.rule_engine.initialize()
            await self.discord_notifier.initialize()
            
            self.is_initialized = True
            logger.info("✅ テクニカル分析サービス初期化完了")
            
        except Exception as e:
            logger.error(f"❌ テクニカル分析サービス初期化エラー: {e}")
            raise
    
    def add_analysis_callback(self, callback: Callable):
        """分析完了時のコールバックを追加"""
        self.analysis_callbacks.append(callback)
        logger.info("✅ 分析コールバックを追加しました")
    
    def add_scenario_callback(self, callback: Callable):
        """シナリオ作成時のコールバックを追加"""
        self.scenario_callbacks.append(callback)
        logger.info("✅ シナリオコールバックを追加しました")
    
    async def analyze_market_conditions(self, symbol: str = "USDJPY=X") -> AnalysisResult:
        """市場条件の分析"""
        try:
            logger.info(f"🔍 市場条件分析開始: {symbol}")
            
            # 分析データの準備
            analysis_data = await self.data_preparator.prepare_analysis_data(
                analysis_type='trend_direction',
                symbol=symbol
            )
            
            if not analysis_data or 'timeframes' not in analysis_data:
                logger.warning(f"⚠️ 分析データの準備に失敗: {symbol}")
                return AnalysisResult(
                    symbol=symbol,
                    timestamp=datetime.now(timezone.utc),
                    analysis_type='trend_direction',
                    conditions_met=False,
                    signals=[],
                    technical_summary="データ不足",
                    confidence=0.0
                )
            
            # ルール評価の実行
            evaluation = await self.rule_engine.evaluate_entry_conditions(
                symbol=symbol,
                analysis_type='trend_direction'
            )
            
            # 結果の解析
            conditions_met = False
            signals = []
            technical_summary = ""
            confidence = 0.0
            
            if evaluation and len(evaluation) > 0:
                for signal_data in evaluation:
                    if signal_data.get('conditions_met', False):
                        conditions_met = True
                        signals.append(signal_data)
                        confidence = max(confidence, signal_data.get('confidence', 0.0))
                
                # テクニカルサマリーの生成
                if signals:
                    technical_summary = self._generate_technical_summary(signals, analysis_data)
            
            result = AnalysisResult(
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                analysis_type='trend_direction',
                conditions_met=conditions_met,
                signals=signals,
                technical_summary=technical_summary,
                confidence=confidence
            )
            
            logger.info(f"📊 分析完了: {symbol} - 条件合致: {conditions_met}, シグナル数: {len(signals)}")
            
            # コールバックの実行
            for callback in self.analysis_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(result)
                    else:
                        callback(result)
                except Exception as e:
                    logger.error(f"❌ 分析コールバックエラー: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 市場条件分析エラー: {e}")
            return AnalysisResult(
                symbol=symbol,
                timestamp=datetime.now(timezone.utc),
                analysis_type='trend_direction',
                conditions_met=False,
                signals=[],
                technical_summary=f"分析エラー: {str(e)}",
                confidence=0.0
            )
    
    async def create_scenarios_from_analysis(self, analysis_result: AnalysisResult) -> List[str]:
        """分析結果からシナリオを作成"""
        if not analysis_result.conditions_met:
            logger.info("ℹ️ エントリー条件が満たされていないため、シナリオを作成しません")
            return []
        
        created_scenarios = []
        
        try:
            for signal_data in analysis_result.signals:
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
                    technical_summary={"summary": analysis_result.technical_summary},
                    created_at=datetime.now(timezone.utc)
                )
                
                # シナリオの作成
                scenario = await self.scenario_manager.create_scenario(
                    entry_signal=entry_signal,
                    symbol=analysis_result.symbol,
                    expires_hours=8
                )
                
                created_scenarios.append(scenario.id)
                logger.info(f"✅ シナリオ作成: {scenario.id} - {scenario.strategy}")
                
                # Discord通知
                try:
                    await self.discord_notifier.send_scenario_created(scenario)
                except Exception as e:
                    logger.error(f"❌ Discord通知エラー: {e}")
                
                # コールバックの実行
                for callback in self.scenario_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(scenario)
                        else:
                            callback(scenario)
                    except Exception as e:
                        logger.error(f"❌ シナリオコールバックエラー: {e}")
            
            return created_scenarios
            
        except Exception as e:
            logger.error(f"❌ シナリオ作成エラー: {e}")
            return []
    
    def _generate_technical_summary(self, signals: List[Dict], analysis_data: Dict) -> str:
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
    
    async def process_data_collection_event(self, symbol: str = "USDJPY=X", new_data_count: int = 0):
        """データ収集完了イベントの処理"""
        try:
            logger.info(f"🔄 データ収集イベント処理開始: {symbol} (新規データ: {new_data_count}件)")
            
            # 新しいデータがある場合のみ分析を実行
            if new_data_count > 0:
                # 市場条件の分析
                analysis_result = await self.analyze_market_conditions(symbol)
                
                # シナリオの作成
                if analysis_result.conditions_met:
                    created_scenarios = await self.create_scenarios_from_analysis(analysis_result)
                    logger.info(f"📊 分析完了: {len(created_scenarios)}個のシナリオを作成")
                else:
                    logger.info("ℹ️ エントリー条件が満たされていません")
            else:
                logger.debug("ℹ️ 新しいデータがないため、分析をスキップします")
            
        except Exception as e:
            logger.error(f"❌ データ収集イベント処理エラー: {e}")
    
    async def close(self):
        """リソースの解放"""
        try:
            await self.data_preparator.connection_manager.close()
            await self.discord_notifier.close()
            logger.info("✅ テクニカル分析サービス終了")
        except Exception as e:
            logger.error(f"❌ 終了処理エラー: {e}")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    logging.basicConfig(level=logging.INFO)
    
    service = TechnicalAnalysisService()
    
    try:
        # 初期化
        await service.initialize()
        
        # 市場条件の分析
        result = await service.analyze_market_conditions()
        print(f"分析結果: {result}")
        
        # シナリオの作成
        if result.conditions_met:
            scenarios = await service.create_scenarios_from_analysis(result)
            print(f"作成されたシナリオ: {scenarios}")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
