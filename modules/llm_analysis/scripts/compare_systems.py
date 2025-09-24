#!/usr/bin/env python3
"""
システム比較ツール

既存のイベント駆動システムと新しい三層ゲート式フィルタリングシステムの
パフォーマンスを比較します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

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


class SystemComparator:
    """システム比較ツール"""
    
    def __init__(self):
        self.connection_manager = None
        
    async def initialize(self):
        """比較ツールの初期化"""
        try:
            logger.info("🔧 システム比較ツール初期化開始")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=2,
                max_connections=5
            )
            await self.connection_manager.initialize()
            
            logger.info("✅ システム比較ツール初期化完了")
            
        except Exception as e:
            logger.error(f"❌ 比較ツール初期化エラー: {e}")
            raise
    
    async def compare_systems(self, hours: int = 24):
        """システムの比較"""
        try:
            logger.info(f"📊 システム比較開始 (過去{hours}時間)")
            
            # 既存システムの統計
            existing_stats = await self._get_existing_system_stats(hours)
            
            # 新システムの統計
            new_stats = await self._get_new_system_stats(hours)
            
            # 比較結果の表示
            self._display_comparison(existing_stats, new_stats, hours)
            
        except Exception as e:
            logger.error(f"❌ システム比較エラー: {e}")
    
    async def _get_existing_system_stats(self, hours: int) -> dict:
        """既存システムの統計取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # ルールベース分析結果の統計
                rule_stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_analyses,
                        COUNT(CASE WHEN confidence_score >= 0.7 THEN 1 END) as signals_generated,
                        AVG(confidence_score) as avg_score,
                        MAX(created_at) as last_analysis
                    FROM llm_analysis_results 
                    WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                """)
                
                # イベント処理統計
                event_stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_events,
                        COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_events,
                        AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time
                    FROM events 
                    WHERE event_type = 'data_collection_completed' 
                    AND created_at >= NOW() - INTERVAL '{hours} hours'
                """)
                
                return {
                    'rule_analyses': rule_stats['total_analyses'] or 0,
                    'signals_generated': rule_stats['signals_generated'] or 0,
                    'avg_score': rule_stats['avg_score'] or 0.0,
                    'last_analysis': rule_stats['last_analysis'],
                    'total_events': event_stats['total_events'] or 0,
                    'processed_events': event_stats['processed_events'] or 0,
                    'avg_processing_time': event_stats['avg_processing_time'] or 0.0
                }
                
        except Exception as e:
            logger.error(f"❌ 既存システム統計取得エラー: {e}")
            return {}
    
    async def _get_new_system_stats(self, hours: int) -> dict:
        """新システムの統計取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 三層ゲートシグナルの統計
                signal_stats = await conn.fetchrow(f"""
                    SELECT 
                        COUNT(*) as total_signals,
                        COUNT(CASE WHEN signal_type = 'BUY' THEN 1 END) as buy_signals,
                        COUNT(CASE WHEN signal_type = 'SELL' THEN 1 END) as sell_signals,
                        AVG(overall_confidence) as avg_confidence,
                        MAX(created_at) as last_signal
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                """)
                
                # ゲート通過率の統計
                gate_stats = await conn.fetch(f"""
                    SELECT 
                        gate1_pattern,
                        gate2_pattern,
                        gate3_pattern,
                        COUNT(*) as count,
                        AVG(overall_confidence) as avg_confidence
                    FROM three_gate_signals 
                    WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                    GROUP BY gate1_pattern, gate2_pattern, gate3_pattern
                    ORDER BY count DESC
                """)
                
                return {
                    'total_signals': signal_stats['total_signals'] or 0,
                    'buy_signals': signal_stats['buy_signals'] or 0,
                    'sell_signals': signal_stats['sell_signals'] or 0,
                    'avg_confidence': signal_stats['avg_confidence'] or 0.0,
                    'last_signal': signal_stats['last_signal'],
                    'gate_patterns': [
                        {
                            'gate1': row['gate1_pattern'],
                            'gate2': row['gate2_pattern'],
                            'gate3': row['gate3_pattern'],
                            'count': row['count'],
                            'avg_confidence': row['avg_confidence']
                        }
                        for row in gate_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"❌ 新システム統計取得エラー: {e}")
            return {}
    
    def _display_comparison(self, existing_stats: dict, new_stats: dict, hours: int):
        """比較結果の表示"""
        print("=" * 100)
        print("📊 システム比較レポート")
        print("=" * 100)
        print(f"⏰ 比較期間: 過去{hours}時間")
        print(f"📅 比較時刻: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        # 既存システムの統計
        print("🔧 既存システム (イベント駆動 + ルールベース):")
        print(f"   📊 総分析回数: {existing_stats.get('rule_analyses', 0)}")
        print(f"   🎯 シグナル生成数: {existing_stats.get('signals_generated', 0)}")
        print(f"   📈 平均スコア: {existing_stats.get('avg_score', 0.0):.2f}")
        print(f"   ⏰ 最終分析: {existing_stats.get('last_analysis', 'なし')}")
        print(f"   🔄 総イベント数: {existing_stats.get('total_events', 0)}")
        print(f"   ✅ 処理済みイベント: {existing_stats.get('processed_events', 0)}")
        print(f"   ⚡ 平均処理時間: {existing_stats.get('avg_processing_time', 0.0):.2f}秒")
        
        # シグナル生成率の計算
        existing_rate = (
            existing_stats.get('signals_generated', 0) / existing_stats.get('rule_analyses', 1) * 100
            if existing_stats.get('rule_analyses', 0) > 0 else 0
        )
        print(f"   📊 シグナル生成率: {existing_rate:.1f}%")
        print()
        
        # 新システムの統計
        print("🚪 新システム (三層ゲート式フィルタリング):")
        print(f"   🎯 総シグナル数: {new_stats.get('total_signals', 0)}")
        print(f"   📈 買いシグナル: {new_stats.get('buy_signals', 0)}")
        print(f"   📉 売りシグナル: {new_stats.get('sell_signals', 0)}")
        print(f"   💯 平均信頼度: {new_stats.get('avg_confidence', 0.0):.2f}")
        print(f"   ⏰ 最終シグナル: {new_stats.get('last_signal', 'なし')}")
        print()
        
        # ゲート通過パターン
        gate_patterns = new_stats.get('gate_patterns', [])
        if gate_patterns:
            print("🚪 ゲート通過パターン:")
            for pattern in gate_patterns[:5]:  # 上位5パターン
                print(f"   📊 {pattern['gate1']} → {pattern['gate2']} → {pattern['gate3']}")
                print(f"      💯 回数: {pattern['count']}, 平均信頼度: {pattern['avg_confidence']:.2f}")
            print()
        
        # 比較サマリー
        print("📈 比較サマリー:")
        if existing_stats.get('rule_analyses', 0) > 0 and new_stats.get('total_signals', 0) > 0:
            print(f"   🔄 既存システム: {existing_stats.get('rule_analyses', 0)}回分析 → {existing_stats.get('signals_generated', 0)}シグナル")
            print(f"   🚪 新システム: {new_stats.get('total_signals', 0)}シグナル生成")
            print(f"   📊 新システムの信頼度: {new_stats.get('avg_confidence', 0.0):.2f}")
            
            if existing_rate > 0:
                improvement = new_stats.get('avg_confidence', 0.0) - existing_stats.get('avg_score', 0.0)
                print(f"   📈 信頼度改善: {improvement:+.2f}")
        else:
            print("   ⚠️ 比較データが不足しています")
        
        print("=" * 100)
    
    async def close(self):
        """比較ツールの終了"""
        try:
            logger.info("🔧 システム比較ツール終了")
            
            if self.connection_manager:
                await self.connection_manager.close()
            
            logger.info("✅ システム比較ツール終了完了")
            
        except Exception as e:
            logger.error(f"❌ 比較ツール終了エラー: {e}")


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='システム比較ツール')
    parser.add_argument('--hours', type=int, default=24, help='比較期間（時間）')
    args = parser.parse_args()
    
    comparator = SystemComparator()
    
    try:
        # 比較ツールの初期化と実行
        await comparator.initialize()
        await comparator.compare_systems(hours=args.hours)
        
    except Exception as e:
        logger.error(f"❌ 比較ツールエラー: {e}")
        sys.exit(1)
    finally:
        await comparator.close()


if __name__ == "__main__":
    # 比較ツールの実行
    asyncio.run(main())
