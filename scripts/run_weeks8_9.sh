#!/bin/sh
# Run from any directory; preserve the frozen model/configuration when resuming.
set -eu
cd "$(dirname "$0")/.."
export GEMINI_MODEL=gemini-3.1-flash-lite
export GEMINI_JUDGE_MODEL=gemini-3.1-flash-lite
export GEMINI_RPM=15
export GEMINI_THINKING_BUDGET=0
.venv/bin/python -m evaluation.harness --repeats 3 --output-dir results/weeks8_9 "$@"
.venv/bin/python -m evaluation.make_results --output-dir results/weeks8_9
.venv/bin/python -m evaluation.repeated_analysis --output-dir results/weeks8_9
