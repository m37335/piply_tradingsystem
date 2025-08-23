"""
Monitor Commands
監視コマンド

責任:
- システム監視・ヘルスチェック
- パフォーマンス監視
- ログ監視・分析
"""

import time
from datetime import datetime, timedelta
from typing import Optional

import httpx
import pytz
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="monitor",
    help="📊 監視・ヘルスチェックコマンド",
    no_args_is_help=True,
)


@app.command()
def health(
    host: str = typer.Option("localhost", "--host", "-h", help="ホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="詳細ヘルスチェック"),
    continuous: bool = typer.Option(False, "--continuous", "-c", help="継続監視"),
    interval: int = typer.Option(5, "--interval", "-i", help="監視間隔（秒）"),
):
    """
    システムヘルスチェック

    Examples:
        exchange-analytics monitor health
        exchange-analytics monitor health --detailed
        exchange-analytics monitor health --continuous --interval 10
    """
    if continuous:
        _continuous_health_monitor(host, port, detailed, interval)
    else:
        _single_health_check(host, port, detailed)


def _single_health_check(host: str, port: int, detailed: bool):
    """一回のヘルスチェック"""
    endpoint = "/api/v1/health/detailed" if detailed else "/api/v1/health"

    console.print(f"🏥 ヘルスチェック実行中... (http://{host}:{port})")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"http://{host}:{port}{endpoint}")

            if response.status_code == 200:
                health_data = response.json()
                _display_health_results(health_data, detailed)
            else:
                console.print(f"❌ ヘルスチェック失敗 (HTTP {response.status_code})")

    except httpx.ConnectError:
        console.print(f"❌ 接続失敗: http://{host}:{port}")
    except Exception as e:
        console.print(f"❌ ヘルスチェックエラー: {e}")


def _continuous_health_monitor(host: str, port: int, detailed: bool, interval: int):
    """継続的ヘルスチェック"""
    console.print(f"📊 継続ヘルスチェック開始 (間隔: {interval}秒, Ctrl+C で停止)")

    def generate_health_display():
        endpoint = "/api/v1/health/detailed" if detailed else "/api/v1/health"

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"http://{host}:{port}{endpoint}")

                if response.status_code == 200:
                    health_data = response.json()
                    return _create_health_panel(health_data, detailed)
                else:
                    return Panel(
                        f"❌ HTTP {response.status_code}",
                        title=f"🏥 Health Check - {datetime.now().strftime('%H:%M:%S')}",
                        border_style="red",
                    )

        except Exception as e:
            return Panel(
                f"❌ Error: {str(e)}",
                title=f"🏥 Health Check - {datetime.now().strftime('%H:%M:%S')}",
                border_style="red",
            )

    try:
        with Live(
            generate_health_display(), refresh_per_second=1 / interval, console=console
        ) as live:
            while True:
                time.sleep(interval)
                live.update(generate_health_display())

    except KeyboardInterrupt:
        console.print("\n⏹️ ヘルスチェック監視を停止しました")


def _display_health_results(health_data: dict, detailed: bool):
    """ヘルスチェック結果を表示"""
    status = health_data.get("status", "unknown")
    status_color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}.get(
        status, "white"
    )

    # 基本情報
    basic_panel = Panel.fit(
        f"""[{status_color}]Status: {status}[/{status_color}]
⏰ Timestamp: {health_data.get('timestamp')}
📦 Version: {health_data.get('version')}
🔧 Service: {health_data.get('service')}""",
        title="🏥 Health Check Results",
        border_style=status_color,
    )

    console.print(basic_panel)

    # 詳細情報
    if detailed and "checks" in health_data:
        checks_table = Table(title="🔍 Component Health Details")
        checks_table.add_column("Component", style="cyan")
        checks_table.add_column("Status", style="bold")
        checks_table.add_column("Response Time", style="yellow")
        checks_table.add_column("Details", style="blue")

        for component, check_data in health_data["checks"].items():
            comp_status = check_data.get("status", "unknown")
            comp_status_color = {
                "healthy": "green",
                "degraded": "yellow",
                "unhealthy": "red",
            }.get(comp_status, "white")

            status_text = f"[{comp_status_color}]{comp_status}[/{comp_status_color}]"

            response_time = f"{check_data.get('response_time_ms', 0)}ms"

            details = []
            if "error" in check_data:
                details.append(f"Error: {check_data['error']}")
            if "connected" in check_data:
                details.append(f"Connected: {check_data['connected']}")

            checks_table.add_row(
                component.replace("_", " ").title(),
                status_text,
                response_time,
                ", ".join(details) if details else "OK",
            )

        console.print(checks_table)


def _create_health_panel(health_data: dict, detailed: bool) -> Panel:
    """ヘルスチェックパネルを作成"""
    status = health_data.get("status", "unknown")
    status_color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}.get(
        status, "white"
    )

    content = f"[{status_color}]Status: {status}[/{status_color}]\n"
    content += f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}\n"

    if detailed and "checks" in health_data:
        content += "\n🔍 Components:\n"
        for component, check_data in health_data["checks"].items():
            comp_status = check_data.get("status", "unknown")
            emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(
                comp_status, "❓"
            )
            content += f"{emoji} {component.replace('_', ' ').title()}\n"

    return Panel.fit(
        content,
        title="🏥 Live Health Monitor",
        border_style=status_color,
    )


@app.command()
def metrics(
    host: str = typer.Option("localhost", "--host", "-h", help="ホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート"),
    live: bool = typer.Option(False, "--live", "-l", help="リアルタイム監視"),
    interval: int = typer.Option(2, "--interval", "-i", help="更新間隔（秒）"),
):
    """
    システムメトリクス監視

    Examples:
        exchange-analytics monitor metrics
        exchange-analytics monitor metrics --live
        exchange-analytics monitor metrics --live --interval 1
    """
    if live:
        _live_metrics_monitor(host, port, interval)
    else:
        _single_metrics_check(host, port)


def _single_metrics_check(host: str, port: int):
    """一回のメトリクス取得"""
    console.print(f"📊 システムメトリクス取得中... (http://{host}:{port})")

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"http://{host}:{port}/api/v1/health/metrics")

            if response.status_code == 200:
                metrics_data = response.json()
                _display_metrics(metrics_data)
            else:
                console.print(f"❌ メトリクス取得失敗 (HTTP {response.status_code})")

    except Exception as e:
        console.print(f"❌ メトリクス取得エラー: {e}")


def _live_metrics_monitor(host: str, port: int, interval: int):
    """リアルタイムメトリクス監視"""
    console.print(
        f"📊 リアルタイムメトリクス監視開始 (間隔: {interval}秒, Ctrl+C で停止)"
    )

    def generate_metrics_display():
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"http://{host}:{port}/api/v1/health/metrics")

                if response.status_code == 200:
                    metrics_data = response.json()
                    return _create_metrics_panel(metrics_data)
                else:
                    return Panel(
                        f"❌ HTTP {response.status_code}",
                        title=f"📊 Metrics - {datetime.now().strftime('%H:%M:%S')}",
                        border_style="red",
                    )

        except Exception as e:
            return Panel(
                f"❌ Error: {str(e)}",
                title=f"📊 Metrics - {datetime.now().strftime('%H:%M:%S')}",
                border_style="red",
            )

    try:
        with Live(
            generate_metrics_display(), refresh_per_second=1 / interval, console=console
        ) as live:
            while True:
                time.sleep(interval)
                live.update(generate_metrics_display())

    except KeyboardInterrupt:
        console.print("\n⏹️ メトリクス監視を停止しました")


def _display_metrics(metrics_data: dict):
    """メトリクスを表示"""
    system = metrics_data.get("system", {})
    process = metrics_data.get("process", {})

    # システムメトリクステーブル
    system_table = Table(title="🖥️ System Metrics")
    system_table.add_column("Metric", style="cyan")
    system_table.add_column("Value", style="bold green")
    system_table.add_column("Status", style="yellow")

    # CPU
    cpu_percent = system.get("cpu_percent", 0)
    cpu_status = (
        "🟢 Normal"
        if cpu_percent < 80
        else "🟡 High" if cpu_percent < 90 else "🔴 Critical"
    )
    system_table.add_row("CPU Usage", f"{cpu_percent:.1f}%", cpu_status)

    # Memory
    memory = system.get("memory", {})
    memory_percent = memory.get("percent", 0)
    memory_status = (
        "🟢 Normal"
        if memory_percent < 80
        else "🟡 High" if memory_percent < 90 else "🔴 Critical"
    )
    memory_gb = memory.get("used", 0) / (1024**3)
    total_gb = memory.get("total", 0) / (1024**3)
    system_table.add_row(
        "Memory Usage",
        f"{memory_gb:.1f}GB / {total_gb:.1f}GB ({memory_percent:.1f}%)",
        memory_status,
    )

    # Disk
    disk = system.get("disk", {})
    disk_percent = disk.get("percent", 0)
    disk_status = (
        "🟢 Normal"
        if disk_percent < 80
        else "🟡 High" if disk_percent < 90 else "🔴 Critical"
    )
    disk_gb = disk.get("used", 0) / (1024**3)
    disk_total_gb = disk.get("total", 0) / (1024**3)
    system_table.add_row(
        "Disk Usage",
        f"{disk_gb:.1f}GB / {disk_total_gb:.1f}GB ({disk_percent:.1f}%)",
        disk_status,
    )

    console.print(system_table)

    # プロセスメトリクステーブル
    process_table = Table(title="⚙️ Process Metrics")
    process_table.add_column("Metric", style="cyan")
    process_table.add_column("Value", style="bold blue")

    process_table.add_row("Process ID", str(process.get("pid", "Unknown")))

    proc_memory = process.get("memory", {})
    proc_memory_mb = proc_memory.get("rss", 0) / (1024**2)
    process_table.add_row("Memory RSS", f"{proc_memory_mb:.1f}MB")

    process_table.add_row("CPU Usage", f"{process.get('cpu_percent', 0):.1f}%")
    process_table.add_row("Threads", str(process.get("num_threads", 0)))

    create_time = process.get("create_time", 0)
    if create_time:
        uptime = time.time() - create_time
        uptime_str = str(timedelta(seconds=int(uptime)))
        process_table.add_row("Uptime", uptime_str)

    console.print(process_table)


def _create_metrics_panel(metrics_data: dict) -> Panel:
    """メトリクスパネルを作成"""
    system = metrics_data.get("system", {})
    process = metrics_data.get("process", {})

    cpu_percent = system.get("cpu_percent", 0)
    memory_percent = system.get("memory", {}).get("percent", 0)

    proc_memory = process.get("memory", {})
    proc_memory_mb = proc_memory.get("rss", 0) / (1024**2)

    content = f"""🖥️ CPU: {cpu_percent:.1f}%
💾 Memory: {memory_percent:.1f}%
⚙️ Process Memory: {proc_memory_mb:.1f}MB
🧵 Threads: {process.get("num_threads", 0)}
⏰ Time: {datetime.now().strftime('%H:%M:%S')}"""

    # 警告レベルに応じて色を決定
    border_color = "green"
    if cpu_percent > 90 or memory_percent > 90:
        border_color = "red"
    elif cpu_percent > 80 or memory_percent > 80:
        border_color = "yellow"

    return Panel.fit(
        content,
        title="📊 Live System Metrics",
        border_style=border_color,
    )


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="表示行数"),
    follow: bool = typer.Option(False, "--follow", "-f", help="リアルタイム監視"),
    level: Optional[str] = typer.Option(
        None, "--level", "-l", help="ログレベルフィルタ"
    ),
    component: Optional[str] = typer.Option(
        None, "--component", "-c", help="コンポーネントフィルタ"
    ),
):
    """
    ログ監視・表示

    Examples:
        exchange-analytics monitor logs
        exchange-analytics monitor logs --lines 100
        exchange-analytics monitor logs --follow --level ERROR
        exchange-analytics monitor logs --component api
    """
    console.print("📝 ログ表示...")

    if follow:
        console.print("🔄 リアルタイムログ監視 (Ctrl+C で停止)")
        # TODO: 実際のログファイル監視実装
        _simulate_log_follow(level, component)
    else:
        _show_recent_logs(lines, level, component)


def _show_recent_logs(lines: int, level: Optional[str], component: Optional[str]):
    """最近のログを表示"""
    console.print(f"📋 最新 {lines} 行のログ")

    # フィルタ情報
    filters = []
    if level:
        filters.append(f"Level: {level}")
    if component:
        filters.append(f"Component: {component}")

    if filters:
        console.print(f"🔍 フィルタ: {', '.join(filters)}")

    # ダミーログエントリ
    log_entries = [
        ("2024-01-15 10:30:15", "INFO", "api", "API server started successfully"),
        ("2024-01-15 10:30:16", "INFO", "database", "Database connection established"),
        ("2024-01-15 10:30:17", "INFO", "cache", "Redis connection established"),
        (
            "2024-01-15 10:30:20",
            "WARNING",
            "api",
            "Rate limit approaching for client 192.168.1.100",
        ),
        (
            "2024-01-15 10:30:25",
            "INFO",
            "data",
            "Exchange rate fetch completed: USD/JPY",
        ),
        ("2024-01-15 10:30:30", "ERROR", "external", "Alpha Vantage API timeout"),
        (
            "2024-01-15 10:30:35",
            "INFO",
            "analysis",
            "Technical analysis completed: RSI calculation",
        ),
        ("2024-01-15 10:30:40", "DEBUG", "cache", "Cache hit: exchange_rate_USD_JPY"),
    ]

    # フィルタ適用
    filtered_entries = log_entries
    if level:
        filtered_entries = [entry for entry in filtered_entries if entry[1] == level]
    if component:
        filtered_entries = [
            entry for entry in filtered_entries if entry[2] == component
        ]

    # 最新N行を取得
    recent_entries = filtered_entries[-lines:]

    # ログテーブル表示
    log_table = Table(title="📝 Recent Logs")
    log_table.add_column("Timestamp", style="cyan", no_wrap=True)
    log_table.add_column("Level", style="bold")
    log_table.add_column("Component", style="yellow")
    log_table.add_column("Message", style="white")

    for timestamp, log_level, comp, message in recent_entries:
        level_color = {
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bright_red",
        }.get(log_level, "white")

        colored_level = f"[{level_color}]{log_level}[/{level_color}]"

        log_table.add_row(timestamp, colored_level, comp, message)

    console.print(log_table)


def _simulate_log_follow(level: Optional[str], component: Optional[str]):
    """ログ監視をシミュレート"""
    import random

    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    components = ["api", "database", "cache", "data", "analysis", "external"]
    messages = [
        "Request processed successfully",
        "Database query executed",
        "Cache operation completed",
        "Data fetch completed",
        "Analysis calculation finished",
        "External API call made",
        "Rate limit check passed",
        "Health check completed",
    ]

    try:
        while True:
            # ランダムログエントリ生成
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_level = random.choice(log_levels)
            comp = random.choice(components)
            message = random.choice(messages)

            # フィルタ適用
            if level and log_level != level:
                time.sleep(1)
                continue
            if component and comp != component:
                time.sleep(1)
                continue

            # ログ表示
            level_color = {
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
            }.get(log_level, "white")

            console.print(
                f"[cyan]{timestamp}[/cyan] [{level_color}]{log_level}[/{level_color}] "
                f"[yellow]{comp}[/yellow] {message}"
            )

            time.sleep(random.uniform(0.5, 3.0))

    except KeyboardInterrupt:
        console.print("\n⏹️ ログ監視を停止しました")


@app.command()
def alerts(
    limit: int = typer.Option(50, "--limit", "-l", help="表示件数"),
    severity: Optional[str] = typer.Option(
        None, "--severity", "-s", help="重要度フィルタ"
    ),
    alert_type: Optional[str] = typer.Option(
        None, "--type", "-t", help="アラートタイプフィルタ"
    ),
    active_only: bool = typer.Option(
        True, "--active-only", "-a", help="アクティブなアラートのみ表示"
    ),
):
    """
    アクティブなアラートを表示

    Examples:
        exchange-analytics monitor alerts
        exchange-analytics monitor alerts --limit 10
        exchange-analytics monitor alerts --severity high
        exchange-analytics monitor alerts --type rate_threshold
    """
    console.print("🚨 アクティブアラート確認中...")

    try:
        # 環境変数を設定
        import os

        os.environ["DATABASE_URL"] = (
            "postgresql+asyncpg://exchange_analytics_user:"
            "exchange_password@localhost:5432/exchange_analytics_production_db"
        )

        # データベース接続
        import asyncio

        from src.infrastructure.database.connection import get_async_session
        from src.infrastructure.database.repositories.alert_repository_impl import (
            AlertRepositoryImpl,
        )

        async def get_alerts_and_stats():
            session = await get_async_session()
            alert_repo = AlertRepositoryImpl(session)

            # アラートデータを取得
            if active_only:
                alerts_data = await alert_repo.find_active_alerts(
                    limit=limit, severity=severity, alert_type=alert_type
                )
            else:
                # 最近のアラートを取得（24時間）
                alerts_data = await alert_repo.find_recent_alerts(hours=24, limit=limit)

            # 統計情報を取得
            stats = await alert_repo.get_alert_statistics()

            await session.close()
            return alerts_data, stats

        alerts_data, stats = asyncio.run(get_alerts_and_stats())

        # アラートテーブル
        alerts_table = Table(title="🚨 Active Alerts")
        alerts_table.add_column("ID", style="cyan", no_wrap=True)
        alerts_table.add_column("Type", style="bold")
        alerts_table.add_column("Severity", style="bold")
        alerts_table.add_column("Message", style="white")
        alerts_table.add_column("Created", style="yellow")
        alerts_table.add_column("Status", style="green")

        for alert in alerts_data:
            severity_level = alert.severity
            severity_color = {
                "low": "blue",
                "medium": "yellow",
                "high": "red",
                "critical": "bright_red",
            }.get(severity_level, "white")

            status = alert.status
            status_color = {
                "active": "red",
                "acknowledged": "yellow",
                "resolved": "green",
            }.get(status, "white")

            # タイムスタンプをJSTに変換
            created_time = alert.created_at
            if created_time:
                # タイムゾーン情報がない場合はJSTとして扱う
                if created_time.tzinfo is None:
                    jst = pytz.timezone("Asia/Tokyo")
                    created_time = jst.localize(created_time)

                # JSTに変換して表示
                jst = pytz.timezone("Asia/Tokyo")
                jst_time = created_time.astimezone(jst)
                created_str = jst_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_str = "N/A"

            alerts_table.add_row(
                str(alert.id),
                alert.alert_type,
                f"[{severity_color}]{severity_level.upper()}[/{severity_color}]",
                (
                    alert.message[:50] + "..."
                    if len(alert.message) > 50
                    else alert.message
                ),
                created_str,
                f"[{status_color}]{status.upper()}[/{status_color}]",
            )

        console.print(alerts_table)

        # サマリー
        active_count = stats.get("active_alerts", 0)
        high_severity = stats.get("severity_distribution", {}).get(
            "high", 0
        ) + stats.get("severity_distribution", {}).get("critical", 0)

        summary_text = (
            f"🚨 Active Alerts: {active_count}\n⚠️ High Severity: {high_severity}"
        )
        summary_color = "red" if active_count > 0 else "green"

        summary_panel = Panel.fit(
            summary_text,
            title="📊 Alert Summary",
            border_style=summary_color,
        )

        console.print(summary_panel)

    except Exception as e:
        console.print(f"❌ アラート取得エラー: {e}")
        raise typer.Exit(1)
