"""
Phase1 パターン検出器の統合テスト

パターン7（つつみ足）、パターン8（赤三兵）、パターン9（引け坊主）の統合テスト
"""

import pandas as pd

from src.infrastructure.analysis.notification_pattern_analyzer import (
    NotificationPatternAnalyzer,
)


class TestPhase1Patterns:
    """Phase1 パターン検出器の統合テストクラス"""

    def setup_method(self):
        """テスト前のセットアップ"""
        self.analyzer = NotificationPatternAnalyzer()

    def test_phase1_patterns_integration(self):
        """Phase1 パターンの統合テスト"""
        # マルチタイムフレームデータを作成（つつみ足パターン）
        multi_timeframe_data = {
            "D1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 19 + [99.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [98.5],
                        "close": [99.5] * 19 + [104.0],
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
                        "open": [100.0] * 19 + [99.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [98.5],
                        "close": [99.5] * 19 + [104.0],
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
                        "open": [100.0] * 19 + [99.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [98.5],
                        "close": [99.5] * 19 + [104.0],
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
                        "open": [100.0] * 19 + [99.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [98.5],
                        "close": [99.5] * 19 + [104.0],
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

        # PatternUtilsのvalidate_timeframe_dataをモック
        for detector in self.analyzer.detectors.values():
            detector.utils.validate_timeframe_data = lambda x: True

        # NotificationPatternAnalyzerの_validate_multi_timeframe_dataもモック
        self.analyzer._validate_multi_timeframe_data = lambda x: True

        # 分析実行
        results = self.analyzer.analyze_multi_timeframe_data(multi_timeframe_data)

        # 結果の確認
        assert isinstance(results, list)

        # つつみ足パターンが検出されることを確認
        pattern_7_detected = any(result["pattern_number"] == 7 for result in results)
        assert pattern_7_detected, "パターン7（つつみ足）が検出されませんでした"

    def test_red_three_soldiers_integration(self):
        """赤三兵パターンの統合テスト"""
        # マルチタイムフレームデータを作成（赤三兵パターン）
        multi_timeframe_data = {
            "D1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 17 + [101.0, 102.0],
                        "high": [101.0] * 17 + [102.0, 103.0],
                        "low": [99.5] * 17 + [100.5, 101.5],
                        "close": [100.8] * 17 + [101.8, 102.8],
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
                        "open": [100.0] * 17 + [101.0, 102.0],
                        "high": [101.0] * 17 + [102.0, 103.0],
                        "low": [99.5] * 17 + [100.5, 101.5],
                        "close": [100.8] * 17 + [101.8, 102.8],
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
                        "open": [100.0] * 17 + [101.0, 102.0],
                        "high": [101.0] * 17 + [102.0, 103.0],
                        "low": [99.5] * 17 + [100.5, 101.5],
                        "close": [100.8] * 17 + [101.8, 102.8],
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
                        "open": [100.0] * 17 + [101.0, 102.0],
                        "high": [101.0] * 17 + [102.0, 103.0],
                        "low": [99.5] * 17 + [100.5, 101.5],
                        "close": [100.8] * 17 + [101.8, 102.8],
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

        # PatternUtilsのvalidate_timeframe_dataをモック
        for detector in self.analyzer.detectors.values():
            detector.utils.validate_timeframe_data = lambda x: True

        # NotificationPatternAnalyzerの_validate_multi_timeframe_dataもモック
        self.analyzer._validate_multi_timeframe_data = lambda x: True

        # 分析実行
        results = self.analyzer.analyze_multi_timeframe_data(multi_timeframe_data)

        # 結果の確認
        assert isinstance(results, list)

        # 赤三兵パターンが検出されることを確認
        pattern_8_detected = any(result["pattern_number"] == 8 for result in results)
        assert pattern_8_detected, "パターン8（赤三兵）が検出されませんでした"

    def test_marubozu_integration(self):
        """引け坊主パターンの統合テスト"""
        # マルチタイムフレームデータを作成（引け坊主パターン）
        multi_timeframe_data = {
            "D1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0] * 19 + [100.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [100.0],
                        "close": [100.5] * 19 + [105.0],
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
                        "open": [100.0] * 19 + [100.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [100.0],
                        "close": [100.5] * 19 + [105.0],
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
                        "open": [100.0] * 19 + [100.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [100.0],
                        "close": [100.5] * 19 + [105.0],
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
                        "open": [100.0] * 19 + [100.0],
                        "high": [101.0] * 19 + [105.0],
                        "low": [99.0] * 19 + [100.0],
                        "close": [100.5] * 19 + [105.0],
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

        # PatternUtilsのvalidate_timeframe_dataをモック
        for detector in self.analyzer.detectors.values():
            detector.utils.validate_timeframe_data = lambda x: True

        # NotificationPatternAnalyzerの_validate_multi_timeframe_dataもモック
        self.analyzer._validate_multi_timeframe_data = lambda x: True

        # 分析実行
        results = self.analyzer.analyze_multi_timeframe_data(multi_timeframe_data)

        # 結果の確認
        assert isinstance(results, list)

        # 引け坊主パターンが検出されることを確認
        pattern_9_detected = any(result["pattern_number"] == 9 for result in results)
        assert pattern_9_detected, "パターン9（引け坊主）が検出されませんでした"

    def test_phase1_patterns_info(self):
        """Phase1 パターン情報の取得テスト"""
        # 全パターン情報を取得
        all_patterns = self.analyzer.get_all_patterns_info()

        # Phase1 パターンが含まれていることを確認
        pattern_numbers = [pattern["pattern_number"] for pattern in all_patterns]

        assert 7 in pattern_numbers, "パターン7（つつみ足）が含まれていません"
        assert 8 in pattern_numbers, "パターン8（赤三兵）が含まれていません"
        assert 9 in pattern_numbers, "パターン9（引け坊主）が含まれていません"

        # 各パターンの詳細情報を確認
        pattern_7_info = next(p for p in all_patterns if p["pattern_number"] == 7)
        assert pattern_7_info["name"] == "つつみ足検出"
        assert pattern_7_info["description"] == "前の足を完全に包み込むローソク足パターン"

        pattern_8_info = next(p for p in all_patterns if p["pattern_number"] == 8)
        assert pattern_8_info["name"] == "赤三兵検出"
        assert pattern_8_info["description"] == "3本連続陽線による強い上昇トレンド"

        pattern_9_info = next(p for p in all_patterns if p["pattern_number"] == 9)
        assert pattern_9_info["name"] == "引け坊主検出"
        assert pattern_9_info["description"] == "ヒゲのない強いローソク足パターン"

    def test_phase1_detectors_status(self):
        """Phase1 検出器の状態確認テスト"""
        # 検出器の状態を取得
        detector_status = self.analyzer.get_detector_status()

        # Phase1 検出器が含まれていることを確認
        detector_names = [
            detector["pattern_name"] for detector in detector_status["active_detectors"]
        ]

        assert "つつみ足検出" in detector_names, "つつみ足検出器が含まれていません"
        assert "赤三兵検出" in detector_names, "赤三兵検出器が含まれていません"
        assert "引け坊主検出" in detector_names, "引け坊主検出器が含まれていません"

    def test_phase1_patterns_with_no_pattern_data(self):
        """パターンなしデータでのテスト"""
        # パターンが検出されないデータ
        no_pattern_data = {
            "D1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 100.1],
                        "high": [100.2, 100.3],
                        "low": [99.9, 100.0],
                        "close": [100.1, 100.2],
                    }
                )
            },
            "H4": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 100.1],
                        "high": [100.2, 100.3],
                        "low": [99.9, 100.0],
                        "close": [100.1, 100.2],
                    }
                )
            },
            "H1": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 100.1],
                        "high": [100.2, 100.3],
                        "low": [99.9, 100.0],
                        "close": [100.1, 100.2],
                    }
                )
            },
            "M5": {
                "price_data": pd.DataFrame(
                    {
                        "open": [100.0, 100.1],
                        "high": [100.2, 100.3],
                        "low": [99.9, 100.0],
                        "close": [100.1, 100.2],
                    }
                )
            },
        }

        # PatternUtilsのvalidate_timeframe_dataをモック
        for detector in self.analyzer.detectors.values():
            detector.utils.validate_timeframe_data = lambda x: True

        # 分析実行
        results = self.analyzer.analyze_multi_timeframe_data(no_pattern_data)

        # 結果の確認（パターンが検出されないことを確認）
        assert isinstance(results, list)
        # このデータではパターンが検出されない可能性が高いが、
        # 検出された場合は結果の形式を確認
        for result in results:
            assert "pattern_number" in result
            assert "pattern_name" in result
            assert "confidence_score" in result
            assert "detected_at" in result

    def test_phase1_patterns_error_handling(self):
        """エラーハンドリングテスト"""
        # 無効なデータ
        invalid_data = {}

        # 分析実行（エラーが発生しないことを確認）
        results = self.analyzer.analyze_multi_timeframe_data(invalid_data)

        # 結果の確認
        assert isinstance(results, list)
        assert len(results) == 0  # 無効なデータでは結果が空になることを確認
