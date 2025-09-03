"""
つつみ足パターン検出器の単体テスト
"""

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.engulfing_pattern_detector import (
    EngulfingPatternDetector,
)


class TestEngulfingPatternDetector:
    """つつみ足パターン検出器のテストクラス"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.detector = EngulfingPatternDetector()

    def test_init(self):
        """初期化テスト"""
        assert self.detector.pattern.pattern_number == 7
        assert self.detector.pattern.name == "つつみ足検出"
        assert self.detector.min_body_ratio == 0.6
        assert self.detector.min_engulfing_ratio == 1.1

    def test_detect_bullish_engulfing(self):
        """陽のつつみ足検出テスト"""
        # テストデータ作成
        price_data = pd.DataFrame(
            {
                "open": [100.0, 99.0],
                "high": [101.0, 105.0],
                "low": [99.0, 98.5],
                "close": [99.5, 104.0],
            }
        )

        # 前の足（陰線）と現在の足（陽線）でつつみ足パターンを作成
        current_candle = price_data.iloc[1]
        previous_candle = price_data.iloc[0]

        result = self.detector._detect_bullish_engulfing(
            current_candle, previous_candle
        )
        assert result is True

    def test_detect_bearish_engulfing(self):
        """陰のつつみ足検出テスト"""
        # テストデータ作成
        price_data = pd.DataFrame(
            {
                "open": [100.0, 104.0],
                "high": [101.0, 105.0],
                "low": [99.0, 99.5],
                "close": [100.5, 99.5],
            }
        )

        # 前の足（陽線）と現在の足（陰線）でつつみ足パターンを作成
        current_candle = price_data.iloc[1]
        previous_candle = price_data.iloc[0]

        result = self.detector._detect_bearish_engulfing(
            current_candle, previous_candle
        )
        assert result is True

    def test_detect_engulfing_pattern(self):
        """つつみ足パターン検出テスト"""
        # 陽のつつみ足パターンのテストデータ
        price_data = pd.DataFrame(
            {
                "open": [100.0, 99.0],
                "high": [101.0, 105.0],
                "low": [99.0, 98.5],
                "close": [99.5, 104.0],
            }
        )

        result = self.detector._detect_engulfing_pattern(price_data)
        assert result is True

    def test_detect_engulfing_pattern_no_pattern(self):
        """つつみ足パターンなしのテスト"""
        # つつみ足パターンではないデータ
        price_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
            }
        )

        result = self.detector._detect_engulfing_pattern(price_data)
        assert result is False

    def test_calculate_engulfing_confidence(self):
        """つつみ足信頼度計算テスト"""
        conditions_met = {
            "D1": True,
            "H4": True,
            "H1": True,
            "M5": True,
        }

        confidence = self.detector._calculate_engulfing_confidence(conditions_met)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.85  # 基本信頼度以上

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

        assert info["pattern_number"] == 7
        assert info["name"] == "つつみ足検出"
        assert info["description"] == "前の足を完全に包み込むローソク足パターン"
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
                        "open": [100.0, 99.0],
                        "high": [101.0, 105.0],
                        "low": [99.0, 98.5],
                        "close": [99.5, 104.0],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1]),
                        "signal": pd.Series([0.0, 0.05]),
                        "histogram": pd.Series([0.0, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0]),
                    },
                },
            },
            "H4": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 99.0],
                        "high": [101.0, 105.0],
                        "low": [99.0, 98.5],
                        "close": [99.5, 104.0],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1]),
                        "signal": pd.Series([0.0, 0.05]),
                        "histogram": pd.Series([0.0, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0]),
                    },
                },
            },
            "H1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 99.0],
                        "high": [101.0, 105.0],
                        "low": [99.0, 98.5],
                        "close": [99.5, 104.0],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1]),
                        "signal": pd.Series([0.0, 0.05]),
                        "histogram": pd.Series([0.0, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0]),
                    },
                },
            },
            "M5": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 99.0],
                        "high": [101.0, 105.0],
                        "low": [99.0, 98.5],
                        "close": [99.5, 104.0],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1]),
                        "signal": pd.Series([0.0, 0.05]),
                        "histogram": pd.Series([0.0, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0]),
                    },
                },
            },
        }

        # PatternUtilsのvalidate_timeframe_dataをモック
        self.detector.utils.validate_timeframe_data = lambda x: True

        result = self.detector.detect(multi_timeframe_data)

        # 結果が辞書形式で返されることを確認
        assert isinstance(result, dict)
        assert result["pattern_number"] == 7
        assert result["pattern_name"] == "つつみ足検出"
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
        # データが1本しかない場合
        price_data = pd.DataFrame(
            {
                "open": [100.0],
                "high": [101.0],
                "low": [99.0],
                "close": [100.5],
            }
        )

        result = self.detector._detect_engulfing_pattern(price_data)
        assert result is False

        # 空のデータフレーム
        empty_data = pd.DataFrame()
        result = self.detector._detect_engulfing_pattern(empty_data)
        assert result is False
