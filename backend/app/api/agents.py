"""HTTP routes for managing agents (thin: I/O and error mapping only)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_agent_service
from app.schemas.agent import AgentCreate, AgentRead, AgentUpdate
from app.services.agents import AgentService
from app.services.base import EntityNotFoundError

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate, service: AgentService = Depends(get_agent_service)
) -> AgentRead:
    agent = await service.create(payload)
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


@router.patch("/{agent_id}", response_model=AgentRead)
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


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, service: AgentService = Depends(get_agent_service)) -> None:
    try:
        await service.delete(agent_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "agent not found") from None
