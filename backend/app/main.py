from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.assistant import router as assistant_router
from app.api.bookings import router as bookings_router
from app.api.tracking import router as tracking_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the embedding model and open the memory pool before the first
    # request, instead of making the first user wait ~20s for them.
    from app.agent.mcp_tools import ExternalMCPTools, stdio_server
    from app.agent.memory import get_checkpointer
    from app.core.config import settings
    from app.rag.embeddings import get_embedder

    get_embedder()
    get_checkpointer()

    external = ExternalMCPTools(
        {
            name: stdio_server(server["command"], server.get("args", []), server.get("env"))
            for name, server in settings.mcp_servers.items()
        }
    ).start()
    app.state.external_tools = external.tools

    yield

    external.stop()


app = FastAPI(
    title="AI Shuttle API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(assistant_router)
app.include_router(bookings_router)
app.include_router(tracking_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
