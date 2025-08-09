"""
Discord Webhook Client
Discord Webhook クライアント

設計書参照:
- インフラ・プラグイン設計_20250809.md

Discord Webhookを使用してメッセージを送信するクライアント
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from ...utils.logging_config import get_infrastructure_logger
from ..external_apis.base_client import APIError, BaseAPIClient

logger = get_infrastructure_logger()


class DiscordClient(BaseAPIClient):
    """
    Discord Webhookクライアント

    責任:
    - Discord Webhookへのメッセージ送信
    - リッチ埋め込み（Embed）の作成
    - ファイル添付の管理
    - エラーハンドリング

    Discord Webhook仕様:
    - 30リクエスト/分の制限
    - 1メッセージあたり2000文字まで
    - 埋め込みは最大10個まで
    """

    def __init__(
        self,
        webhook_url: str,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        **kwargs,
    ):
        """
        初期化

        Args:
            webhook_url: Discord Webhook URL
            username: デフォルトのユーザー名
            avatar_url: デフォルトのアバターURL
            **kwargs: BaseAPIClientの引数
        """
        # URLからベースURLを抽出
        if "/api/webhooks/" in webhook_url:
            base_url = webhook_url.split("/api/webhooks/")[0]
            self.webhook_path = (
                "/api/webhooks/" + webhook_url.split("/api/webhooks/")[1]
            )
        else:
            raise ValueError("Invalid Discord webhook URL")

        super().__init__(
            base_url=base_url,
            rate_limit_calls=30,  # Discord webhook制限
            rate_limit_period=60,
            **kwargs,
        )

        self.webhook_url = webhook_url
        self.default_username = username
        self.default_avatar_url = avatar_url

        logger.info("Initialized Discord webhook client")

    def _get_auth_params(self) -> Dict[str, str]:
        """
        認証パラメータを取得
        Discord Webhookは認証不要

        Returns:
            Dict[str, str]: 空の辞書
        """
        return {}

    async def send_message(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tts: bool = False,
        file: Optional[bytes] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Discordにメッセージを送信

        Args:
            content: メッセージ内容（最大2000文字）
            embeds: 埋め込みのリスト（最大10個）
            username: 送信者名
            avatar_url: アバターURL
            tts: Text-to-Speech有効フラグ
            file: 添付ファイルのバイナリデータ
            filename: 添付ファイル名

        Returns:
            Dict[str, Any]: Discord APIレスポンス

        Raises:
            APIError: 送信エラー
        """
        try:
            # メッセージデータを構築
            payload = self._build_message_payload(
                content=content,
                embeds=embeds,
                username=username or self.default_username,
                avatar_url=avatar_url or self.default_avatar_url,
                tts=tts,
            )

            # バリデーション
            self._validate_message(payload)

            logger.debug(
                f"Sending Discord message: {len(content or '')} chars, {len(embeds or [])} embeds"
            )

            # ファイル添付がある場合
            if file and filename:
                response = await self._send_with_file(payload, file, filename)
            else:
                response = await self.post(self.webhook_path, data=payload)

            logger.info("Discord message sent successfully")
            return response

        except Exception as e:
            logger.error(f"Failed to send Discord message: {str(e)}")
            raise APIError(f"Discord message send failed: {str(e)}")

    async def send_market_report(
        self,
        report_title: str,
        report_content: str,
        market_data: Optional[Dict[str, Any]] = None,
        technical_analysis: Optional[str] = None,
        recommendations: Optional[str] = None,
        confidence_score: Optional[float] = None,
        color: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        市場分析レポートを送信

        Args:
            report_title: レポートタイトル
            report_content: レポート内容
            market_data: 市場データ
            technical_analysis: テクニカル分析
            recommendations: 推奨事項
            confidence_score: 信頼度スコア
            color: 埋め込みの色（16進数）

        Returns:
            Dict[str, Any]: 送信レスポンス
        """
        try:
            # レポート用埋め込みを作成
            embed = self._create_report_embed(
                title=report_title,
                content=report_content,
                market_data=market_data,
                technical_analysis=technical_analysis,
                recommendations=recommendations,
                confidence_score=confidence_score,
                color=color,
            )

            # 短いサマリーメッセージ
            summary = f"📊 **{report_title}**\n市場分析レポートが生成されました。"

            return await self.send_message(
                content=summary, embeds=[embed], username="Market Analyst Bot"
            )

        except Exception as e:
            logger.error(f"Failed to send market report: {str(e)}")
            raise

    async def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        currency_pair: Optional[str] = None,
        current_rate: Optional[float] = None,
        threshold: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        urgency: str = "normal",
    ) -> Dict[str, Any]:
        """
        アラート通知を送信

        Args:
            alert_type: アラート種別
            title: アラートタイトル
            message: アラートメッセージ
            currency_pair: 対象通貨ペア
            current_rate: 現在のレート
            threshold: 閾値
            timestamp: タイムスタンプ
            urgency: 緊急度（normal, high, critical）

        Returns:
            Dict[str, Any]: 送信レスポンス
        """
        try:
            # 緊急度に応じた色を設定
            color_map = {
                "normal": 0x3498DB,  # 青
                "high": 0xF39C12,  # オレンジ
                "critical": 0xE74C3C,  # 赤
            }
            color = color_map.get(urgency, 0x3498DB)

            # アラート用埋め込みを作成
            embed = self._create_alert_embed(
                alert_type=alert_type,
                title=title,
                message=message,
                currency_pair=currency_pair,
                current_rate=current_rate,
                threshold=threshold,
                timestamp=timestamp or datetime.utcnow(),
                color=color,
            )

            # 緊急度に応じた絵文字
            emoji_map = {"normal": "ℹ️", "high": "⚠️", "critical": "🚨"}
            emoji = emoji_map.get(urgency, "ℹ️")

            alert_content = f"{emoji} **{urgency.upper()} ALERT** {emoji}\n{title}"

            return await self.send_message(
                content=alert_content, embeds=[embed], username="Alert System"
            )

        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
            raise

    def _build_message_payload(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Dict[str, Any]]] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
        tts: bool = False,
    ) -> Dict[str, Any]:
        """
        メッセージペイロードを構築

        Args:
            content: メッセージ内容
            embeds: 埋め込みリスト
            username: ユーザー名
            avatar_url: アバターURL
            tts: TTS有効フラグ

        Returns:
            Dict[str, Any]: メッセージペイロード
        """
        payload = {}

        if content:
            payload["content"] = content

        if embeds:
            payload["embeds"] = embeds

        if username:
            payload["username"] = username

        if avatar_url:
            payload["avatar_url"] = avatar_url

        if tts:
            payload["tts"] = tts

        return payload

    def _validate_message(self, payload: Dict[str, Any]) -> None:
        """
        メッセージをバリデーション

        Args:
            payload: メッセージペイロード

        Raises:
            ValueError: バリデーションエラー
        """
        # コンテンツまたは埋め込みが必要
        if not payload.get("content") and not payload.get("embeds"):
            raise ValueError("Message must have content or embeds")

        # コンテンツ長制限
        content = payload.get("content", "")
        if len(content) > 2000:
            raise ValueError(f"Content too long: {len(content)} > 2000 characters")

        # 埋め込み数制限
        embeds = payload.get("embeds", [])
        if len(embeds) > 10:
            raise ValueError(f"Too many embeds: {len(embeds)} > 10")

        # 埋め込みの詳細バリデーション
        for i, embed in enumerate(embeds):
            self._validate_embed(embed, i)

    def _validate_embed(self, embed: Dict[str, Any], index: int) -> None:
        """
        埋め込みをバリデーション

        Args:
            embed: 埋め込みデータ
            index: 埋め込みのインデックス
        """
        # タイトル長制限
        title = embed.get("title", "")
        if len(title) > 256:
            raise ValueError(f"Embed {index} title too long: {len(title)} > 256")

        # 説明長制限
        description = embed.get("description", "")
        if len(description) > 4096:
            raise ValueError(
                f"Embed {index} description too long: {len(description)} > 4096"
            )

        # フィールド数制限
        fields = embed.get("fields", [])
        if len(fields) > 25:
            raise ValueError(f"Embed {index} too many fields: {len(fields)} > 25")

        # フィールドの詳細チェック
        for j, field in enumerate(fields):
            field_name = field.get("name", "")
            field_value = field.get("value", "")

            if len(field_name) > 256:
                raise ValueError(
                    f"Embed {index} field {j} name too long: {len(field_name)} > 256"
                )

            if len(field_value) > 1024:
                raise ValueError(
                    f"Embed {index} field {j} value too long: {len(field_value)} > 1024"
                )

    def _create_report_embed(
        self,
        title: str,
        content: str,
        market_data: Optional[Dict[str, Any]] = None,
        technical_analysis: Optional[str] = None,
        recommendations: Optional[str] = None,
        confidence_score: Optional[float] = None,
        color: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        レポート用埋め込みを作成

        Args:
            title: タイトル
            content: 内容
            market_data: 市場データ
            technical_analysis: テクニカル分析
            recommendations: 推奨事項
            confidence_score: 信頼度スコア
            color: 色

        Returns:
            Dict[str, Any]: 埋め込みデータ
        """
        embed = {
            "title": title[:256],  # タイトル長制限
            "description": content[:4096],  # 説明長制限
            "color": color or 0x1F8B4C,  # デフォルト緑色
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "Exchange Analytics System",
                "icon_url": "https://cdn.discordapp.com/embed/avatars/0.png",
            },
            "fields": [],
        }

        # 市場データを追加
        if market_data:
            market_text = ""
            for pair, data in list(market_data.items())[:5]:  # 最大5ペア
                if isinstance(data, dict) and "latest_rate" in data:
                    rate_info = data["latest_rate"]
                    market_text += f"**{pair}**: {rate_info.rate}\n"
                elif isinstance(data, (int, float)):
                    market_text += f"**{pair}**: {data}\n"

            if market_text:
                embed["fields"].append(
                    {
                        "name": "📈 Market Data",
                        "value": market_text[:1024],
                        "inline": True,
                    }
                )

        # テクニカル分析を追加
        if technical_analysis:
            embed["fields"].append(
                {
                    "name": "📊 Technical Analysis",
                    "value": technical_analysis[:1024],
                    "inline": False,
                }
            )

        # 推奨事項を追加
        if recommendations:
            embed["fields"].append(
                {
                    "name": "💡 Recommendations",
                    "value": recommendations[:1024],
                    "inline": False,
                }
            )

        # 信頼度スコアを追加
        if confidence_score is not None:
            confidence_emoji = (
                "🟢"
                if confidence_score >= 0.8
                else "🟡"
                if confidence_score >= 0.6
                else "🔴"
            )
            embed["fields"].append(
                {
                    "name": "🎯 Confidence Score",
                    "value": f"{confidence_emoji} {confidence_score:.2f} ({confidence_score*100:.1f}%)",
                    "inline": True,
                }
            )

        return embed

    def _create_alert_embed(
        self,
        alert_type: str,
        title: str,
        message: str,
        currency_pair: Optional[str] = None,
        current_rate: Optional[float] = None,
        threshold: Optional[float] = None,
        timestamp: datetime = None,
        color: int = 0x3498DB,
    ) -> Dict[str, Any]:
        """
        アラート用埋め込みを作成

        Args:
            alert_type: アラート種別
            title: タイトル
            message: メッセージ
            currency_pair: 通貨ペア
            current_rate: 現在レート
            threshold: 閾値
            timestamp: タイムスタンプ
            color: 色

        Returns:
            Dict[str, Any]: 埋め込みデータ
        """
        embed = {
            "title": title[:256],
            "description": message[:4096],
            "color": color,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "footer": {
                "text": "Alert System",
                "icon_url": "https://cdn.discordapp.com/embed/avatars/1.png",
            },
            "fields": [{"name": "🔖 Alert Type", "value": alert_type, "inline": True}],
        }

        # 通貨ペア情報を追加
        if currency_pair:
            embed["fields"].append(
                {"name": "💱 Currency Pair", "value": currency_pair, "inline": True}
            )

        # レート情報を追加
        if current_rate is not None:
            embed["fields"].append(
                {
                    "name": "📊 Current Rate",
                    "value": f"{current_rate:.6f}",
                    "inline": True,
                }
            )

        # 閾値情報を追加
        if threshold is not None:
            embed["fields"].append(
                {"name": "⚡ Threshold", "value": f"{threshold:.6f}", "inline": True}
            )

        return embed

    async def _send_with_file(
        self, payload: Dict[str, Any], file_data: bytes, filename: str
    ) -> Dict[str, Any]:
        """
        ファイル添付でメッセージを送信

        Args:
            payload: メッセージペイロード
            file_data: ファイルデータ
            filename: ファイル名

        Returns:
            Dict[str, Any]: レスポンス
        """
        # マルチパートフォームデータとして送信
        # 実装は複雑になるため、基本版では未実装
        # 必要に応じて aiohttp の FormData を使用
        raise NotImplementedError("File upload not yet implemented")

    async def test_connection(self) -> bool:
        """
        Discord Webhook接続をテスト

        Returns:
            bool: 接続成功時True
        """
        try:
            # 簡単なテストメッセージを送信
            test_embed = {
                "title": "Connection Test",
                "description": "Discord webhook connection test successful! ✅",
                "color": 0x00FF00,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self.send_message(
                content="🔧 Testing Discord webhook connection...",
                embeds=[test_embed],
                username="System Test",
            )

            logger.info("Discord webhook connection test successful")
            return True

        except Exception as e:
            logger.error(f"Discord webhook connection test failed: {str(e)}")
            return False

    def get_webhook_info(self) -> Dict[str, Any]:
        """
        Webhook情報を取得

        Returns:
            Dict[str, Any]: Webhook情報
        """
        return {
            "webhook_url": self.webhook_url,
            "default_username": self.default_username,
            "default_avatar_url": self.default_avatar_url,
            "rate_limit": {
                "calls": self.rate_limit_calls,
                "period": self.rate_limit_period,
            },
        }
