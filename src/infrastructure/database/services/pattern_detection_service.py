"""
パターン検出サービス

USD/JPY特化のデータベースベースパターン検出サービス
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.analysis.pattern_detectors import (
    BreakoutDetector,
    CompositeSignalDetector,
    DivergenceDetector,
    PullbackDetector,
    RSIBattleDetector,
    TrendReversalDetector,
)
from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)
from src.infrastructure.database.repositories.pattern_detection_repository_impl import (
    PatternDetectionRepositoryImpl,
)
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.infrastructure.database.services.timeframe_converter import TimeframeConverter
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PatternDetectionService:
    """
    パターン検出サービス

    責任:
    - データベースからのデータ取得
    - 既存パターン検出器との統合
    - 6パターン対応
    - 検出結果の保存

    特徴:
    - USD/JPY特化設計
    - データベースベース検出
    - 既存検出器との互換性
    - 高精度検出
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session

        # リポジトリ初期化
        self.pattern_repo = PatternDetectionRepositoryImpl(session)
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)
        self.price_repo = PriceDataRepositoryImpl(session)

        # 時間軸変換サービス初期化
        self.timeframe_converter = TimeframeConverter(
            self.price_repo, self.indicator_repo
        )

        # USD/JPY設定
        self.currency_pair = "USD/JPY"

        # パターン検出器初期化
        self.detectors = {
            1: TrendReversalDetector(),
            2: PullbackDetector(),
            3: DivergenceDetector(),
            4: BreakoutDetector(),
            5: RSIBattleDetector(),
            6: CompositeSignalDetector(),
        }

        # パターン設定
        self.pattern_configs = {
            1: {
                "name": "トレンド転換",
                "priority": 90,
                "color": "#FF6B6B",
                "description": "上位足でのトレンド転換シグナル",
            },
            2: {
                "name": "押し目・戻り売り",
                "priority": 80,
                "color": "#4ECDC4",
                "description": "トレンド継続中の押し目・戻り売り",
            },
            3: {
                "name": "ダイバージェンス",
                "priority": 85,
                "color": "#45B7D1",
                "description": "価格とRSIの逆行シグナル",
            },
            4: {
                "name": "ブレイクアウト",
                "priority": 75,
                "color": "#96CEB4",
                "description": "重要レベルのブレイクアウト",
            },
            5: {
                "name": "RSI50ライン攻防",
                "priority": 70,
                "color": "#FFEAA7",
                "description": "RSI50ラインでの攻防",
            },
            6: {
                "name": "複合シグナル",
                "priority": 95,
                "color": "#DDA0DD",
                "description": "複数時間軸での一致シグナル",
            },
        }

        logger.info(f"Initialized PatternDetectionService for {self.currency_pair}")

    async def detect_all_patterns(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[int, List[PatternDetectionModel]]:
        """
        全パターンを検出

        Args:
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            Dict[int, List[PatternDetectionModel]]: 検出されたパターンの辞書
        """
        try:
            logger.info(f"Starting pattern detection for {self.currency_pair}")

            # デフォルト期間設定
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(hours=24)  # 24時間分

            # データを取得
            price_data = await self._get_price_data(start_date, end_date)
            indicator_data = await self._get_indicator_data(start_date, end_date)

            if not price_data or not indicator_data:
                logger.warning("Insufficient data for pattern detection")
                return {}

            # 各パターンを検出
            results = {}
            for pattern_number, detector in self.detectors.items():
                try:
                    detected_patterns = await self._detect_single_pattern(
                        pattern_number, detector, price_data, indicator_data
                    )
                    results[pattern_number] = detected_patterns

                    logger.info(
                        f"Pattern {pattern_number} detection completed: "
                        f"{len(detected_patterns)} patterns found"
                    )

                except Exception as e:
                    logger.error(f"Error detecting pattern {pattern_number}: {e}")
                    results[pattern_number] = []

            total_patterns = sum(len(patterns) for patterns in results.values())
            logger.info(f"Pattern detection completed: {total_patterns} total patterns")

            return results

        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            return {}

    async def detect_single_pattern(
        self,
        pattern_number: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[PatternDetectionModel]:
        """
        単一パターンを検出

        Args:
            pattern_number: パターン番号（1-6）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 検出されたパターンリスト
        """
        try:
            if pattern_number not in self.detectors:
                raise ValueError(f"Invalid pattern number: {pattern_number}")

            logger.info(f"Detecting pattern {pattern_number} for {self.currency_pair}")

            # デフォルト期間設定
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(hours=24)

            # データを取得
            price_data = await self._get_price_data(start_date, end_date)
            indicator_data = await self._get_indicator_data(start_date, end_date)

            if not price_data or not indicator_data:
                logger.warning("Insufficient data for pattern detection")
                return []

            # パターンを検出
            detector = self.detectors[pattern_number]
            detected_patterns = await self._detect_single_pattern(
                pattern_number, detector, price_data, indicator_data
            )

            logger.info(
                f"Pattern {pattern_number} detection completed: "
                f"{len(detected_patterns)} patterns found"
            )

            return detected_patterns

        except Exception as e:
            logger.error(f"Error detecting pattern {pattern_number}: {e}")
            return []

    async def _detect_single_pattern(
        self,
        pattern_number: int,
        detector,
        price_data: List,
        indicator_data: Dict,
    ) -> List[PatternDetectionModel]:
        """
        単一パターンを検出（内部メソッド）

        Args:
            pattern_number: パターン番号
            detector: パターン検出器
            price_data: 価格データ
            indicator_data: 指標データ

        Returns:
            List[PatternDetectionModel]: 検出されたパターンリスト
        """
        try:
            # 検出器でパターンを検出（indicator_dataは既にマルチタイムフレーム形式）
            detection_result = detector.detect(indicator_data)

            if not detection_result:
                return []

            # パターンモデルを作成
            patterns = []
            config = self.pattern_configs[pattern_number]

            # 単一の結果を処理
            result = detection_result
            # conditions_metを安全に処理
            conditions_met = result.get("conditions_met", {})
            if not isinstance(conditions_met, dict):
                conditions_met = {}

            # technical_dataを安全に処理
            technical_data = result.get("technical_data", {})
            if not isinstance(technical_data, dict):
                technical_data = {}

            pattern = PatternDetectionModel(
                currency_pair=self.currency_pair,
                pattern_number=pattern_number,
                pattern_name=config["name"],
                priority=config["priority"],
                confidence_score=result.get("confidence", 0.8),
                detection_time=result.get("timestamp", datetime.now()),
                notification_title=result.get("title", config["name"]),
                notification_color=config["color"],
                strategy=result.get("strategy", ""),
                entry_condition=result.get("entry_condition", ""),
                take_profit=result.get("take_profit", ""),
                stop_loss=result.get("stop_loss", ""),
                description=config["description"],
                conditions_met=conditions_met,
                technical_data=technical_data,
            )

            if pattern.validate():
                patterns.append(pattern)

            # 重複チェックと保存
            saved_patterns = await self._save_patterns_with_duplicate_check(patterns)

            return saved_patterns

        except Exception as e:
            print(f"Error in single pattern detection: {e}")
            print(f"Detection result type: {type(detection_result)}")
            print(f"Detection result: {detection_result}")
            import traceback

            traceback.print_exc()
            return []

    async def _get_price_data(self, start_date: datetime, end_date: datetime) -> List:
        """
        価格データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            List: 価格データリスト
        """
        try:
            price_data = await self.price_repo.find_by_date_range(
                start_date, end_date, self.currency_pair, 1000
            )

            # 検出器用の形式に変換
            formatted_data = []
            for data in price_data:
                formatted_data.append(
                    {
                        "timestamp": data.timestamp,
                        "open": data.open_price,
                        "high": data.high_price,
                        "low": data.low_price,
                        "close": data.close_price,
                        "volume": data.volume or 0,
                    }
                )

            return formatted_data

        except Exception as e:
            logger.error(f"Error getting price data: {e}")
            return []

    async def _get_indicator_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        指標データを取得（パターン検出器用形式）

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            Dict: パターン検出器用の指標データ辞書
        """
        try:
            import pandas as pd

            # パターン検出器が期待する形式でデータを構築
            multi_timeframe_data = {}

            # 各タイムフレームのデータを取得
            timeframes = {"M5": "5m", "H1": "1h", "H4": "4h", "D1": "1d"}

            for detector_timeframe, db_timeframe in timeframes.items():
                # 価格データを取得（時間軸別）
                price_data = await self.price_repo.find_by_date_range_and_timeframe(
                    start_date, end_date, self.currency_pair, db_timeframe, 1000
                )

                # DataFrameに変換
                if price_data:
                    df_data = []
                    for data in price_data:
                        df_data.append(
                            {
                                "timestamp": data.timestamp,
                                "Open": (
                                    float(data.open_price) if data.open_price else 0.0
                                ),
                                "High": (
                                    float(data.high_price) if data.high_price else 0.0
                                ),
                                "Low": float(data.low_price) if data.low_price else 0.0,
                                "Close": (
                                    float(data.close_price) if data.close_price else 0.0
                                ),
                                "Volume": int(data.volume) if data.volume else 0,
                            }
                        )
                    price_df = pd.DataFrame(df_data)
                    price_df.set_index("timestamp", inplace=True)
                else:
                    price_df = pd.DataFrame()

                # 指標データを取得
                indicators = await self.indicator_repo.find_by_date_range(
                    start_date, end_date, None, db_timeframe, self.currency_pair, 1000
                )

                # 最新の指標値を取得
                indicator_dict = {}
                for indicator in indicators:
                    if indicator.indicator_type == "RSI":
                        # 最新のRSI値を取得
                        latest_rsi = await self.indicator_repo.find_latest_by_type(
                            "RSI", db_timeframe, limit=1
                        )
                        if latest_rsi:
                            indicator_dict["rsi"] = {
                                "current_value": float(latest_rsi[0].value)
                            }

                    elif indicator.indicator_type == "MACD":
                        # 最新のMACD値を取得
                        latest_macd = await self.indicator_repo.find_latest_by_type(
                            "MACD", db_timeframe, limit=1
                        )
                        if latest_macd:
                            additional_data = latest_macd[0].additional_data or {}
                            indicator_dict["macd"] = {
                                "macd": float(latest_macd[0].value),
                                "signal": additional_data.get("signal_line", 0.0),
                                "histogram": additional_data.get("histogram", 0.0),
                            }

                    elif indicator.indicator_type == "BB":
                        # 最新のボリンジャーバンド値を取得
                        latest_bb = await self.indicator_repo.find_latest_by_type(
                            "BB", db_timeframe, limit=1
                        )
                        if latest_bb:
                            additional_data = latest_bb[0].additional_data or {}
                            indicator_dict["bollinger_bands"] = {
                                "upper": additional_data.get("upper_band", 0.0),
                                "middle": float(latest_bb[0].value),
                                "lower": additional_data.get("lower_band", 0.0),
                            }

                # タイムフレームデータを構築
                multi_timeframe_data[detector_timeframe] = {
                    "price_data": price_df,
                    "indicators": indicator_dict,
                }

            return multi_timeframe_data

        except Exception as e:
            logger.error(f"Error getting indicator data: {e}")
            return {}

    async def _save_patterns_with_duplicate_check(
        self, patterns: List[PatternDetectionModel]
    ) -> List[PatternDetectionModel]:
        """
        重複チェック付きでパターンを保存

        Args:
            patterns: 保存するパターンリスト

        Returns:
            List[PatternDetectionModel]: 保存されたパターンリスト
        """
        try:
            saved_patterns = []

            for pattern in patterns:
                # 重複チェック（1時間以内の同じパターン）
                existing = await self.pattern_repo.find_recent_by_pattern(
                    pattern.pattern_number,
                    pattern.detection_time,
                    self.currency_pair,
                    hours=1,
                )

                if not existing:
                    saved_pattern = await self.pattern_repo.save(pattern)
                    saved_patterns.append(saved_pattern)

            return saved_patterns

        except Exception as e:
            logger.error(f"Error saving patterns: {e}")
            return []

    async def get_latest_patterns(
        self,
        pattern_number: Optional[int] = None,
        limit: int = 10,
    ) -> List[PatternDetectionModel]:
        """
        最新のパターンを取得

        Args:
            pattern_number: パターン番号（デフォルト: None）
            limit: 取得件数（デフォルト: 10）

        Returns:
            List[PatternDetectionModel]: 最新のパターンリスト
        """
        try:
            if pattern_number:
                return await self.pattern_repo.find_latest_by_pattern(
                    pattern_number, self.currency_pair, limit
                )
            else:
                return await self.pattern_repo.find_latest(self.currency_pair, limit)

        except Exception as e:
            logger.error(f"Error getting latest patterns: {e}")
            return []

    async def get_pattern_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        パターン統計を取得

        Args:
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            Dict: パターン統計
        """
        try:
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            stats = await self.pattern_repo.get_statistics(
                start_date, end_date, self.currency_pair
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}

    async def mark_notification_sent(
        self, pattern_id: int, discord_message_id: Optional[str] = None
    ):
        """
        通知送信済みをマーク

        Args:
            pattern_id: パターンID
            discord_message_id: DiscordメッセージID（デフォルト: None）
        """
        try:
            await self.pattern_repo.mark_notification_sent(
                pattern_id, discord_message_id
            )

        except Exception as e:
            logger.error(f"Error marking notification sent: {e}")
