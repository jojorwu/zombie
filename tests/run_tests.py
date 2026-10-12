#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.simulation.reporter import ReportManager


def main():
    print("=" * 65)
    print("        ZOMBIE AI SIMULATION AUTOMATED TEST RUNNER")
    print("=" * 65)
    reporter = ReportManager()
    success, report_path = reporter.run_tests_and_report(start_dir="tests")
    print(f"Test Execution Report: {report_path}")
    print("=" * 65)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
