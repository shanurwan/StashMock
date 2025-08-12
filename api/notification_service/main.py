
import os, json, threading, time, sys
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
NOTIFY_QUEUE = os.getenv("NOTIFY_QUEUE", "notify_events")
USE_FAKE = os.getenv("USE_FAKE_REDIS", "0") == "1"


def get_redis():
    if USE_FAKE:
        import fakeredis
        return fakeredis.FakeRedis(decode_responses=True)
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)

r = get_redis()


DELIVERED = Counter("notifications_delivered_total", "Total notifications delivered")
FAILED    = Counter("notifications_failed_total", "Notifications that failed to process")
QUEUE_LEN = Gauge("notifications_queue_depth", "Length of the notification queue")


app = FastAPI(title="Notification Service", version="0.1.0")

stop_flag = False

def process_message(raw: str) -> None:
    """
    Fake 'send email + log' to simulate real work.
    """
    try:
        msg = json.loads(raw)
    except Exception:
        msg = {"type": "unknown", "data": raw}
    
    time.sleep(0.05)
    DELIVERED.inc()

def consumer_loop():
    while not stop_flag:
        try:
            
            try:
                QUEUE_LEN.set(r.llen(NOTIFY_QUEUE))
            except Exception:
                pass

            item: Optional[tuple[str, str]] = r.brpop(NOTIFY_QUEUE, timeout=1)
            if not item:
                continue
            _, payload = item
            process_message(payload)
        except Exception as e:
            FAILED.inc()
            
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
    return {"status": "ok" if ok else "degraded", "queue": NOTIFY_QUEUE}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/_test/push")
def push_test_event():
    """Utility endpoint to push a test message if you don’t want to call the portfolio API."""
    r.lpush(NOTIFY_QUEUE, json.dumps({"type": "test", "data": {"hello": "world"}}))
    return {"queued": True}
