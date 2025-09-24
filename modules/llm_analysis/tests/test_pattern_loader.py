#!/usr/bin/env python3
"""
PatternLoaderの単体テスト

パターン設定読み込み機能のテストを行います。
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.llm_analysis.core.pattern_loader import PatternLoader


class TestPatternLoader:
    """PatternLoaderのテストクラス"""
    
    def setup_method(self):
        """テスト前のセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = PatternLoader(config_dir=self.temp_dir)
    
    def teardown_method(self):
        """テスト後のクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """初期化テスト"""
        assert self.loader.config_dir == Path(self.temp_dir)
        assert isinstance(self.loader._patterns_cache, dict)
        assert isinstance(self.loader._last_modified, dict)
    
    def test_config_directory_creation(self):
        """設定ディレクトリの自動作成テスト"""
        non_existent_dir = Path(self.temp_dir) / "non_existent"
        loader = PatternLoader(config_dir=str(non_existent_dir))
        assert non_existent_dir.exists()
    
    def test_load_gate_patterns_file_not_found(self):
        """設定ファイルが見つからない場合のテスト"""
        with pytest.raises(FileNotFoundError):
            self.loader.load_gate_patterns(1)
    
    def test_load_gate_patterns_success(self):
        """正常なパターン設定読み込みテスト"""
        # テスト用の設定ファイルを作成
        test_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': [
                        {
                            'name': 'test_condition',
                            'indicator': 'close',
                            'operator': '>',
                            'value': 100,
                            'weight': 0.5
                        }
                    ],
                    'confidence_calculation': {
                        'method': 'weighted_average',
                        'min_confidence': 0.7
                    }
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
        
        # パターン設定を読み込み
        patterns = self.loader.load_gate_patterns(1)
        
        assert 'patterns' in patterns
        assert 'test_pattern' in patterns['patterns']
        assert patterns['patterns']['test_pattern']['name'] == 'テストパターン'
    
    def test_validate_patterns_invalid_structure(self):
        """無効な構造のパターン設定テスト"""
        # 無効な構造の設定ファイルを作成
        invalid_config = {
            'invalid_key': 'invalid_value'
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f, default_flow_style=False)
        
        with pytest.raises(ValueError, match="'patterns'キーが見つかりません"):
            self.loader.load_gate_patterns(1)
    
    def test_validate_single_pattern_missing_required_keys(self):
        """必須キーが不足しているパターンのテスト"""
        invalid_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン'
                    # descriptionが不足
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f, default_flow_style=False)
        
        with pytest.raises(ValueError, match="'description'キーが必要です"):
            self.loader.load_gate_patterns(1)
    
    def test_validate_condition_invalid_operator(self):
        """無効な演算子のテスト"""
        invalid_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': [
                        {
                            'name': 'test_condition',
                            'indicator': 'close',
                            'operator': 'invalid_operator',  # 無効な演算子
                            'value': 100
                        }
                    ]
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_config, f, default_flow_style=False)
        
        with pytest.raises(ValueError, match="無効な演算子"):
            self.loader.load_gate_patterns(1)
    
    def test_reload_patterns_specific_gate(self):
        """特定ゲートの再読み込みテスト"""
        # 初期設定ファイルを作成
        test_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': []
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        # 初回読み込み
        patterns1 = self.loader.load_gate_patterns(1)
        
        # 設定ファイルを更新
        test_config['patterns']['test_pattern']['name'] = '更新されたテストパターン'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        # 再読み込み
        self.loader.reload_patterns(gate_number=1)
        patterns2 = self.loader.load_gate_patterns(1)
        
        assert patterns2['patterns']['test_pattern']['name'] == '更新されたテストパターン'
    
    def test_reload_patterns_all_gates(self):
        """全ゲートの再読み込みテスト"""
        # 複数のゲート設定ファイルを作成
        for gate_num in [1, 2, 3]:
            test_config = {
                'patterns': {
                    f'test_pattern_{gate_num}': {
                        'name': f'テストパターン{gate_num}',
                        'description': f'テスト用のパターン{gate_num}',
                        'conditions': []
                    }
                }
            }
            
            config_file = Path(self.temp_dir) / f"gate{gate_num}_patterns.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(test_config, f, default_flow_style=False)
        
        # 全ゲートの再読み込み
        self.loader.reload_patterns()
        
        # 各ゲートの設定が読み込まれていることを確認
        for gate_num in [1, 2, 3]:
            patterns = self.loader.load_gate_patterns(gate_num)
            assert f'test_pattern_{gate_num}' in patterns['patterns']
    
    def test_get_pattern_conditions(self):
        """パターン条件取得テスト"""
        test_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': [
                        {
                            'name': 'condition1',
                            'indicator': 'close',
                            'operator': '>',
                            'value': 100
                        },
                        {
                            'name': 'condition2',
                            'indicator': 'RSI_14',
                            'operator': '<',
                            'value': 70
                        }
                    ]
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        conditions = self.loader.get_pattern_conditions(1, 'test_pattern')
        
        assert len(conditions) == 2
        assert conditions[0]['name'] == 'condition1'
        assert conditions[1]['name'] == 'condition2'
    
    def test_get_confidence_calculation(self):
        """信頼度計算設定取得テスト"""
        test_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': [],
                    'confidence_calculation': {
                        'method': 'weighted_average',
                        'min_confidence': 0.8
                    }
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        confidence_config = self.loader.get_confidence_calculation(1, 'test_pattern')
        
        assert confidence_config['method'] == 'weighted_average'
        assert confidence_config['min_confidence'] == 0.8
    
    def test_get_pattern_names(self):
        """パターン名一覧取得テスト"""
        test_config = {
            'patterns': {
                'pattern1': {
                    'name': 'パターン1',
                    'description': 'テスト用のパターン1',
                    'conditions': []
                },
                'pattern2': {
                    'name': 'パターン2',
                    'description': 'テスト用のパターン2',
                    'conditions': []
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        pattern_names = self.loader.get_pattern_names(1)
        
        assert len(pattern_names) == 2
        assert 'pattern1' in pattern_names
        assert 'pattern2' in pattern_names
    
    def test_get_cache_info(self):
        """キャッシュ情報取得テスト"""
        # 設定ファイルを作成して読み込み
        test_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': []
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        # パターン設定を読み込み
        self.loader.load_gate_patterns(1)
        
        # キャッシュ情報を取得
        cache_info = self.loader.get_cache_info()
        
        assert 'gate1' in cache_info
        assert cache_info['gate1']['pattern_count'] == 1
        assert 'cached_at' in cache_info['gate1']
    
    def test_clear_cache(self):
        """キャッシュクリアテスト"""
        # 設定ファイルを作成して読み込み
        test_config = {
            'patterns': {
                'test_pattern': {
                    'name': 'テストパターン',
                    'description': 'テスト用のパターン',
                    'conditions': []
                }
            }
        }
        
        config_file = Path(self.temp_dir) / "gate1_patterns.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_config, f, default_flow_style=False)
        
        # パターン設定を読み込み
        self.loader.load_gate_patterns(1)
        
        # キャッシュが存在することを確認
        assert 'gate1' in self.loader._patterns_cache
        
        # キャッシュをクリア
        self.loader.clear_cache()
        
        # キャッシュがクリアされたことを確認
        assert len(self.loader._patterns_cache) == 0
        assert len(self.loader._last_modified) == 0


# テスト実行用のメイン関数
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
