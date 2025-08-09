import os
import asyncio
from fastapi import FastAPI
from redis.asyncio import from_url as redis_from_url
from prometheus_fastapi_instrumentator import Instrumentator

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_TASKS = os.getenv("STREAM_TASKS", "tasks")
GROUP = os.getenv("TASKS_GROUP", "workers")
CONSUMER = os.getenv("CONSUMER_NAME", "worker-1")

app = FastAPI(title="worker_service")
Instrumentator().instrument(app).expose(app)

redis = redis_from_url(REDIS_URL)


@app.on_event("startup")
async def _startup():
    await redis.ping()
    try:
        await redis.xgroup_create(STREAM_TASKS, GROUP, id="$", mkstream=True)
    except Exception:
        pass
    asyncio.create_task(consume_tasks())


@app.get("/health")
async def health():
    return {"status": "ok"}


async def consume_tasks():
    while True:
        try:
            resp = await redis.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER,
                streams={STREAM_TASKS: ">"},
                count=10,
                block=2000,
            )
            if not resp:
                continue

            for _stream, messages in resp:
                for msg_id, fields in messages:
                    task_type = fields.get(b"task_type", b"").decode()
                    if task_type == "recalc":
                        pid = fields.get(b"portfolio_id", b"?").decode()
                        # Simulate heavy compute
                        print(f"[WORKER] Recalculating portfolio {pid} ...")
                        await asyncio.sleep(0.5)
                        print(f"[WORKER] Done portfolio {pid}")
                    await redis.xack(STREAM_TASKS, GROUP, msg_id)
        except Exception as e:
            print("worker error:", e)
            await asyncio.sleep(1)


# Dev server tip:
# uvicorn api.worker_service.main:app --reload --port 8003
