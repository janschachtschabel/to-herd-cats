"""HTTP route exposing the current principal (so the frontend can gate on it)."""

from fastapi import APIRouter, Depends

from app.api.security import Principal, get_principal
from app.schemas.auth import PrincipalRead

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=PrincipalRead)
async def read_me(principal: Principal = Depends(get_principal)) -> PrincipalRead:
    """Return the calling principal's subject and permissions."""
    return PrincipalRead(subject=principal.subject, permissions=sorted(principal.permissions))
