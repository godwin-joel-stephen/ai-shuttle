from fastapi import FastAPI

from app.api.bookings import router as bookings_router


app = FastAPI(
    title="AI Shuttle API",
    version="0.1.0",
)


app.include_router(bookings_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
