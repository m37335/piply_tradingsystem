"""
引け坊主パターン検出器の単体テスト
"""

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.marubozu_detector import (
    MarubozuDetector,
)


class TestMarubozuDetector:
    """引け坊主パターン検出器のテストクラス"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.detector = MarubozuDetector()

    def test_init(self):
        """初期化テスト"""
        assert self.detector.pattern.pattern_number == 9
        assert self.detector.pattern.name == "引け坊主検出"
        assert self.detector.max_wick_ratio == 0.1
        assert self.detector.min_body_ratio == 0.8

    def test_detect_bullish_marubozu(self):
        """大陽線引け坊主検出テスト"""
        # 大陽線引け坊主のテストデータ
        candle = pd.Series(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 100.0,  # 下ヒゲなし
                "close": 105.0,  # 上ヒゲなし
            }
        )

        result = self.detector._detect_bullish_marubozu(candle)
        assert result is True

    def test_detect_bearish_marubozu(self):
        """大陰線引け坊主検出テスト"""
        # 大陰線引け坊主のテストデータ
        candle = pd.Series(
            {
                "open": 105.0,
                "high": 105.0,  # 上ヒゲなし
                "low": 100.0,
                "close": 100.0,  # 下ヒゲなし
            }
        )

        result = self.detector._detect_bearish_marubozu(candle)
        assert result is True

    def test_check_wick_absence(self):
        """ヒゲ欠如チェックテスト"""
        # ヒゲがないローソク足
        candle = pd.Series(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 100.0,
                "close": 105.0,
            }
        )

        result = self.detector._check_wick_absence(candle)
        assert result is True

    def test_check_wick_absence_with_wicks(self):
        """ヒゲ欠如チェックテスト（ヒゲあり）"""
        # ヒゲがあるローソク足
        candle = pd.Series(
            {
                "open": 100.0,
                "high": 107.0,  # 上ヒゲあり
                "low": 98.0,  # 下ヒゲあり
                "close": 105.0,
            }
        )

        result = self.detector._check_wick_absence(candle)
        assert result is False

    def test_detect_marubozu_pattern(self):
        """引け坊主パターン検出テスト"""
        # 引け坊主パターンのテストデータ
        price_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [105.0],
                "low": [100.0],
                "close": [105.0],
            }
        )

        result = self.detector._detect_marubozu_pattern(price_data)
        assert result is True

    def test_detect_marubozu_pattern_no_pattern(self):
        """引け坊主パターンなしのテスト"""
        # 引け坊主パターンではないデータ
        price_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [107.0],  # 上ヒゲあり
                "low": [98.0],  # 下ヒゲあり
                "close": [105.0],
            }
        )

        result = self.detector._detect_marubozu_pattern(price_data)
        assert result is False

    def test_calculate_marubozu_strength(self):
        """引け坊主強度計算テスト"""
        conditions_met = {
            "D1": True,
            "H4": True,
            "H1": True,
            "M5": True,
        }

        confidence = self.detector._calculate_marubozu_strength(conditions_met)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.75  # 基本信頼度以上

    def test_validate_data(self):
        """データ妥当性チェックテスト"""
        # 正常なデータ
        valid_data = {
            "D1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 20,
                        "high": [101.0] * 20,
                        "low": [99.0] * 20,
                        "close": [100.5] * 20,
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0] * 20),
                    "macd": {
                        "macd": pd.Series([0.0] * 20),
                        "signal": pd.Series([0.0] * 20),
                        "histogram": pd.Series([0.0] * 20),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0] * 20),
                        "middle": pd.Series([100.0] * 20),
                        "lower": pd.Series([98.0] * 20),
                    },
                },
            },
            "H4": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 20,
                        "high": [101.0] * 20,
                        "low": [99.0] * 20,
                        "close": [100.5] * 20,
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0] * 20),
                    "macd": {
                        "macd": pd.Series([0.0] * 20),
                        "signal": pd.Series([0.0] * 20),
                        "histogram": pd.Series([0.0] * 20),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0] * 20),
                        "middle": pd.Series([100.0] * 20),
                        "lower": pd.Series([98.0] * 20),
                    },
                },
            },
            "H1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 20,
                        "high": [101.0] * 20,
                        "low": [99.0] * 20,
                        "close": [100.5] * 20,
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0] * 20),
                    "macd": {
                        "macd": pd.Series([0.0] * 20),
                        "signal": pd.Series([0.0] * 20),
                        "histogram": pd.Series([0.0] * 20),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0] * 20),
                        "middle": pd.Series([100.0] * 20),
                        "lower": pd.Series([98.0] * 20),
                    },
                },
            },
            "M5": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 20,
                        "high": [101.0] * 20,
                        "low": [99.0] * 20,
                        "close": [100.5] * 20,
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0] * 20),
                    "macd": {
                        "macd": pd.Series([0.0] * 20),
                        "signal": pd.Series([0.0] * 20),
                        "histogram": pd.Series([0.0] * 20),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0] * 20),
                        "middle": pd.Series([100.0] * 20),
                        "lower": pd.Series([98.0] * 20),
                    },
                },
            },
        }

        result = self.detector._validate_data(valid_data)
        assert result is True

    def test_validate_data_missing_timeframe(self):
        """データ妥当性チェックテスト（時間軸不足）"""
        # 時間軸が不足しているデータ
        invalid_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            # H1とM5が不足
        }

        result = self.detector._validate_data(invalid_data)
        assert result is False

    def test_get_pattern_info(self):
        """パターン情報取得テスト"""
        info = self.detector.get_pattern_info()

        assert info["pattern_number"] == 9
        assert info["name"] == "引け坊主検出"
        assert info["description"] == "ヒゲのない強いローソク足パターン"
        assert "D1" in info["conditions"]
        assert "H4" in info["conditions"]
        assert "H1" in info["conditions"]
        assert "M5" in info["conditions"]

    def test_detect_with_valid_data(self):
        """有効なデータでの検出テスト"""
        # マルチタイムフレームデータを作成
        multi_timeframe_data = {
            "D1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0],
                        "high": [105.0],
                        "low": [100.0],
                        "close": [105.0],
                    }
                )
            },
            "H4": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0],
                        "high": [105.0],
                        "low": [100.0],
                        "close": [105.0],
                    }
                )
            },
            "H1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0],
                        "high": [105.0],
                        "low": [100.0],
                        "close": [105.0],
                    }
                )
            },
            "M5": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0],
                        "high": [105.0],
                        "low": [100.0],
                        "close": [105.0],
                    }
                )
            },
        }

        # PatternUtilsのvalidate_timeframe_dataをモック
        self.detector.utils.validate_timeframe_data = lambda x: True

        result = self.detector.detect(multi_timeframe_data)

        # 結果が辞書形式で返されることを確認
        assert isinstance(result, dict)
        assert result["pattern_number"] == 9
        assert result["pattern_name"] == "引け坊主検出"
        assert "confidence_score" in result
        assert "detected_at" in result

    def test_detect_with_invalid_data(self):
        """無効なデータでの検出テスト"""
        # 空のデータ
        invalid_data = {}

        result = self.detector.detect(invalid_data)
        assert result is None

    def test_edge_cases(self):
        """エッジケーステスト"""
        # 空のデータフレーム
        empty_data = pd.DataFrame()
        result = self.detector._detect_marubozu_pattern(empty_data)
        assert result is False

        # 実体が小さいローソク足
        small_body_candle = pd.Series(
            {
                "open": 100.0,
                "high": 101.0,
                "low": 100.0,
                "close": 100.5,  # 実体が小さい
            }
        )

        result = self.detector._detect_bullish_marubozu(small_body_candle)
        assert result is False

    def test_wick_ratio_calculation(self):
        """ヒゲ比率計算テスト"""
        # 上ヒゲのみ
        upper_wick_candle = pd.Series(
            {
                "open": 100.0,
                "high": 106.0,  # 上ヒゲあり
                "low": 100.0,
                "close": 105.0,
            }
        )

        result = self.detector._check_wick_absence(upper_wick_candle)
        assert result is False

        # 下ヒゲのみ
        lower_wick_candle = pd.Series(
            {
                "open": 100.0,
                "high": 105.0,
                "low": 99.0,  # 下ヒゲあり
                "close": 105.0,
            }
        )

        result = self.detector._check_wick_absence(lower_wick_candle)
        assert result is False
