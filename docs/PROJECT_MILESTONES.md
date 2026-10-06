# Project completion plan through Week 11

These weights are planning estimates for the whole research project, not an instructor-issued grading formula or a measured percentage of research quality. The target is 70% at the Week 7 midterm and 100% by Week 11. A milestone earns its weight only when its acceptance evidence exists.

| Milestone | Weight | Acceptance evidence | Current status |
|---|---:|---|---|
| Research scope and experimental design | 10% | Fixed task, threat model, outcomes and documented protocol | Implemented and documented |
| Agent and mock tool environment | 10% | Working agent loop, tool logs and live clean-task execution | Implemented; live baseline verified |
| Attack benchmark | 10% | 24 unique attacks, four categories, integrity tests | Complete |
| Defense implementations | 10% | Four individual defenses and composite, plus baseline | Implemented and tested |
| Reproducible evaluation and validation tooling | 10% | Atomic checkpoints, resume, repeat support, isolated configurations, scoring, plots, human review workflow | Implemented and tested |
| Software verification | 5% | Passing regression and offline integration tests; archived output | 40 tests passed |
| Balanced pilot and preliminary analysis | 10% | 24 valid attacked episodes, six valid clean controls, observed results table and figure, limitations | Complete: 30 valid pilot episodes, saved results and preliminary analysis |
| Cumulative midterm report | 5% | All seven rubric sections, Weeks 1-7 evidence, plan comparison | Complete: expanded LaTeX report with frozen evidence and appendices |
| Full evaluation and repeated trials | 10% | 24 attacks x six conditions with three trials, clean controls, reviewed failures | Planned for Weeks 8-9 |
| Independent human validation | 10% | 30-50 human-reviewed transcripts, ambiguity counts, agreement/precision/recall | Tooling ready; independent labels pending |
| Final analysis and delivery | 10% | Supported conclusions, limitations, reproducible evidence, final report and presentation | Planned for Weeks 10-11 |

The first six milestones account for 55% under this plan. The balanced pilot and cumulative report bring the target to 70%. No empirical conclusion is inferred from passing unit tests alone.

## Week 7 target

Finish the balanced pilot, retry failed episodes, inspect transcripts and preliminary outputs, publish the tested implementation branch, and prepare the cumulative midterm report. If provider quotas prevent completion, report the actual number of valid observations rather than calling the pilot finished.

## Week 8 target

Complete the first full 144-cell attack grid and six clean controls. Use the pilot to review the outcome definitions before freezing the full protocol. Export a stratified sample of 30-50 transcripts for independent human review. Retain existing results if the source or configuration changes; start a new run directory rather than mixing conditions.

## Week 9 target

Complete the remaining two trials of the primary model experiment, yielding 432 attacked episodes and 18 clean controls in the three-trial experiment. Finish independent human labels and compute validation metrics. Track infrastructure failures separately and retry them where possible. Do not treat repeated observations of one attack as new independent attacks.

## Week 10 target

Analyze defense differences, legitimate-task performance, observed latency and guard-call overhead. Review ambiguous and disagreeing cases. Explain sampling limitations and uncertainty. If the core evaluation and validation are complete and quota permits, add a second model or six more attacks as an extension; do not let optional expansion displace the original deliverables.

## Week 11 target

Finalize the research report and presentation, verify that every result is traceable to a saved run and code version, publish reproducibility instructions and the final code, and rehearse the demonstration. Completion means all promised core deliverables exist and have been checked, not just that the code runs.

## Changes since Progress Report 2

Implemented per-episode resume/checkpointing and an explicit human-label workflow that were described in the earlier report but were not present in the supplied code. Added repeat support, source/configuration fingerprints, archived error retries, separate valid/error counts, corrected recipient scoring, strict boolean judge validation, safe guard failures, composite guard-call accounting, malformed-action checks, and expanded the test suite from 10 to 40 tests.

Model availability and quota were checked with the existing API key. Gemini 3.6 Flash completed a clean run but exposed a five-request-per-minute quota. The balanced pilot uses the project's previously configured Gemini 3.1 Flash-Lite in a separate run directory. Model-specific findings must remain separate.

## Verified midterm milestone

The balanced pilot completed all 30 episodes after retrying network-interrupted runs: six clean controls and 24 attacked episodes. The baseline recorded one successful attack out of four; each defended condition recorded zero out of four. Three model-judge verdicts are unavailable and are excluded from judge metrics. The expanded LaTeX report includes these limitations. These deliverables satisfy the defined 70% planning milestone; the full experiment and independent human validation remain for Weeks 8-11.
