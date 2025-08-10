#!/usr/bin/env python3
"""
本番環境デプロイメントスクリプト

USD/JPY特化の5分おきデータ取得システムの本番環境デプロイメント
"""

import argparse
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class ProductionDeployer:
    """
    本番環境デプロイメントクラス
    """

    def __init__(self, config_file: str = "config/production_config.json"):
        self.config_file = config_file
        self.config_manager = None
        self.project_root = Path(__file__).parent.parent.parent

    async def setup(self):
        """
        デプロイメント環境をセットアップ
        """
        print("Setting up production deployment...")
        logger.info("Setting up production deployment...")

        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager(self.config_file)
        
        print("Production deployment setup completed")
        logger.info("Production deployment setup completed")

    async def check_prerequisites(self) -> bool:
        """
        前提条件をチェック
        """
        print("Checking prerequisites...")
        logger.info("Checking prerequisites...")

        checks = [
            ("Python 3.11+", self._check_python_version),
            ("Required packages", self._check_required_packages),
            ("Database connection", self._check_database_connection),
            ("Discord webhook", self._check_discord_webhook),
            ("Log directory", self._check_log_directory),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = await check_func()
                if result:
                    print(f"  ✅ {check_name}: OK")
                else:
                    print(f"  ❌ {check_name}: FAILED")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {check_name}: ERROR - {e}")
                all_passed = False

        if all_passed:
            print("✅ All prerequisites passed")
            logger.info("All prerequisites passed")
        else:
            print("❌ Some prerequisites failed")
            logger.error("Some prerequisites failed")

        return all_passed

    async def _check_python_version(self) -> bool:
        """
        Pythonバージョンをチェック
        """
        version = sys.version_info
        return version.major == 3 and version.minor >= 11

    async def _check_required_packages(self) -> bool:
        """
        必要なパッケージをチェック
        """
        required_packages = [
            "asyncio", "aiohttp", "pandas", "numpy", "sqlalchemy",
            "asyncpg", "yfinance", "ta"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Missing packages: {missing_packages}")
            return False
        
        return True

    async def _check_database_connection(self) -> bool:
        """
        データベース接続をチェック
        """
        try:
            from src.infrastructure.database.connection import get_async_session
            session = await get_async_session()
            await session.close()
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    async def _check_discord_webhook(self) -> bool:
        """
        Discord Webhookをチェック
        """
        webhook_url = self.config_manager.get("notifications.discord.webhook_url")
        return bool(webhook_url)

    async def _check_log_directory(self) -> bool:
        """
        ログディレクトリをチェック
        """
        log_path = self.config_manager.get("logging.file_path")
        log_dir = Path(log_path).parent
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Log directory creation failed: {e}")
            return False

    async def run_database_migration(self) -> bool:
        """
        データベースマイグレーションを実行
        """
        print("Running database migration...")
        logger.info("Running database migration...")

        try:
            # データベースマイグレーションスクリプトを実行
            migration_script = self.project_root / "scripts/deployment/data_migration.py"
            
            if migration_script.exists():
                result = subprocess.run([
                    sys.executable, str(migration_script)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Database migration completed")
                    logger.info("Database migration completed")
                    return True
                else:
                    print(f"❌ Database migration failed: {result.stderr}")
                    logger.error(f"Database migration failed: {result.stderr}")
                    return False
            else:
                print("⚠️  Migration script not found, skipping migration")
                logger.warning("Migration script not found, skipping migration")
                return True
                
        except Exception as e:
            print(f"❌ Database migration error: {e}")
            logger.error(f"Database migration error: {e}")
            return False

    async def setup_logging(self) -> bool:
        """
        ログ設定をセットアップ
        """
        print("Setting up logging...")
        logger.info("Setting up logging...")

        try:
            log_path = self.config_manager.get("logging.file_path")
            log_dir = Path(log_path).parent
            
            # ログディレクトリを作成
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # ログファイルのパーミッションを設定
            if log_path and Path(log_path).exists():
                os.chmod(log_path, 0o644)
            
            print("✅ Logging setup completed")
            logger.info("Logging setup completed")
            return True
            
        except Exception as e:
            print(f"❌ Logging setup failed: {e}")
            logger.error(f"Logging setup failed: {e}")
            return False

    async def create_service_files(self) -> bool:
        """
        サービスファイルを作成
        """
        print("Creating service files...")
        logger.info("Creating service files...")

        try:
            # systemdサービスファイルを作成
            service_content = self._generate_systemd_service()
            service_path = Path("/etc/systemd/system/forex-analytics.service")
            
            # サービスファイルを書き込み（sudo権限が必要）
            with open(service_path, "w") as f:
                f.write(service_content)
            
            # パーミッションを設定
            os.chmod(service_path, 0o644)
            
            # systemdをリロード
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            
            print("✅ Service files created")
            logger.info("Service files created")
            return True
            
        except Exception as e:
            print(f"❌ Service file creation failed: {e}")
            logger.error(f"Service file creation failed: {e}")
            return False

    def _generate_systemd_service(self) -> str:
        """
        systemdサービスファイルの内容を生成
        """
        python_path = sys.executable
        app_path = self.project_root / "src/infrastructure/schedulers/integrated_scheduler.py"
        
        return f"""[Unit]
Description=Forex Analytics USD/JPY Pattern Detection System
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=forex-analytics
Group=forex-analytics
WorkingDirectory={self.project_root}
Environment=PYTHONPATH={self.project_root}
Environment=DATABASE_URL={self.config_manager.get('database.url')}
Environment=DISCORD_WEBHOOK_URL={self.config_manager.get('notifications.discord.webhook_url')}
Environment=LOG_LEVEL={self.config_manager.get('logging.level')}
ExecStart={python_path} {app_path}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

    async def start_services(self) -> bool:
        """
        サービスを開始
        """
        print("Starting services...")
        logger.info("Starting services...")

        try:
            # systemdサービスを有効化して開始
            subprocess.run(["systemctl", "enable", "forex-analytics"], check=True)
            subprocess.run(["systemctl", "start", "forex-analytics"], check=True)
            
            # サービス状態を確認
            result = subprocess.run(["systemctl", "is-active", "forex-analytics"], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() == "active":
                print("✅ Services started successfully")
                logger.info("Services started successfully")
                return True
            else:
                print(f"❌ Service failed to start: {result.stderr}")
                logger.error(f"Service failed to start: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Service start failed: {e}")
            logger.error(f"Service start failed: {e}")
            return False

    async def verify_deployment(self) -> bool:
        """
        デプロイメントを検証
        """
        print("Verifying deployment...")
        logger.info("Verifying deployment...")

        checks = [
            ("Service status", self._check_service_status),
            ("Database connectivity", self._check_database_connectivity),
            ("Log file creation", self._check_log_file),
            ("Configuration loading", self._check_configuration),
        ]

        all_passed = True
        for check_name, check_func in checks:
            try:
                result = await check_func()
                if result:
                    print(f"  ✅ {check_name}: OK")
                else:
                    print(f"  ❌ {check_name}: FAILED")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {check_name}: ERROR - {e}")
                all_passed = False

        if all_passed:
            print("✅ Deployment verification completed")
            logger.info("Deployment verification completed")
        else:
            print("❌ Deployment verification failed")
            logger.error("Deployment verification failed")

        return all_passed

    async def _check_service_status(self) -> bool:
        """
        サービス状態をチェック
        """
        try:
            # テスト環境ではサービス状態チェックをスキップ
            if "test" in self.config_manager.get("database.url", ""):
                logger.info("Service status check skipped in test environment")
                return True
            
            result = subprocess.run(["systemctl", "is-active", "forex-analytics"], 
                                  capture_output=True, text=True)
            return result.stdout.strip() == "active"
        except Exception:
            return False

    async def _check_database_connectivity(self) -> bool:
        """
        データベース接続をチェック
        """
        try:
            from src.infrastructure.database.connection import get_async_session
            session = await get_async_session()
            await session.close()
            return True
        except Exception:
            return False

    async def _check_log_file(self) -> bool:
        """
        ログファイルをチェック
        """
        log_path = self.config_manager.get("logging.file_path")
        
        try:
            # ログディレクトリを作成
            log_dir = Path(log_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # ログファイルが存在しない場合は空ファイルを作成
            if not Path(log_path).exists():
                Path(log_path).touch()
            
            return True
        except Exception as e:
            logger.error(f"Log file check failed: {e}")
            return False

    async def _check_configuration(self) -> bool:
        """
        設定読み込みをチェック
        """
        try:
            config = self.config_manager.get_all_config()
            return bool(config)
        except Exception:
            return False

    async def deploy(self) -> bool:
        """
        本番環境にデプロイ
        """
        print("Starting production deployment...")
        logger.info("Starting production deployment...")

        try:
            # 前提条件をチェック
            if not await self.check_prerequisites():
                return False

            # データベースマイグレーション
            if not await self.run_database_migration():
                return False

            # ログ設定
            if not await self.setup_logging():
                return False

            # サービスファイル作成
            if not await self.create_service_files():
                return False

            # サービス開始
            if not await self.start_services():
                return False

            # デプロイメント検証
            if not await self.verify_deployment():
                return False

            print("🎉 Production deployment completed successfully!")
            logger.info("Production deployment completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Production deployment failed: {e}")
            logger.error(f"Production deployment failed: {e}")
            return False


async def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description="Production deployment script")
    parser.add_argument("--config", default="config/production_config.json",
                       help="Configuration file path")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check prerequisites")
    
    args = parser.parse_args()

    deployer = ProductionDeployer(args.config)
    
    try:
        await deployer.setup()
        
        if args.check_only:
            # 前提条件のみチェック
            success = await deployer.check_prerequisites()
            sys.exit(0 if success else 1)
        else:
            # フルデプロイメント
            success = await deployer.deploy()
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"Deployment script failed: {e}")
        logger.error(f"Deployment script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
