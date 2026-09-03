"""The agentic tutor: an AI agent that interprets a user's problem and orchestrates the
deterministic engine's tools to solve, visualize, and explain it.

The layer is deliberately **transport-agnostic**. The orchestration loop, the tool
registry, the inspectable trace, and the grounding gate are the same no matter what decides
which tools to call. Two "brains" plug into it:

  * ``ClaudeBrain`` — the real product: Claude interprets the request and drives the tools
    through the Anthropic API (the ``anthropic`` package is imported lazily, only when this
    brain is actually constructed, so nothing else here needs it or the network);
  * ``OfflineBrain`` — a deterministic interpreter that plans the same tool calls from the
    input's structure. It is the graceful fallback when no API key is present, and it is
    what the offline checks run the agent with (constraint C-LOCAL keeps checks off the
    network).

Either way the mathematics is done by the tools, every displayed value traces to a verified
tool result or is labelled model-derived (C-VERIFIED-MATH), and the trace records exactly
which tools were chosen and in what order (criterion G3).
"""

from .agent import Agent, AgentResult, build_agent
from .trace import AgentTrace, ToolCall
from .tools import ToolRegistry, ToolResult

__all__ = [
    "Agent",
    "AgentResult",
    "build_agent",
    "AgentTrace",
    "ToolCall",
    "ToolRegistry",
    "ToolResult",
]
