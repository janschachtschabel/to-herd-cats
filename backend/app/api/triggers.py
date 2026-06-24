"""HTTP routes for managing triggers (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_trigger_service
from app.schemas.trigger import TriggerCreate, TriggerRead, TriggerUpdate
from app.services.base import EntityNotFoundError
from app.services.triggers import TriggerService

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
