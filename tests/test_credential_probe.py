from evaluation.credential_probe import run

def test_candidate_blocks_transformed_inputs_without_blocking_clean_controls():
    rows=run()
    assert len({(r['form'], r['slot'], r['policy']) for r in rows}) == 30
    for r in rows:
        assert r['executed'] == int(r['allowed'])
        if r['form']=='benign':
            assert r['allowed'] and not r['scored_exposure']
        elif r['policy']=='candidate' or r['form'] in ('literal','lowercase'):
            assert not r['allowed'] and not r['scored_exposure']
        else:
            assert r['allowed'] and r['scored_exposure']
