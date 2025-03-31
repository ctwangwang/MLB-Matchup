import requests
import datetime
import pandas as pd
import time
import streamlit as st
from config.situation_mapping import SITUATION_MAPPING


# Function to get today's date in the required format
def get_today_date():
    today = datetime.datetime.now()
    return today.strftime("%Y-%m-%d")


# Safe API request function
def safe_api_request(url, timeout=30, retries=2):
    """Execute safe API request, handle connection issues"""
    # Actual API request
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            return response.json()
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                # Wait before retry
                time.sleep(1)
                continue
            # Last attempt failed, show error
            st.sidebar.error(f"⚠️ Cannot connect to API server ({url})")
            st.sidebar.info(
                "API server is not running. Please run 'python run_api.py' in another terminal to start the API server."
            )
            return {}
        except Exception as e:
            st.sidebar.error(f"⚠️ API request error: {str(e)}")
            return {}


# Function to get today's games
@st.cache_data(ttl=60)  # Cache for 1 minute
def get_today_games(date=None):
    """
    Fetch MLB games scheduled for a specific date

    Args:
        date (str): Date in YYYY-MM-DD format. Defaults to today.

    Returns:
        list: List of game information dictionaries
    """
    if date is None:
        date = get_today_date()

    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        games = []
        if "dates" in data and len(data["dates"]) > 0:
            for game in data["dates"][0].get("games", []):
                game_id = game.get("gamePk")
                game_status = game.get("status", {}).get("abstractGameState", "")

                away_team = (
                    game.get("teams", {})
                    .get("away", {})
                    .get("team", {})
                    .get("name", "Unknown")
                )
                away_team_id = (
                    game.get("teams", {}).get("away", {}).get("team", {}).get("id", 0)
                )
                home_team = (
                    game.get("teams", {})
                    .get("home", {})
                    .get("team", {})
                    .get("name", "Unknown")
                )
                home_team_id = (
                    game.get("teams", {}).get("home", {}).get("team", {}).get("id", 0)
                )

                # Get team records if available
                away_record = (
                    game.get("teams", {}).get("away", {}).get("leagueRecord", {})
                )
                home_record = (
                    game.get("teams", {}).get("home", {}).get("leagueRecord", {})
                )

                away_record_str = (
                    f" ({away_record.get('wins', 0)}-{away_record.get('losses', 0)})"
                    if away_record
                    else ""
                )
                home_record_str = (
                    f" ({home_record.get('wins', 0)}-{home_record.get('losses', 0)})"
                    if home_record
                    else ""
                )

                # Get game time
                game_time = game.get("gameDate", "")
                if game_time:
                    try:
                        game_time_dt = datetime.datetime.fromisoformat(
                            game_time.replace("Z", "+00:00")
                        )
                        local_time = game_time_dt.astimezone()
                        game_time_str = local_time.strftime("%H:%M")
                    except:
                        game_time_str = ""
                else:
                    game_time_str = ""

                game_info = {
                    "id": game_id,
                    "away_team": away_team,
                    "away_team_id": away_team_id,
                    "home_team": home_team,
                    "home_team_id": home_team_id,
                    "matchup": f"{away_team}{away_record_str} @ {home_team}{home_record_str}",
                    "status": game_status,
                    "time": game_time_str,
                }
                games.append(game_info)

        return games
    except Exception as e:
        st.sidebar.error(f"Error fetching today's games: {e}")
        return []


# Function to fetch live score data
def get_live_data(game_id):
    """
    Fetch current score and game information for an MLB game using the MLB Stats API

    Args:
        game_id (str): The MLB game ID to track

    Returns:
        dict: Current score and game state information or None if error
    """
    url = f"https://statsapi.mlb.com/api/v1.1/game/{game_id}/feed/live"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()

        # Extract teams information
        away_team = data["gameData"]["teams"]["away"]["name"]
        away_team_abbrev = data["gameData"]["teams"]["away"].get(
            "abbreviation", away_team[:3].upper()
        )
        away_team_id = data["gameData"]["teams"]["away"]["id"]
        home_team = data["gameData"]["teams"]["home"]["name"]
        home_team_abbrev = data["gameData"]["teams"]["home"].get(
            "abbreviation", home_team[:3].upper()
        )
        home_team_id = data["gameData"]["teams"]["home"]["id"]

        # Extract current score - handling potential missing keys safely
        linescore = data["liveData"].get("linescore", {})

        # Default values if keys are missing
        away_score = 0
        home_score = 0

        # Safely get scores
        if "teams" in linescore:
            if "away" in linescore["teams"] and "runs" in linescore["teams"]["away"]:
                away_score = linescore["teams"]["away"]["runs"] or 0
            if "home" in linescore["teams"] and "runs" in linescore["teams"]["home"]:
                home_score = linescore["teams"]["home"]["runs"] or 0

        # Get current inning information
        inning = linescore.get("currentInning", "N/A")
        inning_half = linescore.get("inningHalf", "N/A")
        inning_state = linescore.get("inningState", "")

        # Get game status
        game_status = data["gameData"]["status"]["detailedState"]
        abstract_game_state = data["gameData"]["status"]["abstractGameState"]

        # Get scheduled start time
        start_time_str = data["gameData"]["datetime"].get("dateTime", "")
        start_time = None
        if start_time_str:
            try:
                start_time = datetime.datetime.fromisoformat(
                    start_time_str.replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                start_time = None

        # Get current play information if available
        current_play_info = "No active play information"
        if "currentPlay" in data["liveData"].get("plays", {}):
            current_play = data["liveData"]["plays"]["currentPlay"]
            if "result" in current_play and "description" in current_play["result"]:
                current_play_info = current_play["result"]["description"]

        # Get pitcher and batter information if available
        pitcher_info = "N/A"
        batter_info = "N/A"
        pitcher_id = None
        batter_id = None

        if "currentPlay" in data["liveData"].get("plays", {}):
            matchup = data["liveData"]["plays"]["currentPlay"].get("matchup", {})
            if "pitcher" in matchup:
                pitcher_name = matchup["pitcher"].get("fullName", "Unknown")
                pitcher_info = pitcher_name
                pitcher_id = matchup["pitcher"].get("id")
            if "batter" in matchup:
                batter_name = matchup["batter"].get("fullName", "Unknown")
                batter_info = batter_name
                batter_id = matchup["batter"].get("id")

        # Get probable pitchers when available
        probable_away_pitcher = None
        probable_home_pitcher = None
        probable_away_pitcher_id = None
        probable_home_pitcher_id = None

        if "probablePitchers" in data["gameData"]:
            pitchers = data["gameData"].get("probablePitchers", {})
            if "away" in pitchers:
                probable_away_pitcher = pitchers["away"].get("fullName", "TBD")
                probable_away_pitcher_id = pitchers["away"].get("id")
            if "home" in pitchers:
                probable_home_pitcher = pitchers["home"].get("fullName", "TBD")
                probable_home_pitcher_id = pitchers["home"].get("id")

        # Get splits information if available
        batter_situation = None
        pitcher_situation = None
        men_on_base_situation = None

        if "currentPlay" in data["liveData"].get("plays", {}):
            matchup = data["liveData"]["plays"]["currentPlay"].get("matchup", {})
            splits = matchup.get("splits", {})

            # Map the splits to situation codes and descriptions
            batter_split = splits.get("batter", "")
            pitcher_split = splits.get("pitcher", "")
            men_on_split = splits.get("menOnBase", "")

            batter_situation = {
                "code": SITUATION_MAPPING["batter"]
                .get(batter_split, {})
                .get("code", "Unknown"),
                "description": SITUATION_MAPPING["batter"]
                .get(batter_split, {})
                .get("description", "Unknown"),
            }

            pitcher_situation = {
                "code": SITUATION_MAPPING["pitcher"]
                .get(pitcher_split, {})
                .get("code", "Unknown"),
                "description": SITUATION_MAPPING["pitcher"]
                .get(pitcher_split, {})
                .get("description", "Unknown"),
            }

            men_on_base_situation = {
                "code": SITUATION_MAPPING["menOnBase"]
                .get(men_on_split, {})
                .get("code", "Unknown"),
                "description": SITUATION_MAPPING["menOnBase"]
                .get(men_on_split, {})
                .get("description", "Unknown"),
            }

        if batter_situation["code"] == "Unknown":
            batter_situation = None
        if pitcher_situation["code"] == "Unknown":
            pitcher_situation = None
        if men_on_base_situation["code"] == "Unknown":
            men_on_base_situation = None

        # Get inning scores safely
        inning_scores = []
        innings = linescore.get("innings", [])
        for i in range(1, 10):  # Standard 9 innings
            inning_data = innings[i - 1] if i <= len(innings) else {}

            # Safely get inning scores with proper type handling
            away_inning_score = inning_data.get("away", {}).get("runs", "-")
            home_inning_score = inning_data.get("home", {}).get("runs", "-")

            # Convert to int if possible, otherwise keep as string
            try:
                away_inning_score = (
                    int(away_inning_score) if str(away_inning_score).isdigit() else "-"
                )
                home_inning_score = (
                    int(home_inning_score) if str(home_inning_score).isdigit() else "-"
                )
            except (ValueError, TypeError):
                away_inning_score = "-"
                home_inning_score = "-"

            inning_scores.append(
                {"inning": i, "away": away_inning_score, "home": home_inning_score}
            )

        # Get base runners information
        bases_occupied = []
        offense = linescore.get("offense", {})
        if offense:
            if offense.get("first"):
                bases_occupied.append(1)
            if offense.get("second"):
                bases_occupied.append(2)
            if offense.get("third"):
                bases_occupied.append(3)

        # Get outs
        outs = linescore.get("outs", 0) if abstract_game_state == "Live" else "-"

        # Get balls and strikes count
        balls = linescore.get("balls", 0) if abstract_game_state == "Live" else "-"
        strikes = linescore.get("strikes", 0) if abstract_game_state == "Live" else "-"

        # Extract batter hot/cold zones if available
        batter_hot_cold_zones = None
        if "currentPlay" in data["liveData"].get("plays", {}):
            matchup = data["liveData"]["plays"]["currentPlay"].get("matchup", {})
            batter_hot_cold_zones = matchup.get("batterHotColdZoneStats", None)

        # Get batter handedness
        batter_handedness = None
        if "currentPlay" in data["liveData"].get("plays", {}):
            matchup = data["liveData"]["plays"]["currentPlay"].get("matchup", {})
            bat_side = matchup.get("batSide", {})
            if bat_side:
                batter_handedness = bat_side.get("code")  # This will be "R" or "L"

        return {
            "away_team": away_team,
            "away_team_abbrev": away_team_abbrev,
            "away_team_id": away_team_id,
            "home_team": home_team,
            "home_team_abbrev": home_team_abbrev,
            "home_team_id": home_team_id,
            "away_score": away_score,
            "home_score": home_score,
            "inning": inning,
            "inning_half": inning_half,
            "inning_state": inning_state,
            "status": game_status,
            "abstract_game_state": abstract_game_state,
            "start_time": start_time,
            "current_play": current_play_info,
            "pitcher": pitcher_info,
            "pitcher_id": pitcher_id,
            "batter": batter_info,
            "batter_id": batter_id,
            "probable_away_pitcher": probable_away_pitcher,
            "probable_away_pitcher_id": probable_away_pitcher_id,
            "probable_home_pitcher": probable_home_pitcher,
            "probable_home_pitcher_id": probable_home_pitcher_id,
            "inning_scores": inning_scores,
            "bases_occupied": bases_occupied,
            "outs": outs,
            "balls": balls,
            "strikes": strikes,
            "batter_situation": batter_situation,
            "pitcher_situation": pitcher_situation,
            "men_on_base_situation": men_on_base_situation,
            "batter_hot_cold_zones": batter_hot_cold_zones,
            "batter_handedness": batter_handedness,
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None
    except (KeyError, IndexError, TypeError) as e:
        st.error(f"Error parsing data: {str(e)}")
        return None


# Function to get batter vs pitcher analysis
def get_batter_analysis(
    team_id,
    pitcher_id,
    API_IMPORTS_SUCCESS,
    API_BASE_URL,
    get_vs_pitcher_stats,
    get_batter_season_stats,
    get_batter_vs_pitcher_stats,
):
    """
    Get batter analysis against a specific pitcher

    Args:
        team_id (int): Team ID to analyze
        pitcher_id (int): Pitcher to analyze against
        API_IMPORTS_SUCCESS (bool): Whether API imports succeeded
        API_BASE_URL (str): Base URL for API
        get_vs_pitcher_stats: Function to get vs pitcher stats
        get_batter_season_stats: Function to get player season stats
        get_batter_vs_pitcher_stats: Function to get batter vs pitcher stats

    Returns:
        dict: Analysis results
    """
    if not API_IMPORTS_SUCCESS:
        # Return mock data for demonstration
        return {
            "best_season_hitter": ("Aaron Judge", 0.310, 0.425, 0.600, 1.025),
            "best_recent_hitter": ("Juan Soto", 0.325, 0.480, 0.590, 1.070),
            "best_vs_pitcher_hitter": ("Giancarlo Stanton", 0.333, 0.400, 0.778, 1.178),
            "all_hitters_vs_pitcher": [
                ("Giancarlo Stanton", 0.333, 0.400, 0.778, 1.178),
                ("Aaron Judge", 0.300, 0.417, 0.700, 1.117),
                ("Anthony Rizzo", 0.278, 0.350, 0.500, 0.850),
            ],
        }

    # Try to get from API first
    try:
        data = safe_api_request(
            f"{API_BASE_URL}/matchup?team_id={team_id}&pitcher_id={pitcher_id}"
        )
        if data:
            return data
    except Exception as e:
        st.warning(f"Could not connect to analysis API: {e}")

    # If API fails, try to calculate directly
    try:
        # Fallback to direct calculation
        return get_batter_vs_pitcher_stats(team_id, pitcher_id)
    except Exception as e:
        st.error(f"Error calculating batter stats: {e}")
        return {}
