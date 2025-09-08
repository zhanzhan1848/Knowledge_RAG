#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Knowledge RAG System - 测试运行脚本
提供便捷的测试执行命令和测试报告生成功能
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestRunner:
    """测试运行器类"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "reports"
        self.ensure_reports_dir()

    def ensure_reports_dir(self):
        """确保报告目录存在"""
        self.reports_dir.mkdir(exist_ok=True)
        (self.reports_dir / "coverage").mkdir(exist_ok=True)
        (self.reports_dir / "performance").mkdir(exist_ok=True)

    def run_command(self, cmd: List[str], description: str) -> bool:
        """运行命令并处理结果"""
        print(f"\n🚀 {description}")
        print(f"执行命令: {' '.join(cmd)}")
        print("-" * 60)

        try:
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=False, text=True, check=False
            )

            if result.returncode == 0:
                print(f"\n✅ {description} 成功完成")
                return True
            else:
                print(f"\n❌ {description} 失败 (退出码: {result.returncode})")
                return False

        except Exception as e:
            print(f"\n💥 {description} 执行出错: {e}")
            return False

    def run_unit_tests(self, verbose: bool = False, coverage: bool = True) -> bool:
        """运行单元测试"""
        cmd = ["python", "-m", "pytest", "tests/unit/"]

        if verbose:
            cmd.extend(["-v", "-s"])

        if coverage:
            cmd.extend(
                [
                    "--cov=src",
                    "--cov-report=html:reports/coverage/unit",
                    "--cov-report=term-missing",
                    "--cov-report=xml:reports/coverage/unit_coverage.xml",
                ]
            )

        cmd.extend(
            [
                "-m",
                "unit",
                "--junitxml=reports/unit_tests.xml",
                "--html=reports/unit_report.html",
                "--self-contained-html",
            ]
        )

        return self.run_command(cmd, "单元测试")

    def run_integration_tests(self, verbose: bool = False) -> bool:
        """运行集成测试"""
        cmd = ["python", "-m", "pytest", "tests/integration/"]

        if verbose:
            cmd.extend(["-v", "-s"])

        cmd.extend(
            [
                "-m",
                "integration",
                "--junitxml=reports/integration_tests.xml",
                "--html=reports/integration_report.html",
                "--self-contained-html",
            ]
        )

        return self.run_command(cmd, "集成测试")

    def run_e2e_tests(self, verbose: bool = False) -> bool:
        """运行端到端测试"""
        cmd = ["python", "-m", "pytest", "tests/e2e/"]

        if verbose:
            cmd.extend(["-v", "-s"])

        cmd.extend(
            [
                "-m",
                "e2e",
                "--junitxml=reports/e2e_tests.xml",
                "--html=reports/e2e_report.html",
                "--self-contained-html",
            ]
        )

        return self.run_command(cmd, "端到端测试")

    def run_performance_tests(self, verbose: bool = False) -> bool:
        """运行性能测试"""
        cmd = ["python", "-m", "pytest", "tests/performance/"]

        if verbose:
            cmd.extend(["-v", "-s"])

        cmd.extend(
            [
                "-m",
                "performance",
                "--junitxml=reports/performance_tests.xml",
                "--html=reports/performance_report.html",
                "--self-contained-html",
                "--durations=0",  # 显示所有测试的执行时间
            ]
        )

        return self.run_command(cmd, "性能测试")

    def run_all_tests(self, verbose: bool = False, parallel: bool = False) -> bool:
        """运行所有测试"""
        cmd = ["python", "-m", "pytest", "tests/"]

        if verbose:
            cmd.extend(["-v", "-s"])

        if parallel:
            cmd.extend(["-n", "auto"])  # 需要安装 pytest-xdist

        cmd.extend(
            [
                "--cov=src",
                "--cov-report=html:reports/coverage/all",
                "--cov-report=term-missing",
                "--cov-report=xml:reports/coverage/all_coverage.xml",
                "--junitxml=reports/all_tests.xml",
                "--html=reports/all_report.html",
                "--self-contained-html",
            ]
        )

        return self.run_command(cmd, "所有测试")

    def run_specific_tests(
        self, test_path: str, markers: Optional[List[str]] = None, verbose: bool = False
    ) -> bool:
        """运行指定的测试"""
        cmd = ["python", "-m", "pytest", test_path]

        if verbose:
            cmd.extend(["-v", "-s"])

        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])

        cmd.extend(
            [
                "--junitxml=reports/specific_tests.xml",
                "--html=reports/specific_report.html",
                "--self-contained-html",
            ]
        )

        return self.run_command(cmd, f"指定测试: {test_path}")

    def run_failed_tests(self, verbose: bool = False) -> bool:
        """重新运行失败的测试"""
        cmd = ["python", "-m", "pytest", "--lf"]

        if verbose:
            cmd.extend(["-v", "-s"])

        cmd.extend(
            [
                "--junitxml=reports/failed_tests.xml",
                "--html=reports/failed_report.html",
                "--self-contained-html",
            ]
        )

        return self.run_command(cmd, "重新运行失败的测试")

    def run_coverage_report(self) -> bool:
        """生成覆盖率报告"""
        cmd = ["python", "-m", "coverage", "html", "-d", "reports/coverage/detailed"]
        success1 = self.run_command(cmd, "生成HTML覆盖率报告")

        cmd = ["python", "-m", "coverage", "xml", "-o", "reports/coverage/coverage.xml"]
        success2 = self.run_command(cmd, "生成XML覆盖率报告")

        cmd = ["python", "-m", "coverage", "report"]
        success3 = self.run_command(cmd, "显示覆盖率摘要")

        return success1 and success2 and success3

    def clean_cache(self) -> bool:
        """清理测试缓存"""
        cache_dirs = [
            ".pytest_cache",
            "__pycache__",
            ".coverage",
            ".testmondata",
            "htmlcov",
        ]

        for cache_dir in cache_dirs:
            cache_path = self.project_root / cache_dir
            if cache_path.exists():
                if cache_path.is_file():
                    cache_path.unlink()
                    print(f"删除文件: {cache_path}")
                else:
                    import shutil

                    shutil.rmtree(cache_path)
                    print(f"删除目录: {cache_path}")

        # 清理Python缓存
        cmd = ["find", ".", "-name", "*.pyc", "-delete"]
        self.run_command(cmd, "清理Python缓存文件")

        cmd = [
            "find",
            ".",
            "-name",
            "__pycache__",
            "-type",
            "d",
            "-exec",
            "rm",
            "-rf",
            "{}",
            "+",
        ]
        self.run_command(cmd, "清理__pycache__目录")

        print("\n🧹 测试缓存清理完成")
        return True

    def generate_test_summary(self) -> str:
        """生成测试摘要报告"""
        summary = f"""
📊 Knowledge RAG System - 测试执行摘要
{'='*60}

测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
项目路径: {self.project_root}

📁 测试报告位置:
  - HTML报告: {self.reports_dir}/
  - 覆盖率报告: {self.reports_dir}/coverage/
  - JUnit XML: {self.reports_dir}/*.xml

🔧 可用的测试命令:
  python scripts/run_tests.py --unit          # 运行单元测试
  python scripts/run_tests.py --integration   # 运行集成测试
  python scripts/run_tests.py --e2e          # 运行端到端测试
  python scripts/run_tests.py --performance  # 运行性能测试
  python scripts/run_tests.py --all          # 运行所有测试
  python scripts/run_tests.py --failed       # 重新运行失败的测试
  python scripts/run_tests.py --clean        # 清理测试缓存

📋 测试标记说明:
  -m unit         # 单元测试
  -m integration  # 集成测试
  -m e2e         # 端到端测试
  -m performance # 性能测试
  -m slow        # 慢速测试
  -m auth        # 认证相关测试
  -m document    # 文档处理测试
  -m vector      # 向量搜索测试
  -m qa          # 问答测试

{'='*60}
"""
        return summary


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Knowledge RAG System 测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python scripts/run_tests.py --unit -v          # 详细运行单元测试
  python scripts/run_tests.py --all --parallel   # 并行运行所有测试
  python scripts/run_tests.py --specific tests/unit/test_auth_service.py
  python scripts/run_tests.py --markers auth document
        """,
    )

    # 测试类型选项
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument("--unit", action="store_true", help="运行单元测试")
    test_group.add_argument("--integration", action="store_true", help="运行集成测试")
    test_group.add_argument("--e2e", action="store_true", help="运行端到端测试")
    test_group.add_argument("--performance", action="store_true", help="运行性能测试")
    test_group.add_argument("--all", action="store_true", help="运行所有测试")
    test_group.add_argument("--failed", action="store_true", help="重新运行失败的测试")
    test_group.add_argument("--specific", type=str, help="运行指定路径的测试")

    # 其他选项
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--parallel", action="store_true", help="并行运行测试")
    parser.add_argument("--no-coverage", action="store_true", help="跳过覆盖率统计")
    parser.add_argument("--markers", nargs="+", help="指定测试标记")
    parser.add_argument("--clean", action="store_true", help="清理测试缓存")
    parser.add_argument("--coverage-report", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--summary", action="store_true", help="显示测试摘要")

    args = parser.parse_args()

    # 创建测试运行器
    runner = TestRunner(project_root)

    # 显示摘要
    if args.summary:
        print(runner.generate_test_summary())
        return

    # 清理缓存
    if args.clean:
        runner.clean_cache()
        return

    # 生成覆盖率报告
    if args.coverage_report:
        runner.run_coverage_report()
        return

    # 执行测试
    success = False

    if args.unit:
        success = runner.run_unit_tests(args.verbose, not args.no_coverage)
    elif args.integration:
        success = runner.run_integration_tests(args.verbose)
    elif args.e2e:
        success = runner.run_e2e_tests(args.verbose)
    elif args.performance:
        success = runner.run_performance_tests(args.verbose)
    elif args.all:
        success = runner.run_all_tests(args.verbose, args.parallel)
    elif args.failed:
        success = runner.run_failed_tests(args.verbose)
    elif args.specific:
        success = runner.run_specific_tests(args.specific, args.markers, args.verbose)
    else:
        # 默认运行单元测试
        print("\n💡 未指定测试类型，默认运行单元测试")
        print("使用 --help 查看所有可用选项\n")
        success = runner.run_unit_tests(args.verbose, not args.no_coverage)

    # 输出结果
    if success:
        print("\n🎉 测试执行成功！")
        print(f"📊 查看详细报告: {runner.reports_dir}")
        sys.exit(0)
    else:
        print("\n💥 测试执行失败！")
        print(f"📋 查看错误报告: {runner.reports_dir}")
        sys.exit(1)


if __name__ == "__main__":
    main()
