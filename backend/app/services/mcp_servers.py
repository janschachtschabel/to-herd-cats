"""Business logic for the MCPServer entity (generic CRUD + tool discovery)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.mcp_gateway import MCPDiscoveryError, discover_tools
from app.models.mcp_server import MCPServer
from app.repositories.mcp_servers import SqlAlchemyMCPServerRepository
from app.services.base import CrudService


class MCPServerService(CrudService[MCPServer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyMCPServerRepository(session))

    async def discover(self, server_id: str) -> MCPServer:
        """Discover the server's tools, cache them, and update its status.

        On a connection/protocol failure the status is persisted as ``error``
        and MCPDiscoveryError is re-raised for the router to map to a 502.
        """
        server = await self.get(server_id)
        try:
            tools = await discover_tools(server)
        except MCPDiscoveryError:
            server.status = "error"
            await self._session.commit()
            raise
        server.discovered_tools = tools
        server.status = "connected"
        await self._session.commit()
        await self._session.refresh(server)
        return server
