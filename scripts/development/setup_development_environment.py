#!/usr/bin/env python3
"""
開発環境セットアップスクリプト

このスクリプトは、CLIデータベース初期化システムの開発に必要な
ツールと設定を自動的にセットアップします。
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """コマンドを実行し、結果を表示"""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} 完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗: {e}")
        print(f"エラー出力: {e.stderr}")
        return False


def create_pyproject_toml() -> bool:
    """pyproject.tomlファイルを作成"""
    print("🔄 pyproject.tomlファイルを作成...")

    content = """[tool.black]
line-length = 88
target-version = ['py39']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    ".mypy_cache",
    ".tox"
]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--verbose",
    "--tb=short"
]
"""

    try:
        with open("pyproject.toml", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ pyproject.tomlファイルを作成完了")
        return True
    except Exception as e:
        print(f"❌ pyproject.tomlファイル作成失敗: {e}")
        return False


def create_pre_commit_config() -> bool:
    """pre-commit設定ファイルを作成"""
    print("🔄 pre-commit設定ファイルを作成...")

    content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
"""

    try:
        with open(".pre-commit-config.yaml", "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ pre-commit設定ファイルを作成完了")
        return True
    except Exception as e:
        print(f"❌ pre-commit設定ファイル作成失敗: {e}")
        return False


def create_vscode_settings() -> bool:
    """VSCode設定ファイルを作成"""
    print("🔄 VSCode設定ファイルを作成...")

    # .vscodeディレクトリを作成
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    settings_content = """{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.flake8Args": ["--max-line-length=88"],
    "python.linting.pylintEnabled": false,
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".pytest_cache": true,
        ".mypy_cache": true
    }
}"""

    try:
        with open(vscode_dir / "settings.json", "w", encoding="utf-8") as f:
            f.write(settings_content)
        print("✅ VSCode設定ファイルを作成完了")
        return True
    except Exception as e:
        print(f"❌ VSCode設定ファイル作成失敗: {e}")
        return False


def main():
    """メイン関数"""
    print("🚀 開発環境セットアップを開始します")
    print("=" * 60)

    # 必要なパッケージのインストール
    packages = ["black", "isort", "flake8", "mypy", "pytest", "pre-commit"]

    success_count = 0
    total_count = len(packages) + 4  # パッケージ + 設定ファイル作成

    # パッケージのインストール
    for package in packages:
        if run_command(f"pip install {package}", f"{package}のインストール"):
            success_count += 1

    # 設定ファイルの作成
    if create_pyproject_toml():
        success_count += 1

    if create_pre_commit_config():
        success_count += 1

    if create_vscode_settings():
        success_count += 1

    # pre-commitフックのインストール
    if run_command("pre-commit install", "pre-commitフックのインストール"):
        success_count += 1

    # 結果の表示
    print("=" * 60)
    print(f"📊 セットアップ結果: {success_count}/{total_count} 完了")

    if success_count == total_count:
        print("🎉 開発環境のセットアップが完了しました！")
        print("\n📋 次のステップ:")
        print("1. エディタでプロジェクトを開く")
        print("2. 仮想環境をアクティベート")
        print("3. コードを書く際は行長88文字以下を意識する")
        print("4. 保存時に自動フォーマットが適用される")
        print("5. コミット前にpre-commitフックが実行される")
    else:
        print("⚠️ 一部のセットアップに失敗しました。手動で確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()
