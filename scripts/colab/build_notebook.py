"""Build a notebook containing only a small allowlist of benchmark sources, no .env or results."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
FILES=sorted((ROOT/"defenses").glob("*.py")) + [ROOT/p for p in [
    "agent/__init__.py","agent/agent.py","agent/tools.py","benchmark/__init__.py","benchmark/attacks.py",
    "evaluation/__init__.py","evaluation/harness.py","evaluation/scorer.py",
    "evaluation/repeated_analysis.py","evaluation/attempt_audit.py","evaluation/ai_review.py"]]
sources={str(p.relative_to(ROOT)):p.read_text() for p in FILES}
sources["agent/llm.py"]=(HERE/"ollama_transport.py").read_text()
sources["evaluation/local_grid.py"]=(HERE/"run_grid.py").read_text()
cells=[]
def add(s,code=True):
    d=dict(cell_type="code" if code else "markdown",metadata={},source=s.strip().splitlines(True))
    if code:d.update(outputs=[],execution_count=None)
    cells.append(d)
add("""# Prompt injection: 450 multi-step episodes on a free GPU
Use a **free GPU runtime** (Runtime → Change runtime type). No API key. The full design is 24 attack designs and one clean control × six defenses × three trials. The actor, guard and judge all use a locally hosted GPT-OSS 20B. Model weights, serving software and decoding can differ from Groq; analyze this as its own study. All tools, pages and email deliveries are synthetic.

Run the setup and two preflight episodes before the main grid. A GPU is not guaranteed. Setup downloads the model and runtime. Stored progress resumes only if the model digest and code still match. The default output directory is ephemeral: use the optional Drive checkpoint before starting or download results before ending the session.""",False)
add("""import os, sys, shutil, subprocess, time, json
from pathlib import Path
import requests
if not shutil.which("nvidia-smi"):
    raise RuntimeError("No NVIDIA GPU. Select a free GPU before running setup.")
gpu=subprocess.check_output(["nvidia-smi","--query-gpu=name,memory.free","--format=csv,noheader,nounits"],text=True)
print("GPU and available MiB:",gpu.strip())
if int(gpu.splitlines()[0].rsplit(",",1)[1]) < 14500:
    raise RuntimeError("Too little free GPU memory for this configuration; no paid fallback.")
work=Path("/content/prompt_injection_gpu")
work.mkdir(exist_ok=True)
os.chdir(work)
server_env={**os.environ,"OLLAMA_HOST":"127.0.0.1:11434","OLLAMA_NO_CLOUD":"1","OLLAMA_NUM_PARALLEL":"1"}
if not shutil.which("ollama"):
    import zstandard
    archive="/content/ollama-package.tar.zst"
    print("Downloading Ollama", flush=True)
    subprocess.run(["curl","-fLsS","--retry","3","--max-time","300","-o",archive,"https://ollama.com/download/ollama-linux-amd64.tar.zst"],check=True)
    print("Extracting Ollama",flush=True)
    with open(archive,"rb") as compressed, zstandard.ZstdDecompressor().stream_reader(compressed) as expanded:
        with subprocess.Popen(["tar","-x","-C","/usr"],stdin=subprocess.PIPE) as tar:
            shutil.copyfileobj(expanded,tar.stdin,1024*1024)
            tar.stdin.close()
            if tar.wait()!=0: raise RuntimeError("Ollama extraction failed")
    Path(archive).unlink()
def serving():
    try: return requests.get("http://127.0.0.1:11434/api/version",timeout=2).ok
    except requests.RequestException: return False
if not serving():
    server_log=open("/content/ollama-grid.log","a")
    server=subprocess.Popen(["ollama","serve"],env=server_env,stdout=server_log,stderr=subprocess.STDOUT)
    for i in range(30):
        if serving(): break
        time.sleep(1)
    if not serving(): raise RuntimeError("Ollama did not start: inspect /content/ollama-grid.log")
print("Downloading GPT-OSS 20B weights",flush=True)
pull=requests.post("http://127.0.0.1:11434/api/pull",json={"model":"gpt-oss:20b","stream":True},stream=True,timeout=(5,300))
pull.raise_for_status()
last=None
for line in pull.iter_lines():
    msg=json.loads(line)
    if "error" in msg: raise RuntimeError(msg["error"])
    frac=msg.get("completed",0)*10//max(1,msg.get("total",1))
    bucket=(msg.get("status"),frac)
    if bucket!=last: print(bucket[0],frac*10,"%",flush=True)
    last=bucket
if last is None or last[0]!="success": raise RuntimeError("Model pull incomplete")""")
add("# Frozen benchmark code. Only agent/llm.py uses the independent local adapter.\nsources = "+repr(sources)+"""
for rel,s in sources.items():
    f=work/rel
    f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(s)
# The primary source supports two hosted providers; reflect the local study's explicit reasoning level.
h=work/"evaluation/harness.py"
h.write_text(h.read_text().replace("llm.PROVIDER == 'groq' else None","llm.PROVIDER in ('groq', 'ollama-local') else None"))
""")
add("""# Optional: set True BEFORE the first grid run for durable per-episode checkpoints.
USE_GOOGLE_DRIVE = False
if USE_GOOGLE_DRIVE:
    from google.colab import drive
    drive.mount("/content/drive")
base=Path("/content/drive/MyDrive" if USE_GOOGLE_DRIVE else "/content")/"prompt_injection_results_ollama"
base.mkdir(exist_ok=True)
def grid(*args):
    subprocess.run([sys.executable,"-u","-m","evaluation.local_grid",*map(str,args)],cwd=work,check=True)
grid(base/"preflight","--smoke")
proc=requests.get("http://127.0.0.1:11434/api/ps",timeout=10).json()["models"]
if not any(m["name"]=="gpt-oss:20b" and m.get("size_vram",0)>0 for m in proc):
    raise RuntimeError("Preflight did not verify GPU offload. Check runtime before starting.")""")
add("""grid(base/"primary_450")
# Export comparisons and a verdict-blinded sample only after collection finishes.
sys.path.insert(0,str(work))
from evaluation import repeated_analysis, attempt_audit, ai_review, harness
out=base/"primary_450"
comparison=repeated_analysis.analyze(out)
harness.atomic_json(out/"matched_results.json",comparison)
harness.atomic_json(out/"attempt_audit.json",attempt_audit.audit(out))
if comparison["saved"]==450 and not (out/"ai_review_packets").exists():
    ai_review.export_sample(out,size=40)
print("Matched counts and first-attempt audit saved. The review packet still needs actual AI assessment.")""")
add("""# Can also run separately after interrupting the grid, to save partial results.
from google.colab import files
archive=shutil.make_archive("/content/prompt_injection_gpu_results","zip",base)
files.download(archive)""")
add((HERE/"finish_review.py").read_text()+"\nfinish_review(base)\n")
doc=dict(nbformat=4,nbformat_minor=4,metadata=dict(accelerator="GPU",kernelspec=dict(name="python3",display_name="Python 3"),colab=dict(name="Prompt_Injection_450.ipynb")),cells=cells)
target=ROOT/"output/weeks10_12/Prompt_Injection_450.ipynb"
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(doc,indent=1)+"\n")
