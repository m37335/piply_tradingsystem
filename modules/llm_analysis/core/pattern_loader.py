#!/usr/bin/env python3
"""
パターン設定読み込みクラス

YAML形式の設定ファイルから三層ゲートのパターン設定を読み込み、
キャッシュ機能とホットリロード機能を提供します。
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PatternLoader:
    """パターン設定読み込みクラス"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初期化
        
        Args:
            config_dir: 設定ファイルディレクトリのパス
        """
        if Path(config_dir).is_absolute():
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path(__file__).parent.parent / config_dir
        self._patterns_cache = {}
        self._last_modified = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'loads': 0
        }
        self.logger = logging.getLogger(__name__)
        
        # 設定ディレクトリの存在確認
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"設定ディレクトリを作成しました: {self.config_dir}")
    
    def load_gate_patterns(self, gate_number: int) -> Dict[str, Any]:
        """
        指定されたゲートのパターン設定を読み込み
        
        Args:
            gate_number: ゲート番号（1, 2, 3）
            
        Returns:
            パターン設定の辞書
            
        Raises:
            FileNotFoundError: 設定ファイルが見つからない場合
            yaml.YAMLError: YAML解析エラーの場合
        """
        cache_key = f"gate{gate_number}"
        
        # キャッシュの確認とファイル更新チェック
        if self._should_reload_cache(cache_key, gate_number):
            self._load_patterns_from_file(gate_number)
            self._cache_stats['misses'] += 1
        else:
            self._cache_stats['hits'] += 1
        
        if cache_key not in self._patterns_cache:
            raise FileNotFoundError(f"GATE {gate_number} のパターン設定が見つかりません")
        
        return self._patterns_cache[cache_key]
    
    def _should_reload_cache(self, cache_key: str, gate_number: int) -> bool:
        """
        キャッシュの再読み込みが必要かチェック
        
        Args:
            cache_key: キャッシュキー
            gate_number: ゲート番号
            
        Returns:
            再読み込みが必要な場合True
        """
        config_file = self.config_dir / f"gate{gate_number}_patterns.yaml"
        
        if not config_file.exists():
            return False
        
        # ファイルの最終更新時刻をチェック
        current_mtime = config_file.stat().st_mtime
        
        if cache_key not in self._last_modified:
            return True
        
        return current_mtime > self._last_modified[cache_key]
    
    def _load_patterns_from_file(self, gate_number: int):
        """
        ファイルからパターン設定を読み込み
        
        Args:
            gate_number: ゲート番号
        """
        config_file = self.config_dir / f"gate{gate_number}_patterns.yaml"
        cache_key = f"gate{gate_number}"
        
        if not config_file.exists():
            self.logger.warning(f"設定ファイルが見つかりません: {config_file}")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                patterns = yaml.safe_load(f)
            
            # 設定の妥当性チェック
            self._validate_patterns(patterns, gate_number)
            
            # キャッシュに保存
            self._patterns_cache[cache_key] = patterns
            self._last_modified[cache_key] = config_file.stat().st_mtime
            
            self._cache_stats['loads'] += 1
            self.logger.info(f"GATE {gate_number} パターン設定を読み込みました: {len(patterns.get('patterns', {}))}個のパターン")
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML解析エラー (GATE {gate_number}): {e}")
            raise
        except Exception as e:
            self.logger.error(f"パターン設定読み込みエラー (GATE {gate_number}): {e}")
            raise
    
    def _validate_patterns(self, patterns: Dict[str, Any], gate_number: int):
        """
        パターン設定の妥当性チェック
        
        Args:
            patterns: パターン設定辞書
            gate_number: ゲート番号
        """
        if not isinstance(patterns, dict):
            raise ValueError(f"GATE {gate_number}: パターン設定は辞書形式である必要があります")
        
        if 'patterns' not in patterns:
            raise ValueError(f"GATE {gate_number}: 'patterns'キーが見つかりません")
        
        patterns_dict = patterns['patterns']
        if not isinstance(patterns_dict, dict):
            raise ValueError(f"GATE {gate_number}: 'patterns'は辞書形式である必要があります")
        
        # 各パターンの妥当性チェック
        for pattern_name, pattern_config in patterns_dict.items():
            self._validate_single_pattern(pattern_name, pattern_config, gate_number)
    
    def _validate_single_pattern(self, pattern_name: str, pattern_config: Dict[str, Any], gate_number: int):
        """
        単一パターンの妥当性チェック
        
        Args:
            pattern_name: パターン名
            pattern_config: パターン設定
            gate_number: ゲート番号
        """
        required_keys = ['name', 'description']
        for key in required_keys:
            if key not in pattern_config:
                raise ValueError(f"GATE {gate_number} パターン '{pattern_name}': '{key}'キーが必要です")
        
        # 条件の妥当性チェック
        if 'conditions' in pattern_config:
            conditions = pattern_config['conditions']
            if not isinstance(conditions, list):
                raise ValueError(f"GATE {gate_number} パターン '{pattern_name}': 'conditions'はリスト形式である必要があります")
            
            for i, condition in enumerate(conditions):
                self._validate_condition(condition, pattern_name, i, gate_number)
    
    def _validate_condition(self, condition: Dict[str, Any], pattern_name: str, index: int, gate_number: int):
        """
        条件の妥当性チェック
        
        Args:
            condition: 条件辞書
            pattern_name: パターン名
            index: 条件のインデックス
            gate_number: ゲート番号
        """
        required_keys = ['name', 'indicator', 'operator']
        for key in required_keys:
            if key not in condition:
                raise ValueError(f"GATE {gate_number} パターン '{pattern_name}' 条件[{index}]: '{key}'キーが必要です")
        
        # 演算子の妥当性チェック
        valid_operators = ['>', '<', '>=', '<=', '==', '!=', 'between', 'not_between', 
                          'all_above', 'all_below', 'any_above', 'any_below', 
                          'near', 'engulfs', 'breaks', 'oscillates_around']
        
        operator = condition['operator']
        if operator not in valid_operators:
            raise ValueError(f"GATE {gate_number} パターン '{pattern_name}' 条件[{index}]: 無効な演算子 '{operator}'")
    
    def reload_patterns(self, gate_number: Optional[int] = None):
        """
        パターン設定の再読み込み
        
        Args:
            gate_number: 指定されたゲート番号（Noneの場合は全ゲート）
        """
        if gate_number:
            cache_key = f"gate{gate_number}"
            if cache_key in self._patterns_cache:
                del self._patterns_cache[cache_key]
            if cache_key in self._last_modified:
                del self._last_modified[cache_key]
            
            self._load_patterns_from_file(gate_number)
            self.logger.info(f"GATE {gate_number} パターン設定を再読み込みしました")
        else:
            self._patterns_cache.clear()
            self._last_modified.clear()
            
            # 全ゲートの設定を再読み込み
            for gate_num in [1, 2, 3]:
                self._load_patterns_from_file(gate_num)
            
            self.logger.info("全パターン設定を再読み込みしました")
    
    def get_pattern_conditions(self, gate_number: int, pattern_name: str) -> List[Dict[str, Any]]:
        """
        特定パターンの条件を取得
        
        Args:
            gate_number: ゲート番号
            pattern_name: パターン名
            
        Returns:
            条件のリスト
        """
        patterns = self.load_gate_patterns(gate_number)
        pattern_config = patterns.get('patterns', {}).get(pattern_name, {})
        return pattern_config.get('conditions', [])
    
    def get_confidence_calculation(self, gate_number: int, pattern_name: str) -> Dict[str, Any]:
        """
        特定パターンの信頼度計算設定を取得
        
        Args:
            gate_number: ゲート番号
            pattern_name: パターン名
            
        Returns:
            信頼度計算設定
        """
        patterns = self.load_gate_patterns(gate_number)
        pattern_config = patterns.get('patterns', {}).get(pattern_name, {})
        return pattern_config.get('confidence_calculation', {})
    
    def get_pattern_names(self, gate_number: int) -> List[str]:
        """
        指定されたゲートのパターン名一覧を取得
        
        Args:
            gate_number: ゲート番号
            
        Returns:
            パターン名のリスト
        """
        patterns = self.load_gate_patterns(gate_number)
        return list(patterns.get('patterns', {}).keys())
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        キャッシュ情報を取得
        
        Returns:
            キャッシュ情報の辞書
        """
        cache_info = {}
        for cache_key, patterns in self._patterns_cache.items():
            cache_info[cache_key] = {
                'pattern_count': len(patterns.get('patterns', {})),
                'last_modified': self._last_modified.get(cache_key, 0),
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
        
        return cache_info
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self._patterns_cache.clear()
        self._last_modified.clear()
        self.logger.info("パターン設定キャッシュをクリアしました")


# テスト用のメイン関数
if __name__ == "__main__":
    import asyncio
    
    async def test_pattern_loader():
        """PatternLoaderのテスト"""
        loader = PatternLoader()
        
        try:
            # GATE 1のパターン設定を読み込み
            patterns = loader.load_gate_patterns(1)
            print(f"GATE 1 パターン数: {len(patterns.get('patterns', {}))}")
            
            # キャッシュ情報を表示
            cache_info = loader.get_cache_info()
            print(f"キャッシュ情報: {cache_info}")
            
        except FileNotFoundError as e:
            print(f"設定ファイルが見つかりません: {e}")
        except Exception as e:
            print(f"エラー: {e}")
    
    # テスト実行
    asyncio.run(test_pattern_loader())
