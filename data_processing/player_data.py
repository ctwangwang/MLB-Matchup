# data_processing/player_data.py
"""
Player Data Processing Module: Handles retrieval, updating, and analysis of player data
"""

import time
from datetime import datetime
from config.team_config import MLB_TEAMS
from database.db_operations import clear_table, insert_or_replace_data
from api.mlb_api import (
    get_team_roster,
    get_batter_season_stats,
    get_player_recent_games,
    get_vs_pitcher_stats,
)


def update_player_season_data(season=None):
    """
    Update all players' season data

    Args:
        season (int, optional): Season year, if not provided uses data from the previous year
    """
    # If season is not provided, use data from the previous year
    if season is None:
        season = datetime.now().year - 1

    # Clear previous data
    clear_table("player_season_stats")

    for team_name, team_id in MLB_TEAMS.items():
        print(f"📥 Updating {season} team roster: {team_name}")

        # Get team player roster - using current year's roster
        players = get_team_roster(team_id, season=datetime.now().year)

        for player in players:
            player_id = player["player_id"]
            full_name = player["full_name"]

            print(f"🔍 Querying {full_name} ({player_id})'s {season} data")

            # Get season data
            avg, obp, slg, ops = get_batter_season_stats(player_id, season=season)

            # Insert data
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

            time.sleep(0.5)  # Avoid API overload

    print(f"✅ {season} data update completed!")


def update_player_recent_data(games_count=5, season=None):
    """
    Update all players' recent game data

    Args:
        games_count (int): Number of recent games to analyze
        season (int, optional): Season year, if not provided uses current year
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    # Clear previous data
    clear_table("player_recent_stats")

    for team_name, team_id in MLB_TEAMS.items():
        print(f"📥 Updating {season} {team_name}'s last {games_count} games data")

        # Get team player roster
        players = get_team_roster(team_id, season=season)

        for player in players:
            player_id = player["player_id"]
            full_name = player["full_name"]

            print(
                f"🔍 Querying {full_name} ({player_id})'s last {games_count} games data"
            )

            # Get recent games data
            _, avg, obp, slg, ops = get_player_recent_games(
                player_id, season=season, games_count=games_count
            )

            # Insert data
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

            time.sleep(0.5)  # Avoid API overload

    print(f"✅ {season}'s last {games_count} games data update completed!")


def get_batter_vs_pitcher_stats(team_id, pitcher_id):
    """
    Get all batters' stats from a team against a specific pitcher

    Args:
        team_id (int): Team ID
        pitcher_id (int): Pitcher ID

    Returns:
        dict: Dictionary containing analysis results
    """
    from database.db_operations import query_db

    # Query all batters from the team
    hitters = query_db(
        "SELECT player_id, full_name FROM player_season_stats WHERE team_id=?",
        (team_id,),
    )

    all_stats = []
    best_vs_pitcher = None

    # Get data for each batter against the pitcher
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

            # Find the batter with highest OPS against this pitcher
            if best_vs_pitcher is None or ops > best_vs_pitcher[4]:
                best_vs_pitcher = hitter_stats

    # Sort by OPS from high to low
    all_stats = sorted(all_stats, key=lambda x: x[4], reverse=True)

    # Query the batter with highest season OPS
    best_season = query_db(
        "SELECT full_name, avg, obp, slg, ops FROM player_season_stats WHERE team_id=? ORDER BY ops DESC LIMIT 1",
        (team_id,),
        one=True,
    )

    # Query the batter with highest OPS in the last 5 games
    best_recent = query_db(
        "SELECT full_name, avg, obp, slg, avg_ops FROM player_recent_stats WHERE team_id=? ORDER BY avg_ops DESC LIMIT 1",
        (team_id,),
        one=True,
    )

    # Assemble return results
    return {
        "best_season_hitter": tuple(best_season) if best_season else None,
        "best_recent_hitter": tuple(best_recent) if best_recent else None,
        "best_vs_pitcher_hitter": best_vs_pitcher,
        "all_hitters_vs_pitcher": all_stats,
    }
