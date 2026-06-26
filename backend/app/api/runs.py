"""HTTP routes for runs: on-demand execution plus read."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_run_service
from app.api.security import require_permission
from app.core.permissions import Permission
from app.schemas.run import CompareRequest, CompareResult, RunInput, RunRead
from app.services.base import EntityNotFoundError
from app.services.runs import RunConfigError, RunService

router = APIRouter(tags=["runs"])


@router.post(
    "/agents/{agent_id}/runs",
    response_model=RunRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.RUN_CREATE))],
)
async def create_run(
    agent_id: str,
    payload: RunInput,
    service: RunService = Depends(get_run_service),
) -> RunRead:
    try:
        run = await service.create_and_execute(agent_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from None
    except RunConfigError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    return RunRead.model_validate(run)


@router.get("/runs", response_model=list[RunRead])
async def list_runs(service: RunService = Depends(get_run_service)) -> list[RunRead]:
    runs = await service.list()
    return [RunRead.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=RunRead)
async def get_run(run_id: str, service: RunService = Depends(get_run_service)) -> RunRead:
    try:
        run = await service.get(run_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "run not found") from None
    return RunRead.model_validate(run)


@router.post("/runs/compare", response_model=CompareResult)
async def compare_runs(
    payload: CompareRequest, service: RunService = Depends(get_run_service)
) -> CompareResult:
    """Structured diff of two runs' results, optionally rendered via a template."""
    try:
        result = await service.compare(
            payload.run_a_id, payload.run_b_id, payload.fields, payload.template_id
        )
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "run not found") from None
    return CompareResult(**result)
