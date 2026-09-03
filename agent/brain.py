"""The brain interface — what decides which tools to call.

A brain interprets the request and *orchestrates* the tools (through the shared tracer, so
the trace, provenance capture and grounding are identical whoever is driving). It returns an
``OrchestrationResult``: the answer text, the active scene, the verified quantities behind
it, and any view-driving directives. It never computes mathematics itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OrchestrationResult:
    answer: str
    scene: dict | None = None
    area: str = ""
    quantities: list[dict] = field(default_factory=list)
    directives: list[dict] = field(default_factory=list)
    grounded_in: list[str] = field(default_factory=list)
    walkthrough: list[dict] = field(default_factory=list)
    declined: bool = False
    model_derived: bool = False


class Brain:
    kind = "base"

    def orchestrate(self, text: str, ctx: dict, tracer) -> OrchestrationResult:
        raise NotImplementedError
