import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def get_database_url() -> str:
    """Return the active SQLite database URL from environment or default."""
    return os.getenv("DATABASE_URL", "sqlite:///./students.db")


def get_engine(db_url: str = None):
    """Create and return a SQLAlchemy engine for SQLite."""
    url = db_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


# Default engine instance for application runtime
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session(target_engine=None):
    """Return a new database session bound to the specified engine or active engine."""
    current_engine = target_engine or get_engine()
    factory = sessionmaker(autocommit=False, autoflush=False, bind=current_engine)
    return factory()


def get_db():
    """FastAPI dependency to provide a database session per request."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine=None):
    """Initialize database tables.
    
    Safe to execute multiple times (idempotent).
    """
    target = target_engine or get_engine()
    # Import models so they are registered with Base.metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=target)
