"""HTTP routes for managing communication channels (thin: I/O + error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_channel_service
from app.api.security import require_permission
from app.core.permissions import Permission
from app.schemas.channel import ChannelCreate, ChannelRead, ChannelUpdate
from app.services.base import EntityNotFoundError
from app.services.channels import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])


@router.post(
    "",
    response_model=ChannelRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.CHANNEL_CREATE))],
)
async def create_channel(
    payload: ChannelCreate, service: ChannelService = Depends(get_channel_service)
) -> ChannelRead:
    entity = await service.create(payload)
    return ChannelRead.model_validate(entity)


@router.get("", response_model=list[ChannelRead])
async def list_channels(
    service: ChannelService = Depends(get_channel_service),
) -> list[ChannelRead]:
    entities = await service.list()
    return [ChannelRead.model_validate(e) for e in entities]


@router.get("/{channel_id}", response_model=ChannelRead)
async def get_channel(
    channel_id: str, service: ChannelService = Depends(get_channel_service)
) -> ChannelRead:
    try:
        entity = await service.get(channel_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "channel not found") from None
    return ChannelRead.model_validate(entity)


@router.patch(
    "/{channel_id}",
    response_model=ChannelRead,
    dependencies=[Depends(require_permission(Permission.CHANNEL_UPDATE))],
)
async def update_channel(
    channel_id: str,
    payload: ChannelUpdate,
    service: ChannelService = Depends(get_channel_service),
) -> ChannelRead:
    try:
        entity = await service.update(channel_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "channel not found") from None
    return ChannelRead.model_validate(entity)


@router.delete(
    "/{channel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.CHANNEL_DELETE))],
)
async def delete_channel(
    channel_id: str, service: ChannelService = Depends(get_channel_service)
) -> None:
    try:
        await service.delete(channel_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "channel not found") from None
