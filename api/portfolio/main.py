#This is the first REST API, it is the main brain that talk to PostgreSQL
#Goal for portfolio service :
# 1 - user see their investment status
# 2 - user perform investment actions
# 3 - user view their investment history
# 4 - user gets real time update and notification
# Note: for simulation simplicity we skip login for now

from fastapi import FastAPI

app = FastAPI()

# create /health for technical check to see if the service is alive and responding
# use case = monitoring & ops, isolation , for engineer to ensure API hasn't crashed

@app.get("/health")
def health_check():
    return {'status': 'Healthy'}


