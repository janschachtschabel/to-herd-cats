"""Shared FastAPI dependencies."""

from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents import AgentService
from app.services.channels import ChannelService
from app.services.data_sources import DataSourceService
from app.services.llm_connections import LLMConnectionService
from app.services.mcp_servers import MCPServerService
from app.services.roles import RoleService
from app.services.settings import SettingService
from app.services.skills import SkillService
from app.services.templates import TemplateService
from app.services.tools import ToolService
from app.services.triggers import TriggerService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield an async DB session bound to the app's session factory.

    The factory lives on ``app.state`` (set in the lifespan, or by tests), so
    requests never reach for a module-level global.
    """
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_agent_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    """Build the agent service for a request, bound to its session."""
    return AgentService(session)


def get_llm_connection_service(
    session: AsyncSession = Depends(get_session),
) -> LLMConnectionService:
    """Build the LLM-connection service for a request, bound to its session."""
    return LLMConnectionService(session)


def get_skill_service(session: AsyncSession = Depends(get_session)) -> SkillService:
    """Build the skill service for a request, bound to its session."""
    return SkillService(session)


def get_mcp_server_service(
    session: AsyncSession = Depends(get_session),
) -> MCPServerService:
    """Build the MCP-server service for a request, bound to its session."""
    return MCPServerService(session)


def get_tool_service(session: AsyncSession = Depends(get_session)) -> ToolService:
    """Build the tool service for a request, bound to its session."""
    return ToolService(session)


def get_data_source_service(
    session: AsyncSession = Depends(get_session),
) -> DataSourceService:
    """Build the data-source service for a request, bound to its session."""
    return DataSourceService(session)


def get_template_service(
    session: AsyncSession = Depends(get_session),
) -> TemplateService:
    """Build the template service for a request, bound to its session."""
    return TemplateService(session)


def get_channel_service(session: AsyncSession = Depends(get_session)) -> ChannelService:
    """Build the channel service for a request, bound to its session."""
    return ChannelService(session)


def get_trigger_service(session: AsyncSession = Depends(get_session)) -> TriggerService:
    """Build the trigger service for a request, bound to its session."""
    return TriggerService(session)


def get_role_service(session: AsyncSession = Depends(get_session)) -> RoleService:
    """Build the role service for a request, bound to its session."""
    return RoleService(session)


def get_setting_service(session: AsyncSession = Depends(get_session)) -> SettingService:
    """Build the setting service for a request, bound to its session."""
    return SettingService(session)
