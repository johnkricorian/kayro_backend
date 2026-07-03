from fastapi import APIRouter

from app.services.scanner import scan_sector

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/scanner/{sector}")
def test_scanner(
    sector: str,
    limit: int = 10
):
    return scan_sector(
        sector=sector,
        limit=limit
    )
