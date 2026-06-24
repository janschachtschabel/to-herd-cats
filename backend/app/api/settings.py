"""HTTP routes for the scoped key/value Setting store (upsert via PUT)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_setting_service
from app.schemas.setting import SettingRead, SettingScope, SettingWrite
from app.services.base import EntityNotFoundError
from app.services.settings import SettingService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=list[SettingRead])
async def list_settings(
    scope: SettingScope | None = None,
    service: SettingService = Depends(get_setting_service),
) -> list[SettingRead]:
    settings = await service.list(scope.value if scope else None)
    return [SettingRead.model_validate(s) for s in settings]


@router.get("/{scope}/{key}", response_model=SettingRead)
async def get_setting(
    scope: SettingScope,
    key: str,
    service: SettingService = Depends(get_setting_service),
) -> SettingRead:
    try:
        setting = await service.get(scope.value, key)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "setting not found") from None
    return SettingRead.model_validate(setting)


@router.put("/{scope}/{key}", response_model=SettingRead)
async def put_setting(
    scope: SettingScope,
    key: str,
    payload: SettingWrite,
    service: SettingService = Depends(get_setting_service),
) -> SettingRead:
    setting = await service.upsert(scope.value, key, payload.value)
    return SettingRead.model_validate(setting)


@router.delete("/{scope}/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    scope: SettingScope,
    key: str,
    service: SettingService = Depends(get_setting_service),
) -> None:
    try:
        await service.delete(scope.value, key)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "setting not found") from None
