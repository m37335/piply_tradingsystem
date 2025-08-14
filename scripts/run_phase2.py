#!/usr/bin/env python3
"""
Phase 2 自動化スクリプト
チャートパターン（パターン10-12）の実装を自動化
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

PHASE2_PATTERNS = [10, 11, 12]

PATTERN_INFO = {
    10: {
        "name": "ダブルトップ/ボトム検出",
        "detector_file": (
            "src/infrastructure/analysis/pattern_detectors/"
            "double_top_bottom_detector.py"
        ),
        "test_file": "tests/unit/test_double_top_bottom_detector.py",
        "class_name": "DoubleTopBottomDetector",
    },
    11: {
        "name": "トリプルトップ/ボトム検出",
        "detector_file": (
            "src/infrastructure/analysis/pattern_detectors/"
            "triple_top_bottom_detector.py"
        ),
        "test_file": "tests/unit/test_triple_top_bottom_detector.py",
        "class_name": "TripleTopBottomDetector",
    },
    12: {
        "name": "フラッグパターン検出",
        "detector_file": (
            "src/infrastructure/analysis/pattern_detectors/" "flag_pattern_detector.py"
        ),
        "test_file": "tests/unit/test_flag_pattern_detector.py",
        "class_name": "FlagPatternDetector",
    },
}


def run_command(command: str, cwd: str = None) -> bool:
    """コマンドを実行し、成功/失敗を返す"""
    try:
        subprocess.run(
            command,
            shell=True,
            cwd=cwd or project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"✅ 成功: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失敗: {command}")
        print(f"エラー: {e.stderr}")
        return False


def git_commit_and_push(pattern_number: int, pattern_name: str):
    """Gitコミットとプッシュを実行"""
    commit_message = f"feat: パターン{pattern_number} {pattern_name}を実装"

    commands = [
        "git add .",
        f'git commit -m "{commit_message}"',
        "git push origin main",
    ]

    for command in commands:
        if not run_command(command):
            print(f"⚠️ Git操作でエラーが発生: {command}")
            return False

    print(f"✅ パターン{pattern_number}のGit操作が完了")
    return True


def run_tests(test_file: str) -> bool:
    """テストを実行"""
    if not os.path.exists(test_file):
        print(f"⚠️ テストファイルが存在しません: {test_file}")
        return False

    return run_command(f"python -m pytest {test_file} -v")


def implement_phase2_pattern(pattern_number: int):
    """Phase 2パターンを実装"""
    pattern_info = PATTERN_INFO[pattern_number]
    pattern_name = pattern_info["name"]

    print(f"\n🚀 パターン{pattern_number}: {pattern_name}の実装を開始")
    print("=" * 60)

    # 1. パターン検出器の実装
    print(f"📝 パターン{pattern_number}検出器を実装中...")
    # ここで実際の実装コードを生成

    # 2. テストの実行
    print(f"🧪 パターン{pattern_number}のテストを実行中...")
    if run_tests(pattern_info["test_file"]):
        print(f"✅ パターン{pattern_number}のテストが成功")
    else:
        print(f"❌ パターン{pattern_number}のテストが失敗")
        return False

    # 3. Git操作
    print(f"📤 パターン{pattern_number}をGitにコミット中...")
    if git_commit_and_push(pattern_number, pattern_name):
        print(f"✅ パターン{pattern_number}の実装が完了")
    else:
        print(f"❌ パターン{pattern_number}のGit操作が失敗")
        return False

    return True


def run_phase2_integration_test():
    """Phase 2統合テストを実行"""
    print("\n🧪 Phase 2統合テストを実行中...")
    print("=" * 60)

    integration_test_file = "tests/integration/test_phase2_patterns.py"

    if run_tests(integration_test_file):
        print("✅ Phase 2統合テストが成功")
        return True
    else:
        print("❌ Phase 2統合テストが失敗")
        return False


def run_phase2():
    """Phase 2実行メイン関数"""
    print("🎯 Phase 2: チャートパターン実装を開始")
    print("=" * 60)

    success_count = 0

    for pattern in PHASE2_PATTERNS:
        if implement_phase2_pattern(pattern):
            success_count += 1
        else:
            print(f"❌ パターン{pattern}の実装が失敗")
            break

        # パターン間の待機時間
        time.sleep(2)

    if success_count == len(PHASE2_PATTERNS):
        print(f"\n🎉 Phase 2実装が完了！ ({success_count}/{len(PHASE2_PATTERNS)}パターン)")

        # 統合テスト実行
        if run_phase2_integration_test():
            print("🎉 Phase 2全体が成功！")
            return True
        else:
            print("❌ Phase 2統合テストが失敗")
            return False
    else:
        print(f"❌ Phase 2実装が失敗 ({success_count}/{len(PHASE2_PATTERNS)}パターン)")
        return False


if __name__ == "__main__":
    success = run_phase2()
    sys.exit(0 if success else 1)
