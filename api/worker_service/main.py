# api/worker_service/main.py
from fastapi import FastAPI

app = FastAPI(title="StashMock Worker Service", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}
