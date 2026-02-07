"""
Database connection and models for AI Verification Service
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Generator
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ================================
# Database Models
# ================================

class AIVerification(Base):
    """AI Verification results table"""
    __tablename__ = "ai_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, nullable=False, index=True)
    verification_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    confidence_score = Column(Float)
    rejection_reasons = Column(ARRAY(Text))
    checks_performed = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class TimelineEvent(Base):
    """Timeline events table"""
    __tablename__ = "timeline_events"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    actor_type = Column(String(20), nullable=False)
    actor_id = Column(Integer)
    description = Column(Text, nullable=False)
    metadata = Column(JSON)
    image_urls = Column(ARRAY(Text))
    created_at = Column(DateTime, default=datetime.utcnow)


# ================================
# Database Utilities
# ================================

def get_db() -> Generator[Session, None, None]:
    """
    Get database session
    
    Usage:
        with get_db() as db:
            # Use db session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_db_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# ================================
# Database Operations
# ================================

def save_verification_result(
    db: Session,
    issue_id: int,
    verification_type: str,
    status: str,
    confidence_score: float,
    rejection_reasons: list,
    checks_performed: dict,
    metadata: dict = None
) -> AIVerification:
    """Save verification result to database"""
    verification = AIVerification(
        issue_id=issue_id,
        verification_type=verification_type,
        status=status,
        confidence_score=confidence_score,
        rejection_reasons=rejection_reasons,
        checks_performed=checks_performed,
        metadata=metadata or {}
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def create_timeline_event(
    db: Session,
    issue_id: int,
    event_type: str,
    actor_type: str,
    description: str,
    actor_id: int = None,
    metadata: dict = None,
    image_urls: list = None
) -> TimelineEvent:
    """Create a timeline event"""
    event = TimelineEvent(
        issue_id=issue_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        description=description,
        metadata=metadata or {},
        image_urls=image_urls or []
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_verification_by_issue_id(db: Session, issue_id: int) -> AIVerification:
    """Get latest verification for an issue"""
    return db.query(AIVerification)\
        .filter(AIVerification.issue_id == issue_id)\
        .order_by(AIVerification.created_at.desc())\
        .first()


def get_all_verifications_for_issue(db: Session, issue_id: int) -> list:
    """Get all verifications for an issue"""
    return db.query(AIVerification)\
        .filter(AIVerification.issue_id == issue_id)\
        .order_by(AIVerification.created_at.desc())\
        .all()


def get_timeline_events(db: Session, issue_id: int) -> list:
    """Get all timeline events for an issue"""
    return db.query(TimelineEvent)\
        .filter(TimelineEvent.issue_id == issue_id)\
        .order_by(TimelineEvent.created_at.asc())\
        .all()
