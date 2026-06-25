"""HTTP routes for managing triggers (thin: I/O and error mapping)."""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import get_trigger_service
from app.schemas.trigger import (
    TriggerCreate,
    TriggerFireResult,
    TriggerRead,
    TriggerUpdate,
)
from app.services.base import EntityNotFoundError
from app.services.triggers import TriggerService
from app.triggers.autonomous import run_autonomous_guarded
from app.triggers.runner import fire

router = APIRouter(prefix="/triggers", tags=["triggers"])


@router.post("", response_model=TriggerRead, status_code=status.HTTP_201_CREATED)
async def create_trigger(
    payload: TriggerCreate, service: TriggerService = Depends(get_trigger_service)
) -> TriggerRead:
    entity = await service.create(payload)
    return TriggerRead.model_validate(entity)


@router.get("", response_model=list[TriggerRead])
async def list_triggers(
    service: TriggerService = Depends(get_trigger_service),
) -> list[TriggerRead]:
    entities = await service.list()
    return [TriggerRead.model_validate(e) for e in entities]


@router.get("/{trigger_id}", response_model=TriggerRead)
async def get_trigger(
    trigger_id: str, service: TriggerService = Depends(get_trigger_service)
) -> TriggerRead:
    try:
        entity = await service.get(trigger_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "trigger not found") from None
    return TriggerRead.model_validate(entity)


@router.patch("/{trigger_id}", response_model=TriggerRead)
async def update_trigger(
    trigger_id: str,
    payload: TriggerUpdate,
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerRead:
    try:
        entity = await service.update(trigger_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "trigger not found") from None
    return TriggerRead.model_validate(entity)


@router.delete("/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    trigger_id: str, service: TriggerService = Depends(get_trigger_service)
) -> None:
    try:
        await service.delete(trigger_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "trigger not found") from None


@router.post("/{trigger_id}/fire", response_model=TriggerFireResult)
async def fire_trigger(
    trigger_id: str,
    request: Request,
    service: TriggerService = Depends(get_trigger_service),
) -> TriggerFireResult:
    """Run a trigger now: autonomous starts a background loop; others fire once."""
    try:
        trigger = await service.get(trigger_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "trigger not found") from None
    factory = request.app.state.session_factory
    agent_id, loop_config = trigger.agent_id, trigger.loop_config
    if trigger.mode == "autonomous":
        # Detached, dev-grade: tracked on app.state so it is not GC'd mid-flight.
        task = asyncio.create_task(
            run_autonomous_guarded(factory, agent_id, trigger_id, loop_config)
        )
        request.app.state.background_tasks.add(task)
        task.add_done_callback(request.app.state.background_tasks.discard)
        return TriggerFireResult(status="started", mode="autonomous")
    run_id = await fire(factory, agent_id, trigger_id)
    return TriggerFireResult(status="fired", run_id=run_id)
