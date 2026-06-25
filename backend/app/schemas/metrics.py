"""Pydantic schema for the observability metrics summary."""

from pydantic import BaseModel


class MetricsSummary(BaseModel):
    total_runs: int
    by_status: dict[str, int]
    total_tokens: int
    total_cost: float
