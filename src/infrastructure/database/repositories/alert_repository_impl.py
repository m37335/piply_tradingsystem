"""
Alert Repository Implementation
アラートリポジトリ実装

責任:
- アラートデータの永続化
- アラート検索・フィルタリング
- アラート状態管理
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.alert_model import AlertModel
from src.infrastructure.database.repositories.base_repository_impl import (
    BaseRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class AlertRepositoryImpl(BaseRepositoryImpl):
    """
    アラートリポジトリ実装

    責任:
    - アラートデータのCRUD操作
    - アラート検索・フィルタリング
    - アラート統計情報の取得
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def save(self, alert: AlertModel) -> AlertModel:
        """
        アラートを保存

        Args:
            alert: 保存するアラート

        Returns:
            AlertModel: 保存されたアラート
        """
        try:
            # セッションに追加
            self.session.add(alert)
            await self.session.commit()
            await self.session.refresh(alert)

            logger.info(f"Saved alert: {alert.alert_type} - {alert.severity}")
            return alert

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to save alert: {str(e)}")
            raise

    async def find_active_alerts(
        self,
        limit: Optional[int] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
    ) -> List[AlertModel]:
        """
        アクティブなアラートを取得

        Args:
            limit: 取得件数制限
            severity: 重要度フィルタ
            alert_type: アラートタイプフィルタ

        Returns:
            List[AlertModel]: アクティブなアラートのリスト
        """
        try:
            query = select(AlertModel).where(AlertModel.status == "active")

            if severity:
                query = query.where(AlertModel.severity == severity)

            if alert_type:
                query = query.where(AlertModel.alert_type == alert_type)

            query = query.order_by(desc(AlertModel.created_at))

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            alerts = result.scalars().all()

            logger.info(f"Found {len(alerts)} active alerts")
            return alerts

        except Exception as e:
            logger.error(f"Error finding active alerts: {e}")
            return []

    async def find_by_severity(
        self, severity: str, limit: Optional[int] = None
    ) -> List[AlertModel]:
        """
        重要度でアラートを検索

        Args:
            severity: 重要度
            limit: 取得件数制限

        Returns:
            List[AlertModel]: アラートのリスト
        """
        try:
            query = select(AlertModel).where(AlertModel.severity == severity)
            query = query.order_by(desc(AlertModel.created_at))

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            alerts = result.scalars().all()

            logger.info(f"Found {len(alerts)} alerts with severity {severity}")
            return alerts

        except Exception as e:
            logger.error(f"Error finding alerts by severity: {e}")
            return []

    async def find_by_type(
        self, alert_type: str, limit: Optional[int] = None
    ) -> List[AlertModel]:
        """
        アラートタイプで検索

        Args:
            alert_type: アラートタイプ
            limit: 取得件数制限

        Returns:
            List[AlertModel]: アラートのリスト
        """
        try:
            query = select(AlertModel).where(AlertModel.alert_type == alert_type)
            query = query.order_by(desc(AlertModel.created_at))

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            alerts = result.scalars().all()

            logger.info(f"Found {len(alerts)} alerts of type {alert_type}")
            return alerts

        except Exception as e:
            logger.error(f"Error finding alerts by type: {e}")
            return []

    async def find_recent_alerts(
        self, hours: int = 24, limit: Optional[int] = None
    ) -> List[AlertModel]:
        """
        最近のアラートを取得

        Args:
            hours: 何時間前まで
            limit: 取得件数制限

        Returns:
            List[AlertModel]: アラートのリスト
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            query = select(AlertModel).where(AlertModel.created_at >= cutoff_time)
            query = query.order_by(desc(AlertModel.created_at))

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            alerts = result.scalars().all()

            logger.info(f"Found {len(alerts)} recent alerts (last {hours}h)")
            return alerts

        except Exception as e:
            logger.error(f"Error finding recent alerts: {e}")
            return []

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """
        アラート統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            # 総アラート数
            total_query = select(func.count(AlertModel.id))
            total_result = await self.session.execute(total_query)
            total_count = total_result.scalar() or 0

            # アクティブアラート数
            active_query = select(func.count(AlertModel.id)).where(
                AlertModel.status == "active"
            )
            active_result = await self.session.execute(active_query)
            active_count = active_result.scalar() or 0

            # 重要度別統計
            severity_stats = {}
            for severity in ["low", "medium", "high", "critical"]:
                query = select(func.count(AlertModel.id)).where(
                    AlertModel.severity == severity
                )
                result = await self.session.execute(query)
                count = result.scalar() or 0
                severity_stats[severity] = count

            # タイプ別統計
            type_stats = {}
            type_query = select(
                AlertModel.alert_type, func.count(AlertModel.id)
            ).group_by(AlertModel.alert_type)
            type_result = await self.session.execute(type_query)

            for alert_type, count in type_result:
                type_stats[alert_type] = count

            # 今日のアラート数
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            today_query = select(func.count(AlertModel.id)).where(
                AlertModel.created_at >= today_start
            )
            today_result = await self.session.execute(today_query)
            today_count = today_result.scalar() or 0

            stats = {
                "total_alerts": total_count,
                "active_alerts": active_count,
                "resolved_alerts": total_count - active_count,
                "severity_distribution": severity_stats,
                "type_distribution": type_stats,
                "today_alerts": today_count,
                "last_updated": datetime.now().isoformat(),
            }

            logger.info(
                f"Alert statistics: {active_count} active out of {total_count} total"
            )
            return stats

        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}

    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """
        アラートを確認済みにする

        Args:
            alert_id: アラートID
            acknowledged_by: 確認者

        Returns:
            bool: 成功時True
        """
        try:
            alert = await self.find_by_id(alert_id)
            if not alert:
                logger.warning(f"Alert {alert_id} not found")
                return False

            alert.acknowledge(acknowledged_by)
            await self.session.commit()

            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            await self.session.rollback()
            return False

    async def resolve_alert(self, alert_id: int, resolved_by: str) -> bool:
        """
        アラートを解決済みにする

        Args:
            alert_id: アラートID
            resolved_by: 解決者

        Returns:
            bool: 成功時True
        """
        try:
            alert = await self.find_by_id(alert_id)
            if not alert:
                logger.warning(f"Alert {alert_id} not found")
                return False

            alert.resolve(resolved_by)
            await self.session.commit()

            logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            await self.session.rollback()
            return False

    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        currency_pair: Optional[str] = None,
        details: Optional[Dict] = None,
        related_data_id: Optional[int] = None,
        related_data_type: Optional[str] = None,
    ) -> Optional[AlertModel]:
        """
        新しいアラートを作成

        Args:
            alert_type: アラートタイプ
            severity: 重要度
            message: メッセージ
            currency_pair: 通貨ペア
            details: 詳細データ
            related_data_id: 関連データID
            related_data_type: 関連データタイプ

        Returns:
            Optional[AlertModel]: 作成されたアラート
        """
        try:
            # アラートタイプ別のWebhook URLを取得
            webhook_url = self._get_webhook_url_for_alert_type(alert_type)

            # 詳細データにWebhook URLを追加
            if details is None:
                details = {}
            details["discord_webhook_url"] = webhook_url

            alert = AlertModel(
                alert_type=alert_type,
                severity=severity,
                message=message,
                currency_pair=currency_pair,
                details=details,
                related_data_id=related_data_id,
                related_data_type=related_data_type,
            )

            saved_alert = await self.save(alert)
            logger.info(f"Created alert: {alert_type} - {severity} - {message}")
            return saved_alert

        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None

    def _get_webhook_url_for_alert_type(self, alert_type: str) -> Optional[str]:
        """
        アラートタイプに応じたWebhook URLを取得

        Args:
            alert_type: アラートタイプ

        Returns:
            Optional[str]: Webhook URL
        """
        try:
            from src.infrastructure.config.alert_config_manager import (
                AlertConfigManager,
            )

            config_manager = AlertConfigManager()
            return config_manager.get_discord_webhook_url(alert_type)

        except Exception as e:
            logger.error(f"Error getting webhook URL for alert type {alert_type}: {e}")
            return None
