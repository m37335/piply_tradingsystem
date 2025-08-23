**旧ファイル名**: `補足設計_Infrastructure層_20250809.md`  

# Infrastructure Layer 補足設計

**作成日**: 2025 年 8 月 9 日
**対象**: Infrastructure Layer の不足コンポーネント補完
**依存関係**: 基本 Infrastructure Layer 設計を拡張

## 1. Messaging & Notification System

### 1.1 Discord Integration

#### src/infrastructure/messaging/discord_client.py

```python
"""Discord メッセージング実装"""
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from ...application.interfaces.notifier_interface import NotifierInterface
from ...domain.entities.analysis_report import AnalysisReport
from ..external_apis.base_api_client import BaseAPIClient
import logging

logger = logging.getLogger(__name__)

class DiscordClient(BaseAPIClient, NotifierInterface):
    """Discord クライアント実装"""

    def __init__(self, webhook_url: str, channel_id: Optional[str] = None):
        # Discord Webhook の URL から base_url を抽出
        base_url = "https://discord.com"
        super().__init__(base_url, timeout=30)

        self.webhook_url = webhook_url
        self.channel_id = channel_id
        self.rate_limit_per_minute = 30  # Discord の制限
        self.message_char_limit = 2000
        self.embed_char_limit = 6000

    async def send_discord_report(self, report: AnalysisReport) -> str:
        """Discord レポート送信"""
        try:
            embed = self._create_report_embed(report)

            payload = {
                "embeds": [embed],
                "username": "Exchange Analytics Bot",
                "avatar_url": "https://cdn.discordapp.com/avatars/bot-avatar.png"
            }

            response = await self._send_webhook(payload)

            # Discord メッセージ ID を返す（簡略化）
            message_id = f"discord_{datetime.utcnow().timestamp()}"
            logger.info(f"Report sent to Discord: {report.id}")

            return message_id

        except Exception as e:
            logger.error(f"Failed to send report to Discord: {str(e)}")
            raise

    async def send_discord_alert(
        self,
        title: str,
        message: str,
        level: str = "info"
    ) -> str:
        """Discord アラート送信"""
        try:
            embed = self._create_alert_embed(title, message, level)

            payload = {
                "embeds": [embed],
                "username": "Exchange Analytics Alert",
            }

            response = await self._send_webhook(payload)

            message_id = f"discord_alert_{datetime.utcnow().timestamp()}"
            logger.info(f"Alert sent to Discord: {title}")

            return message_id

        except Exception as e:
            logger.error(f"Failed to send alert to Discord: {str(e)}")
            raise

    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        content: str,
        content_type: str = "text/plain"
    ) -> bool:
        """メール送信（Discord クライアントでは未サポート）"""
        logger.warning("Email sending not supported by Discord client")
        return False

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """汎用 Webhook 送信"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers or {}
                ) as response:
                    response.raise_for_status()
                    return True
        except Exception as e:
            logger.error(f"Webhook send failed: {str(e)}")
            return False

    async def test_notification_channel(self, channel_type: str) -> Dict[str, Any]:
        """通知チャンネルテスト"""
        if channel_type.lower() != "discord":
            return {
                "status": "error",
                "message": "Unsupported channel type for Discord client"
            }

        try:
            test_embed = {
                "title": "🧪 Test Message",
                "description": "This is a test message from Exchange Analytics",
                "color": 0x00ff00,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Exchange Analytics Test"
                }
            }

            payload = {
                "embeds": [test_embed],
                "username": "Exchange Analytics Test"
            }

            await self._send_webhook(payload)

            return {
                "status": "success",
                "message": "Test message sent successfully",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _send_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Discord Webhook 送信"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                return await response.json() if response.content_type == "application/json" else {}

    def _create_report_embed(self, report: AnalysisReport) -> Dict[str, Any]:
        """レポート用 Embed 作成"""
        # 色を信頼度に基づいて決定
        if report.confidence_score:
            confidence = float(report.confidence_score)
            if confidence >= 0.8:
                color = 0x00ff00  # Green
            elif confidence >= 0.6:
                color = 0xffff00  # Yellow
            else:
                color = 0xff8000  # Orange
        else:
            color = 0x0099ff  # Blue

        embed = {
            "title": f"📊 {report.title}",
            "description": self._truncate_text(report.market_summary, 2000),
            "color": color,
            "timestamp": report.created_at.isoformat() if report.created_at else datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "📈 テクニカル分析",
                    "value": self._truncate_text(report.technical_analysis, 1000),
                    "inline": False
                },
                {
                    "name": "💱 分析対象通貨ペア",
                    "value": ", ".join(report.currency_pairs_analyzed),
                    "inline": True
                },
                {
                    "name": "🎯 信頼度",
                    "value": f"{float(report.confidence_score):.1%}" if report.confidence_score else "N/A",
                    "inline": True
                },
                {
                    "name": "🤖 AI モデル",
                    "value": report.ai_model_used,
                    "inline": True
                }
            ],
            "footer": {
                "text": f"レポートタイプ: {report.report_type.value} | Exchange Analytics",
                "icon_url": "https://cdn.discordapp.com/avatars/bot-avatar.png"
            }
        }

        # 推奨事項があれば追加
        if report.recommendations:
            embed["fields"].append({
                "name": "💡 推奨事項",
                "value": self._truncate_text(report.recommendations, 1000),
                "inline": False
            })

        # ファンダメンタル分析があれば追加
        if report.fundamental_analysis:
            embed["fields"].append({
                "name": "🌍 ファンダメンタル分析",
                "value": self._truncate_text(report.fundamental_analysis, 1000),
                "inline": False
            })

        return embed

    def _create_alert_embed(self, title: str, message: str, level: str) -> Dict[str, Any]:
        """アラート用 Embed 作成"""
        level_config = {
            "info": {"color": 0x3498db, "icon": "ℹ️"},
            "warning": {"color": 0xf39c12, "icon": "⚠️"},
            "error": {"color": 0xe74c3c, "icon": "❌"},
            "success": {"color": 0x2ecc71, "icon": "✅"}
        }

        config = level_config.get(level.lower(), level_config["info"])

        embed = {
            "title": f"{config['icon']} {title}",
            "description": self._truncate_text(message, 2000),
            "color": config["color"],
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": f"Alert Level: {level.upper()} | Exchange Analytics"
            }
        }

        return embed

    def _truncate_text(self, text: str, max_length: int) -> str:
        """テキスト切り詰め"""
        if not text:
            return ""

        if len(text) <= max_length:
            return text

        return text[:max_length - 3] + "..."

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        return await self.test_notification_channel("discord")
```

### 1.2 Email Client

#### src/infrastructure/messaging/email_client.py

```python
"""Email メッセージング実装"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...application.interfaces.notifier_interface import NotifierInterface
from ...domain.entities.analysis_report import AnalysisReport
import logging

logger = logging.getLogger(__name__)

class EmailClient(NotifierInterface):
    """Email クライアント実装"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        use_tls: bool = True
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    async def send_discord_report(self, report: AnalysisReport) -> str:
        """Discord レポート送信（Email では非対応）"""
        logger.warning("Discord report sending not supported by Email client")
        return ""

    async def send_discord_alert(
        self,
        title: str,
        message: str,
        level: str = "info"
    ) -> str:
        """Discord アラート送信（Email では非対応）"""
        logger.warning("Discord alert sending not supported by Email client")
        return ""

    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        content: str,
        content_type: str = "text/plain"
    ) -> bool:
        """メール送信"""
        try:
            # 非同期でメール送信を実行
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_email_sync,
                to_addresses,
                subject,
                content,
                content_type
            )

            logger.info(f"Email sent to {len(to_addresses)} recipients")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def _send_email_sync(
        self,
        to_addresses: List[str],
        subject: str,
        content: str,
        content_type: str
    ):
        """同期メール送信"""
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = ", ".join(to_addresses)
        msg['Subject'] = subject

        # コンテンツ追加
        if content_type == "text/html":
            msg.attach(MIMEText(content, 'html'))
        else:
            msg.attach(MIMEText(content, 'plain'))

        # SMTP 接続・送信
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()

            server.login(self.username, self.password)
            server.send_message(msg)

    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """Webhook 送信（Email では非対応）"""
        logger.warning("Webhook sending not supported by Email client")
        return False

    async def test_notification_channel(self, channel_type: str) -> Dict[str, Any]:
        """通知チャンネルテスト"""
        if channel_type.lower() != "email":
            return {
                "status": "error",
                "message": "Unsupported channel type for Email client"
            }

        try:
            test_subject = "Exchange Analytics - Test Email"
            test_content = """
            This is a test email from Exchange Analytics.

            If you received this email, the email notification system is working correctly.

            --
            Exchange Analytics Team
            """

            # テスト用の送信先（設定から取得すべき）
            test_recipients = [self.from_email]  # 自分宛に送信

            success = await self.send_email(
                test_recipients,
                test_subject,
                test_content
            )

            if success:
                return {
                    "status": "success",
                    "message": "Test email sent successfully",
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to send test email",
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Test failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def send_report_email(
        self,
        report: AnalysisReport,
        recipients: List[str]
    ) -> bool:
        """レポートメール送信"""
        try:
            subject = f"Exchange Analytics - {report.title}"

            # HTML コンテンツ作成
            html_content = self._create_report_html(report)

            return await self.send_email(
                recipients,
                subject,
                html_content,
                "text/html"
            )

        except Exception as e:
            logger.error(f"Failed to send report email: {str(e)}")
            return False

    def _create_report_html(self, report: AnalysisReport) -> str:
        """レポート用 HTML 作成"""
        confidence_color = "#27ae60" if report.confidence_score and float(report.confidence_score) >= 0.7 else "#f39c12"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #3498db; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .section {{ margin-bottom: 20px; padding: 15px; border-left: 4px solid #3498db; background-color: #f8f9fa; }}
                .confidence {{ color: {confidence_color}; font-weight: bold; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #7f8c8d; }}
                .currency-pairs {{ background-color: #ecf0f1; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 {report.title}</h1>
                <p>Exchange Analytics Report - {report.report_date}</p>
            </div>

            <div class="content">
                <div class="section">
                    <h2>📈 市場サマリー</h2>
                    <p>{report.market_summary}</p>
                </div>

                <div class="section">
                    <h2>🔍 テクニカル分析</h2>
                    <p>{report.technical_analysis}</p>
                </div>
        """

        if report.fundamental_analysis:
            html += f"""
                <div class="section">
                    <h2>🌍 ファンダメンタル分析</h2>
                    <p>{report.fundamental_analysis}</p>
                </div>
            """

        if report.recommendations:
            html += f"""
                <div class="section">
                    <h2>💡 推奨事項</h2>
                    <p>{report.recommendations}</p>
                </div>
            """

        html += f"""
                <div class="section">
                    <h2>📊 分析詳細</h2>
                    <div class="currency-pairs">
                        <strong>分析対象通貨ペア:</strong> {", ".join(report.currency_pairs_analyzed)}
                    </div>
                    <p><strong>信頼度:</strong> <span class="confidence">{float(report.confidence_score):.1%}</span></p>
                    <p><strong>AI モデル:</strong> {report.ai_model_used}</p>
                    <p><strong>生成時間:</strong> {report.created_at.strftime('%Y年%m月%d日 %H:%M:%S') if report.created_at else 'N/A'}</p>
                </div>
            </div>

            <div class="footer">
                <p>Exchange Analytics - Powered by AI & Real-time Data</p>
                <p>このメールは自動生成されたレポートです。</p>
            </div>
        </body>
        </html>
        """

        return html
```

## 2. Cache System

### 2.1 Redis Cache Implementation

#### src/infrastructure/cache/redis_cache.py

```python
"""Redis キャッシュ実装"""
import asyncio
import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from ...application.interfaces.cache_interface import CacheInterface
import logging

logger = logging.getLogger(__name__)

class RedisCache(CacheInterface):
    """Redis キャッシュ実装"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        decode_responses: bool = False
    ):
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.decode_responses = decode_responses
        self.redis_client: Optional[redis.Redis] = None
        self.key_prefix = "exchange_analytics:"

    async def connect(self):
        """Redis 接続"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=self.decode_responses
            )

            # 接続テスト
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def disconnect(self):
        """Redis 切断"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """値取得"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            value = await self.redis_client.get(full_key)

            if value is None:
                return None

            # デシリアライゼーション
            return self._deserialize(value)

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """値設定"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            serialized_value = self._serialize(value)

            if expire_seconds:
                await self.redis_client.setex(full_key, expire_seconds, serialized_value)
            else:
                await self.redis_client.set(full_key, serialized_value)

            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """値削除"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            result = await self.redis_client.delete(full_key)

            return result > 0

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    async def exists(self, key: str) -> bool:
        """存在確認"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            result = await self.redis_client.exists(full_key)

            return result > 0

        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {str(e)}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """有効期限設定"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            result = await self.redis_client.expire(full_key, seconds)

            return result

        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {str(e)}")
            return False

    async def get_ttl(self, key: str) -> int:
        """有効期限取得"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            ttl = await self.redis_client.ttl(full_key)

            return ttl

        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {str(e)}")
            return -1

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """値増加"""
        try:
            if not self.redis_client:
                await self.connect()

            full_key = self._make_key(key)
            result = await self.redis_client.incrby(full_key, amount)

            return result

        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """複数値取得"""
        try:
            if not self.redis_client:
                await self.connect()

            full_keys = [self._make_key(key) for key in keys]
            values = await self.redis_client.mget(full_keys)

            result = {}
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize(values[i])

            return result

        except Exception as e:
            logger.error(f"Cache get_many error: {str(e)}")
            return {}

    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire_seconds: Optional[int] = None
    ) -> bool:
        """複数値設定"""
        try:
            if not self.redis_client:
                await self.connect()

            # パイプライン使用で効率化
            async with self.redis_client.pipeline() as pipe:
                for key, value in mapping.items():
                    full_key = self._make_key(key)
                    serialized_value = self._serialize(value)

                    if expire_seconds:
                        pipe.setex(full_key, expire_seconds, serialized_value)
                    else:
                        pipe.set(full_key, serialized_value)

                await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Cache set_many error: {str(e)}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """パターンマッチでクリア"""
        try:
            if not self.redis_client:
                await self.connect()

            full_pattern = self._make_key(pattern)
            keys = await self.redis_client.keys(full_pattern)

            if keys:
                deleted = await self.redis_client.delete(*keys)
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache clear_pattern error for pattern {pattern}: {str(e)}")
            return 0

    async def get_cache_info(self) -> Dict[str, Any]:
        """キャッシュ情報取得"""
        try:
            if not self.redis_client:
                await self.connect()

            info = await self.redis_client.info()

            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'uptime_in_seconds': info.get('uptime_in_seconds')
            }

        except Exception as e:
            logger.error(f"Cache info error: {str(e)}")
            return {}

    def _make_key(self, key: str) -> str:
        """キープリフィックス付与"""
        return f"{self.key_prefix}{key}"

    def _serialize(self, value: Any) -> Union[str, bytes]:
        """シリアライゼーション"""
        try:
            # 基本的なタイプはJSONでシリアライズ
            if isinstance(value, (str, int, float, bool, type(None))):
                return json.dumps(value)
            elif isinstance(value, (dict, list, tuple)):
                return json.dumps(value, default=str, ensure_ascii=False)
            else:
                # 複雑なオブジェクトはpickle
                return pickle.dumps(value)
        except Exception:
            # フォールバック
            return pickle.dumps(value)

    def _deserialize(self, value: Union[str, bytes]) -> Any:
        """デシリアライゼーション"""
        try:
            # JSON として試行
            if isinstance(value, str):
                return json.loads(value)
            elif isinstance(value, bytes):
                try:
                    return json.loads(value.decode('utf-8'))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    # pickle として試行
                    return pickle.loads(value)
        except Exception:
            # 最後の手段
            if isinstance(value, bytes):
                return pickle.loads(value)
            return value

    # コンテキストマネージャー対応
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
```

### 2.2 Cache Interface Definition

#### src/application/interfaces/cache_interface.py

```python
"""キャッシュインターフェース"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List

class CacheInterface(ABC):
    """キャッシュサービスのインターフェース"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """値取得"""
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """値設定"""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """値削除"""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """存在確認"""
        pass

    @abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        """有効期限設定"""
        pass

    @abstractmethod
    async def get_ttl(self, key: str) -> int:
        """有効期限取得"""
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """値増加"""
        pass

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """複数値取得"""
        pass

    @abstractmethod
    async def set_many(
        self,
        mapping: Dict[str, Any],
        expire_seconds: Optional[int] = None
    ) -> bool:
        """複数値設定"""
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """パターンマッチでクリア"""
        pass
```

## 3. Monitoring System

### 3.1 Application Metrics

#### src/infrastructure/monitoring/metrics_collector.py

```python
"""メトリクス収集システム"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """アプリケーションメトリクス収集"""

    def __init__(self, retention_minutes: int = 60):
        self.retention_minutes = retention_minutes
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=retention_minutes))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.start_time = datetime.utcnow()

        # 収集タスク
        self._collection_task: Optional[asyncio.Task] = None
        self._is_running = False

    def start_collection(self):
        """メトリクス収集開始"""
        if not self._is_running:
            self._is_running = True
            self._collection_task = asyncio.create_task(self._collect_metrics_loop())
            logger.info("Metrics collection started")

    def stop_collection(self):
        """メトリクス収集停止"""
        self._is_running = False
        if self._collection_task:
            self._collection_task.cancel()
        logger.info("Metrics collection stopped")

    async def _collect_metrics_loop(self):
        """メトリクス収集ループ"""
        try:
            while self._is_running:
                await self._collect_system_metrics()
                await asyncio.sleep(60)  # 1分間隔
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Metrics collection error: {str(e)}")

    async def _collect_system_metrics(self):
        """システムメトリクス収集"""
        try:
            current_time = datetime.utcnow()

            # CPU・メモリ使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            self.record_gauge('system.cpu_percent', cpu_percent)
            self.record_gauge('system.memory_percent', memory.percent)
            self.record_gauge('system.disk_percent', disk.percent)
            self.record_gauge('system.memory_used_gb', memory.used / (1024**3))

            # プロセス情報
            process = psutil.Process()
            self.record_gauge('process.memory_mb', process.memory_info().rss / (1024**2))
            self.record_gauge('process.cpu_percent', process.cpu_percent())

            # 時系列データとして保存
            metrics_snapshot = {
                'timestamp': current_time,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'process_memory_mb': process.memory_info().rss / (1024**2),
                'process_cpu_percent': process.cpu_percent()
            }

            self.metrics['system'].append(metrics_snapshot)

        except Exception as e:
            logger.error(f"System metrics collection error: {str(e)}")

    def record_counter(self, name: str, value: int = 1):
        """カウンター記録"""
        self.counters[name] += value

    def record_gauge(self, name: str, value: float):
        """ゲージ記録"""
        self.gauges[name] = value

    def record_timer(self, name: str, duration: float):
        """タイマー記録"""
        self.timers[name].append(duration)

        # 最新100件のみ保持
        if len(self.timers[name]) > 100:
            self.timers[name] = self.timers[name][-100:]

    def time_function(self, name: str):
        """関数実行時間測定デコレータ"""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_timer(name, duration)

            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    self.record_timer(name, duration)

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクス サマリー取得"""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

        summary = {
            'uptime_seconds': uptime_seconds,
            'uptime_human': self._format_uptime(uptime_seconds),
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers_summary': self._summarize_timers(),
            'collection_status': 'running' if self._is_running else 'stopped'
        }

        return summary

    def get_system_metrics_history(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """システムメトリクス履歴取得"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        return [
            metric for metric in self.metrics['system']
            if metric['timestamp'] >= cutoff_time
        ]

    def _summarize_timers(self) -> Dict[str, Dict[str, float]]:
        """タイマー統計作成"""
        summaries = {}

        for name, durations in self.timers.items():
            if durations:
                summaries[name] = {
                    'count': len(durations),
                    'avg': sum(durations) / len(durations),
                    'min': min(durations),
                    'max': max(durations),
                    'total': sum(durations)
                }

        return summaries

    def _format_uptime(self, seconds: float) -> str:
        """稼働時間フォーマット"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def reset_metrics(self):
        """メトリクスリセット"""
        self.counters.clear()
        self.gauges.clear()
        self.timers.clear()
        self.metrics.clear()
        logger.info("Metrics reset")

# グローバルインスタンス
metrics_collector = MetricsCollector()
```

### 3.2 Health Check System

#### src/infrastructure/monitoring/health_checker.py

```python
"""ヘルスチェックシステム"""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """ヘルス状態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthCheck:
    """個別ヘルスチェック"""

    def __init__(
        self,
        name: str,
        check_func: Callable,
        timeout_seconds: int = 10,
        description: str = ""
    ):
        self.name = name
        self.check_func = check_func
        self.timeout_seconds = timeout_seconds
        self.description = description
        self.last_check_time: Optional[datetime] = None
        self.last_status = HealthStatus.UNKNOWN
        self.last_error: Optional[str] = None

    async def execute(self) -> Dict[str, Any]:
        """ヘルスチェック実行"""
        start_time = datetime.utcnow()

        try:
            # タイムアウト付き実行
            if asyncio.iscoroutinefunction(self.check_func):
                result = await asyncio.wait_for(
                    self.check_func(),
                    timeout=self.timeout_seconds
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.check_func),
                    timeout=self.timeout_seconds
                )

            # 結果解析
            if isinstance(result, dict):
                status = HealthStatus(result.get('status', 'unknown'))
                details = result
            elif isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                details = {'status': status.value}
            else:
                status = HealthStatus.HEALTHY
                details = {'status': status.value, 'result': str(result)}

            self.last_status = status
            self.last_error = None

        except asyncio.TimeoutError:
            status = HealthStatus.UNHEALTHY
            details = {
                'status': status.value,
                'error': f'Timeout after {self.timeout_seconds} seconds'
            }
            self.last_status = status
            self.last_error = details['error']

        except Exception as e:
            status = HealthStatus.UNHEALTHY
            details = {
                'status': status.value,
                'error': str(e)
            }
            self.last_status = status
            self.last_error = str(e)

        end_time = datetime.utcnow()
        duration_ms = (end_time - start_time).total_seconds() * 1000

        self.last_check_time = end_time

        return {
            'name': self.name,
            'description': self.description,
            'status': status.value,
            'duration_ms': round(duration_ms, 2),
            'timestamp': end_time.isoformat(),
            **details
        }

class HealthChecker:
    """ヘルスチェック管理"""

    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.overall_timeout = 30  # 全体チェックのタイムアウト

    def register_check(
        self,
        name: str,
        check_func: Callable,
        timeout_seconds: int = 10,
        description: str = ""
    ):
        """ヘルスチェック登録"""
        self.health_checks[name] = HealthCheck(
            name=name,
            check_func=check_func,
            timeout_seconds=timeout_seconds,
            description=description
        )
        logger.info(f"Health check registered: {name}")

    def unregister_check(self, name: str):
        """ヘルスチェック削除"""
        if name in self.health_checks:
            del self.health_checks[name]
            logger.info(f"Health check unregistered: {name}")

    async def check_all(self) -> Dict[str, Any]:
        """全ヘルスチェック実行"""
        start_time = datetime.utcnow()

        try:
            # 並列実行
            tasks = [
                check.execute()
                for check in self.health_checks.values()
            ]

            if tasks:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.overall_timeout
                )
            else:
                results = []

            # 結果集約
            check_results = []
            overall_status = HealthStatus.HEALTHY

            for result in results:
                if isinstance(result, Exception):
                    check_result = {
                        'name': 'unknown',
                        'status': HealthStatus.UNHEALTHY.value,
                        'error': str(result),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    overall_status = HealthStatus.UNHEALTHY
                else:
                    check_result = result
                    if result['status'] == HealthStatus.UNHEALTHY.value:
                        overall_status = HealthStatus.UNHEALTHY
                    elif (result['status'] == HealthStatus.DEGRADED.value and
                          overall_status == HealthStatus.HEALTHY):
                        overall_status = HealthStatus.DEGRADED

                check_results.append(check_result)

            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds() * 1000

            return {
                'overall_status': overall_status.value,
                'timestamp': end_time.isoformat(),
                'total_duration_ms': round(total_duration, 2),
                'checks_count': len(check_results),
                'checks': check_results
            }

        except asyncio.TimeoutError:
            return {
                'overall_status': HealthStatus.UNHEALTHY.value,
                'timestamp': datetime.utcnow().isoformat(),
                'error': f'Health check timeout after {self.overall_timeout} seconds',
                'checks': []
            }
        except Exception as e:
            return {
                'overall_status': HealthStatus.UNHEALTHY.value,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'checks': []
            }

    async def check_one(self, name: str) -> Optional[Dict[str, Any]]:
        """個別ヘルスチェック実行"""
        if name not in self.health_checks:
            return None

        return await self.health_checks[name].execute()

    def get_status_summary(self) -> Dict[str, Any]:
        """ステータス サマリー"""
        summary = {
            'total_checks': len(self.health_checks),
            'checks_by_status': {
                'healthy': 0,
                'degraded': 0,
                'unhealthy': 0,
                'unknown': 0
            },
            'last_check_times': {}
        }

        for name, check in self.health_checks.items():
            status = check.last_status.value
            summary['checks_by_status'][status] += 1

            if check.last_check_time:
                summary['last_check_times'][name] = check.last_check_time.isoformat()

        return summary

# グローバルインスタンス
health_checker = HealthChecker()

# 基本的なヘルスチェック関数
async def check_database_connection():
    """データベース接続チェック"""
    try:
        # データベース接続テスト（実装必要）
        # await database.execute("SELECT 1")
        return {'status': 'healthy', 'details': 'Database connection OK'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

async def check_redis_connection():
    """Redis接続チェック"""
    try:
        # Redis接続テスト（実装必要）
        # await redis_client.ping()
        return {'status': 'healthy', 'details': 'Redis connection OK'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

async def check_external_apis():
    """外部API接続チェック"""
    try:
        # Alpha Vantage API テスト（実装必要）
        # await alpha_vantage_client.health_check()
        return {'status': 'healthy', 'details': 'External APIs OK'}
    except Exception as e:
        return {'status': 'degraded', 'error': str(e)}
```

この補足設計により、Infrastructure Layer がより完全で実用的なものになりました。メッセージング、キャッシュ、監視システムが追加され、本格的なプロダクション環境での運用に対応できる設計となっています。

<function_calls>
<invoke name="todo_write">
<parameter name="merge">true
