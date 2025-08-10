"""
効率的パターン検出サービス

5分足ベース + 日足のみ取得のアプローチ
API呼び出し数を最小限に抑えつつ、精度を保つ
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
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
from src.infrastructure.database.services.multi_timeframe_technical_indicator_service import (
    MultiTimeframeTechnicalIndicatorService,
)
from src.infrastructure.database.services.timeframe_data_service import (
    TimeframeDataService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class EfficientPatternDetectionService:
    """
    効率的パターン検出サービス

    特徴:
    - 5分足データを基本として取得
    - 日足データのみを別途取得（トレンド判断用）
    - H1, H4は5分足から集計
    - API呼び出し数を最小限に抑制
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

        # 時間軸データサービス初期化
        self.timeframe_service = TimeframeDataService(session)

        # マルチタイムフレームテクニカル指標サービス初期化
        self.technical_indicator_service = MultiTimeframeTechnicalIndicatorService(
            session
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
                "description": "価格と指標の乖離シグナル",
            },
            4: {
                "name": "ブレイクアウト",
                "priority": 75,
                "color": "#96CEB4",
                "description": "重要なレベル突破シグナル",
            },
            5: {
                "name": "RSIバトル",
                "priority": 70,
                "color": "#FFEAA7",
                "description": "RSI過買い・過売りゾーンでの戦い",
            },
            6: {
                "name": "複合シグナル",
                "priority": 95,
                "color": "#DDA0DD",
                "description": "複数の指標が一致する強力シグナル",
            },
        }

        logger.info(
            f"Initialized EfficientPatternDetectionService for {self.currency_pair}"
        )

    async def detect_all_patterns(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[int, List[PatternDetectionModel]]:
        """
        全パターンを検出

        Args:
            start_date: 開始日時（デフォルト: 過去24時間）
            end_date: 終了日時（デフォルト: 現在時刻）

        Returns:
            Dict[int, List[PatternDetectionModel]]: パターン番号別の検出結果
        """
        try:
            # デフォルト日時の設定
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(hours=24)

            logger.info(f"Detecting all patterns from {start_date} to {end_date}")

            # 効率的なマルチタイムフレームデータを構築
            multi_timeframe_data = await self._build_efficient_multi_timeframe_data(
                start_date, end_date
            )

            if not multi_timeframe_data:
                logger.warning(
                    "No multi-timeframe data available for pattern detection"
                )
                return {}

            # 各パターンを検出
            results = {}
            for pattern_number, detector in self.detectors.items():
                try:
                    patterns = await self._detect_single_pattern(
                        pattern_number, detector, multi_timeframe_data
                    )
                    if patterns:
                        results[pattern_number] = patterns
                        logger.info(
                            f"Detected {len(patterns)} patterns for pattern {pattern_number}"
                        )

                except Exception as e:
                    logger.error(f"Error detecting pattern {pattern_number}: {e}")
                    # デバッグ情報を追加
                    logger.debug(f"Pattern {pattern_number} detector: {detector}")
                    logger.debug(
                        f"Multi-timeframe data keys: {list(multi_timeframe_data.keys())}"
                    )
                    for timeframe, data in multi_timeframe_data.items():
                        logger.debug(
                            f"{timeframe} data: price_data={len(data.get('price_data', pd.DataFrame()))}, indicators={list(data.get('indicators', {}).keys())}"
                        )

            logger.info(
                f"Pattern detection completed. Found patterns: {list(results.keys())}"
            )
            return results

        except Exception as e:
            logger.error(f"Error in detect_all_patterns: {e}")
            return {}

    async def _build_efficient_multi_timeframe_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        効率的なマルチタイムフレームデータを構築

        アプローチ:
        - 時間軸データサービスを使用してマルチタイムフレームデータを取得
        - マルチタイムフレームテクニカル指標サービスを使用して指標を取得
        """
        try:
            # 時間軸データサービスを使用してマルチタイムフレームデータを取得
            multi_timeframe_data = (
                await self.timeframe_service.get_multi_timeframe_data(
                    start_date, end_date
                )
            )

            if not multi_timeframe_data or len(multi_timeframe_data) == 0:
                logger.warning("No multi-timeframe data available")
                return {}

            # 各時間軸の指標データを取得
            m5_indicators = await self.technical_indicator_service.get_latest_indicators_by_timeframe(
                "5m"
            )
            h1_indicators = await self.technical_indicator_service.get_latest_indicators_by_timeframe(
                "1h"
            )
            h4_indicators = await self.technical_indicator_service.get_latest_indicators_by_timeframe(
                "4h"
            )
            d1_indicators = await self.technical_indicator_service.get_latest_indicators_by_timeframe(
                "1d"
            )

            # 指標キーを統一し、パターン検出器が期待する形式に変換
            def normalize_indicators(indicators):
                if not indicators:
                    return {}
                normalized = {}

                # RSI: パターン検出器が期待する形式に変換
                if "rsi" in indicators:
                    rsi_value = indicators["rsi"]["value"]
                    # パターン検出器はcurrent_valueを期待
                    normalized["rsi"] = {"current_value": rsi_value}
                    # 同時にpandas Seriesも提供（他の用途のため）
                    normalized["rsi_series"] = pd.Series([rsi_value] * 20)

                # MACD: パターン検出器が期待する形式に変換
                if "macd" in indicators:
                    macd_value = indicators["macd"]["value"]
                    # additional_dataからsignalとhistogramを取得
                    additional_data = indicators["macd"].get("additional_data", {})
                    signal_value = additional_data.get("signal", [0.0] * 20)[0] if additional_data.get("signal") else 0.0
                    histogram_value = additional_data.get("histogram", [0.0] * 20)[0] if additional_data.get("histogram") else 0.0
                    # パターン検出器はpandas Seriesを期待
                    normalized["macd"] = {
                        "macd": pd.Series([macd_value] * 20),
                        "signal": pd.Series([signal_value] * 20),
                        "histogram": pd.Series([histogram_value] * 20),
                    }

                # ボリンジャーバンド: パターン検出器が期待する形式に変換
                if "bb" in indicators:
                    bb_value = indicators["bb"]["value"]
                    # additional_dataからupper、middle、lowerを取得
                    additional_data = indicators["bb"].get("additional_data", {})
                    upper_value = additional_data.get("upper", [0.0] * 20)[0] if additional_data.get("upper") else bb_value + 1.0
                    middle_value = additional_data.get("middle", [0.0] * 20)[0] if additional_data.get("middle") else bb_value
                    lower_value = additional_data.get("lower", [0.0] * 20)[0] if additional_data.get("lower") else bb_value - 1.0
                    # パターン検出器はpandas Seriesを期待
                    normalized["bollinger_bands"] = {
                        "upper": pd.Series([upper_value] * 20),
                        "middle": pd.Series([middle_value] * 20),
                        "lower": pd.Series([lower_value] * 20),
                    }

                return normalized

            m5_indicators = normalize_indicators(m5_indicators)
            h1_indicators = normalize_indicators(h1_indicators)
            h4_indicators = normalize_indicators(h4_indicators)
            d1_indicators = normalize_indicators(d1_indicators)

            # マルチタイムフレームデータを構築
            result_data = {}

            # 5分足データ
            if "5m" in multi_timeframe_data:
                m5_df = multi_timeframe_data["5m"]["price_data"]
                if not m5_df.empty:
                    result_data["M5"] = {
                        "price_data": m5_df,
                        "indicators": m5_indicators,
                    }

            # 1時間足データ
            if "1h" in multi_timeframe_data:
                h1_df = multi_timeframe_data["1h"]["price_data"]
                if not h1_df.empty:
                    result_data["H1"] = {
                        "price_data": h1_df,
                        "indicators": h1_indicators,
                    }

            # 4時間足データ
            if "4h" in multi_timeframe_data:
                h4_df = multi_timeframe_data["4h"]["price_data"]
                if not h4_df.empty:
                    result_data["H4"] = {
                        "price_data": h4_df,
                        "indicators": h4_indicators,
                    }

            # 日足データ
            if "1d" in multi_timeframe_data:
                d1_df = multi_timeframe_data["1d"]["price_data"]
                if not d1_df.empty:
                    result_data["D1"] = {
                        "price_data": d1_df,
                        "indicators": d1_indicators,
                    }

            logger.info(
                f"Built efficient multi-timeframe data with {len(result_data)} timeframes"
            )
            return result_data

        except Exception as e:
            logger.error(f"Error building efficient multi-timeframe data: {e}")
            return {}

    def _convert_to_dataframe(self, price_data: List) -> pd.DataFrame:
        """
        価格データをDataFrameに変換
        """
        if not price_data:
            return pd.DataFrame()

        df_data = []
        for data in price_data:
            df_data.append(
                {
                    "timestamp": data.timestamp,
                    "Open": float(data.open_price) if data.open_price else 0.0,
                    "High": float(data.high_price) if data.high_price else 0.0,
                    "Low": float(data.low_price) if data.low_price else 0.0,
                    "Close": float(data.close_price) if data.close_price else 0.0,
                    "Volume": int(data.volume) if data.volume else 0,
                }
            )

        df = pd.DataFrame(df_data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)
        return df

    def _aggregate_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        時間軸を集計
        """
        if df.empty:
            return df

        try:
            # OHLCV集計
            agg_df = (
                df.resample(timeframe)
                .agg(
                    {
                        "Open": "first",
                        "High": "max",
                        "Low": "min",
                        "Close": "last",
                        "Volume": "sum",
                    }
                )
                .dropna()
            )

            return agg_df

        except Exception as e:
            logger.error(f"Error aggregating timeframe {timeframe}: {e}")
            return pd.DataFrame()

    async def _get_indicators_for_timeframe(
        self, timeframe: str, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        特定時間軸の指標データを取得
        """
        try:
            indicators = await self.indicator_repo.find_by_date_range(
                start_date, end_date, None, timeframe, self.currency_pair, 100
            )

            indicator_dict = {}

            # RSI
            latest_rsi = await self.indicator_repo.find_latest_by_type(
                "RSI", timeframe, limit=1
            )
            if latest_rsi:
                indicator_dict["rsi"] = {"current_value": float(latest_rsi[0].value)}

            # MACD
            latest_macd = await self.indicator_repo.find_latest_by_type(
                "MACD", timeframe, limit=1
            )
            if latest_macd:
                additional_data = latest_macd[0].additional_data or {}
                indicator_dict["macd"] = {
                    "macd": float(latest_macd[0].value),
                    "signal": additional_data.get("signal_line", 0.0),
                    "histogram": additional_data.get("histogram", 0.0),
                }

            # ボリンジャーバンド
            latest_bb = await self.indicator_repo.find_latest_by_type(
                "BB", timeframe, limit=1
            )
            if latest_bb:
                additional_data = latest_bb[0].additional_data or {}
                indicator_dict["bollinger_bands"] = {
                    "upper": additional_data.get("upper_band", 0.0),
                    "middle": float(latest_bb[0].value),
                    "lower": additional_data.get("lower_band", 0.0),
                }

            return indicator_dict

        except Exception as e:
            logger.error(f"Error getting indicators for timeframe {timeframe}: {e}")
            return {}

    async def _detect_single_pattern(
        self,
        pattern_number: int,
        detector,
        multi_timeframe_data: Dict,
    ) -> List[PatternDetectionModel]:
        """
        単一パターンを検出
        """
        try:
            # パターン検出器で検出
            detection_result = detector.detect(multi_timeframe_data)

            if not detection_result:
                return []

            # 検出結果をデータベースモデルに変換
            pattern = PatternDetectionModel(
                currency_pair=self.currency_pair,
                timestamp=datetime.now(),
                pattern_type=pattern_number,
                pattern_name=detection_result.get("pattern_name", ""),
                confidence_score=detection_result.get("confidence_score", 0.0),
                direction=(
                    "BUY" if detection_result.get("confidence_score", 0) > 0 else "SELL"
                ),
                detection_data=detection_result.get("conditions_met", {}),
                indicator_data=multi_timeframe_data,
                notification_sent=False,
                notification_sent_at=None,
                notification_message=detection_result.get("notification_title", ""),
            )

            # 重複チェックして保存
            saved_patterns = await self._save_patterns_with_duplicate_check([pattern])
            return saved_patterns

        except Exception as e:
            logger.error(f"Error in _detect_single_pattern: {e}")
            return []

    async def _save_patterns_with_duplicate_check(
        self, patterns: List[PatternDetectionModel]
    ) -> List[PatternDetectionModel]:
        """
        重複チェック付きでパターンを保存
        """
        saved_patterns = []

        for pattern in patterns:
            try:
                # 重複チェック（過去1時間以内の同じパターン）
                existing = await self.pattern_repo.find_recent_duplicate(
                    pattern.currency_pair,
                    pattern.pattern_type,
                    pattern.timestamp,
                    hours=1,
                )

                if existing:
                    logger.info(
                        f"Duplicate pattern detected, skipping: {pattern.pattern_name}"
                    )
                    continue

                # 保存
                saved_pattern = await self.pattern_repo.save(pattern)
                saved_patterns.append(saved_pattern)

                logger.info(
                    f"Saved pattern: {pattern.pattern_name} (confidence: {pattern.confidence_score})"
                )

            except Exception as e:
                logger.error(f"Error saving pattern: {e}")

        return saved_patterns

    async def get_latest_patterns(
        self,
        pattern_number: Optional[int] = None,
        limit: int = 10,
    ) -> List[PatternDetectionModel]:
        """
        最新のパターンを取得
        """
        try:
            return await self.pattern_repo.find_latest(
                self.currency_pair, pattern_number, limit
            )
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
        """
        try:
            if end_date is None:
                end_date = datetime.now()
            if start_date is None:
                start_date = end_date - timedelta(days=7)

            patterns = await self.pattern_repo.find_by_date_range(
                start_date, end_date, self.currency_pair
            )

            stats = {
                "total_patterns": len(patterns),
                "patterns_by_type": {},
                "average_confidence": 0.0,
                "notification_rate": 0.0,
            }

            if patterns:
                # パターンタイプ別集計
                for pattern in patterns:
                    pattern_type = pattern.pattern_type
                    if pattern_type not in stats["patterns_by_type"]:
                        stats["patterns_by_type"][pattern_type] = 0
                    stats["patterns_by_type"][pattern_type] += 1

                # 平均信頼度
                total_confidence = sum(p.confidence_score for p in patterns)
                stats["average_confidence"] = total_confidence / len(patterns)

                # 通知率
                notified_count = sum(1 for p in patterns if p.notification_sent)
                stats["notification_rate"] = notified_count / len(patterns)

            return stats

        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}
