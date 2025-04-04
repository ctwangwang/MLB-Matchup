# database/db_setup.py
"""
Database initialization and table creation module
"""

import os
import sqlite3
from config.team_config import DATA_DIR, DB_NAME


def get_db_path():
    """Return complete database path"""
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, DB_NAME)


def create_connection():
    """Create and return database connection"""
    conn = sqlite3.connect(get_db_path())
    return conn


def create_tables():
    """Create required data tables"""
    conn = create_connection()
    cursor = conn.cursor()

    # Player season statistics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_season_stats (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT,
            team_id INTEGER,
            team_name TEXT,
            avg REAL,
            obp REAL,
            slg REAL,
            ops REAL
        )
    """)

    # Player recent statistics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_recent_stats (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT,
            team_id INTEGER,
            avg REAL,
            obp REAL,
            slg REAL,
            avg_ops REAL
        )
    """)

    conn.commit()
    conn.close()

    print("✅ Database tables creation completed")


def initialize_database():
    """Initialize database environment"""
    os.makedirs(DATA_DIR, exist_ok=True)
    create_tables()


if __name__ == "__main__":
    initialize_database()
