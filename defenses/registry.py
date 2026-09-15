"""The set of defense conditions evaluated in the study.

Order matters only for presentation. `none` is the baseline; the four single
defenses map to the proposal's four mechanisms; `combined` is a defense-in-depth
stack used to show the ceiling.
"""
from __future__ import annotations

from defenses.base import CompositeDefense, Defense
from defenses.allowlist import AllowlistDefense
from defenses.guard_llm import GuardLLMDefense
from defenses.instruction_hierarchy import InstructionHierarchyDefense
from defenses.sanitization import SanitizationDefense


def build_defenses() -> list[Defense]:
    sanit = SanitizationDefense()
    hier = InstructionHierarchyDefense()
    guard = GuardLLMDefense()
    allow = AllowlistDefense()
    combined = CompositeDefense(
        name="combined",
        label="Defense-in-depth",
        parts=[SanitizationDefense(), InstructionHierarchyDefense(), AllowlistDefense(), GuardLLMDefense()],
        description="All four defenses layered together.",
    )
    return [Defense(), sanit, hier, guard, allow, combined]


DEFENSE_ORDER = ["none", "sanitization", "instruction_hierarchy", "guard_llm", "allowlist", "combined"]
