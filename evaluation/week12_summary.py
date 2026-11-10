"""Build tables for the November 9 evidence cutoff from saved records."""
import argparse,json
from pathlib import Path
from evaluation.attempt_audit import audit
from evaluation.policy_replay import replay


def summarize(root):
    get=lambda name:json.loads((root/name).read_text())
    single=[json.loads(p.read_text()) for p in sorted((root/'one_step').glob('*.json'))]
    cats={}
    for r in single:
        g=cats.setdefault(r['category'],dict(attempted=0,valid=0,refuse=0,none_hits=0,existing_hits=0,candidate_hits=0,none_tasks=0,existing_tasks=0,candidate_tasks=0))
        g['attempted']+=1
        if r['decision']=='invalid':continue
        g['valid']+=1;g['refuse']+=r['decision']=='refuse'
        for k,arm in r['arms'].items():
            g[k+'_hits']+=arm['hit'] is True;g[k+'_tasks']+=arm['task']
    ga=audit(Path('results/groq_pilot_v3'))
    (root/'groq_audit.json').write_text(json.dumps(ga,indent=2))
    new=[r for r in single if r['decision']!='invalid' and r['attack_id']!='clean']
    return dict(one_step=cats,total=len(single), attacks_valid=len(new),
                no_gate_hits=sum(r['arms']['none']['hit'] for r in new),
                existing_hits=sum(r['arms']['existing']['hit'] for r in new),
                candidate_hits=sum(r['arms']['candidate']['hit'] for r in new),
                no_gate_tasks=sum(r['arms']['none']['task'] for r in new),
                existing_tasks=sum(r['arms']['existing']['task'] for r in new),
                groq={k:v for k,v in ga.items() if k!='rows'},gemini={k:v for k,v in get('gemini_audit.json').items() if k!='rows'},
                replay=[{k:v for k,v in r.items() if k!='rows'} for r in get('replay.json')])

if __name__=='__main__':
    import sys
    print(json.dumps(summarize(Path(sys.argv[1])),indent=2))
