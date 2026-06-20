"""Metrics hooks prepared for later instrumentation."""


class ApiMetrics:
    def record_request(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        _ = (method, path, status_code, duration_ms)


metrics = ApiMetrics()
