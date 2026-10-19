"""Check AI-authored annotations against saved evidence, separately from human labels."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path
from evaluation.harness import load_records, atomic_json


def digest(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


def export_sample(output, size=40, seed=42):
    """Freeze a stratified AI-review packet without automated verdicts."""
    from benchmark.attacks import ATTACKS
    output = Path(output)
    dest = output / 'ai_review_packets'
    if size < 1:
        raise ValueError('Sample size must be positive')
    if dest.exists():
        raise ValueError('AI review packets already exist; preserve the frozen sample')
    groups = {}
    for r in load_records(output):
        c = r['cell']
        if c['status'] == 'ok' and c['category'] != 'clean':
            groups.setdefault((c['category'], c['defense']), []).append(r)
    if not groups:
        raise ValueError('No valid attack episodes available')
    rng = random.Random(seed)
    for group in groups.values(): rng.shuffle(group)
    selected = []
    while groups and len(selected) < size:
        keys = list(groups)
        rng.shuffle(keys)
        for key in keys:
            selected.append(groups[key].pop())
            if not groups[key]: del groups[key]
            if len(selected) == size: break
    attacks = {a.id: a for a in ATTACKS}
    rows = []
    dest.mkdir()
    for i, record in enumerate(selected, 1):
        c, run = record['cell'], record['run']
        attack = attacks[c['attack_id']]
        packet_id = f'ai_{i:03d}'
        atomic_json(dest / f'{packet_id}.json', dict(packet_id=packet_id,
            attack_goal=attack.target_action, payload=attack.payload, marker=attack.marker,
            transcript=run['transcript'], tool_calls=run['tool_calls'], sent_emails=run['sent_emails']))
        rows.append(dict(packet_id=packet_id, run_id=c['run_id'], episode_sha256=digest(record),
                         ai_label='', rationale='', evidence_paths=[]))
    atomic_json(dest / 'annotations.json', dict(review_type='AI-assisted review', reviewer='',
        seed=seed, requested=size, selected=len(rows),
        blinding='Packets omit automated verdicts. The mapping reveals conditions; document actual reviewer exposure.',
        annotations=rows))
    return len(rows)


def evaluate(output, annotations):
    output = Path(output)
    review = json.loads(Path(annotations).read_text())
    if review.get('review_type') != 'AI-assisted review' or not review.get('reviewer'):
        raise ValueError('Explicit AI reviewer provenance is required')
    records = {r['cell']['run_id']: r for r in load_records(output)}
    seen = set()
    comparable = agreements = 0
    counts = dict(succeeded=0, blocked=0, ambiguous=0)
    disagreements = []
    for row in review['annotations']:
        rid = row['run_id']
        if rid in seen or rid not in records:
            raise ValueError('Unknown or duplicate run_id')
        seen.add(rid)
        record = records[rid]
        if digest(record) != row['episode_sha256']:
            raise ValueError('Episode changed since AI review')
        if record['cell']['status'] != 'ok' or record['cell']['category'] == 'clean':
            raise ValueError('Review requires a valid attacked episode')
        label = row['ai_label']
        if label not in counts or not row.get('rationale') or not row.get('evidence_paths'):
            raise ValueError('Each annotation needs a valid label, rationale and evidence paths')
        # Evidence paths are slash-separated JSON keys/array indexes rooted at the episode.
        for path in row['evidence_paths']:
            value = record
            try:
                for part in path.split('/'):
                    value = value[int(part)] if isinstance(value, list) else value[part]
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                raise ValueError('Evidence path does not resolve') from exc
        counts[label] += 1
        predicted = record['cell']['programmatic_success']
        if label != 'ambiguous' and type(predicted) is bool:
            comparable += 1
            agrees = predicted == (label == 'succeeded')
            agreements += agrees
            if not agrees: disagreements.append(rid)
    result = dict(review_type='AI-assisted review', reviewer=review['reviewer'],
                  reviewed=len(seen), labels=counts, comparable=comparable,
                  programmatic_agreement=agreements/comparable if comparable else None,
                  disagreements=disagreements,
                  limitation='AI agreement is not human validation or independent ground truth. Review may be unblinded; consult annotation provenance.')
    atomic_json(output / 'ai_review_metrics.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--annotations', type=Path)
    p.add_argument('--export', action='store_true')
    p.add_argument('--size', type=int, default=40)
    args = p.parse_args()
    if args.export:
        print(f'Exported {export_sample(args.output_dir,args.size)} AI review packets')
    elif args.annotations:
        print(json.dumps(evaluate(args.output_dir,args.annotations),indent=2))
    else:
        p.error('Supply --export or --annotations')
