#!/usr/bin/env python3
"""
パフォーマンス監視ツール

三層ゲート式フィルタリングシステムのパフォーマンスを監視し、
最適化のための詳細な分析を提供します。
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.llm_analysis.core.performance_monitor import performance_monitor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class PerformanceMonitorTool:
    """パフォーマンス監視ツール"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def display_performance_summary(self):
        """パフォーマンスサマリーを表示"""
        try:
            summary = performance_monitor.get_performance_summary()
            
            print("=" * 80)
            print("📊 パフォーマンス監視サマリー")
            print("=" * 80)
            print(f"⏰ 更新時刻: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print()
            
            # メトリクス統計
            print("📈 メトリクス統計:")
            for metric_name, stats in summary['stats'].items():
                print(f"   🔧 {stats['display_name']}:")
                print(f"      📊 実行回数: {stats['count']}")
                print(f"      ⚡ 平均時間: {stats['avg']:.4f}秒")
                print(f"      📈 P95時間: {stats['p95']:.4f}秒")
                print(f"      🆕 最新時間: {stats['last']:.4f}秒")
                print()
            
            # 推奨事項
            if summary['recommendations']:
                print("💡 パフォーマンス改善推奨事項:")
                for i, recommendation in enumerate(summary['recommendations'], 1):
                    print(f"   {i}. {recommendation}")
                print()
            else:
                print("✅ パフォーマンスに問題はありません")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ パフォーマンスサマリー表示エラー: {e}")
    
    def display_detailed_stats(self):
        """詳細統計を表示"""
        try:
            all_stats = performance_monitor.get_all_stats()
            
            print("=" * 80)
            print("📊 詳細パフォーマンス統計")
            print("=" * 80)
            print(f"⏰ 更新時刻: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print()
            
            for metric_name, stats in all_stats.items():
                print(f"🔧 {metric_name}:")
                print(f"   📊 実行回数: {stats.count}")
                print(f"   📈 最小時間: {stats.min_value:.4f}秒")
                print(f"   📈 最大時間: {stats.max_value:.4f}秒")
                print(f"   ⚡ 平均時間: {stats.avg_value:.4f}秒")
                print(f"   📊 中央値: {stats.median_value:.4f}秒")
                print(f"   📈 P95時間: {stats.p95_value:.4f}秒")
                print(f"   📈 P99時間: {stats.p99_value:.4f}秒")
                print(f"   🆕 最新時間: {stats.last_value:.4f}秒")
                print(f"   ⏰ 最終更新: {stats.last_updated.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                print()
            
            print("=" * 80)
            
        except Exception as e:
            self.logger.error(f"❌ 詳細統計表示エラー: {e}")
    
    def export_performance_data(self, output_file: str = None):
        """パフォーマンスデータをエクスポート"""
        try:
            if output_file is None:
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                output_file = f"/app/performance_data_{timestamp}.json"
            
            export_data = performance_monitor.export_stats()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"✅ パフォーマンスデータをエクスポートしました: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"❌ パフォーマンスデータエクスポートエラー: {e}")
            return None
    
    def clear_performance_data(self, metric_name: str = None):
        """パフォーマンスデータをクリア"""
        try:
            performance_monitor.clear_history(metric_name)
            
            if metric_name:
                self.logger.info(f"✅ メトリクス '{metric_name}' のデータをクリアしました")
            else:
                self.logger.info("✅ すべてのパフォーマンスデータをクリアしました")
                
        except Exception as e:
            self.logger.error(f"❌ パフォーマンスデータクリアエラー: {e}")
    
    def display_help(self):
        """ヘルプを表示"""
        print("=" * 80)
        print("📊 パフォーマンス監視ツール")
        print("=" * 80)
        print()
        print("使用方法:")
        print("  python performance_monitor_tool.py [コマンド] [オプション]")
        print()
        print("コマンド:")
        print("  summary          - パフォーマンスサマリーを表示")
        print("  detailed         - 詳細統計を表示")
        print("  export [ファイル] - パフォーマンスデータをエクスポート")
        print("  clear [メトリクス] - パフォーマンスデータをクリア")
        print("  help             - このヘルプを表示")
        print()
        print("例:")
        print("  python performance_monitor_tool.py summary")
        print("  python performance_monitor_tool.py detailed")
        print("  python performance_monitor_tool.py export /tmp/performance.json")
        print("  python performance_monitor_tool.py clear gate1_evaluation_time")
        print()
        print("=" * 80)


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='パフォーマンス監視ツール')
    parser.add_argument('command', nargs='?', default='summary', 
                       choices=['summary', 'detailed', 'export', 'clear', 'help'],
                       help='実行するコマンド')
    parser.add_argument('argument', nargs='?', help='コマンドの引数')
    
    args = parser.parse_args()
    
    tool = PerformanceMonitorTool()
    
    try:
        if args.command == 'summary':
            tool.display_performance_summary()
        elif args.command == 'detailed':
            tool.display_detailed_stats()
        elif args.command == 'export':
            output_file = tool.export_performance_data(args.argument)
            if output_file:
                print(f"✅ パフォーマンスデータをエクスポートしました: {output_file}")
        elif args.command == 'clear':
            tool.clear_performance_data(args.argument)
        elif args.command == 'help':
            tool.display_help()
        else:
            tool.display_help()
            
    except Exception as e:
        logger.error(f"❌ ツール実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # ツールの実行
    asyncio.run(main())
