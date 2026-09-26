"""Cliente MCP mínimo por stdio hacia el erp-mock (M2-T7 en evals → backend en M3-T2).

El backend no depende del SDK `mcp`: este cliente habla JSON-RPC 2.0 delimitado por líneas
(transporte stdio de MCP) con el servidor erp-mock y cumple el protocolo `ToolSession` de
`solaris.mcp_obo`:

    async with StdioToolSession.erp_mock() as session:
        res = await call_erp_tool(session, principal, "get_lot", {"lot_code": ...})

La identidad (`_meta`) la construye SIEMPRE `mcp_obo` desde el Principal autenticado; este módulo
solo transporta. Lanza únicamente el proceso local del repo (`app/mcp/erp_mock`, argv fijo, sin
shell ni red). Lo usan el parser de reclamaciones (M3-T2), el orquestador 8D (M3-T3) y el runner
de evals (`app/evals/mcp_stdio.py` lo reexporta).
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path
from typing import Any

from solaris.settings import REPO_ROOT

ERP_MOCK_DIR = REPO_ROOT / "app" / "mcp" / "erp_mock"
PROTOCOL_VERSION = "2025-06-18"
MAX_LINE = 16 * 1024 * 1024


# Entorno del proceso hijo (M3-T2): solo lo necesario para `uv` y la configuración propia del
# erp-mock (que además lee el .env de la raíz). Sin VIRTUAL_ENV (el MCP corre en su propio entorno
# uv) y sin los secretos del backend (OPENROUTER_API_KEY, AUTH_JWT_SECRET, DEMO_PASSWORD_*...).
_ENV_KEYS = frozenset({"PATH", "HOME", "LANG", "TMPDIR", "TZ", "SOLARIS_DB_PORT",
                       "AUDIT_WRITER_PASSWORD", "AUDIT_DB_NAME"})
_ENV_PREFIXES = ("LC_", "UV_", "ERP_")


def child_env(environ: dict[str, str] | os._Environ[str]) -> dict[str, str]:
    return {k: v for k, v in environ.items()
            if k in _ENV_KEYS or k.startswith(_ENV_PREFIXES)}


class McpError(RuntimeError):
    pass


class ToolResult(dict):
    """Resultado de tools/call: `isError`, `content`, `structuredContent`."""

    @property
    def is_error(self) -> bool:
        return bool(self.get("isError"))

    @property
    def data(self) -> Any:
        sc = self.get("structuredContent")
        if sc is not None:
            return sc
        for c in self.get("content") or []:
            if c.get("type") == "text":
                try:
                    return json.loads(c["text"])
                except (ValueError, KeyError):
                    return c.get("text")
        return None

    @property
    def text(self) -> str:
        return " ".join(c.get("text", "") for c in self.get("content") or [])


class StdioToolSession:
    def __init__(self, argv: list[str], cwd: Path, timeout_s: float = 60.0,
                 client_name: str = "solaris-backend"):
        self._argv, self._cwd, self._timeout = argv, cwd, timeout_s
        self._client_name = client_name
        self._proc: asyncio.subprocess.Process | None = None
        self._next_id = 0

    @classmethod
    def erp_mock(cls, timeout_s: float = 60.0,
                 client_name: str = "solaris-backend") -> StdioToolSession:
        uv = shutil.which("uv")
        if uv is None:
            raise McpError("No se encuentra `uv` para lanzar el MCP erp-mock")
        return cls([uv, "run", "--quiet", "--project", str(ERP_MOCK_DIR), "solaris-erp-mock"],
                   ERP_MOCK_DIR, timeout_s, client_name)

    async def __aenter__(self) -> StdioToolSession:
        env = child_env(os.environ)
        self._proc = await asyncio.create_subprocess_exec(
            *self._argv, cwd=self._cwd, env=env, limit=MAX_LINE,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
            "clientInfo": {"name": self._client_name, "version": "0.1"},
        })
        await self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    async def __aexit__(self, *exc: object) -> None:
        p = self._proc
        if p is None:
            return
        if p.stdin:
            p.stdin.close()
        try:
            await asyncio.wait_for(p.wait(), 5)
        except TimeoutError:
            p.kill()
            await p.wait()

    async def _send(self, msg: dict[str, Any]) -> None:
        if not (self._proc and self._proc.stdin):
            raise McpError("Sesión MCP no iniciada")
        self._proc.stdin.write((json.dumps(msg) + "\n").encode())
        await self._proc.stdin.drain()

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if not (self._proc and self._proc.stdout):
            raise McpError("Sesión MCP no iniciada")
        self._next_id += 1
        rid = self._next_id
        await self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while True:
            line = await asyncio.wait_for(self._proc.stdout.readline(), self._timeout)
            if not line:
                raise McpError(f"El servidor MCP se cerró durante {method}")
            msg = json.loads(line)
            if msg.get("id") != rid:  # notificaciones (logs, progreso): se ignoran
                continue
            if "error" in msg:
                raise McpError(f"{method}: {msg['error']}")
            return msg.get("result") or {}

    async def list_tools(self) -> list[str]:
        return [t["name"] for t in (await self._request("tools/list", {})).get("tools", [])]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None, *,
                        meta: dict[str, Any] | None = None) -> ToolResult:
        params: dict[str, Any] = {"name": name, "arguments": arguments or {}}
        if meta is not None:
            params["_meta"] = meta
        return ToolResult(await self._request("tools/call", params))
