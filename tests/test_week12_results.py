import json
import pytest
from evaluation.week12_results import summarize
from evaluation.week12_review import DIRS
from benchmark.attacks import ATTACKS

def test_repeats_are_separate_and_matching_is_enforced(tmp_path):
    for d in [*DIRS,'isolated']:
        (tmp_path/d).mkdir()
        for a in [None,*ATTACKS]:
            if d=='isolated' and a and a.target_action!='exfiltrate_secret':continue
            k=a.id if a else 'clean'
            r=dict(attack_id=k,decision='refuse',reply='{"action":"refuse"}',fingerprint=k,
                   arms={x:dict(deliveries=0,task=False,hit=False) for x in ('none','existing','candidate')})
            (tmp_path/d/(k+'.json')).write_text(json.dumps(r))
    s=summarize(tmp_path)
    assert s['all_attacked']['valid']==72 and s['controls']['valid']==3
    assert len(s['by_design'])==24 and s['designs_ever_hit']==0
    f=tmp_path/DIRS[1]/'do_01.json'
    r=json.loads(f.read_text());r['fingerprint']='other';f.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='Mismatch'):summarize(tmp_path)
