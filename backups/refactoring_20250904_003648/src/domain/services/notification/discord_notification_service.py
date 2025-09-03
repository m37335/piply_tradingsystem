"""
Discord通知サービス

プロトレーダー向け為替アラートシステム用のDiscord通知サービス
設計書参照: /app/note/2025-01-15_アラートシステム_プロトレーダー向け為替アラートシステム設計書.md
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from src.infrastructure.database.models.entry_signal_model import EntrySignalModel
from src.infrastructure.database.models.risk_alert_model import RiskAlertModel


class DiscordNotificationService:
    """
    Discord通知サービス

    責任:
    - Discord Webhook経由での通知送信
    - メッセージフォーマット
    - エラーハンドリング
    - 通知履歴管理

    特徴:
    - リッチメッセージ対応
    - 複数チャンネル対応
    - レート制限対応
    - エラーリトライ機能
    """

    def __init__(self, webhook_url: str):
        """
        初期化

        Args:
            webhook_url: Discord Webhook URL
        """
        self.webhook_url = webhook_url
        self.session = None

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()

    async def send_entry_signal(self, signal: EntrySignalModel) -> bool:
        """
        エントリーシグナル通知を送信

        Args:
            signal: エントリーシグナル

        Returns:
            bool: 送信成功かどうか
        """
        try:
            message = self._format_entry_signal(signal)
            return await self._send_message(message)
        except Exception as e:
            print(f"Error sending entry signal notification: {e}")
            return False

    async def send_risk_alert(self, alert: RiskAlertModel) -> bool:
        """
        リスクアラート通知を送信

        Args:
            alert: リスクアラート

        Returns:
            bool: 送信成功かどうか
        """
        try:
            message = self._format_risk_alert(alert)
            return await self._send_message(message)
        except Exception as e:
            print(f"Error sending risk alert notification: {e}")
            return False

    async def send_daily_summary(self, date: datetime) -> bool:
        """
        日次サマリー通知を送信

        Args:
            date: 日付

        Returns:
            bool: 送信成功かどうか
        """
        try:
            message = self._format_daily_summary(date)
            return await self._send_message(message)
        except Exception as e:
            print(f"Error sending daily summary notification: {e}")
            return False

    def _format_entry_signal(self, signal: EntrySignalModel) -> Dict[str, Any]:
        """
        エントリーシグナルをDiscord用にフォーマット

        Args:
            signal: エントリーシグナル

        Returns:
            Dict[str, Any]: Discordメッセージ
        """
        emoji_map = {"BUY": "🟢", "SELL": "🔴"}

        signal_emoji = emoji_map.get(signal.signal_type, "⚪")

        # リスク/リワード情報
        try:
            risk_percentage = signal.calculate_risk_percentage()
        except AttributeError:
            risk_percentage = 0.0
            
        try:
            profit_percentage = signal.calculate_profit_percentage()
        except AttributeError:
            profit_percentage = 0.0

        # 指標情報
        indicators_text = self._format_indicators(signal.indicators_used)

        embed = {
            "title": f"{signal_emoji} USD/JPY {signal.signal_type}エントリーシグナル",
            "color": 0x00FF00 if signal.signal_type == "BUY" else 0xFF0000,
            "fields": [
                {
                    "name": "💰 価格情報",
                    "value": (
                        f"• エントリー: {signal.entry_price or 0:.3f}\n"
                        f"• ストップロス: {signal.stop_loss or 0:.3f} ({risk_percentage:.2f}%)\n"
                        f"• 利益確定: {signal.take_profit or 0:.3f} ({profit_percentage:.2f}%)"
                    ),
                    "inline": False,
                },
                {
                    "name": "⚖️ リスク管理",
                    "value": (
                        f"• リスク/リワード比: {signal.risk_reward_ratio or 0}:1\n"
                        f"• 信頼度: {signal.confidence_score or 0}%\n"
                        f"• 推奨ポジションサイズ: {signal.position_size or 0:.2f}%"
                    ),
                    "inline": True,
                },
                {"name": "📊 指標状況", "value": indicators_text, "inline": True},
                {
                    "name": "⚠️ 注意事項",
                    "value": (
                        f"• 有効期限: 30分\n"
                        f"• 市場状況: {self._get_market_condition_text(signal.market_conditions)}\n"
                        f"• 推奨アクション: {self._get_recommended_action(signal)}"
                    ),
                    "inline": False,
                },
            ],
            "footer": {
                "text": f"生成時刻: {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S JST')}"
            },
            "timestamp": signal.timestamp.isoformat(),
        }

        return {"embeds": [embed]}

    def _format_risk_alert(self, alert: RiskAlertModel) -> Dict[str, Any]:
        """
        リスクアラートをDiscord用にフォーマット

        Args:
            alert: リスクアラート

        Returns:
            Dict[str, Any]: Discordメッセージ
        """
        severity_emoji = {"LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴", "CRITICAL": "🚨"}

        emoji = severity_emoji.get(alert.severity, "⚪")

        # 市場データ情報
        market_data_text = self._format_market_data(alert.market_data)

        embed = {
            "title": f"{emoji} リスクアラート: {alert.alert_type.replace('_', ' ').title()}",
            "color": self._get_severity_color(alert.severity),
            "fields": [
                {"name": "📋 アラート内容", "value": alert.message, "inline": False},
                {
                    "name": "🎯 推奨アクション",
                    "value": alert.recommended_action or "特になし",
                    "inline": False,
                },
                {"name": "📊 詳細データ", "value": market_data_text, "inline": False},
            ],
            "footer": {
                "text": f"重要度: {alert.severity} | 検出時刻: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S JST')}"
            },
            "timestamp": alert.timestamp.isoformat(),
        }

        return {"embeds": [embed]}

    def _format_daily_summary(self, date: datetime) -> Dict[str, Any]:
        """
        日次サマリーをDiscord用にフォーマット

        Args:
            date: 日付

        Returns:
            Dict[str, Any]: Discordメッセージ
        """
        # 日次統計を取得（簡易実装）
        stats = self._get_daily_statistics(date)

        embed = {
            "title": f"📈 USD/JPY トレーディングサマリー - {date.strftime('%Y-%m-%d')}",
            "color": 0x0099FF,
            "fields": [
                {
                    "name": "📊 シグナル統計",
                    "value": (
                        f"• 生成シグナル数: {stats['total_signals']}\n"
                        f"• 実行シグナル数: {stats['executed_signals']}\n"
                        f"• 成功率: {stats['success_rate']:.1f}%\n"
                        f"• 平均損益: {stats['avg_pnl']:.2f}%"
                    ),
                    "inline": True,
                },
                {
                    "name": "🚨 リスクアラート",
                    "value": (
                        f"• 高重要度アラート: {stats['high_risk_alerts']}\n"
                        f"• 中重要度アラート: {stats['medium_risk_alerts']}\n"
                        f"• 低重要度アラート: {stats['low_risk_alerts']}"
                    ),
                    "inline": True,
                },
                {
                    "name": "📈 パフォーマンス分析",
                    "value": (
                        f"• 最良シグナル: {stats['best_signal']}\n"
                        f"• 最悪シグナル: {stats['worst_signal']}\n"
                        f"• 平均保有時間: {stats['avg_duration']}分"
                    ),
                    "inline": False,
                },
                {
                    "name": "🔮 明日の予測",
                    "value": stats["tomorrow_prediction"],
                    "inline": False,
                },
            ],
            "footer": {"text": "プロトレーダー向け為替アラートシステム"},
            "timestamp": date.isoformat(),
        }

        return {"embeds": [embed]}

    def _format_indicators(self, indicators: Dict[str, Any]) -> str:
        """
        指標情報をフォーマット

        Args:
            indicators: 指標データ

        Returns:
            str: フォーマット済み指標テキスト
        """
        if not indicators:
            return "データなし"

        formatted = []
        for name, value in indicators.items():
            if isinstance(value, float):
                formatted.append(f"• {name}: {value:.3f}")
            else:
                formatted.append(f"• {name}: {value}")

        return "\n".join(formatted[:5])  # 最大5個まで表示

    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """
        市場データをフォーマット

        Args:
            market_data: 市場データ

        Returns:
            str: フォーマット済み市場データテキスト
        """
        if not market_data:
            return "データなし"

        formatted = []
        for key, value in market_data.items():
            if isinstance(value, float):
                formatted.append(f"• {key}: {value:.5f}")
            else:
                formatted.append(f"• {key}: {value}")

        return "\n".join(formatted[:5])  # 最大5個まで表示

    def _get_market_condition_text(self, market_conditions: Dict[str, Any]) -> str:
        """
        市場状況テキストを取得

        Args:
            market_conditions: 市場状況

        Returns:
            str: 市場状況テキスト
        """
        if not market_conditions:
            return "不明"

        trend = market_conditions.get("trend", "不明")
        volatility = market_conditions.get("volatility", "不明")
        momentum = market_conditions.get("momentum", "不明")

        return f"{trend} | {volatility} | {momentum}"

    def _get_recommended_action(self, signal: EntrySignalModel) -> str:
        """
        推奨アクションを取得

        Args:
            signal: エントリーシグナル

        Returns:
            str: 推奨アクション
        """
        if signal.confidence_score >= 80:
            return "即座にエントリー推奨"
        elif signal.confidence_score >= 60:
            return "確認後にエントリー"
        else:
            return "様子見推奨"

    def _get_severity_color(self, severity: str) -> int:
        """
        重要度に応じた色を取得

        Args:
            severity: 重要度

        Returns:
            int: 色コード
        """
        color_map = {
            "LOW": 0xFFFF00,  # 黄色
            "MEDIUM": 0xFFA500,  # オレンジ
            "HIGH": 0xFF0000,  # 赤
            "CRITICAL": 0x800000,  # 濃い赤
        }
        return color_map.get(severity, 0x808080)  # デフォルトはグレー

    def _get_daily_statistics(self, date: datetime) -> Dict[str, Any]:
        """
        日次統計を取得（簡易実装）

        Args:
            date: 日付

        Returns:
            Dict[str, Any]: 日次統計
        """
        # 実際の実装ではデータベースから取得
        return {
            "total_signals": 15,
            "executed_signals": 8,
            "success_rate": 75.0,
            "avg_pnl": 1.2,
            "high_risk_alerts": 2,
            "medium_risk_alerts": 5,
            "low_risk_alerts": 3,
            "best_signal": "+2.5% (RSI買い)",
            "worst_signal": "-0.8% (BB売り)",
            "avg_duration": 45,
            "tomorrow_prediction": "ボラティリティ上昇予想、慎重なポジション管理を推奨",
        }

    async def _send_message(self, message: Dict[str, Any]) -> bool:
        """
        メッセージを送信

        Args:
            message: 送信メッセージ

        Returns:
            bool: 送信成功かどうか
        """
        if not self.session:
            return False

        try:
            async with self.session.post(
                self.webhook_url, json=message, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                return response.status == 204

        except asyncio.TimeoutError:
            print("Discord notification timeout")
            return False
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
            return False

    async def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功かどうか
        """
        test_message = {
            "content": "🔧 プロトレーダー向け為替アラートシステム - 接続テスト成功"
        }
        return await self._send_message(test_message)
