from sqlalchemy import (
    create_engine, Column, DateTime, Numeric, String, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import os

Base = declarative_base()

# -------- Ledger Table Only --------

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ts = Column(DateTime, default=datetime.utcnow)
    ref = Column(String(255), index=True, nullable=False)
    delta = Column(Numeric(20, 8), nullable=False)
    reason = Column(String(255), nullable=False)
    meta = Column(JSON)

# -------- Database Connection --------

def get_engine():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set")
    return create_engine(dsn, pool_pre_ping=True)

# Init session factory lazily
_engine = None
_SessionLocal = None

def get_db_session():
    global _engine, _SessionLocal

    if _engine is None:
        _engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        )

        # Auto-create tables if needed
        Base.metadata.create_all(_engine)

    return _SessionLocal()
