"""Export FastAPI OpenAPI schema for client-generation workflows."""

from __future__ import annotations

import json

from live_demo_api.app import create_app


def main() -> None:
    app = create_app()
    print(json.dumps(app.openapi(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
