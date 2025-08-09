"""
API Commands
API サーバー管理コマンド

責任:
- API サーバーの起動・停止
- サーバー設定・状態確認
- パフォーマンス監視
"""

import asyncio
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="api",
    help="🌐 API サーバー管理コマンド",
    no_args_is_help=True,
)


@app.command()
def start(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="バインドホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート番号"),
    reload: bool = typer.Option(False, "--reload", "-r", help="ホットリロード有効"),
    workers: int = typer.Option(1, "--workers", "-w", help="ワーカー数"),
    log_level: str = typer.Option("info", "--log-level", "-l", help="ログレベル"),
    background: bool = typer.Option(
        False, "--background", "-d", help="バックグラウンド実行"
    ),
):
    """
    API サーバーを起動

    Examples:
        exchange-analytics api start
        exchange-analytics api start --port 8080 --reload
        exchange-analytics api start --background
    """
    console.print(f"🚀 API サーバーを起動中... (host={host}, port={port})")

    # UvicornでFastAPIサーバーを起動
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.presentation.api.app:app",
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        log_level,
    ]

    if reload:
        cmd.append("--reload")

    if workers > 1:
        cmd.extend(["--workers", str(workers)])

    try:
        if background:
            # バックグラウンド実行
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd(),
            )

            console.print(
                f"✅ API サーバーをバックグラウンドで起動 (PID: {process.pid})"
            )
            console.print(f"🌐 URL: http://{host}:{port}")
            console.print(f"📚 Docs: http://{host}:{port}/docs")

            # PIDを保存
            pid_file = Path("api_server.pid")
            pid_file.write_text(str(process.pid))

        else:
            # フォアグラウンド実行
            console.print(f"🌐 API サーバー起動: http://{host}:{port}")
            console.print(f"📚 API ドキュメント: http://{host}:{port}/docs")
            console.print("🛑 停止: Ctrl+C")

            subprocess.run(cmd, cwd=Path.cwd())

    except KeyboardInterrupt:
        console.print("\n⏹️ API サーバーを停止中...")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ API サーバー起動失敗: {e}")
        raise typer.Exit(1)


@app.command()
def stop():
    """
    API サーバーを停止
    """
    console.print("⏹️ API サーバーを停止中...")

    pid_file = Path("api_server.pid")

    if not pid_file.exists():
        console.print("❌ 実行中のAPI サーバーが見つかりません")
        return

    try:
        pid = int(pid_file.read_text().strip())

        # プロセスを停止
        import psutil

        process = psutil.Process(pid)
        process.terminate()

        # 少し待って強制終了
        time.sleep(2)
        if process.is_running():
            process.kill()

        pid_file.unlink()
        console.print("✅ API サーバーを停止しました")

    except (ValueError, psutil.NoSuchProcess):
        console.print("❌ プロセスが見つかりません")
        pid_file.unlink(missing_ok=True)
    except Exception as e:
        console.print(f"❌ 停止に失敗: {e}")


@app.command()
def restart(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="バインドホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート番号"),
):
    """
    API サーバーを再起動
    """
    console.print("🔄 API サーバーを再起動中...")

    # 停止
    stop()
    time.sleep(1)

    # 起動
    start(host=host, port=port, background=True)


@app.command()
def status(
    host: str = typer.Option("localhost", "--host", "-h", help="ホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート"),
):
    """
    API サーバーの状態確認
    """
    console.print("🔍 API サーバー状態確認中...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("ヘルスチェック中...", total=None)

        try:
            # ヘルスチェック
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"http://{host}:{port}/api/v1/health")

                if response.status_code == 200:
                    health_data = response.json()

                    progress.stop()

                    # ステータス表示
                    status_panel = Panel.fit(
                        f"""[green]✅ API サーバー稼働中[/green]

🌐 URL: http://{host}:{port}
📚 Docs: http://{host}:{port}/docs
🏥 Status: {health_data.get('status', 'unknown')}
⏰ Timestamp: {health_data.get('timestamp', 'unknown')}
📦 Version: {health_data.get('version', 'unknown')}""",
                        title="📊 API Server Status",
                        border_style="green",
                    )

                    console.print(status_panel)

                else:
                    progress.stop()
                    console.print(
                        f"❌ API サーバーエラー (HTTP {response.status_code})"
                    )

        except httpx.ConnectError:
            progress.stop()
            console.print(f"❌ API サーバーに接続できません (http://{host}:{port})")
        except httpx.TimeoutException:
            progress.stop()
            console.print("❌ API サーバーのレスポンスがタイムアウトしました")
        except Exception as e:
            progress.stop()
            console.print(f"❌ 状態確認エラー: {e}")


@app.command()
def health(
    host: str = typer.Option("localhost", "--host", "-h", help="ホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="詳細ヘルスチェック"),
):
    """
    API サーバーのヘルスチェック
    """
    endpoint = "/api/v1/health/detailed" if detailed else "/api/v1/health"

    console.print(f"🏥 ヘルスチェック実行中... ({'詳細' if detailed else '基本'})")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"http://{host}:{port}{endpoint}")

            if response.status_code == 200:
                health_data = response.json()

                # 基本情報表示
                console.print(
                    f"✅ [green]Status: {health_data.get('status', 'unknown')}[/green]"
                )
                console.print(f"⏰ Timestamp: {health_data.get('timestamp')}")
                console.print(f"📦 Version: {health_data.get('version')}")

                # 詳細情報表示
                if detailed and "checks" in health_data:
                    checks_table = Table(title="🔍 Component Health Checks")
                    checks_table.add_column("Component", style="cyan")
                    checks_table.add_column("Status", style="bold")
                    checks_table.add_column("Details")

                    for component, check_data in health_data["checks"].items():
                        status = check_data.get("status", "unknown")
                        status_color = {
                            "healthy": "green",
                            "degraded": "yellow",
                            "unhealthy": "red",
                        }.get(status, "white")

                        status_text = f"[{status_color}]{status}[/{status_color}]"

                        details = []
                        if "response_time_ms" in check_data:
                            details.append(
                                f"Response: {check_data['response_time_ms']}ms"
                            )
                        if "error" in check_data:
                            details.append(f"Error: {check_data['error']}")

                        checks_table.add_row(
                            component.replace("_", " ").title(),
                            status_text,
                            ", ".join(details) if details else "OK",
                        )

                    console.print(checks_table)

            else:
                console.print(f"❌ ヘルスチェック失敗 (HTTP {response.status_code})")

    except Exception as e:
        console.print(f"❌ ヘルスチェックエラー: {e}")


@app.command()
def metrics(
    host: str = typer.Option("localhost", "--host", "-h", help="ホスト"),
    port: int = typer.Option(8000, "--port", "-p", help="ポート"),
    live: bool = typer.Option(False, "--live", "-l", help="リアルタイム監視"),
):
    """
    API サーバーのメトリクス取得
    """
    if live:
        # リアルタイム監視
        _live_metrics(host, port)
    else:
        # 一回の取得
        _show_metrics(host, port)


def _show_metrics(host: str, port: int):
    """メトリクス一回表示"""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"http://{host}:{port}/api/v1/health/metrics")

            if response.status_code == 200:
                metrics_data = response.json()

                # システムメトリクス
                system = metrics_data.get("system", {})
                process = metrics_data.get("process", {})

                metrics_table = Table(title="📊 System Metrics")
                metrics_table.add_column("Category", style="cyan")
                metrics_table.add_column("Metric", style="bold")
                metrics_table.add_column("Value", style="green")

                # CPU
                metrics_table.add_row(
                    "System", "CPU Usage", f"{system.get('cpu_percent', 0):.1f}%"
                )

                # Memory
                memory = system.get("memory", {})
                memory_gb = memory.get("used", 0) / (1024**3)
                total_gb = memory.get("total", 0) / (1024**3)
                metrics_table.add_row(
                    "System",
                    "Memory Usage",
                    f"{memory_gb:.1f}GB / {total_gb:.1f}GB ({memory.get('percent', 0):.1f}%)",
                )

                # Disk
                disk = system.get("disk", {})
                disk_gb = disk.get("used", 0) / (1024**3)
                disk_total_gb = disk.get("total", 0) / (1024**3)
                metrics_table.add_row(
                    "System",
                    "Disk Usage",
                    f"{disk_gb:.1f}GB / {disk_total_gb:.1f}GB ({disk.get('percent', 0):.1f}%)",
                )

                # Process
                proc_memory = process.get("memory", {})
                proc_memory_mb = proc_memory.get("rss", 0) / (1024**2)
                metrics_table.add_row(
                    "Process", "Memory RSS", f"{proc_memory_mb:.1f}MB"
                )
                metrics_table.add_row(
                    "Process", "CPU Usage", f"{process.get('cpu_percent', 0):.1f}%"
                )
                metrics_table.add_row(
                    "Process", "Threads", str(process.get("num_threads", 0))
                )

                console.print(metrics_table)

            else:
                console.print(f"❌ メトリクス取得失敗 (HTTP {response.status_code})")

    except Exception as e:
        console.print(f"❌ メトリクス取得エラー: {e}")


def _live_metrics(host: str, port: int):
    """リアルタイムメトリクス監視"""
    console.print("📊 リアルタイムメトリクス監視開始 (Ctrl+C で停止)")

    def generate_metrics_table():
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"http://{host}:{port}/api/v1/health/metrics")

                if response.status_code == 200:
                    metrics_data = response.json()
                    system = metrics_data.get("system", {})
                    process = metrics_data.get("process", {})

                    table = Table(
                        title=f"📊 Live Metrics - {time.strftime('%H:%M:%S')}"
                    )
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="bold green")

                    # システムメトリクス
                    table.add_row("CPU Usage", f"{system.get('cpu_percent', 0):.1f}%")

                    memory = system.get("memory", {})
                    table.add_row("Memory Usage", f"{memory.get('percent', 0):.1f}%")

                    # プロセスメトリクス
                    proc_memory = process.get("memory", {})
                    proc_memory_mb = proc_memory.get("rss", 0) / (1024**2)
                    table.add_row("Process Memory", f"{proc_memory_mb:.1f}MB")
                    table.add_row(
                        "Process CPU", f"{process.get('cpu_percent', 0):.1f}%"
                    )
                    table.add_row("Threads", str(process.get("num_threads", 0)))

                    return table
                else:
                    return Panel(f"❌ HTTP {response.status_code}", style="red")

        except Exception as e:
            return Panel(f"❌ Error: {e}", style="red")

    try:
        with Live(
            generate_metrics_table(), refresh_per_second=2, console=console
        ) as live:
            while True:
                time.sleep(0.5)
                live.update(generate_metrics_table())

    except KeyboardInterrupt:
        console.print("\n⏹️ リアルタイム監視を停止しました")
