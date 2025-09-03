# Analysis Scripts Directory

## 概要

システムの分析・デバッグ用スクリプトを管理するディレクトリです。パフォーマンス分析、条件最適化、データ検証などのスクリプトが保存されています。

## 保存されているファイル

### 分析スクリプト（5 ファイル）

- `analyze_buy_sell_differences.py` - 買い売り差異分析
- `analyze_current_conditions.py` - 現在状況分析
- `analyze_pattern_conditions.py` - パターン条件分析
- `analyze_price_movement_after_reversal.py` - 反転後の価格動向分析
- `analyze_reversal_points.py` - 反転ポイント分析

### チェックスクリプト（5 ファイル）

- `check_available_indicators.py` - 利用可能指標チェック
- `check_price_data.py` - 価格データチェック
- `check_rsi_timeframes.py` - RSI タイムフレームチェック
- `check_technical_data.py` - テクニカルデータチェック
- `check_test_data.py` - テストデータチェック

### 比較・最適化スクリプト（3 ファイル）

- `compare_analysis_methods.py` - 分析手法比較
- `optimize_conditions.py` - 条件最適化
- `optimize_ma_timeframes.py` - 移動平均タイムフレーム最適化

### 表示・検証スクリプト（3 ファイル）

- `show_current_conditions.py` - 現在状況表示
- `verify_signal_performance.py` - シグナル性能検証
- `timezone_fix.py` - タイムゾーン修正

### 戦略・実装スクリプト（2 ファイル）

- `trading_strategy_implementation.py` - 取引戦略実装
- `ma_based_entry_timing.py` - 移動平均ベースエントリー

## よく編集するファイル

- `optimize_*.py` - 条件最適化時
- `analyze_*.py` - 新しい分析要件追加時
- `check_*.py` - データ検証要件変更時

## 注意事項

- 分析結果は本番環境に影響しないよう注意
- 大量データ処理時はメモリ使用量を監視
- 分析スクリプトの実行時間を考慮
- 結果は適切なフォルダに保存

## 関連フォルダ

- `scripts/development/` - 開発スクリプト
- `data/` - 分析データ
- `reports/` - 分析レポート
