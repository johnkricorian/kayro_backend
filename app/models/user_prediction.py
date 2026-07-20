from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserPredictionCreate(BaseModel):
    ticker: str = Field(
        min_length=1,
        max_length=20,
    )

    forecast_horizon: int = Field(
        default=15,
        ge=1,
        le=365,
    )


class UserPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    forecast_horizon: int
    status: str

    kayro_score: int | None
    recommendation: str | None
    confidence: float | None

    direction: str | None
    probability_up: float | None
    probability_down: float | None

    latest_close: float | None
    target_price: float | None

    prediction_payload: dict | None

    created_at: datetime
    updated_at: datetime
