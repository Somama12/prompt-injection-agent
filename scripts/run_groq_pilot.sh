#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export LLM_PROVIDER=groq
export GROQ_MODEL=openai/gpt-oss-20b
export GROQ_JUDGE_MODEL=openai/gpt-oss-20b
export GROQ_RPM=5
# Six clean controls and four attacks across six conditions: 30 pilot episodes.
# Stop on the first service/quota error. Resume checkpoints with the same settings.
.venv/bin/python -m evaluation.harness --limit 1 --repeats 1 --stop-after-errors 1 --output-dir results/groq_pilot_v3 "$@"
.venv/bin/python -m evaluation.make_results --output-dir results/groq_pilot_v3
.venv/bin/python -m evaluation.repeated_analysis --output-dir results/groq_pilot_v3
