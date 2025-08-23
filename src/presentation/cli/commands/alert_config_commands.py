"""
Alert Configuration Commands
アラート設定コマンド

責任:
- アラート設定の表示・編集
- 設定の検証
- 設定の保存・読み込み
"""

import os

import typer
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from src.infrastructure.config.alert_config_manager import AlertConfigManager
from src.utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="alert-config",
    help="🚨 アラート設定管理コマンド",
    no_args_is_help=True,
)


@app.command()
def show(
    config_path: str = typer.Option(
        "config/alerts.yaml", "--config", "-c", help="設定ファイルパス"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="表示形式 (table, yaml, json)"
    ),
):
    """
    アラート設定を表示

    Examples:
        exchange-analytics alert-config show
        exchange-analytics alert-config show --format yaml
        exchange-analytics alert-config show --config custom_alerts.yaml
    """
    try:
        config_manager = AlertConfigManager(config_path)
        config = config_manager.get_config()

        if format == "yaml":
            _show_yaml_config(config)
        elif format == "json":
            _show_json_config(config)
        else:
            _show_table_config(config)

    except Exception as e:
        console.print(f"❌ 設定表示エラー: {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    config_path: str = typer.Option(
        "config/alerts.yaml", "--config", "-c", help="設定ファイルパス"
    ),
):
    """
    アラート設定を検証

    Examples:
        exchange-analytics alert-config validate
        exchange-analytics alert-config validate --config custom_alerts.yaml
    """
    try:
        config_manager = AlertConfigManager(config_path)
        config = config_manager.get_config()

        # 設定の検証
        validation_results = _validate_config(config)

        # 結果を表示
        _show_validation_results(validation_results)

    except Exception as e:
        console.print(f"❌ 設定検証エラー: {e}")
        raise typer.Exit(1)


@app.command()
def edit(
    config_path: str = typer.Option(
        "config/alerts.yaml", "--config", "-c", help="設定ファイルパス"
    ),
):
    """
    アラート設定を編集

    Examples:
        exchange-analytics alert-config edit
        exchange-analytics alert-config edit --config custom_alerts.yaml
    """
    try:
        config_manager = AlertConfigManager(config_path)
        config = config_manager.get_config()

        console.print("📝 アラート設定編集")
        console.print("現在の設定を表示します...")

        _show_table_config(config)

        console.print("\n⚠️  設定編集機能は開発中です")
        console.print("設定ファイルを直接編集してください: " + config_path)

    except Exception as e:
        console.print(f"❌ 設定編集エラー: {e}")
        raise typer.Exit(1)


@app.command()
def reload(
    config_path: str = typer.Option(
        "config/alerts.yaml", "--config", "-c", help="設定ファイルパス"
    ),
):
    """
    アラート設定を再読み込み

    Examples:
        exchange-analytics alert-config reload
        exchange-analytics alert-config reload --config custom_alerts.yaml
    """
    try:
        config_manager = AlertConfigManager(config_path)
        config_manager.reload_config()

        console.print("✅ アラート設定を再読み込みしました")

        # 再読み込み後の設定を表示
        config = config_manager.get_config()
        _show_table_config(config)

    except Exception as e:
        console.print(f"❌ 設定再読み込みエラー: {e}")
        raise typer.Exit(1)


def _show_table_config(config):
    """テーブル形式で設定を表示"""
    console.print("\n🚨 アラート設定")

    # レート閾値アラート
    rate_config = config.rate_threshold_alerts
    if rate_config.get("enabled", False):
        rate_table = Table(title="💰 レート閾値アラート設定")
        rate_table.add_column("通貨ペア", style="cyan")
        rate_table.add_column("上限閾値", style="red")
        rate_table.add_column("下限閾値", style="green")
        rate_table.add_column("チェック間隔", style="yellow")
        rate_table.add_column("重要度", style="bold")

        currency_pairs = rate_config.get("currency_pairs", {})
        for pair, settings in currency_pairs.items():
            rate_table.add_row(
                pair,
                str(settings.get("upper_threshold", "N/A")),
                str(settings.get("lower_threshold", "N/A")),
                f"{settings.get('check_interval_minutes', 5)}分",
                settings.get("severity", "medium").upper(),
            )

        console.print(rate_table)
    else:
        console.print("💰 レート閾値アラート: 無効")

    # パターン検出アラート
    pattern_config = config.pattern_detection_alerts
    if pattern_config.get("enabled", False):
        pattern_table = Table(title="📊 パターン検出アラート設定")
        pattern_table.add_column("パターンタイプ", style="cyan")
        pattern_table.add_column("有効", style="bold")
        pattern_table.add_column("最小信頼度", style="yellow")
        pattern_table.add_column("重要度", style="bold")

        patterns = pattern_config.get("patterns", {})
        for pattern_type, settings in patterns.items():
            pattern_table.add_row(
                pattern_type,
                "✅" if settings.get("enabled", False) else "❌",
                f"{settings.get('min_confidence', 0.8) * 100:.0f}%",
                settings.get("severity", "medium").upper(),
            )

        console.print(pattern_table)
    else:
        console.print("📊 パターン検出アラート: 無効")

    # システムリソースアラート
    resource_config = config.system_resource_alerts
    if resource_config.get("enabled", False):
        resource_table = Table(title="🖥️ システムリソースアラート設定")
        resource_table.add_column("リソース", style="cyan")
        resource_table.add_column("警告閾値", style="yellow")
        resource_table.add_column("危険閾値", style="red")
        resource_table.add_column("重要度", style="bold")

        for resource, settings in resource_config.items():
            if isinstance(settings, dict) and "warning_threshold" in settings:
                resource_table.add_row(
                    resource.replace("_", " ").title(),
                    f"{settings.get('warning_threshold', 0)}%",
                    f"{settings.get('critical_threshold', 0)}%",
                    settings.get("severity", "medium").upper(),
                )

        console.print(resource_table)
    else:
        console.print("🖥️ システムリソースアラート: 無効")

    # 通知設定
    notification_config = config.notification_settings
    notification_table = Table(title="📢 通知設定")
    notification_table.add_column("通知方法", style="cyan")
    notification_table.add_column("有効", style="bold")
    notification_table.add_column("設定", style="yellow")

    for method, settings in notification_config.items():
        enabled = "✅" if settings.get("enabled", False) else "❌"
        config_info = ""
        if method == "email" and settings.get("enabled", False):
            recipients = settings.get("recipients", [])
            config_info = f"受信者: {len(recipients)}人"
        elif method == "discord" and settings.get("enabled", False):
            webhook = settings.get("webhook_url", "")
            alert_type_webhooks = settings.get("alert_type_webhooks", {})

            if alert_type_webhooks:
                config_info = (
                    f"Webhook設定済み (タイプ別: {len(alert_type_webhooks)}種類)"
                )
            else:
                config_info = "Webhook設定済み" if webhook else "Webhook未設定"
        elif method == "slack" and settings.get("enabled", False):
            webhook = settings.get("webhook_url", "")
            config_info = "Webhook設定済み" if webhook else "Webhook未設定"

        notification_table.add_row(method.title(), enabled, config_info)

    console.print(notification_table)

    # Discord設定の詳細表示
    discord_config = notification_config.get("discord", {})
    if discord_config.get("enabled", False):
        alert_type_webhooks = discord_config.get("alert_type_webhooks", {})
        if alert_type_webhooks:
            webhook_table = Table(title="🔗 Discord Webhook設定詳細")
            webhook_table.add_column("アラートタイプ", style="cyan")
            webhook_table.add_column("Webhook URL", style="yellow")
            webhook_table.add_column("説明", style="green")

            for alert_type, webhook_url in alert_type_webhooks.items():
                description = ""
                if alert_type == "system_resource":
                    description = "システムリソース監視"
                elif alert_type == "api_error":
                    description = "API エラー監視"
                elif alert_type == "data_fetch_error":
                    description = "データ取得エラー"
                elif alert_type == "rate_threshold":
                    description = "為替レート閾値"
                elif alert_type == "pattern_detection":
                    description = "パターン検出"
                elif alert_type == "default":
                    description = "デフォルト設定"
                else:
                    description = "カスタム設定"

                # Webhook URLを短縮表示
                short_url = (
                    webhook_url[:50] + "..." if len(webhook_url) > 50 else webhook_url
                )
                webhook_table.add_row(alert_type, short_url, description)

            console.print(webhook_table)


def _show_yaml_config(config):
    """YAML形式で設定を表示"""
    import yaml

    config_dict = config.dict()
    yaml_str = yaml.dump(config_dict, default_flow_style=False, allow_unicode=True)

    syntax = Syntax(yaml_str, "yaml", theme="monokai")
    console.print(syntax)


def _show_json_config(config):
    """JSON形式で設定を表示"""
    import json

    config_dict = config.dict()
    json_str = json.dumps(config_dict, indent=2, ensure_ascii=False)

    syntax = Syntax(json_str, "json", theme="monokai")
    console.print(syntax)


def _validate_config(config):
    """設定を検証"""
    results = {"valid": True, "errors": [], "warnings": []}

    # レート閾値アラートの検証
    rate_config = config.rate_threshold_alerts
    if rate_config.get("enabled", False):
        currency_pairs = rate_config.get("currency_pairs", {})
        if not currency_pairs:
            results["warnings"].append(
                "レート閾値アラートが有効ですが、通貨ペアが設定されていません"
            )

        for pair, settings in currency_pairs.items():
            upper = settings.get("upper_threshold")
            lower = settings.get("lower_threshold")
            if upper is not None and lower is not None and upper <= lower:
                results["errors"].append(f"{pair}: 上限閾値が下限閾値以下です")

    # パターン検出アラートの検証
    pattern_config = config.pattern_detection_alerts
    if pattern_config.get("enabled", False):
        confidence_threshold = pattern_config.get("confidence_threshold", 0.8)
        if not 0 <= confidence_threshold <= 1:
            results["errors"].append("信頼度閾値は0から1の間である必要があります")

        patterns = pattern_config.get("patterns", {})
        if not patterns:
            results["warnings"].append(
                "パターン検出アラートが有効ですが、パターンが設定されていません"
            )

    # 通知設定の検証
    notification_config = config.notification_settings
    discord_config = notification_config.get("discord", {})
    if discord_config.get("enabled", False):
        webhook_url = discord_config.get("webhook_url", "")
        alert_type_webhooks = discord_config.get("alert_type_webhooks", {})

        # 従来の設定とアラートタイプ別設定の両方がない場合
        if not webhook_url and not alert_type_webhooks:
            results["warnings"].append(
                "Discord通知が有効ですが、Webhook URLが設定されていません"
            )

        # アラートタイプ別設定の検証
        if alert_type_webhooks:
            # デフォルト設定の確認
            if "default" not in alert_type_webhooks:
                results["warnings"].append(
                    "アラートタイプ別Webhook設定がありますが、デフォルト設定がありません"
                )

            # 各アラートタイプの設定確認
            for alert_type, webhook in alert_type_webhooks.items():
                if not webhook or webhook.startswith("${") and webhook.endswith("}"):
                    env_var = webhook[2:-1]
                    if not os.getenv(env_var):
                        results["warnings"].append(
                            f"アラートタイプ '{alert_type}' の環境変数 '{env_var}' が設定されていません"
                        )

    # エラーがある場合は無効
    if results["errors"]:
        results["valid"] = False

    return results


def _show_validation_results(results):
    """検証結果を表示"""
    console.print("\n🔍 アラート設定検証結果")

    if results["valid"]:
        console.print("✅ 設定は有効です")
    else:
        console.print("❌ 設定にエラーがあります")

    if results["errors"]:
        error_table = Table(title="❌ エラー", title_style="red")
        error_table.add_column("エラー", style="red")

        for error in results["errors"]:
            error_table.add_row(error)

        console.print(error_table)

    if results["warnings"]:
        warning_table = Table(title="⚠️ 警告", title_style="yellow")
        warning_table.add_column("警告", style="yellow")

        for warning in results["warnings"]:
            warning_table.add_row(warning)

        console.print(warning_table)

    if not results["errors"] and not results["warnings"]:
        console.print("🎉 設定に問題はありません")
