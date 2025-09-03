#!/usr/bin/env python3
"""
テスト実行スクリプト
包括的なテストスイートの実行とレポート生成
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestRunner:
    """テストランナー"""
    
    def __init__(self, config_file: str = "config/test_config.json"):
        self.config_file = Path(config_file)
        self.test_dir = Path("tests")
        self.reports_dir = Path("reports")
        self.coverage_dir = Path("reports/coverage")
        
        # ディレクトリの作成
        self.reports_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_unit_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """単体テストの実行"""
        print("🧪 Running unit tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "unit"),
            "--cov=src",
            "--cov-report=html:" + str(self.coverage_dir / "unit"),
            "--cov-report=json:" + str(self.coverage_dir / "unit_coverage.json"),
            "--cov-report=term-missing",
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """統合テストの実行"""
        print("🔗 Running integration tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "integration"),
            "--cov=src",
            "--cov-report=html:" + str(self.coverage_dir / "integration"),
            "--cov-report=json:" + str(self.coverage_dir / "integration_coverage.json"),
            "--cov-report=term-missing",
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_e2e_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """E2Eテストの実行"""
        print("🌐 Running E2E tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "e2e"),
            "--cov=src",
            "--cov-report=html:" + str(self.coverage_dir / "e2e"),
            "--cov-report=json:" + str(self.coverage_dir / "e2e_coverage.json"),
            "--cov-report=term-missing",
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_performance_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """パフォーマンステストの実行"""
        print("⚡ Running performance tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "performance"),
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_security_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """セキュリティテストの実行"""
        print("🔒 Running security tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "security"),
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_ai_analysis_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """AI分析テストの実行"""
        print("🤖 Running AI analysis tests...")
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir / "ai_analysis"),
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_all_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """全テストの実行"""
        print("🚀 Running all tests...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_success": True,
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0
            }
        }
        
        # 各テストタイプの実行
        test_types = [
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),
            ("e2e", self.run_e2e_tests),
            ("performance", self.run_performance_tests),
            ("security", self.run_security_tests),
            ("ai_analysis", self.run_ai_analysis_tests)
        ]
        
        for test_type, test_func in test_types:
            print(f"\n📋 Running {test_type} tests...")
            result = test_func(verbose)
            results["tests"][test_type] = result
            
            if not result["success"]:
                results["overall_success"] = False
            
            # 結果の表示
            if result["success"]:
                print(f"✅ {test_type} tests passed")
            else:
                print(f"❌ {test_type} tests failed")
                if verbose and result["error"]:
                    print(f"Error: {result['error']}")
        
        # サマリーの生成
        self._generate_summary(results)
        
        # レポートの保存
        self._save_test_report(results)
        
        return results
    
    def _generate_summary(self, results: Dict[str, Any]) -> None:
        """テストサマリーの生成"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for test_type, result in results["tests"].items():
            if result["success"]:
                # 成功したテストの数を推定
                output_lines = result["output"].split("\n")
                for line in output_lines:
                    if "passed" in line and "failed" in line:
                        # pytestの出力から数値を抽出
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == "passed":
                                if i > 0 and parts[i-1].isdigit():
                                    passed_tests += int(parts[i-1])
                            elif part == "failed":
                                if i > 0 and parts[i-1].isdigit():
                                    failed_tests += int(parts[i-1])
                            elif part == "skipped":
                                if i > 0 and parts[i-1].isdigit():
                                    skipped_tests += int(parts[i-1])
        
        total_tests = passed_tests + failed_tests + skipped_tests
        
        results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
    
    def _save_test_report(self, results: Dict[str, Any]) -> None:
        """テストレポートの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"test_report_{timestamp}.json"
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Test report saved: {report_file}")
    
    def generate_coverage_report(self) -> Dict[str, Any]:
        """カバレッジレポートの生成"""
        print("📈 Generating coverage report...")
        
        cmd = [
            "python", "-m", "pytest",
            "--cov=src",
            "--cov-report=html:" + str(self.coverage_dir / "combined"),
            "--cov-report=json:" + str(self.coverage_dir / "combined_coverage.json"),
            "--cov-report=term-missing",
            "--cov-fail-under=95"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> Dict[str, Any]:
        """特定のテストの実行"""
        print(f"🎯 Running specific test: {test_path}")
        
        cmd = [
            "python", "-m", "pytest",
            test_path,
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }
    
    def run_tests_with_filter(self, filter_pattern: str, verbose: bool = False) -> Dict[str, Any]:
        """フィルタ付きテストの実行"""
        print(f"🔍 Running tests with filter: {filter_pattern}")
        
        cmd = [
            "python", "-m", "pytest",
            "-k", filter_pattern,
            "--cov=src",
            "--cov-report=html:" + str(self.coverage_dir / "filtered"),
            "--cov-report=json:" + str(self.coverage_dir / "filtered_coverage.json"),
            "--cov-report=term-missing",
            "-v" if verbose else "-q"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "output": e.stdout,
                "error": e.stderr,
                "return_code": e.returncode
            }


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Run test suite")
    parser.add_argument(
        "--test-type",
        choices=["unit", "integration", "e2e", "performance", "security", "ai_analysis", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--specific-test",
        help="Run specific test file or function"
    )
    parser.add_argument(
        "--filter",
        help="Filter tests by pattern"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.specific_test:
        result = runner.run_specific_test(args.specific_test, args.verbose)
    elif args.filter:
        result = runner.run_tests_with_filter(args.filter, args.verbose)
    elif args.test_type == "all":
        result = runner.run_all_tests(args.verbose)
    else:
        # 特定のテストタイプの実行
        test_functions = {
            "unit": runner.run_unit_tests,
            "integration": runner.run_integration_tests,
            "e2e": runner.run_e2e_tests,
            "performance": runner.run_performance_tests,
            "security": runner.run_security_tests,
            "ai_analysis": runner.run_ai_analysis_tests
        }
        
        if args.test_type in test_functions:
            result = test_functions[args.test_type](args.verbose)
        else:
            print(f"❌ Unknown test type: {args.test_type}")
            sys.exit(1)
    
    # カバレッジレポートの生成
    if args.coverage:
        coverage_result = runner.generate_coverage_report()
        if coverage_result["success"]:
            print("✅ Coverage report generated successfully")
        else:
            print("❌ Failed to generate coverage report")
    
    # 結果の表示
    if result.get("overall_success", result.get("success", False)):
        print("\n🎉 All tests completed successfully!")
        
        if "summary" in result:
            summary = result["summary"]
            print(f"📊 Test Summary:")
            print(f"   Total tests: {summary['total_tests']}")
            print(f"   Passed: {summary['passed_tests']}")
            print(f"   Failed: {summary['failed_tests']}")
            print(f"   Skipped: {summary['skipped_tests']}")
            print(f"   Success rate: {summary['success_rate']:.1f}%")
        
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
