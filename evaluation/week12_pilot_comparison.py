"""Cross-pilot descriptive table, keeping providers and valid denominators distinct."""
import json,statistics
from pathlib import Path
from evaluation.harness import load_records

def compare(sources):
    rows=[]
    for source in sources:
        groups={}
        for r in load_records(Path(source)):
            c=r['cell']
            groups.setdefault(c['defense'],[]).append(c)
        for defense,cells in sorted(groups.items()):
            attacked=[c for c in cells if c['category']!='clean' and c['status']=='ok']
            rows.append(dict(source=source,defense=defense,valid_attacked=len(attacked),
                hits=sum(c['programmatic_success'] is True for c in attacked),
                task_completed=sum(c['legitimate_success'] for c in attacked),
                guarded_calls=sum(c['guard_calls'] for c in attacked),
                median_elapsed_seconds=statistics.median(c['latency_s'] for c in attacked) if attacked else None,
                errors=sum(c['status']!='ok' for c in cells),
                judge_available=sum(type(c['judge_success']) is bool for c in attacked)))
    return rows
if __name__=='__main__':
    import sys
    print(json.dumps(compare(sys.argv[1:]),indent=2))
