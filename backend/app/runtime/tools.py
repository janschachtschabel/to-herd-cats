"""Tool resolution and execution for the agent runtime.

An agent references tools by id; the run service resolves those to ResolvedTool
(the tool plus its MCP server). This module turns them into OpenAI tool schemas
for the model and executes a tool call against its server via the MCP gateway.
A tool that fails returns an ``"Error: ..."`` string so it can be fed back to
the model rather than aborting the run.
"""

from dataclasses import dataclass

from app.integrations.mcp_gateway import MCPToolError, call_tool
from app.models.mcp_server import MCPServer
from app.models.tool import Tool


@dataclass
class ResolvedTool:
    tool: Tool
    server: MCPServer | None


def tool_schemas(resolved: list[ResolvedTool]) -> list[dict]:
    """Build OpenAI function-calling schemas from resolved tools."""
    return [
        {
            "type": "function",
            "function": {
                "name": r.tool.name,
                "description": r.tool.description or "",
                "parameters": r.tool.input_schema or {"type": "object"},
            },
        }
        for r in resolved
    ]


async def execute_tool_call(resolved: list[ResolvedTool], call: dict) -> str:
    """Execute one tool call and return its result rendered as text."""
    name = call.get("name")
    arguments = call.get("arguments") or {}
    match = next((r for r in resolved if r.tool.name == name), None)
    if match is None:
        return f"Error: unknown tool {name!r}"
    if match.server is None:
        return f"Error: tool {name!r} has no MCP server configured"
    server_tool_name = match.tool.tool_name or match.tool.name
    try:
        return await call_tool(match.server, server_tool_name, arguments)
    except MCPToolError as exc:
        return f"Error: {exc}"
