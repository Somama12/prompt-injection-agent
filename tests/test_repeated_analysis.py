import pytest
from evaluation.harness import atomic_json
from evaluation.repeated_analysis import analyze


def test_pairs_require_matched_valid_trials(tmp_path):
    atomic_json(tmp_path/'manifest.json', {'config': {'defenses':['none','allowlist'], 'attacks':['a'], 'repeats':2}})
    def save(d,t,status,success):
        atomic_json(tmp_path/'episodes'/f'{d}-{t}.json', {'cell':dict(defense=d,attack_id='a',trial=t,status=status,
            programmatic_success=success,judge_success=None,legitimate_success=False)})
    save('none',1,'ok',True)
    save('allowlist',1,'ok',False)
    save('none',2,'error',True)
    save('allowlist',2,'ok',False)
    r=analyze(tmp_path)
    assert (r['planned'],r['saved'],r['valid']) == (8,4,3)
    assert len(r['missing_cells']) == 4
    assert r['paired_comparisons'][0]['matched_pairs'] == 1
    assert r['paired_comparisons'][0]['baseline_only_succeeded'] == 1
    assert r['by_trial'][0]['clean_success'] is None
    assert r['by_trial'][2]['errors'] == 1
    atomic_json(tmp_path/'episodes'/'duplicate.json', {'cell':dict(defense='none',attack_id='a',trial=1)})
    with pytest.raises(ValueError,match='Duplicate'): analyze(tmp_path)
