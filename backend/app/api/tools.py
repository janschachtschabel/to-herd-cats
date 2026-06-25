"""HTTP routes for managing tools (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_tool_service
from app.schemas.tool import ToolCreate, ToolRead, ToolUpdate
from app.services.base import EntityNotFoundError
from app.services.tools import ToolService

router = APIRouter(prefix="/tools", tags=["tools"])


@router.post("", response_model=ToolRead, status_code=status.HTTP_201_CREATED)
async def create_tool(
    payload: ToolCreate, service: ToolService = Depends(get_tool_service)
) -> ToolRead:
    entity = await service.create(payload)
    return ToolRead.model_validate(entity)


@router.get("", response_model=list[ToolRead])
async def list_tools(
    service: ToolService = Depends(get_tool_service),
) -> list[ToolRead]:
    entities = await service.list()
    return [ToolRead.model_validate(e) for e in entities]


@router.get("/{tool_id}", response_model=ToolRead)
async def get_tool(tool_id: str, service: ToolService = Depends(get_tool_service)) -> ToolRead:
    try:
        entity = await service.get(tool_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tool not found") from None
    return ToolRead.model_validate(entity)


@router.patch("/{tool_id}", response_model=ToolRead)
async def update_tool(
    tool_id: str,
    payload: ToolUpdate,
    service: ToolService = Depends(get_tool_service),
) -> ToolRead:
    try:
        entity = await service.update(tool_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tool not found") from None
    return ToolRead.model_validate(entity)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(tool_id: str, service: ToolService = Depends(get_tool_service)) -> None:
    try:
        await service.delete(tool_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "tool not found") from None
