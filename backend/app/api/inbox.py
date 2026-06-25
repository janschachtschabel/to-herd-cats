"""HTTP routes for the postbox: read items and respond (resume the run)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_inbox_service, get_run_service
from app.schemas.inbox_item import InboxItemRead, InboxResponse
from app.schemas.run import RunRead
from app.services.base import EntityNotFoundError
from app.services.inbox import InboxService
from app.services.runs import InboxStateError, RunConfigError, RunService

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("", response_model=list[InboxItemRead])
async def list_inbox(
    service: InboxService = Depends(get_inbox_service),
) -> list[InboxItemRead]:
    items = await service.list()
    return [InboxItemRead.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=InboxItemRead)
async def get_inbox_item(
    item_id: str, service: InboxService = Depends(get_inbox_service)
) -> InboxItemRead:
    try:
        item = await service.get(item_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "inbox item not found") from None
    return InboxItemRead.model_validate(item)


@router.post("/{item_id}/respond", response_model=RunRead)
async def respond_to_inbox(
    item_id: str,
    payload: InboxResponse,
    service: RunService = Depends(get_run_service),
) -> RunRead:
    """Reply to a pending item; the response resumes its run."""
    try:
        run = await service.respond_to_inbox(item_id, payload.model_dump(mode="json"))
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "inbox item not found") from None
    except InboxStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None
    except RunConfigError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from None
    return RunRead.model_validate(run)
