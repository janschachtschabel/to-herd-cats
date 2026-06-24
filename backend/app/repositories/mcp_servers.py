"""Persistence access for MCPServer (generic CRUD from BaseRepository)."""

from app.models.mcp_server import MCPServer
from app.repositories.base import BaseRepository


class SqlAlchemyMCPServerRepository(BaseRepository[MCPServer]):
    model = MCPServer
