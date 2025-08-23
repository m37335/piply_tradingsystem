"""
Discord埋め込みメッセージビルダー
Discord用の埋め込みメッセージを作成
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytz


class DiscordEmbedBuilder:
    """Discord埋め込みメッセージビルダー"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 色の定義
        self.colors = {
            "success": 0x00FF00,  # 緑
            "warning": 0xFFA500,  # オレンジ
            "error": 0xFF0000,  # 赤
            "info": 0x0099FF,  # 青
            "high_importance": 0xFF0000,  # 赤
            "medium_importance": 0xFFA500,  # オレンジ
            "low_importance": 0x00FF00,  # 緑
        }

        # 国名の日本語マッピング
        self.country_names = {
            "japan": "日本",
            "united states": "アメリカ",
            "euro zone": "ユーロ圏",
            "united kingdom": "イギリス",
            "china": "中国",
            "australia": "オーストラリア",
            "canada": "カナダ",
            "switzerland": "スイス",
            "new zealand": "ニュージーランド",
            "germany": "ドイツ",
            "france": "フランス",
            "italy": "イタリア",
            "spain": "スペイン",
            "netherlands": "オランダ",
            "belgium": "ベルギー",
            "austria": "オーストリア",
            "ireland": "アイルランド",
            "finland": "フィンランド",
            "portugal": "ポルトガル",
            "greece": "ギリシャ",
            "slovenia": "スロベニア",
            "cyprus": "キプロス",
            "malta": "マルタ",
            "slovakia": "スロバキア",
            "estonia": "エストニア",
            "latvia": "ラトビア",
            "lithuania": "リトアニア",
            "luxembourg": "ルクセンブルク",
        }

        # 経済指標名の日本語マッピング
        self.indicator_names = {
            "Consumer Price Index (CPI) y/y": "消費者物価指数（前年比）",
            "Core Consumer Price Index (CPI) y/y": "コア消費者物価指数（前年比）",
            "Gross Domestic Product (GDP) q/q": "国内総生産（前期比）",
            "Gross Domestic Product (GDP) y/y": "国内総生産（前年比）",
            "Unemployment Rate": "失業率",
            "Non-Farm Payrolls": "非農業部門雇用者数",
            "Average Hourly Earnings m/m": "平均時給（前月比）",
            "Average Hourly Earnings y/y": "平均時給（前年比）",
            "Retail Sales m/m": "小売売上高（前月比）",
            "Retail Sales y/y": "小売売上高（前年比）",
            "Industrial Production m/m": "鉱工業生産指数（前月比）",
            "Industrial Production y/y": "鉱工業生産指数（前年比）",
            "Manufacturing PMI": "製造業PMI",
            "Services PMI": "サービス業PMI",
            "Composite PMI": "総合PMI",
            "Interest Rate Decision": "政策金利決定",
            "Federal Funds Rate": "FF金利",
            "ECB Interest Rate Decision": "ECB政策金利決定",
            "Bank of Japan Interest Rate Decision": "日銀政策金利決定",
            "Trade Balance": "貿易収支",
            "Current Account": "経常収支",
            "Business Confidence": "企業信頼感指数",
            "Consumer Confidence": "消費者信頼感指数",
            "Housing Starts": "住宅着工件数",
            "Building Permits": "建築許可件数",
            "Existing Home Sales": "中古住宅販売件数",
            "New Home Sales": "新築住宅販売件数",
            "Durable Goods Orders m/m": "耐久財受注（前月比）",
            "Core Durable Goods Orders m/m": "コア耐久財受注（前月比）",
            "ISM Manufacturing PMI": "ISM製造業PMI",
            "ISM Services PMI": "ISMサービス業PMI",
            "Philadelphia Fed Manufacturing Index": "フィラデルフィア連銀製造業指数",
            "Richmond Fed Manufacturing Index": "リッチモンド連銀製造業指数",
            "Dallas Fed Manufacturing Index": "ダラス連銀製造業指数",
            "Kansas City Fed Manufacturing Index": "カンザスシティ連銀製造業指数",
            "Chicago PMI": "シカゴPMI",
            "New York Empire State Manufacturing Index": "NY連銀製造業指数",
            "Michigan Consumer Sentiment": "ミシガン大学消費者信頼感指数",
            "Conference Board Consumer Confidence": "カンファレンスボード消費者信頼感指数",
            "JOLTs Job Openings": "JOLTS求人件数",
            "ADP Non-Farm Employment Change": "ADP雇用統計",
            "Initial Jobless Claims": "新規失業保険申請件数",
            "Continuing Jobless Claims": "継続失業保険申請件数",
            "Personal Income m/m": "個人所得（前月比）",
            "Personal Spending m/m": "個人支出（前月比）",
            "Core PCE Price Index m/m": "コアPCE物価指数（前月比）",
            "Core PCE Price Index y/y": "コアPCE物価指数（前年比）",
            "PCE Price Index m/m": "PCE物価指数（前月比）",
            "PCE Price Index y/y": "PCE物価指数（前年比）",
            "Employment Cost Index q/q": "雇用コスト指数（前期比）",
            "Unit Labor Costs q/q": "単位労働コスト（前期比）",
            "Productivity q/q": "労働生産性（前期比）",
            "Factory Orders m/m": "製造業受注（前月比）",
            "Wholesale Inventories m/m": "卸売在庫（前月比）",
            "Business Inventories m/m": "企業在庫（前月比）",
            "Capacity Utilization Rate": "設備稼働率",
            "NAHB Housing Market Index": "NAHB住宅市場指数",
            "S&P/Case-Shiller Home Price Indices y/y": "ケース・シラー住宅価格指数（前年比）",
            "FHFA House Price Index m/m": "FHFA住宅価格指数（前月比）",
            "Pending Home Sales m/m": "住宅販売契約件数（前月比）",
            "Construction Spending m/m": "建設支出（前月比）",
            "ISM Manufacturing Prices": "ISM製造業物価指数",
            "ISM Services Prices": "ISMサービス業物価指数",
            "Import Prices m/m": "輸入物価（前月比）",
            "Export Prices m/m": "輸出物価（前月比）",
            "PPI m/m": "生産者物価指数（前月比）",
            "PPI y/y": "生産者物価指数（前年比）",
            "Core PPI m/m": "コア生産者物価指数（前月比）",
            "Core PPI y/y": "コア生産者物価指数（前年比）",
            "CPI m/m": "消費者物価指数（前月比）",
            "CPI y/y": "消費者物価指数（前年比）",
            "Core CPI m/m": "コア消費者物価指数（前月比）",
            "Core CPI y/y": "コア消費者物価指数（前年比）",
        }

    def create_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00FF00,
        fields: Optional[List[Dict[str, Any]]] = None,
        footer: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
        url: Optional[str] = None,
        thumbnail: Optional[Dict[str, str]] = None,
        image: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        基本的な埋め込みメッセージを作成

        Args:
            title: タイトル
            description: 説明
            color: 色（16進数）
            fields: フィールドのリスト
            footer: フッター情報
            timestamp: タイムスタンプ
            url: URL
            thumbnail: サムネイル
            image: 画像

        Returns:
            Dict[str, Any]: Discord埋め込みメッセージ
        """
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": timestamp.isoformat() if timestamp else None,
        }

        if url:
            embed["url"] = url

        if fields:
            embed["fields"] = fields

        if footer:
            embed["footer"] = footer

        if thumbnail:
            embed["thumbnail"] = thumbnail

        if image:
            embed["image"] = image

        return embed

    def _format_datetime_jst(self, date_str: str) -> str:
        """日時をJST形式でフォーマット"""
        try:
            if isinstance(date_str, str):
                # UTC時刻をJSTに変換
                utc_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                jst_tz = pytz.timezone("Asia/Tokyo")
                jst_dt = utc_dt.astimezone(jst_tz)
                return jst_dt.strftime("%Y年%m月%d日 %H:%M JST")
            elif isinstance(date_str, datetime):
                # 既にdatetimeオブジェクトの場合
                jst_tz = pytz.timezone("Asia/Tokyo")
                jst_dt = date_str.astimezone(jst_tz)
                return jst_dt.strftime("%Y年%m月%d日 %H:%M JST")
        except Exception as e:
            self.logger.warning(f"Failed to format datetime: {e}")
            return str(date_str)

        return str(date_str)

    def _get_japanese_country_name(self, country: str) -> str:
        """国名を日本語に変換"""
        return self.country_names.get(country.lower(), country)

    def _get_japanese_indicator_name(self, indicator: str) -> str:
        """経済指標名を日本語に変換"""
        return self.indicator_names.get(indicator, indicator)

    def create_economic_event_embed(
        self, event_data: Dict[str, Any], notification_type: str = "new_event"
    ) -> Dict[str, Any]:
        """
        経済イベント用の埋め込みメッセージを作成（日本語版）

        Args:
            event_data: イベントデータ
            notification_type: 通知タイプ

        Returns:
            Dict[str, Any]: Discord埋め込みメッセージ
        """
        # 重要度に応じた色を決定
        importance = event_data.get("importance", "medium")
        color = self.colors.get(f"{importance}_importance", self.colors["info"])

        # 通知タイプに応じたタイトルとアイコン
        type_icons = {
            "new_event": "📅",
            "forecast_change": "📊",
            "actual_announcement": "📈",
            "surprise_alert": "⚠️",
        }

        icon = type_icons.get(notification_type, "📅")

        # 経済指標名を日本語化
        event_name = event_data.get("event_name", "Economic Event")
        japanese_event_name = self._get_japanese_indicator_name(event_name)
        title = f"{icon} {japanese_event_name}"

        # 国名を日本語化
        country = self._get_japanese_country_name(event_data.get("country", "Unknown"))

        # 発表時刻を明確に表示
        date_str = event_data.get("date_utc", "")
        announcement_time = self._format_datetime_jst(date_str)

        description = f"**{country}**\n📅 **発表時刻**: {announcement_time}"

        # フィールドの作成
        fields = []

        # 重要度
        importance_text = {"high": "高", "medium": "中", "low": "低"}.get(
            importance, importance
        )

        fields.append(
            {"name": "重要度", "value": f"`{importance_text}`", "inline": True}
        )

        # 予測値
        forecast = event_data.get("forecast_value")
        if forecast is not None:
            fields.append({"name": "予測値", "value": f"`{forecast}`", "inline": True})

        # 前回値
        previous = event_data.get("previous_value")
        if previous is not None:
            fields.append({"name": "前回値", "value": f"`{previous}`", "inline": True})

        # 実際値（発表済みの場合）
        actual = event_data.get("actual_value")
        if actual is not None:
            fields.append({"name": "実際値", "value": f"`{actual}`", "inline": True})

        # 通貨・単位
        currency = event_data.get("currency")
        unit = event_data.get("unit")
        if currency or unit:
            if currency and unit:
                unit_str = f"{currency} {unit}".strip()
            else:
                unit_str = currency or unit
            fields.append({"name": "単位", "value": f"`{unit_str}`", "inline": True})

        # カテゴリ
        category = event_data.get("category")
        if category:
            fields.append(
                {"name": "カテゴリ", "value": f"`{category}`", "inline": True}
            )

        # サプライズ計算（実際値と予測値がある場合）
        if actual is not None and forecast is not None:
            try:
                actual_val = float(actual)
                forecast_val = float(forecast)
                if forecast_val != 0:
                    surprise = ((actual_val - forecast_val) / abs(forecast_val)) * 100
                    surprise_icon = "📈" if surprise > 0 else "📉"
                    surprise_text = "予想上回り" if surprise > 0 else "予想下回り"
                    fields.append(
                        {
                            "name": "サプライズ",
                            "value": f"{surprise_icon} `{surprise:+.2f}%` ({surprise_text})",
                            "inline": True,
                        }
                    )
            except (ValueError, ZeroDivisionError):
                pass

        # フッター
        footer = {
            "text": f"経済カレンダーシステム • {notification_type.replace('_', ' ').title()}"
        }

        return self.create_embed(
            title=title,
            description=description,
            color=color,
            fields=fields,
            footer=footer,
            timestamp=datetime.utcnow(),
        )

    def create_ai_report_embed(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AIレポート用の埋め込みメッセージを作成（レポート形式）

        Args:
            report_data: レポートデータ

        Returns:
            Dict[str, Any]: Discord埋め込みメッセージ
        """
        title = "🤖 AI分析レポート"

        # イベント情報
        event_name = report_data.get("event_name", "Unknown Event")
        japanese_event_name = self._get_japanese_indicator_name(event_name)
        country = self._get_japanese_country_name(report_data.get("country", "Unknown"))

        # 発表時刻
        date_str = report_data.get("date_utc", "")
        announcement_time = self._format_datetime_jst(date_str)

        description = f"**{japanese_event_name}** ({country})\n📅 **発表時刻**: {announcement_time}"

        # 信頼度スコアに応じた色
        confidence = report_data.get("confidence_score", 0.5)
        if confidence >= 0.8:
            color = self.colors["success"]
        elif confidence >= 0.6:
            color = self.colors["warning"]
        else:
            color = self.colors["error"]

        fields = []

        # レポートタイプ
        report_type = report_data.get("report_type", "unknown")
        type_display = {
            "pre_event": "事前分析",
            "post_event": "事後分析",
            "forecast_change": "予測変更分析",
        }.get(report_type, report_type)

        fields.append(
            {"name": "分析タイプ", "value": f"`{type_display}`", "inline": True}
        )

        # 信頼度スコア
        confidence_percent = confidence * 100
        confidence_text = (
            "高" if confidence >= 0.8 else "中" if confidence >= 0.6 else "低"
        )
        fields.append(
            {
                "name": "信頼度",
                "value": f"`{confidence_percent:.1f}%` ({confidence_text})",
                "inline": True,
            }
        )

        # USD/JPY予測
        prediction = report_data.get("usd_jpy_prediction", {})
        if prediction:
            direction = prediction.get("direction", "unknown")
            strength = prediction.get("strength", "unknown")
            target_price = prediction.get("target_price")
            timeframe = prediction.get("timeframe", "")

            direction_icon = "📈" if direction == "bullish" else "📉"
            direction_text = "上昇" if direction == "bullish" else "下降"
            strength_text = {"strong": "強い", "medium": "中程度", "weak": "弱い"}.get(
                strength, strength
            )

            prediction_text = f"{direction_icon} **{direction_text}** ({strength_text})"
            if target_price:
                prediction_text += f"\n🎯 **目標価格**: `{target_price}`"
            if timeframe:
                prediction_text += f"\n⏰ **期間**: {timeframe}"

            fields.append(
                {"name": "USD/JPY予測", "value": prediction_text, "inline": False}
            )

        # 分析理由
        reasons = prediction.get("reasons", [])
        if reasons:
            reasons_text = "\n".join(
                [f"• {reason}" for reason in reasons[:5]]
            )  # 最大5個まで
            if len(reasons) > 5:
                reasons_text += f"\n• ... 他{len(reasons) - 5}個"

            fields.append({"name": "分析理由", "value": reasons_text, "inline": False})

        # レポート内容
        report_content = report_data.get("report_content", "")
        if report_content and len(report_content) > 0:
            # レポート内容が長すぎる場合は切り詰める
            if len(report_content) > 1024:
                report_content = report_content[:1021] + "..."

            fields.append(
                {"name": "詳細分析", "value": report_content, "inline": False}
            )

        # フッター
        footer = {"text": "AI分析システム • Powered by GPT-4"}

        return self.create_embed(
            title=title,
            description=description,
            color=color,
            fields=fields,
            footer=footer,
            timestamp=datetime.utcnow(),
        )

    def create_error_embed(
        self,
        error_message: str,
        error_type: str = "general",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        エラー通知用の埋め込みメッセージを作成

        Args:
            error_message: エラーメッセージ
            error_type: エラータイプ
            context: エラーコンテキスト

        Returns:
            Dict[str, Any]: Discord埋め込みメッセージ
        """
        title = "⚠️ システムエラー"

        # エラータイプに応じた説明
        type_descriptions = {
            "database": "データベースエラー",
            "api": "API接続エラー",
            "network": "ネットワークエラー",
            "validation": "データ検証エラー",
            "general": "一般エラー",
        }

        description = type_descriptions.get(error_type, "システムエラーが発生しました")

        fields = []

        # エラーメッセージ
        if len(error_message) > 1024:
            error_message = error_message[:1021] + "..."

        fields.append(
            {"name": "エラー詳細", "value": f"```{error_message}```", "inline": False}
        )

        # コンテキスト情報
        if context:
            context_str = "\n".join([f"• {k}: {v}" for k, v in context.items()])
            if len(context_str) > 1024:
                context_str = context_str[:1021] + "..."

            fields.append(
                {"name": "コンテキスト", "value": context_str, "inline": False}
            )

        # フッター
        footer = {"text": "System Monitor • Error Alert"}

        return self.create_embed(
            title=title,
            description=description,
            color=self.colors["error"],
            fields=fields,
            footer=footer,
            timestamp=datetime.utcnow(),
        )

    def create_system_status_embed(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        システムステータス用の埋め込みメッセージを作成

        Args:
            status_data: ステータスデータ

        Returns:
            Dict[str, Any]: Discord埋め込みメッセージ
        """
        title = "🔧 システムステータス"
        description = "システムの現在の状態"

        fields = []

        # 各コンポーネントのステータス
        for component, status in status_data.items():
            if isinstance(status, bool):
                status_icon = "✅" if status else "❌"
                status_text = "正常" if status else "異常"
            else:
                status_icon = "ℹ️"
                status_text = str(status)

            fields.append(
                {
                    "name": component.replace("_", " ").title(),
                    "value": f"{status_icon} {status_text}",
                    "inline": True,
                }
            )

        # フッター
        footer = {"text": "System Monitor • Status Report"}

        return self.create_embed(
            title=title,
            description=description,
            color=self.colors["info"],
            fields=fields,
            footer=footer,
            timestamp=datetime.utcnow(),
        )
