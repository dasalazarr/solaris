"""Cliente MCP mínimo por stdio para el runner de evals (suite `containment`).

Desde M3-T2 vive en el backend (`solaris.mcp_stdio`), porque también lo usa el parser de
reclamaciones; aquí solo se reexporta para no cambiar los imports del runner.
"""

from solaris.mcp_stdio import ERP_MOCK_DIR, McpError, StdioToolSession, ToolResult

__all__ = ["ERP_MOCK_DIR", "McpError", "StdioToolSession", "ToolResult"]
