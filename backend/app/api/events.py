"""HTTP route for publishing events that fire event-mode triggers."""

from fastapi import APIRouter, Request

from app.schemas.event import EventDispatchResult, EventIn
from app.triggers.events import dispatch

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventDispatchResult)
async def publish_event(payload: EventIn, request: Request) -> EventDispatchResult:
    """Publish an event; fire every enabled event-trigger that matches it."""
    factory = request.app.state.session_factory
    run_ids = await dispatch(factory, payload.source, payload.payload)
    return EventDispatchResult(fired=len(run_ids), run_ids=run_ids)
