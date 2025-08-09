# api/notification_service/main.py
import os
import asyncio
from fastapi import FastAPI
from redis.asyncio import from_url as redis_from_url
from prometheus_fastapi_instrumentator import Instrumentator

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_EVENTS = os.getenv("STREAM_EVENTS", "events")
GROUP = os.getenv("EVENTS_GROUP", "notif-group")
CONSUMER = os.getenv("CONSUMER_NAME", "notif-1")

app = FastAPI(title="notification_service")
Instrumentator().instrument(app).expose(app)

redis = redis_from_url(REDIS_URL)


@app.on_event("startup")
async def _startup():
    await redis.ping()
    # Create consumer group if not exists (MKSTREAM to auto-create stream)
    try:
        await redis.xgroup_create(STREAM_EVENTS, GROUP, id="$", mkstream=True)
    except Exception:
        # group likely exists
        pass
    asyncio.create_task(consume_loop())


@app.get("/health")
async def health():
    return {"status": "ok"}


async def consume_loop():
    # Keep reading new messages
    while True:
        try:
            resp = await redis.xreadgroup(
                groupname=GROUP,
                consumername=CONSUMER,
                streams={STREAM_EVENTS: ">"},
                count=10,
                block=2000,  # 2s
            )
            if not resp:
                continue

            # resp: List[ (stream, [ (id, {field: val}), ... ]) ]
            for _stream, messages in resp:
                for msg_id, fields in messages:
                    event_type = fields.get(b"event_type", b"").decode()
                    if event_type == "email":
                        to = fields.get(b"to", b"").decode()
                        subject = fields.get(b"subject", b"").decode()
                        body = fields.get(b"body", b"").decode()
                        # Simulate sending email
                        print(f"[EMAIL] → {to} | {subject} | {body}")
                    # Acknowledge processing
                    await redis.xack(STREAM_EVENTS, GROUP, msg_id)
        except Exception as e:
            print("consumer error:", e)
            await asyncio.sleep(1)


# Dev server tip:
# uvicorn api.notification_service.main:app --reload --port 8002
