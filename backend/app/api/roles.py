"""HTTP routes for managing roles (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_role_service
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.base import EntityNotFoundError
from app.services.roles import RoleService

router = APIRouter(prefix="/roles", tags=["auth"])


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate, service: RoleService = Depends(get_role_service)
) -> RoleRead:
    entity = await service.create(payload)
    return RoleRead.model_validate(entity)


@router.get("", response_model=list[RoleRead])
async def list_roles(
    service: RoleService = Depends(get_role_service),
) -> list[RoleRead]:
    entities = await service.list()
    return [RoleRead.model_validate(e) for e in entities]


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(role_id: str, service: RoleService = Depends(get_role_service)) -> RoleRead:
    try:
        entity = await service.get(role_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "role not found") from None
    return RoleRead.model_validate(entity)


@router.patch("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: str,
    payload: RoleUpdate,
    service: RoleService = Depends(get_role_service),
) -> RoleRead:
    try:
        entity = await service.update(role_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "role not found") from None
    return RoleRead.model_validate(entity)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str, service: RoleService = Depends(get_role_service)) -> None:
    try:
        await service.delete(role_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "role not found") from None
