from fastapi import FastAPI

from live_demo_tts_service.health import get_health

app = FastAPI(
    title="Live Demo Agent TTS Service",
    description="Optional local TTS skeleton. Speech synthesis is not implemented in Phase 1.",
    version="0.1.0",
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return get_health()


def main() -> None:
    import uvicorn

    uvicorn.run("live_demo_tts_service.main:app", host="127.0.0.1", port=8100)
