from fastapi import APIRouter, Query

from app.database.prediction_repository import get_leaderboard

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"]
)


@router.get("")
def leaderboard(
    limit: int = Query(default=20, ge=1, le=100)
):
    return get_leaderboard(limit)
