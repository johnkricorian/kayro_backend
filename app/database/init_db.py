from app.database.database import Base, engine
from app.database.models import Prediction

def init_db():
    print("🗄️ Creating SQLite database...")
    print("Tables detected:", Base.metadata.tables.keys())
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")
