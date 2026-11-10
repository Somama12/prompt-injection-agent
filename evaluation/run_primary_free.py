"""Resume the frozen Groq multi-step grid. Each cell receives one primary attempt.
Model step limits are recorded and the next cell runs. Stop on provider/judge errors.
Restart later with the same directory and source to retain a first-attempt audit trail.
"""
from pathlib import Path
from evaluation import harness
from agent import llm
import json
import os
import sys


def main():
    if llm.PROVIDER!='groq' or os.getenv('GROQ_FREE_PLAN_CONFIRMED')!='1':
        raise ValueError('Requires the confirmed free Groq configuration.')
    out=Path('results/groq_full_three_trials')
    out.mkdir(exist_ok=True,parents=True)
    if '--retry-first-operational' in sys.argv:
        errors=[json.loads(f.read_text())['cell'] for f in sorted((out/'episodes').glob('*.json'))]
        errors=[c for c in errors if c['status']!='ok']
        if len(errors)!=1 or errors[0]['error'].startswith('hit max_steps='):
            raise ValueError('Only use this option for a single saved operational error.')
        harness.run_full(output_dir=out,repeats=3,max_runs=1,retry_errors=True,stop_after_errors=1)
        c=json.loads((out/'episodes'/(errors[0]['run_id']+'.json')).read_text())['cell']
        if c['status']!='ok' and not c['error'].startswith('hit max_steps='):return
    while True:
        before=set((out/'episodes').glob('*.json'))
        harness.run_full(output_dir=out,repeats=3,max_runs=1,stop_after_errors=1)
        new=set((out/'episodes').glob('*.json'))-before
        if not new:break
        c=json.loads(next(iter(new)).read_text())['cell']
        if c['status']!='ok' and not c['error'].startswith('hit max_steps='):
            print('Stopped on operational error; retained record. Inspect before resuming.',flush=True)
            break
        if c['category']!='clean' and c['status']=='ok' and c['judge_success'] is None:
            print('Stopped on unavailable judge verdict; inspect quota or provider.',flush=True)
            break
if __name__=='__main__':main()
