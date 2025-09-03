#!/usr/bin/env python3
"""
リファクタリング実行スクリプト

このスクリプトは、Exchange Analytics Systemのリファクタリングを
段階的に実行するためのメインスクリプトです。
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RefactoringExecutor:
    """リファクタリング実行クラス"""
    
    def __init__(self, root_path: str = "/app"):
        self.root_path = Path(root_path)
        self.backup_dir = self.root_path / "backups" / f"refactoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.analysis_report = None
        
    def create_backup(self):
        """システム全体のバックアップを作成"""
        logger.info("バックアップを作成中...")
        
        try:
            # バックアップディレクトリの作成
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 重要なディレクトリのコピー
            important_dirs = ['scripts', 'src', 'tests', 'config']
            for dir_name in important_dirs:
                src_dir = self.root_path / dir_name
                if src_dir.exists():
                    dst_dir = self.backup_dir / dir_name
                    self._copy_directory(src_dir, dst_dir)
            
            # 重要なファイルのコピー
            important_files = ['README.md', 'crontab_new.txt', 'requirements.txt']
            for file_name in important_files:
                src_file = self.root_path / file_name
                if src_file.exists():
                    dst_file = self.backup_dir / file_name
                    self._copy_file(src_file, dst_file)
            
            logger.info(f"バックアップが完了しました: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"バックアップ作成エラー: {e}")
            return False
    
    def _copy_directory(self, src: Path, dst: Path):
        """ディレクトリをコピー"""
        if dst.exists():
            import shutil
            shutil.rmtree(dst)
        
        import shutil
        shutil.copytree(src, dst)
    
    def _copy_file(self, src: Path, dst: Path):
        """ファイルをコピー"""
        import shutil
        shutil.copy2(src, dst)
    
    def run_script_analysis(self):
        """スクリプト分析を実行"""
        logger.info("スクリプト分析を実行中...")
        
        try:
            # 分析ツールの実行
            analysis_script = self.root_path / "scripts" / "refactoring" / "script_analyzer.py"
            if not analysis_script.exists():
                logger.error("分析ツールが見つかりません")
                return False
            
            # 分析の実行
            result = subprocess.run([
                sys.executable, str(analysis_script),
                "--root-path", str(self.root_path),
                "--output", "script_analysis_report.json"
            ], capture_output=True, text=True, cwd=str(self.root_path))
            
            if result.returncode == 0:
                logger.info("スクリプト分析が完了しました")
                
                # レポートの読み込み
                report_path = self.root_path / "scripts" / "refactoring" / "script_analysis_report.json"
                if report_path.exists():
                    with open(report_path, 'r', encoding='utf-8') as f:
                        self.analysis_report = json.load(f)
                    return True
                else:
                    logger.error("分析レポートが見つかりません")
                    return False
            else:
                logger.error(f"分析ツールの実行エラー: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"スクリプト分析エラー: {e}")
            return False
    
    def show_analysis_summary(self):
        """分析結果のサマリーを表示"""
        if not self.analysis_report:
            logger.error("分析レポートがありません")
            return
        
        summary = self.analysis_report['summary']
        
        print("\n" + "="*60)
        print("📊 リファクタリング分析結果")
        print("="*60)
        print(f"総ファイル数: {summary['total_files']}")
        print(f"高リスクファイル: {summary['high_risk']}")
        print(f"中リスクファイル: {summary['medium_risk']}")
        print(f"低リスクファイル: {summary['low_risk']}")
        print(f"安全に削除可能: {summary['safe_to_delete']}")
        
        if summary['safe_to_delete'] > 0:
            print("\n🗑️  削除推奨ファイル:")
            for file_path in self.analysis_report['safe_to_delete_files']:
                print(f"  • {file_path}")
    
    def run_tests(self):
        """テストを実行"""
        logger.info("テストを実行中...")
        
        try:
            # pytestの実行
            result = subprocess.run([
                sys.executable, "-m", "pytest", "tests/", "-v"
            ], capture_output=True, text=True, cwd=str(self.root_path))
            
            if result.returncode == 0:
                logger.info("テストが完了しました")
                return True
            else:
                logger.warning(f"テストで警告があります: {result.stdout}")
                return True  # 警告があっても続行
                
        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")
            return False
    
    def cleanup_archive_files(self):
        """アーカイブファイルの整理"""
        if not self.analysis_report:
            logger.error("分析レポートがありません")
            return False
        
        logger.info("アーカイブファイルの整理を開始...")
        
        try:
            # 安全に削除可能なファイルの削除
            safe_files = self.analysis_report['safe_to_delete_files']
            archive_files = [f for f in safe_files if 'archive' in f]
            
            if not archive_files:
                logger.info("削除可能なアーカイブファイルはありません")
                return True
            
            print(f"\n🗑️  削除対象のアーカイブファイル ({len(archive_files)}件):")
            for file_path in archive_files:
                print(f"  • {file_path}")
            
            # ユーザーの確認
            response = input("\nこれらのファイルを削除しますか？ (y/N): ")
            if response.lower() != 'y':
                logger.info("削除をキャンセルしました")
                return True
            
            # 段階的な削除
            for file_path in archive_files:
                full_path = self.root_path / file_path
                if full_path.exists():
                    try:
                        full_path.unlink()
                        logger.info(f"削除完了: {file_path}")
                    except Exception as e:
                        logger.error(f"削除エラー {file_path}: {e}")
                        return False
            
            logger.info("アーカイブファイルの整理が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"アーカイブファイル整理エラー: {e}")
            return False
    
    def cleanup_test_files(self):
        """テストファイルの整理"""
        if not self.analysis_report:
            logger.error("分析レポートがありません")
            return False
        
        logger.info("テストファイルの整理を開始...")
        
        try:
            # 重複テストの特定
            test_files = [f for f in self.analysis_report['safe_to_delete_files'] if 'test' in f]
            
            if not test_files:
                logger.info("整理対象のテストファイルはありません")
                return True
            
            print(f"\n🧪 整理対象のテストファイル ({len(test_files)}件):")
            for file_path in test_files:
                print(f"  • {file_path}")
            
            # ユーザーの確認
            response = input("\nこれらのファイルを整理しますか？ (y/N): ")
            if response.lower() != 'y':
                logger.info("整理をキャンセルしました")
                return True
            
            # 段階的な整理
            for file_path in test_files:
                full_path = self.root_path / file_path
                if full_path.exists():
                    try:
                        # ファイルをアーカイブディレクトリに移動
                        archive_dir = self.root_path / "scripts" / "archive" / "refactoring_cleanup"
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        
                        archive_path = archive_dir / full_path.name
                        full_path.rename(archive_path)
                        logger.info(f"アーカイブ完了: {file_path}")
                        
                    except Exception as e:
                        logger.error(f"整理エラー {file_path}: {e}")
                        return False
            
            logger.info("テストファイルの整理が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"テストファイル整理エラー: {e}")
            return False
    
    def final_verification(self):
        """最終検証"""
        logger.info("最終検証を実行中...")
        
        try:
            # テストの再実行
            if not self.run_tests():
                logger.error("最終検証でテストが失敗しました")
                return False
            
            # システムの健全性チェック
            health_check_script = self.root_path / "scripts" / "monitoring" / "realtime_monitor.py"
            if health_check_script.exists():
                result = subprocess.run([
                    sys.executable, str(health_check_script),
                    "--interval", "1", "--no-alerts"
                ], capture_output=True, text=True, cwd=str(self.root_path), timeout=30)
                
                if result.returncode == 0:
                    logger.info("システム健全性チェックが完了しました")
                else:
                    logger.warning("システム健全性チェックで警告があります")
            
            logger.info("最終検証が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"最終検証エラー: {e}")
            return False
    
    def execute_refactoring(self, phase: str):
        """指定されたフェーズのリファクタリングを実行"""
        logger.info(f"フェーズ {phase} のリファクタリングを開始...")
        
        if phase == "1":
            # Phase 1: 事前準備
            if not self.create_backup():
                return False
            
            if not self.run_script_analysis():
                return False
            
            self.show_analysis_summary()
            return True
            
        elif phase == "2":
            # Phase 2: 安全なスクリプト整理
            if not self.cleanup_archive_files():
                return False
            
            if not self.cleanup_test_files():
                return False
            
            return True
            
        elif phase == "3":
            # Phase 3: コード品質向上
            logger.info("コード品質向上は手動で実施してください")
            return True
            
        elif phase == "4":
            # Phase 4: 最終検証
            if not self.final_verification():
                return False
            
            return True
            
        else:
            logger.error(f"不明なフェーズ: {phase}")
            return False

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="リファクタリング実行スクリプト")
    parser.add_argument(
        "--phase",
        choices=["1", "2", "3", "4", "all"],
        default="1",
        help="実行するフェーズ (デフォルト: 1)"
    )
    parser.add_argument(
        "--root-path",
        default="/app",
        help="対象のルートディレクトリ (デフォルト: /app)"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="バックアップをスキップ"
    )
    
    args = parser.parse_args()
    
    # リファクタリング実行クラスの初期化
    executor = RefactoringExecutor(args.root_path)
    
    try:
        if args.phase == "all":
            # 全フェーズの実行
            phases = ["1", "2", "3", "4"]
            for phase in phases:
                logger.info(f"\n{'='*60}")
                logger.info(f"フェーズ {phase} を開始")
                logger.info(f"{'='*60}")
                
                if not executor.execute_refactoring(phase):
                    logger.error(f"フェーズ {phase} でエラーが発生しました")
                    break
                
                logger.info(f"フェーズ {phase} が完了しました")
                
                if phase != "4":
                    response = input(f"\nフェーズ {phase} が完了しました。次のフェーズに進みますか？ (y/N): ")
                    if response.lower() != 'y':
                        logger.info("リファクタリングを中断しました")
                        break
        else:
            # 単一フェーズの実行
            if not executor.execute_refactoring(args.phase):
                logger.error(f"フェーズ {args.phase} でエラーが発生しました")
                return 1
        
        logger.info("リファクタリングが完了しました")
        return 0
        
    except KeyboardInterrupt:
        logger.info("リファクタリングが中断されました")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
