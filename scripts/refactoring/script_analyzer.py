#!/usr/bin/env python3
"""
スクリプト依存関係分析ツール

このツールは、Exchange Analytics Systemのスクリプトの依存関係と使用状況を分析し、
リファクタリングの安全性を確保するための情報を提供します。
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScriptAnalyzer:
    """スクリプトの依存関係と使用状況を分析するクラス"""

    def __init__(self, root_path: str = "/app"):
        self.root_path = Path(root_path)
        self.scripts_dir = self.root_path / "scripts"
        self.src_dir = self.root_path / "src"
        self.tests_dir = self.root_path / "tests"
        
        # 分析結果
        self.imports_map = defaultdict(set)  # ファイル -> インポート先
        self.imported_by_map = defaultdict(set)  # ファイル -> インポート元
        self.usage_map = defaultdict(set)  # ファイル -> 使用箇所
        self.risk_assessment = {}  # ファイル -> リスク評価
        
    def analyze_all_scripts(self) -> Dict:
        """全スクリプトの分析を実行"""
        logger.info("スクリプト分析を開始します...")
        
        # 各ディレクトリの分析
        self._analyze_directory(self.scripts_dir, "scripts")
        self._analyze_directory(self.src_dir, "src")
        self._analyze_directory(self.tests_dir, "tests")
        
        # 使用状況の分析
        self._analyze_usage_patterns()
        
        # リスク評価
        self._assess_risks()
        
        return self._generate_report()
    
    def _analyze_directory(self, directory: Path, dir_type: str):
        """指定されたディレクトリ内のPythonファイルを分析"""
        if not directory.exists():
            logger.warning(f"ディレクトリが存在しません: {directory}")
            return
            
        for py_file in directory.rglob("*.py"):
            logger.info(f"分析中: {py_file}")
            self._analyze_python_file(py_file, dir_type)
    
    def _analyze_python_file(self, file_path: Path, dir_type: str):
        """Pythonファイルの依存関係を分析"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # インポート文の抽出
            imports = self._extract_imports(content)
            
            # 相対パスを絶対パスに変換
            absolute_imports = self._resolve_imports(imports, file_path)
            
            # マップに追加
            relative_path = str(file_path.relative_to(self.root_path))
            self.imports_map[relative_path] = absolute_imports
            
            for imported_file in absolute_imports:
                self.imported_by_map[imported_file].add(relative_path)
                
        except Exception as e:
            logger.error(f"ファイル分析エラー {file_path}: {e}")
    
    def _extract_imports(self, content: str) -> List[str]:
        """Pythonファイルからインポート文を抽出"""
        imports = []
        
        # 標準的なインポート文
        import_patterns = [
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*$',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import',
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+([a-zA-Z_][a-zA-Z0-9_,\s]*)',
        ]
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
                
            for pattern in import_patterns:
                match = re.match(pattern, line)
                if match:
                    imports.append(match.group(1))
                    break
        
        # 動的インポート
        dynamic_patterns = [
            r'__import__\s*\(\s*["\']([^"\']+)["\']',
            r'importlib\.import_module\s*\(\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in dynamic_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return list(set(imports))
    
    def _resolve_imports(self, imports: List[str], source_file: Path) -> List[str]:
        """インポートパスを絶対パスに解決"""
        resolved = []
        
        for imp in imports:
            # スクリプトディレクトリからの相対インポート
            if imp.startswith('scripts.'):
                script_path = self.root_path / imp.replace('.', '/') + '.py'
                if script_path.exists():
                    resolved.append(str(script_path.relative_to(self.root_path)))
            
            # srcディレクトリからの相対インポート
            elif imp.startswith('src.'):
                src_path = self.root_path / imp.replace('.', '/') + '.py'
                if src_path.exists():
                    resolved.append(str(src_path.relative_to(self.root_path)))
            
            # その他の相対インポート
            elif not imp.startswith(('.', '/')):
                # 標準ライブラリやサードパーティライブラリは除外
                if not self._is_standard_library(imp):
                    # 相対パスで解決を試行
                    possible_paths = [
                        source_file.parent / f"{imp}.py",
                        source_file.parent / imp / "__init__.py",
                        self.scripts_dir / f"{imp}.py",
                        self.src_dir / f"{imp}.py",
                    ]
                    
                    for path in possible_paths:
                        if path.exists():
                            resolved.append(str(path.relative_to(self.root_path)))
                            break
        
        return resolved
    
    def _is_standard_library(self, module_name: str) -> bool:
        """標準ライブラリかどうかを判定"""
        standard_modules = {
            'os', 'sys', 're', 'json', 'logging', 'pathlib', 'typing',
            'collections', 'datetime', 'time', 'random', 'math', 'statistics',
            'itertools', 'functools', 'argparse', 'subprocess', 'shutil',
            'glob', 'fnmatch', 'tempfile', 'pickle', 'sqlite3', 'csv',
            'xml', 'html', 'urllib', 'requests', 'threading', 'multiprocessing',
            'asyncio', 'concurrent', 'queue', 'socket', 'ssl', 'hashlib',
            'base64', 'zlib', 'gzip', 'bz2', 'lzma', 'tarfile', 'zipfile',
            'configparser', 'logging', 'getpass', 'platform', 'psutil'
        }
        
        return module_name.split('.')[0] in standard_modules
    
    def _analyze_usage_patterns(self):
        """使用パターンの分析"""
        logger.info("使用パターンの分析を開始...")
        
        # cronジョブでの使用状況
        self._analyze_cron_usage()
        
        # テストでの使用状況
        self._analyze_test_usage()
        
        # 設定ファイルでの参照
        self._analyze_config_references()
    
    def _analyze_cron_usage(self):
        """cronジョブでの使用状況を分析"""
        crontab_file = self.root_path / "crontab_new.txt"
        if crontab_file.exists():
            with open(crontab_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pythonスクリプトの実行を検索
            python_scripts = re.findall(r'python\s+([^\s]+\.py)', content)
            for script in python_scripts:
                if script.startswith('scripts/'):
                    script_path = script
                    self.usage_map[script_path].add('cron')
                    logger.info(f"cronで使用: {script_path}")
    
    def _analyze_test_usage(self):
        """テストでの使用状況を分析"""
        # テストファイル内でのスクリプト参照
        for test_file in self.tests_dir.rglob("*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # scriptsディレクトリからのインポートを検索
                script_imports = re.findall(r'from\s+scripts\.([^\s]+)', content)
                for script_import in script_imports:
                    script_path = f"scripts/{script_import.replace('.', '/')}.py"
                    self.usage_map[script_path].add('test')
                    
            except Exception as e:
                logger.error(f"テストファイル分析エラー {test_file}: {e}")
    
    def _analyze_config_references(self):
        """設定ファイルでの参照を分析"""
        config_files = [
            self.root_path / "README.md",
            self.root_path / "scripts" / "README.md",
            self.root_path / "src" / "README.md",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # スクリプトの参照を検索
                    script_refs = re.findall(r'scripts/([^\s]+\.py)', content)
                    for script_ref in script_refs:
                        script_path = f"scripts/{script_ref}"
                        self.usage_map[script_path].add('documentation')
                        
                except Exception as e:
                    logger.error(f"設定ファイル分析エラー {config_file}: {e}")
    
    def _assess_risks(self):
        """各ファイルのリスクを評価"""
        logger.info("リスク評価を開始...")
        
        for file_path in self.imports_map.keys():
            risk_level = self._calculate_risk_level(file_path)
            self.risk_assessment[file_path] = risk_level
    
    def _calculate_risk_level(self, file_path: str) -> Dict:
        """ファイルのリスクレベルを計算"""
        risk_score = 0
        risk_factors = []
        
        # 使用状況によるリスク
        usage = self.usage_map.get(file_path, set())
        if 'cron' in usage:
            risk_score += 10
            risk_factors.append("cronジョブで使用")
        if 'test' in usage:
            risk_score += 3
            risk_factors.append("テストで使用")
        if 'documentation' in usage:
            risk_score += 2
            risk_factors.append("ドキュメントで参照")
        
        # 依存関係によるリスク
        imported_by = self.imported_by_map.get(file_path, set())
        if imported_by:
            risk_score += len(imported_by) * 2
            risk_factors.append(f"{len(imported_by)}個のファイルからインポート")
        
        # ディレクトリによるリスク
        if file_path.startswith('scripts/cron/'):
            risk_score += 5
            risk_factors.append("cronディレクトリ")
        elif file_path.startswith('scripts/monitoring/'):
            risk_score += 5
            risk_factors.append("monitoringディレクトリ")
        elif file_path.startswith('scripts/deployment/'):
            risk_score += 5
            risk_factors.append("deploymentディレクトリ")
        elif file_path.startswith('scripts/archive/'):
            risk_score += 1
            risk_factors.append("archiveディレクトリ")
        
        # リスクレベルの判定
        if risk_score >= 15:
            risk_level = "高"
        elif risk_score >= 8:
            risk_level = "中"
        else:
            risk_level = "低"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "usage": list(usage),
            "imported_by": list(imported_by)
        }
    
    def _generate_report(self) -> Dict:
        """分析レポートを生成"""
        logger.info("分析レポートを生成中...")
        
        # 統計情報
        total_files = len(self.imports_map)
        high_risk_files = len([f for f, r in self.risk_assessment.items() if r['risk_level'] == '高'])
        medium_risk_files = len([f for f, r in self.risk_assessment.items() if r['risk_level'] == '中'])
        low_risk_files = len([f for f, r in self.risk_assessment.items() if r['risk_level'] == '低'])
        
        # 削除推奨ファイル
        safe_to_delete = [
            f for f, r in self.risk_assessment.items()
            if (r['risk_level'] == '低' and not r['usage'] 
                and not r['imported_by'])
        ]

        # 注意が必要なファイル
        high_attention = [
            f for f, r in self.risk_assessment.items()
            if r['risk_level'] == '高'
        ]
        
        report = {
            "summary": {
                "total_files": total_files,
                "high_risk": high_risk_files,
                "medium_risk": medium_risk_files,
                "low_risk": low_risk_files,
                "safe_to_delete": len(safe_to_delete)
            },
            "risk_assessment": self.risk_assessment,
            "safe_to_delete_files": safe_to_delete,
            "high_attention_files": high_attention,
            "imports_map": dict(self.imports_map),
            "usage_map": dict(self.usage_map)
        }
        
        return report
    
    def save_report(self, report: Dict, output_file: str = "script_analysis_report.json"):
        """レポートをJSONファイルに保存"""
        output_path = self.root_path / "scripts" / "refactoring" / output_file
        
        # ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"レポートを保存しました: {output_path}")
    
    def print_summary(self, report: Dict):
        """レポートのサマリーを表示"""
        summary = report['summary']
        
        print("\n" + "="*60)
        print("📊 スクリプト分析結果サマリー")
        print("="*60)
        print(f"総ファイル数: {summary['total_files']}")
        print(f"高リスクファイル: {summary['high_risk']}")
        print(f"中リスクファイル: {summary['medium_risk']}")
        print(f"低リスクファイル: {summary['low_risk']}")
        print(f"安全に削除可能: {summary['safe_to_delete']}")
        
        print("\n" + "-"*60)
        print("⚠️  高リスクファイル（削除不可）")
        print("-"*60)
        for file_path in report['high_attention_files']:
            risk_info = report['risk_assessment'][file_path]
            print(f"• {file_path} (リスクスコア: {risk_info['risk_score']})")
            print(f"  理由: {', '.join(risk_info['risk_factors'])}")
        
        print("\n" + "-"*60)
        print("🗑️  安全に削除可能なファイル")
        print("-"*60)
        for file_path in report['safe_to_delete_files']:
            print(f"• {file_path}")
        
        print("\n" + "-"*60)
        print("📝 推奨事項")
        print("-"*60)
        print("1. 高リスクファイルは絶対に削除しないでください")
        print("2. 中リスクファイルは慎重に扱い、事前にテストしてください")
        print("3. 低リスクファイルは段階的に削除してください")
        print("4. 削除前には必ずバックアップを取ってください")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="スクリプト依存関係分析ツール")
    parser.add_argument(
        "--root-path", 
        default="/app", 
        help="分析対象のルートディレクトリ (デフォルト: /app)"
    )
    parser.add_argument(
        "--output", 
        default="script_analysis_report.json",
        help="出力ファイル名 (デフォルト: script_analysis_report.json)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="詳細なログを出力"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 分析の実行
    analyzer = ScriptAnalyzer(args.root_path)
    report = analyzer.analyze_all_scripts()
    
    # レポートの保存
    analyzer.save_report(report, args.output)
    
    # サマリーの表示
    analyzer.print_summary(report)
    
    logger.info("分析が完了しました。詳細はレポートファイルを確認してください。")

if __name__ == "__main__":
    main()
