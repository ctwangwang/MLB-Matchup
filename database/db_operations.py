# database/db_operations.py
"""
Database Operations Module: Contains functions for querying, updating, deleting, and other database operations
"""

import sqlite3
from .db_setup import get_db_path


def query_db(query, params=(), one=False):
    """Execute SQL query and return results"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = (
        sqlite3.Row
    )  # Enable row factory to access results by column name
    cur = conn.cursor()
    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()

    # If a single result is requested or there's only one result, return it directly
    if one or (len(results) == 1 and one is None):
        return results[0] if results else None
    return results


def insert_or_replace_data(table, data):
    """Insert or replace records in the database

    Args:
        table (str): Table name
        data (dict): Dictionary of column names and values
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    values = tuple(data.values())

    query = f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.execute(query, values)

    conn.commit()
    conn.close()


def insert_many(table, columns, data_list):
    """Batch insert multiple rows of data

    Args:
        table (str): Table name
        columns (list): List of column names
        data_list (list): List containing multiple data tuples
    """
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    columns_str = ", ".join(columns)
    placeholders = ", ".join(["?" for _ in columns])

    query = f"INSERT OR REPLACE INTO {table} ({columns_str}) VALUES ({placeholders})"
    cursor.executemany(query, data_list)

    conn.commit()
    conn.close()


def clear_table(table):
    """Clear all data from the specified table"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()

    print(f"✅ Table {table} has been cleared")


def get_team_best_hitters(
    team_id, criteria="ops", table="player_season_stats", limit=5
):
    """Get team's best hitters

    Args:
        team_id (int): Team ID
        criteria (str): Sorting criteria (avg, obp, slg, ops)
        table (str): Table name
        limit (int): Number of records to return

    Returns:
        list: List of batter records
    """
    # Note: If table is player_recent_stats, the ops column name is avg_ops
    ops_column = "avg_ops" if table == "player_recent_stats" else "ops"
    criteria = (
        ops_column if criteria == "ops" and table == "player_recent_stats" else criteria
    )

    query = f"""
        SELECT full_name, avg, obp, slg, {ops_column}
        FROM {table}
        WHERE team_id = ?
        ORDER BY {criteria} DESC
        LIMIT ?
    """

    return query_db(query, (team_id, limit))
