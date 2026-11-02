from fastapi import FastAPI

from app.api.assistant import router as assistant_router
from app.api.bookings import router as bookings_router


app = FastAPI(
    title="AI Shuttle API",
    version="0.1.0",
)


app.include_router(assistant_router)
app.include_router(bookings_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
