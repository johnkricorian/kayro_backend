import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def build_database_url():
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")

    if instance_connection_name:
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")

        missing = [
            name
            for name, value in {
                "DB_USER": db_user,
                "DB_PASSWORD": db_password,
                "DB_NAME": db_name,
            }.items()
            if not value
        ]

        if missing:
            raise RuntimeError(
                f"Missing database environment variables: {', '.join(missing)}"
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=db_user,
            password=db_password,
            database=db_name,
            query={
                "host": f"/cloudsql/{instance_connection_name}"
            },
        )

    db_path = os.getenv("KAYRO_DB_PATH", "./kayro.db")
    return f"sqlite:///{db_path}"

DATABASE_URL = build_database_url()

is_sqlite = str(DATABASE_URL).startswith("sqlite")

engine_options = {
    "pool_pre_ping": True,
}

if is_sqlite:
    engine_options["connect_args"] = {
        "check_same_thread": False
    }
else:
    engine_options.update(
        {
            "pool_size": 5,
            "max_overflow": 2,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
    )

engine = create_engine(
    DATABASE_URL,
    **engine_options,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
