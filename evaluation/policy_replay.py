"""Replay saved proposals through two deterministic policies, without model or tool execution."""
import json
from pathlib import Path
from evaluation.credential_probe import Candidate
from defenses.allowlist import AllowlistDefense
from defenses.base import ActionContext


def replay(directory):
    rows=[]
    for file in sorted((Path(directory)/'episodes').glob('*.json')):
        r=json.loads(file.read_text())
        for i,call in enumerate(r['run'].get('tool_calls',[])):
            ctx=ActionContext(i,call['name'],call['args'],'','')
            rows.append(dict(run_id=r['cell']['run_id'],position=i,tool=call['name'],
                existing=AllowlistDefense().check_action(ctx).allowed,
                candidate=Candidate().check_action(ctx).allowed))
    return dict(source=str(directory),episodes=len(list((Path(directory)/'episodes').glob('*.json'))),
                proposals=len(rows),existing_veto=sum(not r['existing'] for r in rows),
                changed=sum(r['existing']!=r['candidate'] for r in rows), rows=rows)

if __name__=='__main__':
    import sys
    print(json.dumps([replay(d) for d in sys.argv[1:]],indent=2))
