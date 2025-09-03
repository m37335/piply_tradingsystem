"""
プログレスバー管理モジュール（tqdm統一）

このモジュールは、EnhancedUnifiedTechnicalCalculatorで使用する
プログレスバー管理機能を提供します。tqdmライブラリを使用して
統一されたプログレス表示を実現します。

Author: EnhancedUnifiedTechnicalCalculator Team
Created: 2025-08-15
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ProgressManager:
    """
    プログレスバー管理クラス（tqdm統一）

    責任:
    - 複数レベルのプログレスバー管理
    - 時間足別・指標別の進捗表示
    - 詳細進捗とサマリー進捗の切り替え
    - エラーハンドリングとリソース管理

    Attributes:
        enable_progress (bool): プログレスバー表示の有効/無効
        tqdm_config (dict): tqdmの設定パラメータ
        progress_bars (dict): 管理中のプログレスバー
    """

    def __init__(
        self, 
        enable_progress: bool = True, 
        tqdm_config: Optional[Dict[str, Any]] = None
    ):
        """
        ProgressManagerを初期化

        Args:
            enable_progress: プログレスバー表示の有効/無効
            tqdm_config: tqdmの設定パラメータ
        """
        self.enable_progress = enable_progress
        self.tqdm_config = tqdm_config or {
            "ncols": 100,
            "bar_format": (
                "{desc}: {percentage:3.0f}%|{bar:25}| "
                "{n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
            ),
            "colour": "cyan",
            "leave": False,  # 完了後にプログレスバーを残さない
            "dynamic_ncols": False,  # 固定列幅で改行を防ぐ
            "ascii": False,  # Unicode文字を使用
            "smoothing": 0.3,  # スムージング効果
        }
        self.progress_bars: Dict[str, Any] = {}

    def start_timeframe_progress(
        self, timeframe: str, total_indicators: int
    ) -> Optional[Any]:
        """
        時間足別プログレス開始

        Args:
            timeframe: 時間足（例: "M5", "H1", "H4", "D1"）
            total_indicators: 計算する指標の総数

        Returns:
            プログレスバーオブジェクト（無効時はNone）
        """
        if not self.enable_progress:
            return None

        try:
            from tqdm import tqdm
            
            pbar = tqdm(
                total=total_indicators,
                desc=f"📊 {timeframe} 指標計算中",
                **self.tqdm_config
            )
            self.progress_bars[f"timeframe_{timeframe}"] = pbar
            logger.debug(f"時間足プログレス開始: {timeframe}")
            return pbar
            
        except ImportError:
            logger.warning("tqdmライブラリがインストールされていません。プログレスバーを無効化します。")
            self.enable_progress = False
            return None
        except Exception as e:
            logger.error(f"時間足プログレス開始エラー: {e}")
            return None

    def start_indicator_progress(self, indicator: str, total_steps: int) -> Optional[Any]:
        """
        指標別プログレス開始

        Args:
            indicator: 指標名（例: "RSI", "MACD", "BB"）
            total_steps: 処理ステップの総数

        Returns:
            プログレスバーオブジェクト（無効時はNone）
        """
        if not self.enable_progress:
            return None

        try:
            from tqdm import tqdm
            
            pbar = tqdm(
                total=total_steps,
                desc=f"🔍 {indicator} 処理中",
                **self.tqdm_config
            )
            self.progress_bars[f"indicator_{indicator}"] = pbar
            logger.debug(f"指標プログレス開始: {indicator}")
            return pbar
            
        except ImportError:
            logger.warning("tqdmライブラリがインストールされていません。プログレスバーを無効化します。")
            self.enable_progress = False
            return None
        except Exception as e:
            logger.error(f"指標プログレス開始エラー: {e}")
            return None

    def update_progress(
        self, 
        progress_id: Optional[Any], 
        advance: int = 1, 
        description: Optional[str] = None
    ) -> None:
        """
        プログレス更新

        Args:
            progress_id: プログレスバーオブジェクト
            advance: 進捗量
            description: 更新する説明文
        """
        if not self.enable_progress or progress_id is None:
            return

        try:
            if description:
                progress_id.set_description(description)
            progress_id.update(advance)
            
            # リアルタイム更新のためのフラッシュ
            if hasattr(progress_id, 'refresh'):
                progress_id.refresh()
            
        except Exception as e:
            logger.error(f"プログレス更新エラー: {e}")

    def close_progress(self, progress_id: Optional[Any]) -> None:
        """
        プログレス終了

        Args:
            progress_id: プログレスバーオブジェクト
        """
        if not self.enable_progress or progress_id is None:
            return

        try:
            # プログレスバーを確実に閉じる
            if hasattr(progress_id, 'close'):
                # 既に閉じられているかチェック
                if hasattr(progress_id, 'closed'):
                    if not progress_id.closed:
                        progress_id.close()
                        logger.debug("プログレスバーを閉じました")
                else:
                    # closed属性がない場合は直接close
                    progress_id.close()
                    logger.debug("プログレスバーを閉じました")
                    
        except Exception as e:
            logger.error(f"プログレスバー終了エラー: {e}")
                
        except Exception as e:
            logger.error(f"プログレス終了エラー: {e}")

    def close_all_progress(self) -> None:
        """全てのプログレスバーを閉じる"""
        for progress_id in self.progress_bars.values():
            self.close_progress(progress_id)
        self.progress_bars.clear()

    def __enter__(self):
        """コンテキストマネージャー開始"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        self.close_all_progress()
        
        if exc_type is not None:
            logger.error(f"ProgressManagerでエラーが発生: {exc_type.__name__}: {exc_val}")


@contextmanager
def create_progress_manager(enable_progress: bool = True, tqdm_config: Optional[Dict[str, Any]] = None):
    """
    プログレスマネージャーのコンテキストマネージャー

    Args:
        enable_progress: プログレスバー表示の有効/無効
        tqdm_config: tqdmの設定パラメータ

    Yields:
        ProgressManager: プログレス管理オブジェクト
    """
    manager = ProgressManager(enable_progress, tqdm_config)
    try:
        yield manager
    finally:
        manager.close_all_progress()
