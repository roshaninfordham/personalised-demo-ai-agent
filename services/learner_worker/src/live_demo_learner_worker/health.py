def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "learner-worker"}
