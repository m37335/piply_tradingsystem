# パターン検出実装計画書_phase1 - ローソク足パターン（パターン7-9）

## 📋 Phase 1 概要

### 目的
- ローソク足パターン（パターン7-9）の実装
- 既存の6つのパターン検出器に加えて、新規ローソク足パターンを追加
- 各パターン実装後のテスト実行、Git更新、GitHub同期の自動化

### 実装期間
- **期間**: 1-2週間
- **対象パターン**: パターン7（つつみ足）、パターン8（赤三兵）、パターン9（引け坊主）

### 実装方針
- 段階的実装（パターン7 → パターン8 → パターン9）
- 各パターン実装後の即座テスト実行
- Gitコミット・プッシュの自動化
- 既存システムとの統合テスト

---

## 🏗️ パターン7: つつみ足検出

### 実装ファイル
- **メインファイル**: `src/infrastructure/analysis/pattern_detectors/engulfing_pattern_detector.py`
- **テストファイル**: `tests/unit/test_engulfing_pattern_detector.py`
- **統合テスト**: `tests/integration/test_phase1_patterns.py`

### クラス構造

```python
class EngulfingPatternDetector:
    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_7()
        self.utils = PatternUtils()
        self.min_body_ratio = 0.6  # 実体比率の最小値
        self.min_engulfing_ratio = 1.1  # 包み込み比率の最小値

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """つつみ足パターン検出"""
        pass

    def _detect_bullish_engulfing(self, price_data: pd.DataFrame) -> bool:
        """陽のつつみ足検出"""
        pass

    def _detect_bearish_engulfing(self, price_data: pd.DataFrame) -> bool:
        """陰のつつみ足検出"""
        pass

    def _calculate_engulfing_confidence(self, pattern_data: Dict) -> float:
        """つつみ足の信頼度計算"""
        pass

    def _validate_candlestick_data(self, price_data: pd.DataFrame) -> bool:
        """ローソク足データの妥当性チェック"""
        pass

    def _calculate_body_size(self, open_price: float, close_price: float) -> float:
        """実体サイズ計算"""
        pass

    def _calculate_wick_size(self, high: float, low: float, body_high: float, body_low: float) -> Dict[str, float]:
        """ヒゲサイズ計算"""
        pass
```

### 実装タスク
- [ ] クラス定義とメソッド実装
- [ ] 陽のつつみ足検出ロジック
- [ ] 陰のつつみ足検出ロジック
- [ ] 信頼度計算アルゴリズム
- [ ] データ妥当性チェック
- [ ] 単体テスト作成
- [ ] 統合テスト実行
- [ ] Gitコミット・プッシュ

### パターン特徴
- **陽のつつみ足**: 前の陰線を完全に包み込む陽線（買いシグナル）
- **陰のつつみ足**: 前の陽線を完全に包み込む陰線（売りシグナル）
- **信頼度**: 85-90%
- **実装難易度**: 低
- **優先度**: HIGH (85)

---

## 🏗️ パターン8: 赤三兵検出

### 実装ファイル
- **メインファイル**: `src/infrastructure/analysis/pattern_detectors/red_three_soldiers_detector.py`
- **テストファイル**: `tests/unit/test_red_three_soldiers_detector.py`

### クラス構造

```python
class RedThreeSoldiersDetector:
    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_8()
        self.utils = PatternUtils()
        self.min_body_ratio = 0.5  # 実体比率の最小値
        self.min_close_increase = 0.001  # 終値上昇の最小値

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """赤三兵パターン検出"""
        pass

    def _check_three_consecutive_bullish_candles(self, price_data: pd.DataFrame) -> bool:
        """3本連続陽線チェック"""
        pass

    def _check_higher_closes(self, price_data: pd.DataFrame) -> bool:
        """終値の高値更新チェック"""
        pass

    def _check_body_size_consistency(self, price_data: pd.DataFrame) -> bool:
        """実体サイズの一貫性チェック"""
        pass

    def _calculate_pattern_strength(self, price_data: pd.DataFrame) -> float:
        """パターン強度計算"""
        pass
```

### 実装タスク
- [ ] クラス定義とメソッド実装
- [ ] 3本連続陽線検出ロジック
- [ ] 終値高値更新チェック
- [ ] 実体サイズ一貫性チェック
- [ ] パターン強度計算
- [ ] 単体テスト作成
- [ ] 統合テスト実行
- [ ] Gitコミット・プッシュ

### パターン特徴
- 3本連続の陽線で終値が前の足より高く更新
- 強い上昇トレンドの開始を示唆
- **信頼度**: 80-85%
- **実装難易度**: 低
- **優先度**: HIGH (80)

---

## 🏗️ パターン9: 大陽線/大陰線引け坊主

### 実装ファイル
- **メインファイル**: `src/infrastructure/analysis/pattern_detectors/marubozu_detector.py`
- **テストファイル**: `tests/unit/test_marubozu_detector.py`

### クラス構造

```python
class MarubozuDetector:
    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_9()
        self.utils = PatternUtils()
        self.max_wick_ratio = 0.1  # ヒゲ比率の最大値
        self.min_body_ratio = 0.8  # 実体比率の最小値

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """引け坊主パターン検出"""
        pass

    def _detect_bullish_marubozu(self, price_data: pd.DataFrame) -> bool:
        """大陽線引け坊主検出"""
        pass

    def _detect_bearish_marubozu(self, price_data: pd.DataFrame) -> bool:
        """大陰線引け坊主検出"""
        pass

    def _check_wick_absence(self, high: float, low: float, open_price: float, close_price: float) -> bool:
        """ヒゲの欠如チェック"""
        pass

    def _calculate_marubozu_strength(self, price_data: pd.DataFrame) -> float:
        """引け坊主強度計算"""
        pass
```

### 実装タスク
- [ ] クラス定義とメソッド実装
- [ ] 大陽線引け坊主検出ロジック
- [ ] 大陰線引け坊主検出ロジック
- [ ] ヒゲ欠如チェック
- [ ] 引け坊主強度計算
- [ ] 単体テスト作成
- [ ] 統合テスト実行
- [ ] Gitコミット・プッシュ

### パターン特徴
- ヒゲがないか非常に短い大陽線/大陰線
- 非常に強い買い/売りの勢い
- **信頼度**: 75-80%
- **実装難易度**: 低
- **優先度**: MEDIUM (75)

---

## 🔧 共通実装コンポーネント

### 1. パターン定義拡張

#### ファイル: `src/domain/entities/notification_pattern.py`

```python
# Phase 1 パターン定義メソッド追加
@staticmethod
def create_pattern_7() -> 'NotificationPattern':
    """パターン7: つつみ足検出"""
    return NotificationPattern(
        pattern_number=7,
        name="つつみ足検出",
        description="前の足を完全に包み込むローソク足パターン",
        priority=PatternPriority.HIGH,
        conditions={
            'D1': ["陽のつつみ足", "陰のつつみ足"],
            'H4': ["陽のつつみ足", "陰のつつみ足"],
            'H1': ["陽のつつみ足", "陰のつつみ足"],
            'M5': ["陽のつつみ足", "陰のつつみ足"]
        },
        notification_title="🔄 つつみ足パターン検出",
        notification_color="#FF6B6B"
    )

@staticmethod
def create_pattern_8() -> 'NotificationPattern':
    """パターン8: 赤三兵検出"""
    return NotificationPattern(
        pattern_number=8,
        name="赤三兵検出",
        description="3本連続陽線による強い上昇トレンド",
        priority=PatternPriority.HIGH,
        conditions={
            'D1': ["3本連続陽線", "終値高値更新"],
            'H4': ["3本連続陽線", "終値高値更新"],
            'H1': ["3本連続陽線", "終値高値更新"],
            'M5': ["3本連続陽線", "終値高値更新"]
        },
        notification_title="🔴 赤三兵パターン検出",
        notification_color="#4ECDC4"
    )

@staticmethod
def create_pattern_9() -> 'NotificationPattern':
    """パターン9: 引け坊主検出"""
    return NotificationPattern(
        pattern_number=9,
        name="引け坊主検出",
        description="ヒゲのない強いローソク足パターン",
        priority=PatternPriority.MEDIUM,
        conditions={
            'D1': ["大陽線引け坊主", "大陰線引け坊主"],
            'H4': ["大陽線引け坊主", "大陰線引け坊主"],
            'H1': ["大陽線引け坊主", "大陰線引け坊主"],
            'M5': ["大陽線引け坊主", "大陰線引け坊主"]
        },
        notification_title="⚡ 引け坊主パターン検出",
        notification_color="#45B7D1"
    )
```

### 2. 分析エンジン拡張

#### ファイル: `src/infrastructure/analysis/notification_pattern_analyzer.py`

```python
# Phase 1 検出器の追加
self.detectors.update({
    7: EngulfingPatternDetector(),
    8: RedThreeSoldiersDetector(),
    9: MarubozuDetector()
})

# Phase 1 パターン定義の追加
self.patterns.update({
    7: NotificationPattern.create_pattern_7(),
    8: NotificationPattern.create_pattern_8(),
    9: NotificationPattern.create_pattern_9()
})
```

### 3. 通知テンプレート拡張

#### ファイル: `src/infrastructure/messaging/templates/pattern_templates.py`

```python
# Phase 1 パターン用テンプレート
PATTERN_TEMPLATES = {
    7: {
        'title': "🔄 つつみ足パターン検出",
        'color': "#FF6B6B",
        'description': "強い反転シグナルが検出されました"
    },
    8: {
        'title': "🔴 赤三兵パターン検出",
        'color': "#4ECDC4",
        'description': "強い上昇トレンドの開始を示唆"
    },
    9: {
        'title': "⚡ 引け坊主パターン検出",
        'color': "#45B7D1",
        'description': "非常に強い買い/売りシグナル"
    }
}
```

---

## 🧪 テスト戦略

### 1. 単体テスト

#### ファイル構造
```
test_structure:
  unit_tests:
    - "tests/unit/test_engulfing_pattern_detector.py"
    - "tests/unit/test_red_three_soldiers_detector.py"
    - "tests/unit/test_marubozu_detector.py"
```

#### テスト内容
- 各検出器の基本機能テスト
- エッジケーステスト
- エラーハンドリングテスト
- パフォーマンステスト

### 2. 統合テスト

#### ファイル構造
```
integration_tests:
  - "tests/integration/test_phase1_patterns.py"
```

#### テスト内容
- Phase 1 パターンの統合テスト
- 既存システムとの統合テスト
- データベース統合テスト
- 通知システム統合テスト

---

## 🔄 自動化スクリプト

### 1. Phase 1 実装自動化スクリプト

#### ファイル: `scripts/implement_phase1_pattern.py`

```python
def implement_phase1_pattern(pattern_number: int):
    """Phase 1 パターン実装を自動化"""
    # ファイル作成
    create_phase1_pattern_files(pattern_number)
    # テスト実行
    run_phase1_tests(pattern_number)
    # Git更新
    commit_and_push_phase1(pattern_number)

def create_phase1_pattern_files(pattern_number: int):
    """Phase 1 パターンファイル作成"""
    pass

def run_phase1_tests(pattern_number: int):
    """Phase 1 テスト実行"""
    command = f"python -m pytest tests/unit/test_pattern_{pattern_number}_detector.py -v"
    # テスト実行ロジック

def commit_and_push_phase1(pattern_number: int):
    """Phase 1 Gitコミット・プッシュ"""
    commands = [
        "git add .",
        f"git commit -m 'feat: Phase 1 パターン{pattern_number}実装完了'",
        "git push"
    ]
    # Git操作ロジック
```

### 2. Phase 1 実行スクリプト

#### ファイル: `scripts/run_phase1.py`

```python
PHASE1_PATTERNS = [7, 8, 9]

def run_phase1():
    """Phase 1 実行"""
    for pattern in PHASE1_PATTERNS:
        implement_phase1_pattern(pattern)
    run_phase1_integration_test()

def run_phase1_integration_test():
    """Phase 1 統合テスト実行"""
    command = "python -m pytest tests/integration/test_phase1_patterns.py -v"
    # 統合テスト実行ロジック
```

---

## 📊 実装スケジュール

### Week 1
- パターン7実装（つつみ足検出）
- パターン8実装（赤三兵検出）
- 各パターンの単体テスト

### Week 2
- パターン9実装（引け坊主検出）
- Phase 1 統合テスト
- 既存システムとの統合テスト
- ドキュメント更新

---

## 🎯 成功指標

### 技術指標
- **単体テスト通過率**: 100%
- **統合テスト通過率**: 100%
- **コードカバレッジ**: 90%以上
- **性能劣化**: 既存システムの5%以内

### 品質指標
- **バグ率**: 1%以下
- **コードレビュー通過率**: 100%
- **ドキュメント完成度**: 100%

### 運用指標
- **通知精度向上**: 既存比15%向上
- **システム安定性**: 99.9%稼働率維持
- **開発効率**: 自動化により60%向上

---

## ⚠️ リスク管理

### 技術リスク
- **性能劣化**: ローソク足パターン検出による性能劣化
  - **対策**: 効率的なアルゴリズム実装と性能監視
- **互換性問題**: 既存システムとの互換性問題
  - **対策**: 十分な統合テストと段階的実装

### 運用リスク
- **偽シグナル**: ローソク足パターンによる偽シグナル増加
  - **対策**: 信頼度閾値の調整と複数条件の組み合わせ
- **通知過多**: 通知過多
  - **対策**: 優先度フィルタリング強化

### スケジュールリスク
- **実装遅延**: 実装遅延
  - **対策**: バッファ時間の確保と自動化
- **品質低下**: 品質低下
  - **対策**: 自動テストの徹底とコードレビュー

---

## 📝 次のステップ

1. **Phase 1 開始**: ローソク足パターンの実装開始
2. **自動化スクリプト準備**: 実装・テスト・Git更新の自動化
3. **テスト環境構築**: 新パターンの検証環境準備
4. **監視システム強化**: パフォーマンス監視の強化
5. **ドキュメント更新**: 実装状況の継続的更新
6. **Phase 2 準備**: チャートパターン実装の準備
