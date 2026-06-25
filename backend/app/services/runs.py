"""Business logic for Runs: create, execute on demand, and read.

M4.1 executes synchronously as a single LLM call. Background/durable execution
(triggers) and the LangGraph postbox come in later sub-increments.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models._base import utcnow
from app.models.agent import Agent
from app.models.llm_connection import LLMConnection
from app.models.run import Run
from app.repositories.agents import SqlAlchemyAgentRepository
from app.repositories.llm_connections import SqlAlchemyLLMConnectionRepository
from app.repositories.runs import SqlAlchemyRunRepository
from app.runtime.executor import run_agent
from app.schemas.run import RunInput
from app.services.base import EntityNotFoundError


class RunConfigError(Exception):
    """Raised when an agent cannot be run (e.g. no usable LLM connection)."""


class RunService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._runs = SqlAlchemyRunRepository(session)
        self._agents = SqlAlchemyAgentRepository(session)
        self._llm = SqlAlchemyLLMConnectionRepository(session)

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

        run = Run(agent_id=agent_id, status="queued", input=payload.model_dump(mode="json"))
        await self._runs.add(run)
        await self._session.commit()

        await self._execute(run, agent, connection)
        await self._session.refresh(run)
        return run

    async def _resolve_connection(self, agent: Agent) -> LLMConnection:
        if not agent.llm_connection_id:
            raise RunConfigError("agent has no LLM connection")
        connection = await self._llm.get(agent.llm_connection_id)
        if connection is None:
            raise RunConfigError("agent's LLM connection does not exist")
        return connection

    async def _execute(self, run: Run, agent: Agent, connection: LLMConnection) -> None:
        run.status = "running"
        run.started_at = utcnow()
        await self._session.commit()
        try:
            outcome = await run_agent(agent, connection, run.input)
        except Exception as exc:  # provider/LLM failure -> record a failed run
            run.status = "failed"
            run.result = {"error": str(exc)}
        else:
            run.result = {"content": outcome.content}
            run.metrics = {
                "tokens": outcome.total_tokens,
                "cost": outcome.cost,
                "model": outcome.model,
            }
            run.status = "completed"
        run.finished_at = utcnow()
        await self._session.commit()
