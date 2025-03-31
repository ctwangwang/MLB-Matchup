# database/db_setup.py
"""
數據庫初始化和表格創建模組
"""

import os
import sqlite3
from config.team_config import DATA_DIR, DB_NAME


def get_db_path():
    """返回數據庫完整路徑"""
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, DB_NAME)


def create_connection():
    """創建並返回數據庫連接"""
    conn = sqlite3.connect(get_db_path())
    return conn


def create_tables():
    """創建所需的數據表格"""
    conn = create_connection()
    cursor = conn.cursor()

    # 球員賽季統計表
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

    # 球員近期統計表
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

    print("✅ 數據庫表格創建完成")


def initialize_database():
    """初始化數據庫環境"""
    os.makedirs(DATA_DIR, exist_ok=True)
    create_tables()


if __name__ == "__main__":
    initialize_database()
