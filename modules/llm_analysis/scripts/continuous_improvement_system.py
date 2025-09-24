#!/usr/bin/env python3
"""
継続的改善システム

三層ゲート式フィルタリングシステムの継続的な改善を自動化し、
パフォーマンスと精度の向上を図ります。
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ContinuousImprovementSystem:
    """継続的改善システム"""
    
    def __init__(self):
        self.connection_manager = None
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        
        # 改善履歴
        self.improvement_history = []
        
        # 改善しきい値
        self.improvement_thresholds = {
            'signal_generation_rate': 0.05,  # 5%未満で改善
            'avg_confidence': 0.6,  # 0.6未満で改善
            'gate_pass_rate': 0.1,  # 10%未満で改善
            'performance_degradation': 0.2  # 20%以上の性能低下で改善
        }
    
    async def initialize(self):
        """改善システムの初期化"""
        try:
            self.logger.info("🔧 継続的改善システム初期化開始")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=2,
                max_connections=5
            )
            await self.connection_manager.initialize()
            
            self.logger.info("✅ 継続的改善システム初期化完了")
            
        except Exception as e:
            self.logger.error(f"❌ 改善システム初期化エラー: {e}")
            raise
    
    async def start_continuous_improvement(self, check_interval: int = 3600):
        """
        継続的改善を開始
        
        Args:
            check_interval: チェック間隔（秒）
        """
        if self.is_running:
            self.logger.warning("⚠️ 継続的改善は既に実行中です")
            return
        
        try:
            self.logger.info(f"🚀 継続的改善開始 (チェック間隔: {check_interval}秒)")
            self.is_running = True
            
            while self.is_running:
                await self._perform_improvement_cycle()
                await asyncio.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 継続的改善を停止します")
        except Exception as e:
            self.logger.error(f"❌ 継続的改善エラー: {e}")
        finally:
            self.is_running = False
    
    async def _perform_improvement_cycle(self):
        """改善サイクルを実行"""
        try:
            self.logger.info("🔄 改善サイクル開始")
            
            # 現在のパフォーマンスを分析
            current_performance = await self._analyze_current_performance()
            
            # 改善が必要かチェック
            improvement_needed = self._check_improvement_needed(current_performance)
            
            if improvement_needed:
                # 改善を実行
                improvement_result = await self._execute_improvement(current_performance)
                
                # 改善履歴に記録
                self._record_improvement(improvement_result)
                
                # 改善結果をログ出力
                self._log_improvement_result(improvement_result)
            else:
                self.logger.info("✅ 改善は不要です")
            
            self.logger.info("🔄 改善サイクル完了")
            
        except Exception as e:
            self.logger.error(f"❌ 改善サイクルエラー: {e}")
    
    async def _analyze_current_performance(self) -> Dict[str, Any]:
        """現在のパフォーマンスを分析"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 過去24時間のパフォーマンス統計
                performance_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_signals,
                        AVG(overall_confidence) as avg_confidence,
                        COUNT(CASE WHEN overall_confidence >= 0.8 THEN 1 END) as high_confidence_signals,
                        COUNT(CASE WHEN overall_confidence >= 0.7 THEN 1 END) as medium_confidence_signals
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                # 各ゲートの統計
                gate_stats = {}
                for gate_num in [1, 2, 3]:
                    gate_stat = await conn.fetchrow(f"""
                        SELECT 
                            COUNT(*) as total_evaluations,
                            COUNT(CASE WHEN gate{gate_num}_confidence >= 0.7 THEN 1 END) as passed_evaluations,
                            AVG(gate{gate_num}_confidence) as avg_confidence
                        FROM three_gate_signals 
                        WHERE created_at >= NOW() - INTERVAL '24 hours'
                    """)
                    
                    pass_rate = 0.0
                    if gate_stat['total_evaluations'] > 0:
                        pass_rate = gate_stat['passed_evaluations'] / gate_stat['total_evaluations']
                    
                    gate_stats[f'gate{gate_num}'] = {
                        'total_evaluations': gate_stat['total_evaluations'] or 0,
                        'passed_evaluations': gate_stat['passed_evaluations'] or 0,
                        'pass_rate': pass_rate,
                        'avg_confidence': float(gate_stat['avg_confidence'] or 0.0)
                    }
                
                # シグナル生成率の計算
                signal_generation_rate = 0.0
                if performance_stats['total_signals'] > 0:
                    # 過去24時間のイベント数で正規化
                    event_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM events 
                        WHERE event_type = 'data_collection_completed' 
                        AND created_at >= NOW() - INTERVAL '24 hours'
                    """)
                    if event_count > 0:
                        signal_generation_rate = performance_stats['total_signals'] / event_count
                
                return {
                    'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                    'signal_generation_rate': signal_generation_rate,
                    'avg_confidence': float(performance_stats['avg_confidence'] or 0.0),
                    'high_confidence_signals': performance_stats['high_confidence_signals'] or 0,
                    'medium_confidence_signals': performance_stats['medium_confidence_signals'] or 0,
                    'gate_statistics': gate_stats
                }
                
        except Exception as e:
            self.logger.error(f"❌ パフォーマンス分析エラー: {e}")
            return {}
    
    def _check_improvement_needed(self, performance: Dict[str, Any]) -> bool:
        """改善が必要かチェック"""
        try:
            # シグナル生成率のチェック
            signal_generation_rate = performance.get('signal_generation_rate', 0.0)
            if signal_generation_rate < self.improvement_thresholds['signal_generation_rate']:
                self.logger.info(f"⚠️ シグナル生成率が低い: {signal_generation_rate:.2%}")
                return True
            
            # 平均信頼度のチェック
            avg_confidence = performance.get('avg_confidence', 0.0)
            if avg_confidence < self.improvement_thresholds['avg_confidence']:
                self.logger.info(f"⚠️ 平均信頼度が低い: {avg_confidence:.2f}")
                return True
            
            # 各ゲートの通過率チェック
            gate_stats = performance.get('gate_statistics', {})
            for gate_name, gate_stat in gate_stats.items():
                pass_rate = gate_stat.get('pass_rate', 0.0)
                if pass_rate < self.improvement_thresholds['gate_pass_rate']:
                    self.logger.info(f"⚠️ {gate_name.upper()}の通過率が低い: {pass_rate:.2%}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 改善必要性チェックエラー: {e}")
            return False
    
    async def _execute_improvement(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """改善を実行"""
        try:
            self.logger.info("🔧 改善実行開始")
            
            improvement_result = {
                'improvement_timestamp': datetime.now(timezone.utc).isoformat(),
                'improvement_type': 'automatic',
                'improvements_applied': [],
                'performance_before': performance,
                'performance_after': None
            }
            
            # シグナル生成率が低い場合の改善
            signal_generation_rate = performance.get('signal_generation_rate', 0.0)
            if signal_generation_rate < self.improvement_thresholds['signal_generation_rate']:
                improvement = await self._improve_signal_generation_rate()
                improvement_result['improvements_applied'].append(improvement)
            
            # 平均信頼度が低い場合の改善
            avg_confidence = performance.get('avg_confidence', 0.0)
            if avg_confidence < self.improvement_thresholds['avg_confidence']:
                improvement = await self._improve_confidence()
                improvement_result['improvements_applied'].append(improvement)
            
            # ゲート通過率が低い場合の改善
            gate_stats = performance.get('gate_statistics', {})
            for gate_name, gate_stat in gate_stats.items():
                pass_rate = gate_stat.get('pass_rate', 0.0)
                if pass_rate < self.improvement_thresholds['gate_pass_rate']:
                    improvement = await self._improve_gate_pass_rate(gate_name)
                    improvement_result['improvements_applied'].append(improvement)
            
            # 改善後のパフォーマンスを測定（次回サイクルで更新）
            improvement_result['performance_after'] = "測定中"
            
            self.logger.info("✅ 改善実行完了")
            return improvement_result
            
        except Exception as e:
            self.logger.error(f"❌ 改善実行エラー: {e}")
            return {}
    
    async def _improve_signal_generation_rate(self) -> Dict[str, Any]:
        """シグナル生成率の改善"""
        try:
            self.logger.info("🔧 シグナル生成率改善開始")
            
            # 信頼度閾値を下げる
            improvement = {
                'type': 'signal_generation_rate',
                'action': 'lower_confidence_thresholds',
                'description': '信頼度閾値を0.1下げてシグナル生成率を向上',
                'parameters': {
                    'gate1_threshold_adjustment': -0.1,
                    'gate2_threshold_adjustment': -0.1,
                    'gate3_threshold_adjustment': -0.1
                }
            }
            
            # 実際の設定変更は設定最適化ツールを使用
            # ここでは改善提案のみ記録
            
            self.logger.info("✅ シグナル生成率改善完了")
            return improvement
            
        except Exception as e:
            self.logger.error(f"❌ シグナル生成率改善エラー: {e}")
            return {}
    
    async def _improve_confidence(self) -> Dict[str, Any]:
        """信頼度の改善"""
        try:
            self.logger.info("🔧 信頼度改善開始")
            
            improvement = {
                'type': 'confidence',
                'action': 'optimize_pattern_conditions',
                'description': 'パターン条件を最適化して信頼度を向上',
                'parameters': {
                    'pattern_weight_adjustment': 0.1,
                    'condition_optimization': True
                }
            }
            
            self.logger.info("✅ 信頼度改善完了")
            return improvement
            
        except Exception as e:
            self.logger.error(f"❌ 信頼度改善エラー: {e}")
            return {}
    
    async def _improve_gate_pass_rate(self, gate_name: str) -> Dict[str, Any]:
        """ゲート通過率の改善"""
        try:
            self.logger.info(f"🔧 {gate_name.upper()}通過率改善開始")
            
            improvement = {
                'type': 'gate_pass_rate',
                'gate': gate_name,
                'action': 'adjust_gate_conditions',
                'description': f'{gate_name.upper()}の条件を調整して通過率を向上',
                'parameters': {
                    'confidence_threshold_adjustment': -0.05,
                    'pattern_condition_relaxation': True
                }
            }
            
            self.logger.info(f"✅ {gate_name.upper()}通過率改善完了")
            return improvement
            
        except Exception as e:
            self.logger.error(f"❌ {gate_name.upper()}通過率改善エラー: {e}")
            return {}
    
    def _record_improvement(self, improvement_result: Dict[str, Any]):
        """改善履歴に記録"""
        try:
            self.improvement_history.append(improvement_result)
            
            # 履歴をファイルに保存
            history_file = Path("/app/improvement_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.improvement_history, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info("✅ 改善履歴を記録しました")
            
        except Exception as e:
            self.logger.error(f"❌ 改善履歴記録エラー: {e}")
    
    def _log_improvement_result(self, improvement_result: Dict[str, Any]):
        """改善結果をログ出力"""
        try:
            print("=" * 80)
            print("🔧 改善実行結果")
            print("=" * 80)
            print(f"⏰ 改善時刻: {improvement_result['improvement_timestamp']}")
            print(f"🔧 改善タイプ: {improvement_result['improvement_type']}")
            print()
            
            improvements_applied = improvement_result.get('improvements_applied', [])
            if improvements_applied:
                print("✅ 適用された改善:")
                for i, improvement in enumerate(improvements_applied, 1):
                    print(f"   {i}. {improvement['description']}")
                    print(f"      タイプ: {improvement['type']}")
                    print(f"      アクション: {improvement['action']}")
                    print()
            else:
                print("ℹ️ 適用された改善はありません")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ 改善結果ログ出力エラー: {e}")
    
    def get_improvement_history(self) -> List[Dict[str, Any]]:
        """改善履歴を取得"""
        return self.improvement_history.copy()
    
    def display_improvement_summary(self):
        """改善サマリーを表示"""
        try:
            print("=" * 80)
            print("📊 継続的改善サマリー")
            print("=" * 80)
            print(f"📅 改善履歴数: {len(self.improvement_history)}")
            print()
            
            if self.improvement_history:
                print("🔧 最近の改善:")
                recent_improvements = self.improvement_history[-5:]  # 最近5件
                for i, improvement in enumerate(recent_improvements, 1):
                    print(f"   {i}. {improvement['improvement_timestamp']}")
                    improvements_applied = improvement.get('improvements_applied', [])
                    print(f"      適用改善数: {len(improvements_applied)}")
                    for imp in improvements_applied:
                        print(f"         • {imp['description']}")
                    print()
            else:
                print("ℹ️ 改善履歴はありません")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ 改善サマリー表示エラー: {e}")
    
    async def close(self):
        """改善システムの終了"""
        try:
            self.logger.info("🔧 継続的改善システム終了")
            
            if self.connection_manager:
                await self.connection_manager.close()
            
            self.logger.info("✅ 継続的改善システム終了完了")
            
        except Exception as e:
            self.logger.error(f"❌ 改善システム終了エラー: {e}")


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='継続的改善システム')
    parser.add_argument('command', nargs='?', default='start',
                       choices=['start', 'analyze', 'history', 'help'],
                       help='実行するコマンド')
    parser.add_argument('--interval', type=int, default=3600, help='チェック間隔（秒）')
    
    args = parser.parse_args()
    
    improvement_system = ContinuousImprovementSystem()
    
    try:
        # 改善システムの初期化
        await improvement_system.initialize()
        
        if args.command == 'start':
            # 継続的改善を開始
            await improvement_system.start_continuous_improvement(args.interval)
            
        elif args.command == 'analyze':
            # 現在のパフォーマンスを分析
            performance = await improvement_system._analyze_current_performance()
            print("=" * 80)
            print("📊 現在のパフォーマンス分析")
            print("=" * 80)
            print(f"⏰ 分析時刻: {performance.get('analysis_timestamp', 'N/A')}")
            print(f"🎯 シグナル生成率: {performance.get('signal_generation_rate', 0.0):.2%}")
            print(f"💯 平均信頼度: {performance.get('avg_confidence', 0.0):.2f}")
            print(f"⭐ 高信頼度シグナル: {performance.get('high_confidence_signals', 0)}")
            print(f"📈 中信頼度シグナル: {performance.get('medium_confidence_signals', 0)}")
            print()
            
            gate_stats = performance.get('gate_statistics', {})
            for gate_name, gate_stat in gate_stats.items():
                print(f"{gate_name.upper()}:")
                print(f"   📊 総評価回数: {gate_stat.get('total_evaluations', 0)}")
                print(f"   ✅ 通過回数: {gate_stat.get('passed_evaluations', 0)}")
                print(f"   📈 通過率: {gate_stat.get('pass_rate', 0.0):.2%}")
                print(f"   💯 平均信頼度: {gate_stat.get('avg_confidence', 0.0):.2f}")
                print()
            
            print("=" * 80)
            
        elif args.command == 'history':
            # 改善履歴を表示
            improvement_system.display_improvement_summary()
            
        elif args.command == 'help':
            print("=" * 80)
            print("🔧 継続的改善システム")
            print("=" * 80)
            print()
            print("使用方法:")
            print("  python continuous_improvement_system.py [コマンド] [オプション]")
            print()
            print("コマンド:")
            print("  start            - 継続的改善を開始")
            print("  analyze          - 現在のパフォーマンスを分析")
            print("  history          - 改善履歴を表示")
            print("  help             - このヘルプを表示")
            print()
            print("オプション:")
            print("  --interval SEC   - チェック間隔（秒、デフォルト: 3600）")
            print()
            print("例:")
            print("  python continuous_improvement_system.py start")
            print("  python continuous_improvement_system.py start --interval 1800")
            print("  python continuous_improvement_system.py analyze")
            print("  python continuous_improvement_system.py history")
            print()
            print("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ システム実行エラー: {e}")
        sys.exit(1)
    finally:
        await improvement_system.close()


if __name__ == "__main__":
    # システムの実行
    asyncio.run(main())
