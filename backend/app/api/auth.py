"""Auth-facing reads: the current principal, and the permission catalog."""

from fastapi import APIRouter, Depends

from app.api.security import Principal, get_principal
from app.core.permissions import ALL_PERMISSIONS
from app.schemas.auth import PermissionOption, PrincipalRead

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=PrincipalRead)
async def read_me(principal: Principal = Depends(get_principal)) -> PrincipalRead:
    """Return the calling principal's subject and permissions."""
    return PrincipalRead(subject=principal.subject, permissions=sorted(principal.permissions))


@router.get("/permissions", response_model=list[PermissionOption])
async def list_permissions() -> list[PermissionOption]:
    """The full permission catalog, for the role editor's multi-select."""
    return [PermissionOption(id=permission, name=permission) for permission in ALL_PERMISSIONS]
