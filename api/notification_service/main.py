# This one will listen for events from Redis and send email/SMS notifications.
# api/notification_service/main.py
from fastapi import FastAPI

app = FastAPI(title="StashMock Notification Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}
