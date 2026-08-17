from fastapi import APIRouter, Query

from app.services.fmp import (
    get_available_sectors,
    get_available_industries,
    get_available_countries,
)

from app.services.market_universe import (
    get_market_universe,
)


router = APIRouter(
    prefix="/universe",
    tags=["Market Universe"]
)


@router.get("/sectors")
def sectors():
    return get_available_sectors()


@router.get("/industries")
def industries():
    return get_available_industries()


@router.get("/countries")
def countries():
    return get_available_countries()


@router.get("/stocks")
def stocks(
    sector: str | None = None,
    industry: str | None = None,
    country: str | None = None,
    exchange: str | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=1000
    )
):
    return get_market_universe(
        sector=sector,
        industry=industry,
        country=country,
        exchange=exchange,
        limit=limit
    )
