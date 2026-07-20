from app.database.database import Base, engine
import app.database.models  # noqa: F401
from app.core.logger import create_logger

logger = create_logger(__name__)


def init_db() -> None:
    logger.info("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    logger.info(
        "Tables detected: %s",
        ", ".join(sorted(Base.metadata.tables.keys())),
    )

    logger.info("Database initialized successfully.")
