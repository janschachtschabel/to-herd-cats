"""HTTP routes for managing data sources (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_data_source_service
from app.api.security import require_permission
from app.core.permissions import Permission
from app.schemas.data_source import (
    DataSourceCreate,
    DataSourceRead,
    DataSourceUpdate,
)
from app.services.base import EntityNotFoundError
from app.services.data_sources import DataSourceService

router = APIRouter(prefix="/data-sources", tags=["data"])


@router.post(
    "",
    response_model=DataSourceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.DATA_SOURCE_CREATE))],
)
async def create_data_source(
    payload: DataSourceCreate,
    service: DataSourceService = Depends(get_data_source_service),
) -> DataSourceRead:
    entity = await service.create(payload)
    return DataSourceRead.model_validate(entity)


@router.get("", response_model=list[DataSourceRead])
async def list_data_sources(
    service: DataSourceService = Depends(get_data_source_service),
) -> list[DataSourceRead]:
    entities = await service.list()
    return [DataSourceRead.model_validate(e) for e in entities]


@router.get("/{source_id}", response_model=DataSourceRead)
async def get_data_source(
    source_id: str, service: DataSourceService = Depends(get_data_source_service)
) -> DataSourceRead:
    try:
        entity = await service.get(source_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "data source not found") from None
    return DataSourceRead.model_validate(entity)


@router.patch(
    "/{source_id}",
    response_model=DataSourceRead,
    dependencies=[Depends(require_permission(Permission.DATA_SOURCE_UPDATE))],
)
async def update_data_source(
    source_id: str,
    payload: DataSourceUpdate,
    service: DataSourceService = Depends(get_data_source_service),
) -> DataSourceRead:
    try:
        entity = await service.update(source_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "data source not found") from None
    return DataSourceRead.model_validate(entity)


@router.delete(
    "/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.DATA_SOURCE_DELETE))],
)
async def delete_data_source(
    source_id: str, service: DataSourceService = Depends(get_data_source_service)
) -> None:
    try:
        await service.delete(source_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "data source not found") from None
