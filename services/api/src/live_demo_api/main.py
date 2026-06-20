from fastapi import FastAPI

from live_demo_api.health import get_health

app = FastAPI(
    title="Live Demo Agent API",
    description="Skeleton API service for Phase 1. Live demo logic is not implemented yet.",
    version="0.1.0",
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return get_health()


def main() -> None:
    import uvicorn

    uvicorn.run("live_demo_api.main:app", host="127.0.0.1", port=8000)
