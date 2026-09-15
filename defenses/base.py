"""The defense interface.

Every defense is a small object that hooks one of three points in the agent
loop. Keeping the hooks narrow is what makes the comparison fair: the agent
architecture, model, temperature and task are identical across conditions, and
only these three seams change.

    system_suffix()        -> text appended to the agent's system prompt
    wrap_tool_result()     -> rewrites untrusted tool output before the agent sees it
    check_action()         -> vetoes a proposed tool call before it executes
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionContext:
    """What a defense knows when it decides whether to allow a tool call."""

    step: int
    tool_name: str
    args: dict[str, Any]
    transcript: str
    untrusted_content: str
    prior_calls: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    allowed: bool
    reason: str = ""


ALLOW = Verdict(True)


class Defense:
    name = "none"
    label = "No defense"
    description = "Baseline agent with no protective measures."

    def system_suffix(self) -> str:
        return ""

    def wrap_tool_result(self, tool_name: str, result: str) -> str:
        return result

    def check_action(self, ctx: ActionContext) -> Verdict:
        return ALLOW

    # Reported in the results table as a rough complexity proxy.
    @property
    def extra_llm_calls_per_action(self) -> int:
        return 0


class CompositeDefense(Defense):
    """Defense-in-depth: run several defenses in series.

    System suffixes concatenate, wrappers chain, and the first veto wins.
    """

    def __init__(self, name: str, label: str, parts: list[Defense], description: str = "") -> None:
        self.name = name
        self.label = label
        self.parts = parts
        self.description = description or "Layered: " + " + ".join(p.name for p in parts)

    def system_suffix(self) -> str:
        return "\n".join(s for s in (p.system_suffix() for p in self.parts) if s)

    def wrap_tool_result(self, tool_name: str, result: str) -> str:
        for p in self.parts:
            result = p.wrap_tool_result(tool_name, result)
        return result

    def check_action(self, ctx: ActionContext) -> Verdict:
        for p in self.parts:
            verdict = p.check_action(ctx)
            if not verdict.allowed:
                return Verdict(False, f"[{p.name}] {verdict.reason}")
        return ALLOW

    @property
    def extra_llm_calls_per_action(self) -> int:
        return sum(p.extra_llm_calls_per_action for p in self.parts)
