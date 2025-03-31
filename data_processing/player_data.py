# data_processing/player_data.py
"""
球員數據處理模組：處理球員資料的獲取、更新和分析
"""

import time
from config.team_config import MLB_TEAMS
from database.db_operations import clear_table, insert_or_replace_data
from api.mlb_api import (
    get_team_roster,
    get_batter_season_stats,
    get_player_recent_games,
    get_vs_pitcher_stats,
)


def update_player_season_data(season=2024):
    """
    更新所有球員的賽季數據

    Args:
        season (int): 賽季年份
    """
    # 清空原先的數據
    clear_table("player_season_stats")

    for team_name, team_id in MLB_TEAMS.items():
        print(f"📥 更新 {season} 年球隊名單: {team_name}")

        # 獲取隊伍球員名單
        players = get_team_roster(team_id, season=season + 1)  # 使用下一年的名單

        for player in players:
            player_id = player["player_id"]
            full_name = player["full_name"]

            print(f"🔍 查詢 {full_name} ({player_id}) 的 {season} 年數據")

            # 獲取賽季數據
            avg, obp, slg, ops = get_batter_season_stats(player_id, season=season)

            # 插入數據
            player_data = {
                "player_id": player_id,
                "full_name": full_name,
                "team_id": team_id,
                "team_name": team_name,
                "avg": avg,
                "obp": obp,
                "slg": slg,
                "ops": ops,
            }
            insert_or_replace_data("player_season_stats", player_data)

            time.sleep(0.5)  # 避免API過載

    print(f"✅ {season} 年數據更新完成！")


def update_player_recent_data(games_count=5, season=2025):
    """
    更新所有球員的最近比賽數據

    Args:
        games_count (int): 要分析的最近比賽場數
        season (int): 賽季年份
    """
    # 清空原先的數據
    clear_table("player_recent_stats")

    for team_name, team_id in MLB_TEAMS.items():
        print(f"📥 更新 {season} 年 {team_name} 最近 {games_count} 場比賽數據")

        # 獲取隊伍球員名單
        players = get_team_roster(team_id, season=season)

        for player in players:
            player_id = player["player_id"]
            full_name = player["full_name"]

            print(f"🔍 查詢 {full_name} ({player_id}) 的最近 {games_count} 場比賽數據")

            # 獲取最近比賽數據
            _, avg, obp, slg, ops = get_player_recent_games(
                player_id, season=season, games_count=games_count
            )

            # 插入數據
            player_data = {
                "player_id": player_id,
                "full_name": full_name,
                "team_id": team_id,
                "avg": avg,
                "obp": obp,
                "slg": slg,
                "avg_ops": ops,
            }
            insert_or_replace_data("player_recent_stats", player_data)

            time.sleep(0.5)  # 避免API過載

    print(f"✅ {season} 最近 {games_count} 場比賽數據更新完成！")


def get_batter_vs_pitcher_stats(team_id, pitcher_id):
    """
    獲取球隊所有打者對特定投手的數據

    Args:
        team_id (int): 球隊ID
        pitcher_id (int): 投手ID

    Returns:
        dict: 包含分析結果的字典
    """
    from database.db_operations import query_db

    # 查詢該隊所有打者
    hitters = query_db(
        "SELECT player_id, full_name FROM player_season_stats WHERE team_id=?",
        (team_id,),
    )

    all_stats = []
    best_vs_pitcher = None

    # 逐一獲取打者對該投手的數據
    for hitter in hitters:
        player_id = hitter["player_id"]
        player_name = hitter["full_name"]

        vs_stats = get_vs_pitcher_stats(player_id, pitcher_id)

        if vs_stats:
            avg, obp, slg, ops = (
                vs_stats["avg"],
                vs_stats["obp"],
                vs_stats["slg"],
                vs_stats["ops"],
            )
            hitter_stats = (player_name, avg, obp, slg, ops)
            all_stats.append(hitter_stats)

            # 找到對該投手OPS最高的打者
            if best_vs_pitcher is None or ops > best_vs_pitcher[4]:
                best_vs_pitcher = hitter_stats

    # 按照OPS由高到低排序
    all_stats = sorted(all_stats, key=lambda x: x[4], reverse=True)

    # 查詢當季OPS最高的打者
    best_season = query_db(
        "SELECT full_name, avg, obp, slg, ops FROM player_season_stats WHERE team_id=? ORDER BY ops DESC LIMIT 1",
        (team_id,),
        one=True,
    )

    # 查詢最近5場OPS最高的打者
    best_recent = query_db(
        "SELECT full_name, avg, obp, slg, avg_ops FROM player_recent_stats WHERE team_id=? ORDER BY avg_ops DESC LIMIT 1",
        (team_id,),
        one=True,
    )

    # 組裝返回結果
    return {
        "best_season_hitter": tuple(best_season) if best_season else None,
        "best_recent_hitter": tuple(best_recent) if best_recent else None,
        "best_vs_pitcher_hitter": best_vs_pitcher,
        "all_hitters_vs_pitcher": all_stats,
    }
