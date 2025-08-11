# Note フォルダ構成

このフォルダは、USD/JPY為替分析システムの開発に関する各種ドキュメントを整理したものです。

## 📁 フォルダ構成

### 🏗️ `design_documents/` - 設計書
システム全体の設計に関するドキュメント
- **基本設計書**: システム全体の基本設計
- **詳細内部設計**: 内部実装の詳細設計
- **アプリケーション層設計**: アプリケーション層の設計
- **プレゼンテーション層設計**: プレゼンテーション層の設計
- **補足設計**: 各層の補足設計書
- **インフラ・プラグイン設計**: インフラストラクチャ設計
- **モジュール設計思想**: モジュール設計の思想
- **フォルダ構成実装ガイド**: フォルダ構成のガイド

### 📊 `implementation_status/` - 実装状況
実装の進捗状況と計画に関するドキュメント
- **notification_implementation_status_2025*.md**: 通知機能の実装状況（Phase別）
- **notification_implementation_plan_2025*.md**: 通知機能の実装計画
- **system_implementation_completion_report_2025.md**: システム実装完了レポート
- **implementation_todo_2025.yaml**: 実装TODOリスト
- **multiframe_continuous_processing_*.md**: マルチタイムフレーム処理の設計・計画
- **current_situation_analysis_2025.md**: 現在の状況分析
- **TODO.yaml**: 全体TODOリスト

### 🔍 `pattern_analysis/` - パターン分析
パターン検出機能に関するドキュメント
- **パターン検出検討案.md**: パターン検出の総合検討案（16パターン）
- **パターン検出案.md**: テクニカル分析パターンの基本案
- **パターン5実装エラーとデータベース設計メモ.md**: パターン5実装時のエラーとDB設計メモ

### ⚡ `api_optimization/` - API最適化
API最適化に関するドキュメント
- **api_optimization_design_2025.md**: API最適化の設計
- **api_optimization_implementation_plan_2025.yaml**: API最適化の実装計画
- **api_optimization_implementation_report_2025.md**: API最適化の実装レポート

### 🗄️ `database_design/` - データベース設計
データベース設計に関するドキュメント
- **database_implementation_design_2025.md**: データベース実装設計
- **database_implementation_plan_2025.yaml**: データベース実装計画

### 📈 `trade_settings/` - トレード設定
トレード分析設定に関するドキュメント
- **trade_chart_settings_2025.md**: トレードチャート設定
- **trade_chart_settings_complete_2025.md**: トレードチャート設定（完全版）
- **discord_notification_patterns_2025.md**: Discord通知パターン設計

## 📋 ドキュメント更新履歴

### 2025年8月11日
- フォルダ構成の整理
- カテゴリ別分類の実施
- README.mdの作成

### 2025年8月10日
- パターン検出検討案の作成（16パターン）
- 実装状況の更新

### 2025年8月9日
- 基本設計書の作成
- 各層の設計書作成

## 🎯 主要ドキュメント

### 最新の重要ドキュメント
1. **パターン検出検討案.md** - 16パターンの包括的検討案
2. **system_implementation_completion_report_2025.md** - システム実装完了レポート
3. **current_situation_analysis_2025.md** - 現在の状況分析

### 設計書
1. **基本設計書_20250809.md** - システム全体の基本設計
2. **詳細内部設計_20250809.md** - 内部実装の詳細設計

### 実装計画
1. **implementation_todo_2025.yaml** - 実装TODOリスト
2. **notification_implementation_plan_2025.yaml** - 通知機能実装計画

## 📝 ドキュメント作成ガイドライン

### ファイル命名規則
- **設計書**: `[機能名]_設計_YYYYMMDD.md`
- **実装状況**: `[機能名]_implementation_status_YYYY.md`
- **計画書**: `[機能名]_plan_YYYY.yaml`
- **レポート**: `[機能名]_report_YYYY.md`

### 更新履歴の記録
各ドキュメントの末尾に更新履歴を記録することを推奨します。

### バージョン管理
重要な変更がある場合は、ファイル名にバージョン番号を付けることを推奨します。
