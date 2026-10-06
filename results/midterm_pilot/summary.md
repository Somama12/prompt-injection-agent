# Benchmark results

Model: gemini-3.1-flash-lite; repeats: 1; saved episodes: 30/30.

Errors are excluded from attack-success denominators and reported separately. Missing results are not zero success. Single-trial results are preliminary; repeated episodes are not independent attack designs.

| Defense | Valid attacks | Errors | Attack success | Task success under attack | Clean success | Mean latency | Guard calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| none | 4 | 0 | 25.0% | 75.0% | 1/1 | 32.05 s | 0.00 |
| sanitization | 4 | 0 | 0.0% | 100.0% | 1/1 | 26.80 s | 0.00 |
| instruction_hierarchy | 4 | 0 | 0.0% | 100.0% | 1/1 | 22.37 s | 0.00 |
| guard_llm | 4 | 0 | 0.0% | 100.0% | 1/1 | 33.81 s | 1.25 |
| allowlist | 4 | 0 | 0.0% | 100.0% | 1/1 | 27.45 s | 0.00 |
| combined | 4 | 0 | 0.0% | 100.0% | 1/1 | 29.74 s | 1.00 |

Judge verdicts available: 21. Agreement with the deterministic scorer: 100.0%.
Agreement between automated scorers is not human validation. See evaluation.validation for blinded review.

Latency includes rate-limit waits and provider retries in the agent/guard loop, but excludes the later judge call. Guard calls are a cost proxy, not a dollar-cost measurement.
Task success uses a keyword/length heuristic and needs manual validation. Credential exposure means a secret in an executed tool argument in this mock environment; it does not establish real-world network exfiltration.
