import os

import pytest
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

from app.agent.mcp_tools import ExternalMCPTools, stdio_server


@pytest.fixture(scope="module")
def clear_path_as_external():
    # Our own MCP server, launched over stdio like any third-party one,
    # pointed at the test database.
    tools = ExternalMCPTools(
        {
            "clear-path": stdio_server(
                "python",
                ["-m", "app.mcp_server"],
                env={**os.environ, "DATABASE_URL": os.environ["DATABASE_URL"]},
            )
        }
    ).start()
    yield tools
    tools.stop()


def test_discovers_and_calls_remote_tools(clear_path_as_external):
    tools = {t.name: t for t in clear_path_as_external.tools}

    assert {"get_today", "search_policies", "book_usual_shuttle"} <= set(tools)
    assert set(tools["get_today"].invoke({})) == {"date", "weekday"}
    assert tools["get_today"].metadata == {"mcp_server": "clear-path"}


def test_remote_schema_drives_arguments(clear_path_as_external):
    tools = {t.name: t for t in clear_path_as_external.tools}

    result = tools["check_booking_eligibility"].invoke({"booking_date": "2030-01-05"})

    assert result["eligible"] is False


def test_unavailable_server_is_skipped():
    tools = ExternalMCPTools(
        {"missing": stdio_server("python", ["-m", "no_such_module"])},
        connect_timeout=10,
    ).start()

    try:
        assert tools.tools == []
    finally:
        tools.stop()
