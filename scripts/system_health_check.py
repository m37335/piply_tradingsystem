#!/usr/bin/env python3
"""
システム全体のヘルスチェックスクリプト

システム全体の状態を確認し、問題があれば報告します。
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_collection.core.data_collection_service import DataCollectionService
from modules.data_collection.config.settings import DataCollectionSettings
from modules.scheduler.core.scheduler_service import SchedulerService
from modules.scheduler.config.settings import SchedulerSettings
from modules.llm_analysis.core.llm_analysis_service import LLMAnalysisService
from modules.llm_analysis.config.settings import LLMAnalysisSettings
from modules.rate_limiting.core.integrated_rate_limit_manager import IntegratedRateLimitManager
from modules.rate_limiting.config.settings import RateLimitingSettings

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemHealthChecker:
    """システムヘルスチェッカー"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "services": {},
            "issues": [],
            "recommendations": []
        }
    
    async def check_all_services(self) -> dict:
        """すべてのサービスのヘルスチェックを実行"""
        logger.info("Starting system health check...")
        
        # 各サービスのヘルスチェック
        await self._check_data_collection_service()
        await self._check_scheduler_service()
        await self._check_llm_analysis_service()
        await self._check_rate_limiting_service()
        
        # 全体のステータスを決定
        self._determine_overall_status()
        
        # 推奨事項を生成
        self._generate_recommendations()
        
        logger.info("System health check completed")
        return self.results
    
    async def _check_data_collection_service(self) -> None:
        """データ収集サービスのヘルスチェック"""
        try:
            logger.info("Checking data collection service...")
            settings = DataCollectionSettings.from_env()
            service = DataCollectionService(settings)
            
            # ヘルスチェックを実行
            health = await service.health_check()
            
            self.results["services"]["data_collection"] = {
                "status": health.get("status", "unknown"),
                "details": health,
                "timestamp": datetime.now().isoformat()
            }
            
            if health.get("status") != "healthy":
                self.results["issues"].append({
                    "service": "data_collection",
                    "issue": f"Service status: {health.get('status')}",
                    "severity": "high" if health.get("status") == "unhealthy" else "medium"
                })
            
        except Exception as e:
            logger.error(f"Failed to check data collection service: {e}")
            self.results["services"]["data_collection"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results["issues"].append({
                "service": "data_collection",
                "issue": f"Health check failed: {e}",
                "severity": "high"
            })
    
    async def _check_scheduler_service(self) -> None:
        """スケジューラーサービスのヘルスチェック"""
        try:
            logger.info("Checking scheduler service...")
            settings = SchedulerSettings.from_env()
            service = SchedulerService(settings)
            
            # ヘルスチェックを実行
            health = await service.health_check()
            
            self.results["services"]["scheduler"] = {
                "status": health.get("status", "unknown"),
                "details": health,
                "timestamp": datetime.now().isoformat()
            }
            
            if health.get("status") != "healthy":
                self.results["issues"].append({
                    "service": "scheduler",
                    "issue": f"Service status: {health.get('status')}",
                    "severity": "high" if health.get("status") == "unhealthy" else "medium"
                })
            
        except Exception as e:
            logger.error(f"Failed to check scheduler service: {e}")
            self.results["services"]["scheduler"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results["issues"].append({
                "service": "scheduler",
                "issue": f"Health check failed: {e}",
                "severity": "high"
            })
    
    async def _check_llm_analysis_service(self) -> None:
        """LLM分析サービスのヘルスチェック"""
        try:
            logger.info("Checking LLM analysis service...")
            settings = LLMAnalysisSettings.from_env()
            service = LLMAnalysisService(settings)
            
            # ヘルスチェックを実行
            health = await service.health_check()
            
            self.results["services"]["llm_analysis"] = {
                "status": health.get("status", "unknown"),
                "details": health,
                "timestamp": datetime.now().isoformat()
            }
            
            if health.get("status") != "healthy":
                self.results["issues"].append({
                    "service": "llm_analysis",
                    "issue": f"Service status: {health.get('status')}",
                    "severity": "high" if health.get("status") == "unhealthy" else "medium"
                })
            
        except Exception as e:
            logger.error(f"Failed to check LLM analysis service: {e}")
            self.results["services"]["llm_analysis"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results["issues"].append({
                "service": "llm_analysis",
                "issue": f"Health check failed: {e}",
                "severity": "high"
            })
    
    async def _check_rate_limiting_service(self) -> None:
        """レート制限サービスのヘルスチェック"""
        try:
            logger.info("Checking rate limiting service...")
            settings = RateLimitingSettings.from_env()
            manager = IntegratedRateLimitManager(settings)
            
            # ヘルスチェックを実行
            health = await manager.health_check()
            
            self.results["services"]["rate_limiting"] = {
                "status": health.get("status", "unknown"),
                "details": health,
                "timestamp": datetime.now().isoformat()
            }
            
            if health.get("status") != "healthy":
                self.results["issues"].append({
                    "service": "rate_limiting",
                    "issue": f"Service status: {health.get('status')}",
                    "severity": "high" if health.get("status") == "unhealthy" else "medium"
                })
            
        except Exception as e:
            logger.error(f"Failed to check rate limiting service: {e}")
            self.results["services"]["rate_limiting"] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.results["issues"].append({
                "service": "rate_limiting",
                "issue": f"Health check failed: {e}",
                "severity": "high"
            })
    
    def _determine_overall_status(self) -> None:
        """全体のステータスを決定"""
        service_statuses = [
            service.get("status", "unknown")
            for service in self.results["services"].values()
        ]
        
        if "error" in service_statuses:
            self.results["overall_status"] = "critical"
        elif "unhealthy" in service_statuses:
            self.results["overall_status"] = "unhealthy"
        elif "degraded" in service_statuses:
            self.results["overall_status"] = "degraded"
        elif all(status == "healthy" for status in service_statuses):
            self.results["overall_status"] = "healthy"
        else:
            self.results["overall_status"] = "unknown"
    
    def _generate_recommendations(self) -> None:
        """推奨事項を生成"""
        recommendations = []
        
        # サービス別の推奨事項
        for service_name, service_info in self.results["services"].items():
            status = service_info.get("status", "unknown")
            
            if status == "error":
                recommendations.append({
                    "service": service_name,
                    "recommendation": "Check service configuration and dependencies",
                    "priority": "high"
                })
            elif status == "unhealthy":
                recommendations.append({
                    "service": service_name,
                    "recommendation": "Restart service and check logs",
                    "priority": "high"
                })
            elif status == "degraded":
                recommendations.append({
                    "service": service_name,
                    "recommendation": "Monitor service performance and consider scaling",
                    "priority": "medium"
                })
        
        # 全体的な推奨事項
        if self.results["overall_status"] == "critical":
            recommendations.append({
                "service": "system",
                "recommendation": "Immediate attention required - check all services",
                "priority": "critical"
            })
        elif self.results["overall_status"] == "unhealthy":
            recommendations.append({
                "service": "system",
                "recommendation": "System requires maintenance - schedule downtime",
                "priority": "high"
            })
        elif self.results["overall_status"] == "degraded":
            recommendations.append({
                "service": "system",
                "recommendation": "Monitor system performance closely",
                "priority": "medium"
            })
        elif self.results["overall_status"] == "healthy":
            recommendations.append({
                "service": "system",
                "recommendation": "System is operating normally - continue monitoring",
                "priority": "low"
            })
        
        self.results["recommendations"] = recommendations
    
    def print_summary(self) -> None:
        """サマリーを出力"""
        print("\n" + "="*60)
        print("SYSTEM HEALTH CHECK SUMMARY")
        print("="*60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['overall_status'].upper()}")
        print()
        
        # サービス別ステータス
        print("SERVICE STATUS:")
        for service_name, service_info in self.results["services"].items():
            status = service_info.get("status", "unknown")
            print(f"  {service_name}: {status.upper()}")
        print()
        
        # 問題の報告
        if self.results["issues"]:
            print("ISSUES FOUND:")
            for issue in self.results["issues"]:
                print(f"  [{issue['severity'].upper()}] {issue['service']}: {issue['issue']}")
            print()
        
        # 推奨事項
        if self.results["recommendations"]:
            print("RECOMMENDATIONS:")
            for rec in self.results["recommendations"]:
                print(f"  [{rec['priority'].upper()}] {rec['service']}: {rec['recommendation']}")
            print()
        
        print("="*60)
    
    def save_report(self, filename: str = None) -> None:
        """レポートをファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_check_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Health check report saved to {filename}")


async def main():
    """メイン関数"""
    checker = SystemHealthChecker()
    
    try:
        # ヘルスチェックを実行
        results = await checker.check_all_services()
        
        # サマリーを出力
        checker.print_summary()
        
        # レポートを保存
        checker.save_report()
        
        # 終了コードを設定
        if results["overall_status"] in ["critical", "unhealthy"]:
            sys.exit(1)
        elif results["overall_status"] == "degraded":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"\nERROR: Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
