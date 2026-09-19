"""Database engine configuration and session provider."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# Configure engine connect arguments
connect_args = {}
database_uri = settings.SQLALCHEMY_DATABASE_URI

if database_uri.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_uri,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
