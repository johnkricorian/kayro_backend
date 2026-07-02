from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    ticker: Mapped[str] = mapped_column(
        String,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    forecast_horizon: Mapped[int] = mapped_column(Integer)

    predicted_direction: Mapped[str] = mapped_column(String)

    probability_up: Mapped[float] = mapped_column(Float)

    confidence: Mapped[float] = mapped_column(Float)

    kayro_score: Mapped[int] = mapped_column(Integer)

    recommendation: Mapped[str] = mapped_column(String)

    price_at_prediction: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    price_after_horizon: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    prediction_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    evaluated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

class Prediction(Base):
    __tablename__ = "predictions"

    ...
    # ton modèle actuel


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    ticker: Mapped[str] = mapped_column(
        String,
        index=True
    )

    quantity: Mapped[float] = mapped_column(Float)

    average_price: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
