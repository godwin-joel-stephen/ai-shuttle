"""Clear Path as an MCP server.

Exposes the same tools the in-app agent uses (bookings, shuttle options,
live status, booking rules and policy search) over the Model Context
Protocol, so any MCP client, such as Claude Desktop or Claude Code, can use
Clear Path's capabilities. Every call goes through the same services and
booking rules as the app; nothing here talks to the database directly.

    python -m app.mcp_server                # stdio, for desktop clients
    python -m app.mcp_server --http 8001    # Streamable HTTP at /mcp
"""

import argparse
import inspect
import os
from collections.abc import Callable

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from sqlalchemy.orm import Session

from app.core import clock
from app.db.database import SessionLocal
from app.rag.embeddings import Embedder, get_embedder
from app.repositories.user_repository import UserRepository
from app.tools.assistant_tools import MUTATING_TOOLS, create_assistant_tools


# Single-user demo: the MCP client acts for this rider.
DEFAULT_USER_ID = int(os.environ.get("CLEAR_PATH_USER_ID", "1"))

_DESTRUCTIVE_TOOLS = {"cancel_booking"}


def _annotations(name: str) -> ToolAnnotations:
    """Hints clients use to decide when to ask the user before a call."""

    return ToolAnnotations(
        read_only_hint=name not in MUTATING_TOOLS,
        destructive_hint=name in _DESTRUCTIVE_TOOLS,
        # Booking twice returns the existing booking.
        idempotent_hint=name not in _DESTRUCTIVE_TOOLS,
        open_world_hint=False,
    )


def create_mcp_server(
    session_factory: Callable[[], Session] = SessionLocal,
    embedder_factory: Callable[[], Embedder] = get_embedder,
    user_id: int = DEFAULT_USER_ID,
) -> MCPServer:
    with session_factory() as db:
        user = UserRepository(db).get_by_id(user_id)
        rider = user.name if user else "the rider"
        # Built once only to read each tool's name, description and
        # signature; calls get fresh tools bound to a fresh session.
        templates = create_assistant_tools(db, user_id, embedder_factory())

    server = MCPServer(
        name="clear-path",
        title="Clear Path",
        instructions=(
            f"Clear Path books and tracks commuter shuttles for {rider}. "
            "Call get_today before resolving relative dates; tools take dates "
            "as YYYY-MM-DD. Use the tools for every fact about bookings, "
            "shuttles and policies, and confirm before cancelling."
        ),
    )

    def get_today() -> dict:
        """Today's date and weekday, for resolving "tomorrow" or "Friday"."""

        today = clock.today()
        return {"date": today.isoformat(), "weekday": f"{today:%A}"}

    server.add_tool(get_today, annotations=_annotations("get_today"))

    for template in templates:
        server.add_tool(
            _bind(template.name, template.func, session_factory, embedder_factory, user_id),
            name=template.name,
            description=template.description,
            annotations=_annotations(template.name),
        )

    return server


def _bind(
    name: str,
    signature_source: Callable,
    session_factory: Callable[[], Session],
    embedder_factory: Callable[[], Embedder],
    user_id: int,
) -> Callable:
    def call(**arguments):
        with session_factory() as db:
            tools = create_assistant_tools(db, user_id, embedder_factory())
            tool = next(t for t in tools if t.name == name)
            return tool.invoke(arguments)

    # MCPServer builds the tool's input schema from the signature.
    call.__name__ = name
    call.__signature__ = inspect.signature(signature_source)
    return call


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--http", type=int, metavar="PORT", help="serve Streamable HTTP on this port")
    args = parser.parse_args()

    server = create_mcp_server()

    if args.http:
        server.run(transport="streamable-http", port=args.http)
    else:
        server.run()


if __name__ == "__main__":
    main()
