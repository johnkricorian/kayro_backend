from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Opportunity
from sqlalchemy import func

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

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import Opportunity


from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.database.models import Opportunity


def upsert_opportunities(
    db: Session,
    opportunities: list[dict],
    forecast_horizon: int,
) -> int:
    if not opportunities:
        return 0

    now = datetime.now(timezone.utc)

    try:
        for item in opportunities:
            ticker = item["ticker"].upper()
            sector = item["sector"].strip().lower()

            rows = (
                db.query(Opportunity)
                .filter(
                    Opportunity.ticker == ticker,
                    Opportunity.forecast_horizon == forecast_horizon,
                )
                .order_by(
                    Opportunity.updated_at.desc(),
                    Opportunity.id.desc(),
                )
                .all()
            )

            row = rows[0] if rows else None

            for duplicate in rows[1:]:
                db.delete(duplicate)

            if row is None:
                row = Opportunity(
                    ticker=ticker,
                    sector=sector,
                    forecast_horizon=forecast_horizon,
                )
                db.add(row)

            row.sector = sector
            row.kayro_score = item["kayro_score"]
            row.recommendation = item["recommendation"]
            row.prediction = item["prediction"]
            row.confidence = item["confidence"]
            row.price = item["price"]
            row.change_percent = item["change_percent"]
            row.json_payload = item
            row.updated_at = now

        db.commit()
        return len(opportunities)

    except Exception:
        db.rollback()
        raise

def get_opportunities(
    db: Session,
    sectors: list[str],
    forecast_horizon: int,
    limit: int,
) -> list[dict]:
    normalized_sectors = [
        sector.strip().lower()
        for sector in sectors
        if sector.strip()
    ]

    query = db.query(Opportunity).filter(
        Opportunity.forecast_horizon == forecast_horizon
    )

    if normalized_sectors:
        query = query.filter(
            Opportunity.sector.in_(normalized_sectors)
        )

    rows = (
        query
        .order_by(Opportunity.kayro_score.desc())
        .limit(limit)
        .all()
    )

    return [row.json_payload for row in rows]


def delete_stale_opportunities(
    db: Session,
    forecast_horizon: int,
    refresh_started_at: datetime,
) -> int:
    try:
        deleted = (
            db.query(Opportunity)
            .filter(
                Opportunity.forecast_horizon == forecast_horizon,
                Opportunity.updated_at < refresh_started_at,
            )
            .delete(synchronize_session=False)
        )

        db.commit()
        return deleted

    except Exception:
        db.rollback()
        raise

def remove_duplicate_opportunities(db: Session) -> int:
    duplicates = (
        db.query(
            Opportunity.ticker,
            Opportunity.forecast_horizon,
            func.count(Opportunity.id).label("count"),
        )
        .group_by(
            Opportunity.ticker,
            Opportunity.forecast_horizon,
        )
        .having(func.count(Opportunity.id) > 1)
        .all()
    )

    deleted_count = 0

    for ticker, forecast_horizon, _ in duplicates:
        rows = (
            db.query(Opportunity)
            .filter(
                Opportunity.ticker == ticker,
                Opportunity.forecast_horizon == forecast_horizon,
            )
            .order_by(
                Opportunity.updated_at.desc(),
                Opportunity.id.desc(),
            )
            .all()
        )

        for duplicate in rows[1:]:
            db.delete(duplicate)
            deleted_count += 1

    db.commit()
    return deleted_count

def opportunities_count(db: Session) -> int:
    return db.query(Opportunity).count()
