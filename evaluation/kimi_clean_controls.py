"""Measure legitimate task completion and latency on the fixed clean article."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from getpass import getpass
from hashlib import sha256
import json
import os
from pathlib import Path
from unittest.mock import patch

import requests

from agent import llm
from agent.agent import run_agent
from benchmark.attacks import clean_page
from defenses.registry import DEFENSE_ORDER, build_defenses
from evaluation.harness import atomic_json, source_digest
from evaluation.scorer import legitimate_task_success


MODEL = "kimi-k3.1-pro"
OUT = Path("results/kimi_clean_controls")
usage = ContextVar("episode_usage")


def main():
    key = os.getenv("MOONSHOT_API_KEY") or getpass("Kimi credential (hidden): ")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = dict(model=MODEL, page_sha256=sha256(clean_page().encode()).hexdigest(),
                    code_sha256=source_digest(), runner_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                    temperature="provider default", scope="18 clean controls", concurrent_episodes=3)
    frozen = OUT / "manifest.json"
    if frozen.exists() and json.loads(frozen.read_text()) != manifest:
        raise SystemExit("Saved control configuration differs.")
    atomic_json(frozen, manifest)

    def generate(prompt, *, system_instruction, model, temperature, max_output_tokens=1024):
        reply = requests.post(
            "https://api.moonshot.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": MODEL, "messages": [
                {"role": "system", "content": system_instruction}, {"role": "user", "content": prompt}],
                  "max_tokens": max_output_tokens},
            timeout=90, allow_redirects=False)
        if reply.status_code != 200:
            raise llm.LLMError(f"Kimi HTTP {reply.status_code}")
        data = reply.json()
        usage.get().append(data.get("usage", {}))
        return data["choices"][0]["message"].get("content") or ""

    def episode(job):
        trial, name = job
        target = OUT / f"{name}__clean__{trial}.json"
        if target.exists():
            return
        usage.set([])
        defense = next(d for d in build_defenses() if d.name == name)
        run = run_agent(attack_id="__clean__", page_content=clean_page(), defense=defense, model=MODEL)
        success, reason = legitimate_task_success(run)
        atomic_json(target, dict(trial=trial, defense=name, model=MODEL, run=run.to_dict(),
                                 task_success=success, task_reason=reason, usage=usage.get()))
        print(f"Trial {trial} {name}: {run.latency_s:.1f}s, task={success}, error={run.error!r}", flush=True)
        if run.error.startswith("Kimi HTTP") or "Kimi HTTP" in run.error:
            raise RuntimeError(run.error)

    with patch.object(llm, "generate", generate), ThreadPoolExecutor(max_workers=3) as workers:
        for trial in range(1, 4):
            list(workers.map(episode, [(trial, name) for name in DEFENSE_ORDER]))


if __name__ == "__main__":
    main()
