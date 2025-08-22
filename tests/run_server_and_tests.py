#!/usr/bin/env python3
"""
Single-command launcher:
- Starts the Flask app in a subprocess
- Waits for readiness
- Runs test targets from tests/run_config.json (or CLI args)
- Stops the server on completion

Usage (one IDE command forever):
  Command: python3 tests/run_server_and_tests.py
  Working dir: /Users/rick/Desktop/stuff/code_projects/IBS/trading

Optional CLI override:
  python3 tests/run_server_and_tests.py tests/integration/test_real_data_validation.py
"""
import json
import os
import signal
import subprocess
import sys
import time
from typing import List

import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'tests', 'run_config.json')
BASE_URL = 'http://localhost:5001'


def load_config(cli_targets: List[str]):
    if cli_targets:
        return {
            "targets": cli_targets,
            "server": {
                "path": "start_app.py",
                "ready_url": f"{BASE_URL}/api/system_status",
                "timeout_seconds": 30,
            },
        }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    # default fallback
    return {
        "targets": ["tests/run_everything.py"],
        "server": {
            "path": "start_app.py",
            "ready_url": f"{BASE_URL}/api/system_status",
            "timeout_seconds": 30,
        },
    }


def start_server(server_path: str):
    print(f"🚀 Starting server: {server_path}")
    proc = subprocess.Popen([sys.executable, server_path], cwd=PROJECT_ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc


def wait_for_ready(url: str, timeout: int = 30):
    print(f"⏳ Waiting for server ready: {url} (timeout={timeout}s)")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 500, 404):
                print("✅ Server responded")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    print("❌ Server readiness timeout")
    return False


def run_target(target: str) -> bool:
    print(f"\n==== Running target: {target} ====")
    # If target is a module path, run as script; support unittest module run
    if target.endswith('.py'):
        cmd = [sys.executable, target]
    else:
        # Assume unittest module path
        cmd = [sys.executable, '-m', 'unittest', target, '-v']
    proc = subprocess.Popen(cmd, cwd=PROJECT_ROOT)
    proc.wait()
    code = proc.returncode
    print(f"==== Completed target: {target} (exit {code}) ====")
    return code == 0


def stop_server(proc: subprocess.Popen):
    if proc and proc.poll() is None:
        print("🛑 Stopping server...")
        try:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        print("✅ Server stopped")


def main():
    cli_targets = sys.argv[1:]
    cfg = load_config(cli_targets)

    # Start server
    proc = start_server(cfg['server']['path'])
    try:
        if not wait_for_ready(cfg['server']['ready_url'], cfg['server'].get('timeout_seconds', 30)):
            stop_server(proc)
            return 1

        passed = 0
        total = 0
        for target in cfg.get('targets', []):
            total += 1
            if run_target(target):
                passed += 1

        print("\n==============================")
        print("Launcher Summary:")
        print(f"Passed: {passed}/{total}")
        success_rate = (passed / total * 100) if total else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("==============================")
        return 0 if passed == total else 1

    finally:
        stop_server(proc)


if __name__ == '__main__':
    sys.exit(main())
