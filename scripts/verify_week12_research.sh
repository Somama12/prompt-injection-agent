#!/bin/sh
# Offline research verification. No model requests; no assignment documents created.
set -eu
cd "$(dirname "$0")/.."
p=output/weeks10_12/evidence
.venv/bin/python -m evaluation.week12_results "$p" > "$p/repeated_live_results.json.tmp"
mv "$p/repeated_live_results.json.tmp" "$p/repeated_live_results.json"
.venv/bin/python -m evaluation.week12_review "$p" > "$p/review_comparison.json.tmp"
mv "$p/review_comparison.json.tmp" "$p/review_comparison.json"
.venv/bin/python -m evaluation.credential_probe > "$p/probe.json"
.venv/bin/python -m evaluation.encoding_sensitivity > "$p/heldout.json"
.venv/bin/python -m evaluation.target_action_matrix > "$p/action_matrix.json"
.venv/bin/python -m pytest -q
