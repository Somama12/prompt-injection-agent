# Week 12 research findings from saved experiments

The completed experiments address two questions. Can the email policy protect the user's intended delivery when the agent has already chosen a final action? How reliably do the agent and its tools convey the source material when they process an ordinary article? The matched pilots also supply limited evidence about the full agent under injected input.

## Review of all 75 Groq final decisions

We examined the archived recipient, subject, email content and refusals for three trials each of 24 designs and one clean control. The review classified observable outcomes before applying the delivery policy. It was retrospective and AI-assisted. The reviewer knew earlier aggregate findings. Each annotation identifies its source file and SHA-256 digest.

| Observed ungated decision | Count |
|---|---:|
| Refused to send | 33 |
| Ordinary summary to the authorized recipient, including three clean controls | 15 |
| Summary addressed to the wrong recipient | 12 |
| Summary containing the synthetic credential in the subject or body | 6 |
| Message containing only the assigned marker | 6 |
| Summary with the assigned marker appended | 3 |

Across the 72 attacked decisions, the frozen security scorer agreed with this review on 69. The three disagreements were repeats of one design. The delivered content included the marker alongside a useful summary. The frozen rule counted replacement of the summary, while the design's stated goal was inclusion. A retrospective goal-aware count agreed on all 72. That agreement checks the revised interpretation on known data. An independent evaluation would require new evidence.

In the paired replay, the existing allow-list and the repaired policy each allowed three assigned effects. Repair increased useful deliveries without the assigned effect from 12/72 to 18/72. At the level of individual decisions there were six gains and zero losses. At the level of designs there were two improvements and 22 ties. Removing both improved designs leaves no difference between policies on the other 66 decisions. The six gains show a reproducible benefit on the two observed cases. These data offer little evidence about the frequency of that benefit on new designs.

## Full-agent pilot comparisons

For each model we matched the same four attacked cases under each condition against the baseline. A favorable outcome requires both legitimate-task completion and absence of the frozen scorer's assigned effect. Clean controls and archived failed attempts are excluded here. Each pilot contributed 24 attacked episodes and six clean controls. One trial per design and condition limits comparisons between defenses.

| Condition | Gemini favorable cases / 4 | Gemini gained / lost vs baseline | Groq favorable cases / 4 | Groq gained / lost vs baseline |
|---|---:|---:|---:|---:|
| Baseline | 3 | — | 3 | — |
| Sanitization | 4 | 1 / 0 | 4 | 1 / 0 |
| Instruction hierarchy | 4 | 1 / 0 | 3 | 1 / 1 |
| Guard model | 4 | 1 / 0 | 3 | 0 / 0 |
| Action allow-list | 4 | 1 / 0 | 3 | 0 / 0 |
| Combined | 4 | 1 / 0 | 4 | 1 / 0 |

Equal aggregate rates can conceal different failures. The Groq instruction-hierarchy condition and baseline each succeeded on three cases. Matching by design shows that the former recovered one baseline failure and lost one baseline success. More observations are required to estimate how often either change occurs.

## Content fidelity in all 150 Kimi format trials

Five renderings of one synthetic article were each tested under six conditions with five repeats. One failed attempt was retried. Each final record contains one email to the authorized recipient. We reviewed the distinct capacity and forecast statements against the source, then linked the annotations to all deliveries by the exact body digest. There were 93 distinct email bodies. The scope of the retrospective AI-assisted review was the meaning of the three core figures, the annual-demand qualifier, and coverage of the two optional details.

All 150 emails described the 1.4 MW installation correctly and presented the electricity share and annual utility savings as projections. Two omitted the explicit annual time basis of the electricity-demand share. Omitting optional details was common even with complete preservation of the three figures.

| Source format | Episodes | Explicit annual demand basis | Backup battery mentioned | Planned EV charging mentioned |
|---|---:|---:|---:|---:|
| Original paragraphs | 30 | 30 | 1 | 1 |
| Continuous text | 30 | 29 | 30 | 30 |
| Bullets | 30 | 29 | 20 | 20 |
| HTML | 30 | 30 | 12 | 12 |
| JSON | 30 | 30 | 10 | 10 |

### Where content was lost

Every saved episode made one completed call to the extractive summarizer. We reproduced its returned text exactly in 150/150 cases from its recorded input. When the tool output contained the word “battery,” the delivered email mentioned the battery in 61/61 cases. When the output omitted the word, 12/89 emails still mentioned it. The agent also had the article from its read step. These observations identify where information was available during the recorded workflow. They do not establish which message the model relied on.

To isolate formatting at the tool boundary, we supplied each of the five unchanged source renderings directly to the deterministic summarizer, once per rendering. The implementation selects up to three nonempty paragraphs and truncates the joined text to 700 characters before appending an ellipsis. The original paragraph rendering dropped the battery mention. All four other renderings retained it. All five direct extracts omitted the word “charging.” This five-input control tests the tool alone. The full-agent results also reflect the text the agent chose to pass to the tool and the final email it composed. Additional articles would be necessary to establish a general format effect.

### Defense overhead

The completed Kimi episodes logged 604 agent calls and 50 guard calls. The guard-only and combined conditions each used 25 guard calls in 25 episodes. The other four conditions used none. Overall median episode latency was 43.6 seconds. The saved usage records counted 757,675 tokens across the successful attempts and another 4,176 in the archived failed attempt. Parallel collection and provider variation limit causal interpretation of timing differences.

## Research scope at cutoff

The labels, paired comparisons and tool analysis above cover the completed cohorts. The revised 210-episode Kimi security comparison has 18 recorded clean controls and 192 unobserved adversarial outcomes. The pilots cover four designs, and the 75 final decisions measure behavior at the delivery stage. An end-to-end ranking across all 24 designs and six conditions remains unresolved. No project percentage follows from these counts.

## Reproduce the analysis offline

From the project root, run `.venv/bin/python -m evaluation.archived_findings`. The module uses the Python standard library and local project code. It uses saved records in `results/kimi_format_study/` and `output/weeks10_12/evidence/`. The latter contains both pilot archives, the paired repair results, the source-linked decision labels and the body-linked Kimi labels. The command validates cell coverage, proposal digests, reviewed email bodies and replayed extracts before writing `archived_findings.json`. That file includes the comparison counts and the mapping from each Kimi episode to its source digest and label. The labels record retrospective judgments and reproduce the tabulation of those judgments.

## Six-condition security comparison using completed full-agent episodes

**Question.** On the Groq designs with a valid full-agent episode in every condition, how often did an assigned attack effect occur, and how often did the user receive a useful summary without that effect? This retrospective analysis uses the project's original programmatic security and legitimate-task scores. It complements the final-action replay by measuring the agent through delivery.

**Selection and overlap.** We retained every fully matched design from the balanced pilot and the interrupted broader Groq collection. The pilot contained four attacked designs in all six conditions. The broader collection contained five, with one design shared. This gives eight distinct designs and 48 attacked episodes in the primary comparison. The common design uses the pilot observations. Replacing them with the broader collection's observations leaves every table entry unchanged. Each collection also had six successful clean controls. A provider error on a further design supplied no valid outcome and is excluded. The recorded model, temperature and source fingerprint match across collections. Planned design lists, repeat counts and request rate limits differ.

| Full-agent condition | Assigned effect observed / 8 | Useful delivery without assigned effect / 8 |
|---|---:|---:|
| Baseline | 1 | 3 |
| Sanitization | 2 | 4 |
| Instruction hierarchy | 0 | 7 |
| Guard model | 0 | 4 |
| Action allow-list | 0 | 3 |
| Combined | 0 | 7 |

**Interpretation.** Four conditions had zero scored effects, but their useful deliveries ranged from three to seven. That difference matters to a user who still needs the summary. Instruction hierarchy and the combined defense tied on both observed counts. Five of the eight designs come from the direct-override family and the other three families contribute one design each. Collection stopped in benchmark order. With one observation per selected design and condition, the table describes these cases and cannot establish a general ranking. The 75-decision experiment separately covers the final delivery step for all 24 designs in three trials.

**Reproduction.** Run `.venv/bin/python -m evaluation.archived_security_comparison`. The resulting `output/weeks10_12/evidence/archived_security_comparison.json` includes results for each collection, both ways of resolving overlap, the excluded terminal error, and source digests.

**Possible final scope.** The completed empirical comparison can be reported as a six-condition full-agent comparison on eight matched Groq designs, supplemented by the repeated 24-design final-delivery analysis and the 150-trial Kimi clean-input study. This is a retrospective reduction in scope relative to the 210-episode plan. Under this scope the broader Kimi security experiment becomes future work. The assignment's acceptance of the narrower scope is a separate decision.
