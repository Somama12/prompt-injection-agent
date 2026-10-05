"""Resumable, serial benchmark. Each completed episode is saved atomically."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from agent import llm
from agent.agent import run_agent
from benchmark.attacks import ATTACKS, CATEGORIES, clean_page, poisoned_page
from defenses.registry import build_defenses, DEFENSE_ORDER
from evaluation import scorer

RESULTS_DIR = Path(__file__).resolve().parents[1] / 'results'

@dataclass
class Cell:
    run_id: str
    attack_id: str
    category: str
    defense: str
    defense_label: str
    trial: int
    model: str
    status: str = 'ok'
    programmatic_success: bool | None = None
    programmatic_evidence: str = ''
    judge_success: bool | None = None
    judge_reason: str = ''
    legitimate_success: bool = False
    legitimate_reason: str = ''
    llm_calls: int = 0
    guard_calls: int = 0
    latency_s: float = 0
    blocked_count: int = 0
    error: str = ''


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    with temp.open('w') as f:
        json.dump(value, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def source_digest():
    root = Path(__file__).resolve().parents[1]
    h = hashlib.sha256()
    for folder in ('agent', 'benchmark', 'defenses'):
        for p in sorted((root / folder).glob('*.py')):
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    for name in ('harness.py', 'scorer.py'):
        h.update((root / 'evaluation' / name).read_bytes())
    return h.hexdigest()


def _run_one(attack, defense_name, trial, model, use_judge):
    # A fresh defense instance prevents state leakage between episodes.
    defense = next(d for d in build_defenses() if d.name == defense_name)
    aid = attack.id if attack else '__clean__'
    rid = f'{defense_name}__{aid}__{trial:03d}'
    cell = Cell(rid, aid, attack.category if attack else 'clean', defense_name,
                defense.label, trial, model)
    started = time.monotonic()
    try:
        run = run_agent(attack_id=aid, page_content=poisoned_page(attack) if attack else clean_page(),
                        defense=defense, model=model)
        cell.llm_calls, cell.guard_calls = run.llm_calls, run.guard_calls
        cell.blocked_count = len(run.blocked_actions)
        cell.latency_s = round(run.latency_s, 3)
        cell.error = run.error
        cell.status = 'error' if run.error else 'ok'
        cell.legitimate_success, cell.legitimate_reason = scorer.legitimate_task_success(run)
        if attack:
            cell.programmatic_success, cell.programmatic_evidence = scorer.programmatic_attack_success(attack, run)
            if use_judge and not run.error:
                cell.judge_success, cell.judge_reason = scorer.judge_attack_success(attack, run)
        return {'cell': asdict(cell), 'run': run.to_dict()}
    except Exception as exc:
        cell.status = 'error'
        cell.error = str(exc).replace(os.environ.get('GEMINI_API_KEY') or '__NO_KEY__', '[REDACTED]')
        cell.latency_s = round(time.monotonic() - started, 3)
        return {'cell': asdict(cell), 'run': {'error': cell.error}}


def load_records(output):
    return [json.loads(p.read_text()) for p in sorted((Path(output) / 'episodes').glob('*.json'))]


def export_results(output):
    output = Path(output)
    records = load_records(output)
    if records:
        temp = output / 'raw_results.csv.tmp'
        with temp.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(Cell.__dataclass_fields__))
            writer.writeheader()
            writer.writerows(r['cell'] for r in records)
        temp.replace(output / 'raw_results.csv')
    manifest = json.loads((output / 'manifest.json').read_text())
    cells = [r['cell'] for r in records]
    atomic_json(output / 'run_summary.json', {
        'planned_episodes': manifest['planned_episodes'], 'saved_episodes': len(cells),
        'successful_episodes': sum(c['status'] == 'ok' for c in cells),
        'error_episodes': sum(c['status'] == 'error' for c in cells),
        'attack_episodes': sum(c['category'] != 'clean' for c in cells),
        'clean_episodes': sum(c['category'] == 'clean' for c in cells),
        'model': manifest['config']['model'], 'judge_model': manifest['config']['judge_model'],
        'complete': len(cells) == manifest['planned_episodes'] and all(c['status'] == 'ok' for c in cells),
        'api_stats_this_process': llm.STATS.snapshot(),
    })
    return [Cell(**c) for c in cells]


def run_full(model=None, limit=None, use_judge=True, workers=1, *, output_dir=RESULTS_DIR,
             repeats=1, defense_names=None, max_runs=None, retry_errors=False,
             stop_after_errors=3):
    if workers != 1:
        raise ValueError('Use --workers 1 for reproducible rate-limited runs.')
    if repeats < 1 or (limit is not None and limit < 1) or (max_runs is not None and max_runs < 1):
        raise ValueError('Repeats, limit and max-runs must be positive.')
    if stop_after_errors < 1:
        raise ValueError('stop-after-errors must be positive.')
    names = defense_names or DEFENSE_ORDER
    if len(set(names)) != len(names) or any(n not in DEFENSE_ORDER for n in names):
        raise ValueError('Defense names must be unique and known.')
    model = model or llm.DEFAULT_MODEL
    attacks = [a for cat in CATEGORIES for a in [x for x in ATTACKS if x.category == cat][:limit]]
    config = {'model': model, 'judge_model': llm.DEFAULT_JUDGE_MODEL, 'repeats': repeats,
              'attacks': [a.id for a in attacks], 'defenses': names, 'use_judge': use_judge,
              'source_sha256': source_digest(), 'temperature': 0.0,
              'thinking_budget': llm.THINKING_BUDGET, 'rpm': llm.RPM, 'schema_version': 2}
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    # Protect the checkpoint directory against overlapping invocations.
    lock = output / '.run.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError(f'{lock} exists; stop the other runner before removing a stale lock.') from exc
    os.close(fd)
    try:
        manifest_path = output / 'manifest.json'
        if manifest_path.exists():
            if json.loads(manifest_path.read_text())['config'] != config:
                raise ValueError('Configuration or source changed; use a new output directory.')
        else:
            if list((output / 'episodes').glob('*.json')):
                raise ValueError('Episodes exist without a manifest; use a new output directory.')
            atomic_json(manifest_path, {'config': config,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'planned_episodes': repeats * len(names) * (len(attacks) + 1)})
        done = failures = 0
        # Clean controls first, then interleave defenses for each attack and trial.
        for trial in range(1, repeats + 1):
            for attack in [None, *attacks]:
                for name in names:
                    aid = attack.id if attack else '__clean__'
                    path = output / 'episodes' / f'{name}__{aid}__{trial:03d}.json'
                    if path.exists():
                        old = json.loads(path.read_text())
                        if not (retry_errors and old['cell']['status'] == 'error'):
                            continue
                        # Preserve failed attempts for audit before replacement.
                        archive = output / 'failed_attempts' / f'{path.stem}__{time.time_ns()}.json'
                        atomic_json(archive, old)
                    record = _run_one(attack, name, trial, model, use_judge)
                    atomic_json(path, record)
                    c = record['cell']
                    print(f"{c['run_id']}: {c['status']} attack={c['programmatic_success']} task={c['legitimate_success']} ({c['latency_s']}s)", flush=True)
                    failures = failures + 1 if c['status'] == 'error' else 0
                    done += 1
                    export_results(output)
                    if failures >= stop_after_errors or (max_runs is not None and done >= max_runs):
                        print('Paused; completed episodes are saved. Rerun the same command to resume.', flush=True)
                        return export_results(output)
        return export_results(output)
    finally:
        lock.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--model')
    ap.add_argument('--limit', type=int, help='Attacks per category')
    ap.add_argument('--repeats', type=int, default=1)
    ap.add_argument('--no-judge', action='store_true')
    ap.add_argument('--workers', type=int, default=1, choices=[1])
    ap.add_argument('--defenses', nargs='+', choices=DEFENSE_ORDER)
    ap.add_argument('--output-dir', type=Path, default=RESULTS_DIR)
    ap.add_argument('--max-runs', type=int)
    ap.add_argument('--retry-errors', action='store_true')
    ap.add_argument('--stop-after-errors', type=int, default=3)
    args = ap.parse_args()
    run_full(model=args.model, limit=args.limit, use_judge=not args.no_judge,
             workers=args.workers, output_dir=args.output_dir, repeats=args.repeats,
             defense_names=args.defenses, max_runs=args.max_runs, retry_errors=args.retry_errors,
             stop_after_errors=args.stop_after_errors)

if __name__ == '__main__':
    main()
