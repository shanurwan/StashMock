from fastapi import FastAPI
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram
from fastapi.responses import Response
import time
import os

# OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    service_name = os.environ.get("OTEL_SERVICE_NAME", "hello-service")
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)
except Exception:
    tracer = None

app = FastAPI(title="Hello Platform")

REQS = Counter("hello_requests_total", "Total hello requests", ["path"])
LAT = Histogram(
    "hello_request_seconds", "Latency", buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2)
)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/hello")
def hello(name: str = "world"):
    start = time.time()
    if tracer:
        with tracer.start_as_current_span("hello-handler"):
            time.sleep(0.03)  # simulate work
            REQS.labels(path="/hello").inc()
    else:
        time.sleep(0.03)
        REQS.labels(path="/hello").inc()
    LAT.observe(time.time() - start)
    return {"message": f"hello, {name}"}
