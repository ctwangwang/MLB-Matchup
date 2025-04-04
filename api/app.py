# api/app.py
"""
FastAPI Application Module: Handles API requests and responses
"""

from fastapi import FastAPI, HTTPException
from config.team_config import MLB_TEAMS
from data_processing.player_data import get_batter_vs_pitcher_stats

# Create FastAPI application
app = FastAPI(title="MLB Stats API")


@app.get("/")
def read_root():
    """API homepage"""
    return {"message": "Welcome to MLB Stats API"}


@app.get("/matchup")
def get_matchup(team_id: int, pitcher_id: int):
    """
    Get batter vs pitcher matchup data

    Args:
        team_id (int): Team ID
        pitcher_id (int): Pitcher ID

    Returns:
        dict: Batter vs pitcher matchup statistics
    """
    try:
        # Get team name
        team_name = next(
            (name for name, id in MLB_TEAMS.items() if id == team_id), "Unknown Team"
        )

        # Get matchup data
        matchup_data = get_batter_vs_pitcher_stats(team_id, pitcher_id)

        # Add team name to return data
        matchup_data["team_name"] = team_name

        return matchup_data

    except Exception as e:
        print(f"⚠️ API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/games/today")
def get_today_games():
    """Get today's games"""
    from api.mlb_api import get_today_games as fetch_games

    try:
        games = fetch_games()
        return {"games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{game_id}/pitchers")
def get_game_pitchers(game_id: int):
    """Get pitchers in a game"""
    from api.mlb_api import get_game_pitchers as fetch_pitchers

    try:
        pitchers = fetch_pitchers(game_id)
        return pitchers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/team/{team_id}/pitchers")
def get_team_pitchers_api(team_id: int):
    """Get team pitchers list"""
    from api.mlb_api import get_team_pitchers as fetch_team_pitchers

    try:
        pitchers = fetch_team_pitchers(team_id)
        return {"pitchers": pitchers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
