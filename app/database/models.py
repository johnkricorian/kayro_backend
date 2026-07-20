from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Boolean,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
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

# app/database/models.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    JSON
)

class Opportunity(Base):
    __tablename__ = "opportunities"

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "forecast_horizon",
            name="uq_opportunity_ticker_horizon",
        ),
    )

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False, index=True)
    sector = Column(String, nullable=False, index=True)
    forecast_horizon = Column(Integer, nullable=False, index=True)

    kayro_score = Column(Integer)
    recommendation = Column(String)
    prediction = Column(String)
    confidence = Column(Float)
    price = Column(Float)
    change_percent = Column(Float)

    json_payload = Column(JSON)
    updated_at = Column(DateTime, nullable=False)

class UserPrediction(Base):
    __tablename__ = "user_predictions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker",
            "forecast_horizon",
            name="uq_user_prediction_user_ticker_horizon",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    ticker: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    forecast_horizon: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=15,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="selected",
    )

    kayro_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    recommendation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    direction: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    probability_up: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    probability_down: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    latest_close: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    target_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    prediction_payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
