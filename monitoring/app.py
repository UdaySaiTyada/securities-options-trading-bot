from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import json
from datetime import datetime
from typing import Dict, List, Optional

app = FastAPI(title="Trading Bot Monitor")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0)

class TradeStatus(BaseModel):
    symbol: str
    position_type: str
    entry_price: float
    current_price: float
    pnl: float
    timestamp: datetime

class PortfolioStatus(BaseModel):
    total_value: float
    cash_balance: float
    positions_value: float
    total_pnl: float
    risk_exposure: float

@app.get("/")
async def root():
    return {"status": "running"}

@app.get("/active-trades", response_model=List[TradeStatus])
async def get_active_trades():
    try:
        trades = redis_client.get('active_trades')
        if trades:
            return json.loads(trades)
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio", response_model=PortfolioStatus)
async def get_portfolio_status():
    try:
        portfolio = redis_client.get('portfolio_status')
        if portfolio:
            return json.loads(portfolio)
        raise HTTPException(status_code=404, detail="Portfolio data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/performance")
async def get_performance_metrics():
    try:
        metrics = redis_client.get('performance_metrics')
        if metrics:
            return json.loads(metrics)
        return {"message": "No performance metrics available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-metrics")
async def get_risk_metrics():
    try:
        metrics = redis_client.get('risk_metrics')
        if metrics:
            return json.loads(metrics)
        return {"message": "No risk metrics available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trading-signals")
async def get_trading_signals():
    try:
        signals = redis_client.get('trading_signals')
        if signals:
            return json.loads(signals)
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system-health")
async def get_system_health():
    try:
        # Check Redis connection
        redis_status = redis_client.ping()
        
        # Get bot status
        bot_status = redis_client.get('bot_status')
        if bot_status:
            bot_status = json.loads(bot_status)
        else:
            bot_status = {"status": "unknown"}
        
        return {
            "redis_connected": redis_status,
            "bot_status": bot_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
