"""Database initialization and default user seeding."""

from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.models.enums import UserRole
import app.models  # Ensure all models are registered with Base metadata


def init_db(db: Session) -> None:
    """Create all tables and seed default users if not already present."""
    Base.metadata.create_all(bind=engine)

    # Seed Admin User
    admin = db.query(User).filter(User.email == "admin@pbnc.internal").first()
    if not admin:
        admin = User(
            email="admin@pbnc.internal",
            hashed_password=get_password_hash("admin12345"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)

    # Seed Reviewer User
    reviewer = db.query(User).filter(User.email == "reviewer@pbnc.internal").first()
    if not reviewer:
        reviewer = User(
            email="reviewer@pbnc.internal",
            hashed_password=get_password_hash("reviewer12345"),
            full_name="Quality Reviewer",
            role=UserRole.REVIEWER,
            is_active=True,
        )
        db.add(reviewer)

    # Seed Standard Examination User
    user = db.query(User).filter(User.email == "user@pbnc.internal").first()
    if not user:
        user = User(
            email="user@pbnc.internal",
            hashed_password=get_password_hash("user12345"),
            full_name="Standard Exam User",
            role=UserRole.USER,
            is_active=True,
        )
        db.add(user)

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db(db)
        print("Database initialized and default users seeded successfully.")
    finally:
        db.close()
