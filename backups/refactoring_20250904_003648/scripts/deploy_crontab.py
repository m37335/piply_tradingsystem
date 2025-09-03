#!/usr/bin/env python3
"""
crontabデプロイスクリプト
本番環境でのcrontab設定を管理
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CrontabDeployer:
    """crontabデプロイヤー"""
    
    def __init__(self, config_dir: str = "config/crontab/production"):
        self.config_dir = Path(config_dir)
        self.log_dir = Path("data/logs")
        self.backup_dir = Path("data/backups/crontab")
        
    def deploy_crontab(self, schedule_type: str = "all") -> Dict[str, Any]:
        """
        crontabをデプロイ
        
        Args:
            schedule_type: スケジュールタイプ ("weekly", "daily", "realtime", "all")
            
        Returns:
            Dict[str, Any]: デプロイ結果
        """
        try:
            logger.info(f"Starting crontab deployment for schedule type: {schedule_type}")
            
            # ログディレクトリの作成
            self._create_log_directories()
            
            # 現在のcrontabをバックアップ
            backup_result = self._backup_current_crontab()
            
            # 新しいcrontab設定を生成
            new_crontab = self._generate_crontab_config(schedule_type)
            
            # crontabを更新
            deploy_result = self._update_crontab(new_crontab)
            
            # 設定の検証
            validation_result = self._validate_crontab()
            
            result = {
                "success": True,
                "schedule_type": schedule_type,
                "backup_result": backup_result,
                "deploy_result": deploy_result,
                "validation_result": validation_result,
                "timestamp": self._get_timestamp()
            }
            
            logger.info("Crontab deployment completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in crontab deployment: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def _create_log_directories(self) -> None:
        """ログディレクトリの作成"""
        try:
            # スケジューラーログディレクトリ
            (self.log_dir / "scheduler").mkdir(parents=True, exist_ok=True)
            (self.log_dir / "ai_analysis").mkdir(parents=True, exist_ok=True)
            (self.log_dir / "notifications").mkdir(parents=True, exist_ok=True)
            (self.log_dir / "reports").mkdir(parents=True, exist_ok=True)
            (self.log_dir / "maintenance").mkdir(parents=True, exist_ok=True)
            (self.log_dir / "monitoring").mkdir(parents=True, exist_ok=True)
            (self.log_dir / "analysis").mkdir(parents=True, exist_ok=True)
            
            logger.info("Log directories created successfully")
            
        except Exception as e:
            logger.error(f"Error creating log directories: {e}")
            raise
    
    def _backup_current_crontab(self) -> Dict[str, Any]:
        """現在のcrontabをバックアップ"""
        try:
            # バックアップディレクトリの作成
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 現在のcrontabを取得
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            current_crontab = result.stdout if result.returncode == 0 else ""
            
            # バックアップファイルに保存
            backup_file = self.backup_dir / f"crontab_backup_{self._get_timestamp()}.txt"
            with open(backup_file, "w") as f:
                f.write(current_crontab)
            
            logger.info(f"Current crontab backed up to: {backup_file}")
            
            return {
                "success": True,
                "backup_file": str(backup_file),
                "crontab_lines": len(current_crontab.splitlines()) if current_crontab else 0
            }
            
        except Exception as e:
            logger.error(f"Error backing up current crontab: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_crontab_config(self, schedule_type: str) -> str:
        """新しいcrontab設定を生成"""
        try:
            crontab_lines = []
            
            # ヘッダーコメント
            crontab_lines.append("# investpy Economic Calendar System - Crontab Configuration")
            crontab_lines.append(f"# Generated at: {self._get_timestamp()}")
            crontab_lines.append("# Schedule type: " + schedule_type)
            crontab_lines.append("")
            
            # 環境変数設定
            crontab_lines.append("# Environment variables")
            crontab_lines.append("SHELL=/bin/bash")
            crontab_lines.append("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin")
            crontab_lines.append("PYTHONPATH=/app")
            crontab_lines.append("")
            
            # スケジュールファイルの読み込み
            schedule_files = []
            if schedule_type in ["weekly", "all"]:
                schedule_files.append("weekly_schedule.cron")
            if schedule_type in ["daily", "all"]:
                schedule_files.append("daily_schedule.cron")
            if schedule_type in ["realtime", "all"]:
                schedule_files.append("realtime_schedule.cron")
            
            # 各スケジュールファイルの内容を読み込み
            for schedule_file in schedule_files:
                file_path = self.config_dir / schedule_file
                if file_path.exists():
                    with open(file_path, "r") as f:
                        content = f.read().strip()
                        if content:
                            crontab_lines.append(f"# {schedule_file}")
                            crontab_lines.append(content)
                            crontab_lines.append("")
            
            # フッターコメント
            crontab_lines.append("# End of crontab configuration")
            
            return "\n".join(crontab_lines)
            
        except Exception as e:
            logger.error(f"Error generating crontab config: {e}")
            raise
    
    def _update_crontab(self, crontab_content: str) -> Dict[str, Any]:
        """crontabを更新"""
        try:
            # 一時ファイルにcrontab内容を保存
            temp_file = self.backup_dir / "temp_crontab.txt"
            with open(temp_file, "w") as f:
                f.write(crontab_content)
            
            # crontabを更新
            result = subprocess.run(
                ["crontab", str(temp_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 一時ファイルを削除
            temp_file.unlink(missing_ok=True)
            
            logger.info("Crontab updated successfully")
            
            return {
                "success": True,
                "crontab_lines": len(crontab_content.splitlines()),
                "command_output": result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating crontab: {e}")
            return {
                "success": False,
                "error": str(e),
                "stderr": e.stderr
            }
        except Exception as e:
            logger.error(f"Error updating crontab: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_crontab(self) -> Dict[str, Any]:
        """crontab設定の検証"""
        try:
            # 現在のcrontabを取得
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            
            current_crontab = result.stdout
            
            # 基本的な検証
            validation = {
                "success": True,
                "total_lines": len(current_crontab.splitlines()),
                "has_weekly_schedule": "weekly_schedule.cron" in current_crontab,
                "has_daily_schedule": "daily_schedule.cron" in current_crontab,
                "has_realtime_schedule": "realtime_schedule.cron" in current_crontab,
                "has_environment_variables": "PYTHONPATH=/app" in current_crontab
            }
            
            logger.info("Crontab validation completed")
            return validation
            
        except Exception as e:
            logger.error(f"Error validating crontab: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_schedules(self) -> Dict[str, Any]:
        """現在のスケジュール一覧を表示"""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            
            current_crontab = result.stdout
            
            # スケジュールの解析
            schedules = {
                "weekly": [],
                "daily": [],
                "realtime": [],
                "maintenance": [],
                "monitoring": []
            }
            
            for line in current_crontab.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    if "weekly" in line:
                        schedules["weekly"].append(line)
                    elif "daily" in line:
                        schedules["daily"].append(line)
                    elif "realtime" in line or "*/30" in line or "*/15" in line or "*/5" in line:
                        schedules["realtime"].append(line)
                    elif "maintenance" in line or "backup" in line or "cleanup" in line:
                        schedules["maintenance"].append(line)
                    elif "monitoring" in line or "health" in line or "performance" in line:
                        schedules["monitoring"].append(line)
            
            return {
                "success": True,
                "schedules": schedules,
                "total_schedules": sum(len(s) for s in schedules.values())
            }
            
        except Exception as e:
            logger.error(f"Error listing schedules: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_timestamp(self) -> str:
        """タイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy crontab configuration")
    parser.add_argument(
        "--schedule-type",
        choices=["weekly", "daily", "realtime", "all"],
        default="all",
        help="Schedule type to deploy"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List current schedules"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate current crontab configuration"
    )
    
    args = parser.parse_args()
    
    deployer = CrontabDeployer()
    
    if args.list:
        result = deployer.list_schedules()
        print("Current schedules:")
        for schedule_type, schedules in result["schedules"].items():
            print(f"\n{schedule_type.upper()}:")
            for schedule in schedules:
                print(f"  {schedule}")
    elif args.validate:
        result = deployer._validate_crontab()
        print("Validation result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        result = deployer.deploy_crontab(args.schedule_type)
        if result["success"]:
            print("✅ Crontab deployment completed successfully")
            print(f"Schedule type: {result['schedule_type']}")
            print(f"Backup created: {result['backup_result']['backup_file']}")
        else:
            print("❌ Crontab deployment failed")
            print(f"Error: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
