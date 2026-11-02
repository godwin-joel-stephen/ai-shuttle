"""Tools from external MCP servers, made available to the agent.

The agent discovers these at startup instead of having them hard-coded:
each configured server is launched over stdio, its tools are listed, and
each becomes a LangChain tool the graph can call like its own.

The agent runs synchronously, while MCP clients are async, so the
sessions live on a dedicated event loop thread and tool calls are handed
to it. Each server's session is opened and closed inside one long-lived
task, because the stdio transport must exit in the task that entered it.
"""

import asyncio
import json
import logging
import sys
import threading
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parents[2]


def stdio_server(command: str, args: list[str], env: dict[str, str] | None = None) -> StdioServerParameters:
    # "python" means this backend's interpreter, so bundled servers run in
    # the same virtualenv; servers start in the backend directory.
    return StdioServerParameters(
        command=sys.executable if command == "python" else command,
        args=args,
        env=env,
        cwd=_BACKEND_DIR,
    )


class ExternalMCPTools:
    def __init__(
        self,
        servers: dict[str, StdioServerParameters],
        connect_timeout: float = 20,
        call_timeout: float = 10,
    ):
        self.servers = servers
        self.connect_timeout = connect_timeout
        self.call_timeout = call_timeout
        self.tools: list[BaseTool] = []
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="mcp-client", daemon=True)
        self._shutdown: asyncio.Event | None = None
        self._serving: list[asyncio.Future] = []

    def start(self) -> "ExternalMCPTools":
        self._thread.start()
        self._shutdown = asyncio.run_coroutine_threadsafe(self._make_event(), self._loop).result()

        for name, params in self.servers.items():
            ready: asyncio.Future = self._loop.create_future()
            self._serving.append(
                asyncio.run_coroutine_threadsafe(self._serve(name, params, ready), self._loop)
            )
            try:
                tools = asyncio.run_coroutine_threadsafe(
                    self._wait(ready), self._loop
                ).result(timeout=self.connect_timeout)
            except Exception:
                # One unavailable server must not take the agent down.
                logger.warning("MCP server %r unavailable; continuing without it", name, exc_info=True)
                continue

            self.tools.extend(tools)
            logger.info("MCP server %r: %s", name, [t.name for t in tools])

        return self

    def stop(self) -> None:
        if self._shutdown is not None:
            self._loop.call_soon_threadsafe(self._shutdown.set)
        for serving in self._serving:
            try:
                serving.result(timeout=5)
            except Exception:
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)

    @staticmethod
    async def _make_event() -> asyncio.Event:
        return asyncio.Event()

    @staticmethod
    async def _wait(ready: asyncio.Future):
        return await ready

    async def _serve(self, name: str, params: StdioServerParameters, ready: asyncio.Future) -> None:
        try:
            # The real stderr: a server process needs a file descriptor for
            # its logs, which a replaced sys.stderr (e.g. under pytest) lacks.
            async with stdio_client(params, errlog=sys.__stderr__) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    listed = await session.list_tools()
                    ready.set_result([self._wrap(session, tool) for tool in listed.tools])
                    await self._shutdown.wait()
        except Exception as e:
            if not ready.done():
                ready.set_exception(e)
            else:
                logger.warning("MCP server %r disconnected", name, exc_info=True)

    def _wrap(self, session: ClientSession, tool: Any) -> BaseTool:
        def call(**arguments) -> dict:
            result = asyncio.run_coroutine_threadsafe(
                session.call_tool(tool.name, arguments),
                self._loop,
            ).result(timeout=self.call_timeout)

            text = "\n".join(c.text for c in result.content if getattr(c, "text", None))
            if result.is_error:
                return {"error": text or f"{tool.name} failed."}
            try:
                return json.loads(text)
            except ValueError:
                return {"result": text}

        return StructuredTool.from_function(
            func=call,
            name=tool.name,
            description=tool.description or tool.name,
            args_schema=tool.input_schema,
        )
