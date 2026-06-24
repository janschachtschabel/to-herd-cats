"""Business logic for the MCPServer entity (generic CRUD from CrudService)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mcp_server import MCPServer
from app.repositories.mcp_servers import SqlAlchemyMCPServerRepository
from app.services.base import CrudService


class MCPServerService(CrudService[MCPServer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SqlAlchemyMCPServerRepository(session))
