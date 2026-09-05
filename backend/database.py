# database.py - Database connection and session management

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - Update with your PostgreSQL credentials
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/lifepath_db"
)

# Fix for SQLAlchemy compatibility with some providers (like Render) asking for postgres://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine — Phase 12: SQL echo is opt-in (SQL_ECHO=true) so production
# logs never carry verbose SQL/schema detail by default. Reason: PII/schema
# leak surface. Risk: developers lose SQL logs unless SQL_ECHO=true (runbook).
_SQL_ECHO = os.getenv("SQL_ECHO", "false").strip().lower() in ("1", "true", "yes")
engine = create_engine(DATABASE_URL, echo=_SQL_ECHO)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


