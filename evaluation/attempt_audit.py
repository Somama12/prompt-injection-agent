"""Compare first and latest attempts for each planned cell without rerunning a model."""
import argparse
from collections import defaultdict
import json
from pathlib import Path


def audit(output):
    p = Path(output)
    manifest = json.loads((p/'manifest.json').read_text())
    groups = defaultdict(list)
    for file in sorted((p/'failed_attempts').glob('*.json')):
        r = json.loads(file.read_text())
        groups[r['cell']['run_id']].append(r)
    current = {}
    for file in sorted((p/'episodes').glob('*.json')):
        r = json.loads(file.read_text())
        rid = r['cell']['run_id']
        if rid in current:
            raise ValueError('duplicate current record')
        current[rid] = r
    if set(groups) - set(current):
        raise ValueError('archived attempt without current record')
    rows = []
    for rid,r in current.items():
        history = groups[rid] + [r]
        for i,rec in enumerate(history):
            c = rec['cell']
            rows.append(dict(run_id=rid, attempt=i+1, first=i==0, latest=i==len(history)-1,
                             attacked=c['category']!='clean', status=c['status'], error=c['error'],
                             task=c['legitimate_success'], attack=c['programmatic_success'],
                             delivered=len(rec['run'].get('sent_emails',[])), calls=c['llm_calls']))
    def measure(name):
        subset=[r for r in rows if r[name]]
        val=[r for r in subset if r['attacked'] and r['status']=='ok']
        return dict(attempted=len(subset),valid=sum(r['status']=='ok' for r in subset),
                    valid_attacked=len(val), hits=sum(r['attack'] is True for r in val),
                    task_done=sum(r['task'] for r in val), errors=sum(r['status']!='ok' for r in subset))
    return dict(planned=manifest['planned_episodes'],first=measure('first'),latest=measure('latest'),
                attempts=len(rows), attempts_with_error_after_delivery=sum(r['status']!='ok' and r['delivered']>0 for r in rows),
                recovered_cells=sum(bool(groups[k]) and r['cell']['status']=='ok' for k,r in current.items()),rows=rows)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output',type=Path)
    print(json.dumps(audit(ap.parse_args().output),indent=2))
