"""Summarize checkpoints without counting infrastructure errors as safe attacks."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from benchmark.attacks import CATEGORIES
from evaluation.harness import RESULTS_DIR, load_records, atomic_json


def summarize(output):
    output = Path(output)
    manifest = json.loads((output / 'manifest.json').read_text())
    cells = [r['cell'] for r in load_records(output)]
    config = manifest['config']
    table = []
    for defense in config['defenses']:
        attacked = [c for c in cells if c['defense'] == defense and c['category'] != 'clean']
        valid = [c for c in attacked if c['status'] == 'ok']
        clean = [c for c in cells if c['defense'] == defense and c['category'] == 'clean' and c['status'] == 'ok']
        table.append({'defense': defense, 'valid_attacks': len(valid),
                      'attack_errors': len(attacked) - len(valid),
                      'attack_successes': sum(c['programmatic_success'] is True for c in valid),
                      'attack_success_rate': sum(c['programmatic_success'] is True for c in valid) / len(valid) if valid else None,
                      'task_success_under_attack': sum(c['legitimate_success'] for c in valid) / len(valid) if valid else None,
                      'clean_valid': len(clean), 'clean_successes': sum(c['legitimate_success'] for c in clean),
                      'mean_latency_s': statistics.mean(c['latency_s'] for c in valid) if valid else None,
                      'mean_guard_calls': statistics.mean(c['guard_calls'] for c in valid) if valid else None})
    atomic_json(output / 'analysis.json', table)
    lines = ['# Benchmark results', '', f"Model: {config['model']}; repeats: {config['repeats']}; saved episodes: {len(cells)}/{manifest['planned_episodes']}.",
             '', 'Errors are excluded from attack-success denominators and reported separately. Missing results are not zero success. Single-trial results are preliminary; repeated episodes are not independent attack designs.', '',
             '| Defense | Valid attacks | Errors | Attack success | Task success under attack | Clean success | Mean latency | Guard calls |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    def pct(value): return 'N/A' if value is None else f'{value:.1%}'
    def number(value): return 'N/A' if value is None else f'{value:.2f}'
    for row in table:
        lines.append(f"| {row['defense']} | {row['valid_attacks']} | {row['attack_errors']} | {pct(row['attack_success_rate'])} | {pct(row['task_success_under_attack'])} | {row['clean_successes']}/{row['clean_valid']} | {number(row['mean_latency_s'])} s | {number(row['mean_guard_calls'])} |")
    judged = [c for c in cells if c['status'] == 'ok' and type(c['judge_success']) is bool]
    lines += ['', f"Judge verdicts available: {len(judged)}. Agreement with the deterministic scorer: " + (pct(sum(c['judge_success'] == c['programmatic_success'] for c in judged) / len(judged)) if judged else 'N/A') + '.',
              'Agreement between automated scorers is not human validation. See evaluation.validation for blinded review.', '',
              'Latency includes rate-limit waits and provider retries in the agent/guard loop, but excludes the later judge call. Guard calls are a cost proxy, not a dollar-cost measurement.',
              'Task success uses a keyword/length heuristic and needs manual validation. Credential exposure means a secret in an executed tool argument in this mock environment; it does not establish real-world network exfiltration.']
    (output / 'summary.md').write_text('\n'.join(lines) + '\n')
    matrix = np.full((len(CATEGORIES), len(config['defenses'])), np.nan)
    counts = {}
    for i, category in enumerate(CATEGORIES):
        for j, defense in enumerate(config['defenses']):
            subset = [c for c in cells if c['status'] == 'ok' and c['category'] == category and c['defense'] == defense]
            counts[i,j] = len(subset)
            if subset: matrix[i,j] = sum(c['programmatic_success'] is True for c in subset) / len(subset) * 100
    fig, ax = plt.subplots(figsize=(12, 5.8))
    cmap = plt.get_cmap('YlOrRd').with_extremes(bad='#eeeeee')
    im = ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=0, vmax=100, aspect='auto')
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i,j]
            text = 'No valid runs' if np.isnan(val) else f'{val:.0f}%\nn={counts[i,j]}'
            ax.text(j, i, text, ha='center', va='center', color='white' if val > 60 else 'black', fontsize=9)
    ax.set_xticks(range(len(config['defenses'])), [d.replace('_', ' ') for d in config['defenses']], rotation=25, ha='right')
    ax.set_yticks(range(len(CATEGORIES)), list(CATEGORIES.values()))
    ax.set_title('Observed attack success by category and defense\nErrors excluded; gray cells have no valid observations')
    fig.colorbar(im, ax=ax, label='Attack success (%)')
    fig.tight_layout()
    fig.savefig(output / 'heatmap.png', dpi=180)
    plt.close(fig)
    return table


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-dir', type=Path, default=RESULTS_DIR)
    args = ap.parse_args()
    summarize(args.output_dir)
    print(f'Wrote summary.md, analysis.json and heatmap.png in {args.output_dir}')

if __name__ == '__main__': main()
