"""HTTP routes for runs: on-demand execution plus read."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_run_service
from app.schemas.run import RunInput, RunRead
from app.services.base import EntityNotFoundError
from app.services.runs import RunConfigError, RunService

router = APIRouter(tags=["runs"])


@router.post(
    "/agents/{agent_id}/runs",
    response_model=RunRead,
    status_code=status.HTTP_201_CREATED,
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
