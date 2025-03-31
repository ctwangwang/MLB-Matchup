# database/db_operations.py
"""
數據庫操作模組：包含查詢、更新、刪除等數據庫操作函數
"""

import sqlite3
from .db_setup import get_db_path


def query_db(query, params=(), one=False):
    """執行SQL查詢並返回結果"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # 啟用行工廠使結果能用列名訪問
    cur = conn.cursor()
    cur.execute(query, params)
    results = cur.fetchall()
    conn.close()

    # 如果請求單一結果或只有一個結果，直接返回
    if one or (len(results) == 1 and one is None):
        return results[0] if results else None
    return results


def insert_or_replace_data(table, data):
    """插入或替換數據庫中的記錄

    Args:
        table (str): 表格名稱
        data (dict): 列名與值的字典
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
    """批量插入多行數據

    Args:
        table (str): 表格名稱
        columns (list): 列名列表
        data_list (list): 包含多個數據元組的列表
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
    """清空指定表格的所有數據"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute(f"DELETE FROM {table}")

    conn.commit()
    conn.close()

    print(f"✅ 表格 {table} 已清空")


def get_team_best_hitters(
    team_id, criteria="ops", table="player_season_stats", limit=5
):
    """獲取球隊最佳打者

    Args:
        team_id (int): 球隊ID
        criteria (str): 排序標準 (avg, obp, slg, ops)
        table (str): 表格名稱
        limit (int): 返回記錄數量

    Returns:
        list: 打者記錄的列表
    """
    # 注意：若表格為player_recent_stats，ops列名為avg_ops
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
