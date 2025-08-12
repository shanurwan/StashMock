
import os, json, threading, time
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TASK_QUEUE = os.getenv("TASK_QUEUE", "worker_tasks")
USE_FAKE = os.getenv("USE_FAKE_REDIS", "0") == "1"

def get_redis():
    if USE_FAKE:
        import fakeredis
        return fakeredis.FakeRedis(decode_responses=True)
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)

r = get_redis()

QUEUE_DEPTH = Gauge("worker_queue_depth", "Current depth of worker task queue")
TASKS_DONE  = Counter("worker_tasks_done_total", "Tasks processed")
TASKS_FAIL  = Counter("worker_tasks_failed_total", "Tasks failed")

app = FastAPI(title="Worker Service", version="0.1.0")

stop_flag = False

def handle_task(raw: str):
    """
    Simulate a heavier background job (pricing, reconciliation, etc).
    """
    try:
        task = json.loads(raw)
    except Exception:
        task = {"task": "unknown", "raw": raw}
    # pretend it’s CPU/IO heavy
    time.sleep(0.1)
    TASKS_DONE.inc()

def consumer_loop():
    while not stop_flag:
        try:
            try:
                QUEUE_DEPTH.set(r.llen(TASK_QUEUE))
            except Exception:
                pass

            item: Optional[tuple[str, str]] = r.brpop(TASK_QUEUE, timeout=1)
            if not item:
                continue
            _, payload = item
            handle_task(payload)
        except Exception:
            TASKS_FAIL.inc()
            time.sleep(0.1)

t = threading.Thread(target=consumer_loop, daemon=True)
t.start()

@app.get("/health")
def health():
    try:
        r.ping()
        ok = True
    except Exception:
        ok = False
    return {"status": "ok" if ok else "degraded", "queue": TASK_QUEUE}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/_test/enqueue")
def enqueue_test_task():
    """
    Convenience endpoint to push a demo task if you don’t have a producer yet.
    """
    r.lpush(TASK_QUEUE, json.dumps({"task": "revalue", "id": int(time.time())}))
    return {"queued": True}
