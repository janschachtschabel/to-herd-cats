"""LangGraph runtime: an agent run as a graph, with optional human approval.

The graph generates a draft (reusing the M4.1 executor); for agents whose
guardrails require approval it pauses at a ``review`` node via LangGraph's
``interrupt()``. The paused state is checkpointed (keyed by the run's
thread_id) and a human response resumes it.

The checkpointer is an in-process MemorySaver: paused runs survive for the
process lifetime, which is enough for single-node dev. A persistent saver on the
app DB (for restart/HA durability) is a follow-up (plan, M5).
"""

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel

from app.models.agent import Agent
from app.models.llm_connection import LLMConnection
from app.runtime.executor import run_agent

# Process-lifetime checkpoint store shared across runs (dev). Durable saver = M5.
_CHECKPOINTER = MemorySaver()


class RunState(TypedDict, total=False):
    goal: str
    draft: str
    usage: dict
    decision: dict


class GraphResult(BaseModel):
    interrupted: bool
    interrupt_value: dict | None = None
    draft: str | None = None
    usage: dict | None = None
    decision: dict | None = None


def _requires_approval(agent: Agent) -> bool:
    return bool((agent.guardrails or {}).get("requires_approval_for"))


def _make_generate(agent: Agent, connection: LLMConnection):
    async def generate(state: RunState) -> dict[str, Any]:
        outcome = await run_agent(agent, connection, {"goal": state.get("goal", "")})
        return {
            "draft": outcome.content,
            "usage": {
                "tokens": outcome.total_tokens,
                "cost": outcome.cost,
                "model": outcome.model,
            },
        }

    return generate


def _review(state: RunState) -> dict[str, Any]:
    decision = interrupt(
        {
            "type": "approval_request",
            "description_md": state.get("draft", ""),
            "allowed_responses": ["accept", "edit", "reject"],
        }
    )
    return {"decision": decision}


def _build(agent: Agent, connection: LLMConnection):
    builder = StateGraph(RunState)
    builder.add_node("generate", _make_generate(agent, connection))
    builder.add_edge(START, "generate")
    if _requires_approval(agent):
        builder.add_node("review", _review)
        builder.add_edge("generate", "review")
        builder.add_edge("review", END)
    else:
        builder.add_edge("generate", END)
    return builder.compile(checkpointer=_CHECKPOINTER)


def _interpret(out: dict) -> GraphResult:
    if "__interrupt__" in out:
        return GraphResult(interrupted=True, interrupt_value=out["__interrupt__"][0].value)
    return GraphResult(
        interrupted=False,
        draft=out.get("draft"),
        usage=out.get("usage"),
        decision=out.get("decision"),
    )


async def start_run(
    agent: Agent, connection: LLMConnection, run_input: dict, thread_id: str
) -> GraphResult:
    graph = _build(agent, connection)
    config = {"configurable": {"thread_id": thread_id}}
    out = await graph.ainvoke({"goal": run_input.get("goal", "")}, config=config)
    return _interpret(out)


async def resume_run(
    agent: Agent, connection: LLMConnection, thread_id: str, response: dict
) -> GraphResult:
    graph = _build(agent, connection)
    config = {"configurable": {"thread_id": thread_id}}
    out = await graph.ainvoke(Command(resume=response), config=config)
    return _interpret(out)
