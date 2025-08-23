# 🔄 継続処理システム統合設計書

**旧ファイル名**: `継続処理システム統合設計書_2025.md`  
**作成日**: 2025 年 1 月  
**プロジェクト**: Exchange Analytics System  
**設計対象**: UnifiedTechnicalCalculator を継続処理システムに統合する設計

## 🎯 設計目的

### 問題解決

- **既存システムの複雑性**: 複数のテクニカル指標計算サービスが分散している問題の解決
- **機能の重複**: TALibTechnicalIndicatorService と UnifiedTechnicalCalculator の機能重複の解消
- **保守性の向上**: 単一の統合されたテクニカル指標計算システムの確立
- **新機能の活用**: ストキャスティクス、ATR などの追加指標の活用

### システム概要

**統合アプローチ**: パターン A（完全置き換え型）による UnifiedTechnicalCalculator の継続処理システムへの統合
**統合対象**: TALibTechnicalIndicatorService を UnifiedTechnicalCalculator で完全置き換え
**新機能追加**: 既存の RSI、MACD、ボリンジャーバンドに加えて、ストキャスティクス、ATR を追加

## 🏗️ システムアーキテクチャ

### 統合前の構成

```
継続処理システム
├── ContinuousProcessingService
│   └── TALibTechnicalIndicatorService (置き換え対象)
├── ContinuousProcessingScheduler
│   └── TALibTechnicalIndicatorService (置き換え対象)
└── SystemInitializationManager
    └── TALibTechnicalIndicatorService (置き換え対象)
```

### 統合後の構成

```
継続処理システム
├── ContinuousProcessingService
│   └── UnifiedTechnicalCalculator (新規統合)
├── ContinuousProcessingScheduler
│   └── UnifiedTechnicalCalculator (新規統合)
└── SystemInitializationManager
    └── UnifiedTechnicalCalculator (新規統合)
```

### データフロー

#### 現在のデータフロー

```
5分足データ取得 → ContinuousProcessingService.process_5m_data()
    ↓
TALibTechnicalIndicatorService.calculate_and_save_all_indicators()
    ↓
データベース保存
```

#### 統合後のデータフロー

```
5分足データ取得 → ContinuousProcessingService.process_5m_data()
    ↓
UnifiedTechnicalCalculator.calculate_timeframe_indicators("M5")
    ↓
データベース保存（直接UnifiedTechnicalCalculatorが実行）
```

## 📋 統合コンポーネント詳細

### 1. UnifiedTechnicalCalculator

#### 基本情報

- **ファイル**: `scripts/cron/unified_technical_calculator.py`
- **責任**: TA-Lib を使用した高性能テクニカル指標計算
- **統合方式**: 完全置き換え型

#### 主要機能

```python
class UnifiedTechnicalCalculator:
    def __init__(self, currency_pair: str = "USD/JPY"):
        # TA-Lib設定
        self.indicators_config = {
            "RSI": {"period": 14, "overbought": 70, "oversold": 30},
            "MACD": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "BB": {"period": 20, "std_dev": 2},
            "SMA": {"periods": [5, 10, 20, 50, 100, 200]},
            "EMA": {"periods": [12, 26]},
            "STOCH": {"fastk_period": 14, "slowk_period": 3, "slowd_period": 3},
            "ATR": {"period": 14},
        }

        # 時間足設定
        self.timeframes = {
            "M5": {"description": "5分足", "days": 7},
            "H1": {"description": "1時間足", "days": 30},
            "H4": {"description": "4時間足", "days": 60},
            "D1": {"description": "日足", "days": 365},
        }

    async def calculate_all_indicators(self) -> Dict[str, int]:
        """全テクニカル指標を計算"""

    async def calculate_timeframe_indicators(self, timeframe: str) -> int:
        """特定時間足の指標を計算"""

    async def health_check(self) -> Dict[str, Any]:
        """健全性チェック（互換性のため）"""
```

#### 計算対象指標

1. **RSI**: 期間 14, オーバーブ ought/オーバーソールドレベル設定
2. **MACD**: 標準設定（12,26,9）
3. **ボリンジャーバンド**: 期間 20, 標準偏差 2
4. **移動平均線**: SMA（5,10,20,50,100,200 期間）、EMA（12,26 期間）
5. **ストキャスティクス**: 標準設定（14,3,3）
6. **ATR**: 期間 14

### 2. 統合ポイント詳細

#### 統合ポイント 1: ContinuousProcessingService

**現在の実装**

```python
class ContinuousProcessingService:
    def __init__(self, session: AsyncSession):
        self.technical_indicator_service = TALibTechnicalIndicatorService(session)
```

**統合後の実装**

```python
class ContinuousProcessingService:
    def __init__(self, session: AsyncSession):
        self.technical_indicator_service = UnifiedTechnicalCalculator("USD/JPY")
        self.session = session  # UnifiedTechnicalCalculatorに渡す必要あり
```

#### 統合ポイント 2: ContinuousProcessingScheduler

**現在の実装**

```python
class ContinuousProcessingScheduler:
    def __init__(self, session: AsyncSession):
        self.continuous_service = ContinuousProcessingService(session)
```

**統合後の実装**

```python
class ContinuousProcessingScheduler:
    def __init__(self, session: AsyncSession):
        self.continuous_service = ContinuousProcessingService(session)
        # UnifiedTechnicalCalculatorがContinuousProcessingService内で初期化される
```

#### 統合ポイント 3: SystemInitializationManager

**現在の実装**

```python
class SystemInitializationManager:
    def __init__(self, session: AsyncSession):
        self.continuous_service = ContinuousProcessingService(session)
```

**統合後の実装**

```python
class SystemInitializationManager:
    def __init__(self, session: AsyncSession):
        self.continuous_service = ContinuousProcessingService(session)
        # 間接的にUnifiedTechnicalCalculatorが統合される
```

## 🔧 インターフェース互換性

### 互換性を保つメソッド

#### 既存の TALibTechnicalIndicatorService

```python
class TALibTechnicalIndicatorService:
    async def calculate_and_save_all_indicators(self, timeframe: str) -> Dict[str, int]
    async def calculate_rsi(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def calculate_macd(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def calculate_bollinger_bands(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def health_check(self) -> Dict[str, Any]
```

#### UnifiedTechnicalCalculator（互換性を保つ）

```python
class UnifiedTechnicalCalculator:
    async def calculate_and_save_all_indicators(self, timeframe: str) -> Dict[str, int]
    async def calculate_rsi(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def calculate_macd(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def calculate_bollinger_bands(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def health_check(self) -> Dict[str, Any]

    # 追加機能
    async def calculate_stochastic(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
    async def calculate_atr(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
```

## 📊 設定統合

### 現在の設定

```python
# TALibTechnicalIndicatorService
self.timeframes = ["M5", "H1", "H4", "D1"]
self.currency_pair = "USD/JPY"
```

### 統合後の設定

```python
# UnifiedTechnicalCalculator
self.timeframes = {
    "M5": {"description": "5分足", "days": 7},
    "H1": {"description": "1時間足", "days": 30},
    "H4": {"description": "4時間足", "days": 60},
    "D1": {"description": "日足", "days": 365},
}
self.currency_pair = "USD/JPY"
```

## 🚀 移行戦略

### ステップ 1: 準備段階（1 日）

#### 1.1 インターフェース互換性の確保

- [ ] UnifiedTechnicalCalculator に既存メソッドの対応実装
- [ ] 戻り値の形式統一
- [ ] エラーハンドリングの統一

#### 1.2 テスト環境の準備

- [ ] テスト用データベースの準備
- [ ] 既存システムの動作確認
- [ ] 新システムの動作確認

### ステップ 2: 段階的置き換え（2 日）

#### 2.1 ContinuousProcessingService の置き換え

- [ ] 既存 TALibTechnicalIndicatorService の削除
- [ ] UnifiedTechnicalCalculator の統合
- [ ] 動作確認とテスト

#### 2.2 ContinuousProcessingScheduler の置き換え

- [ ] 間接的な統合の確認
- [ ] スケジューラー機能のテスト
- [ ] エラーハンドリングの確認

#### 2.3 SystemInitializationManager の置き換え

- [ ] 初期化処理の確認
- [ ] システムサイクルのテスト
- [ ] 健全性チェックの確認

### ステップ 3: 完全統合（1 日）

#### 3.1 最終テスト

- [ ] 全機能の統合テスト
- [ ] パフォーマンステスト
- [ ] エラーケースのテスト

#### 3.2 最適化

- [ ] パフォーマンスの調整
- [ ] メモリ使用量の最適化
- [ ] ログ出力の調整

#### 3.3 既存コードの削除

- [ ] TALibTechnicalIndicatorService の完全削除
- [ ] 不要なインポートの削除
- [ ] 設定ファイルの更新

## 📈 期待される効果

### パフォーマンス向上

- **計算速度**: TA-Lib による高速計算
- **メモリ効率**: 統合によるメモリ使用量の削減
- **データベース効率**: 直接保存による処理の簡素化

### 機能拡張

- **追加指標**: ストキャスティクス、ATR の追加
- **分析精度**: より多くの指標による分析精度の向上
- **柔軟性**: 新しい指標の追加が容易

### 保守性向上

- **コード統合**: 重複コードの削除
- **単一責任**: テクニカル指標計算の責任統一
- **テスト容易性**: 単一システムのテスト

## ⚠️ リスクと対策

### リスク 1: 移行時のデータ不整合

**対策**

- 移行前のデータバックアップ
- 段階的な移行によるリスク分散
- 詳細なログ出力による問題の早期発見

### リスク 2: パフォーマンス劣化

**対策**

- 移行前後のパフォーマンス比較
- 必要に応じた最適化の実施
- 監視システムによる継続的なパフォーマンス監視

### リスク 3: 既存機能の動作不良

**対策**

- 包括的なテストの実施
- ロールバック計画の準備
- 段階的な機能確認

## 📋 実装チェックリスト

### 準備段階

- [ ] UnifiedTechnicalCalculator のインターフェース互換性確認
- [ ] テスト環境の準備
- [ ] 既存システムの動作確認
- [ ] 新システムの動作確認

### 実装段階

- [ ] ContinuousProcessingService の統合
- [ ] ContinuousProcessingScheduler の統合
- [ ] SystemInitializationManager の統合
- [ ] 各段階での動作確認

### 完了段階

- [ ] 全機能の統合テスト
- [ ] パフォーマンステスト
- [ ] 既存コードの削除
- [ ] ドキュメントの更新

## 🎯 成功指標

### 技術指標

- **計算速度**: 既存比 20% 以上の向上
- **メモリ使用量**: 既存比 15% 以上の削減
- **エラー率**: 既存比以下を維持

### 機能指標

- **計算精度**: 既存と同等以上の精度を維持
- **新機能活用**: ストキャスティクス、ATR の正常動作
- **システム安定性**: 継続処理の安定動作

### 保守性指標

- **コード行数**: 重複コードの削除による 30% 以上の削減
- **テストカバレッジ**: 90% 以上のテストカバレッジ維持
- **ドキュメント整備**: 統合後のドキュメント更新完了

## 📚 参考資料

### 既存設計書

- `note/CLIデータベース初期化システム実装仕様書_2025.md`
- `note/implementation_status/multiframe_continuous_processing_design_2025.md`

### 実装ファイル

- `scripts/cron/unified_technical_calculator.py`
- `src/infrastructure/analysis/technical_indicators.py`
- `src/infrastructure/analysis/talib_technical_indicators.py`

### 関連コンポーネント

- `src/infrastructure/database/services/talib_technical_indicator_service.py`
- `src/infrastructure/schedulers/continuous_processing_scheduler.py`
- `src/infrastructure/database/services/continuous_processing_service.py`
