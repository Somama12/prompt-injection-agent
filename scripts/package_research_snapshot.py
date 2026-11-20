"""Build and verify a self-contained archive from explicitly selected research files."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "output/research_final"
EVIDENCE = Path("output/weeks10_12/evidence")


def select_files():
    files = set()
    for folder in ("agent", "benchmark", "defenses", "evaluation"):
        files.update(path.relative_to(ROOT) for path in (ROOT / folder).glob("*.py"))
    for folder in ("groq_pilot_v3", "groq_full_three_trials"):
        base = Path("results") / folder
        files.add(base / "manifest.json")
        files.update(path.relative_to(ROOT) for path in (ROOT / base / "episodes").glob("*.json"))
        files.update(path.relative_to(ROOT) for path in (ROOT / base / "failed_attempts").glob("*.json"))
    files.update(path.relative_to(ROOT) for path in (ROOT / "results/kimi_format_study").rglob("*.json"))
    for folder in ("one_step", "one_step_trial2", "one_step_trial3"):
        files.update(path.relative_to(ROOT) for path in (ROOT / EVIDENCE / folder).glob("*.json"))
    for name in ("archived_findings.json", "archived_security_comparison.json",
                 "archived_decision_labels.json", "kimi_summary_labels.json",
                 "credential_repair_results.json", "midterm_pilot_records.json.gz",
                 "groq_pilot_v3_records.json.gz"):
        files.add(EVIDENCE / name)
    files.update(Path(name) for name in (
        "scripts/verify_research_snapshot.py", "scripts/audit_saved_research.py",
        "output/research_final/score_audit.json", "output/research_final/software_tests.txt",
        "requirements.txt", "docs/RESEARCH_COMPLETION.md"))
    return sorted(files)


def check_for_credentials(files):
    secret_values = []
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                value = value.strip().strip("'\"")
                if re.search(r"KEY|TOKEN|PASSWORD", key, re.I) and len(value) >= 16:
                    secret_values.append(value.encode())
    for name in files:
        raw = (ROOT / name).read_bytes()
        if name.suffix == ".gz":
            raw = gzip.decompress(raw)
        if any(secret in raw for secret in secret_values) or re.search(rb"(?:gsk_|sk-)[A-Za-z0-9_-]{24,}", raw):
            raise ValueError(f"Potential credential in selected file {name}")


def main():
    os.chdir(ROOT)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    test_output = (DESTINATION / "software_tests.txt").read_text()
    if not re.search(r"\b\d+ passed\b", test_output) or re.search(r"\b\d+ (failed|error)", test_output):
        raise ValueError("Wait for a completed, passing software test log before packaging")
    files = select_files()
    check_for_credentials(files)
    manifest = dict(snapshot_date="2026-11-20", scope="Retrospective comparison of completed cohorts",
                    files={str(p): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files})
    with tempfile.TemporaryDirectory(prefix="seminar-research-") as temp:
        isolated = Path(temp)
        for name in files:
            target = isolated / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        (isolated / "RESEARCH_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        (isolated / "README.txt").write_text(
            "Senior Seminar II research snapshot, November 20, 2026\n\n"
            "From this directory run: python3 -m scripts.verify_research_snapshot\n"
            "Table reconstruction uses the Python standard library and bundled code.\n"
            "For independent rescoring and policy replay, install requirements.txt in a virtual\n"
            "environment, then run: python -m scripts.verify_research_snapshot --rescore\n"
            "Both checks run offline. No API keys or new model runs are required.\n"
            "See docs/RESEARCH_COMPLETION.md for the scope and remaining research questions.\n")
        clean_env = {k:v for k,v in os.environ.items() if k in {"PATH", "HOME", "TMPDIR", "SYSTEMROOT"}}
        checks = []
        for python, options in [(shutil.which("python3"), []), (sys.executable, ["--rescore"])]:
            result = subprocess.run([python, "-m", "scripts.verify_research_snapshot", *options],
                                    cwd=isolated, env=clean_env, text=True, capture_output=True, check=True)
            checks.append(result.stdout.strip())
        archive = DESTINATION / "Research_Snapshot_Somama_Siddiqui.zip"
        temporary = archive.with_suffix(".zip.tmp")
        with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as bundle:
            for path in sorted(isolated.rglob("*")):
                if path.is_file() and "__pycache__" not in path.parts:
                    bundle.write(path, path.relative_to(isolated))
        with ZipFile(temporary) as bundle:
            if bundle.testzip() is not None:
                raise ValueError("Archive integrity check failed")
        temporary.replace(archive)
    receipt = dict(archive=archive.name, sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                   verified_files=len(files), credential_scan="passed", isolated_verification=checks)
    (DESTINATION / "reproduction_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
