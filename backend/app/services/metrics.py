"""Observability: aggregate run metrics (tokens / cost) for visibility.

Read-only and separate from RunService (execution): it summarizes what runs
have already recorded in ``Run.metrics``. Aggregation runs in Python rather than
SQL over the JSON column, so it stays portable across SQLite and PostgreSQL; at
this stage the run count is small. A tracing backend (Langfuse / OTel) is a
deliberate follow-up.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.runs import SqlAlchemyRunRepository


class MetricsService:
    def __init__(self, session: AsyncSession) -> None:
        self._runs = SqlAlchemyRunRepository(session)

    async def summary(self) -> dict:
        """Totals across all runs: count, status breakdown, tokens and cost."""
        runs = await self._runs.list()
        by_status: dict[str, int] = {}
        total_tokens = 0
        total_cost = 0.0
        for run in runs:
            by_status[run.status] = by_status.get(run.status, 0) + 1
            metrics = run.metrics or {}
            total_tokens += metrics.get("tokens") or 0
            total_cost += metrics.get("cost") or 0.0
        return {
            "total_runs": len(runs),
            "by_status": by_status,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 6),
        }
