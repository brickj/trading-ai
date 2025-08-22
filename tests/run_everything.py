#!/usr/bin/env python3
"""
Unified Python Test Runner (no shell required)
- Verifies server availability
- Runs comprehensive system, frontend, integration, and real-data validation tests
- Prints a clear summary
"""
import os
import sys
import time
import subprocess
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
BASE_URL = os.environ.get("TRADING_APP_URL", "http://localhost:5001")


def check_server(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{BASE_URL}/api/system_status", timeout=2)
            if r.status_code in (200, 500, 404):
                return True
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    return False


def run_py(cmd, name):
    print(f"\n==== Running: {name} ====")
    proc = subprocess.Popen([sys.executable, *cmd], cwd=PROJECT_ROOT)
    proc.wait()
    code = proc.returncode
    print(f"==== Completed: {name} (exit {code}) ====")
    return code == 0


def run_unittest(module_path, name):
    print(f"\n==== Running unittest: {name} ====")
    proc = subprocess.Popen([sys.executable, "-m", "unittest", module_path, "-v"], cwd=PROJECT_ROOT)
    proc.wait()
    code = proc.returncode
    print(f"==== Completed unittest: {name} (exit {code}) ====")
    return code == 0


def main():
    print("🧪 Unified Test Runner")
    print("Project Root:", PROJECT_ROOT)
    print("Target URL:", BASE_URL)

    # Ensure server is up first
    if not check_server(timeout=12):
        print("❌ Server is not responding at", BASE_URL)
        print("Please start it in another terminal: python3 start_app.py")
        return 1

    passed = 0
    total = 0

    # 1) Comprehensive system test (python-only)
    total += 1
    if run_py(["tests/comprehensive_system_test.py"], "Comprehensive System Test"):
        passed += 1

    # 2) Frontend page tests (requests-based)
    total += 1
    if run_py(["tests/comprehensive_frontend_test.py"], "Comprehensive Frontend Test"):
        passed += 1

    # 3) Integration runner (python-only orchestrator)
    total += 1
    if run_py(["tests/run_comprehensive_tests.py"], "Integration Orchestrator"):
        passed += 1

    # 4) New real data validation test (unittest discovery)
    total += 1
    if run_unittest("tests/integration/test_real_data_validation.py", "Real Data Validation"):
        passed += 1

    print("\n==============================")
    print("Test Summary:")
    print(f"Passed: {passed}/{total}")
    success_rate = (passed / total * 100) if total else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print("==============================")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
