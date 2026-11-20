# Research completion record

Research cutoff and verification date — November 20, 2026.

## Final working scope

The completed study evaluates security and useful task delivery in a controlled article-to-email workflow. Following the November 10 discussion, the final working scope consists of three completed empirical studies and retrospective validation. The end-to-end comparison uses eight matched Groq designs under six conditions. The delivery-policy comparison uses three recorded final decisions for each of 24 designs and a clean control. The Kimi experiment measures task preservation across five formats of one clean article.

This revises the original 450-episode plan and the subsequent 210-episode Kimi plan. The latter has 18 completed clean controls and 192 unobserved adversarial outcomes. Those unobserved outcomes are an extension outside the working final scope. Instructor approval of this scope has not been recorded. Independent human validation was replaced with explicitly identified AI-assisted review at the user's request.

## Completed acceptance checks

| Component | Verified evidence |
|---|---|
| Implementation | Agent loop, instrumented local tools, six defense conditions, resumable collection and scoring are present. |
| Full-agent comparison | Eight designs have a valid episode under every condition, giving 48 matched outcomes. |
| Raw-score reconciliation | All 66 valid source episodes reproduce the stored security and task scores. Executed sends match mailbox records. One terminal provider error is excluded. |
| Duplicate sensitivity | Replacing the shared design's pilot observations with its later observations leaves every aggregate count unchanged. |
| Case-level comparison | Gains and losses against baseline, per-family counts and omission of each design in turn are saved in the security analysis. |
| Final-decision replay | The local policies reproduce all 75 archived decisions and the stored paired repair results. |
| AI-assisted review | Source-linked outcome labels cover all 75 final proposals. Content annotations cover 93 unique bodies mapped to all 150 Kimi deliveries. |
| Kimi fidelity | All 150 recorded summary-tool outputs reproduce exactly. Delivered summaries preserve the three core figures. |
| Software and analysis checks | Full test output is archived. Additional regression cases reject missing evidence and mismatched metadata and expose gains/losses concealed by equal totals. |
| Reproduction package | Source records, labels, analysis code, configurations and hashes are packaged together. Two isolated runs rebuild the tables, including a run that independently rescores and replays the archived decisions. |

The packaged test log and reproduction receipt are the authoritative outputs for the last two checks.

## Results that answer the research questions

### Security and task preservation

| Condition | Assigned effect, of 8 | Useful delivery without effect, of 8 | Baseline failures recovered | Baseline successes lost |
|---|---:|---:|---:|---:|
| Baseline | 1 | 3 | 0 | 0 |
| Sanitization | 2 | 4 | 1 | 0 |
| Instruction hierarchy | 0 | 7 | 5 | 1 |
| Guard model | 0 | 4 | 1 | 0 |
| Action allow-list | 0 | 3 | 0 | 0 |
| Combined | 0 | 7 | 4 | 0 |

The combined and hierarchy conditions tie on their totals but differ by case. The combined condition preserves all three baseline successes and recovers four failures. The hierarchy condition loses the baseline's role-play success while recovering five failures. Five of the eight cases belong to direct override. Within that family, hierarchy completes five of five useful deliveries without an effect and the combined condition completes four of five. Each other family contributes one case, which is too little evidence to estimate a family-specific success rate reliably.

The leave-one-design-out results show how each of the eight observations affects the totals. They are descriptive sensitivity checks. There is one retained trial per design and condition in this comparison, so the data offer limited evidence of repeatability.

### Delivery-policy repair

Across 72 final proposals for attacked inputs, useful delivery without the assigned effect increased from 12 to 18 after the repair, with six gains and no losses. The two policies each allowed three assigned effects under the goal-aware count. All six gains come from two designs repeated three times. The benefit is therefore localized to those designs. The frozen scorer agreed with the expanded AI-assisted review on 69 of 72 attacked decisions. The three disagreements are repetitions of the marker-inclusion case.

### Clean-input fidelity

Kimi completed 149 of 150 cells on the first attempt and the remaining cell on retry. All final records contain one authorized delivery. The source's capacity, projected electricity share and estimated annual savings are preserved in every reviewed body. Two summaries leave the annual basis of electricity demand implicit. Battery and charging details appear in 73 emails each. The battery appears in 30 of 30 continuous-text cases and one of 30 original-paragraph cases.

All 61 emails whose summary-tool return mentioned the battery retained it. Twelve of the 89 emails whose tool return omitted it recovered the detail elsewhere in the workflow. The agent also had access to the article. This identifies information availability at each stage while leaving the model's internal attribution unobserved.

## Scientific limitations retained in the final conclusions

- Case selection was retrospective and collection stopped in benchmark order.
- Five of eight matched designs belong to one family.
- Both automated outcome measures and the AI-assisted review can have errors.
- The repair was designed after examples had been inspected.
- The five Kimi formats contain one article and share a single task.
- A final-action replay cannot measure model adaptation after an earlier veto.
- Repeated trials of a design do not create new independent designs.
- The observed zero counts apply to the evaluated cases and scoring rule.
- Provider, model and sampling differences prevent a causal provider comparison.

## Reproduction

Unzip output/research_final/Research_Snapshot_Somama_Siddiqui.zip into an empty directory, then run

    python3 -m scripts.verify_research_snapshot

This verifies the manifest and reconstructs the main tables using the standard library and included code.

To independently recompute scores and replay the delivery policies, install requirements.txt in a virtual environment and run

    python -m scripts.verify_research_snapshot --rescore

The verification entry point disables network connections. It reads recorded decisions and operates local mock tools. All evidence and code inputs are covered by the manifest. AI-assisted labels remain recorded judgments whose aggregation is reproducible.

The source workspace also contains scripts/package_research_snapshot.py, which creates the archive and verifies it in a fresh temporary directory. The file output/research_final/reproduction_receipt.json records the archive hash and verification outputs.

## Remaining project delivery work

The research and code for this working scope are ready to support the final paper and presentation. Those deliverables and GitHub publication are subsequent work. The broader Kimi comparison, independent human review, and generalization to additional articles remain extensions. The earlier percentage targets were planning weights, so this record uses completed acceptance checks.
