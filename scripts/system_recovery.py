#!/usr/bin/env python3
"""
Exchange Analytics システム復旧プログラム
System Recovery Program for Exchange Analytics

このプログラムは、システムの主要サービスを確認し、
停止しているサービスを自動的に復旧します。

対応サービス：
- Cron サービス
- PostgreSQL データベース
- Redis キャッシュサーバー
- API サーバー
- パフォーマンス監視システム
"""

import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class ServiceStatus:
    """サービス状態を管理するデータクラス"""

    name: str
    is_running: bool
    status_message: str
    recovery_action: str
    priority: int  # 1: 高, 2: 中, 3: 低


class SystemRecoveryManager:
    """システム復旧管理クラス"""

    def __init__(self):
        self.logger = self._setup_logging()
        self.services_status: Dict[str, ServiceStatus] = {}
        self.recovery_log: List[str] = []

    def _setup_logging(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # ファイルハンドラー
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "system_recovery.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def check_service_status(
        self,
        service_name: str,
        check_command: str,
        start_command: str,
        status_pattern: str = "running",
    ) -> ServiceStatus:
        """サービス状態をチェック"""
        try:
            result = subprocess.run(
                check_command, shell=True, capture_output=True, text=True, timeout=10
            )

            is_running = status_pattern in result.stdout.lower()
            status_message = f"{'✅ 動作中' if is_running else '❌ 停止中'}"
            recovery_action = f"{start_command}" if not is_running else "不要"

            return ServiceStatus(
                name=service_name,
                is_running=is_running,
                status_message=status_message,
                recovery_action=recovery_action,
                priority=1 if service_name in ["cron", "postgresql"] else 2,
            )

        except subprocess.TimeoutExpired:
            return ServiceStatus(
                name=service_name,
                is_running=False,
                status_message="❌ タイムアウト",
                recovery_action=f"{start_command}",
                priority=1,
            )
        except Exception as e:
            return ServiceStatus(
                name=service_name,
                is_running=False,
                status_message=f"❌ エラー: {str(e)}",
                recovery_action=f"{start_command}",
                priority=1,
            )

    def check_cron_service(self) -> ServiceStatus:
        """Cronサービス状態チェック"""
        return self.check_service_status(
            "Cron", "service cron status", "service cron start", "running"
        )

    def check_postgresql_service(self) -> ServiceStatus:
        """PostgreSQLサービス状態チェック"""
        return self.check_service_status(
            "PostgreSQL",
            "service postgresql status",
            "service postgresql start",
            "online",
        )

    def check_redis_service(self) -> ServiceStatus:
        """Redisサービス状態チェック"""
        return self.check_service_status(
            "Redis",
            "service redis-server status",
            "service redis-server start",
            "running",
        )

    def check_api_server(self) -> ServiceStatus:
        """APIサーバー状態チェック"""
        try:
            result = subprocess.run(
                "./exchange-analytics api status",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=project_root,
            )

            is_running = (
                "running" in result.stdout.lower()
                or "接続できません" not in result.stdout
            )
            status_message = f"{'✅ 動作中' if is_running else '❌ 停止中'}"
            recovery_action = (
                "./exchange-analytics api start --background"
                if not is_running
                else "不要"
            )

            return ServiceStatus(
                name="API Server",
                is_running=is_running,
                status_message=status_message,
                recovery_action=recovery_action,
                priority=2,
            )

        except Exception as e:
            return ServiceStatus(
                name="API Server",
                is_running=False,
                status_message=f"❌ エラー: {str(e)}",
                recovery_action="./exchange-analytics api start --background",
                priority=2,
            )

    def check_performance_monitor(self) -> ServiceStatus:
        """パフォーマンス監視システム状態チェック"""
        try:
            # ログファイルの最終更新時刻をチェック
            log_file = project_root / "logs" / "performance_monitoring_test_cron.log"
            if not log_file.exists():
                return ServiceStatus(
                    name="Performance Monitor",
                    is_running=False,
                    status_message="❌ ログファイルなし",
                    recovery_action="手動確認が必要",
                    priority=3,
                )

            # 1時間以内に更新されているかチェック
            mtime = log_file.stat().st_mtime
            current_time = time.time()
            is_recent = (current_time - mtime) < 3600  # 1時間

            status_message = f"{'✅ 正常動作' if is_recent else '❌ 停止中'}"
            recovery_action = "手動実行が必要" if not is_recent else "不要"

            return ServiceStatus(
                name="Performance Monitor",
                is_running=is_recent,
                status_message=status_message,
                recovery_action=recovery_action,
                priority=3,
            )

        except Exception as e:
            return ServiceStatus(
                name="Performance Monitor",
                is_running=False,
                status_message=f"❌ エラー: {str(e)}",
                recovery_action="手動確認が必要",
                priority=3,
            )

    def recover_service(self, service: ServiceStatus) -> bool:
        """サービス復旧実行"""
        if service.is_running:
            self.logger.info(f"✅ {service.name}: 既に動作中")
            return True

        self.logger.info(f"🔄 {service.name}: 復旧開始...")
        self.recovery_log.append(f"{datetime.now()}: {service.name} 復旧開始")

        try:
            result = subprocess.run(
                service.recovery_action,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.logger.info(f"✅ {service.name}: 復旧成功")
                self.recovery_log.append(f"{datetime.now()}: {service.name} 復旧成功")
                return True
            else:
                self.logger.error(f"❌ {service.name}: 復旧失敗 - {result.stderr}")
                self.recovery_log.append(
                    f"{datetime.now()}: {service.name} 復旧失敗 - {result.stderr}"
                )
                return False

        except Exception as e:
            self.logger.error(f"❌ {service.name}: 復旧エラー - {str(e)}")
            self.recovery_log.append(
                f"{datetime.now()}: {service.name} 復旧エラー - {str(e)}"
            )
            return False

    def run_system_check(self) -> Dict[str, ServiceStatus]:
        """システム全体の状態チェック"""
        self.logger.info("🔍 システム状態チェック開始")

        services = [
            self.check_cron_service(),
            self.check_postgresql_service(),
            self.check_redis_service(),
            self.check_api_server(),
            self.check_performance_monitor(),
        ]

        for service in services:
            self.services_status[service.name] = service

        return self.services_status

    def run_system_recovery(self, auto_recover: bool = True) -> bool:
        """システム復旧実行"""
        self.logger.info("🚀 システム復旧開始")

        # 優先度順にソート
        sorted_services = sorted(
            self.services_status.values(), key=lambda x: x.priority
        )

        recovery_success = True

        # 今回の不具合経験を反映: Cronサービスが停止している場合の特別処理
        cron_service = next((s for s in sorted_services if s.name == "Cron"), None)
        if cron_service and not cron_service.is_running:
            self.logger.warning("🚨 重要: Cronサービスが停止しています")
            self.logger.warning(
                "⚠️ これにより、以下のサービスが影響を受ける可能性があります:"
            )
            self.logger.warning("   - パフォーマンス監視システム（定期実行停止）")
            self.logger.warning("   - APIサーバー自動起動（定期チェック停止）")
            self.logger.warning("   - データ取得システム（定期実行停止）")
            self.logger.warning("   - 経済指標配信システム（定期配信停止）")

            if auto_recover:
                self.logger.info("🔄 Cronサービスを最優先で復旧します...")
                if not self.recover_service(cron_service):
                    self.logger.error("❌ Cronサービス復旧に失敗しました")
                    recovery_success = False
                    return recovery_success
                else:
                    self.logger.info("✅ Cronサービス復旧成功")
                    # 復旧後、他のサービスも再チェック
                    time.sleep(2)
                    self.run_system_check()

        # 通常の復旧処理
        for service in sorted_services:
            if not service.is_running:
                if auto_recover:
                    if not self.recover_service(service):
                        recovery_success = False
                        if service.priority == 1:  # 高優先度サービスで失敗
                            break
                else:
                    self.logger.warning(f"⚠️ {service.name}: 手動復旧が必要")

        return recovery_success

    def print_status_report(self):
        """状態レポート表示"""
        print("\n" + "=" * 60)
        print("📊 Exchange Analytics システム状態レポート")
        print("=" * 60)

        # 今回の不具合経験を反映: システム全体の健全性評価
        cron_service = self.services_status.get("Cron")
        if cron_service and not cron_service.is_running:
            print("🚨 警告: Cronサービスが停止しています")
            print("   これにより、定期実行される全てのサービスが影響を受けます")
            print("   2025年8月24日の不具合と同様の問題が発生する可能性があります")
            print()

        for service in sorted(self.services_status.values(), key=lambda x: x.priority):
            status_icon = "🟢" if service.is_running else "🔴"
            priority_icon = (
                "🔥"
                if service.priority == 1
                else "⚡" if service.priority == 2 else "💡"
            )

            print(f"{status_icon} {priority_icon} {service.name}")
            print(f"   状態: {service.status_message}")
            if not service.is_running:
                print(f"   復旧: {service.recovery_action}")
            print()

        if self.recovery_log:
            print("📝 復旧ログ:")
            for log_entry in self.recovery_log[-5:]:  # 最新5件
                print(f"   {log_entry}")

        print("=" * 60)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Exchange Analytics システム復旧プログラム"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="状態チェックのみ実行"
    )
    parser.add_argument(
        "--auto-recover", action="store_true", default=True, help="自動復旧を有効にする"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログ出力")

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    recovery_manager = SystemRecoveryManager()

    try:
        # システム状態チェック
        services_status = recovery_manager.run_system_check()

        # 状態レポート表示
        recovery_manager.print_status_report()

        if args.check_only:
            return

        # 復旧が必要なサービスがあるかチェック
        stopped_services = [s for s in services_status.values() if not s.is_running]

        if not stopped_services:
            print("✅ 全てのサービスが正常に動作しています")
            return

        # 復旧実行
        if args.auto_recover:
            print(f"\n🔄 {len(stopped_services)}個のサービスを復旧します...")
            success = recovery_manager.run_system_recovery(auto_recover=True)

            if success:
                print("✅ システム復旧が完了しました")
            else:
                print("❌ 一部のサービスで復旧に失敗しました")
                print("手動での確認をお勧めします")
        else:
            print("\n⚠️ 自動復旧が無効です。手動で復旧してください")

    except KeyboardInterrupt:
        print("\n⚠️ 操作が中断されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
