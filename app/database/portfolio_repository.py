from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.database.models import PortfolioPosition


def add_position(
    ticker: str,
    quantity: float,
    average_price: float
):
    db: Session = SessionLocal()

    try:
        position = PortfolioPosition(
            ticker=ticker.upper(),
            quantity=quantity,
            average_price=average_price
        )

        db.add(position)
        db.commit()
        db.refresh(position)

        return position

    finally:
        db.close()


def get_positions():
    db: Session = SessionLocal()

    try:
        return (
            db.query(PortfolioPosition)
            .order_by(PortfolioPosition.ticker)
            .all()
        )

    finally:
        db.close()


def get_position(
    ticker: str
):
    db: Session = SessionLocal()

    try:
        return (
            db.query(PortfolioPosition)
            .filter(
                PortfolioPosition.ticker == ticker.upper()
            )
            .first()
        )

    finally:
        db.close()


def update_position(
    ticker: str,
    quantity: float,
    average_price: float
):
    db: Session = SessionLocal()

    try:
        position = (
            db.query(PortfolioPosition)
            .filter(
                PortfolioPosition.ticker == ticker.upper()
            )
            .first()
        )

        if position is None:
            return None

        position.quantity = quantity
        position.average_price = average_price

        db.commit()
        db.refresh(position)

        return position

    finally:
        db.close()


def delete_position(
    ticker: str
):
    db: Session = SessionLocal()

    try:
        position = (
            db.query(PortfolioPosition)
            .filter(
                PortfolioPosition.ticker == ticker.upper()
            )
            .first()
        )

        if position is None:
            return False

        db.delete(position)
        db.commit()

        return True

    finally:
        db.close()
