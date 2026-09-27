import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.agents.graph import portfolio_graph
from src.data_engine.ingester import init_db

app = FastAPI(title="FinAgent-X Portfolio Intelligence API")

# Initialize database tables on server startup
init_db()

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

class AnalysisRequest(BaseModel):
    ticker: str
    as_of_date: str = "2026-09-01"

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the interactive HTML dashboard at root URL."""
    html_file = os.path.join(static_dir, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>FinAgent-X API is running. index.html not found.</h1>"

@app.get("/health")
def health_check():
    return {"status": "online", "system": "FinAgent-X"}

@app.post("/api/v1/analyze")
async def analyze(req: AnalysisRequest):
    try:
        initial_state = {
            "ticker": req.ticker,
            "as_of_date": req.as_of_date,
            "quant_signals": {},
            "fundamental_data": {},
            "sentiment_analysis": {},
            "final_decision": {},
            "messages": []
        }
        result = portfolio_graph.invoke(initial_state)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
