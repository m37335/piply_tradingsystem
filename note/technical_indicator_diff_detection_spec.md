# テクニカル指標差分検知機能 実装仕様書

**プロジェクト名**: Exchange Analytics System - テクニカル指標差分検知機能  
**作成日**: 2025 年 8 月 15 日  
**バージョン**: 1.0.0  
**目的**: テクニカル指標計算の効率化と重複回避のための差分検知機能の実装

## 📋 概要

### 背景

現在のテクニカル指標計算システムは、毎回全データを対象に計算を実行しているため、以下の課題がある：

- 既に計算済みのデータも再計算される
- 処理時間が長い
- リソースの無駄遣い
- 重複データの発生リスク

### 解決策

`price_data`テーブルに計算状態管理列を追加し、未計算データのみを対象とした効率的な計算システムを構築する。

### 目標

- 計算済みデータの重複回避
- 処理時間の大幅短縮
- 差分検知による効率的な計算
- 計算状況の可視化

## 🗄️ データベース設計

### 変更対象テーブル

**テーブル名**: `price_data`

### 追加列

```sql
-- 計算済みフラグ（デフォルト: FALSE）
ALTER TABLE price_data ADD COLUMN technical_indicators_calculated BOOLEAN DEFAULT FALSE;

-- 計算実行時刻
ALTER TABLE price_data ADD COLUMN technical_indicators_calculated_at TIMESTAMP WITH TIME ZONE;

-- 計算バージョン（将来の拡張用）
ALTER TABLE price_data ADD COLUMN technical_indicators_version INTEGER DEFAULT 0;
```

### インデックス

```sql
-- 差分検知用インデックス（高速化）
CREATE INDEX idx_price_data_calculated ON price_data(technical_indicators_calculated, timestamp);

-- 時間足別検索用インデックス
CREATE INDEX idx_price_data_calculated_timeframe ON price_data(technical_indicators_calculated, data_source, timestamp);
```

### 初期化 SQL

```sql
-- 既存データの初期化（全データを未計算状態に設定）
UPDATE price_data
SET technical_indicators_calculated = FALSE,
    technical_indicators_calculated_at = NULL,
    technical_indicators_version = 0
WHERE technical_indicators_calculated IS NULL;
```

## 🏗️ アーキテクチャ設計

### システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                   差分検知システム                          │
├─────────────────────────────────────────────────────────────┤
│  DiffDetectionService                                      │
│  ├── detect_calculation_differences()                      │
│  ├── get_uncalculated_data()                               │
│  └── update_calculation_flags()                            │
├─────────────────────────────────────────────────────────────┤
│  EnhancedUnifiedTechnicalCalculator (拡張)                │
│  ├── calculate_with_diff_detection()                       │
│  ├── calculate_for_uncalculated_data()                     │
│  └── mark_as_calculated()                                  │
├─────────────────────────────────────────────────────────────┤
│  TechnicalIndicatorDiffCalculator (新規)                   │
│  ├── calculate_differential_indicators()                   │
│  ├── validate_calculation_completeness()                   │
│  └── generate_diff_report()                                │
└─────────────────────────────────────────────────────────────┘
```

### クラス設計

#### 1. DiffDetectionService

**ファイル**: `src/infrastructure/database/services/diff_detection_service.py`

```python
class DiffDetectionService:
    """
    テクニカル指標計算の差分検知サービス

    責任:
    - 未計算データの検知
    - 差分計算対象の特定
    - 計算状態の管理
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.price_repo = PriceDataRepositoryImpl(session)

    async def detect_calculation_differences(self) -> Dict[str, int]:
        """
        各時間足の未計算データ件数を検知

        Returns:
            Dict[str, int]: 時間足別の未計算件数
        """

    async def get_uncalculated_data(
        self,
        timeframe: str,
        limit: Optional[int] = None
    ) -> List[PriceDataModel]:
        """
        指定時間足の未計算データを取得

        Args:
            timeframe: 時間足（"5m", "1h", "4h", "1d"）
            limit: 取得件数制限

        Returns:
            List[PriceDataModel]: 未計算データのリスト
        """

    async def update_calculation_flags(
        self,
        processed_data: List[PriceDataModel],
        version: int = 1
    ) -> bool:
        """
        計算完了フラグを更新

        Args:
            processed_data: 計算処理したデータのリスト
            version: 計算バージョン

        Returns:
            bool: 更新成功時True
        """

    async def get_calculation_status(self) -> Dict[str, Any]:
        """
        計算状況の統計を取得

        Returns:
            Dict[str, Any]: 計算状況の詳細
        """
```

#### 2. TechnicalIndicatorDiffCalculator

**ファイル**: `src/application/services/technical_indicator_diff_calculator.py`

```python
class TechnicalIndicatorDiffCalculator:
    """
    差分検知付きテクニカル指標計算サービス

    責任:
    - 差分検知と計算の統合
    - 効率的な計算実行
    - 計算結果の検証
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair = currency_pair
        self.calculator = None
        self.diff_service = None

    async def initialize(self):
        """初期化処理"""

    async def calculate_differential_indicators(
        self,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        差分検知付きテクニカル指標計算

        Args:
            limit: 各時間足の処理件数制限

        Returns:
            Dict[str, Any]: 計算結果の詳細
        """

    async def calculate_for_timeframe(
        self,
        timeframe: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        指定時間足の差分計算

        Args:
            timeframe: 時間足
            limit: 処理件数制限

        Returns:
            Dict[str, Any]: 計算結果
        """

    async def validate_calculation_completeness(self) -> bool:
        """
        計算完了の検証

        Returns:
            bool: 計算が完了している場合True
        """

    async def generate_diff_report(self) -> Dict[str, Any]:
        """
        差分計算レポートの生成

        Returns:
            Dict[str, Any]: 詳細レポート
        """
```

#### 3. EnhancedUnifiedTechnicalCalculator (拡張)

**ファイル**: `scripts/cron/enhanced_unified_technical_calculator.py`

```python
# 既存クラスに追加するメソッド

async def calculate_with_diff_detection(
    self,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    差分検知付きテクニカル指標計算

    Args:
        limit: 各時間足の処理件数制限

    Returns:
        Dict[str, Any]: 計算結果の詳細
    """

async def calculate_for_uncalculated_data(
    self,
    timeframe: str,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    未計算データのみを対象とした計算

    Args:
        timeframe: 時間足
        limit: 処理件数制限

    Returns:
        Dict[str, Any]: 計算結果
    """

async def mark_as_calculated(
    self,
    processed_data: List[PriceDataModel]
) -> bool:
    """
    計算完了フラグを更新

    Args:
        processed_data: 処理したデータのリスト

    Returns:
        bool: 更新成功時True
    """
```

## 📁 ファイル構成

### 新規作成ファイル

```
/app/
├── src/
│   ├── infrastructure/
│   │   └── database/
│   │       └── services/
│   │           └── diff_detection_service.py          # 新規
│   └── application/
│       └── services/
│           └── technical_indicator_diff_calculator.py # 新規
├── scripts/
│   └── cron/
│       ├── enhanced_unified_technical_calculator.py   # 拡張
│       └── test_technical_calculator.py               # 拡張
└── tests/
    └── unit/
        └── test_diff_detection_service.py             # 新規
```

### 変更対象ファイル

1. **`scripts/cron/enhanced_unified_technical_calculator.py`**

   - 差分検知機能の統合
   - 既存メソッドの拡張

2. **`scripts/cron/test_technical_calculator.py`**

   - 差分検知機能のテスト統合
   - 新しいオプションの追加

3. **`src/infrastructure/database/models/price_data_model.py`**

   - 新しい列の定義追加

4. **`src/infrastructure/database/repositories/price_data_repository_impl.py`**
   - 差分検知用クエリメソッドの追加

## 🔄 ワークフロー詳細

### 差分検知ワークフロー

```python
async def differential_calculation_workflow():
    """
    差分検知付きテクニカル指標計算の完全なワークフロー
    """

    # Step 1: 差分検知
    diff_service = DiffDetectionService(session)
    differences = await diff_service.detect_calculation_differences()

    # Step 2: 計算対象の特定
    for timeframe, count in differences.items():
        if count > 0:
            logger.info(f"📊 {timeframe}: {count}件の未計算データを検出")

    # Step 3: 差分計算実行
    calculator = TechnicalIndicatorDiffCalculator("USD/JPY")
    await calculator.initialize()

    results = await calculator.calculate_differential_indicators()

    # Step 4: 計算完了フラグ更新
    await calculator.mark_calculation_complete()

    # Step 5: 結果検証
    completeness = await calculator.validate_calculation_completeness()

    return results
```

### データフロー

```
1. 差分検知
   ↓
2. 未計算データ取得
   ↓
3. テクニカル指標計算
   ↓
4. 計算結果保存
   ↓
5. フラグ更新
   ↓
6. 完了検証
```

## 🎯 実装仕様

### 差分検知ロジック

```python
async def detect_calculation_differences(self) -> Dict[str, int]:
    """
    各時間足の未計算データ件数を検知
    """
    differences = {}

    # 各時間足のデータソースマッピング
    timeframe_sources = {
        "5m": ["yahoo_finance_5m_continuous", "yahoo_finance_5m_differential"],
        "1h": ["yahoo_finance_1h_differential"],
        "4h": ["yahoo_finance_4h_differential"],
        "1d": ["yahoo_finance_1d_differential"]
    }

    for timeframe, sources in timeframe_sources.items():
        # 未計算データの件数を取得
        count = await self._count_uncalculated_data(sources)
        differences[timeframe] = count

    return differences
```

### フラグ更新ロジック

```python
async def update_calculation_flags(
    self,
    processed_data: List[PriceDataModel],
    version: int = 1
) -> bool:
    """
    計算完了フラグを更新
    """
    try:
        current_time = datetime.now(pytz.timezone("Asia/Tokyo"))

        for data in processed_data:
            data.technical_indicators_calculated = True
            data.technical_indicators_calculated_at = current_time
            data.technical_indicators_version = version

        # バッチ更新
        await self.price_repo.update_batch(processed_data)

        logger.info(f"✅ 計算フラグ更新完了: {len(processed_data)}件")
        return True

    except Exception as e:
        logger.error(f"❌ 計算フラグ更新エラー: {e}")
        return False
```

## 📊 パフォーマンス仕様

### 処理時間目標

- **差分検知**: 1 秒以内
- **未計算データ取得**: 3 秒以内
- **フラグ更新**: 2 秒以内
- **全体処理時間**: 従来の 50%以下

### メモリ使用量目標

- **差分検知**: 10MB 以内
- **未計算データ取得**: 50MB 以内
- **フラグ更新**: 20MB 以内
- **合計メモリ使用量**: 100MB 以内

### データ処理量

- **初回実行**: 全データ（従来通り）
- **2 回目以降**: 新規データのみ（大幅削減）

## 🧪 テスト仕様

### 単体テスト

```python
class TestDiffDetectionService:
    """差分検知サービスのテスト"""

    async def test_detect_calculation_differences(self):
        """差分検知のテスト"""

    async def test_get_uncalculated_data(self):
        """未計算データ取得のテスト"""

    async def test_update_calculation_flags(self):
        """フラグ更新のテスト"""
```

### 統合テスト

```python
class TestTechnicalIndicatorDiffCalculator:
    """差分計算器の統合テスト"""

    async def test_calculate_differential_indicators(self):
        """差分計算の統合テスト"""

    async def test_calculation_completeness(self):
        """計算完了検証のテスト"""
```

### パフォーマンステスト

```python
class TestDiffDetectionPerformance:
    """パフォーマンステスト"""

    async def test_detection_speed(self):
        """検知速度のテスト"""

    async def test_memory_usage(self):
        """メモリ使用量のテスト"""
```

## 🔧 実装チェックリスト

### Phase 1: データベース拡張

- [ ] `price_data`テーブルに計算フラグ列を追加
- [ ] インデックスを作成
- [ ] 既存データの初期化
- [ ] データベースマイグレーションスクリプト作成

### Phase 2: 差分検知機能実装

- [ ] `DiffDetectionService`クラス作成
- [ ] `TechnicalIndicatorDiffCalculator`クラス作成
- [ ] 差分検知ロジック実装
- [ ] フラグ更新ロジック実装

### Phase 3: 既存システム統合

- [ ] `EnhancedUnifiedTechnicalCalculator`拡張
- [ ] `test_technical_calculator.py`拡張
- [ ] 新しいオプション追加（`--diff-only`）
- [ ] 既存機能との互換性確保

### Phase 4: テスト・検証

- [ ] 単体テスト作成・実行
- [ ] 統合テスト作成・実行
- [ ] パフォーマンステスト実行
- [ ] 本番環境での動作確認

## 🚀 使用方法

### 差分計算のみ実行

```bash
cd /app && source .env && PYTHONPATH=/app python scripts/cron/test_technical_calculator.py --diff-only
```

### 差分計算 + 制限付き

```bash
cd /app && source .env && PYTHONPATH=/app python scripts/cron/test_technical_calculator.py --diff-only --limit 100
```

### 従来の全件計算（互換性維持）

```bash
cd /app && source .env && PYTHONPATH=/app python scripts/cron/test_technical_calculator.py --full
```

## 📈 期待される効果

### パフォーマンス向上

- **初回実行**: 従来通り（全データ計算）
- **2 回目以降**: 処理時間 50%以上短縮
- **継続運用**: 新規データのみの効率的な計算

### 運用メリット

- **進捗管理**: 計算状況の可視化
- **エラー復旧**: 途中失敗時の再開が容易
- **監視機能**: 計算状況の監視が可能
- **リソース効率**: 不要な再計算の回避

---

_この実装仕様書は、テクニカル指標計算の効率化を目的として作成され、差分検知機能の詳細な実装指針を提供します。_
