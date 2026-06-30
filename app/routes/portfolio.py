from fastapi import APIRouter, HTTPException, Query

from app.services.portfolio_engine import rank_all_stocks, rank_sector

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)


@router.get("/rankings")
def get_rankings(
    limit: int = Query(default=20, ge=1, le=50),
    forecast_horizon: int = Query(default=15, ge=1, le=60)
):
    return {
        "limit": limit,
        "forecast_horizon": forecast_horizon,
        "stocks": rank_all_stocks(
            limit=limit,
            forecast_horizon=forecast_horizon
        )
    }


@router.get("/sector/{sector}")
def get_sector_rankings(
    sector: str,
    limit: int = Query(default=20, ge=1, le=50),
    forecast_horizon: int = Query(default=15, ge=1, le=60)
):
    try:
        return {
            "sector": sector,
            "limit": limit,
            "forecast_horizon": forecast_horizon,
            "stocks": rank_sector(
                sector=sector,
                limit=limit,
                forecast_horizon=forecast_horizon
            )
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )
