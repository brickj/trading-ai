#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash run_comprehensive_tests.sh
