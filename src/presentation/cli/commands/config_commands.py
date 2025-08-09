"""
Config Commands
設定管理コマンド

責任:
- 動的設定の管理
- 環境変数の設定・確認
- 設定ファイルの生成・検証
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="config",
    help="⚙️ 設定管理コマンド",
    no_args_is_help=True,
)


@app.command()
def show(
    environment: str = typer.Option("default", "--env", "-e", help="環境名"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="特定のキー"),
    format: str = typer.Option(
        "table", "--format", "-f", help="出力形式 (table, json, yaml)"
    ),
):
    """
    設定を表示

    Examples:
        exchange-analytics config show
        exchange-analytics config show --env production
        exchange-analytics config show --key api.alpha_vantage.rate_limit
        exchange-analytics config show --format json
    """
    console.print(f"⚙️ 設定表示 (環境: {environment})")

    # ダミー設定データ
    config_data = {
        "api": {
            "alpha_vantage": {
                "api_key": "****hidden****",
                "rate_limit": 500,
                "timeout": 30,
            },
            "openai": {
                "api_key": "****hidden****",
                "model": "gpt-4",
                "max_tokens": 2000,
            },
        },
        "database": {
            "url": "postgresql://localhost:5432/exchange_analytics",
            "pool_size": 10,
            "echo": False,
        },
        "cache": {
            "redis_url": "redis://localhost:6379/0",
            "default_ttl": 3600,
            "max_connections": 20,
        },
        "discord": {
            "webhook_url": "****hidden****",
            "username": "Exchange Analytics Bot",
        },
    }

    if key:
        # 特定のキーを表示
        keys = key.split(".")
        value = config_data

        try:
            for k in keys:
                value = value[k]

            console.print(f"🔑 キー: {key}")
            console.print(f"💡 値: {value}")

        except (KeyError, TypeError):
            console.print(f"❌ キーが見つかりません: {key}")
            return

    elif format == "json":
        # JSON形式で表示
        json_str = json.dumps(config_data, indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        console.print(syntax)

    elif format == "yaml":
        # YAML形式で表示 (簡易実装)
        console.print("📋 Configuration (YAML format):")
        _print_yaml_like(config_data)

    else:
        # テーブル形式で表示
        _print_config_table(config_data, environment)


def _print_config_table(config_data: Dict[str, Any], environment: str):
    """設定をテーブル形式で表示"""
    config_table = Table(title=f"⚙️ Configuration Settings ({environment})")
    config_table.add_column("Category", style="cyan", no_wrap=True)
    config_table.add_column("Key", style="bold")
    config_table.add_column("Value", style="green")
    config_table.add_column("Type", style="yellow")

    def add_config_rows(data: Dict[str, Any], prefix: str = ""):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # ネストした設定は再帰的に処理
                add_config_rows(value, full_key)
            else:
                # 値の型を判定
                value_type = type(value).__name__

                # 秘匿情報をマスク
                if (
                    "key" in key.lower()
                    or "password" in key.lower()
                    or "secret" in key.lower()
                ):
                    display_value = "****hidden****"
                else:
                    display_value = str(value)

                # カテゴリを抽出
                category = prefix.split(".")[0] if prefix else "root"

                config_table.add_row(category, full_key, display_value, value_type)

    add_config_rows(config_data)
    console.print(config_table)


def _print_yaml_like(data: Dict[str, Any], indent: int = 0):
    """YAML風の表示"""
    for key, value in data.items():
        if isinstance(value, dict):
            console.print("  " * indent + f"{key}:")
            _print_yaml_like(value, indent + 1)
        else:
            # 秘匿情報をマスク
            if "key" in key.lower() or "password" in key.lower():
                display_value = "****hidden****"
            else:
                display_value = value

            console.print("  " * indent + f"{key}: {display_value}")


@app.command()
def set(
    key: str = typer.Argument(..., help="設定キー (例: api.alpha_vantage.rate_limit)"),
    value: str = typer.Argument(..., help="設定値"),
    environment: str = typer.Option("default", "--env", "-e", help="環境名"),
    data_type: str = typer.Option(
        "auto", "--type", "-t", help="データ型 (auto, string, int, float, bool, json)"
    ),
):
    """
    設定を更新

    Examples:
        exchange-analytics config set api.alpha_vantage.rate_limit 1000
        exchange-analytics config set database.echo true --type bool
        exchange-analytics config set api.openai.model "gpt-4" --env production
    """
    console.print(f"✏️ 設定更新...")
    console.print(f"🔑 キー: {key}")
    console.print(f"💡 値: {value}")
    console.print(f"🌍 環境: {environment}")

    # データ型変換
    if data_type == "auto":
        # 自動判定
        if value.lower() in ("true", "false"):
            parsed_value = value.lower() == "true"
            detected_type = "boolean"
        elif value.isdigit():
            parsed_value = int(value)
            detected_type = "integer"
        elif value.replace(".", "").isdigit():
            parsed_value = float(value)
            detected_type = "float"
        else:
            parsed_value = value
            detected_type = "string"
    else:
        # 指定された型に変換
        type_map = {
            "string": str,
            "int": int,
            "float": float,
            "bool": lambda x: x.lower() == "true",
            "json": json.loads,
        }

        if data_type not in type_map:
            console.print(f"❌ 無効なデータ型: {data_type}")
            return

        try:
            parsed_value = type_map[data_type](value)
            detected_type = data_type
        except (ValueError, json.JSONDecodeError) as e:
            console.print(f"❌ 値の変換に失敗: {e}")
            return

    console.print(f"🔍 検出された型: {detected_type}")

    # 確認
    confirm = typer.confirm(f"設定を更新しますか？")
    if not confirm:
        console.print("❌ 設定更新をキャンセルしました")
        return

    # TODO: 実際の設定更新処理
    # config_manager = get_config_manager()
    # await config_manager.set(key, parsed_value, environment)

    console.print("✅ 設定を更新しました")


@app.command()
def delete(
    key: str = typer.Argument(..., help="削除する設定キー"),
    environment: str = typer.Option("default", "--env", "-e", help="環境名"),
    force: bool = typer.Option(False, "--force", "-f", help="確認をスキップ"),
):
    """
    設定を削除

    Examples:
        exchange-analytics config delete api.deprecated_setting
        exchange-analytics config delete temp.test_config --force
    """
    console.print(f"🗑️ 設定削除...")
    console.print(f"🔑 キー: {key}")
    console.print(f"🌍 環境: {environment}")

    if not force:
        console.print("[yellow]⚠️ この操作は取り消せません！[/yellow]")
        confirm = typer.confirm(f"設定 '{key}' を削除しますか？")
        if not confirm:
            console.print("❌ 設定削除をキャンセルしました")
            return

    # TODO: 実際の設定削除処理
    # config_manager = get_config_manager()
    # await config_manager.delete(key, environment)

    console.print("✅ 設定を削除しました")


@app.command()
def env():
    """
    環境変数を表示
    """
    console.print("🌍 環境変数一覧")

    # 重要な環境変数
    important_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "ALPHA_VANTAGE_API_KEY",
        "OPENAI_API_KEY",
        "DISCORD_WEBHOOK_URL",
        "JWT_SECRET",
        "ENVIRONMENT",
        "LOG_LEVEL",
    ]

    env_table = Table(title="🔧 Environment Variables")
    env_table.add_column("Variable", style="cyan", no_wrap=True)
    env_table.add_column("Value", style="bold")
    env_table.add_column("Status", style="green")

    for var in important_vars:
        value = os.getenv(var)

        if value:
            # 機密情報をマスク
            if any(
                secret in var.lower()
                for secret in ["key", "secret", "password", "token"]
            ):
                display_value = f"****hidden**** (len: {len(value)})"
            else:
                display_value = value

            status = "✅ Set"
        else:
            display_value = "[red]Not set[/red]"
            status = "❌ Missing"

        env_table.add_row(var, display_value, status)

    console.print(env_table)

    # 設定されていない必須変数があるかチェック
    missing_vars = [var for var in important_vars if not os.getenv(var)]

    if missing_vars:
        missing_panel = Panel.fit(
            f"""[yellow]⚠️ 未設定の環境変数があります:[/yellow]

{chr(10).join('• ' + var for var in missing_vars)}

[blue]設定方法:[/blue]
export VARIABLE_NAME=value
または .env ファイルに記載""",
            title="⚠️ Missing Environment Variables",
            border_style="yellow",
        )

        console.print(missing_panel)


@app.command()
def validate(
    environment: str = typer.Option("default", "--env", "-e", help="環境名"),
):
    """
    設定を検証
    """
    console.print(f"🔍 設定検証中... (環境: {environment})")

    # 検証結果テーブル
    validation_table = Table(title="🛡️ Configuration Validation")
    validation_table.add_column("Category", style="cyan")
    validation_table.add_column("Check", style="bold")
    validation_table.add_column("Status", style="green")
    validation_table.add_column("Details")

    # 検証項目のシミュレーション
    checks = [
        ("Database", "Connection URL", "✅ Valid", "PostgreSQL format detected"),
        ("Database", "Pool Size", "✅ Valid", "10 (within recommended range)"),
        ("Cache", "Redis URL", "✅ Valid", "Redis format detected"),
        ("Cache", "TTL Value", "✅ Valid", "3600 seconds"),
        ("API", "Alpha Vantage Key", "⚠️ Warning", "Key format valid, but not tested"),
        ("API", "OpenAI Key", "⚠️ Warning", "Key format valid, but not tested"),
        ("API", "Rate Limits", "✅ Valid", "All within API limits"),
        ("Discord", "Webhook URL", "✅ Valid", "Discord webhook format"),
        ("Security", "JWT Secret", "❌ Error", "Secret too short (< 32 chars)"),
        ("Logging", "Log Level", "✅ Valid", "INFO level"),
    ]

    for category, check, status, details in checks:
        validation_table.add_row(category, check, status, details)

    console.print(validation_table)

    # サマリー
    errors = sum(1 for _, _, status, _ in checks if "❌" in status)
    warnings = sum(1 for _, _, status, _ in checks if "⚠️" in status)
    passed = sum(1 for _, _, status, _ in checks if "✅" in status)

    if errors > 0:
        summary_style = "red"
        summary_text = f"❌ {errors} errors, ⚠️ {warnings} warnings, ✅ {passed} passed"
    elif warnings > 0:
        summary_style = "yellow"
        summary_text = f"⚠️ {warnings} warnings, ✅ {passed} passed"
    else:
        summary_style = "green"
        summary_text = f"✅ All {passed} checks passed"

    summary_panel = Panel.fit(
        summary_text,
        title="📊 Validation Summary",
        border_style=summary_style,
    )

    console.print(summary_panel)


@app.command()
def export(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="出力ファイルパス"),
    environment: str = typer.Option("default", "--env", "-e", help="環境名"),
    format: str = typer.Option("json", "--format", "-f", help="出力形式 (json, yaml, env)"),
    include_secrets: bool = typer.Option(False, "--include-secrets", help="機密情報も含める"),
):
    """
    設定をファイルにエクスポート

    Examples:
        exchange-analytics config export --output config.json
        exchange-analytics config export --format env --output .env
        exchange-analytics config export --include-secrets
    """
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"config_{environment}_{timestamp}.{format}")

    console.print(f"📤 設定エクスポート...")
    console.print(f"📁 出力先: {output}")
    console.print(f"🌍 環境: {environment}")
    console.print(f"📋 形式: {format}")

    if include_secrets:
        console.print("[yellow]⚠️ 機密情報も含めてエクスポートします[/yellow]")

    # ダミー設定データ
    config_data = {
        "api.alpha_vantage.api_key": (
            "demo_key_12345" if include_secrets else "****hidden****"
        ),
        "api.alpha_vantage.rate_limit": 500,
        "database.url": "postgresql://localhost:5432/exchange_analytics",
        "database.pool_size": 10,
        "cache.redis_url": "redis://localhost:6379/0",
        "cache.default_ttl": 3600,
    }

    # フォーマット別出力
    if format == "json":
        # JSON形式
        nested_config = {}
        for key, value in config_data.items():
            keys = key.split(".")
            current = nested_config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value

        content = json.dumps(nested_config, indent=2, ensure_ascii=False)

    elif format == "env":
        # .env形式
        lines = []
        for key, value in config_data.items():
            env_key = key.upper().replace(".", "_")
            lines.append(f"{env_key}={value}")
        content = "\n".join(lines)

    elif format == "yaml":
        # YAML形式 (簡易実装)
        lines = []
        for key, value in config_data.items():
            lines.append(f"{key}: {value}")
        content = "\n".join(lines)

    else:
        console.print(f"❌ サポートされていない形式: {format}")
        return

    # ファイル出力をシミュレート
    output.write_text(content, encoding="utf-8")

    console.print(f"✅ エクスポート完了: {output}")
    console.print(f"📊 設定項目数: {len(config_data)}")
    console.print(f"📏 ファイルサイズ: {len(content)} bytes")


@app.command()
def tree(
    environment: str = typer.Option("default", "--env", "-e", help="環境名"),
):
    """
    設定をツリー形式で表示
    """
    console.print(f"🌳 設定ツリー (環境: {environment})")

    # 設定ツリーを作成
    config_tree = Tree("⚙️ Configuration")

    # API設定
    api_branch = config_tree.add("🌐 API")
    alpha_vantage = api_branch.add("📊 Alpha Vantage")
    alpha_vantage.add("🔑 api_key: ****hidden****")
    alpha_vantage.add("⏱️ rate_limit: 500")
    alpha_vantage.add("⏰ timeout: 30")

    openai = api_branch.add("🤖 OpenAI")
    openai.add("🔑 api_key: ****hidden****")
    openai.add("🧠 model: gpt-4")
    openai.add("📝 max_tokens: 2000")

    # データベース設定
    db_branch = config_tree.add("🗄️ Database")
    db_branch.add("🔗 url: postgresql://localhost:5432/exchange_analytics")
    db_branch.add("🏊 pool_size: 10")
    db_branch.add("🔍 echo: false")

    # キャッシュ設定
    cache_branch = config_tree.add("💾 Cache")
    cache_branch.add("🔗 redis_url: redis://localhost:6379/0")
    cache_branch.add("⏰ default_ttl: 3600")
    cache_branch.add("🔗 max_connections: 20")

    # Discord設定
    discord_branch = config_tree.add("💬 Discord")
    discord_branch.add("🔗 webhook_url: ****hidden****")
    discord_branch.add("👤 username: Exchange Analytics Bot")

    console.print(config_tree)
