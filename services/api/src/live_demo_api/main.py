from live_demo_api.app import create_app

app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run("live_demo_api.main:app", host="127.0.0.1", port=8000)
