import os, time, json, redis, random, string

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def random_id(n=6):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def seed():
    # Push tasks for worker and notifications to demonstrate scaling/decoupling
    for _ in range(50):
        r.lpush(os.getenv("TASK_QUEUE", "worker_tasks"), json.dumps({"task":"revalue","id":random_id()}))
        r.lpush(os.getenv("NOTIFY_QUEUE", "notify_events"), "seeded_event")
    print("Seeded 50 tasks & notifications")

if __name__ == "__main__":
    seed()
