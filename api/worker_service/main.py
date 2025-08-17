# api/worker_service/main.py
from __future__ import annotations
import os, json, asyncio, time
from fastapi import FastAPI
from redis import Redis
import fakeredis

REDIS_URL = os.getenv("REDIS_URL", "fakeredis://")
TASK_QUEUE = os.getenv("TASK_QUEUE", "worker_tasks")


def _redis_client() -> Redis:
    if REDIS_URL.startswith("fakeredis://"):
        return fakeredis.FakeRedis(decode_responses=True)
    return Redis.from_url(REDIS_URL, decode_responses=True)


app = FastAPI(title="StashMock Worker Service", version="0.1.0")

state = {"processed": 0, "last_task": None, "started_at": int(time.time())}

stop_event = asyncio.Event()


async def _worker_loop():
    r = _redis_client()
    while not stop_event.is_set():
        try:
            item = r.blpop(TASK_QUEUE, timeout=1)
            if not item:
                await asyncio.sleep(0)
                continue
            _queue, payload = item
            task = json.loads(payload)
            # Simulate doing some work (sleep a tiny bit)
            await asyncio.sleep(0.05)
            state["processed"] += 1
            state["last_task"] = task
        except Exception:
            await asyncio.sleep(0.1)


@app.on_event("startup")
async def _startup():
    app.worker_task = asyncio.create_task(_worker_loop())


@app.on_event("shutdown")
async def _shutdown():
    stop_event.set()
    t = getattr(app, "worker_task", None)
    if t:
        await t


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    return state
