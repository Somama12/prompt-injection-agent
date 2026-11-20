"""Compare five benign renderings of the same article across six defense settings."""
import fcntl
import html
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from getpass import getpass
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import requests

from agent import llm
from agent.agent import run_agent
from benchmark.attacks import clean_page
from defenses.registry import DEFENSE_ORDER, build_defenses
from evaluation.harness import atomic_json, source_digest
from evaluation.kimi_clean_controls import MODEL, usage
from evaluation.scorer import legitimate_task_success

OUT = Path("results/kimi_format_study")
WORKERS = 8


def pages():
    original = clean_page().strip()
    title, *body = [" ".join(p.split()) for p in original.split("\n\n") if p.strip()]
    return {
        "original": original,
        "continuous": " ".join([title, *body]),
        "bullets": title + "\n\n" + "\n".join("- " + p for p in body),
        "html": "<article><h1>" + html.escape(title) + "</h1>" +
                "".join("<p>" + html.escape(p) + "</p>" for p in body) + "</article>",
        "json": json.dumps({"title": title, "paragraphs": body}, ensure_ascii=False),
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lock = (OUT / ".lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    inputs = pages()
    manifest = dict(model=MODEL, code=source_digest(), runner=sha256(Path(__file__).read_bytes()).hexdigest(),
                    pages=inputs, repeats=5, defenses=DEFENSE_ORDER, workers=WORKERS,
                    temperature="provider default", objective="legitimate task completion and format sensitivity")
    manifest_file = OUT / "manifest.json"
    if manifest_file.exists() and json.loads(manifest_file.read_text()) != manifest:
        raise SystemExit("Existing run has a different configuration.")
    if not manifest_file.exists():
        atomic_json(manifest_file, manifest)
    key = os.getenv("MOONSHOT_API_KEY") or getpass("Kimi credential (hidden): ")

    def generate(prompt, *, system_instruction, model, temperature, max_output_tokens=1024):
        for attempt in range(5):
            try:
                response = requests.post("https://api.moonshot.ai/v1/chat/completions",
                    headers={"Authorization": "Bearer " + key},
                    json={"model": MODEL, "messages": [{"role": "system", "content": system_instruction},
                          {"role": "user", "content": prompt}], "max_tokens": max_output_tokens},
                    timeout=90, allow_redirects=False)
            except requests.RequestException as exc:
                raise llm.LLMError(type(exc).__name__) from None
            if response.status_code == 200:
                data = response.json()
                usage.get().append(data["usage"])
                return data["choices"][0]["message"].get("content") or ""
            if response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
                raise llm.LLMError(f"Kimi HTTP {response.status_code}")
            retry = response.headers.get("Retry-After", "")
            time.sleep(max(2**(attempt+1), float(retry) if retry.isdigit() else 0))

    def execute(job):
        fmt, condition, trial = job
        rid = f"{fmt}__{condition}__{trial}"
        path = OUT / (rid + ".json")
        if path.exists():
            return
        usage.set([])
        defense = next(d for d in build_defenses() if d.name == condition)
        run = run_agent(attack_id="__clean__", page_content=inputs[fmt], defense=defense, model=MODEL)
        success, reason = legitimate_task_success(run)
        record = dict(id=rid, format=fmt, defense=condition, trial=trial, run=run.to_dict(),
                      task_success=success, reason=reason, usage=usage.get())
        if run.error and not run.error.startswith("hit max_steps"):
            atomic_json(OUT / "failed_attempts" / f"{rid}.{time.time_ns()}.json", record)
            raise RuntimeError(run.error)
        atomic_json(path, record)

    jobs = [(fmt, d, t) for t in range(1, 6) for d in DEFENSE_ORDER for fmt in inputs]
    random.Random(42).shuffle(jobs)
    with patch.object(llm, "generate", generate), ThreadPoolExecutor(max_workers=WORKERS) as workers:
        futures = [workers.submit(execute, job) for job in jobs]
        try:
            for n, future in enumerate(as_completed(futures), 1):
                future.result()
                if n == 1 or n % 10 == 0:
                    print(f"{n}/150 episodes saved", flush=True)
        except BaseException:
            for future in futures:
                future.cancel()
            raise


if __name__ == "__main__":
    main()
