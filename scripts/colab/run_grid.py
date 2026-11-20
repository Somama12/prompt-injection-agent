"""Run only inside the notebook's isolated copy with its local model adapter."""
import argparse
import json
from pathlib import Path
import statistics
import time
from agent import llm
from evaluation import harness

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    out=args.out
    if llm.PROVIDER != "ollama-local":
        raise RuntimeError("Only use the isolated loopback transport")
    out.mkdir(parents=True, exist_ok=True)
    def get(path):
        r=llm.SESSION.get(llm.BASE+path, timeout=10)
        r.raise_for_status()
        return r.json()
    tag=next(m for m in get("/api/tags")["models"] if m["name"]==llm.DEFAULT_MODEL)
    identity=dict(provider=llm.PROVIDER, model=tag["name"], digest=tag["digest"],
                  runtime=get("/api/version")["version"], model_details=tag["details"],
                  context=8192, reasoning="low", temperature=0, source=harness.source_digest())
    meta=out/"local_runtime.json"
    if meta.exists() and json.loads(meta.read_text()) != identity:
        raise RuntimeError("Model, runtime, or source changed: start a new directory.")
    harness.atomic_json(meta,identity)
    if args.smoke:
        # Two preflight episodes outside the 450: clean task, then an attacked guard+judge path.
        from benchmark.attacks import ATTACKS
        for a,d in [(None,"none"),(ATTACKS[0],"guard_llm")]:
            r=harness._run_one(a,d,1,llm.DEFAULT_MODEL,True)
            c=r["cell"]
            harness.atomic_json(out/(c["run_id"]+".json"),r)
            read_page=any(t["name"]=="read_webpage" and not t["blocked_by"] and not t["result"].startswith("ERROR:") for t in r["run"].get("tool_calls",[]))
            if c["status"]!="ok" or not read_page or (a is None and not c["legitimate_success"]) or (a and (c["guard_calls"]<1 or type(c["judge_success"])!=bool)):
                raise RuntimeError("GPU preflight failed: "+c["run_id"]+" "+c["error"])
        print("Preflight passed; two smoke episodes excluded from research totals.")
        return
    # Retain step-limit outcomes, stop immediately for infrastructure/judge errors.
    duration=[]
    while True:
        before={p.stem for p in (out/"episodes").glob("*.json")}
        if len(before)==450: break
        start=time.monotonic()
        harness.run_full(repeats=3, output_dir=out, max_runs=1)
        new={p.stem for p in (out/"episodes").glob("*.json")}-before
        if len(new)!=1: raise RuntimeError("Expected one new checkpoint")
        cell=json.loads((out/"episodes"/(new.pop()+".json")).read_text())["cell"]
        if ((cell["status"]!="ok" and not cell["error"].startswith("hit max_steps=")) or
            (cell["status"]=="ok" and cell["category"]!="clean" and cell["judge_success"] is None)):
            raise RuntimeError("Stopped; inspect saved infrastructure/judge error "+cell["run_id"])
        duration.append(time.monotonic()-start)
        n=len(before)+1
        print(f"{n}/450 attempted. Rough remaining time at this session's mean: "
              f"{(450-n)*statistics.mean(duration)/3600:.2f} h",flush=True)
    print((out/"run_summary.json").read_text())

if __name__=="__main__":
    main()
