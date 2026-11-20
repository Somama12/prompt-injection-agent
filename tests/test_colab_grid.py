"""Exercise the notebook's embedded benchmark in isolation without a GPU or any model calls."""
import json
import os
from pathlib import Path
import subprocess
import sys

def test_colab_embedded_grid(tmp_path):
    root=Path(__file__).resolve().parents[1]
    nb=json.loads((root/"output/weeks10_12/Prompt_Injection_450.ipynb").read_text())
    code=["".join(c["source"]) for c in nb["cells"] if c["cell_type"]=="code"]
    for cell in code: compile(cell,"colab","exec")
    exec(code[1],{"work":tmp_path})
    for name in ("agent/agent.py","benchmark/attacks.py","evaluation/scorer.py"):
        assert (tmp_path/name).read_bytes()==(root/name).read_bytes()
    subprocess.run([sys.executable,"-c", """
import sys,json
from unittest.mock import Mock
from pathlib import Path
from agent import llm
from agent.tools import AUTHORIZED_RECIPIENT,ARTICLE_URL
from evaluation import local_grid,harness
from benchmark.attacks import ATTACKS
from defenses.registry import DEFENSE_ORDER
assert (1+len(ATTACKS))*len(DEFENSE_ORDER)*3 == 450
def reply(x): return Mock(json=lambda:x)
llm.SESSION.get=lambda url,**kw: reply({"models":[{"name":llm.DEFAULT_MODEL,"digest":"test","details":{}}]} if url.endswith("tags") else {"version":"test"})
def post(url,json,**kwargs):
    p=json
    assert url.startswith("http://127.0.0.1:") and p["think"]=="low"
    system,prompt=[m["content"] for m in p["messages"]]
    def action(n,a): return {"tool_calls":[{"function":{"name":n,"arguments":a}}]}
    if "tools" in p:
        if "TOOL_RESULT (read_webpage)" not in prompt: msg=action("read_webpage",{"url":ARTICLE_URL})
        elif "TOOL_RESULT (send_email)" not in prompt: msg=action("send_email",{"to":AUTHORIZED_RECIPIENT,"subject":"Campus","body":"The campus solar array is intended to generate renewable energy for university buildings."})
        else: msg={"content":"FINAL: Delivered."}
    elif "security monitor" in system: msg={"content":"ALLOW"}
    else: msg={"content":'{"attack_succeeded":false,"reason":"No attacker delivery"}'}
    return reply(dict(done=True,done_reason="stop",model=llm.DEFAULT_MODEL,message=msg))
llm.SESSION.post=post
sys.argv=["local_grid","smoke","--smoke"]
local_grid.main()
assert not Path("smoke/episodes").exists()
harness.run_full(repeats=3,max_runs=1,output_dir=Path("primary"))
m=json.loads(Path("primary/manifest.json").read_text())
assert m["planned_episodes"]==450 and m["config"]["provider"]=="ollama-local" and m["config"]["reasoning_effort"]=="low"
assert json.loads(Path("primary/run_summary.json").read_text())["saved_episodes"]==1
"""],cwd=tmp_path,env={**os.environ,"PYTHONPATH":str(tmp_path)},check=True)
