from fastapi import APIRouter

from app.database.prediction_repository import get_global_stats

router = APIRouter(
    prefix="/stats",
    tags=["Stats"]
)


@router.get("")
def stats():
    return get_global_stats()
