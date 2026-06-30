from fastapi import APIRouter, HTTPException, Query

from app.services.scanner import scan_sector
from app.services.sector_loader import get_available_sectors

router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"]
)


@router.get("")
def get_sectors():
    return {
        "sectors": get_available_sectors()
    }


@router.get("/{sector}/top")
def get_top_stocks(
    sector: str,
    limit: int = Query(default=20, ge=1, le=50)
):
    try:
        return {
            "sector": sector,
            "limit": limit,
            "stocks": scan_sector(sector, limit)
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
