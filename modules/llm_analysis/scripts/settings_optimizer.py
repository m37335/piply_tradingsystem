#!/usr/bin/env python3
"""
設定最適化ツール

三層ゲート式フィルタリングシステムの設定を最適化し、
パフォーマンスと精度の向上を図ります。
"""

import asyncio
import json
import logging
import sys
import yaml
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


class SettingsOptimizer:
    """設定最適化ツール"""
    
    def __init__(self):
        self.connection_manager = None
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path("/app/modules/llm_analysis/config")
        
        # デフォルト設定
        self.default_settings = {
            'gate1': {
                'confidence_threshold': 0.7,
                'pattern_weights': {
                    'trending_market': 1.0,
                    'trend_reversal': 1.0,
                    'ranging_market': 1.0
                }
            },
            'gate2': {
                'confidence_threshold': 0.6,
                'pattern_weights': {
                    'pullback_setup': 1.0,
                    'breakout_setup': 1.0,
                    'first_pullback': 1.0,
                    'range_boundary': 1.0
                }
            },
            'gate3': {
                'confidence_threshold': 0.7,
                'pattern_weights': {
                    'price_action_reversal': 1.0,
                    'volume_breakout': 1.0
                }
            }
        }
    
    async def initialize(self):
        """最適化ツールの初期化"""
        try:
            self.logger.info("🔧 設定最適化ツール初期化開始")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=2,
                max_connections=5
            )
            await self.connection_manager.initialize()
            
            self.logger.info("✅ 設定最適化ツール初期化完了")
            
        except Exception as e:
            self.logger.error(f"❌ 最適化ツール初期化エラー: {e}")
            raise
    
    async def analyze_current_settings(self) -> Dict[str, Any]:
        """現在の設定を分析"""
        try:
            self.logger.info("📊 現在の設定分析開始")
            
            analysis_result = {
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'current_settings': {},
                'performance_metrics': {},
                'optimization_recommendations': []
            }
            
            # 現在の設定を読み込み
            for gate_num in [1, 2, 3]:
                gate_config = await self._load_gate_config(gate_num)
                analysis_result['current_settings'][f'gate{gate_num}'] = gate_config
            
            # パフォーマンスメトリクスを取得
            performance_metrics = await self._get_performance_metrics()
            analysis_result['performance_metrics'] = performance_metrics
            
            # 最適化推奨事項を生成
            recommendations = self._generate_optimization_recommendations(
                analysis_result['current_settings'],
                performance_metrics
            )
            analysis_result['optimization_recommendations'] = recommendations
            
            self.logger.info("✅ 現在の設定分析完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ 設定分析エラー: {e}")
            raise
    
    async def _load_gate_config(self, gate_num: int) -> Dict[str, Any]:
        """ゲート設定を読み込み"""
        try:
            config_file = self.config_dir / f"gate{gate_num}_patterns.yaml"
            
            if not config_file.exists():
                self.logger.warning(f"GATE {gate_num} 設定ファイルが見つかりません: {config_file}")
                return {}
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            return config
            
        except Exception as e:
            self.logger.error(f"❌ GATE {gate_num} 設定読み込みエラー: {e}")
            return {}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンスメトリクスを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 過去7日間のシグナル統計
                signal_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_signals,
                        AVG(overall_confidence) as avg_confidence,
                        COUNT(CASE WHEN overall_confidence >= 0.8 THEN 1 END) as high_confidence_count,
                        COUNT(CASE WHEN overall_confidence >= 0.7 THEN 1 END) as medium_confidence_count
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                
                # 各ゲートの統計
                gate_stats = {}
                for gate_num in [1, 2, 3]:
                    gate_stat = await conn.fetchrow(f"""
                        SELECT 
                            COUNT(*) as total_evaluations,
                            AVG(gate{gate_num}_confidence) as avg_confidence,
                            COUNT(CASE WHEN gate{gate_num}_confidence >= 0.7 THEN 1 END) as high_confidence_count
                        FROM three_gate_signals 
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                    """)
                    
                    gate_stats[f'gate{gate_num}'] = {
                        'total_evaluations': gate_stat['total_evaluations'] or 0,
                        'avg_confidence': float(gate_stat['avg_confidence'] or 0.0),
                        'high_confidence_count': gate_stat['high_confidence_count'] or 0
                    }
                
                return {
                    'signal_statistics': {
                        'total_signals': signal_stats['total_signals'] or 0,
                        'avg_confidence': float(signal_stats['avg_confidence'] or 0.0),
                        'high_confidence_count': signal_stats['high_confidence_count'] or 0,
                        'medium_confidence_count': signal_stats['medium_confidence_count'] or 0
                    },
                    'gate_statistics': gate_stats
                }
                
        except Exception as e:
            self.logger.error(f"❌ パフォーマンスメトリクス取得エラー: {e}")
            return {}
    
    def _generate_optimization_recommendations(
        self, 
        current_settings: Dict[str, Any], 
        performance_metrics: Dict[str, Any]
    ) -> List[str]:
        """最適化推奨事項を生成"""
        recommendations = []
        
        # シグナル生成率のチェック
        signal_stats = performance_metrics.get('signal_statistics', {})
        total_signals = signal_stats.get('total_signals', 0)
        
        if total_signals == 0:
            recommendations.append(
                "シグナルが生成されていません。信頼度閾値を下げることを検討してください。"
            )
        
        # 各ゲートの信頼度チェック
        gate_stats = performance_metrics.get('gate_statistics', {})
        for gate_name, gate_stat in gate_stats.items():
            avg_confidence = gate_stat.get('avg_confidence', 0.0)
            high_confidence_count = gate_stat.get('high_confidence_count', 0)
            total_evaluations = gate_stat.get('total_evaluations', 0)
            
            if total_evaluations > 0:
                high_confidence_rate = high_confidence_count / total_evaluations
                
                if high_confidence_rate < 0.1:  # 10%未満
                    recommendations.append(
                        f"{gate_name.upper()}の高信頼度率が{high_confidence_rate:.1%}と低いです。"
                        "信頼度閾値を下げることを検討してください。"
                    )
                elif high_confidence_rate > 0.8:  # 80%以上
                    recommendations.append(
                        f"{gate_name.upper()}の高信頼度率が{high_confidence_rate:.1%}と高いです。"
                        "信頼度閾値を上げることを検討してください。"
                    )
        
        # パターン使用頻度のチェック
        for gate_name, gate_config in current_settings.items():
            patterns = gate_config.get('patterns', {})
            if patterns:
                pattern_names = list(patterns.keys())
                if len(pattern_names) > 1:
                    recommendations.append(
                        f"{gate_name.upper()}で複数のパターンが定義されています。"
                        "使用頻度の低いパターンの見直しを検討してください。"
                    )
        
        return recommendations
    
    async def optimize_settings(self, optimization_type: str = "balanced") -> Dict[str, Any]:
        """
        設定を最適化
        
        Args:
            optimization_type: 最適化タイプ ("aggressive", "balanced", "conservative")
            
        Returns:
            最適化された設定
        """
        try:
            self.logger.info(f"🔧 設定最適化開始 (タイプ: {optimization_type})")
            
            # 最適化パラメータを取得
            optimization_params = self._get_optimization_params(optimization_type)
            
            # 最適化された設定を生成
            optimized_settings = {}
            for gate_num in [1, 2, 3]:
                gate_name = f"gate{gate_num}"
                current_config = await self._load_gate_config(gate_num)
                optimized_config = self._optimize_gate_config(
                    gate_name, 
                    current_config, 
                    optimization_params
                )
                optimized_settings[gate_name] = optimized_config
            
            self.logger.info("✅ 設定最適化完了")
            return optimized_settings
            
        except Exception as e:
            self.logger.error(f"❌ 設定最適化エラー: {e}")
            raise
    
    def _get_optimization_params(self, optimization_type: str) -> Dict[str, Any]:
        """最適化パラメータを取得"""
        params = {
            "aggressive": {
                "confidence_threshold_adjustment": -0.1,
                "pattern_weight_adjustment": 0.1,
                "description": "積極的な最適化（信頼度閾値を下げ、パターン重みを上げる）"
            },
            "balanced": {
                "confidence_threshold_adjustment": 0.0,
                "pattern_weight_adjustment": 0.0,
                "description": "バランス型最適化（現在の設定を維持）"
            },
            "conservative": {
                "confidence_threshold_adjustment": 0.1,
                "pattern_weight_adjustment": -0.1,
                "description": "保守的な最適化（信頼度閾値を上げ、パターン重みを下げる）"
            }
        }
        
        return params.get(optimization_type, params["balanced"])
    
    def _optimize_gate_config(
        self, 
        gate_name: str, 
        current_config: Dict[str, Any], 
        optimization_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ゲート設定を最適化"""
        optimized_config = current_config.copy()
        
        # 信頼度閾値の調整
        confidence_adjustment = optimization_params.get("confidence_threshold_adjustment", 0.0)
        
        # パターンの信頼度閾値を調整
        patterns = optimized_config.get('patterns', {})
        for pattern_name, pattern_config in patterns.items():
            if isinstance(pattern_config, dict):
                # 信頼度閾値の調整
                for sub_pattern_name, sub_pattern_config in pattern_config.items():
                    if isinstance(sub_pattern_config, dict) and 'confidence_threshold' in sub_pattern_config:
                        current_threshold = sub_pattern_config['confidence_threshold']
                        new_threshold = max(0.1, min(1.0, current_threshold + confidence_adjustment))
                        sub_pattern_config['confidence_threshold'] = new_threshold
        
        return optimized_config
    
    async def apply_optimized_settings(self, optimized_settings: Dict[str, Any], backup: bool = True):
        """最適化された設定を適用"""
        try:
            self.logger.info("🔧 最適化設定の適用開始")
            
            if backup:
                await self._backup_current_settings()
            
            # 各ゲートの設定を適用
            for gate_name, gate_config in optimized_settings.items():
                gate_num = int(gate_name.replace('gate', ''))
                await self._apply_gate_config(gate_num, gate_config)
            
            self.logger.info("✅ 最適化設定の適用完了")
            
        except Exception as e:
            self.logger.error(f"❌ 設定適用エラー: {e}")
            raise
    
    async def _backup_current_settings(self):
        """現在の設定をバックアップ"""
        try:
            backup_dir = Path("/app/backups/settings")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            
            for gate_num in [1, 2, 3]:
                config_file = self.config_dir / f"gate{gate_num}_patterns.yaml"
                if config_file.exists():
                    backup_file = backup_dir / f"gate{gate_num}_patterns_{timestamp}.yaml"
                    backup_file.write_text(config_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            self.logger.info(f"✅ 設定バックアップ完了: {backup_dir}")
            
        except Exception as e:
            self.logger.error(f"❌ 設定バックアップエラー: {e}")
    
    async def _apply_gate_config(self, gate_num: int, gate_config: Dict[str, Any]):
        """ゲート設定を適用"""
        try:
            config_file = self.config_dir / f"gate{gate_num}_patterns.yaml"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(gate_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            self.logger.info(f"✅ GATE {gate_num} 設定を適用しました: {config_file}")
            
        except Exception as e:
            self.logger.error(f"❌ GATE {gate_num} 設定適用エラー: {e}")
    
    def display_analysis_result(self, analysis_result: Dict[str, Any]):
        """分析結果を表示"""
        try:
            print("=" * 80)
            print("🔧 設定分析レポート")
            print("=" * 80)
            print(f"📅 分析時刻: {analysis_result['analysis_timestamp']}")
            print()
            
            # 現在の設定
            print("⚙️ 現在の設定:")
            for gate_name, gate_config in analysis_result['current_settings'].items():
                print(f"   {gate_name.upper()}:")
                patterns = gate_config.get('patterns', {})
                print(f"      📋 パターン数: {len(patterns)}")
                for pattern_name in patterns.keys():
                    print(f"         • {pattern_name}")
                print()
            
            # パフォーマンスメトリクス
            performance_metrics = analysis_result.get('performance_metrics', {})
            signal_stats = performance_metrics.get('signal_statistics', {})
            print("📊 パフォーマンスメトリクス:")
            print(f"   🎯 総シグナル数: {signal_stats.get('total_signals', 0)}")
            print(f"   💯 平均信頼度: {signal_stats.get('avg_confidence', 0.0):.2f}")
            print(f"   ⭐ 高信頼度シグナル: {signal_stats.get('high_confidence_count', 0)}")
            print(f"   📈 中信頼度シグナル: {signal_stats.get('medium_confidence_count', 0)}")
            print()
            
            # 最適化推奨事項
            recommendations = analysis_result.get('optimization_recommendations', [])
            if recommendations:
                print("💡 最適化推奨事項:")
                for i, recommendation in enumerate(recommendations, 1):
                    print(f"   {i}. {recommendation}")
                print()
            else:
                print("✅ 設定に問題はありません")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ 分析結果表示エラー: {e}")
    
    async def close(self):
        """最適化ツールの終了"""
        try:
            self.logger.info("🔧 設定最適化ツール終了")
            
            if self.connection_manager:
                await self.connection_manager.close()
            
            self.logger.info("✅ 設定最適化ツール終了完了")
            
        except Exception as e:
            self.logger.error(f"❌ 最適化ツール終了エラー: {e}")


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='設定最適化ツール')
    parser.add_argument('command', nargs='?', default='analyze',
                       choices=['analyze', 'optimize', 'help'],
                       help='実行するコマンド')
    parser.add_argument('--type', choices=['aggressive', 'balanced', 'conservative'],
                       default='balanced', help='最適化タイプ')
    parser.add_argument('--apply', action='store_true', help='最適化設定を適用')
    parser.add_argument('--backup', action='store_true', default=True, help='設定をバックアップ')
    
    args = parser.parse_args()
    
    optimizer = SettingsOptimizer()
    
    try:
        # 最適化ツールの初期化
        await optimizer.initialize()
        
        if args.command == 'analyze':
            # 設定分析
            analysis_result = await optimizer.analyze_current_settings()
            optimizer.display_analysis_result(analysis_result)
            
        elif args.command == 'optimize':
            # 設定最適化
            optimized_settings = await optimizer.optimize_settings(args.type)
            
            print("=" * 80)
            print("🔧 最適化された設定")
            print("=" * 80)
            print(f"📅 最適化タイプ: {args.type}")
            print()
            
            for gate_name, gate_config in optimized_settings.items():
                print(f"{gate_name.upper()}:")
                patterns = gate_config.get('patterns', {})
                print(f"   📋 パターン数: {len(patterns)}")
                for pattern_name in patterns.keys():
                    print(f"      • {pattern_name}")
                print()
            
            if args.apply:
                await optimizer.apply_optimized_settings(optimized_settings, args.backup)
                print("✅ 最適化設定を適用しました")
            else:
                print("💡 --apply オプションを指定すると設定を適用できます")
            
            print("=" * 80)
            
        elif args.command == 'help':
            print("=" * 80)
            print("🔧 設定最適化ツール")
            print("=" * 80)
            print()
            print("使用方法:")
            print("  python settings_optimizer.py [コマンド] [オプション]")
            print()
            print("コマンド:")
            print("  analyze          - 現在の設定を分析")
            print("  optimize         - 設定を最適化")
            print("  help             - このヘルプを表示")
            print()
            print("オプション:")
            print("  --type TYPE      - 最適化タイプ (aggressive/balanced/conservative)")
            print("  --apply          - 最適化設定を適用")
            print("  --backup         - 設定をバックアップ (デフォルト: True)")
            print()
            print("例:")
            print("  python settings_optimizer.py analyze")
            print("  python settings_optimizer.py optimize --type aggressive --apply")
            print("  python settings_optimizer.py optimize --type conservative")
            print()
            print("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ ツール実行エラー: {e}")
        sys.exit(1)
    finally:
        await optimizer.close()


if __name__ == "__main__":
    # ツールの実行
    asyncio.run(main())
