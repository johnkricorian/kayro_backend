from app.database.database import Base, engine
from app.database.models import (
    Opportunity,
    PortfolioPosition,
    Prediction,
)
from app.core.logger import create_logger

logger = create_logger(__name__)

def init_db():
    logger.info("Creating database tables")

    Base.metadata.create_all(bind=engine)

    logger.info(
        "Tables detected: %s",
        list(Base.metadata.tables.keys()),
    )

    logger.info("Database initialized")
