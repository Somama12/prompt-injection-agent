"""Trial-level coverage and matched comparisons; repeats are not new attacks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from evaluation.harness import load_records, atomic_json


def analyze(output):
    output = Path(output)
    manifest = json.loads((output / 'manifest.json').read_text())
    config = manifest['config']
    records = load_records(output)
    cells = {}
    expected = {(d, a, t) for d in config['defenses']
                for a in ['__clean__', *config['attacks']]
                for t in range(1, config['repeats'] + 1)}
    for record in records:
        c = record['cell']
        key = c['defense'], c['attack_id'], c['trial']
        if key not in expected or key in cells:
            raise ValueError('Duplicate or unexpected episode cell')
        cells[key] = c
    rows = []
    for trial in range(1, config['repeats'] + 1):
        for defense in config['defenses']:
            observed = [c for (d, a, t), c in cells.items() if d == defense and t == trial]
            valid = [c for c in observed if c['status'] == 'ok' and c['attack_id'] != '__clean__']
            clean = cells.get((defense, '__clean__', trial))
            rows.append(dict(trial=trial, defense=defense, planned_attacks=len(config['attacks']),
                valid_attacks=len(valid), attack_successes=sum(c['programmatic_success'] is True for c in valid),
                missing=len(config['attacks']) + 1 - len(observed),
                errors=sum(c['status'] != 'ok' for c in observed),
                judge_missing=sum(type(c['judge_success']) is not bool for c in valid),
                clean_success=clean['legitimate_success'] if clean and clean['status'] == 'ok' else None))
    comparisons = []
    if 'none' in config['defenses']:
        for defense in config['defenses']:
            if defense == 'none': continue
            pairs = []
            for attack in config['attacks']:
                for trial in range(1, config['repeats'] + 1):
                    baseline = cells.get(('none', attack, trial))
                    treated = cells.get((defense, attack, trial))
                    if all(c and c['status'] == 'ok' and type(c['programmatic_success']) is bool for c in (baseline, treated)):
                        pairs.append((baseline['programmatic_success'], treated['programmatic_success']))
            comparisons.append(dict(defense=defense, matched_pairs=len(pairs),
                both_succeeded=sum(b and d for b, d in pairs),
                baseline_only_succeeded=sum(b and not d for b, d in pairs),
                defense_only_succeeded=sum(d and not b for b, d in pairs),
                neither_succeeded=sum(not b and not d for b, d in pairs)))
    result = dict(planned=len(expected), saved=len(cells), valid=sum(c['status'] == 'ok' for c in cells.values()),
                  missing_cells=[dict(defense=d, attack_id=a, trial=t) for d, a, t in sorted(expected - cells.keys())],
                  by_trial=rows, paired_comparisons=comparisons,
                  interpretation='Descriptive matched outcomes only. Trials of the same attack are dependent; no independent-sample significance claim.')
    atomic_json(output / 'repeated_analysis.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    result = analyze(args.output_dir)
    print(f"Saved {result['saved']}/{result['planned']}; valid {result['valid']}")
