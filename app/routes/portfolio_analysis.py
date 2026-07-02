from fastapi import APIRouter

from app.services.portfolio_analyzer import analyze_portfolio

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio Analysis"]
)


@router.get("/analyze")
def portfolio_analysis():
    return analyze_portfolio()
