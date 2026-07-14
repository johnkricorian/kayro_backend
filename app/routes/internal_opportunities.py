import time

from fastapi import APIRouter

from app.jobs.generate_opportunities import generate


router = APIRouter(
    prefix="/internal/opportunities",
    tags=["Internal"],
)


@router.post("/refresh")
def refresh_opportunities():
    started_at = time.perf_counter()

    generated_count = generate()

    elapsed = time.perf_counter() - started_at

    return {
        "status": "completed",
        "generated": generated_count,
        "duration_seconds": round(elapsed, 2),
    }
