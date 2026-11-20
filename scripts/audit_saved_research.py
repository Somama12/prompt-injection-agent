"""Recompute archived scores and verify local replay using saved observations."""
import json
from pathlib import Path

from agent.agent import AgentRun
from agent.tools import ToolCall
from benchmark.attacks import ATTACKS
from evaluation.archived_findings import EVIDENCE, digest, read, require
from evaluation.credential_repair_study import analyze
from evaluation.scorer import legitimate_task_success, programmatic_attack_success

attacks = {attack.id: attack for attack in ATTACKS}
audit = []
errors = []
for collection in ("groq_pilot_v3", "groq_full_three_trials"):
    for path in sorted((Path("results") / collection / "episodes").glob("*.json")):
        record = read(path)
        cell = record["cell"]
        if cell["error"]:
            errors.append(str(path))
            continue
        trace = record["run"].copy()
        trace["tool_calls"] = [ToolCall(**call) for call in trace["tool_calls"]]
        run = AgentRun(**trace)
        task = legitimate_task_success(run)[0]
        effect = None
        if cell["attack_id"] != "__clean__":
            effect = programmatic_attack_success(attacks[cell["attack_id"]], run)[0]
        require((task, effect) == (cell["legitimate_success"], cell["programmatic_success"]),
                f"Rescoring disagrees at {path}")
        executed = [call.args for call in run.tool_calls
                    if call.name == "send_email" and call.blocked_by is None and not call.result.startswith("ERROR:")]
        require(executed == run.sent_emails, f"Mailbox disagrees with executed actions at {path}")
        audit.append(dict(path=str(path), sha256=digest(path.read_bytes()), task=task, assigned_effect=effect))
require(len(audit) == 66 and len(errors) == 1, "Unexpected archived source coverage")
require(analyze(EVIDENCE) == read(EVIDENCE / "credential_repair_results.json"), "Paired replay drift")
result = dict(source_episodes_rescored=len(audit), excluded_terminal_errors=errors,
              score_disagreements=0, mailbox_disagreements=0, final_decisions_replayed=75, rows=audit)
destination = Path("output/research_final/score_audit.json")
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print("66 source episodes rescored and 75 final decisions replayed without discrepancies.")
