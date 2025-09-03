#!/usr/bin/env python3
"""
Cron Monitoring Script
crontabのテスト実行をリアルタイム監視
"""

import os
import time
from datetime import datetime

import pytz
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


def get_log_content(file_path, lines=5):
    """ログファイルの最新行を取得"""
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.readlines()
                return content[-lines:] if content else []
        return []
    except Exception:
        return []


def create_monitoring_panel():
    """監視パネル作成"""
    jst = pytz.timezone("Asia/Tokyo")
    current_time = datetime.now(jst)

    # ログファイル監視
    logs = {
        "🧪 基本テスト": ("logs/cron_test.log", 3),
        "🌐 APIヘルス": ("logs/api_health_cron.log", 2),
        "📊 スケジューラー": ("logs/scheduler_cron.log", 3),
        "💱 FXテスト": ("logs/fx_test_cron.log", 2),
    }

    content = f"[bold green]⏰ Cron Monitor[/bold green]\n\n"
    content += f"🕘 現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S JST')}\n"
    content += f"🔄 UTC時刻: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"

    # 各ログファイルの状況
    for log_name, (file_path, lines) in logs.items():
        content += f"[bold yellow]{log_name}[/bold yellow]:\n"

        if os.path.exists(file_path):
            log_lines = get_log_content(file_path, lines)
            if log_lines:
                file_size = os.path.getsize(file_path)
                content += f"  📁 サイズ: {file_size} bytes\n"
                for line in log_lines:
                    content += f"  📝 {line.strip()}\n"
            else:
                content += "  📝 ログなし\n"
        else:
            content += "  ❌ ファイルなし\n"
        content += "\n"

    # 次回実行予定
    current_minute = current_time.minute
    next_basic = 60 - current_time.second  # 次の毎分実行まで
    next_api = (2 - (current_minute % 2)) * 60 - current_time.second  # 次の2分間隔
    next_scheduler = (3 - (current_minute % 3)) * 60 - current_time.second  # 次の3分間隔
    next_fx = (5 - (current_minute % 5)) * 60 - current_time.second  # 次の5分間隔

    content += "[bold blue]⏰ 次回実行予定[/bold blue]:\n"
    content += f"🧪 基本テスト: {next_basic}秒後\n"
    content += f"🌐 APIチェック: {next_api}秒後\n"
    content += f"📊 スケジューラー: {next_scheduler}秒後\n"
    content += f"💱 FXテスト: {next_fx}秒後\n"

    return Panel.fit(content, title="📊 Cron Real-time Monitor", border_style="green")


def main():
    """メイン実行"""
    console = Console()

    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                panel = create_monitoring_panel()
                live.update(panel)
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n⏹️ Cron monitoring stopped")


if __name__ == "__main__":
    main()
