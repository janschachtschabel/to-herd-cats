"""Business logic for Runs: create + execute (via the graph), postbox respond, read.

Execution is synchronous and routed through the LangGraph runtime: a run either
completes, or pauses at an approval interrupt (status=waiting_human) and posts an
InboxItem. A human response resumes the run. Background/durable execution is M5.
"""

# Lazy annotations: the CRUD ``list`` method shadows the builtin ``list`` in the
# class namespace, so method return hints like ``list[ResolvedTool]`` must not be
# evaluated eagerly.
from __future__ import annotations

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.channels.delivery import route_and_deliver
from app.models._base import utcnow
from app.models.agent import Agent
from app.models.inbox_item import InboxItem
from app.models.llm_connection import LLMConnection
from app.models.memory import MemoryRecord
from app.models.run import Run
from app.repositories.agents import SqlAlchemyAgentRepository
from app.repositories.data_sources import SqlAlchemyDataSourceRepository
from app.repositories.inbox_items import SqlAlchemyInboxItemRepository
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository
from app.repositories.mcp_servers import SqlAlchemyMCPServerRepository
from app.repositories.memories import SqlAlchemyMemoryRepository
from app.repositories.runs import SqlAlchemyRunRepository
from app.repositories.skills import SqlAlchemySkillRepository
from app.repositories.templates import SqlAlchemyTemplateRepository
from app.repositories.tools import SqlAlchemyToolRepository
from app.runtime.graph import GraphResult, resume_run, start_run
from app.runtime.memory import embedding_for, recall
from app.runtime.retrieval import ResolvedDataSource, retrieve_context
from app.runtime.structured import compare_results, render_output, structure_output
from app.runtime.tools import ResolvedTool
from app.schemas.run import RunInput
from app.services.base import EntityNotFoundError

logger = logging.getLogger(__name__)


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
        self._templates = SqlAlchemyTemplateRepository(session)
        self._data_sources = SqlAlchemyDataSourceRepository(session)
        self._memories = SqlAlchemyMemoryRepository(session)
        self._skills = SqlAlchemySkillRepository(session)

    async def get(self, run_id: str) -> Run:
        run = await self._runs.get(run_id)
        if run is None:
            raise EntityNotFoundError(run_id)
        return run

    async def list(self) -> list[Run]:
        return await self._runs.list()

    async def compare(
        self,
        run_a_id: str,
        run_b_id: str,
        fields: list[str] | None = None,
        template_id: str | None = None,
    ) -> dict:
        run_a = await self.get(run_a_id)
        run_b = await self.get(run_b_id)
        comparison = compare_results(run_a.result or {}, run_b.result or {}, fields)
        rendered = None
        if template_id:
            template = await self._templates.get(template_id)
            if template and template.render_template:
                rendered = render_output(template.render_template, comparison)
        return {"comparison": comparison, "rendered": rendered}

    async def create_and_execute(
        self, agent_id: str, payload: RunInput, trigger_id: str | None = None
    ) -> Run:
        agent = await self._agents.get(agent_id)
        if agent is None:
            raise EntityNotFoundError(agent_id)
        connection = await self._resolve_connection(agent)
        resolved = await self._resolve_tools(agent)
        sources = await self._resolve_data_sources(agent)
        skills = await self._resolve_skills(agent)

        run = Run(
            agent_id=agent_id,
            trigger_id=trigger_id,
            status="queued",
            input=payload.model_dump(mode="json"),
        )
        await self._runs.add(run)
        await self._session.commit()

        run.status = "running"
        run.started_at = utcnow()
        run.thread_id = run.id
        await self._session.commit()

        context = await self._build_context(agent, payload.goal, sources, connection)
        try:
            result = await start_run(
                agent,
                connection,
                resolved,
                run.input,
                thread_id=run.id,
                context=context,
                skills=skills,
            )
        except Exception as exc:  # provider/runtime failure -> failed run
            self._mark_failed(run, exc)
        else:
            await self._apply_result(run, agent, result, connection)
        await self._session.commit()
        await self._session.refresh(run)
        await self._route_pending_items(run)
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
            # Leave the item pending so a transient failure can be answered again.
            self._mark_failed(run, exc)
            await self._session.commit()
            await self._session.refresh(run)
            return run

        await self._apply_result(run, agent, result, connection)
        item.status = "answered"
        item.response = response
        item.responded_by = response.get("responded_by")
        item.responded_at = utcnow()
        await self._session.commit()
        await self._session.refresh(run)
        await self._route_pending_items(run)
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
                logger.warning("agent %s skips missing or disabled tool %s", agent.id, tool_id)
                continue
            server = await self._mcp.get(tool.mcp_server_id) if tool.mcp_server_id else None
            resolved.append(ResolvedTool(tool=tool, server=server))
        return resolved

    async def _resolve_data_sources(self, agent: Agent) -> list[ResolvedDataSource]:
        resolved: list[ResolvedDataSource] = []
        for ds_id in agent.data_source_ids or []:
            ds = await self._data_sources.get(ds_id)
            if ds is None or not ds.enabled:
                logger.warning("agent %s skips missing or disabled data source %s", agent.id, ds_id)
                continue
            server = await self._mcp.get(ds.mcp_server_id) if ds.mcp_server_id else None
            resolved.append(ResolvedDataSource(data_source=ds, server=server))
        return resolved

    async def _resolve_skills(self, agent: Agent) -> str:
        """Combine the agent's enabled skills' instructions into one prompt block."""
        blocks: list[str] = []
        for skill_id in agent.skill_ids or []:
            skill = await self._skills.get(skill_id)
            if skill is None or not skill.enabled:
                logger.warning("agent %s skips missing or disabled skill %s", agent.id, skill_id)
                continue
            blocks.append(f"## Skill: {skill.name}\n{skill.instructions}".strip())
        return "\n\n".join(blocks)

    async def _build_context(
        self,
        agent: Agent,
        goal: str,
        sources: list[ResolvedDataSource],
        connection: LLMConnection,
    ) -> str:
        # Recalled memory and retrieved data-source content are both injected as
        # run context; each section labels itself (see initial_messages).
        sections: list[str] = []
        memory = await self._recall_memory(agent, goal, connection)
        if memory:
            sections.append(memory)
        if sources:
            retrieved = await retrieve_context(sources, goal)
            if retrieved:
                sections.append(retrieved)
        return "\n\n".join(sections)

    async def _recall_memory(self, agent: Agent, query: str, connection: LLMConnection) -> str:
        mode = (agent.memory or {}).get("mode", "none")
        if mode == "none":
            return ""
        memories = await self._memories.for_agent(agent.id)
        recalled = await recall(memories, mode, query, connection)
        return f"Memory from past interactions:\n{recalled}" if recalled else ""

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

    async def _route_pending_items(self, run: Run) -> None:
        # After a run pauses, route its new postbox item(s) to outbound channels
        # and persist which channels they went to. Delivery is best-effort.
        if run.status != "waiting_human":
            return
        items = await self._inbox.pending_for_run(run.id)
        for item in items:
            await route_and_deliver(self._session, item)
        if items:
            await self._session.commit()

    async def _apply_result(
        self, run: Run, agent: Agent, result: GraphResult, connection: LLMConnection
    ) -> None:
        # A resume can pause again (another tool approval, or the output review),
        # so this is shared by both create and respond.
        if result.interrupted:
            self._wait_for_human(run, agent, result)
        else:
            await self._finalize(run, agent, result, connection)

    async def _finalize(
        self, run: Run, agent: Agent, result: GraphResult, connection: LLMConnection
    ) -> None:
        # The output decision comes from the graph (the review node), not the raw
        # response, so a tool-approval reply is never misread as an output verdict.
        decision = result.decision or {}
        action = decision.get("action", "accept")
        if action == "reject":
            run.result = {"rejected": True}
        else:
            content = decision.get("content", result.draft) if action == "edit" else result.draft
            await self._apply_output(run, agent, content or "", connection)
        if result.usage:
            run.metrics = result.usage
        run.status = "completed"
        run.finished_at = utcnow()
        await self._store_memory(run, agent, connection)

    async def _apply_output(
        self, run: Run, agent: Agent, content: str, connection: LLMConnection
    ) -> None:
        # With a template, coerce the answer into its schema and render it;
        # otherwise keep the plain-text answer.
        template = await self._resolve_template(agent)
        if template is None or not template.output_schema:
            run.result = {"content": content}
            return
        structured = await structure_output(connection, content, template.output_schema)
        run.result = structured
        if template.render_template:
            run.rendered_outputs = [
                {
                    "format": template.format,
                    "content": render_output(template.render_template, structured),
                }
            ]

    async def _store_memory(self, run: Run, agent: Agent, connection: LLMConnection) -> None:
        # Persist a completed interaction so future runs of this agent can recall
        # it; long-term mode also stores an embedding for semantic recall.
        mode = (agent.memory or {}).get("mode", "none")
        if mode == "none":
            return
        goal = (run.input or {}).get("goal", "")
        content = f"Goal: {goal}\nAnswer: {self._memory_answer(run.result or {})}"
        embedding = await embedding_for(content, mode, connection)
        self._session.add(
            MemoryRecord(agent_id=agent.id, run_id=run.id, content=content, embedding=embedding)
        )

    @staticmethod
    def _memory_answer(result: dict) -> str:
        if "content" in result:
            return str(result["content"])
        if result.get("rejected"):
            return "(output rejected by a human)"
        return json.dumps(result, ensure_ascii=False)

    async def _resolve_template(self, agent: Agent):
        if not agent.default_template_id:
            return None
        return await self._templates.get(agent.default_template_id)

    def _mark_failed(self, run: Run, exc: Exception) -> None:
        logger.exception("run %s failed", run.id)
        run.status = "failed"
        run.result = {"error": str(exc)}
        run.finished_at = utcnow()
