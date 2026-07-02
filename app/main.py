from fastapi import FastAPI
from dotenv import load_dotenv

from app.routes.score import router as score_router
from app.routes.sectors import router as sectors_router
from app.routes.test import router as test_router
from app.routes.portfolio import router as portfolio_router
from app.routes.test_scanner import router as test_scanner_router
from app.database.init_db import init_db
from app.routes.predictions import router as predictions_router
from app.routes.evaluation import router as evaluation_router
from app.routes.stats import router as stats_router
from app.routes.leaderboard import router as leaderboard_router
from app.routes.portfolio_positions import router as portfolio_positions_router
from app.routes.portfolio_analysis import (router as portfolio_analysis_router)

from contextlib import asynccontextmanager
from app.services.model_loader import warmup_models

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n🚀 Initializing database...")
    init_db()
    print("\n🚀 Warming up XGBoost models...")
    warmup_models()
    yield


app = FastAPI(
    title="Kayro Stock API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(score_router)
app.include_router(sectors_router)
app.include_router(test_router)
app.include_router(portfolio_router)
app.include_router(test_scanner_router)
app.include_router(predictions_router)
app.include_router(evaluation_router)
app.include_router(stats_router)
app.include_router(leaderboard_router)
app.include_router(portfolio_positions_router)
app.include_router(portfolio_analysis_router)

@app.get("/")
def root():
    return {
        "status": "running"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }
