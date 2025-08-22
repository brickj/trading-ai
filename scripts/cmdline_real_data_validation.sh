#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest tests/integration/test_real_data_validation.py -v
