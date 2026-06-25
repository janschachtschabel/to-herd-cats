"""LangGraph runtime: an agent run as an agent<->tools loop with optional approval.

The ``agent`` node calls the model (with the agent's tool schemas); if the model
requests tools, the ``tools`` node executes them via the MCP gateway and loops
back, bounded by MAX_ITERATIONS. When the model returns a final answer, the run
ends - or, for agents whose guardrails require approval, pauses at a ``review``
node via ``interrupt()`` (the postbox). The paused state is checkpointed by the
run's thread_id; a human response resumes it.

The checkpointer is an in-process MemorySaver (process-lifetime, single-node
dev). A persistent saver on the app DB (restart/HA durability) is a follow-up.
"""

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel

from app.integrations.litellm_gateway import complete
from app.models.agent import Agent
from app.models.llm_connection import LLMConnection
from app.runtime.executor import initial_messages
from app.runtime.tools import ResolvedTool, execute_tool_call, tool_schemas

# Process-lifetime checkpoint store shared across runs (dev). Durable saver = M5.
_CHECKPOINTER = MemorySaver()
MAX_ITERATIONS = 8


class RunState(TypedDict, total=False):
    messages: list[dict]
    pending: list[dict]
    iterations: int
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


def _make_agent_node(connection: LLMConnection, schemas: list[dict]):
    async def agent(state: RunState) -> dict[str, Any]:
        messages = state.get("messages", [])
        result = await complete(connection, messages, tools=schemas or None)
        assistant = result.assistant_message or {
            "role": "assistant",
            "content": result.content,
        }
        update: dict[str, Any] = {
            "messages": messages + [assistant],
            "usage": {
                "tokens": result.total_tokens,
                "cost": result.cost,
                "model": result.model,
            },
        }
        if result.tool_calls:
            update["pending"] = result.tool_calls
        else:
            update["pending"] = []
            update["draft"] = result.content
        return update

    return agent


def _tool_needs_approval(resolved: list[ResolvedTool], call: dict) -> bool:
    match = next((r for r in resolved if r.tool.name == call.get("name")), None)
    return bool(match and match.tool.requires_approval)


def _make_tools_node(resolved: list[ResolvedTool]):
    async def tools(state: RunState) -> dict[str, Any]:
        pending = state.get("pending", [])
        # The approval interrupt must precede execution: LangGraph re-runs a node
        # from the top on resume, so a tool executed before the interrupt would
        # run twice. Decide approvals first (pure), then execute once.
        needs_approval = [c for c in pending if _tool_needs_approval(resolved, c)]
        decision: dict = {}
        if needs_approval:
            decision = interrupt(
                {
                    "type": "approval_request",
                    "description_md": "Approve tool call(s): "
                    + ", ".join(c["name"] for c in needs_approval),
                    "tool_calls": needs_approval,
                    "allowed_responses": ["accept", "reject"],
                }
            )
        rejected = (decision or {}).get("action") == "reject"

        tool_messages = []
        for call in pending:
            if rejected and _tool_needs_approval(resolved, call):
                output = "Tool call rejected by a human."
            else:
                output = await execute_tool_call(resolved, call)
            tool_messages.append({"role": "tool", "tool_call_id": call["id"], "content": output})
        return {
            "messages": state.get("messages", []) + tool_messages,
            "pending": [],
            "iterations": state.get("iterations", 0) + 1,
        }

    return tools


def _make_route(requires_approval: bool):
    def route(state: RunState) -> str:
        if state.get("pending") and state.get("iterations", 0) < MAX_ITERATIONS:
            return "tools"
        return "review" if requires_approval else END

    return route


def _review(state: RunState) -> dict[str, Any]:
    decision = interrupt(
        {
            "type": "approval_request",
            "description_md": state.get("draft", ""),
            "allowed_responses": ["accept", "edit", "reject"],
        }
    )
    return {"decision": decision}


def _build(agent: Agent, connection: LLMConnection, resolved: list[ResolvedTool]):
    requires_approval = _requires_approval(agent)
    builder = StateGraph(RunState)
    builder.add_node("agent", _make_agent_node(connection, tool_schemas(resolved)))
    builder.add_node("tools", _make_tools_node(resolved))
    builder.add_edge(START, "agent")
    builder.add_edge("tools", "agent")

    path_map: dict[str, str] = {"tools": "tools", END: END}
    if requires_approval:
        builder.add_node("review", _review)
        builder.add_edge("review", END)
        path_map["review"] = "review"
    builder.add_conditional_edges("agent", _make_route(requires_approval), path_map)
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
    agent: Agent,
    connection: LLMConnection,
    resolved: list[ResolvedTool],
    run_input: dict,
    thread_id: str,
    context: str = "",
) -> GraphResult:
    graph = _build(agent, connection, resolved)
    config = {"configurable": {"thread_id": thread_id}}
    messages = initial_messages(agent, run_input.get("goal", ""), context)
    out = await graph.ainvoke({"messages": messages}, config=config)
    return _interpret(out)


async def resume_run(
    agent: Agent,
    connection: LLMConnection,
    resolved: list[ResolvedTool],
    thread_id: str,
    response: dict,
) -> GraphResult:
    graph = _build(agent, connection, resolved)
    config = {"configurable": {"thread_id": thread_id}}
    out = await graph.ainvoke(Command(resume=response), config=config)
    return _interpret(out)
