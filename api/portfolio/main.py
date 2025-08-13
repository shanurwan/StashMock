# This is the main portfolio to enable product and QA teams to rapidly access real account data for tesing/demo
# Goal for portfolio service :
# 1 - user see their investment status
# 2 - user perform investment actions
# 3 - user view their investment history
# 4 - user gets real time update and notification


from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Stashmock Portfolio Service", version="1.0.0")


# create /health for technical check to see if the service is alive and responding
# use case = monitoring & ops, isolation , for engineer to ensure API hasn't crashed

@app.get("/health")
def health_check():
    return {"status": "Healthy"}


# user see their investment status
@app.get("/status")
def health_check():
    return {"status": "Healthy"}
