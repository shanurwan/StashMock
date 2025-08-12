
import os, json
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
NOTIFY_QUEUE = os.getenv("NOTIFY_QUEUE", "notify_events")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def publish(event_type: str, payload: dict):
    """
    Publish a simple event to Redis. We use a LIST here for simplicity.
    In production you might use Redis Streams (XADD).
    """
    msg = {"type": event_type, "data": payload}
    r.lpush(NOTIFY_QUEUE, json.dumps(msg))
