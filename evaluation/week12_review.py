"""Deterministic, category-balanced selection over three final-action trials.
Comparison is confined to the ungated final action. Human labels are never generated.
"""
import hashlib,json
from pathlib import Path
from benchmark.attacks import ATTACKS,CATEGORIES
from evaluation.validation import metrics

DIRS=['one_step','one_step_trial2','one_step_trial3']


def select(root):
    selected=[]
    for t,d in enumerate(DIRS):
        for cat in CATEGORIES:
            items=[a for a in ATTACKS if a.category==cat]
            # Three of six per category per trial. Rotate to cover all six.
            for i in range(3):
                a=items[(t*2+i)%len(items)]
                f=root/d/(a.id+'.json')
                if f.exists():
                    r=json.loads(f.read_text())
                    selected.append((f'{t+1}:{a.id}',f,r,a))
    return selected


def evaluate(root):
    entries=json.loads((root/'review_labels.json').read_text())
    if entries['review_type']!='AI-assisted, unblinded':raise ValueError('Missing AI provenance')
    records=select(root)
    by_id={r['id']:r for r in entries['annotations']}
    if len(entries['annotations'])!=len(by_id) or len(records)!=36 or set(by_id)!={rid for rid,*_ in records}:
        raise ValueError('Incomplete or duplicate review sample')
    pairs=[];differences=[]
    for rid,f,r,a in records:
        v=by_id[rid]
        if v['sha256']!=hashlib.sha256(f.read_bytes()).hexdigest():raise ValueError('Evidence changed')
        if not v['reason'] or v['label'] not in ('achieved','not achieved','ambiguous'):raise ValueError('Invalid annotation')
        if v['label']=='ambiguous' or r['decision']=='invalid':continue
        pred=r['arms']['none']['hit'];actual=v['label']=='achieved'
        pairs.append((pred,actual))
        if pred!=actual:differences.append(rid)
    return dict(selected=len(records),binary=len(pairs),comparison=metrics(pairs),disagreements=differences)
if __name__=='__main__':
    import sys
    print(json.dumps(evaluate(Path(sys.argv[1])),indent=2))
