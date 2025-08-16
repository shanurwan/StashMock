# api/portfolio_service/metrics.py
from __future__ import annotations
import time
from typing import Callable
from fastapi import Request
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "Request latency (s)", ["method", "path"])

def prometheus_middleware() -> Callable:
    async def _mw(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        latency = time.perf_counter() - start
        # Use route path template when possible
        path = request.scope.get("path", request.url.path)
        REQUEST_LATENCY.labels(request.method, path).observe(latency)
        REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
        return response
    return _mw
