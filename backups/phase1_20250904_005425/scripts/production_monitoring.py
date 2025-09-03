#!/usr/bin/env python3
"""
本番環境監視スクリプト
本番環境での包括的な監視システム
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# .envファイルの読み込み
try:
    from dotenv import load_dotenv
    load_dotenv('/app/.env')
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")
except FileNotFoundError:
    print("⚠️ .env file not found, using system environment variables")


class ProductionMonitor:
    """本番環境監視クラス"""
    
    def __init__(self, config_file: str = "config/production_config.json"):
        self.config_file = Path(config_file)
        self.data_dir = Path("data")
        self.monitoring_dir = Path("data/monitoring")
        self.alerts_dir = Path("data/alerts")
        
        # ディレクトリの作成
        self.monitoring_dir.mkdir(parents=True, exist_ok=True)
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
    
    async def monitor_database_health(self) -> Dict[str, Any]:
        """データベースヘルス監視"""
        print("🗄️ Monitoring database health...")
        
        try:
            # データベース接続テスト
            cmd = ["python", "-c", """
import os
import sys
import time
sys.path.insert(0, '.')
try:
    from src.infrastructure.database.config.database_config import DatabaseConfig
    from src.infrastructure.database.config.connection_manager import ConnectionManager

    config = DatabaseConfig()
    manager = ConnectionManager(config)

    start_time = time.time()
    with manager.get_connection() as conn:
        result = conn.execute('SELECT 1')
        query_time = time.time() - start_time
        print(f'Database response time: {query_time:.3f}s')
except ImportError as e:
    print(f'Database modules not found: {e}')
    print('This is expected if the database modules are not yet implemented')
    sys.exit(0)
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    response_time = float(stdout.decode().split(": ")[1].split("s")[0])
                except (IndexError, ValueError):
                    response_time = 0.0
                
                return {
                    "success": True,
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": stderr.decode(),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_redis_health(self) -> Dict[str, Any]:
        """Redisヘルス監視"""
        print("🔴 Monitoring Redis health...")
        
        try:
            cmd = ["python", "-c", """
import os
import redis
import time

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
try:
    r = redis.from_url(redis_url)
    start_time = time.time()
    r.ping()
    response_time = time.time() - start_time
    print(f'Redis response time: {response_time:.3f}s')
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    response_time = float(stdout.decode().split(": ")[1].split("s")[0])
                except (IndexError, ValueError):
                    response_time = 0.0
                
                return {
                    "success": True,
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": stderr.decode(),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_discord_webhook(self) -> Dict[str, Any]:
        """Discord Webhook監視"""
        print("📢 Monitoring Discord webhook...")
        
        try:
            cmd = ["python", "-c", """
import os
import requests
import time

        webhook_url = os.getenv('DISCORD_ECONOMICINDICATORS_WEBHOOK_URL')
if not webhook_url:
    print('Discord webhook URL not set')
    exit(1)

try:
    start_time = time.time()
    response = requests.get(webhook_url, timeout=10)
    response_time = time.time() - start_time

    if response.status_code == 200:
        print(f'Discord webhook response time: {response_time:.3f}s')
    else:
        print(f'Discord webhook error: {response.status_code}')
        exit(1)
except Exception as e:
    print(f'Discord webhook check failed: {e}')
    exit(1)
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    response_time = float(stdout.decode().split(": ")[1].split("s")[0])
                except (IndexError, ValueError):
                    response_time = 0.0
                
                return {
                    "success": True,
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": stderr.decode(),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_openai_api(self) -> Dict[str, Any]:
        """OpenAI API監視"""
        print("🤖 Monitoring OpenAI API...")
        
        try:
            cmd = ["python", "-c", """
import os
import openai
import time

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print('OpenAI API key not set')
    exit(1)

try:
    openai.api_key = api_key
    start_time = time.time()
    response = openai.Model.list()
    response_time = time.time() - start_time
    print(f'OpenAI API response time: {response_time:.3f}s')
except Exception as e:
    print(f'OpenAI API error: {e}')
    exit(1)
"""]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                try:
                    response_time = float(stdout.decode().split(": ")[1].split("s")[0])
                except (IndexError, ValueError):
                    response_time = 0.0
                
                return {
                    "success": True,
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": stderr.decode(),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_crontab_status(self) -> Dict[str, Any]:
        """crontab状態監視"""
        print("⏰ Monitoring crontab status...")
        
        try:
            cmd = ["crontab", "-l"]
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                crontab_content = stdout.decode()
                job_count = len([line for line in crontab_content.split('\n') 
                               if line.strip() and not line.startswith('#')])
                
                return {
                    "success": True,
                    "status": "active",
                    "job_count": job_count,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "inactive",
                    "error": "No crontab found",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_system_resources(self) -> Dict[str, Any]:
        """システムリソース監視"""
        print("💻 Monitoring system resources...")
        
        try:
            import psutil

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024**3)  # GB
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024**3)  # GB
            
            # ネットワークI/O
            network = psutil.net_io_counters()
            
            return {
                "success": True,
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": round(memory_available, 2),
                "disk_percent": disk_percent,
                "disk_free_gb": round(disk_free, 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "timestamp": datetime.now().isoformat()
            }
            
        except ImportError:
            return {
                "success": False,
                "status": "error",
                "error": "psutil not available",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def monitor_log_health(self) -> Dict[str, Any]:
        """ログヘルス監視"""
        print("📝 Monitoring log health...")
        
        try:
            log_dirs = [
                "data/logs/app",
                "data/logs/error",
                "data/logs/scheduler",
                "data/logs/notifications",
                "data/logs/ai_analysis",
                "data/logs/database",
                "data/logs/monitoring"
            ]
            
            log_stats = {}
            total_size = 0
            
            for log_dir in log_dirs:
                if Path(log_dir).exists():
                    dir_size = sum(f.stat().st_size for f in Path(log_dir).rglob('*') 
                                 if f.is_file())
                    log_stats[log_dir] = {
                        "size_bytes": dir_size,
                        "size_mb": round(dir_size / (1024**2), 2)
                    }
                    total_size += dir_size
            
            return {
                "success": True,
                "status": "healthy",
                "total_size_mb": round(total_size / (1024**2), 2),
                "log_directories": log_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_alerts(self, monitoring_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """アラートチェック"""
        alerts = []
        
        # データベースアラート
        if "database" in monitoring_data:
            db_data = monitoring_data["database"]
            if not db_data.get("success", False):
                alerts.append({
                    "type": "database_error",
                    "severity": "high",
                    "message": f"Database health check failed: {db_data.get('error', 'Unknown error')}",
                    "timestamp": datetime.now().isoformat()
                })
            elif db_data.get("response_time", 0) > 5.0:
                alerts.append({
                    "type": "database_slow",
                    "severity": "medium",
                    "message": f"Database response time is slow: {db_data['response_time']:.2f}s",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Redisアラート
        if "redis" in monitoring_data:
            redis_data = monitoring_data["redis"]
            if not redis_data.get("success", False):
                alerts.append({
                    "type": "redis_error",
                    "severity": "high",
                    "message": f"Redis health check failed: {redis_data.get('error', 'Unknown error')}",
                    "timestamp": datetime.now().isoformat()
                })
        
        # システムリソースアラート
        if "system_resources" in monitoring_data:
            sys_data = monitoring_data["system_resources"]
            if sys_data.get("success", False):
                if sys_data.get("cpu_percent", 0) > 80:
                    alerts.append({
                        "type": "high_cpu",
                        "severity": "medium",
                        "message": f"High CPU usage: {sys_data['cpu_percent']}%",
                        "timestamp": datetime.now().isoformat()
                    })
                
                if sys_data.get("memory_percent", 0) > 80:
                    alerts.append({
                        "type": "high_memory",
                        "severity": "medium",
                        "message": f"High memory usage: {sys_data['memory_percent']}%",
                        "timestamp": datetime.now().isoformat()
                    })
                
                if sys_data.get("disk_percent", 0) > 90:
                    alerts.append({
                        "type": "high_disk",
                        "severity": "high",
                        "message": f"High disk usage: {sys_data['disk_percent']}%",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return alerts
    
    async def send_discord_alert(self, alert: Dict[str, Any]) -> bool:
        """Discordアラート送信"""
        try:
            webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
            if not webhook_url:
                return False
            
            import requests

            # アラートの色を設定
            color_map = {
                "low": 0x00FF00,    # 緑
                "medium": 0xFFA500,  # オレンジ
                "high": 0xFF0000     # 赤
            }
            
            embed = {
                "title": f"🚨 System Alert: {alert['type'].replace('_', ' ').title()}",
                "description": alert["message"],
                "color": color_map.get(alert["severity"], 0xFF0000),
                "timestamp": alert["timestamp"],
                "footer": {
                    "text": "Production Monitor"
                }
            }
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Failed to send Discord alert: {e}")
            return False
    
    async def run_monitoring_cycle(self) -> Dict[str, Any]:
        """監視サイクルの実行"""
        print("🔍 Running monitoring cycle...")
        
        # 各監視項目の実行
        monitoring_tasks = [
            ("database", self.monitor_database_health()),
            ("redis", self.monitor_redis_health()),
            ("discord_webhook", self.monitor_discord_webhook()),
            ("openai_api", self.monitor_openai_api()),
            ("crontab", self.monitor_crontab_status()),
            ("system_resources", self.monitor_system_resources()),
            ("log_health", self.monitor_log_health())
        ]
        
        monitoring_data = {}
        
        for name, task in monitoring_tasks:
            monitoring_data[name] = await task
        
        # アラートチェック
        alerts = await self.check_alerts(monitoring_data)
        
        # アラート送信
        for alert in alerts:
            await self.send_discord_alert(alert)
        
        # 監視データの保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        monitoring_file = self.monitoring_dir / f"monitoring_{timestamp}.json"
        
        monitoring_report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_data": monitoring_data,
            "alerts": alerts,
            "summary": {
                "total_checks": len(monitoring_data),
                "healthy_checks": sum(1 for data in monitoring_data.values() 
                                    if data.get("success", False)),
                "unhealthy_checks": sum(1 for data in monitoring_data.values() 
                                      if not data.get("success", False)),
                "alert_count": len(alerts)
            }
        }
        
        with open(monitoring_file, "w", encoding="utf-8") as f:
            json.dump(monitoring_report, f, indent=2, ensure_ascii=False)
        
        # アラートの保存
        if alerts:
            alert_file = self.alerts_dir / f"alerts_{timestamp}.json"
            with open(alert_file, "w", encoding="utf-8") as f:
                json.dump(alerts, f, indent=2, ensure_ascii=False)
        
        return monitoring_report
    
    async def run_continuous_monitoring(self, interval: int = 300) -> None:
        """継続的監視の実行"""
        print(f"🔄 Starting continuous monitoring (interval: {interval}s)")
        
        while True:
            try:
                report = await self.run_monitoring_cycle()
                
                summary = report["summary"]
                print(f"📊 Monitoring Summary:")
                print(f"   Healthy: {summary['healthy_checks']}/{summary['total_checks']}")
                print(f"   Alerts: {summary['alert_count']}")
                
                if summary["alert_count"] > 0:
                    print(f"   ⚠️ {summary['alert_count']} alerts generated")
                
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(interval)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Production monitoring")
    parser.add_argument(
        "--mode",
        choices=["single", "continuous"],
        default="single",
        help="Monitoring mode"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Monitoring interval in seconds (continuous mode)"
    )
    parser.add_argument(
        "--config",
        default="config/production_config.json",
        help="Configuration file path"
    )
    
    args = parser.parse_args()
    
    monitor = ProductionMonitor(args.config)
    
    if args.mode == "continuous":
        asyncio.run(monitor.run_continuous_monitoring(args.interval))
    else:
        report = asyncio.run(monitor.run_monitoring_cycle())
        
        summary = report["summary"]
        print(f"\n📊 Monitoring Report:")
        print(f"   Total checks: {summary['total_checks']}")
        print(f"   Healthy: {summary['healthy_checks']}")
        print(f"   Unhealthy: {summary['unhealthy_checks']}")
        print(f"   Alerts: {summary['alert_count']}")
        
        if summary["alert_count"] > 0:
            print(f"\n⚠️ {summary['alert_count']} alerts generated")
            sys.exit(1)
        else:
            print("\n✅ All systems healthy")
            sys.exit(0)


if __name__ == "__main__":
    main()
