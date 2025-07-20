from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from config import Config
from models import Base

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_engine()
        # Ensure SessionLocal is initialized
        if not self.SessionLocal:
            raise RuntimeError("Failed to initialize database session")
    
    def _setup_engine(self):
        """Setup database engine based on configuration"""
        if Config.DATABASE_URL.startswith("sqlite"):
            # SQLite configuration
            self.engine = create_engine(
                Config.DATABASE_URL,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=Config.DEBUG
            )
        else:
            # PostgreSQL configuration
            self.engine = create_engine(
                Config.DATABASE_URL,
                echo=Config.DEBUG,
                pool_pre_ping=True
            )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get database session (for sync operations)"""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()

# Global database instance
db = Database()

def init_database():
    """Initialize database and create tables"""
    db.create_tables() 