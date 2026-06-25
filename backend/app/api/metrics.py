"""HTTP route for observability metrics."""

from fastapi import APIRouter, Depends

from app.api.deps import get_metrics_service
from app.schemas.metrics import MetricsSummary
from app.services.metrics import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary", response_model=MetricsSummary)
async def metrics_summary(
    service: MetricsService = Depends(get_metrics_service),
) -> MetricsSummary:
    """Aggregate cost and token usage across all runs."""
    return MetricsSummary(**await service.summary())
