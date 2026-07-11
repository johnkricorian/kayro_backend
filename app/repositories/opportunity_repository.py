from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import Opportunity


def save_opportunities(
    db: Session,
    opportunities: list[dict],
    forecast_horizon: int
) -> None:
    """
    Replace all cached opportunities for a given forecast horizon.
    """

    db.query(Opportunity).filter(
        Opportunity.forecast_horizon == forecast_horizon
    ).delete(synchronize_session=False)

    now = datetime.utcnow()

    for item in opportunities:
        db.add(
            Opportunity(
                ticker=item["ticker"],
                sector=item["sector"],
                forecast_horizon=forecast_horizon,
                kayro_score=item["kayro_score"],
                recommendation=item["recommendation"],
                prediction=item["prediction"],
                confidence=item["confidence"],
                price=item["price"],
                change_percent=item["change_percent"],
                json_payload=item,
                updated_at=now
            )
        )

    db.commit()


def get_opportunities(
    db: Session,
    sectors: list[str],
    forecast_horizon: int,
    limit: int
) -> list[dict]:
    """
    Returns cached opportunities.
    """

    query = (
        db.query(Opportunity)
        .filter(
            Opportunity.forecast_horizon == forecast_horizon
        )
    )

    if sectors:
        query = query.filter(
            Opportunity.sector.in_(sectors)
        )

    rows = (
        query
        .order_by(
            Opportunity.kayro_score.desc()
        )
        .limit(limit)
        .all()
    )

    return [
        row.json_payload
        for row in rows
    ]


def delete_opportunities(
    db: Session,
    forecast_horizon: int | None = None
) -> None:
    """
    Clears cached opportunities.
    """

    query = db.query(Opportunity)

    if forecast_horizon is not None:
        query = query.filter(
            Opportunity.forecast_horizon == forecast_horizon
        )

    query.delete(synchronize_session=False)

    db.commit()


def opportunities_count(
    db: Session
) -> int:
    return db.query(Opportunity).count()
