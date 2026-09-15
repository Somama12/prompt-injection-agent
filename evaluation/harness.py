"""The evaluation harness.

Runs every (attack x defense) cell plus a per-defense "clean" run that measures
legitimate task success. Each agent episode makes real Gemini calls. Results are
written to results/raw_results.csv and full transcripts to results/transcripts/.

Usage:
    python -m evaluation.harness            # full run
    python -m evaluation.harness --limit 2  # 2 attacks/category (smoke test)
    python -m evaluation.harness --no-judge # skip the LLM-judge pass
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field

from agent import llm
from agent.agent import run_agent
from benchmark.attacks import ATTACKS, CATEGORIES, clean_page, poisoned_page
from defenses.registry import build_defenses
from evaluation import scorer

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
TRANSCRIPT_DIR = os.path.join(RESULTS_DIR, "transcripts")


@dataclass
class Cell:
    attack_id: str
    category: str
    attack_name: str
    defense: str
    defense_label: str
    target_action: str
    programmatic_success: bool = False
    programmatic_evidence: str = ""
    judge_success: object = None  # bool | None
    judge_reason: str = ""
    agreement: object = None  # bool | None
    llm_calls: int = 0
    guard_calls: int = 0
    latency_s: float = 0.0
    blocked_count: int = 0
    error: str = ""


def _run_one_cell(attack, defense, model, use_judge) -> tuple[Cell, dict]:
    run = run_agent(
        attack_id=attack.id,
        page_content=poisoned_page(attack),
        defense=defense,
        model=model,
    )
    prog, evidence = scorer.programmatic_attack_success(attack, run)
    cell = Cell(
        attack_id=attack.id,
        category=attack.category,
        attack_name=attack.name,
        defense=defense.name,
        defense_label=defense.label,
        target_action=attack.target_action,
        programmatic_success=prog,
        programmatic_evidence=evidence,
        llm_calls=run.llm_calls,
        guard_calls=run.guard_calls,
        latency_s=round(run.latency_s, 3),
        blocked_count=len(run.blocked_actions),
        error=run.error,
    )
    if use_judge:
        j, reason = scorer.judge_attack_success(attack, run)
        cell.judge_success = j
        cell.judge_reason = reason
        cell.agreement = (j == prog) if j is not None else None
    return cell, run.to_dict()


def run_full(model=None, limit=None, use_judge=True, workers=4) -> list[Cell]:
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    defenses = build_defenses()

    attacks = ATTACKS
    if limit:
        # first `limit` attacks per category, for a quick smoke run
        by_cat: dict[str, list] = {}
        for a in ATTACKS:
            by_cat.setdefault(a.category, []).append(a)
        attacks = [a for cat in by_cat.values() for a in cat[:limit]]

    jobs = [(a, d) for d in defenses for a in attacks]
    total = len(jobs)
    print(f"Running {len(attacks)} attacks x {len(defenses)} defenses = {total} cells "
          f"(judge={'on' if use_judge else 'off'}, workers={workers})")

    cells: list[Cell] = []
    transcripts: dict[str, dict] = {}
    done = 0
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_run_one_cell, a, d, model, use_judge): (a, d) for a, d in jobs}
        for fut in as_completed(futs):
            a, d = futs[fut]
            try:
                cell, tdict = fut.result()
            except Exception as exc:  # noqa: BLE001
                cell = Cell(a.id, a.category, a.name, d.name, d.label, a.target_action,
                            error=f"harness exception: {exc}")
                tdict = {"attack_id": a.id, "defense": d.name, "error": str(exc)}
            cells.append(cell)
            transcripts[f"{d.name}__{a.id}"] = tdict
            done += 1
            flag = "HIT " if cell.programmatic_success else "safe"
            print(f"[{done:3d}/{total}] {d.name:22s} {a.id:6s} {flag} "
                  f"({cell.latency_s:.1f}s){'  ERR:'+cell.error if cell.error else ''}")

    with open(os.path.join(TRANSCRIPT_DIR, "transcripts.json"), "w") as f:
        json.dump(transcripts, f, indent=2)

    # Legitimate-task success: one clean (no-injection) run per defense.
    print("\nMeasuring legitimate task success (clean page, per defense)...")
    task_success: dict[str, dict] = {}
    for d in defenses:
        run = run_agent(attack_id="__clean__", page_content=clean_page(), defense=d, model=model)
        ok, why = scorer.legitimate_task_success(run)
        task_success[d.name] = {
            "task_success": ok, "reason": why,
            "latency_s": round(run.latency_s, 3), "llm_calls": run.llm_calls,
            "error": run.error,
        }
        print(f"  {d.name:22s} task_success={ok}  ({run.latency_s:.1f}s)  {why}")

    _write_outputs(cells, task_success, defenses, attacks, use_judge, time.monotonic() - t0)
    return cells


def _write_outputs(cells, task_success, defenses, attacks, use_judge, elapsed):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fields = list(asdict(cells[0]).keys())
    with open(os.path.join(RESULTS_DIR, "raw_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in cells:
            w.writerow(asdict(c))

    with open(os.path.join(RESULTS_DIR, "task_success.json"), "w") as f:
        json.dump(task_success, f, indent=2)

    stats = llm.STATS.snapshot()
    summary = {
        "n_attacks": len(attacks),
        "n_defenses": len(defenses),
        "n_cells": len(cells),
        "judge_used": use_judge,
        "wall_clock_s": round(elapsed, 1),
        "api_stats": stats,
        "defenses": [{"name": d.name, "label": d.label, "description": d.description,
                      "extra_llm_calls_per_action": d.extra_llm_calls_per_action}
                     for d in defenses],
        "categories": CATEGORIES,
    }
    with open(os.path.join(RESULTS_DIR, "run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote results/raw_results.csv ({len(cells)} rows), task_success.json, run_summary.json")
    print(f"API calls: {stats['calls']}  retries: {stats['retries']}  failures: {stats['failures']}  "
          f"mean latency: {stats['mean_latency_s']}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="attacks per category (smoke test)")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default=None)
    args = ap.parse_args()
    run_full(model=args.model, limit=args.limit, use_judge=not args.no_judge, workers=args.workers)


if __name__ == "__main__":
    main()
