#!/usr/bin/env python3
"""
本番稼働実行スクリプト
本番環境での稼働開始
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class GoLiveExecutor:
    """本番稼働実行クラス"""

    def __init__(self, config_file: str = "config/production_config.json"):
        self.config_file = Path(config_file)
        self.data_dir = Path("data")
        self.go_live_dir = Path("data/go_live")

        # ディレクトリの作成
        self.go_live_dir.mkdir(parents=True, exist_ok=True)

    async def run_preparation_checks(self) -> Dict[str, Any]:
        """稼働前チェックの実行"""
        print("🔍 Running pre-go-live checks...")

        try:
            cmd = ["python", "scripts/go_live_preparation.py", "--check", "all"]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                print("✅ Pre-go-live checks passed")
                return {"success": True, "message": "All checks passed"}
            else:
                return {
                    "success": False,
                    "error": f"Pre-go-live checks failed: {stderr.decode()}",
                }

        except Exception as e:
            return {"success": False, "error": f"Pre-go-live checks failed: {str(e)}"}

    async def start_monitoring(self) -> Dict[str, Any]:
        """監視システムの開始"""
        print("📊 Starting monitoring system...")

        try:
            # 監視プロセスの開始
            cmd = [
                "python",
                "scripts/production_monitoring.py",
                "--mode",
                "continuous",
                "--interval",
                "300",
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            # プロセスIDを保存
            pid_file = self.go_live_dir / "monitoring.pid"
            with open(pid_file, "w") as f:
                f.write(str(process.pid))

            print("✅ Monitoring system started")
            return {
                "success": True,
                "message": "Monitoring started",
                "pid": process.pid,
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to start monitoring: {str(e)}"}

    async def start_schedulers(self) -> Dict[str, Any]:
        """スケジューラーの開始"""
        print("⏰ Starting schedulers...")

        try:
            # crontabの確認
            cmd = ["crontab", "-l"]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                job_count = len(
                    [
                        line
                        for line in stdout.decode().split("\n")
                        if line.strip() and not line.startswith("#")
                    ]
                )

                print(f"✅ Schedulers active with {job_count} jobs")
                return {
                    "success": True,
                    "message": f"Schedulers active ({job_count} jobs)",
                }
            else:
                return {"success": False, "error": "No crontab jobs found"}

        except Exception as e:
            return {"success": False, "error": f"Failed to start schedulers: {str(e)}"}

    async def run_initial_data_fetch(self) -> Dict[str, Any]:
        """初期データ取得の実行"""
        print("📥 Running initial data fetch...")

        try:
            # 初期データ取得の実行
            cmd = [
                "python",
                "-c",
                """
import asyncio
import sys
sys.path.insert(0, '.')
from src.application.use_cases.fetch import FetchEconomicCalendarUseCase
from src.domain.services.investpy.investpy_service import InvestpyService
from src.infrastructure.database.repositories.sql.sql_economic_calendar_repository import SQLEconomicCalendarRepository

async def fetch_initial_data():
    # サービスの初期化
    investpy_service = InvestpyService()
    repository = SQLEconomicCalendarRepository()
    
    # ユースケースの実行
    use_case = FetchEconomicCalendarUseCase(investpy_service, repository)
    
    # 今日から1週間分のデータを取得
    result = await use_case.execute(
        from_date='01/12/2023',
        to_date='07/12/2023',
        fetch_type='initial'
    )
    
    print(f'Initial data fetch completed: {result}')
    return result

asyncio.run(fetch_initial_data())
""",
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                print("✅ Initial data fetch completed")
                return {"success": True, "message": "Initial data fetched successfully"}
            else:
                return {
                    "success": False,
                    "error": f"Initial data fetch failed: {stderr.decode()}",
                }

        except Exception as e:
            return {"success": False, "error": f"Initial data fetch failed: {str(e)}"}

    async def run_initial_ai_analysis(self) -> Dict[str, Any]:
        """初期AI分析の実行"""
        print("🤖 Running initial AI analysis...")

        try:
            # 初期AI分析の実行
            cmd = [
                "python",
                "-c",
                """
import asyncio
import sys
sys.path.insert(0, '.')
from src.application.use_cases.ai_report import GenerateAIReportUseCase
from src.domain.services.ai_analysis.ai_analysis_service import AIAnalysisService
from src.infrastructure.database.repositories.sql.sql_ai_report_repository import SQLAIReportRepository

async def run_initial_ai_analysis():
    # サービスの初期化
    ai_service = AIAnalysisService()
    repository = SQLAIReportRepository()
    
    # ユースケースの実行
    use_case = GenerateAIReportUseCase(ai_service, repository)
    
    # 高重要度イベントのAI分析を実行
    result = await use_case.generate_pre_event_reports_for_high_importance()
    
    print(f'Initial AI analysis completed: {result}')
    return result

asyncio.run(run_initial_ai_analysis())
""",
            ]

            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                print("✅ Initial AI analysis completed")
                return {
                    "success": True,
                    "message": "Initial AI analysis completed successfully",
                }
            else:
                return {
                    "success": False,
                    "error": f"Initial AI analysis failed: {stderr.decode()}",
                }

        except Exception as e:
            return {"success": False, "error": f"Initial AI analysis failed: {str(e)}"}

    async def send_go_live_notification(self) -> Dict[str, Any]:
        """稼働開始通知の送信"""
        print("📢 Sending go-live notification...")

        try:
            # .envファイルの読み込み
            try:
                from dotenv import load_dotenv

                load_dotenv("/app/.env")
            except ImportError:
                pass

            webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
            if not webhook_url:
                return {
                    "success": False,
                    "error": "Discord economic indicators webhook URL not set",
                }

            import requests

            embed = {
                "title": "🚀 Production Go-Live",
                "description": "investpy Economic Calendar System is now live!",
                "color": 0x00FF00,
                "timestamp": datetime.now().isoformat(),
                "fields": [
                    {
                        "name": "Status",
                        "value": "✅ System is now running in production",
                        "inline": True,
                    },
                    {
                        "name": "Features",
                        "value": "• Economic data fetching\n• AI analysis\n• Discord notifications\n• Real-time monitoring",
                        "inline": True,
                    },
                ],
                "footer": {"text": "Production System"},
            }

            payload = {"embeds": [embed]}

            response = requests.post(webhook_url, json=payload, timeout=10)

            if response.status_code == 200:
                print("✅ Go-live notification sent")
                return {"success": True, "message": "Notification sent successfully"}
            else:
                return {
                    "success": False,
                    "error": f"Failed to send notification: {response.status_code}",
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to send notification: {str(e)}"}

    async def run_performance_test(self) -> Dict[str, Any]:
        """パフォーマンステストの実行"""
        print("⚡ Running performance test...")

        try:
            start_time = datetime.now()

            # 簡単なパフォーマンステスト
            cmd = ["python", "scripts/run_tests.py", "--test-type", "performance"]
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await result.communicate()
            end_time = datetime.now()

            execution_time = (end_time - start_time).total_seconds()

            if result.returncode == 0:
                print(f"✅ Performance test completed in {execution_time:.2f}s")
                return {
                    "success": True,
                    "message": "Performance test passed",
                    "execution_time": execution_time,
                }
            else:
                return {
                    "success": False,
                    "error": f"Performance test failed: {stderr.decode()}",
                }

        except Exception as e:
            return {"success": False, "error": f"Performance test failed: {str(e)}"}

    async def create_go_live_report(self, results: Dict[str, Any]) -> None:
        """稼働開始レポートの作成"""
        print("📊 Creating go-live report...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.go_live_dir / f"go_live_report_{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_success": all(
                result.get("success", False) for result in results.values()
            ),
            "steps": results,
            "summary": {
                "total_steps": len(results),
                "successful_steps": sum(
                    1 for result in results.values() if result.get("success", False)
                ),
                "failed_steps": sum(
                    1 for result in results.values() if not result.get("success", False)
                ),
            },
            "status": (
                "LIVE"
                if all(result.get("success", False) for result in results.values())
                else "FAILED"
            ),
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Go-live report saved: {report_file}")

    async def execute_go_live(self) -> Dict[str, Any]:
        """本番稼働の実行"""
        print("🚀 Starting production go-live...")

        results = {}

        # 各ステップの実行
        steps = [
            ("preparation_checks", self.run_preparation_checks),
            ("start_monitoring", self.start_monitoring),
            ("start_schedulers", self.start_schedulers),
            ("initial_data_fetch", self.run_initial_data_fetch),
            ("initial_ai_analysis", self.run_initial_ai_analysis),
            ("performance_test", self.run_performance_test),
            ("go_live_notification", self.send_go_live_notification),
        ]

        for step_name, step_func in steps:
            print(f"\n📋 Executing {step_name}...")
            result = await step_func()
            results[step_name] = result

            if result["success"]:
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed: {result.get('error', 'Unknown error')}")

        # レポートの作成
        await self.create_go_live_report(results)

        # 全体の結果
        overall_success = all(
            result.get("success", False) for result in results.values()
        )

        if overall_success:
            print("\n🎉 Production go-live completed successfully!")
            print("✅ System is now LIVE in production")
            print("🚀 All services are running")
            print("📊 Monitoring is active")
            print("🤖 AI analysis is operational")
            print("📢 Notifications are enabled")
        else:
            print("\n❌ Production go-live failed!")
            print("Please review the failed steps and try again")

        return {"success": overall_success, "results": results}


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Production go-live execution")
    parser.add_argument(
        "--step",
        choices=[
            "preparation_checks",
            "start_monitoring",
            "start_schedulers",
            "initial_data_fetch",
            "initial_ai_analysis",
            "performance_test",
            "go_live_notification",
            "all",
        ],
        default="all",
        help="Specific step to execute",
    )
    parser.add_argument(
        "--config",
        default="config/production_config.json",
        help="Configuration file path",
    )

    args = parser.parse_args()

    executor = GoLiveExecutor(args.config)

    if args.step == "all":
        result = await executor.execute_go_live()
    else:
        # 特定のステップの実行
        step_functions = {
            "preparation_checks": executor.run_preparation_checks,
            "start_monitoring": executor.start_monitoring,
            "start_schedulers": executor.start_schedulers,
            "initial_data_fetch": executor.run_initial_data_fetch,
            "initial_ai_analysis": executor.run_initial_ai_analysis,
            "performance_test": executor.run_performance_test,
            "go_live_notification": executor.send_go_live_notification,
        }

        if args.step in step_functions:
            result = await step_functions[args.step]()
        else:
            print(f"❌ Unknown step: {args.step}")
            sys.exit(1)

    # 結果の表示
    if result.get("success", False):
        print("\n✅ Go-live step completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Go-live step failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
