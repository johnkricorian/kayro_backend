from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.repositories.opportunity_repository import get_opportunities

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)

@router.get("")
def opportunities(
    sectors: list[str] = Query(default=["technology"]),
    limit: int = Query(default=20, ge=1, le=100),
    forecast_horizon: int = Query(default=15),
    db: Session = Depends(get_db),
):
    return get_opportunities(
        db=db,
        sectors=[sector.lower() for sector in sectors],
        forecast_horizon=forecast_horizon,
        limit=limit,
    )
