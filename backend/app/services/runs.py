"""Business logic for Runs: create + execute (via the graph), postbox respond, read.

Execution is synchronous and routed through the LangGraph runtime: a run either
completes, or pauses at an approval interrupt (status=waiting_human) and posts an
InboxItem. A human response resumes the run. Background/durable execution is M5.
"""

# Lazy annotations: the CRUD ``list`` method shadows the builtin ``list`` in the
# class namespace, so method return hints like ``list[ResolvedTool]`` must not be
# evaluated eagerly.
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models._base import utcnow
from app.models.agent import Agent
from app.models.inbox_item import InboxItem
from app.models.llm_connection import LLMConnection
from app.models.run import Run
from app.repositories.agents import SqlAlchemyAgentRepository
from app.repositories.inbox_items import SqlAlchemyInboxItemRepository
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository
from app.repositories.mcp_servers import SqlAlchemyMCPServerRepository
from app.repositories.runs import SqlAlchemyRunRepository
from app.repositories.tools import SqlAlchemyToolRepository
from app.runtime.graph import GraphResult, resume_run, start_run
from app.runtime.tools import ResolvedTool
from app.schemas.run import RunInput
from app.services.base import EntityNotFoundError


class RunConfigError(Exception):
    """Raised when an agent cannot be run (e.g. no usable LLM connection)."""


class InboxStateError(Exception):
    """Raised when an inbox item cannot accept a response (already answered)."""


class RunService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._runs = SqlAlchemyRunRepository(session)
        self._agents = SqlAlchemyAgentRepository(session)
        self._llm = SqlAlchemyLLMConnectionRepository(session)
        self._inbox = SqlAlchemyInboxItemRepository(session)
        self._tools = SqlAlchemyToolRepository(session)
        self._mcp = SqlAlchemyMCPServerRepository(session)

    async def get(self, run_id: str) -> Run:
        run = await self._runs.get(run_id)
        if run is None:
            raise EntityNotFoundError(run_id)
        return run

    async def list(self) -> list[Run]:
        return await self._runs.list()

    async def create_and_execute(self, agent_id: str, payload: RunInput) -> Run:
        agent = await self._agents.get(agent_id)
        if agent is None:
            raise EntityNotFoundError(agent_id)
        connection = await self._resolve_connection(agent)
        resolved = await self._resolve_tools(agent)

        run = Run(agent_id=agent_id, status="queued", input=payload.model_dump(mode="json"))
        await self._runs.add(run)
        await self._session.commit()

        run.status = "running"
        run.started_at = utcnow()
        run.thread_id = run.id
        await self._session.commit()

        try:
            result = await start_run(agent, connection, resolved, run.input, thread_id=run.id)
        except Exception as exc:  # provider/runtime failure -> failed run
            self._mark_failed(run, exc)
        else:
            self._apply_result(run, agent, result)
        await self._session.commit()
        await self._session.refresh(run)
        return run

    async def respond_to_inbox(self, inbox_item_id: str, response: dict) -> Run:
        item = await self._inbox.get(inbox_item_id)
        if item is None:
            raise EntityNotFoundError(inbox_item_id)
        if item.status != "pending":
            raise InboxStateError("inbox item already answered")
        run = await self.get(item.run_id)
        agent = await self._agents.get(run.agent_id)
        connection = await self._resolve_connection(agent)
        resolved = await self._resolve_tools(agent)

        try:
            result = await resume_run(agent, connection, resolved, run.thread_id, response)
        except Exception as exc:
            self._mark_failed(run, exc)
        else:
            self._apply_result(run, agent, result)

        item.status = "answered"
        item.response = response
        item.responded_by = response.get("responded_by")
        item.responded_at = utcnow()
        await self._session.commit()
        await self._session.refresh(run)
        return run

    async def _resolve_connection(self, agent: Agent) -> LLMConnection:
        if not agent.llm_connection_id:
            raise RunConfigError("agent has no LLM connection")
        connection = await self._llm.get(agent.llm_connection_id)
        if connection is None:
            raise RunConfigError("agent's LLM connection does not exist")
        return connection

    async def _resolve_tools(self, agent: Agent) -> list[ResolvedTool]:
        resolved: list[ResolvedTool] = []
        for tool_id in agent.tool_ids or []:
            tool = await self._tools.get(tool_id)
            if tool is None or not tool.enabled:
                continue
            server = await self._mcp.get(tool.mcp_server_id) if tool.mcp_server_id else None
            resolved.append(ResolvedTool(tool=tool, server=server))
        return resolved

    def _wait_for_human(self, run: Run, agent: Agent, result: GraphResult) -> None:
        run.status = "waiting_human"
        value = result.interrupt_value or {}
        self._session.add(
            InboxItem(
                run_id=run.id,
                agent_id=agent.id,
                type=value.get("type", "approval_request"),
                payload=value,
                allowed_responses=value.get("allowed_responses", []),
                status="pending",
            )
        )

    def _apply_result(self, run: Run, agent: Agent, result: GraphResult) -> None:
        # A resume can pause again (another tool approval, or the output review),
        # so this is shared by both create and respond.
        if result.interrupted:
            self._wait_for_human(run, agent, result)
        else:
            self._finalize(run, result)

    def _finalize(self, run: Run, result: GraphResult) -> None:
        # The output decision comes from the graph (the review node), not the raw
        # response, so a tool-approval reply is never misread as an output verdict.
        decision = result.decision or {}
        action = decision.get("action", "accept")
        if action == "reject":
            run.result = {"rejected": True}
        elif action == "edit":
            run.result = {"content": decision.get("content", result.draft)}
        else:  # accept / no approval needed
            run.result = {"content": result.draft}
        if result.usage:
            run.metrics = result.usage
        run.status = "completed"
        run.finished_at = utcnow()

    def _mark_failed(self, run: Run, exc: Exception) -> None:
        run.status = "failed"
        run.result = {"error": str(exc)}
        run.finished_at = utcnow()
