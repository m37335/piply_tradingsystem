#!/usr/bin/env python3
"""
メモリ最適化システムテスト
"""

import asyncio
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, "/app")

from src.infrastructure.optimization.memory_optimizer import MemoryOptimizer


class MemoryOptimizerTester:
    """メモリ最適化システムテスト"""
    
    def __init__(self):
        self.optimizer = None
    
    def initialize(self):
        """初期化"""
        print("🔧 メモリ最適化システムテストを初期化中...")
        
        self.optimizer = MemoryOptimizer()
        
        print("✅ 初期化完了")
    
    def test_memory_snapshot(self):
        """メモリスナップショットテスト"""
        print("\n📊 メモリスナップショットテスト...")
        
        try:
            snapshot = self.optimizer.take_memory_snapshot()
            
            print("✅ メモリスナップショット取得成功")
            print(f"   📅 時刻: {snapshot.timestamp}")
            print(f"   💾 メモリ使用量: {snapshot.memory_usage_mb:.1f} MB")
            print(f"   📊 メモリ使用率: {snapshot.memory_percent:.1f}%")
            print(f"   💿 利用可能メモリ: {snapshot.available_mb:.1f} MB")
            print(f"   🗄️  総メモリ: {snapshot.total_mb:.1f} MB")
            
            print(f"   🔧 ガベージコレクション統計:")
            gc_counts = snapshot.gc_stats['counts']
            print(f"     gen0: {gc_counts[0]}, gen1: {gc_counts[1]}, gen2: {gc_counts[2]}")
            
            print(f"   📋 オブジェクト数:")
            for obj_type, count in snapshot.object_counts.items():
                print(f"     {obj_type}: {count:,}個")
            
            return True
        except Exception as e:
            print(f"❌ メモリスナップショットテストエラー: {e}")
            return False
    
    def test_memory_leak_detection(self):
        """メモリリーク検出テスト"""
        print("\n🔍 メモリリーク検出テスト...")
        
        try:
            # 複数のスナップショットを取得
            print("  📊 複数スナップショット取得中...")
            for i in range(3):
                self.optimizer.take_memory_snapshot()
                print(f"    スナップショット {i+1} 完了")
                time.sleep(1)
            
            # リーク検出
            leaks = self.optimizer.detect_memory_leaks(hours=1)
            
            print(f"✅ メモリリーク検出完了: {len(leaks)}件")
            
            for leak in leaks:
                print(f"  🚨 リーク検出:")
                print(f"     オブジェクトタイプ: {leak.object_type}")
                print(f"     増加数: +{leak.count_increase}個")
                print(f"     メモリ増加: +{leak.memory_increase_mb:.1f} MB")
                print(f"     期間: {leak.duration_minutes:.1f}分")
                print(f"     深刻度: {leak.severity}")
            
            return True
        except Exception as e:
            print(f"❌ メモリリーク検出テストエラー: {e}")
            return False
    
    def test_memory_optimization(self):
        """メモリ最適化テスト"""
        print("\n🔧 メモリ最適化テスト...")
        
        try:
            # 最適化前のスナップショット
            before_snapshot = self.optimizer.take_memory_snapshot()
            print(f"  📊 最適化前: {before_snapshot.memory_usage_mb:.1f} MB")
            
            # メモリ最適化実行
            results = self.optimizer.optimize_memory_usage()
            
            print("✅ メモリ最適化完了")
            print(f"   📊 最適化前: {results['before_mb']:.1f} MB")
            print(f"   📊 最適化後: {results['after_mb']:.1f} MB")
            print(f"   💾 解放メモリ: {results['freed_mb']:.1f} MB")
            print(f"   🔄 GC実行回数: {results['gc_runs']}回")
            
            print(f"   📋 実行された最適化:")
            for optimization in results['optimizations']:
                print(f"     - {optimization}")
            
            return True
        except Exception as e:
            print(f"❌ メモリ最適化テストエラー: {e}")
            return False
    
    def test_memory_statistics(self):
        """メモリ統計情報テスト"""
        print("\n📈 メモリ統計情報テスト...")
        
        try:
            # 複数のスナップショットを取得
            for i in range(5):
                self.optimizer.take_memory_snapshot()
                time.sleep(0.5)
            
            # 統計情報を取得
            stats = self.optimizer.get_memory_statistics(hours=1)
            
            if 'error' in stats:
                print(f"⚠️  統計情報エラー: {stats['error']}")
                return False
            
            print("✅ メモリ統計情報取得成功")
            print(f"   📅 期間: {stats['period_hours']}時間")
            print(f"   📊 スナップショット数: {stats['snapshot_count']}")
            
            # メモリ使用量統計
            memory_usage = stats['memory_usage']
            print(f"   💾 メモリ使用量:")
            print(f"     現在: {memory_usage['current_mb']:.1f} MB")
            print(f"     平均: {memory_usage['average_mb']:.1f} MB")
            print(f"     最小: {memory_usage['min_mb']:.1f} MB")
            print(f"     最大: {memory_usage['max_mb']:.1f} MB")
            print(f"     傾向: {memory_usage['trend']}")
            
            # メモリ使用率統計
            memory_percent = stats['memory_percent']
            print(f"   📊 メモリ使用率:")
            print(f"     現在: {memory_percent['current']:.1f}%")
            print(f"     平均: {memory_percent['average']:.1f}%")
            print(f"     最小: {memory_percent['min']:.1f}%")
            print(f"     最大: {memory_percent['max']:.1f}%")
            
            return True
        except Exception as e:
            print(f"❌ メモリ統計情報テストエラー: {e}")
            return False
    
    def test_memory_recommendations(self):
        """メモリ推奨事項テスト"""
        print("\n💡 メモリ推奨事項テスト...")
        
        try:
            recommendations = self.optimizer.get_memory_recommendations()
            
            print(f"✅ メモリ推奨事項取得成功: {len(recommendations)}件")
            
            for rec in recommendations:
                severity_icon = "🔴" if rec['severity'] == 'high' else "🟡"
                print(f"  {severity_icon} {rec['message']}")
                print(f"     💡 {rec['action']}")
            
            return True
        except Exception as e:
            print(f"❌ メモリ推奨事項テストエラー: {e}")
            return False
    
    def test_memory_report(self):
        """メモリレポートテスト"""
        print("\n📋 メモリレポートテスト...")
        
        try:
            report = self.optimizer.generate_memory_report()
            
            print("✅ メモリレポート生成成功")
            print(f"   📅 生成時刻: {report['timestamp']}")
            
            if report['current_snapshot']:
                snapshot = report['current_snapshot']
                print(f"   💾 現在のメモリ使用量: {snapshot['memory_usage_mb']:.1f} MB")
                print(f"   📊 現在のメモリ使用率: {snapshot['memory_percent']:.1f}%")
            
            print(f"   🚨 リーク検出: {len(report['leaks'])}件")
            print(f"   💡 推奨事項: {len(report['recommendations'])}件")
            
            return True
        except Exception as e:
            print(f"❌ メモリレポートテストエラー: {e}")
            return False
    
    def run_all_tests(self):
        """全テストを実行"""
        print("🚀 メモリ最適化システムテスト開始")
        print("=" * 60)
        
        self.initialize()
        
        tests = [
            ("メモリスナップショット", self.test_memory_snapshot),
            ("メモリリーク検出", self.test_memory_leak_detection),
            ("メモリ最適化", self.test_memory_optimization),
            ("メモリ統計情報", self.test_memory_statistics),
            ("メモリ推奨事項", self.test_memory_recommendations),
            ("メモリレポート", self.test_memory_report),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"❌ {test_name}で予期しないエラー: {e}")
                results.append((test_name, False))
        
        # 結果サマリー
        print("\n" + "=" * 60)
        print("📊 テスト結果サマリー")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n結果: {passed}/{total} テスト成功")
        
        if passed == total:
            print("🎉 全テスト成功！メモリ最適化システムは正常に動作しています。")
        else:
            print("⚠️  一部のテストが失敗しました。詳細を確認してください。")
    
    def cleanup(self):
        """クリーンアップ"""
        print("\n🧹 クリーンアップ完了")


def main():
    """メイン関数"""
    tester = MemoryOptimizerTester()
    try:
        tester.run_all_tests()
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()
