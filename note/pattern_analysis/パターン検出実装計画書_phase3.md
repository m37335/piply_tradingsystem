# パターン検出実装計画書_phase3 - 高度なパターン（パターン13-14）

## 📋 Phase 3 概要

### 目的
- 高度なチャートパターン（パターン13-14）の実装
- より複雑で精度の高いパターン検出機能の追加
- 既存システムの高度化と精度向上

### 実装期間
- **期間**: 3-4週間
- **対象パターン**: パターン13（三尊天井/逆三尊）、パターン14（ウェッジパターン）

### 実装方針
- 段階的実装（パターン13 → パターン14）
- 高度なアルゴリズム実装
- 精度向上のための複数条件組み合わせ
- 既存システムとの統合テスト

---

## 🏗️ パターン13: 三尊天井/逆三尊検出

### 実装ファイル
- **メインファイル**: `src/infrastructure/analysis/pattern_detectors/three_buddhas_detector.py`
- **テストファイル**: `tests/unit/test_three_buddhas_detector.py`
- **統合テスト**: `tests/integration/test_phase3_patterns.py`

### クラス構造
```python
class ThreeBuddhasDetector:
    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_13()
        self.utils = PatternUtils()
        self.min_peak_distance = 8  # ピーク間の最小距離
        self.peak_tolerance = 0.012  # ピークの許容誤差（1.2%）
        self.middle_peak_ratio = 0.02  # 中央ピークの高さ比率（2%）
        self.neckline_tolerance = 0.006  # ネックラインの許容誤差（0.6%）
    
    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """三尊天井/逆三尊パターン検出"""
        pass
    
    def _detect_three_buddhas_top(self, price_data: pd.DataFrame) -> bool:
        """三尊天井検出"""
        pass
    
    def _detect_inverse_three_buddhas(self, price_data: pd.DataFrame) -> bool:
        """逆三尊検出"""
        pass
    
    def _find_three_peaks_with_middle_higher(self, price_data: pd.DataFrame) -> List[int]:
        """中央が高い3つのピーク検出"""
        pass
    
    def _find_three_peaks_with_middle_lower(self, price_data: pd.DataFrame) -> List[int]:
        """中央が低い3つのピーク検出"""
        pass
    
    def _validate_three_buddhas_pattern(self, price_data: pd.DataFrame, peaks: List[int]) -> bool:
        """三尊パターン検証"""
        pass
    
    def _calculate_three_buddhas_confidence(self, pattern_data: Dict) -> float:
        """三尊パターン信頼度計算"""
        pass
```

### 実装タスク
- [ ] クラス定義とメソッド実装
- [ ] 三尊天井検出ロジック
- [ ] 逆三尊検出ロジック
- [ ] 3つのピーク検出アルゴリズム（中央高/低）
- [ ] 三尊パターン検証
- [ ] 信頼度計算アルゴリズム
- [ ] 単体テスト作成
- [ ] 統合テスト実行
- [ ] Gitコミット・プッシュ

### パターン特徴
- **三尊天井**: 中央が最も高い3つの高値で形成される売りシグナル
- **逆三尊**: 中央が最も低い3つの安値で形成される買いシグナル
- **信頼度**: 90-95%
- **実装難易度**: 高
- **優先度**: HIGH (90)

---

## 🏗️ パターン14: ウェッジパターン検出

### 実装ファイル
- **メインファイル**: `src/infrastructure/analysis/pattern_detectors/wedge_pattern_detector.py`
- **テストファイル**: `tests/unit/test_wedge_pattern_detector.py`

### クラス構造
```python
class WedgePatternDetector:
    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_14()
        self.utils = PatternUtils()
        self.min_wedge_length = 10  # ウェッジの最小長さ
        self.max_wedge_length = 50  # ウェッジの最大長さ
        self.angle_tolerance = 15  # 角度の許容誤差（度）
        self.convergence_threshold = 0.8  # 収束判定閾値
    
    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """ウェッジパターン検出"""
        pass
    
    def _detect_rising_wedge(self, price_data: pd.DataFrame) -> bool:
        """上昇ウェッジ検出"""
        pass
    
    def _detect_falling_wedge(self, price_data: pd.DataFrame) -> bool:
        """下降ウェッジ検出"""
        pass
    
    def _identify_wedge_lines(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """ウェッジライン識別"""
        pass
    
    def _calculate_wedge_angle(self, line1: List[float], line2: List[float]) -> float:
        """ウェッジ角度計算"""
        pass
    
    def _validate_wedge_breakout(self, price_data: pd.DataFrame, wedge_data: Dict) -> bool:
        """ウェッジブレイクアウト検証"""
        pass
    
    def _calculate_wedge_confidence(self, pattern_data: Dict) -> float:
        """ウェッジパターン信頼度計算"""
        pass
```

### 実装タスク
- [ ] クラス定義とメソッド実装
- [ ] 上昇ウェッジ検出ロジック
- [ ] 下降ウェッジ検出ロジック
- [ ] ウェッジライン識別
- [ ] 角度計算アルゴリズム
- [ ] ブレイクアウト検証
- [ ] 信頼度計算アルゴリズム
- [ ] 単体テスト作成
- [ ] 統合テスト実行
- [ ] Gitコミット・プッシュ

### パターン特徴
- **上昇ウェッジ**: 上昇トレンド後の収束パターン（売りシグナル）
- **下降ウェッジ**: 下降トレンド後の収束パターン（買いシグナル）
- **信頼度**: 85-90%
- **実装難易度**: 高
- **優先度**: HIGH (85)

---

## 🔧 共通実装コンポーネント

### 1. パターン定義更新

#### ファイル: `src/domain/entities/notification_pattern.py`

```python
@classmethod
def create_pattern_13(cls) -> "NotificationPattern":
    """パターン13: 三尊天井/逆三尊検出を作成"""
    return cls(
        pattern_number=13,
        name="三尊天井/逆三尊検出",
        description="中央が突出した3つのピーク/ボトムで形成される強力なパターン",
        priority=PatternPriority.HIGH,
        conditions={
            "D1": ["三尊天井", "逆三尊"],
            "H4": ["三尊天井", "逆三尊"],
            "H1": ["三尊天井", "逆三尊"],
            "M5": ["三尊天井", "逆三尊"],
        },
        notification_title="🔄 三尊天井/逆三尊パターン検出",
        notification_color="0x800080",
        take_profit="+150pips",
        stop_loss="-75pips",
        confidence="高（90-95%）",
    )

@classmethod
def create_pattern_14(cls) -> "NotificationPattern":
    """パターン14: ウェッジパターン検出を作成"""
    return cls(
        pattern_number=14,
        name="ウェッジパターン検出",
        description="収束するトレンドラインで形成されるパターン",
        priority=PatternPriority.HIGH,
        conditions={
            "D1": ["上昇ウェッジ", "下降ウェッジ"],
            "H4": ["上昇ウェッジ", "下降ウェッジ"],
            "H1": ["上昇ウェッジ", "下降ウェッジ"],
            "M5": ["上昇ウェッジ", "下降ウェッジ"],
        },
        notification_title="🔄 ウェッジパターン検出",
        notification_color="0xFF8C00",
        take_profit="+120pips",
        stop_loss="-60pips",
        confidence="高（85-90%）",
    )
```

### 2. 分析エンジン統合

#### ファイル: `src/infrastructure/analysis/notification_pattern_analyzer.py`

```python
from .pattern_detectors.three_buddhas_detector import ThreeBuddhasDetector
from .pattern_detectors.wedge_pattern_detector import WedgePatternDetector

def __init__(self):
    # 既存の検出器
    self.detectors = {
        # ... 既存の検出器 ...
        
        # Phase 3 新規検出器
        "ThreeBuddhasDetector": ThreeBuddhasDetector(),
        "WedgePatternDetector": WedgePatternDetector(),
    }
    
    # パターン定義
    self.patterns = {
        # ... 既存のパターン ...
        
        # Phase 3 新規パターン
        13: NotificationPattern.create_pattern_13(),
        14: NotificationPattern.create_pattern_14(),
    }
```

### 3. モジュール初期化更新

#### ファイル: `src/infrastructure/analysis/pattern_detectors/__init__.py`

```python
"""
パターン検出器モジュール

14個のパターン検出器を提供
"""

from .three_buddhas_detector import ThreeBuddhasDetector
from .wedge_pattern_detector import WedgePatternDetector

__all__ = [
    # 既存の検出器
    "EngulfingPatternDetector",
    "RedThreeSoldiersDetector", 
    "MarubozuDetector",
    "DoubleTopBottomDetector",
    "TripleTopBottomDetector",
    "FlagPatternDetector",
    
    # Phase 3 新規検出器
    "ThreeBuddhasDetector",
    "WedgePatternDetector",
]
```

---

## 🧪 テスト戦略

### 単体テスト

#### 三尊天井/逆三尊検出器テスト
- 三尊天井検出テスト
- 逆三尊検出テスト
- 3つのピーク検出テスト（中央高/低）
- 三尊パターン検証テスト
- 信頼度計算テスト
- エッジケーステスト

#### ウェッジパターン検出器テスト
- 上昇ウェッジ検出テスト
- 下降ウェッジ検出テスト
- ウェッジライン識別テスト
- 角度計算テスト
- ブレイクアウト検証テスト
- 信頼度計算テスト

### 統合テスト

#### Phase 3統合テスト
- 全パターンの統合テスト
- 検出器の状態確認
- エラーハンドリング
- パフォーマンステスト

---

## 🚀 自動化スクリプト

### 1. Phase 3 自動化スクリプト

#### ファイル: `scripts/run_phase3.py`

```python
PHASE3_PATTERNS = [13, 14]

PATTERN_INFO = {
    13: {
        "name": "三尊天井/逆三尊検出",
        "detector_file": "src/infrastructure/analysis/pattern_detectors/three_buddhas_detector.py",
        "test_file": "tests/unit/test_three_buddhas_detector.py",
        "class_name": "ThreeBuddhasDetector"
    },
    14: {
        "name": "ウェッジパターン検出",
        "detector_file": "src/infrastructure/analysis/pattern_detectors/wedge_pattern_detector.py",
        "test_file": "tests/unit/test_wedge_pattern_detector.py",
        "class_name": "WedgePatternDetector"
    }
}

def run_phase3():
    """Phase 3 実行"""
    for pattern in PHASE3_PATTERNS:
        implement_phase3_pattern(pattern)
    run_phase3_integration_test()
```

---

## 📊 実装スケジュール

### Week 1-2
- パターン13実装（三尊天井/逆三尊検出）
- パターン13の単体テスト
- アルゴリズム最適化

### Week 3-4
- パターン14実装（ウェッジパターン検出）
- パターン14の単体テスト
- Phase 3 統合テスト

### Week 5
- 既存システムとの統合テスト
- パフォーマンス最適化
- ドキュメント更新

---

## 🎯 成功指標

### 技術指標
- **単体テスト通過率**: 100%
- **統合テスト通過率**: 100%
- **コードカバレッジ**: 95%以上
- **性能劣化**: 既存システムの3%以内

### 品質指標
- **バグ率**: 0.5%以下
- **コードレビュー通過率**: 100%
- **ドキュメント完成度**: 100%

### 運用指標
- **通知精度向上**: 既存比30%向上
- **システム安定性**: 99.95%稼働率維持
- **開発効率**: 自動化により80%向上

---

## ⚠️ リスク管理

### 技術リスク
- **複雑性**: 高度なパターン検出の複雑性
  - **対策**: 段階的実装と十分なテスト
- **性能影響**: 複雑なアルゴリズムによる性能劣化
  - **対策**: 効率的なアルゴリズム実装とキャッシュ活用

### 運用リスク
- **偽シグナル**: 高度なパターンによる偽シグナル
  - **対策**: 信頼度閾値の調整と複数条件の組み合わせ
- **検出遅延**: 複雑なパターンによる検出遅延
  - **対策**: 最適化されたアルゴリズムと並列処理

---

## 📝 次のステップ

1. **Phase 3 開始**: 高度なパターンの実装開始
2. **自動化スクリプト準備**: Phase 3用自動化スクリプト作成
3. **テスト環境構築**: 新パターンの検証環境準備
4. **監視システム強化**: パフォーマンス監視の強化
5. **ドキュメント更新**: 実装状況の継続的更新
6. **Phase 4 準備**: ライン分析パターン実装の準備

---

**作成日**: 2025年8月11日  
**作成者**: AI Assistant  
**ステータス**: 📋 **計画中**
