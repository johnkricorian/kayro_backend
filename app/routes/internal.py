import os

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    status,
)

from app.services.prediction_batch import (
    generate_prediction_batch,
)
from app.services.prediction_evaluator import (
    evaluate_pending_predictions,
)


router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


def _validate_internal_api_key(
    x_internal_api_key: str | None,
) -> None:
    expected_key = os.getenv(
        "QEYRO_INTERNAL_API_KEY"
    )

    if not expected_key:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=(
                "Internal API key is not configured"
            ),
        )

    if x_internal_api_key != expected_key:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail="Invalid internal API key",
        )


@router.post("/daily-prediction-batch")
def daily_prediction_batch(
    x_internal_api_key: str | None = Header(
        default=None
    ),
) -> dict:
    _validate_internal_api_key(
        x_internal_api_key
    )

    return generate_prediction_batch(
        force_refresh=True
    )


@router.post("/evaluate-predictions")
def evaluate_predictions(
    x_internal_api_key: str | None = Header(
        default=None
    ),
) -> dict:
    _validate_internal_api_key(
        x_internal_api_key
    )

    return evaluate_pending_predictions()
