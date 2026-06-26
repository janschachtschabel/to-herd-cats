"""HTTP routes for managing MCP servers (thin: I/O and error mapping)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_mcp_server_service
from app.api.security import require_permission
from app.core.permissions import Permission
from app.integrations.mcp_gateway import MCPDiscoveryError
from app.schemas.mcp_server import MCPServerCreate, MCPServerRead, MCPServerUpdate
from app.services.base import EntityNotFoundError
from app.services.mcp_servers import MCPServerService

router = APIRouter(prefix="/mcp-servers", tags=["mcp"])


@router.post(
    "",
    response_model=MCPServerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.MCP_SERVER_CREATE))],
)
async def create_mcp_server(
    payload: MCPServerCreate,
    service: MCPServerService = Depends(get_mcp_server_service),
) -> MCPServerRead:
    entity = await service.create(payload)
    return MCPServerRead.model_validate(entity)


@router.get("", response_model=list[MCPServerRead])
async def list_mcp_servers(
    service: MCPServerService = Depends(get_mcp_server_service),
) -> list[MCPServerRead]:
    entities = await service.list()
    return [MCPServerRead.model_validate(e) for e in entities]


@router.get("/{server_id}", response_model=MCPServerRead)
async def get_mcp_server(
    server_id: str, service: MCPServerService = Depends(get_mcp_server_service)
) -> MCPServerRead:
    try:
        entity = await service.get(server_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mcp server not found") from None
    return MCPServerRead.model_validate(entity)


@router.patch(
    "/{server_id}",
    response_model=MCPServerRead,
    dependencies=[Depends(require_permission(Permission.MCP_SERVER_UPDATE))],
)
async def update_mcp_server(
    server_id: str,
    payload: MCPServerUpdate,
    service: MCPServerService = Depends(get_mcp_server_service),
) -> MCPServerRead:
    try:
        entity = await service.update(server_id, payload)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mcp server not found") from None
    return MCPServerRead.model_validate(entity)


@router.delete(
    "/{server_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission(Permission.MCP_SERVER_DELETE))],
)
async def delete_mcp_server(
    server_id: str, service: MCPServerService = Depends(get_mcp_server_service)
) -> None:
    try:
        await service.delete(server_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mcp server not found") from None


@router.post(
    "/{server_id}/discover",
    response_model=MCPServerRead,
    dependencies=[Depends(require_permission(Permission.MCP_SERVER_DISCOVER))],
)
async def discover_mcp_server(
    server_id: str, service: MCPServerService = Depends(get_mcp_server_service)
) -> MCPServerRead:
    """Connect to the server, cache its tools, and update its status."""
    try:
        server = await service.discover(server_id)
    except EntityNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "mcp server not found") from None
    except MCPDiscoveryError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from None
    return MCPServerRead.model_validate(server)
