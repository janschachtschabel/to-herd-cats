"""HTTP routes for managing output templates (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_template_service
from app.api.security import require_permission
from app.core.permissions import Permission
from app.schemas.template import TemplateCreate, TemplateRead, TemplateUpdate
from app.services.base import EntityNotFoundError
from app.services.templates import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post(
    "",
    response_model=TemplateRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.TEMPLATE_CREATE))],
)
async def create_template(
    payload: TemplateCreate, service: TemplateService = Depends(get_template_service)
) -> TemplateRead:
    entity = await service.create(payload)
    return TemplateRead.model_validate(entity)


@router.get("", response_model=list[TemplateRead])
async def list_templates(
    service: TemplateService = Depends(get_template_service),
) -> list[TemplateRead]:
    entities = await service.list()
    return [TemplateRead.model_validate(e) for e in entities]


@router.get("/{template_id}", response_model=TemplateRead)
async def get_template(
    template_id: str, service: TemplateService = Depends(get_template_service)
) -> TemplateRead:
    try:
        entity = await service.get(template_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "template not found") from None
    return TemplateRead.model_validate(entity)


@router.patch(
    "/{template_id}",
    response_model=TemplateRead,
    dependencies=[Depends(require_permission(Permission.TEMPLATE_UPDATE))],
)
async def update_template(
    template_id: str,
    payload: TemplateUpdate,
    service: TemplateService = Depends(get_template_service),
) -> TemplateRead:
    try:
        entity = await service.update(template_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "template not found") from None
    return TemplateRead.model_validate(entity)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.TEMPLATE_DELETE))],
)
async def delete_template(
    template_id: str, service: TemplateService = Depends(get_template_service)
) -> None:
    try:
        await service.delete(template_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "template not found") from None
