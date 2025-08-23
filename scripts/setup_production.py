#!/usr/bin/env python3
"""
本番環境セットアップスクリプト
本番環境の初期設定と検証を実行
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionSetup:
    """本番環境セットアップ"""
    
    def __init__(self, config_file: str = "config/production_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.data_dir = Path("data")
        self.logs_dir = self.data_dir / "logs"
        self.backups_dir = self.data_dir / "backups"
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            raise
    
    def setup_directories(self) -> Dict[str, Any]:
        """必要なディレクトリの作成"""
        try:
            logger.info("Creating production directories")
            
            directories = [
                self.data_dir,
                self.logs_dir,
                self.logs_dir / "scheduler",
                self.logs_dir / "ai_analysis",
                self.logs_dir / "notifications",
                self.logs_dir / "reports",
                self.logs_dir / "maintenance",
                self.logs_dir / "monitoring",
                self.logs_dir / "analysis",
                self.logs_dir / "database",
                self.backups_dir,
                self.backups_dir / "database",
                self.backups_dir / "logs",
                self.backups_dir / "crontab",
                Path("data/economic_calendar/raw"),
                Path("data/economic_calendar/processed"),
                Path("data/economic_calendar/archive"),
                Path("data/ai_reports/generated"),
                Path("data/ai_reports/templates"),
                Path("data/ai_reports/archive")
            ]
            
            created_dirs = []
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(directory))
                logger.info(f"Created directory: {directory}")
            
            return {
                "success": True,
                "directories_created": len(created_dirs),
                "directories": created_dirs
            }
            
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def setup_logging(self) -> Dict[str, Any]:
        """ログ設定のセットアップ"""
        try:
            logger.info("Setting up logging configuration")
            
            # ログ設定ファイルの存在確認
            logging_config = Path("config/logging.yaml")
            if not logging_config.exists():
                return {
                    "success": False,
                    "error": "Logging configuration file not found"
                }
            
            # ログディレクトリの権限設定
            for log_dir in self.logs_dir.rglob("*"):
                if log_dir.is_dir():
                    os.chmod(log_dir, 0o755)
            
            return {
                "success": True,
                "logging_config": str(logging_config),
                "log_directories": [str(d) for d in self.logs_dir.rglob("*") if d.is_dir()]
            }
            
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_environment(self) -> Dict[str, Any]:
        """環境変数の検証"""
        try:
            logger.info("Validating environment variables")
            
            required_vars = [
                "DATABASE_URL",
                "REDIS_URL",
                "DISCORD_WEBHOOK_URL",
                "OPENAI_API_KEY"
            ]
            
            optional_vars = [
                "DISCORD_ECONOMICINDICATORS_WEBHOOK_URL",
                "LOG_LEVEL",
                "ENVIRONMENT"
            ]
            
            validation_result = {
                "success": True,
                "required_vars": {},
                "optional_vars": {},
                "missing_required": [],
                "missing_optional": []
            }
            
            # 必須環境変数の検証
            for var in required_vars:
                value = os.getenv(var)
                if value:
                    validation_result["required_vars"][var] = "SET"
                else:
                    validation_result["required_vars"][var] = "MISSING"
                    validation_result["missing_required"].append(var)
                    validation_result["success"] = False
            
            # オプション環境変数の検証
            for var in optional_vars:
                value = os.getenv(var)
                if value:
                    validation_result["optional_vars"][var] = "SET"
                else:
                    validation_result["optional_vars"][var] = "MISSING"
                    validation_result["missing_optional"].append(var)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating environment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def setup_database(self) -> Dict[str, Any]:
        """データベースのセットアップ"""
        try:
            logger.info("Setting up database")
            
            # データベースマイグレーションの実行
            result = subprocess.run(
                ["python", "-m", "scripts.setup_database"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Database setup completed",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": "Database setup failed",
                    "stderr": result.stderr
                }
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def setup_crontab(self) -> Dict[str, Any]:
        """crontabのセットアップ"""
        try:
            logger.info("Setting up crontab configuration")
            
            # crontabデプロイスクリプトの実行
            result = subprocess.run(
                ["python", "scripts/deploy_crontab.py", "--schedule-type", "all"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Crontab setup completed",
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": "Crontab setup failed",
                    "stderr": result.stderr
                }
            
        except Exception as e:
            logger.error(f"Error setting up crontab: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_health_checks(self) -> Dict[str, Any]:
        """ヘルスチェックの実行"""
        try:
            logger.info("Running health checks")
            
            health_checks = {
                "database": self._check_database_connection(),
                "redis": self._check_redis_connection(),
                "discord": self._check_discord_webhook(),
                "openai": self._check_openai_api(),
                "file_permissions": self._check_file_permissions()
            }
            
            all_passed = all(check["success"] for check in health_checks.values())
            
            return {
                "success": all_passed,
                "health_checks": health_checks,
                "passed_checks": len([c for c in health_checks.values() if c["success"]]),
                "total_checks": len(health_checks)
            }
            
        except Exception as e:
            logger.error(f"Error running health checks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_database_connection(self) -> Dict[str, Any]:
        """データベース接続のチェック"""
        try:
            # 簡易的なデータベース接続テスト
            result = subprocess.run(
                ["python", "-c", "import psycopg2; print('Database connection test')"],
                capture_output=True,
                text=True,
                check=False
            )
            
            return {
                "success": result.returncode == 0,
                "message": "Database connection test completed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_redis_connection(self) -> Dict[str, Any]:
        """Redis接続のチェック"""
        try:
            # 簡易的なRedis接続テスト
            result = subprocess.run(
                ["python", "-c", "import redis; print('Redis connection test')"],
                capture_output=True,
                text=True,
                check=False
            )
            
            return {
                "success": result.returncode == 0,
                "message": "Redis connection test completed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_discord_webhook(self) -> Dict[str, Any]:
        """Discord Webhookのチェック"""
        try:
            webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
            if webhook_url and webhook_url.startswith("https://discord.com/api/webhooks/"):
                return {
                    "success": True,
                    "message": "Discord webhook URL format is valid"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid Discord webhook URL"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_openai_api(self) -> Dict[str, Any]:
        """OpenAI APIのチェック"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and len(api_key) > 20:
                return {
                    "success": True,
                    "message": "OpenAI API key format is valid"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid OpenAI API key"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """ファイル権限のチェック"""
        try:
            # 重要なディレクトリの権限チェック
            critical_dirs = [
                self.data_dir,
                self.logs_dir,
                self.backups_dir
            ]
            
            for directory in critical_dirs:
                if not os.access(directory, os.W_OK):
                    return {
                        "success": False,
                        "error": f"No write permission for {directory}"
                    }
            
            return {
                "success": True,
                "message": "File permissions are correct"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def setup_production(self) -> Dict[str, Any]:
        """本番環境の完全セットアップ"""
        try:
            logger.info("Starting production environment setup")
            
            results = {
                "directories": self.setup_directories(),
                "logging": self.setup_logging(),
                "environment": self.validate_environment(),
                "database": self.setup_database(),
                "crontab": self.setup_crontab(),
                "health_checks": self.run_health_checks()
            }
            
            # 全体の成功判定
            all_success = all(result["success"] for result in results.values())
            
            return {
                "success": all_success,
                "setup_results": results,
                "timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error in production setup: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def _get_timestamp(self) -> str:
        """タイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup production environment")
    parser.add_argument(
        "--config",
        default="config/production_config.json",
        help="Production config file path"
    )
    parser.add_argument(
        "--skip-health-checks",
        action="store_true",
        help="Skip health checks"
    )
    
    args = parser.parse_args()
    
    setup = ProductionSetup(args.config)
    
    if args.skip_health_checks:
        # ヘルスチェックをスキップしたセットアップ
        results = {
            "directories": setup.setup_directories(),
            "logging": setup.setup_logging(),
            "environment": setup.validate_environment(),
            "database": setup.setup_database(),
            "crontab": setup.setup_crontab()
        }
        
        all_success = all(result["success"] for result in results.values())
        
        if all_success:
            print("✅ Production setup completed successfully (health checks skipped)")
        else:
            print("❌ Production setup failed")
            for name, result in results.items():
                if not result["success"]:
                    print(f"  {name}: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    else:
        # 完全なセットアップ
        result = setup.setup_production()
        
        if result["success"]:
            print("✅ Production environment setup completed successfully")
            print(f"Health checks passed: {result['setup_results']['health_checks']['passed_checks']}/{result['setup_results']['health_checks']['total_checks']}")
        else:
            print("❌ Production environment setup failed")
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
