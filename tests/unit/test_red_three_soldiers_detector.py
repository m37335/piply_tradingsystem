"""
赤三兵パターン検出器の単体テスト
"""

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.red_three_soldiers_detector import (
    RedThreeSoldiersDetector,
)


class TestRedThreeSoldiersDetector:
    """赤三兵パターン検出器のテストクラス"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.detector = RedThreeSoldiersDetector()

    def test_init(self):
        """初期化テスト"""
        assert self.detector.pattern.pattern_number == 8
        assert self.detector.pattern.name == "赤三兵検出"
        assert self.detector.min_body_ratio == 0.5
        assert self.detector.min_close_increase == 0.001

    def test_check_three_consecutive_bullish_candles(self):
        """3本連続陽線チェックテスト"""
        # 3本連続陽線のテストデータ
        candles = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],
            }
        )

        result = self.detector._check_three_consecutive_bullish_candles(candles)
        assert result is True

    def test_check_three_consecutive_bullish_candles_false(self):
        """3本連続陽線チェックテスト（陰線混在）"""
        # 陰線が混在するテストデータ
        candles = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [99.5, 101.5, 102.5],  # 1本目が陰線
            }
        )

        result = self.detector._check_three_consecutive_bullish_candles(candles)
        assert result is False

    def test_check_higher_closes(self):
        """終値高値更新チェックテスト"""
        # 終値が高値更新されるテストデータ
        candles = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 101.5, 102.5],  # 終値が上昇
            }
        )

        result = self.detector._check_higher_closes(candles)
        assert result is True

    def test_check_higher_closes_false(self):
        """終値高値更新チェックテスト（高値更新なし）"""
        # 終値が高値更新されないテストデータ
        candles = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.5, 100.3, 100.1],  # 終値が下降
            }
        )

        result = self.detector._check_higher_closes(candles)
        assert result is False

    def test_check_body_size_consistency(self):
        """実体サイズ一貫性チェックテスト"""
        # 実体サイズが一貫しているテストデータ
        candles = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.5, 100.5, 101.5],
                "close": [100.8, 101.8, 102.8],
            }
        )

        result = self.detector._check_body_size_consistency(candles)
        assert result is True

    def test_check_body_size_consistency_false(self):
        """実体サイズ一貫性チェックテスト（一貫性なし）"""
        # 実体サイズが一貫していないテストデータ
        candles = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [100.1, 102.0, 102.1],  # 1本目が非常に小さい実体
                "low": [100.0, 100.0, 101.0],
                "close": [100.05, 101.5, 102.05],
            }
        )

        result = self.detector._check_body_size_consistency(candles)
        assert result is False

    def test_detect_red_three_soldiers_pattern(self):
        """赤三兵パターン検出テスト"""
        # 赤三兵パターンのテストデータ
        price_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.5, 100.5, 101.5],
                "close": [100.8, 101.8, 102.8],
            }
        )

        result = self.detector._detect_red_three_soldiers_pattern(price_data)
        assert result is True

    def test_detect_red_three_soldiers_pattern_no_pattern(self):
        """赤三兵パターンなしのテスト"""
        # 赤三兵パターンではないデータ
        price_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [99.5, 100.3, 100.1],  # 終値が下降
            }
        )

        result = self.detector._detect_red_three_soldiers_pattern(price_data)
        assert result is False

    def test_calculate_pattern_strength(self):
        """パターン強度計算テスト"""
        conditions_met = {
            "D1": True,
            "H4": True,
            "H1": True,
            "M5": True,
        }

        confidence = self.detector._calculate_pattern_strength(conditions_met)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.80  # 基本信頼度以上

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

        assert info["pattern_number"] == 8
        assert info["name"] == "赤三兵検出"
        assert info["description"] == "3本連続陽線による強い上昇トレンド"
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
                        "open": [100.0, 101.0, 102.0],
                        "high": [101.0, 102.0, 103.0],
                        "low": [99.5, 100.5, 101.5],
                        "close": [100.8, 101.8, 102.8],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0, 70.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1, 0.2]),
                        "signal": pd.Series([0.0, 0.05, 0.15]),
                        "histogram": pd.Series([0.0, 0.05, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0, 98.0]),
                    },
                },
            },
            "H4": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 101.0, 102.0],
                        "high": [101.0, 102.0, 103.0],
                        "low": [99.5, 100.5, 101.5],
                        "close": [100.8, 101.8, 102.8],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0, 70.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1, 0.2]),
                        "signal": pd.Series([0.0, 0.05, 0.15]),
                        "histogram": pd.Series([0.0, 0.05, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0, 98.0]),
                    },
                },
            },
            "H1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 101.0, 102.0],
                        "high": [101.0, 102.0, 103.0],
                        "low": [99.5, 100.5, 101.5],
                        "close": [100.8, 101.8, 102.8],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0, 70.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1, 0.2]),
                        "signal": pd.Series([0.0, 0.05, 0.15]),
                        "histogram": pd.Series([0.0, 0.05, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0, 98.0]),
                    },
                },
            },
            "M5": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 101.0, 102.0],
                        "high": [101.0, 102.0, 103.0],
                        "low": [99.5, 100.5, 101.5],
                        "close": [100.8, 101.8, 102.8],
                    }
                ),
                "indicators": {
                    "rsi": pd.Series([50.0, 60.0, 70.0]),
                    "macd": {
                        "macd": pd.Series([0.0, 0.1, 0.2]),
                        "signal": pd.Series([0.0, 0.05, 0.15]),
                        "histogram": pd.Series([0.0, 0.05, 0.05]),
                    },
                    "bollinger_bands": {
                        "upper": pd.Series([102.0, 102.0, 102.0]),
                        "middle": pd.Series([100.0, 100.0, 100.0]),
                        "lower": pd.Series([98.0, 98.0, 98.0]),
                    },
                },
            },
        }

        # PatternUtilsのvalidate_timeframe_dataをモック
        self.detector.utils.validate_timeframe_data = lambda x: True

        result = self.detector.detect(multi_timeframe_data)

        # 結果が辞書形式で返されることを確認
        assert isinstance(result, dict)
        assert result["pattern_number"] == 8
        assert result["pattern_name"] == "赤三兵検出"
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
        # データが2本しかない場合
        price_data = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
            }
        )

        result = self.detector._detect_red_three_soldiers_pattern(price_data)
        assert result is False

        # 空のデータフレーム
        empty_data = pd.DataFrame()
        result = self.detector._detect_red_three_soldiers_pattern(empty_data)
        assert result is False
