# api/notification_service/main.py
from __future__ import annotations
import os, json, asyncio, time
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis import Redis
import fakeredis

REDIS_URL = os.getenv("REDIS_URL", "fakeredis://")
NOTIFY_QUEUE = os.getenv("NOTIFY_QUEUE", "notify_events")

def _redis_client() -> Redis:
    if REDIS_URL.startswith("fakeredis://"):
        return fakeredis.FakeRedis(decode_responses=True)
    return Redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="StashMock Notification Service", version="0.1.0")

state = {
    "processed": 0,
    "last_event": None,
    "started_at": int(time.time())
}

stop_event = asyncio.Event()

async def _consumer_loop():
    r = _redis_client()
    # Use BLPOP-style polling; fakeredis supports BLPOP but we can also poll with timeout
    while not stop_event.is_set():
        try:
            item = r.blpop(NOTIFY_QUEUE, timeout=1)  # blocks up to 1s
            if not item:
                await asyncio.sleep(0)  # yield
                continue
            _queue, payload = item
            evt = json.loads(payload)
            # Simulate "sending" (email/log/whatever)
            # In real app you'd call SES/SMTP/etc. Here we just update stats.
            state["processed"] += 1
            state["last_event"] = evt
        except Exception:
            # never crash the loop on transient errors
            await asyncio.sleep(0.1)

@app.on_event("startup")
async def _startup():
    app.consumer_task = asyncio.create_task(_consumer_loop())

@app.on_event("shutdown")
async def _shutdown():
    stop_event.set()
    t = getattr(app, "consumer_task", None)
    if t:
        await t

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def stats():
    return state

