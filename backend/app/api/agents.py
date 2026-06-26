"""HTTP routes for managing agents (thin: I/O and error mapping only)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_agent_service
from app.api.security import Principal, get_principal, require_permission
from app.core.permissions import Permission
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.services.agents import AgentService
from app.services.base import EntityNotFoundError

router = APIRouter(prefix="/agents", tags=["agents"])


def require_agent_access(permission: str):
    """Authorize an agent mutation: allowed if the principal holds ``permission``
    or owns the agent (``created_by`` == subject). 404 if the agent is gone."""

    async def guard(
        agent_id: str,
        principal: Principal = Depends(get_principal),
        service: AgentService = Depends(get_agent_service),
    ) -> Principal:
        try:
            agent = await service.get(agent_id)
        except EntityNotFoundError:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from None
        if not (principal.has(permission) or agent.created_by == principal.subject):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"missing permission: {permission}")
        return principal

    return guard


@router.post(
    "",
    response_model=AgentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.AGENT_CREATE))],
)
async def create_agent(
    payload: AgentCreate,
    principal: Principal = Depends(get_principal),
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    agent = await service.create(payload, created_by=principal.subject)
    return AgentRead.model_validate(agent)


@router.get("", response_model=list[AgentRead])
async def list_agents(
    service: AgentService = Depends(get_agent_service),
) -> list[AgentRead]:
    agents = await service.list()
    return [AgentRead.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str, service: AgentService = Depends(get_agent_service)) -> AgentRead:
    try:
        agent = await service.get(agent_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from None
    return AgentRead.model_validate(agent)


@router.patch(
    "/{agent_id}",
    response_model=AgentRead,
    dependencies=[Depends(require_agent_access(Permission.AGENT_UPDATE))],
)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    service: AgentService = Depends(get_agent_service),
) -> AgentRead:
    try:
        agent = await service.update(agent_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from None
    return AgentRead.model_validate(agent)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_agent_access(Permission.AGENT_DELETE))],
)
async def delete_agent(agent_id: str, service: AgentService = Depends(get_agent_service)) -> None:
    try:
        await service.delete(agent_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from None
