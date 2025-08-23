# 🔄 継続処理システム統合実装仕様書

**旧ファイル名**: `継続処理システム統合実装仕様書_2025.md`  
**作成日**: 2025 年 1 月  
**プロジェクト**: Exchange Analytics System  
**設計書**: `note/continuous_processing_system_integration_design_2025.md`  
**実装対象**: UnifiedTechnicalCalculator を継続処理システムに統合する具体的な実装

## 📋 概要

### 目的

- 設計書に基づく具体的な実装仕様の定義
- 依存関係にあるファイルやフォルダの明示
- 実装する必要があるクラスやメソッドの詳細設計
- 各コンポーネントの目的と機能の明確化

### 基本方針

- **完全置き換え型統合**: TALibTechnicalIndicatorService を UnifiedTechnicalCalculator で完全置き換え
- **インターフェース互換性**: 既存システムとの互換性を保つ
- **段階的実装**: リスクを最小化する段階的アプローチ
- **品質保証**: 包括的なテストとエラーハンドリング

## 🏗️ システム構成図

```
継続処理システム統合
├── 修正対象ファイル
│   ├── src/infrastructure/database/services/continuous_processing_service.py
│   ├── src/infrastructure/schedulers/continuous_processing_scheduler.py
│   └── src/infrastructure/database/services/system_initialization_manager.py
├── 統合対象ファイル
│   └── scripts/cron/unified_technical_calculator.py
├── 非使用対象ファイル
│   └── src/infrastructure/database/services/talib_technical_indicator_service.py
└── 新規作成ファイル
    ├── src/infrastructure/database/services/unified_technical_indicator_service.py
    └── tests/integration/test_unified_technical_integration.py
```

## 📁 ファイル詳細仕様

### 1. 修正対象ファイル

#### 1.1 `src/infrastructure/database/services/continuous_processing_service.py`

**修正目的**: TALibTechnicalIndicatorService を UnifiedTechnicalCalculator に置き換え

**依存関係**:

```
continuous_processing_service.py
├── unified_technical_calculator.py (新規統合)
├── price_data_model.py (既存)
├── technical_indicator_model.py (既存)
└── timeframe_aggregator_service.py (既存)
```

**修正内容**:

```python
# 修正前
from src.infrastructure.database.services.talib_technical_indicator_service import (
    TALibTechnicalIndicatorService,
)

class ContinuousProcessingService:
    def __init__(self, session: AsyncSession):
        self.technical_indicator_service = TALibTechnicalIndicatorService(session)

# 修正後
from scripts.cron.unified_technical_calculator import UnifiedTechnicalCalculator

class ContinuousProcessingService:
    def __init__(self, session: AsyncSession):
        self.technical_indicator_service = UnifiedTechnicalCalculator("USD/JPY")
        self.session = session
        # UnifiedTechnicalCalculator の初期化
        asyncio.create_task(self._initialize_unified_calculator())

    async def _initialize_unified_calculator(self):
        """UnifiedTechnicalCalculator の初期化"""
        await self.technical_indicator_service.initialize()
```

**修正メソッド**:

```python
async def process_5m_data(self, price_data: PriceDataModel) -> Dict[str, Any]:
    """
    5分足データ処理（修正版）

    修正内容:
    - TALibTechnicalIndicatorService の呼び出しを UnifiedTechnicalCalculator に変更
    - 新しいインターフェースに対応
    """
    try:
        # 既存の処理
        aggregation_result = await self.timeframe_aggregator.aggregate_timeframes(price_data)

        # 修正: UnifiedTechnicalCalculator を使用
        indicator_result = await self.technical_indicator_service.calculate_timeframe_indicators("M5")

        # 結果の統合
        result = {
            "aggregation": aggregation_result,
            "indicators": indicator_result,
            "processing_time": time.time() - start_time,
        }

        return result

    except Exception as e:
        logger.error(f"5分足データ処理エラー: {e}")
        raise
```

#### 1.2 `src/infrastructure/schedulers/continuous_processing_scheduler.py`

**修正目的**: 間接的な UnifiedTechnicalCalculator 統合の確認

**依存関係**:

```
continuous_processing_scheduler.py
├── continuous_processing_service.py (修正済み)
├── data_fetcher_service.py (既存)
└── unified_technical_calculator.py (間接的)
```

**修正内容**:

```python
class ContinuousProcessingScheduler:
    def __init__(self, session: AsyncSession):
        # 修正: ContinuousProcessingService が UnifiedTechnicalCalculator を使用
        self.continuous_service = ContinuousProcessingService(session)
        self.data_fetcher = DataFetcherService(session)

    async def run_single_cycle(self):
        """
        単一サイクル実行（修正版）

        修正内容:
        - UnifiedTechnicalCalculator の動作確認
        - エラーハンドリングの強化
        """
        try:
            logger.info("🔄 継続処理サイクル開始（UnifiedTechnicalCalculator統合版）")

            # データ取得
            result = await self._direct_fetch_data()

            # 修正: UnifiedTechnicalCalculator による処理
            if result:
                await self.continuous_service.process_5m_data(result)

            logger.info("✅ 継続処理サイクル完了（UnifiedTechnicalCalculator統合版）")
            return result

        except Exception as e:
            logger.error(f"❌ 継続処理サイクルエラー: {e}")
            raise
```

#### 1.3 `src/infrastructure/database/services/system_initialization_manager.py`

**修正目的**: 間接的な UnifiedTechnicalCalculator 統合の確認

**依存関係**:

```
system_initialization_manager.py
├── continuous_processing_service.py (修正済み)
├── initial_data_loader_service.py (既存)
└── unified_technical_calculator.py (間接的)
```

**修正内容**:

```python
class SystemInitializationManager:
    def __init__(self, session: AsyncSession):
        # 修正: ContinuousProcessingService が UnifiedTechnicalCalculator を使用
        self.continuous_service = ContinuousProcessingService(session)
        self.initial_loader = InitialDataLoaderService(session)
        self.monitor = ContinuousProcessingMonitor()

    async def run_system_cycle(self, force_reinitialize: bool = False) -> Dict[str, Any]:
        """
        システムサイクル実行（修正版）

        修正内容:
        - UnifiedTechnicalCalculator の統合確認
        - 新機能（ストキャスティクス、ATR）の活用
        """
        try:
            # 既存の処理
            if force_reinitialize or not await self.check_initialization_status():
                return await self.perform_initial_initialization()

            # 修正: UnifiedTechnicalCalculator による継続処理
            result = await self.continuous_service.process_5m_data(latest_data)

            return {
                "status": "success",
                "processing_time": result.get("processing_time", 0),
                "data_volume": result.get("data_volume", 0),
                "indicators_calculated": result.get("indicators", {}),
            }

        except Exception as e:
            logger.error(f"システムサイクルエラー: {e}")
            return {"status": "error", "error": str(e)}
```

### 2. 統合対象ファイル

#### 2.1 `scripts/cron/unified_technical_calculator.py`

**統合目的**: 既存の UnifiedTechnicalCalculator にインターフェース互換性を追加

**依存関係**:

```
unified_technical_calculator.py
├── price_data_model.py (既存)
├── technical_indicator_model.py (既存)
├── technical_indicator_repository_impl.py (既存)
└── database/connection.py (既存)
```

**追加メソッド**:

```python
class UnifiedTechnicalCalculator:
    # 既存のメソッドに加えて、互換性を保つメソッドを追加

    async def calculate_and_save_all_indicators(self, timeframe: str) -> Dict[str, int]:
        """
        既存インターフェースとの互換性を保つメソッド

        Args:
            timeframe: 時間足

        Returns:
            Dict[str, int]: 各指標の保存件数
        """
        try:
            # 既存の calculate_timeframe_indicators を呼び出し
            total_count = await self.calculate_timeframe_indicators(timeframe)

            return {
                "total": total_count,
                "timeframe": timeframe,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"calculate_and_save_all_indicators エラー: {e}")
            return {"error": str(e)}

    async def calculate_rsi(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        RSI計算（互換性メソッド）

        Args:
            data: 価格データ
            timeframe: 時間足

        Returns:
            Dict[str, Any]: RSI計算結果
        """
        try:
            # 既存の RSI 計算ロジックを使用
            rsi_values = talib.RSI(data["Close"].values, timeperiod=14)
            current_rsi = rsi_values[-1] if not np.isnan(rsi_values[-1]) else None

            return {
                "current_value": round(current_rsi, 2) if current_rsi else None,
                "timeframe": timeframe,
                "indicator": "RSI"
            }

        except Exception as e:
            logger.error(f"RSI計算エラー: {e}")
            return {"error": str(e)}

    async def calculate_macd(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        MACD計算（互換性メソッド）
        """
        # 同様の実装

    async def calculate_bollinger_bands(self, data: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
        """
        ボリンジャーバンド計算（互換性メソッド）
        """
        # 同様の実装

    async def health_check(self) -> Dict[str, Any]:
        """
        健全性チェック（互換性メソッド）

        Returns:
            Dict[str, Any]: 健全性チェック結果
        """
        try:
            # 基本的な健全性チェック
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(),
                "indicators_available": list(self.indicators_config.keys()),
                "timeframes_available": list(self.timeframes.keys()),
                "database_connection": "connected" if self.session else "disconnected"
            }

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }
```

### 3. 非使用対象ファイル

#### 3.1 `src/infrastructure/database/services/talib_technical_indicator_service.py`

**非使用理由**: UnifiedTechnicalCalculator に完全置き換え（削除は行わない）

**非使用前の確認事項**:

- [ ] 他のファイルからの参照がないことを確認
- [ ] 重要な機能が UnifiedTechnicalCalculator に移行されていることを確認
- [ ] テストケースが新しいシステムでカバーされていることを確認
- [ ] ファイルは保持し、使用しない状態にする

### 4. 新規作成ファイル

#### 4.1 `src/infrastructure/database/services/unified_technical_indicator_service.py`

**作成目的**: UnifiedTechnicalCalculator のサービス層ラッパー

**依存関係**:

```
unified_technical_indicator_service.py
├── unified_technical_calculator.py (既存)
├── technical_indicator_repository_impl.py (既存)
└── database/connection.py (既存)
```

**クラス設計**:

```python
"""
UnifiedTechnicalIndicatorService
UnifiedTechnicalCalculator のサービス層ラッパー

責任:
- UnifiedTechnicalCalculator の初期化と管理
- データベースセッションの管理
- エラーハンドリングとログ記録
- 既存システムとの互換性確保
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from scripts.cron.unified_technical_calculator import UnifiedTechnicalCalculator
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)

logger = logging.getLogger(__name__)


class UnifiedTechnicalIndicatorService:
    """
    UnifiedTechnicalCalculator のサービス層ラッパー
    """

    def __init__(self, session: AsyncSession, currency_pair: str = "USD/JPY"):
        self.session = session
        self.currency_pair = currency_pair
        self.calculator: Optional[UnifiedTechnicalCalculator] = None
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)

        # 初期化状態
        self.is_initialized = False
        self.initialization_error = None

    async def initialize(self) -> bool:
        """
        サービスを初期化

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            logger.info("UnifiedTechnicalIndicatorService 初期化開始")

            # UnifiedTechnicalCalculator の初期化
            self.calculator = UnifiedTechnicalCalculator(self.currency_pair)
            await self.calculator.initialize()

            self.is_initialized = True
            logger.info("UnifiedTechnicalIndicatorService 初期化完了")
            return True

        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"UnifiedTechnicalIndicatorService 初期化エラー: {e}")
            return False

    async def calculate_and_save_all_indicators(self, timeframe: str) -> Dict[str, int]:
        """
        全テクニカル指標を計算して保存

        Args:
            timeframe: 時間足

        Returns:
            Dict[str, int]: 各指標の保存件数
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_timeframe_indicators(timeframe)

        except Exception as e:
            logger.error(f"calculate_and_save_all_indicators エラー: {e}")
            return {"error": str(e)}

    async def calculate_rsi(self, data, timeframe: str) -> Dict[str, Any]:
        """
        RSI計算（互換性メソッド）
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_rsi(data, timeframe)

        except Exception as e:
            logger.error(f"RSI計算エラー: {e}")
            return {"error": str(e)}

    async def calculate_macd(self, data, timeframe: str) -> Dict[str, Any]:
        """
        MACD計算（互換性メソッド）
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_macd(data, timeframe)

        except Exception as e:
            logger.error(f"MACD計算エラー: {e}")
            return {"error": str(e)}

    async def calculate_bollinger_bands(self, data, timeframe: str) -> Dict[str, Any]:
        """
        ボリンジャーバンド計算（互換性メソッド）
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_bollinger_bands(data, timeframe)

        except Exception as e:
            logger.error(f"ボリンジャーバンド計算エラー: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        健全性チェック

        Returns:
            Dict[str, Any]: 健全性チェック結果
        """
        try:
            if not self.is_initialized:
                return {
                    "status": "uninitialized",
                    "error": "サービスが初期化されていません",
                    "timestamp": datetime.now()
                }

            # 基本的な健全性チェック
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(),
                "service_type": "UnifiedTechnicalIndicatorService",
                "currency_pair": self.currency_pair,
                "calculator_initialized": self.calculator is not None,
                "session_active": self.session is not None
            }

            # 計算機の健全性チェック
            if self.calculator:
                calculator_health = await self.calculator.health_check()
                health_status["calculator_health"] = calculator_health

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def cleanup(self):
        """
        リソースのクリーンアップ
        """
        try:
            if self.calculator:
                await self.calculator.cleanup()
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
```

#### 4.2 `tests/integration/test_unified_technical_integration.py`

**作成目的**: 統合テストの実装

**依存関係**:

```
test_unified_technical_integration.py
├── unified_technical_indicator_service.py (新規)
├── continuous_processing_service.py (修正済み)
├── continuous_processing_scheduler.py (修正済み)
└── system_initialization_manager.py (修正済み)
```

**テストクラス設計**:

```python
"""
UnifiedTechnicalCalculator 統合テスト

テスト対象:
- UnifiedTechnicalIndicatorService の初期化と動作
- ContinuousProcessingService との統合
- ContinuousProcessingScheduler との統合
- SystemInitializationManager との統合
- エラーハンドリングとロールバック機能
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from src.infrastructure.database.services.unified_technical_indicator_service import (
    UnifiedTechnicalIndicatorService,
)
from src.infrastructure.database.services.continuous_processing_service import (
    ContinuousProcessingService,
)
from src.infrastructure.schedulers.continuous_processing_scheduler import (
    ContinuousProcessingScheduler,
)
from src.infrastructure.database.services.system_initialization_manager import (
    SystemInitializationManager,
)


class TestUnifiedTechnicalIntegration:
    """UnifiedTechnicalCalculator 統合テストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        return AsyncMock()

    @pytest.fixture
    def mock_unified_calculator(self):
        """モックUnifiedTechnicalCalculator"""
        mock = AsyncMock()
        mock.calculate_timeframe_indicators.return_value = {
            "RSI": 10,
            "MACD": 5,
            "BB": 8,
            "STOCH": 6,
            "ATR": 4
        }
        mock.health_check.return_value = {"status": "healthy"}
        return mock

    @pytest.fixture
    def unified_service(self, mock_session):
        """UnifiedTechnicalIndicatorService インスタンス"""
        return UnifiedTechnicalIndicatorService(mock_session, "USD/JPY")

    @pytest.fixture
    def continuous_service(self, mock_session):
        """ContinuousProcessingService インスタンス"""
        return ContinuousProcessingService(mock_session)

    @pytest.fixture
    def scheduler(self, mock_session):
        """ContinuousProcessingScheduler インスタンス"""
        return ContinuousProcessingScheduler(mock_session)

    @pytest.fixture
    def init_manager(self, mock_session):
        """SystemInitializationManager インスタンス"""
        return SystemInitializationManager(mock_session)

    async def test_unified_service_initialization(self, unified_service):
        """UnifiedTechnicalIndicatorService の初期化テスト"""
        with patch('scripts.cron.unified_technical_calculator.UnifiedTechnicalCalculator') as mock_calc:
            mock_calc.return_value.initialize = AsyncMock(return_value=True)

            result = await unified_service.initialize()

            assert result is True
            assert unified_service.is_initialized is True
            assert unified_service.calculator is not None

    async def test_calculate_and_save_all_indicators(self, unified_service, mock_unified_calculator):
        """全指標計算テスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        result = await unified_service.calculate_and_save_all_indicators("M5")

        assert "RSI" in result
        assert "MACD" in result
        assert "BB" in result
        assert "STOCH" in result
        assert "ATR" in result

    async def test_continuous_service_integration(self, continuous_service):
        """ContinuousProcessingService 統合テスト"""
        # 統合後の動作確認
        assert hasattr(continuous_service, 'technical_indicator_service')
        assert continuous_service.technical_indicator_service is not None

    async def test_scheduler_integration(self, scheduler):
        """ContinuousProcessingScheduler 統合テスト"""
        # 間接的な統合確認
        assert hasattr(scheduler, 'continuous_service')
        assert scheduler.continuous_service is not None

    async def test_init_manager_integration(self, init_manager):
        """SystemInitializationManager 統合テスト"""
        # 間接的な統合確認
        assert hasattr(init_manager, 'continuous_service')
        assert init_manager.continuous_service is not None

    async def test_health_check(self, unified_service, mock_unified_calculator):
        """健全性チェックテスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        health = await unified_service.health_check()

        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert health["service_type"] == "UnifiedTechnicalIndicatorService"

    async def test_error_handling(self, unified_service):
        """エラーハンドリングテスト"""
        # 初期化前のエラーハンドリング
        result = await unified_service.calculate_and_save_all_indicators("M5")
        assert "error" in result

        # 健全性チェックのエラーハンドリング
        health = await unified_service.health_check()
        assert health["status"] == "uninitialized"
```

## 🔧 実装順序と依存関係

### 実装フェーズ 1: 基盤準備（1 日）

#### 1.1 UnifiedTechnicalCalculator の拡張

- [ ] `scripts/cron/unified_technical_calculator.py` に互換性メソッドを追加
- [ ] `calculate_and_save_all_indicators()` メソッドの実装
- [ ] `calculate_rsi()`, `calculate_macd()`, `calculate_bollinger_bands()` メソッドの実装
- [ ] `health_check()` メソッドの実装

#### 1.2 UnifiedTechnicalIndicatorService の作成

- [ ] `src/infrastructure/database/services/unified_technical_indicator_service.py` の作成
- [ ] サービス層ラッパーの実装
- [ ] 初期化とエラーハンドリングの実装

### 実装フェーズ 2: 統合実装（2 日）

#### 2.1 ContinuousProcessingService の修正

- [ ] `src/infrastructure/database/services/continuous_processing_service.py` の修正
- [ ] TALibTechnicalIndicatorService の削除
- [ ] UnifiedTechnicalCalculator の統合
- [ ] 初期化処理の追加

#### 2.2 ContinuousProcessingScheduler の修正

- [ ] `src/infrastructure/schedulers/continuous_processing_scheduler.py` の修正
- [ ] 間接的な統合の確認
- [ ] エラーハンドリングの強化

#### 2.3 SystemInitializationManager の修正

- [ ] `src/infrastructure/database/services/system_initialization_manager.py` の修正
- [ ] 間接的な統合の確認
- [ ] 新機能の活用

### 実装フェーズ 3: テストと最適化（1 日）

#### 3.1 統合テストの実装

- [ ] `tests/integration/test_unified_technical_integration.py` の作成
- [ ] 各コンポーネントの統合テスト
- [ ] エラーハンドリングのテスト

#### 3.2 最適化と調整

- [ ] パフォーマンスの調整
- [ ] メモリ使用量の最適化
- [ ] ログ出力の調整

#### 3.3 既存コードの非使用化

- [ ] `src/infrastructure/database/services/talib_technical_indicator_service.py` の非使用化
- [ ] 不要なインポートの削除
- [ ] 設定ファイルの更新

## 📊 実装チェックリスト

### フェーズ 1: 基盤準備

- [ ] UnifiedTechnicalCalculator の互換性メソッド追加
- [ ] UnifiedTechnicalIndicatorService の作成
- [ ] 基本テストの実装

### フェーズ 2: 統合実装

- [ ] ContinuousProcessingService の修正
- [ ] ContinuousProcessingScheduler の修正
- [ ] SystemInitializationManager の修正
- [ ] 各段階での動作確認

### フェーズ 3: テストと最適化

- [ ] 統合テストの実装
- [ ] パフォーマンステスト
- [ ] 既存コードの非使用化
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

### 設計書

- `note/continuous_processing_system_integration_design_2025.md`

### 実装ファイル

- `scripts/cron/unified_technical_calculator.py`
- `src/infrastructure/database/services/continuous_processing_service.py`
- `src/infrastructure/schedulers/continuous_processing_scheduler.py`
- `src/infrastructure/database/services/system_initialization_manager.py`

### 関連コンポーネント

- `src/infrastructure/database/models/price_data_model.py`
- `src/infrastructure/database/models/technical_indicator_model.py`
- `src/infrastructure/database/repositories/technical_indicator_repository_impl.py`
