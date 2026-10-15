import os
import time
import json
import unittest
from datetime import datetime
from typing import Dict, Any, Tuple


class ReportManager:
    """
    Automated Timestamped Reporting Engine.
    Creates structured, date-stamped reports for launches and test executions:
    - reports/launches/YYYY-MM-DD_HH-MM-SS/
    - reports/tests/YYYY-MM-DD_HH-MM-SS/
    """
    def __init__(self, base_reports_dir: str = "reports"):
        self.base_reports_dir = base_reports_dir
        self.launches_dir = os.path.join(base_reports_dir, "launches")
        self.tests_dir = os.path.join(base_reports_dir, "tests")
        os.makedirs(self.launches_dir, exist_ok=True)
        os.makedirs(self.tests_dir, exist_ok=True)

    @staticmethod
    def get_timestamp_folder() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def create_launch_report(self, launch_type: str, stats: Dict[str, Any]) -> str:
        """Creates a timestamped report folder under reports/launches/."""
        folder_name = self.get_timestamp_folder()
        report_path = os.path.join(self.launches_dir, folder_name)
        os.makedirs(report_path, exist_ok=True)

        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "launch_type": launch_type,
            "metrics": stats,
        }

        json_file = os.path.join(report_path, "launch_summary.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        txt_file = os.path.join(report_path, "launch_summary.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("=== ZOMBIE AI SIMULATION LAUNCH REPORT ===\n")
            f.write(f"Timestamp   : {summary_data['timestamp']}\n")
            f.write(f"Launch Type : {launch_type}\n")
            f.write("-" * 45 + "\n")
            for k, v in stats.items():
                f.write(f"{k:20s}: {v}\n")

        print(f"[ReportManager] Launch report generated at: {report_path}")
        return report_path

    def run_tests_and_report(self, start_dir: str = "tests") -> Tuple[bool, str]:
        """Executes unit tests and creates a timestamped report folder under reports/tests/."""
        folder_name = self.get_timestamp_folder()
        report_path = os.path.join(self.tests_dir, folder_name)
        os.makedirs(report_path, exist_ok=True)

        log_file_path = os.path.join(report_path, "test_results.txt")
        json_file_path = os.path.join(report_path, "test_results.json")

        loader = unittest.TestLoader()
        suite = loader.discover(start_dir)

        start_time = time.time()
        with open(log_file_path, "w", encoding="utf-8") as stream:
            runner = unittest.TextTestRunner(stream=stream, verbosity=2)
            result = runner.run(suite)
        elapsed = time.time() - start_time

        test_data = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "passed": result.wasSuccessful(),
            "elapsed_seconds": round(elapsed, 4),
            "failure_details": [f"{test}: {msg}" for test, msg in result.failures],
            "error_details": [f"{test}: {msg}" for test, msg in result.errors],
        }

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        print(f"[ReportManager] Test suite executed: {result.testsRun} tests in {elapsed:.3f}s. Passed: {result.wasSuccessful()}")
        print(f"[ReportManager] Test report generated at: {report_path}")
        return result.wasSuccessful(), report_path
