from app.database.database import Base, engine
from app.database.models import Prediction, PortfolioPosition
from app.core.logger import create_logger

logger = create_logger(__name__)

def init_db():
    logger.info("🗄️ Creating SQLite database...")
    logger.info("Tables detected:", Base.metadata.tables.keys())

    Base.metadata.create_all(bind=engine)

    logger.info("✅ Database initialized")
