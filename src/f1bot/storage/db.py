"""Database setup and connection."""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from f1bot.config import settings
from f1bot.logging import get_logger

logger = get_logger(__name__)

# Create data directory if needed
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Create engine
engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.db_url else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    logger.info("Initializing database...")
    
    with engine.connect() as conn:
        # Users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                lang TEXT NOT NULL DEFAULT 'ru',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Races table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS races (
                race_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                start_time_utc TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                meta_json TEXT
            )
        """))
        
        # Contents table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                lang TEXT NOT NULL,
                status TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(race_id, content_type, lang)
            )
        """))
        
        # Bingo cards table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bingo_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_id TEXT NOT NULL,
                lang TEXT NOT NULL,
                cells_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(race_id, lang)
            )
        """))
        
        # Bingo user state table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bingo_user_state (
                race_id TEXT NOT NULL,
                telegram_id INTEGER NOT NULL,
                states_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (race_id, telegram_id)
            )
        """))
        
        conn.commit()
    
    logger.info("Database initialized successfully")


def get_db() -> Session:
    """Get database session."""
    return SessionLocal()
