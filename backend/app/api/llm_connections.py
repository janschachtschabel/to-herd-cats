"""HTTP routes for managing LLM connections (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_llm_connection_service
from app.schemas.llm_connection import (
    LLMConnectionCreate,
    LLMConnectionRead,
    LLMConnectionUpdate,
)
from app.services.base import EntityNotFoundError
from app.services.llm_connections import LLMConnectionService

router = APIRouter(prefix="/llm-connections", tags=["llm"])


@router.post("", response_model=LLMConnectionRead, status_code=status.HTTP_201_CREATED)
async def create_llm_connection(
    payload: LLMConnectionCreate,
    service: LLMConnectionService = Depends(get_llm_connection_service),
) -> LLMConnectionRead:
    entity = await service.create(payload)
    return LLMConnectionRead.model_validate(entity)


@router.get("", response_model=list[LLMConnectionRead])
async def list_llm_connections(
    service: LLMConnectionService = Depends(get_llm_connection_service),
) -> list[LLMConnectionRead]:
    entities = await service.list()
    return [LLMConnectionRead.model_validate(e) for e in entities]


@router.get("/{connection_id}", response_model=LLMConnectionRead)
async def get_llm_connection(
    connection_id: str,
    service: LLMConnectionService = Depends(get_llm_connection_service),
) -> LLMConnectionRead:
    try:
        entity = await service.get(connection_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "llm connection not found") from None
    return LLMConnectionRead.model_validate(entity)


@router.patch("/{connection_id}", response_model=LLMConnectionRead)
async def update_llm_connection(
    connection_id: str,
    payload: LLMConnectionUpdate,
    service: LLMConnectionService = Depends(get_llm_connection_service),
) -> LLMConnectionRead:
    try:
        entity = await service.update(connection_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "llm connection not found") from None
    return LLMConnectionRead.model_validate(entity)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_connection(
    connection_id: str,
    service: LLMConnectionService = Depends(get_llm_connection_service),
) -> None:
    try:
        await service.delete(connection_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "llm connection not found") from None
