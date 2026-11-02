"""A standalone weather MCP server (Open-Meteo, no API key).

Deliberately independent of the Clear Path app: it imports nothing from
`app`, so it stands in for any third-party MCP server the agent can be
pointed at through configuration.

    python -m mcp_servers.weather    # stdio
"""

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes, grouped.
_CONDITIONS = [
    ({0}, "clear"),
    ({1, 2}, "partly cloudy"),
    ({3}, "overcast"),
    ({45, 48}, "foggy"),
    ({51, 53, 55, 56, 57}, "drizzle"),
    ({61, 63, 65, 66, 67, 80, 81, 82}, "rain"),
    ({71, 73, 75, 77, 85, 86}, "snow"),
    ({95, 96, 99}, "thunderstorm"),
]

server = MCPServer(
    name="weather",
    title="Weather",
    instructions="Current conditions and near-term rain chances for a location.",
)


def describe(code: int) -> str:
    return next((label for codes, label in _CONDITIONS if code in codes), "unknown")


@server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=True))
def get_current_weather(latitude: float, longitude: float) -> dict:
    """Current weather at a location: conditions, temperature, rain now, and
    the chance of rain over the next two hours."""

    response = httpx.get(
        OPEN_METEO_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,weather_code,wind_speed_10m",
            "hourly": "precipitation_probability",
            "forecast_hours": 2,
            "timezone": "auto",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    current = data["current"]

    return {
        "conditions": describe(current["weather_code"]),
        "temperature_c": current["temperature_2m"],
        "precipitation_mm": current["precipitation"],
        "wind_kmh": current["wind_speed_10m"],
        "rain_chance_next_2h_percent": max(data["hourly"]["precipitation_probability"], default=0),
    }


if __name__ == "__main__":
    server.run()
