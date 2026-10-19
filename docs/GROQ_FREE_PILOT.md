# Groq free-plan pilot

Prepared October 19, 2026. No live Groq result is claimed yet.

Groq's published free-plan limits for `openai/gpt-oss-20b` are 30 requests/minute,
1,000 requests/day, 8,000 tokens/minute and 200,000 tokens/day. Actual account limits
may differ. Source: https://console.groq.com/docs/rate-limits
The advertised generation speed is not an end-to-end benchmark estimate. The daily
token quota may require the full experiment to span multiple days.

## Account setup

Create a free Groq account and a key at https://console.groq.com/keys.
Confirm the account is on the Free plan; do not enable a paid plan for this task.
Add these entries to the existing ignored `.env` file locally:

```dotenv
GROQ_API_KEY=your-local-key
GROQ_FREE_PLAN_CONFIRMED=1
```

The confirmation flag records the user's account check. It cannot enforce billing
on a paid account. The code does not create accounts, change billing, upgrade plans,
or fall back to a different provider. Never publish `.env` or paste a key into chat.

## Run and evaluate

```sh
sh scripts/run_groq_pilot.sh --max-runs 1
# Inspect the clean control, latency, parsing, and any provider error first.
sh scripts/run_groq_pilot.sh
# Explicitly retry error checkpoints only after addressing their cause:
sh scripts/run_groq_pilot.sh --retry-errors
```

The full pilot contains 30 episodes: six controls and four representative attacks
across six conditions. Five request starts per minute is a conservative initial
setting; token quotas can still be reached. A 429 response raises a quota error
without automatic provider retries. The runner stops after one episode error;
unavailable judge verdicts are recorded separately. No real email is sent.

The agent, guard and judge all use the explicitly selected Groq model. GPT-OSS uses
low reasoning effort; output budgets remain the existing per-call budgets. Truncated
or empty answers fail rather than becoming successful responses. A pilot may show
that reasoning token budgets need adjustment; any such adjustment requires a new
experiment directory/configuration before collecting comparable results.

Gemini data remains separate. Provider and reasoning effort are recorded in schema-3
manifests. The source fingerprint changed with this adapter: earlier schema-2 Gemini
runs must be resumed using their original code/configuration (the Week 8–9 run used
commit dbb56d2's agent/harness source), not silently resumed with the new adapter.
Do not combine the Gemini pilot and Groq observations as one model's results.

Only after valid controls and a representative attack pilot will we choose the
full-study schedule and estimate completion time from measured performance.

## Live compatibility findings

The account owner confirmed Free-plan status. A minimal request authenticated
successfully. The first two clean-control configurations were rejected with HTTP
400 because GPT-OSS emitted native tool intent despite the text ACTION prompt.
These failed attempts remain in `results/groq_pilot` and `results/groq_pilot_v2`.

The revised adapter declares only the three local mock tools and converts one native
function call into the existing ACTION format. It never executes a tool remotely;
the existing parser, defenses and local dispatcher still decide execution. Guard
and judge requests receive no tool definitions. This is a provider-specific action
transport difference and must be disclosed in comparisons with Gemini. The revised
pilot directory is `results/groq_pilot_v3`; the script now targets that directory.
