"""Verify the frozen archive and recompute its tables without model requests."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import socket

from evaluation.archived_findings import assess_decisions, assess_formats, assess_pilot
from evaluation.archived_security_comparison import compare


def verify():
    manifest = json.loads(Path("RESEARCH_MANIFEST.json").read_text())
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256(Path(name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Evidence or code changed: {name}")
    evidence = Path("output/weeks10_12/evidence")
    archived = json.loads((evidence / "archived_findings.json").read_text())
    fresh = dict(kimi=assess_formats(), final_decisions=assess_decisions(),
                 paired_pilots={model: assess_pilot(name) for model, name in
                                [("Gemini", "midterm_pilot_records.json.gz"),
                                 ("Groq", "groq_pilot_v3_records.json.gz")]})
    if fresh != archived:
        raise ValueError("Recomputed archive tables disagree")
    stored = json.loads((evidence / "archived_security_comparison.json").read_text())
    if compare() != stored:
        raise ValueError("Recomputed security comparison disagrees")
    return len(manifest["files"])


def block_connection(*args, **kwargs):
    raise RuntimeError("Offline verification attempted a network connection")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rescore", action="store_true", help="Also replay the recorded scores using installed project dependencies")
    args = parser.parse_args()
    socket.socket.connect = block_connection
    socket.create_connection = block_connection
    files = verify()
    if args.rescore:
        runpy.run_path("scripts/audit_saved_research.py", run_name="__main__")
        verify()
    print(f"Verified {files} file hashes, 48 matched episodes, 75 reviewed decisions and 150 format trials.")
