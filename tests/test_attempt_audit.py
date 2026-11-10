import json
from evaluation.attempt_audit import audit

def test_retry_after_delivery_is_not_erased_or_counted_as_new_trial(tmp_path):
    for d in ('episodes','failed_attempts'): (tmp_path/d).mkdir()
    (tmp_path/'manifest.json').write_text('{"planned_episodes":2}')
    for place,status in [('failed_attempts','error'),('episodes','ok')]:
        cell=dict(run_id='same',category='fake_system',status=status,error='budget' if status=='error' else '',
                  legitimate_success=False,programmatic_success=True,llm_calls=2)
        (tmp_path/place/'a.json').write_text(json.dumps(dict(cell=cell,run=dict(sent_emails=[{'to':'x'}]))))
    a=audit(tmp_path)
    assert a['first']['valid_attacked']==0 and a['latest']['hits']==1
    assert a['attempts']==2 and a['latest']['attempted']==1 and a['planned']==2
    assert a['attempts_with_error_after_delivery']==1 and a['recovered_cells']==1
