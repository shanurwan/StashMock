# api/portfolio_service/metrics.py
from __future__ import annotations
import json
import time
import logging
from typing import Callable
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge

# ---------- Prometheus ----------
REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "route", "status"]
)

REQUEST_EXCEPTIONS_TOTAL = Counter(
    "http_request_exceptions_total",
    "Unhandled exceptions during request processing",
    ["method", "route", "exc_type"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "route"],
    # latency buckets (tune later if needed)
    buckets=(0.005, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

INFLIGHT = Gauge("http_requests_in_flight", "In-flight HTTP requests")


def _route_template(request: Request) -> str:
    # Use the route path template if available (e.g., /portfolios/{pid}/summary)
    route = request.scope.get("route")
    if route and getattr(route, "path", None):
        return route.path
    # fallback: raw path
    return request.url.path


# ---------- Logging ----------
_log = logging.getLogger("stashmock.api")
_log.setLevel(logging.INFO)


def _json_log(event: str, **fields):
    try:
        msg = {"event": event, **fields}
        _log.info(json.dumps(msg, separators=(",", ":")))
    except Exception:
        # never let logging crash a request
        _log.warning("log_failed", exc_info=True)


# ---------- Middleware (metrics + logs) ----------
def observability_middleware() -> Callable:
    async def _mw(request: Request, call_next):
        start = time.perf_counter()
        route = _route_template(request)
        method = request.method

        INFLIGHT.inc()
        try:
            response: Response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            # record exception path; re-raise for FastAPI to handle
            REQUEST_EXCEPTIONS_TOTAL.labels(method, route, exc.__class__.__name__).inc()
            latency = time.perf_counter() - start
            REQUEST_LATENCY.labels(method, route).observe(latency)
            INFLIGHT.dec()
            _json_log(
                "request_error",
                method=method,
                route=route,
                status=500,
                latency_ms=round(latency * 1000, 3),
                exc_type=exc.__class__.__name__,
            )
            raise

        latency = time.perf_counter() - start
        REQUESTS_TOTAL.labels(method, route, str(status)).inc()
        REQUEST_LATENCY.labels(method, route).observe(latency)
        INFLIGHT.dec()

        # terse structured access log
        _json_log(
            "request",
            method=method,
            route=route,
            status=status,
            latency_ms=round(latency * 1000, 3),
        )
        return response

    return _mw
