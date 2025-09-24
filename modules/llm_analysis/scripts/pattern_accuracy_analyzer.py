#!/usr/bin/env python3
"""
パターン精度分析ツール

三層ゲート式フィルタリングシステムのパターン精度を分析し、
改善のための詳細な統計と推奨事項を提供します。
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


class PatternAccuracyAnalyzer:
    """パターン精度分析ツール"""
    
    def __init__(self):
        self.connection_manager = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """分析ツールの初期化"""
        try:
            self.logger.info("🔧 パターン精度分析ツール初期化開始")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=2,
                max_connections=5
            )
            await self.connection_manager.initialize()
            
            self.logger.info("✅ パターン精度分析ツール初期化完了")
            
        except Exception as e:
            self.logger.error(f"❌ 分析ツール初期化エラー: {e}")
            raise
    
    async def analyze_pattern_accuracy(self, days: int = 7) -> Dict[str, Any]:
        """
        パターン精度を分析
        
        Args:
            days: 分析期間（日数）
            
        Returns:
            分析結果
        """
        try:
            self.logger.info(f"📊 パターン精度分析開始 (過去{days}日間)")
            
            analysis_result = {
                'analysis_period': f"{days}日間",
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'gate_statistics': {},
                'pattern_effectiveness': {},
                'recommendations': []
            }
            
            # 各ゲートの統計を分析
            for gate_num in [1, 2, 3]:
                gate_stats = await self._analyze_gate_statistics(gate_num, days)
                analysis_result['gate_statistics'][f'gate{gate_num}'] = gate_stats
            
            # パターン効果性を分析
            pattern_effectiveness = await self._analyze_pattern_effectiveness(days)
            analysis_result['pattern_effectiveness'] = pattern_effectiveness
            
            # 推奨事項を生成
            recommendations = self._generate_recommendations(analysis_result)
            analysis_result['recommendations'] = recommendations
            
            self.logger.info("✅ パターン精度分析完了")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"❌ パターン精度分析エラー: {e}")
            raise
    
    async def _analyze_gate_statistics(self, gate_num: int, days: int) -> Dict[str, Any]:
        """ゲート統計を分析"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # ゲート通過率の統計
                gate_stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_evaluations,
                        COUNT(CASE WHEN gate{gate_num}_confidence >= 0.7 THEN 1 END) as passed_evaluations,
                        AVG(gate{gate_num}_confidence) as avg_confidence,
                        MIN(gate{gate_num}_confidence) as min_confidence,
                        MAX(gate{gate_num}_confidence) as max_confidence,
                        COUNT(DISTINCT gate{gate_num}_pattern) as unique_patterns
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                """)
                
                # パターン別統計
                pattern_stats = await conn.fetch(f"""
                    SELECT 
                        gate{gate_num}_pattern as pattern_name,
                        COUNT(*) as usage_count,
                        AVG(gate{gate_num}_confidence) as avg_confidence,
                        COUNT(CASE WHEN gate{gate_num}_confidence >= 0.7 THEN 1 END) as pass_count
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                    GROUP BY gate{gate_num}_pattern
                    ORDER BY usage_count DESC
                """)
                
                # 通過率の計算
                pass_rate = 0.0
                if gate_stats['total_evaluations'] > 0:
                    pass_rate = gate_stats['passed_evaluations'] / gate_stats['total_evaluations']
                
                return {
                    'total_evaluations': gate_stats['total_evaluations'] or 0,
                    'passed_evaluations': gate_stats['passed_evaluations'] or 0,
                    'pass_rate': pass_rate,
                    'avg_confidence': float(gate_stats['avg_confidence'] or 0.0),
                    'min_confidence': float(gate_stats['min_confidence'] or 0.0),
                    'max_confidence': float(gate_stats['max_confidence'] or 0.0),
                    'unique_patterns': gate_stats['unique_patterns'] or 0,
                    'pattern_breakdown': [
                        {
                            'pattern_name': row['pattern_name'],
                            'usage_count': row['usage_count'],
                            'avg_confidence': float(row['avg_confidence'] or 0.0),
                            'pass_count': row['pass_count'],
                            'pass_rate': row['pass_count'] / row['usage_count'] if row['usage_count'] > 0 else 0.0
                        }
                        for row in pattern_stats
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"❌ GATE {gate_num} 統計分析エラー: {e}")
            return {}
    
    async def _analyze_pattern_effectiveness(self, days: int) -> Dict[str, Any]:
        """パターン効果性を分析"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # シグナル生成統計
                signal_stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
                        COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals,
                        AVG(overall_confidence) as avg_confidence,
                        COUNT(CASE WHEN overall_confidence >= 0.8 THEN 1 END) as high_confidence_signals
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                """)
                
                # ゲート通過パターンの統計
                gate_pattern_stats = await conn.fetch(f"""
                    SELECT 
                        gate1_pattern,
                        gate2_pattern,
                        gate3_pattern,
                        COUNT(*) as signal_count,
                        AVG(overall_confidence) as avg_confidence,
                        COUNT(CASE WHEN overall_confidence >= 0.8 THEN 1 END) as high_confidence_count
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '{days} days'
                    GROUP BY gate1_pattern, gate2_pattern, gate3_pattern
                    ORDER BY signal_count DESC
                    LIMIT 10
                """)
                
                # 高信頼度シグナル率の計算
                high_confidence_rate = 0.0
                if signal_stats['total_signals'] > 0:
                    high_confidence_rate = signal_stats['high_confidence_signals'] / signal_stats['total_signals']
                
                return {
                    'total_signals': signal_stats['total_signals'] or 0,
                    'buy_signals': signal_stats['buy_signals'] or 0,
                    'sell_signals': signal_stats['sell_signals'] or 0,
                    'avg_confidence': float(signal_stats['avg_confidence'] or 0.0),
                    'high_confidence_signals': signal_stats['high_confidence_signals'] or 0,
                    'high_confidence_rate': high_confidence_rate,
                    'top_gate_patterns': [
                        {
                            'gate1_pattern': row['gate1_pattern'],
                            'gate2_pattern': row['gate2_pattern'],
                            'gate3_pattern': row['gate3_pattern'],
                            'signal_count': row['signal_count'],
                            'avg_confidence': float(row['avg_confidence'] or 0.0),
                            'high_confidence_count': row['high_confidence_count'],
                            'high_confidence_rate': row['high_confidence_count'] / row['signal_count'] if row['signal_count'] > 0 else 0.0
                        }
                        for row in gate_pattern_stats
                    ]
                }
                
        except Exception as e:
            self.logger.error(f"❌ パターン効果性分析エラー: {e}")
            return {}
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """推奨事項を生成"""
        recommendations = []
        
        # ゲート統計から推奨事項を生成
        for gate_name, gate_stats in analysis_result['gate_statistics'].items():
            if gate_stats.get('total_evaluations', 0) == 0:
                continue
            
            pass_rate = gate_stats.get('pass_rate', 0.0)
            avg_confidence = gate_stats.get('avg_confidence', 0.0)
            
            # 通過率が低い場合
            if pass_rate < 0.1:  # 10%未満
                recommendations.append(
                    f"{gate_name.upper()}の通過率が{pass_rate:.1%}と低いです。"
                    "パターン条件の緩和を検討してください。"
                )
            elif pass_rate > 0.8:  # 80%以上
                recommendations.append(
                    f"{gate_name.upper()}の通過率が{pass_rate:.1%}と高いです。"
                    "パターン条件の厳格化を検討してください。"
                )
            
            # 信頼度が低い場合
            if avg_confidence < 0.5:
                recommendations.append(
                    f"{gate_name.upper()}の平均信頼度が{avg_confidence:.2f}と低いです。"
                    "パターン条件の見直しを検討してください。"
                )
        
        # パターン効果性から推奨事項を生成
        pattern_effectiveness = analysis_result.get('pattern_effectiveness', {})
        high_confidence_rate = pattern_effectiveness.get('high_confidence_rate', 0.0)
        
        if high_confidence_rate < 0.3:  # 30%未満
            recommendations.append(
                f"高信頼度シグナル率が{high_confidence_rate:.1%}と低いです。"
                "全体的なパターン精度の向上を検討してください。"
            )
        
        # パターン使用頻度の偏りをチェック
        for gate_name, gate_stats in analysis_result['gate_statistics'].items():
            pattern_breakdown = gate_stats.get('pattern_breakdown', [])
            if len(pattern_breakdown) > 1:
                # 最も使用頻度の高いパターンと低いパターンの差をチェック
                max_usage = max(p['usage_count'] for p in pattern_breakdown)
                min_usage = min(p['usage_count'] for p in pattern_breakdown)
                
                if max_usage > min_usage * 10:  # 10倍以上の差
                    recommendations.append(
                        f"{gate_name.upper()}でパターン使用頻度に偏りがあります。"
                        "使用頻度の低いパターンの見直しを検討してください。"
                    )
        
        return recommendations
    
    def display_analysis_result(self, analysis_result: Dict[str, Any]):
        """分析結果を表示"""
        try:
            print("=" * 80)
            print("📊 パターン精度分析レポート")
            print("=" * 80)
            print(f"⏰ 分析期間: {analysis_result['analysis_period']}")
            print(f"📅 分析時刻: {analysis_result['analysis_timestamp']}")
            print()
            
            # ゲート統計
            print("🚪 ゲート統計:")
            for gate_name, gate_stats in analysis_result['gate_statistics'].items():
                print(f"   {gate_name.upper()}:")
                print(f"      📊 総評価回数: {gate_stats.get('total_evaluations', 0)}")
                print(f"      ✅ 通過回数: {gate_stats.get('passed_evaluations', 0)}")
                print(f"      📈 通過率: {gate_stats.get('pass_rate', 0.0):.1%}")
                print(f"      💯 平均信頼度: {gate_stats.get('avg_confidence', 0.0):.2f}")
                print(f"      🔧 ユニークパターン数: {gate_stats.get('unique_patterns', 0)}")
                
                # パターン別統計
                pattern_breakdown = gate_stats.get('pattern_breakdown', [])
                if pattern_breakdown:
                    print(f"      📋 パターン別統計:")
                    for pattern in pattern_breakdown[:3]:  # 上位3パターン
                        print(f"         • {pattern['pattern_name']}: "
                              f"使用{pattern['usage_count']}回, "
                              f"通過率{pattern['pass_rate']:.1%}, "
                              f"信頼度{pattern['avg_confidence']:.2f}")
                print()
            
            # パターン効果性
            pattern_effectiveness = analysis_result.get('pattern_effectiveness', {})
            print("🎯 パターン効果性:")
            print(f"   📊 総シグナル数: {pattern_effectiveness.get('total_signals', 0)}")
            print(f"   📈 買いシグナル: {pattern_effectiveness.get('buy_signals', 0)}")
            print(f"   📉 売りシグナル: {pattern_effectiveness.get('sell_signals', 0)}")
            print(f"   💯 平均信頼度: {pattern_effectiveness.get('avg_confidence', 0.0):.2f}")
            print(f"   ⭐ 高信頼度シグナル率: {pattern_effectiveness.get('high_confidence_rate', 0.0):.1%}")
            print()
            
            # 推奨事項
            recommendations = analysis_result.get('recommendations', [])
            if recommendations:
                print("💡 改善推奨事項:")
                for i, recommendation in enumerate(recommendations, 1):
                    print(f"   {i}. {recommendation}")
                print()
            else:
                print("✅ パターン精度に問題はありません")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ 分析結果表示エラー: {e}")
    
    async def close(self):
        """分析ツールの終了"""
        try:
            self.logger.info("🔧 パターン精度分析ツール終了")
            
            if self.connection_manager:
                await self.connection_manager.close()
            
            self.logger.info("✅ パターン精度分析ツール終了完了")
            
        except Exception as e:
            self.logger.error(f"❌ 分析ツール終了エラー: {e}")


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='パターン精度分析ツール')
    parser.add_argument('--days', type=int, default=7, help='分析期間（日数）')
    parser.add_argument('--export', type=str, help='結果をエクスポートするファイルパス')
    
    args = parser.parse_args()
    
    analyzer = PatternAccuracyAnalyzer()
    
    try:
        # 分析ツールの初期化と実行
        await analyzer.initialize()
        analysis_result = await analyzer.analyze_pattern_accuracy(days=args.days)
        
        # 結果の表示
        analyzer.display_analysis_result(analysis_result)
        
        # エクスポート
        if args.export:
            with open(args.export, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"✅ 分析結果をエクスポートしました: {args.export}")
        
    except Exception as e:
        logger.error(f"❌ 分析ツールエラー: {e}")
        sys.exit(1)
    finally:
        await analyzer.close()


if __name__ == "__main__":
    # 分析ツールの実行
    asyncio.run(main())
