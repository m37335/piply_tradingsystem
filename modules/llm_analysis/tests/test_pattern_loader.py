#!/usr/bin/env python3
"""
PatternLoaderの直接テスト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.llm_analysis.core.pattern_loader import PatternLoader

def test_pattern_loader():
    """PatternLoaderのテスト"""
    print("PatternLoaderテスト開始")
    
    # 設定ディレクトリの確認
    config_dir = Path("modules/llm_analysis/config")
    print(f"設定ディレクトリ: {config_dir}")
    print(f"存在確認: {config_dir.exists()}")
    
    if config_dir.exists():
        files = list(config_dir.glob("*.yaml"))
        print(f"YAMLファイル: {files}")
    
    # PatternLoaderの初期化
    loader = PatternLoader(config_dir="/app/modules/llm_analysis/config")
    print(f"PatternLoader初期化完了")
    print(f"設定ディレクトリ: {loader.config_dir}")
    print(f"設定ディレクトリ存在確認: {loader.config_dir.exists()}")
    
    # GATE 1のパターン設定読み込み
    try:
        patterns = loader.load_gate_patterns(1)
        print(f"GATE 1 パターン設定読み込み成功")
        print(f"パターン数: {len(patterns.get('patterns', {}))}")
        for pattern_name in patterns.get('patterns', {}).keys():
            print(f"  - {pattern_name}")
    except Exception as e:
        print(f"GATE 1 パターン設定読み込みエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pattern_loader()
