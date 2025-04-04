# api/mlb_api.py
"""
MLB API Request Module: Handles all interactions with the MLB API
"""

import requests
from datetime import datetime
import pytz


def get_today_games():
    """
    Get today's games

    Returns:
        list: List of today's games
    """

    # Get current date (YYYY-MM-DD format)
    pacific_tz = pytz.timezone("America/Los_Angeles")
    today_date = datetime.now(pacific_tz).strftime("%Y-%m-%d")

    # Use the correct API URL
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_date}"
    response = requests.get(url).json()

    # Check if there are any games
    if "dates" not in response or not response["dates"]:
        return []  # Return empty list when no games

    games = response["dates"][0].get("games", [])

    return [
        {
            "game_id": game["gamePk"],
            "away_team": game["teams"]["away"]["team"]["name"],
            "away_team_id": game["teams"]["away"]["team"]["id"],
            "home_team": game["teams"]["home"]["team"]["name"],
            "home_team_id": game["teams"]["home"]["team"]["id"],
        }
        for game in games
    ]


def get_player_info(player_id):
    """
    Get player basic information

    Args:
        player_id (int): Player ID

    Returns:
        dict: Dictionary containing player ID and full name, returns None if not found
    """
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    response = requests.get(url).json()

    try:
        player = response["people"][0]
        return {"player_id": player["id"], "full_name": player["fullName"]}
    except (KeyError, IndexError):
        return None


def get_team_roster(team_id, season=None):
    """
    Get team roster

    Args:
        team_id (int): Team ID
        season (int, optional): Season year, uses current year if not provided

    Returns:
        list: Team roster list
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?season={season}"
    response = requests.get(url).json()
    players = response.get("roster", [])

    return [
        {
            "player_id": player["person"]["id"],
            "full_name": player["person"]["fullName"],
            "position": player["position"]["abbreviation"],
        }
        for player in players
    ]


def get_team_pitchers(team_id, season=None):
    """
    Get team pitchers list

    Args:
        team_id (int): Team ID
        season (int, optional): Season year, uses current year if not provided

    Returns:
        list: Pitchers list
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?season={season}"
    response = requests.get(url).json()

    pitchers = []
    for player in response.get("roster", []):
        if player["position"]["abbreviation"] in ["P"]:  # Only filter pitchers
            pitchers.append(
                {
                    "pitcher_id": player["person"]["id"],
                    "full_name": player["person"]["fullName"],
                }
            )

    return pitchers


def get_game_pitchers(game_id):
    """
    Get all pitchers in a game

    Args:
        game_id (int): Game ID

    Returns:
        dict: Dictionary containing home and away team pitchers
    """
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    response = requests.get(url).json()

    pitchers = {"away": [], "home": []}

    try:
        # Get away team pitchers information
        away_pitchers_ids = response["teams"]["away"].get("pitchers", [])
        home_pitchers_ids = response["teams"]["home"].get("pitchers", [])

        # Get detailed information for all pitchers
        for pitcher_id in away_pitchers_ids:
            pitcher_info = get_player_info(pitcher_id)
            if pitcher_info:
                pitchers["away"].append(
                    {"pitcher_id": pitcher_id, "full_name": pitcher_info["full_name"]}
                )

        for pitcher_id in home_pitchers_ids:
            pitcher_info = get_player_info(pitcher_id)
            if pitcher_info:
                pitchers["home"].append(
                    {"pitcher_id": pitcher_id, "full_name": pitcher_info["full_name"]}
                )

        return pitchers
    except (KeyError, IndexError) as e:
        print(f"Error fetching pitchers: {e}")
        return {"away": [], "home": []}


def get_game_details(game_id):
    """
    Get detailed game information

    Args:
        game_id (int): Game ID

    Returns:
        dict: Dictionary containing game details
    """
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    response = requests.get(url).json()

    # Get starting pitchers ID and name
    try:
        away_pitcher_id = response["teams"]["away"]["pitchers"][0]
        home_pitcher_id = response["teams"]["home"]["pitchers"][0]

        # Get complete pitcher information
        away_pitcher_info = get_player_info(away_pitcher_id)
        home_pitcher_info = get_player_info(home_pitcher_id)

        return {
            "away_pitcher_id": away_pitcher_id,
            "away_pitcher_name": away_pitcher_info["full_name"]
            if away_pitcher_info
            else "Unknown",
            "home_pitcher_id": home_pitcher_id,
            "home_pitcher_name": home_pitcher_info["full_name"]
            if home_pitcher_info
            else "Unknown",
        }
    except (KeyError, IndexError):
        # Return empty values if starting pitchers cannot be obtained
        return {
            "away_pitcher_id": None,
            "away_pitcher_name": "Not announced",
            "home_pitcher_id": None,
            "home_pitcher_name": "Not announced",
        }


def get_batter_season_stats(player_id, season=None):
    """
    Get player's season batting statistics

    Args:
        player_id (int): Player ID
        season (int, optional): Season year, uses current year if not provided

    Returns:
        tuple: (AVG, OBP, SLG, OPS, BABIP, AB/HR, HR, RBI)
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&season={season}&group=hitting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("avg", None),  # Batting Average AVG
            data.get("obp", None),  # On-base Percentage OBP
            data.get("slg", None),  # Slugging Percentage SLG
            data.get("ops", None),  # OPS
            data.get("babip", None),  # Batting Average on Balls in Play BABIP
            data.get("atBatsPerHomeRun", None),  # At Bats Per Home Run AB/HR
            data.get("homeRuns", None),  # Home Runs HR
            data.get("rbi", None),  # Runs Batted In RBI
        )

    return (None, None, None, None, None, None, None, None)  # Return None when no data


def get_pitcher_season_stats(pitcher_id, season=None):
    """
    Get pitcher's season statistics

    Args:
        pitcher_id (int): Pitcher ID
        season (int, optional): Season year, uses current year if not provided

    Returns:
        tuple: (AVG against, OPS against, ERA, WHIP, K/9, BB/9, H/9, HR/9, Wins, Losses, Holds, Saves)
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&season={season}&group=pitching"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("avg", None),  # Batting Average Against AVG
            data.get("ops", None),  # OPS Against
            data.get("era", None),  # Earned Run Average ERA
            data.get("whip", None),  # Walks plus Hits per Inning Pitched WHIP
            data.get("strikeoutsPer9Inn", None),  # Strikeouts per 9 Innings K/9
            data.get("walksPer9Inn", None),  # Walks per 9 Innings BB/9
            data.get("hitsPer9Inn", None),  # Hits per 9 Innings H/9
            data.get("homeRunsPer9", None),  # Home Runs per 9 Innings HR/9
            data.get("wins", None),  # Wins W
            data.get("losses", None),  # Losses L
            data.get("holds", None),  # Holds HLD
            data.get("saves", None),  # Saves SV
        )

    return (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )  # Return None when no data


def get_player_recent_games(player_id, season=None, games_count=5):
    """
    Get player's hitting statistics from recent games and calculate averages

    Args:
        player_id (int): Player ID
        season (int, optional): Season year, uses current year if not provided
        games_count (int): Number of games to calculate

    Returns:
        tuple: (player ID, average AVG, average OBP, average SLG, average OPS)
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&season={season}&gameType=S,R&group=hitting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats:
        hits, at_bats, walks, hbp, sac_fly, total_bases = (
            0,
            0,
            0,
            0,
            0,
            0,
        )  # Initialize calculation variables

        for game in stats[0]["splits"][-games_count:]:  # Get the most recent N games
            stat = game["stat"]
            hits += int(stat.get("hits", 0))  # Hits
            at_bats += int(stat.get("atBats", 0))  # At Bats
            walks += int(stat.get("baseOnBalls", 0))  # Walks
            hbp += int(stat.get("hitByPitch", 0))  # Hit By Pitch
            sac_fly += int(stat.get("sacFlies", 0))  # Sacrifice Flies
            total_bases += int(stat.get("totalBases", 0))  # Total Bases

        # Manually calculate AVG, OBP, SLG
        avg = hits / at_bats if at_bats else 0  # Batting Average AVG
        obp = (
            (hits + walks + hbp) / (at_bats + walks + hbp + sac_fly)
            if (at_bats + walks + hbp + sac_fly)
            else 0
        )  # On-base Percentage OBP
        slg = total_bases / at_bats if at_bats else 0  # Slugging Percentage SLG
        ops = obp + slg  # Manually calculate OPS

        return player_id, avg, obp, slg, ops

    return player_id, 0, 0, 0, 0  # Return 0 when no data


def get_vs_pitcher_stats(player_id, pitcher_id):
    """
    Get batter's historical statistics against a pitcher

    Args:
        player_id (int): Batter ID
        pitcher_id (int): Pitcher ID

    Returns:
        dict: Dictionary containing statistics, returns None if no data
    """
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=vsPlayer&group=hitting&opposingPlayerId={pitcher_id}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"⚠️ API Request Failed: {response.status_code}, URL: {url}")
        return None

    data = response.json()

    # Ensure stats key exists
    if "stats" not in data or not isinstance(data["stats"], list):
        print(f"⚠️ Invalid API response format: {data}")
        return None

    for stat_item in data["stats"]:
        # Extract only career data
        if stat_item["type"]["displayName"] == "vsPlayerTotal":
            splits = stat_item.get("splits", [])
            if splits:
                stat = splits[0]["stat"]
                return {
                    "avg": round(float(stat.get("avg", "0.000")), 3),
                    "obp": round(float(stat.get("obp", "0.000")), 3),
                    "slg": round(float(stat.get("slg", "0.000")), 3),
                    "ops": round(float(stat.get("ops", "0.000")), 3),
                }

    print(f"⚠️ No career stats found for batter {player_id} vs pitcher {pitcher_id}")
    return None


# Add these functions to mlb_api.py
def get_batter_situation_stats(batter_id, situation_code, season=None):
    """
    Get batter stats in specific situations (vs LHP/RHP)

    Args:
        batter_id (int): Batter MLB ID
        situation_code (str): Situation code (vr/vl)
        season (int, optional): Season year, defaults to previous season if None

    Returns:
        dict: Contains AVG, OBP, SLG, OPS or None if not available
    """
    if season is None:
        # Default to current season rather than previous
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats?stats=statSplits&season={season}&group=hitting&sitCodes={situation_code}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "stats" in data and data["stats"]:
            splits = data["stats"][0].get("splits", [])
            if splits:
                stats = splits[0]["stat"]
                return {
                    "avg": round(float(stats.get("avg", 0)), 3),
                    "obp": round(float(stats.get("obp", 0)), 3),
                    "slg": round(float(stats.get("slg", 0)), 3),
                    "ops": round(float(stats.get("ops", 0)), 3),
                    "situation": situation_code,
                    "season": season,
                }
    except Exception as e:
        print(f"Error getting batter situation stats: {e}")

    return None


def get_pitcher_situation_stats(pitcher_id, situation_code, season=None):
    """
    Get pitcher stats in specific situations (vs LHB/RHB or men on base)

    Args:
        pitcher_id (int): Pitcher MLB ID
        situation_code (str): Situation code (vr/vl/risp)
        season (int, optional): Season year, defaults to current season if None

    Returns:
        dict: Contains AVG, OBP, SLG, OPS allowed or None if not available
    """
    if season is None:
        # Default to current season rather than previous
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=statSplits&season={season}&group=pitching&sitCodes={situation_code}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "stats" in data and data["stats"]:
            splits = data["stats"][0].get("splits", [])
            if splits:
                stats = splits[0]["stat"]
                return {
                    "avg": round(float(stats.get("avg", 0)), 3),
                    "obp": round(float(stats.get("obp", 0)), 3),
                    "slg": round(float(stats.get("slg", 0)), 3),
                    "ops": round(float(stats.get("ops", 0)), 3),
                    "situation": situation_code,
                    "season": season,
                }
    except Exception as e:
        print(f"Error getting pitcher situation stats: {e}")

    return None


def get_pitcher_sabermetrics(pitcher_id, season=None):
    """
    Get pitcher advanced statistics (Sabermetrics)

    Args:
        pitcher_id (int): Pitcher ID
        season (int, optional): Season year, uses current year if not provided

    Returns:
        tuple: (FIP, FIP-, WAR, ERA-, xFIP, ra9WAR, RAR, EXLI)
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=sabermetrics&season={season}&group=pitching"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("fip", None),  # Fielding Independent Pitching FIP
            data.get("fipMinus", None),  # FIP- (FIP relative to league average)
            data.get("war", None),  # Wins Above Replacement WAR
            data.get("eraMinus", None),  # ERA- (ERA relative to league average)
            data.get("xfip", None),  # Expected Fielding Independent Pitching xFIP
            data.get("ra9War", None),  # RA9-based WAR
            data.get("rar", None),  # Runs Above Replacement
            data.get("exli", None),  # Exited Leverage Index
        )

    return (None, None, None, None, None, None, None, None)  # Return None when no data


def get_batter_sabermetrics(batter_id, season=None):
    """
    Get batter advanced statistics (Sabermetrics)

    Args:
        batter_id (int): Batter ID
        season (int, optional): Season year, uses current year if not provided

    Returns:
        tuple: (wRC, wRC+, WAR, wOBA, wRAA, Batting, Spd, UBR)
    """
    # If season is not provided, use current year
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats?stats=sabermetrics&season={season}&group=batting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("wRc", None),  # Weighted Runs Created wRC
            data.get("wRcPlus", None),  # wRC+ (relative to league average)
            data.get("war", None),  # Wins Above Replacement WAR
            data.get("woba", None),  # Weighted On-base Average wOBA
            data.get("wRaa", None),  # Weighted Runs Above Average wRAA
            data.get("batting", None),  # Batting component of WAR
            data.get("spd", None),  # Speed metric Spd
            data.get("ubr", None),  # Ultimate Base Running UBR
        )

    return (None, None, None, None, None, None, None, None)  # Return None when no data
