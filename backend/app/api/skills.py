"""HTTP routes for managing skills (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_skill_service
from app.schemas.skill import SkillCreate, SkillRead, SkillUpdate
from app.services.base import EntityNotFoundError
from app.services.skills import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate, service: SkillService = Depends(get_skill_service)
) -> SkillRead:
    entity = await service.create(payload)
    return SkillRead.model_validate(entity)


@router.get("", response_model=list[SkillRead])
async def list_skills(
    service: SkillService = Depends(get_skill_service),
) -> list[SkillRead]:
    entities = await service.list()
    return [SkillRead.model_validate(e) for e in entities]


@router.get("/{skill_id}", response_model=SkillRead)
async def get_skill(
    skill_id: str, service: SkillService = Depends(get_skill_service)
) -> SkillRead:
    try:
        entity = await service.get(skill_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "skill not found") from None
    return SkillRead.model_validate(entity)


@router.patch("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: str,
    payload: SkillUpdate,
    service: SkillService = Depends(get_skill_service),
) -> SkillRead:
    try:
        entity = await service.update(skill_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "skill not found") from None
    return SkillRead.model_validate(entity)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str, service: SkillService = Depends(get_skill_service)
) -> None:
    try:
        await service.delete(skill_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "skill not found") from None
