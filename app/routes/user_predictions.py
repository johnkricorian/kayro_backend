from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.current_user import get_current_user_id
from app.database.database import get_db
from app.models.user_prediction import (
    UserPredictionCreate,
    UserPredictionResponse,
)
from app.repositories.user_prediction_repository import (
    delete_user_prediction,
    get_user_predictions,
    save_user_prediction,
)
from app.services.score_engine import build_stock_score


router = APIRouter(
    prefix="/user-predictions",
    tags=["User predictions"],
)


@router.post(
    "",
    response_model=UserPredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_prediction(
    body: UserPredictionCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    prediction_payload = build_stock_score(
        ticker=body.ticker,
        forecast_horizon=body.forecast_horizon,
    )

    return save_user_prediction(
        db,
        user_id=user_id,
        ticker=body.ticker,
        forecast_horizon=body.forecast_horizon,
        prediction_payload=prediction_payload,
    )


@router.get(
    "",
    response_model=list[UserPredictionResponse],
)
def list_user_predictions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_user_predictions(
        db,
        user_id=user_id,
    )


@router.delete(
    "/{ticker}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_user_prediction(
    ticker: str,
    forecast_horizon: int = 15,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    deleted = delete_user_prediction(
        db,
        user_id=user_id,
        ticker=ticker,
        forecast_horizon=forecast_horizon,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found.",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
