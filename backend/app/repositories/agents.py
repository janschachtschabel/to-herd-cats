"""Persistence access for Agent (generic CRUD from BaseRepository)."""

from app.models.agent import Agent
from app.repositories.base import BaseRepository


class SqlAlchemyAgentRepository(BaseRepository[Agent]):
    model = Agent
