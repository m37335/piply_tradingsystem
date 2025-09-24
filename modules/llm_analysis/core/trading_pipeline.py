"""
売買パイプライン

正しい設計に基づく売買パイプライン：
1. 5分間隔でデータ収集・テクニカル指標計算・ルール判定
2. 条件成立時のみStream APIでリアルタイム監視
3. エントリーポイント確認・Discord配信
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any

from .data_preparator import LLMDataPreparator
from .rule_engine import RuleBasedEngine
from .scenario_manager import ScenarioManager
from .snapshot_manager import SnapshotManager
from ..notification.discord_notifier import DiscordNotifier
from ..providers.yahoo_finance_stream_client import YahooFinanceStreamClient
from .adherence_evaluator import AdherenceEvaluator


class TradingPipeline:
    """売買パイプライン（正しい設計）"""
    
    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        
        # コンポーネントの初期化
        self.data_preparator = LLMDataPreparator()
        self.rule_engine = RuleBasedEngine()
        self.scenario_manager = ScenarioManager()
        self.snapshot_manager = SnapshotManager()
        self.discord_notifier = DiscordNotifier()
        self.stream_client = YahooFinanceStreamClient()
        self.adherence_evaluator = AdherenceEvaluator()
        
        # パイプライン状態
        self.is_running = False
        self.active_scenarios: Dict[str, Any] = {}
        self.last_analysis_time: Optional[datetime] = None
        
        self.logger.info("✅ 売買パイプライン初期化完了")
    
    async def initialize(self):
        """非同期初期化"""
        await self.data_preparator.initialize()
        await self.rule_engine.initialize()
        await self.scenario_manager.initialize()
        await self.snapshot_manager.initialize()
        await self.discord_notifier.initialize()
        await self.stream_client.initialize()
        
        self.logger.info("✅ 売買パイプライン全コンポーネント初期化完了")
    
    async def start_pipeline(self, symbol: str = 'USDJPY=X'):
        """
        パイプラインの開始
        
        Args:
            symbol: 監視対象の通貨ペア
        """
        if self.is_running:
            self.logger.warning("⚠️ パイプラインは既に実行中です")
            return
        
        self.is_running = True
        self.logger.info(f"🚀 売買パイプライン開始: {symbol}")
        
        try:
            # メインループ: 5分間隔で分析
            while self.is_running:
                await self._run_analysis_cycle(symbol)
                
                # 5分間隔で待機
                await asyncio.sleep(300)  # 300秒 = 5分
                
        except Exception as e:
            self.logger.error(f"❌ パイプラインエラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_running = False
            await self._cleanup()
    
    async def _run_analysis_cycle(self, symbol: str):
        """
        分析サイクルの実行（5分間隔）
        
        Args:
            symbol: 監視対象の通貨ペア
        """
        try:
            current_time = datetime.now(timezone.utc)
            self.logger.info(f"📊 分析サイクル開始: {current_time.strftime('%H:%M:%S')}")
            
            # 1. データ準備（TimescaleDBから最新データ取得）
            analysis_data = await self.data_preparator.prepare_analysis_data(
                analysis_type='trend_direction',
                symbol=symbol,
                timeframes=['5m', '15m', '1h', '4h', '1d']
            )
            
            if not analysis_data:
                self.logger.warning("⚠️ 分析データの準備に失敗")
                return
            
            # 2. ルールベース判定
            entry_signals = await self.rule_engine.evaluate_entry_conditions(symbol, 'trend_direction')
            self.logger.info(f"🔍 ルール評価結果: {len(entry_signals)}個のシグナル")
            
            # 3. 新しいシナリオの作成
            new_scenarios = []
            for signal in entry_signals:
                scenario = await self.scenario_manager.create_scenario(signal, symbol)
                new_scenarios.append(scenario)
                self.active_scenarios[scenario.id] = scenario
                
                # Discord通知: シナリオ作成
                await self.discord_notifier.send_scenario_created(scenario)
                self.logger.info(f"📋 シナリオ作成: {scenario.id}")
            
            # 4. ルールベース判定結果のDiscord配信（条件満たした場合）
            if entry_signals:
                await self._send_rule_evaluation_results(entry_signals, symbol)
            
            # 5. 既存シナリオの監視（Stream API）
            if self.active_scenarios:
                await self._monitor_active_scenarios(symbol)
            
            # 6. 期限切れシナリオのクリーンアップ
            await self._cleanup_expired_scenarios()
            
            self.last_analysis_time = current_time
            self.logger.info(f"✅ 分析サイクル完了: {len(new_scenarios)}個の新シナリオ")
            
        except Exception as e:
            self.logger.error(f"❌ 分析サイクルエラー: {e}")
            import traceback
            traceback.print_exc()
    
    async def _monitor_active_scenarios(self, symbol: str):
        """
        アクティブシナリオの監視（Stream API）
        
        Args:
            symbol: 監視対象の通貨ペア
        """
        if not self.active_scenarios:
            return
        
        self.logger.info(f"👀 アクティブシナリオ監視開始: {len(self.active_scenarios)}個")
        
        # Stream APIコールバックの設定
        async def price_callback(price_data):
            await self._process_price_update(price_data)
        
        # コールバック設定
        self.stream_client.add_callback('pricing', price_callback)
        
        # 短時間のストリーミング（30秒間）
        try:
            await asyncio.wait_for(
                self.stream_client.start_price_stream([symbol]),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            self.logger.info("⏰ ストリーミング監視完了（30秒）")
        except Exception as e:
            self.logger.error(f"❌ ストリーミング監視エラー: {e}")
    
    async def _process_price_update(self, price_data):
        """
        価格更新の処理
        
        Args:
            price_data: 価格データ
        """
        try:
            for scenario_id, scenario in list(self.active_scenarios.items()):
                # エントリー条件の確認
                if scenario.status.value == 'armed':
                    entry_result = await self._check_entry_conditions(scenario, price_data)
                    if entry_result['should_enter']:
                        await self._execute_entry(scenario, price_data, entry_result)
                
                # エグジット条件の確認
                elif scenario.status.value == 'entered':
                    exit_result = await self._check_exit_conditions(scenario, price_data)
                    if exit_result['should_exit']:
                        await self._execute_exit(scenario, price_data, exit_result)
                        
        except Exception as e:
            self.logger.error(f"❌ 価格更新処理エラー: {e}")
    
    async def _check_entry_conditions(self, scenario, price_data) -> Dict:
        """エントリー条件の確認"""
        # 実装: シナリオのエントリー条件と現在価格を比較
        # 簡略化のため、ダミー実装
        return {
            'should_enter': False,  # 実際の条件判定ロジック
            'confidence': 0.0
        }
    
    async def _check_exit_conditions(self, scenario, price_data) -> Dict:
        """エグジット条件の確認"""
        # 実装: シナリオのエグジット条件と現在価格を比較
        # 簡略化のため、ダミー実装
        return {
            'should_exit': False,  # 実際の条件判定ロジック
            'exit_reason': None
        }
    
    async def _execute_entry(self, scenario, price_data, entry_result):
        """エントリーの実行"""
        try:
            # シナリオステータス更新
            scenario.status = 'entered'
            scenario.entered_at = datetime.now(timezone.utc)
            scenario.entry_price = price_data.mid_price
            
            # スナップ保存
            entry_snapshot = await self.snapshot_manager.save_entry_snapshot(scenario, price_data)
            
            # Discord通知: エントリー
            await self.discord_notifier.send_entry_signal(scenario, entry_snapshot)
            
            self.logger.info(f"🟢 エントリー実行: {scenario.id} @ {price_data.mid_price:.5f}")
            
        except Exception as e:
            self.logger.error(f"❌ エントリー実行エラー: {e}")
    
    async def _execute_exit(self, scenario, price_data, exit_result):
        """エグジットの実行"""
        try:
            # シナリオステータス更新
            scenario.status = 'exited'
            scenario.exited_at = datetime.now(timezone.utc)
            scenario.exit_price = price_data.mid_price
            scenario.exit_reason = exit_result['exit_reason']
            
            # 損益計算
            if scenario.direction.value == 'BUY':
                scenario.profit_loss = (price_data.mid_price - scenario.entry_price) * 10000
            else:
                scenario.profit_loss = (scenario.entry_price - price_data.mid_price) * 10000
            
            # スナップ保存
            exit_snapshot = await self.snapshot_manager.save_exit_snapshot(scenario, price_data)
            
            # ルール遵守判定
            adherence_score = await self.adherence_evaluator.evaluate_trade(scenario)
            
            # Discord通知: エグジット
            await self.discord_notifier.send_exit_signal(scenario, exit_snapshot)
            
            # アクティブシナリオから削除
            if scenario.id in self.active_scenarios:
                del self.active_scenarios[scenario.id]
            
            self.logger.info(f"🔴 エグジット実行: {scenario.id} @ {price_data.mid_price:.5f} (P&L: {scenario.profit_loss:.1f})")
            
        except Exception as e:
            self.logger.error(f"❌ エグジット実行エラー: {e}")
    
    async def _send_rule_evaluation_results(self, entry_signals: List, symbol: str):
        """
        ルール評価結果のDiscord配信
        
        Args:
            entry_signals: エントリーシグナルリスト
            symbol: 通貨ペア
        """
        try:
            # ルール評価結果のサマリー作成
            signal_summary = []
            for signal in entry_signals:
                signal_summary.append({
                    'strategy': signal.strategy,
                    'direction': signal.direction.value,
                    'confidence': signal.confidence,
                    'timeframe': signal.timeframe,
                    'entry_price': signal.entry_price,
                    'stop_loss': signal.stop_loss,
                    'take_profit': signal.take_profit
                })
            
            # Discord通知: ルール評価結果
            await self.discord_notifier.send_rule_evaluation_results(
                symbol=symbol,
                signals=signal_summary,
                analysis_time=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"📊 ルール評価結果Discord配信: {len(entry_signals)}個のシグナル")
            
        except Exception as e:
            self.logger.error(f"❌ ルール評価結果Discord配信エラー: {e}")
    
    async def _cleanup_expired_scenarios(self):
        """期限切れシナリオのクリーンアップ"""
        current_time = datetime.now(timezone.utc)
        expired_scenarios = []
        
        for scenario_id, scenario in self.active_scenarios.items():
            if current_time > scenario.expires_at:
                scenario.status = 'expired'
                expired_scenarios.append(scenario_id)
        
        for scenario_id in expired_scenarios:
            del self.active_scenarios[scenario_id]
            self.logger.info(f"⏰ 期限切れシナリオ削除: {scenario_id}")
    
    async def _cleanup(self):
        """リソースのクリーンアップ"""
        try:
            await self.data_preparator.close()
            await self.rule_engine.close()
            await self.scenario_manager.close()
            await self.snapshot_manager.close()
            await self.discord_notifier.close()
            await self.stream_client.close()
            
            self.logger.info("✅ パイプラインリソースクリーンアップ完了")
        except Exception as e:
            self.logger.error(f"❌ クリーンアップエラー: {e}")
    
    async def stop_pipeline(self):
        """パイプラインの停止"""
        self.is_running = False
        self.logger.info("🛑 パイプライン停止要求")
    
    def get_pipeline_status(self) -> Dict:
        """パイプライン状態の取得"""
        return {
            'is_running': self.is_running,
            'active_scenarios': len(self.active_scenarios),
            'last_analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            'scenario_ids': list(self.active_scenarios.keys())
        }
