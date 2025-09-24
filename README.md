# 🚀 Exchange Analytics USD/JPY パターン検出システム

**モジュール化されたアーキテクチャ・24時間自動稼働・統合AI分析・Discord自動通知システム**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.0+-green.svg)](https://www.timescale.com/)
[![Discord](https://img.shields.io/badge/Discord-Webhook-orange.svg)](https://discord.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple.svg)](https://openai.com/)
[![Yahoo Finance](https://img.shields.io/badge/Yahoo%20Finance-Free%20Data-red.svg)](https://finance.yahoo.com/)
[![TA-Lib](https://img.shields.io/badge/TA--Lib-Technical%20Analysis-purple.svg)](https://ta-lib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 概要

Exchange Analytics USD/JPY パターン検出システムは、**モジュール化されたアーキテクチャ**で構築された**24時間自動稼働**の為替分析システムです。**統合AI分析**と**Discord自動通知**、**三層ゲートシステム**による高度なパターン検出を提供します。

**稼働開始**: 2025年8月10日 日本時間8:00から  
**稼働モード**: 24時間自動稼働（平日）  
**データ取得**: USD/JPY 5分間隔  
**パターン検出**: 三層ゲートシステムによる高度なパターン検出  
**AI分析**: GPT-4統合による高度な市場分析  
**通知**: Discord自動配信  
**アーキテクチャ**: モジュール化されたマイクロサービス設計  
**開発状況**: システム最適化完了（2025年9月23日）

## 🏗️ モジュール化アーキテクチャ

### 📊 **データ収集モジュール** (`modules/data_collection/`)

**機能**:
- Yahoo Finance APIからのリアルタイムデータ収集
- 複数時間軸（M5, M15, H1, H4, D1）での同時収集
- インテリジェントデータコレクターによる優先度ベース収集
- レート制限管理とサーキットブレーカー
- データ品質管理と自動検証

**技術スタック**:
- Python 3.8+ / asyncio / asyncpg
- yfinance / aiohttp / PostgreSQL
- レート制限: トークンバケット、スライディングウィンドウ

### 💾 **データ永続化モジュール** (`modules/data_persistence/`)

**機能**:
- PostgreSQL + TimescaleDBによる高性能時系列データ管理
- 自動データ圧縮と保持ポリシー
- データギャップ検出と欠損データ補完
- LLM分析結果の構造化保存
- マイグレーション管理とスキーマバージョン管理

**技術スタック**:
- PostgreSQL 15+ / TimescaleDB 2.0+
- asyncpg / psycopg2 / SQLAlchemy 2.0+

### 🤖 **LLM分析モジュール** (`modules/llm_analysis/`)

**機能**:
- GPT-4/Claude統合による包括的市場分析
- イベント駆動アーキテクチャによる自動分析実行
- 三層ゲートシステム（D1/H4トレンド、H1ゾーン、M5タイミング）
- ルールベース売買システム（5つのアクティブルール）
- シナリオ管理とDiscord通知

**技術スタック**:
- OpenAI GPT-4 / Anthropic Claude
- TA-Lib / yfinance / Discord Webhook
- 非同期処理 / 品質管理システム

### 📈 **経済指標モジュール** (`modules/economic_indicators/`)

**機能**:
- FRED API、Investing.com、Trading Economicsからの経済指標収集
- 経済カレンダー管理とイベント追跡
- インパクト分析と市場への影響評価
- 複数プロバイダー対応とフォールバック機能

### ⚡ **レート制限モジュール** (`modules/rate_limiting/`)

**機能**:
- 統合レート制限管理システム
- サーキットブレーカーとフォールバック管理
- ロードバランサー（ラウンドロビン、重み付き、ヘルスベース）
- 分散レート制限と適応的制限調整

### 📅 **スケジューラーモジュール** (`modules/scheduler/`)

**機能**:
- 市場時間を考慮したインテリジェントスケジューリング
- 祝日管理と市場時間調整
- タスク実行とエラーハンドリング
- データ収集タスクの自動スケジューリング

### 🔔 **通知モジュール** (`modules/notification/`)

**機能**:
- Discord Webhook統合
- リッチな埋め込みメッセージ配信
- 通知ルールエンジンとクールダウン管理
- エラーアラートとシステム監視通知

### 📊 **モニタリングモジュール** (`modules/monitoring/`)

**機能**:
- システムヘルスチェックとパフォーマンス監視
- Prometheus + Grafana統合
- リアルタイム監視ダッシュボード
- アラート管理と通知

### 🛡️ **リスク管理モジュール** (`modules/risk_management/`)

**機能**:
- 動的ストップロス調整
- ポートフォリオリスク管理
- ポジションサイズ計算
- リスク評価と制御

### 🎯 **シグナル生成モジュール** (`modules/signal_generation/`)

**機能**:
- テクニカル指標ベースのシグナル生成
- パターン認識とシグナル評価
- シグナル品質管理と信頼度計算
- 複数時間軸でのシグナル統合

### 🧠 **機械学習推論モジュール** (`modules/ml_inference/`)

**機能**:
- 機械学習モデルの推論実行
- 予測モデル管理と更新
- 特徴量エンジニアリング
- モデル性能監視

## 🌟 システム機能

### 🔍 **三層ゲートシステム**

#### **Gate 1: トレンド分析** (D1/H4)
- 長期トレンドの方向性判定
- 移動平均線とトレンドライン分析
- トレンド強度の定量化

#### **Gate 2: ゾーン分析** (H1)
- サポート・レジスタンスレベル検出
- 価格ゾーンの重要度評価
- ブレイクアウト可能性の分析

#### **Gate 3: タイミング分析** (M5)
- エントリータイミングの最適化
- 短期シグナルの精度向上
- リスク管理パラメータの調整

### 🤖 **統合AI分析機能**

- **GPT-4統合**: OpenAI GPT-4による高度な市場分析
- **通貨相関分析**: 複数通貨ペアの相関性分析
- **テクニカル指標統合**: 複数指標の統合分析
- **市場シナリオ生成**: AIによる市場シナリオ予測
- **リスク評価**: AIによるリスク分析と推奨事項

### 📊 **テクニカル指標分析**

- **RSI**: 相対力指数（14期間）
- **MACD**: 移動平均収束拡散（12,26,9）
- **ボリンジャーバンド**: 価格変動の統計的範囲（20期間,2σ）
- **移動平均**: 短期・中期・長期移動平均
- **ストキャスティクス**: オシレーター分析

### 🔔 **自動通知システム**

- **Discord通知**: パターン検出時の自動配信
- **AI分析レポート**: 統合AI分析の定期配信
- **システム監視**: システム状態の定期報告
- **エラー通知**: 異常発生時の即座通知

## 🚀 本番稼働スケジュール

### メインシステム稼働状況

**USD/JPYデータ取得・分析**:
- **実行間隔**: 5分間隔
- **稼働時間**: 平日24時間（月曜〜金曜）
- **処理内容**: データ取得 → 指標計算 → パターン検出 → Discord通知

**統合AI分析**:
- **実行間隔**: 2時間間隔
- **稼働時間**: 平日8:00-2:00 JST
- **処理内容**: 通貨相関分析 → テクニカル分析 → AI分析 → Discord配信

**日次レポート**:
- **実行時刻**: 毎日6:00 JST
- **内容**: 日次統計・パターン検出結果

**週次レポート**:
- **実行時刻**: 毎週土曜日6:00 JST
- **内容**: 週次統計・システム稼働状況

## ⚡ クイックスタート

### 1. 環境設定

```bash
# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp env.example .env
# DISCORD_WEBHOOK_URL, DISCORD_MONITORING_WEBHOOK_URL, OPENAI_API_KEY を設定
```

### 2. データベース設定

```bash
# PostgreSQL + TimescaleDB設定
# データベース初期化
python modules/data_persistence/core/database/database_initializer.py

# マイグレーション実行
python modules/data_persistence/migrations/migration_manager.py
```

### 3. システムテスト

```bash
# データ収集テスト
python modules/data_collection/main.py --test

# LLM分析テスト
python modules/llm_analysis/main.py --test

# 統合システムテスト
python scripts/comprehensive_system_check.py
```

### 4. 本番稼働開始

```bash
# データ収集デーモン起動
python modules/data_collection/daemon/data_collection_daemon.py

# LLM分析システム起動
python modules/llm_analysis/scripts/start_event_driven_system.py

# 継続的監視ツール起動
python modules/llm_analysis/scripts/continuous_monitor.py
```

## 🔧 システム管理

### 稼働状況確認

```bash
# システムヘルスチェック
python scripts/system_health_check.py

# データ収集状況確認
python modules/data_collection/tools/realtime_monitor.py

# LLM分析状況確認
python modules/llm_analysis/scripts/continuous_monitor.py

# データベース接続確認
python modules/data_persistence/tests/test_database_connection.py
```

### 監視・メンテナンス

**ログ確認**:
```bash
# システムログ
tail -f logs/data_collection_daemon.log
tail -f logs/three_gate_system.log

# エラーログ監視
grep -i "error\|failed\|exception" logs/*.log
```

**トラブルシューティング**:
```bash
# データベース接続テスト
python modules/data_persistence/tests/test_database_connection.py

# データ収集テスト
python modules/data_collection/tests/test_data_collection_service.py

# LLM分析テスト
python modules/llm_analysis/tests/test_llm_analyzer.py
```

## 📊 システム機能詳細

### 三層ゲートシステム詳細

**Gate 1: トレンド分析**:
- **D1分析**: 日足レベルでの長期トレンド判定
- **H4分析**: 4時間足レベルでの中期トレンド確認
- **移動平均**: SMA20, SMA50, SMA200の関係性分析
- **トレンド強度**: 定量化されたトレンド強度スコア

**Gate 2: ゾーン分析**:
- **H1分析**: 1時間足レベルでの価格ゾーン特定
- **サポート・レジスタンス**: 重要価格レベルの自動検出
- **ブレイクアウト**: 価格レベルの突破可能性評価
- **ボリューム分析**: 価格変動の信頼性評価

**Gate 3: タイミング分析**:
- **M5分析**: 5分足レベルでのエントリータイミング
- **RSI分析**: 過買い・過売り状況の判定
- **MACD分析**: 短期シグナルの確認
- **リスク管理**: ストップロス・テイクプロフィット設定

### 統合AI分析エンジン

**AI分析機能**:
1. **通貨相関分析**: USD/JPY、EUR/USD、GBP/USD等の相関性分析
2. **テクニカル指標統合**: 複数指標の統合分析
3. **GPT-4分析**: OpenAI GPT-4による高度な市場分析
4. **シナリオ生成**: 市場シナリオとリスク評価
5. **推奨事項**: AIによる取引推奨事項

### ルールベース売買システム

**アクティブルール**:
- **pullback_buy**: 押し目買い（RSI ≤ 40, 価格 > EMA200）
- **reversal_sell**: 逆張り売り（RSI ≥ 70, 価格 < EMA200）
- **trend_follow_sell**: 下降トレンドフォロー売り
- **strong_downtrend_sell**: 強い下降トレンド売り（RSI 25-40）

## 📈 パフォーマンス & 制限

### システム性能

- **データ取得**: 5分間隔での安定取得
- **パターン検出**: リアルタイム検出（< 1秒）
- **AI分析**: 2時間間隔での統合分析（< 3分）
- **Discord配信**: < 3秒での自動配信
- **システム監視**: 30分間隔でのヘルスチェック

### 制限・制約

- **データソース**: Yahoo Finance（無料）
- **通貨ペア**: USD/JPYメイン、複数通貨相関分析対応
- **稼働時間**: 平日24時間（土日祝日は停止）
- **AI分析**: 平日8:00-2:00 JST
- **データベース**: PostgreSQL + TimescaleDB

## 🛡️ セキュリティ & 運用

### セキュリティ対策

- **環境変数**: APIキー・Webhook URLの安全な管理
- **ログ管理**: 自動ログローテーション
- **エラーハンドリング**: 包括的な例外処理
- **リソース監視**: メモリ・CPU使用率の監視
- **API制限管理**: 外部API呼び出しの制限管理

### 運用監視

- **ヘルスチェック**: 30分間隔
- **エラー監視**: 10分間隔・自動アラート
- **ログローテーション**: 自動・容量制限
- **パフォーマンス監視**: 定期的な性能レポート
- **AI分析監視**: 統合AI分析の実行状況監視

## 🔮 今後の拡張予定

### Phase 4 完了（2025年9月実装完了）✅

#### **モジュール化アーキテクチャ実装完了**

- **🏗️ モジュール化**: 9つの独立したモジュールによるマイクロサービス設計 ✅
- **📊 データ収集**: 高性能なデータ収集システム ✅
- **💾 データ永続化**: TimescaleDBによる時系列データ最適化 ✅
- **🤖 LLM分析**: 統合AI分析システム ✅
- **📈 経済指標**: 複数プロバイダー対応の経済指標収集 ✅
- **⚡ レート制限**: 統合レート制限管理システム ✅
- **📅 スケジューラー**: 市場時間対応のインテリジェントスケジューリング ✅
- **🔔 通知**: Discord統合通知システム ✅
- **📊 モニタリング**: Prometheus + Grafana統合監視 ✅

### Phase 5 計画（2025年予定）

- **Web UI**: ダッシュボード・リアルタイム表示
- **モバイル対応**: スマートフォン最適化
- **クラウド展開**: AWS/Azure本格展開
- **リアルタイムAI**: リアルタイムAI分析機能

### 短期計画

- **追加パターン検出**: より多くの為替パターン
- **複数通貨ペア**: EUR/USD、GBP/USD等への拡張
- **機械学習**: 履歴データ学習による予測精度向上
- **AI分析強化**: より詳細な市場分析機能

### 中期計画

- **Web UI**: ダッシュボード・リアルタイム表示
- **モバイル対応**: スマートフォン最適化
- **クラウド展開**: AWS/Azure本格展開
- **リアルタイムAI**: リアルタイムAI分析機能

### 長期計画

- **高度AI分析**: GPT-4統合による高度な分析
- **ポートフォリオ管理**: 複数通貨ペア統合管理
- **自動売買**: パターン検出による自動売買機能
- **予測モデル**: 機械学習による予測モデル構築

## 📞 サポート

### トラブルシューティング

**よくある問題**:

1. **Discord通知失敗**
   ```bash
   # Webhook URL確認
   echo $DISCORD_WEBHOOK_URL
   # テスト実行
   python modules/llm_analysis/tests/test_discord_notifier.py
   ```

2. **AI分析失敗**
   ```bash
   # OpenAI API Key確認
   echo $OPENAI_API_KEY
   # LLM分析テスト
   python modules/llm_analysis/tests/test_llm_analyzer.py
   ```

3. **データベース接続エラー**
   ```bash
   # PostgreSQL接続確認
   python modules/data_persistence/tests/test_database_connection.py
   # データベース初期化
   python modules/data_persistence/core/database/database_initializer.py
   ```

4. **データ収集エラー**
   ```bash
   # データ収集テスト
   python modules/data_collection/tests/test_data_collection_service.py
   # Yahoo Finance接続確認
   python modules/data_collection/tests/test_yahoo_finance_provider.py
   ```

### ログ分析

```bash
# エラーパターン検索
grep -i "error\|failed\|exception" logs/*.log

# パフォーマンス分析
grep "実行時間\|execution time" logs/*.log

# システム監視ログ確認
tail -f logs/data_collection_daemon.log
tail -f logs/three_gate_system.log
```

## 🚀 システム最適化完了（2025年9月23日）

### 📊 最適化成果

#### **モジュール化アーキテクチャ実装完了**

- **🏗️ アーキテクチャ**: 9つの独立したモジュールによるマイクロサービス設計
- **📊 データ収集**: 高性能な非同期データ収集システム
- **💾 データ永続化**: TimescaleDBによる時系列データ最適化
- **🤖 LLM分析**: 統合AI分析システムと三層ゲートシステム
- **📈 経済指標**: 複数プロバイダー対応の経済指標収集
- **⚡ レート制限**: 統合レート制限管理システム
- **📅 スケジューラー**: 市場時間対応のインテリジェントスケジューリング
- **🔔 通知**: Discord統合通知システム
- **📊 モニタリング**: Prometheus + Grafana統合監視

#### **実装完了機能**

- **統合システム**: 全モジュールの統合と連携
- **イベント駆動**: データ収集完了時の自動分析実行
- **三層ゲート**: D1/H4（トレンド）、H1（ゾーン）、M5（タイミング）の3段階分析
- **ルールベース売買**: 5つのアクティブルールによる自動シグナル生成
- **Discord通知**: リッチな埋め込みメッセージでの通知配信
- **リアルタイム監視**: 継続的監視ツールによるシステム状況の可視化

### 🎯 最適化後のシステム構成

#### **モジュール化されたアーキテクチャ**

- **`modules/data_collection/`**: データ収集モジュール
- **`modules/data_persistence/`**: データ永続化モジュール
- **`modules/llm_analysis/`**: LLM分析モジュール
- **`modules/economic_indicators/`**: 経済指標モジュール
- **`modules/rate_limiting/`**: レート制限モジュール
- **`modules/scheduler/`**: スケジューラーモジュール
- **`modules/notification/`**: 通知モジュール
- **`modules/monitoring/`**: モニタリングモジュール
- **`modules/risk_management/`**: リスク管理モジュール
- **`modules/signal_generation/`**: シグナル生成モジュール
- **`modules/ml_inference/`**: 機械学習推論モジュール

### 🔧 最適化効果

#### **開発効率の向上**

- **明確な構造**: モジュール化による直感的な構造
- **保守性**: 各モジュールの独立した管理
- **テスタビリティ**: モジュール単位でのテスト実行
- **拡張性**: 新機能の追加が容易

#### **本番稼働の最適化**

- **必要最小限の構成**: 本番稼働に必要なモジュールのみ
- **システム整合性**: モジュール間の適切な連携
- **パフォーマンス向上**: 各モジュールの最適化による高速化
- **スケーラビリティ**: モジュール単位でのスケーリング

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🙏 謝辞

- [Yahoo Finance](https://finance.yahoo.com/) - 無料金融データ
- [OpenAI](https://openai.com/) - GPT-4 AI分析
- [TA-Lib](https://ta-lib.org/) - テクニカル分析ライブラリ
- [PostgreSQL](https://www.postgresql.org/) - データベース
- [TimescaleDB](https://www.timescale.com/) - 時系列データ最適化
- [Discord](https://discord.com/) - 通知プラットフォーム

---

**🚀 Exchange Analytics USD/JPY パターン検出システム**

**モジュール化されたアーキテクチャ・24時間自動稼働・統合AI分析・Discord自動通知・三層ゲートシステム・本格運用対応**

**Phase 1完了**: 2025年8月11日 ✅  
**Phase 2完了**: 2025年8月12日 ✅  
**Phase 3完了**: 2025年8月14日 ✅  
**モジュール化完了**: 2025年9月23日 ✅  
**実装パターン**: 複数の為替パターン ✅  
**高度な分析機能**: 三層ゲートシステム・統合AI分析 ✅  
**モジュール化**: 9つの独立したモジュール ✅  
**システム最適化**: モジュール化アーキテクチャ実装完了 ✅  
**本番稼働最適化**: 必要最小限のモジュール構成 ✅  
**自動化**: 完全自動化実現 ✅  
**実際の市場データ検証**: 完了 ✅  
**ドキュメント**: 包括的ドキュメント整備完了 ✅