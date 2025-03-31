# api/app.py
"""
FastAPI 應用模組：處理API請求和響應
"""

from fastapi import FastAPI, HTTPException
from config.team_config import MLB_TEAMS
from data_processing.player_data import get_batter_vs_pitcher_stats

# 創建 FastAPI 應用
app = FastAPI(title="MLB Stats API")


@app.get("/")
def read_root():
    """API首頁"""
    return {"message": "Welcome to MLB Stats API"}


@app.get("/matchup")
def get_matchup(team_id: int, pitcher_id: int):
    """
    獲取打者對投手的對戰數據

    Args:
        team_id (int): 球隊ID
        pitcher_id (int): 投手ID

    Returns:
        dict: 打者對投手的對戰統計
    """
    try:
        # 獲取球隊名稱
        team_name = next(
            (name for name, id in MLB_TEAMS.items() if id == team_id), "Unknown Team"
        )

        # 獲取對戰數據
        matchup_data = get_batter_vs_pitcher_stats(team_id, pitcher_id)

        # 添加球隊名稱到返回數據
        matchup_data["team_name"] = team_name

        return matchup_data

    except Exception as e:
        print(f"⚠️ API錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/games/today")
def get_today_games():
    """獲取今日比賽"""
    from api.mlb_api import get_today_games as fetch_games

    try:
        games = fetch_games()
        return {"games": games}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{game_id}/pitchers")
def get_game_pitchers(game_id: int):
    """獲取比賽中的投手"""
    from api.mlb_api import get_game_pitchers as fetch_pitchers

    try:
        pitchers = fetch_pitchers(game_id)
        return pitchers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/team/{team_id}/pitchers")
def get_team_pitchers_api(team_id: int):
    """獲取球隊投手列表"""
    from api.mlb_api import get_team_pitchers as fetch_team_pitchers

    try:
        pitchers = fetch_team_pitchers(team_id)
        return {"pitchers": pitchers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
