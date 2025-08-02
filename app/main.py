from fastapi import FastAPI
from sample import user_portfolios, risk_scores

app = FastAPI()

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/portfolio/{user_id}")
def get_portfolio(user_id: str):
    portfolio = user_portfolios.get(user_id)
    if not portfolio:
        return {"error": "User not found"}
    return {"user_id": user_id, "portfolio": portfolio}

@app.get("/risk-score/{user_id}")
def get_risk_score(user_id: str):
    score = risk_scores.get(user_id)
    if score is None:
        return {"error": "User not found"}
    return {"user_id": user_id, "risk_score": score}
