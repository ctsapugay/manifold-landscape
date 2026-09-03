"""The agent trace — an inspectable record of what the agent did.

Every tool the agent calls is recorded here: the tool's name, the input the agent chose,
whether it succeeded, and — crucially — the *provenance* of every value the tool produced
and whether it passed verification. This is what the transparency toggle (criterion G7)
shows the user, and what the G3 check reads to confirm the agent chose and sequenced tool
calls in response to the input, with every displayed value coming from a tool.

Plain dataclasses, JSON-serializable; no dependency on the transport.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ToolCall:
    """One tool invocation the agent made, and what it produced."""

    index: int
    tool: str
    input: dict
    ok: bool
    summary: str = ""
    area: str = ""
    # provenance of each verified quantity the tool produced (never "model")
    provenance: list[str] = field(default_factory=list)
    produced: list[str] = field(default_factory=list)  # quantity names
    verified: bool = False  # every produced quantity passed its verification step
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentTrace:
    """The full record of one agent turn: how it interpreted the input and every tool call.

    ``brain`` names what decided the tool calls ("claude" or "offline"); ``interpretation``
    is the agent's read of the request (area, kind), so a reader can see the *reasoning
    step* even though the values all come from tools.
    """

    brain: str
    request: str
    interpretation: str = ""
    calls: list[ToolCall] = field(default_factory=list)
    model_derived: bool = False  # did any displayed value come from the model, not a tool?

    def record(self, call: ToolCall) -> ToolCall:
        self.calls.append(call)
        return call

    @property
    def tool_sequence(self) -> list[str]:
        return [c.tool for c in self.calls]

    @property
    def all_verified(self) -> bool:
        """True if every successful tool call produced only verified quantities."""
        producing = [c for c in self.calls if c.ok and c.produced]
        return bool(producing) and all(c.verified for c in producing)

    def to_dict(self) -> dict:
        return {
            "brain": self.brain,
            "request": self.request,
            "interpretation": self.interpretation,
            "tool_sequence": self.tool_sequence,
            "calls": [c.to_dict() for c in self.calls],
            "model_derived": self.model_derived,
        }
