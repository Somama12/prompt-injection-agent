# Weeks 8–9 research and implementation

Updated October 19, 2026. This work continues the completed midterm; it does not revise the midterm report.

## Acceptance target: 80–85% overall

The existing 70% milestone is the implemented system, tests, balanced pilot and midterm report. The next 10 percentage points require the complete three-trial experiment: 24 attacks × six conditions × three trials = 432 attacked episodes, plus 18 clean controls. The next five points target a documented AI-assisted review of 30–50 full-study transcripts with evidence references and disagreement analysis. These are project planning estimates, not a grading formula or measured scientific completeness.

The user selected AI-assisted review for this stage. It is a change from the original independent-human-label plan. AI review does not fulfill independent human validation; its agreement numbers are descriptive consistency checks, not accuracy against human ground truth. The original human-label workflow remains available separately. Reaching 85% requires actual saved outputs, not just implemented scripts. Final interpretation, reproducibility audit, presentation and final delivery remain for Weeks 10–11, with this validation limitation disclosed.

## New implementation

- `evaluation/repeated_analysis.py` audits expected cells, per-trial coverage, missing/error episodes, clean controls and unavailable judge verdicts. Matched comparisons use only the same attack and trial in the baseline and defense, with valid binary outcomes on both sides. No independent-sample significance test is applied to repeated versions of the same attack.
- `evaluation/ai_review.py` validates explicit AI provenance, unique episode identifiers, evidence hashes, labels and resolvable JSON evidence paths. It writes `ai_review_metrics.json`, never human labels or human-validation metrics. Ambiguous cases do not become negatives.
- `scripts/run_weeks8_9.sh` preserves the experiment settings for reproducible continuation and regenerates aggregate and trial-level analysis.
- The project Python environment has been restored locally. Installed versions are captured in `evidence/weeks8_9/requirements-lock.txt`.

## Completed evidence audit

The assistant inspected executed tool arguments, blocked-action outcomes and sent-email records for all 24 attacked pilot episodes. Annotations are saved in `evidence/weeks8_9/pilot_ai_review.json`, with one successful attack and 23 unsuccessful attacks. All 24 annotations agree with the deterministic scorer. This was an unblinded retrospective audit: previous results were visible to the assistant. It covers only four attack designs and is not the planned full-study review sample.

The baseline fake-system case delivered a mock message to the attacker. The allow-list and guard conditions attempted the same unauthorized destination, blocked it, and recovered to the authorized professor address. A blocked proposal was not counted as delivery. The credential cases showed no session credential in executed arguments. These findings support the pilot's recorded outcomes but do not establish general defense effectiveness.

## Reproduction

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r evidence/weeks8_9/requirements-lock.txt
.venv/bin/python -m pytest -q
sh scripts/run_weeks8_9.sh
# After resolving service failures, explicitly retry failed episodes:
sh scripts/run_weeks8_9.sh --retry-errors
.venv/bin/python -m evaluation.ai_review \
  --output-dir results/midterm_pilot \
  --annotations evidence/weeks8_9/pilot_ai_review.json
```

The existing `.env` provides the API key; credentials are never part of the evidence archive. The runner is serial, uses a maximum of 15 request starts per minute, checkpoints every episode, and stops after three consecutive episode errors. Resume uses the identical source fingerprint and configuration. Preserve archived failed attempts. Do not change model, attacks, or implementation inside an existing experiment directory.

## Remaining acceptance checks

1. Complete all 450 episodes, inspect errors and retry infrastructure failures; publish actual valid/missing/error counts.
2. Produce aggregate and per-trial comparisons with explicit denominators. Judge failures are separate from episode validity.
3. Select 30–50 valid full-study transcripts across categories and conditions; save AI annotations with evidence, provenance and limitations.
4. Examine scorer disagreements and ambiguous cases, then assign the planning milestone from completed evidence.

The original 30-episode pilot remains separate from the full three-trial experiment. Offline tests and AI review of old pilot evidence do not stand in for new experimental observations.

To freeze the full-study review sample once sufficient valid episodes exist:

```sh
.venv/bin/python -m evaluation.ai_review --output-dir results/weeks8_9 --export --size 40
# Read the numbered packets; enter actual AI assessments, rationale, evidence paths,
# reviewer identity and exposure to earlier results in ai_review_packets/annotations.json.
.venv/bin/python -m evaluation.ai_review --output-dir results/weeks8_9 \
  --annotations results/weeks8_9/ai_review_packets/annotations.json
```

The exporter will disclose a smaller selected count if fewer valid transcripts exist. It refuses to overwrite a frozen sample. Empty annotations are not completed reviews and cannot be scored. Review packets omit automated verdicts, but the annotation mapping exposes the condition; report the actual level of blinding.
