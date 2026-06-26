"""HTTP route for publishing events that fire event-mode triggers."""

from fastapi import APIRouter, Depends, Request

from app.api.security import require_permission
from app.core.permissions import Permission
from app.schemas.event import EventDispatchResult, EventIn
from app.triggers.events import dispatch

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventDispatchResult,
    dependencies=[Depends(require_permission(Permission.EVENT_PUBLISH))],
)
async def publish_event(payload: EventIn, request: Request) -> EventDispatchResult:
    """Publish an event; fire every enabled event-trigger that matches it."""
    factory = request.app.state.session_factory
    run_ids = await dispatch(factory, payload.source, payload.payload)
    return EventDispatchResult(fired=len(run_ids), run_ids=run_ids)
