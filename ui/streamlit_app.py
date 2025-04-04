# ui/streamlit_app.py
import os
import sys

# Set project root directory path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import streamlit as st
import pandas as pd
import requests
import time
from config.team_config import MLB_TEAMS

# Check if using mock data
USE_MOCK_DATA = os.environ.get("USE_MOCK_DATA") == "1"

# API base URL
# API_BASE_URL = "http://localhost:8000"
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


# Mock data functions
def get_mock_team_pitchers():
    """Return mock team pitcher data"""
    return {
        "pitchers": [
            {"pitcher_id": 123456, "full_name": "Clayton Kershaw"},
            {"pitcher_id": 234567, "full_name": "Walker Buehler"},
            {"pitcher_id": 345678, "full_name": "Julio Urías"},
        ]
    }


def get_mock_today_games():
    """Return mock today's games data"""
    return {
        "games": [
            {
                "game_id": 1,
                "away_team": "New York Yankees",
                "away_team_id": 147,
                "home_team": "Boston Red Sox",
                "home_team_id": 111,
            },
            {
                "game_id": 2,
                "away_team": "Los Angeles Dodgers",
                "away_team_id": 119,
                "home_team": "San Francisco Giants",
                "home_team_id": 137,
            },
        ]
    }


def get_mock_game_pitchers():
    """Return mock game pitchers data"""
    return {
        "away": [
            {"pitcher_id": 123456, "full_name": "Gerrit Cole"},
            {"pitcher_id": 234567, "full_name": "Luis Severino"},
        ],
        "home": [
            {"pitcher_id": 345678, "full_name": "Chris Sale"},
            {"pitcher_id": 456789, "full_name": "Nick Pivetta"},
        ],
    }


def get_mock_matchup_data():
    """Return mock matchup data"""
    return {
        "team_name": "New York Yankees",
        "best_season_hitter": ("Aaron Judge", 0.310, 0.425, 0.600, 1.025),
        "best_recent_hitter": ("Juan Soto", 0.325, 0.480, 0.590, 1.070),
        "best_vs_pitcher_hitter": ("Giancarlo Stanton", 0.333, 0.400, 0.778, 1.178),
        "all_hitters_vs_pitcher": [
            ("Giancarlo Stanton", 0.333, 0.400, 0.778, 1.178),
            ("Aaron Judge", 0.300, 0.417, 0.700, 1.117),
            ("Anthony Rizzo", 0.278, 0.350, 0.500, 0.850),
        ],
    }


# Safe API request function
def safe_api_request(url, timeout=10, retries=2):
    """Execute safe API request, handling connection issues"""
    global USE_MOCK_DATA  # Declare global variable first

    if USE_MOCK_DATA:
        # Use mock data
        if "games/today" in url:
            return get_mock_today_games()
        elif "/game/" in url and "/pitchers" in url:
            return get_mock_game_pitchers()
        elif "/team/" in url and "/pitchers" in url:
            return get_mock_team_pitchers()
        elif "matchup" in url:
            return get_mock_matchup_data()
        return {}

    # Actual API request
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            return response.json()
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                # Wait before retrying
                time.sleep(1)
                continue
            # Last attempt failed, display error
            st.error(f"⚠️ Unable to connect to API server ({url})")
            st.info(
                "API server is not running. Please run 'python run_api.py' in another terminal to start the API server."
            )
            # Use mock data
            USE_MOCK_DATA = True
            return safe_api_request(url)
        except Exception as e:
            st.error(f"⚠️ API request error: {str(e)}")
            return {}


def setup_page_config():
    """Set page configuration and styles"""
    st.set_page_config(
        page_title="MLB Matchup Data Analysis", page_icon="⚾", layout="wide"
    )

    # Custom CSS styles
    st.markdown(
        """
        <style>
        h1 { font-size: 60px !important; }
        h2 { font-size: 45px !important; }
        .stTable { font-size: 22px !important; }
        label { font-size: 24px !important; font-weight: bold; } /* Enlarge selectbox title font */
        div[data-baseweb="select"] > div { font-size: 20px !important; } /* Enlarge selectbox option font */
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Display mock data status at the top of the page
    if USE_MOCK_DATA:
        st.warning("⚠️ Using mock data - API server not connected")


def display_hitter_data(title, hitter_data):
    """
    Display hitter data table

    Args:
        title (str): Table title
        hitter_data (tuple/list): Hitter data
    """
    if hitter_data:
        if isinstance(hitter_data, tuple):
            hitter_data = [list(hitter_data)]
        elif isinstance(hitter_data, list) and isinstance(
            hitter_data[0], (str, float, int)
        ):
            hitter_data = [hitter_data]

        df = pd.DataFrame(
            hitter_data, columns=["Batter", "AVG", "OBP", "SLG", "OPS"]
        ).round(3)

        st.write(f"### {title}")
        st.table(df.set_index("Batter"))  # Hide index
    else:
        st.write(f"⚠️ {title} - No data available")


def today_games_tab():
    """Today's games analysis tab"""
    st.header("📅 Today's Games")

    # Get today's games
    response_data = safe_api_request(f"{API_BASE_URL}/games/today")
    today_games = response_data.get("games", [])

    if not today_games:
        st.write("⚠️ No games today")
        return

    # Select game
    game_options = [f"{g['away_team']} @ {g['home_team']}" for g in today_games]
    selected_game = st.selectbox("Select Game", game_options)

    # Get selected game information
    selected_index = game_options.index(selected_game)
    selected_game_info = today_games[selected_index]

    # Get all pitchers in the game
    game_pitchers = safe_api_request(
        f"{API_BASE_URL}/game/{selected_game_info['game_id']}/pitchers"
    )

    # Create two-column analysis block
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"⚔️ Away Team: {selected_game_info['away_team']}")

        # Away team pitcher dropdown
        away_pitcher_options = [p["full_name"] for p in game_pitchers.get("away", [])]
        away_pitcher_ids = {
            p["full_name"]: p["pitcher_id"] for p in game_pitchers.get("away", [])
        }

        if away_pitcher_options:
            selected_away_pitcher = st.selectbox(
                "Select Away Team Pitcher",
                away_pitcher_options,
                key="away_pitcher_select",
            )
            selected_away_pitcher_id = away_pitcher_ids[selected_away_pitcher]
        else:
            st.write("⚠️ No pitcher data available")
            selected_away_pitcher_id = None
            selected_away_pitcher = None

        # Analysis button - Away team pitcher vs Home team batters
        if selected_away_pitcher_id and st.button(
            "Analyze Home Team Batters vs Away Team Pitcher",
            key="home_vs_away_analysis",
        ):
            # Analyze home team batters against selected away pitcher
            data = safe_api_request(
                f"{API_BASE_URL}/matchup?team_id={selected_game_info['home_team_id']}&pitcher_id={selected_away_pitcher_id}"
            )

            # Display data
            if data.get("best_season_hitter"):
                display_hitter_data(
                    f"🏆 Highest Season OPS Batter ({selected_game_info['home_team']})",
                    data.get("best_season_hitter"),
                )

            if data.get("best_recent_hitter"):
                display_hitter_data(
                    f"📈 Highest OPS Batter Last 5 Games ({selected_game_info['home_team']})",
                    data.get("best_recent_hitter"),
                )

            if data.get("best_vs_pitcher_hitter"):
                display_hitter_data(
                    f"🔥 Highest OPS Batter vs {selected_away_pitcher} ({selected_game_info['home_team']})",
                    data.get("best_vs_pitcher_hitter"),
                )

            if data.get("all_hitters_vs_pitcher"):
                display_hitter_data(
                    f"📊 All Team Data vs {selected_away_pitcher} ({selected_game_info['home_team']})",
                    data.get("all_hitters_vs_pitcher"),
                )

            if not data.get("best_vs_pitcher_hitter"):
                st.write(f"⚠️ No matchup data against {selected_away_pitcher}")

    with col2:
        st.subheader(f"🏠 Home Team: {selected_game_info['home_team']}")

        # Home team pitcher dropdown
        home_pitcher_options = [p["full_name"] for p in game_pitchers.get("home", [])]
        home_pitcher_ids = {
            p["full_name"]: p["pitcher_id"] for p in game_pitchers.get("home", [])
        }

        if home_pitcher_options:
            selected_home_pitcher = st.selectbox(
                "Select Home Team Pitcher",
                home_pitcher_options,
                key="home_pitcher_select",
            )
            selected_home_pitcher_id = home_pitcher_ids[selected_home_pitcher]
        else:
            st.write("⚠️ No pitcher data available")
            selected_home_pitcher_id = None
            selected_home_pitcher = None

        # Analysis button - Home team pitcher vs Away team batters
        if selected_home_pitcher_id and st.button(
            "Analyze Away Team Batters vs Home Team Pitcher",
            key="away_vs_home_analysis",
        ):
            # Analyze away team batters against selected home pitcher
            data = safe_api_request(
                f"{API_BASE_URL}/matchup?team_id={selected_game_info['away_team_id']}&pitcher_id={selected_home_pitcher_id}"
            )

            # Display data
            if data.get("best_season_hitter"):
                display_hitter_data(
                    f"🏆 Highest Season OPS Batter ({selected_game_info['away_team']})",
                    data.get("best_season_hitter"),
                )

            if data.get("best_recent_hitter"):
                display_hitter_data(
                    f"📈 Highest OPS Batter Last 5 Games ({selected_game_info['away_team']})",
                    data.get("best_recent_hitter"),
                )

            if data.get("best_vs_pitcher_hitter"):
                display_hitter_data(
                    f"🔥 Highest OPS Batter vs {selected_home_pitcher} ({selected_game_info['away_team']})",
                    data.get("best_vs_pitcher_hitter"),
                )

            if data.get("all_hitters_vs_pitcher"):
                display_hitter_data(
                    f"📊 All Team Data vs {selected_home_pitcher} ({selected_game_info['away_team']})",
                    data.get("all_hitters_vs_pitcher"),
                )

            if not data.get("best_vs_pitcher_hitter"):
                st.write(f"⚠️ No matchup data against {selected_home_pitcher}")


def custom_matchup_tab():
    """Custom matchup analysis tab"""
    st.header("🔍 Custom Matchup Analysis")

    # Ensure MLB_TEAMS is not empty
    if not MLB_TEAMS:
        st.error("⚠️ Team data failed to load. Please check config/team_config.py")
        return

    # Select team
    team_name = st.selectbox(
        "Select Your Team", list(MLB_TEAMS.keys()), key="custom_team"
    )
    team_id = MLB_TEAMS[team_name]

    # Select opponent team
    opponent_team_name = st.selectbox(
        "Select Opponent Team", list(MLB_TEAMS.keys()), key="custom_opponent"
    )
    opponent_team_id = MLB_TEAMS[opponent_team_name]

    # Get opponent pitcher list
    response_data = safe_api_request(f"{API_BASE_URL}/team/{opponent_team_id}/pitchers")
    pitchers = response_data.get("pitchers", [])

    if not pitchers:
        st.write("⚠️ No pitchers available for this team")
        return

    # Extract pitcher names
    pitcher_names = [p["full_name"] for p in pitchers]

    # Create name -> ID mapping
    pitcher_ids = {p["full_name"]: p["pitcher_id"] for p in pitchers}

    # Select opponent pitcher
    selected_pitcher_name = st.selectbox(
        "Select Opponent Pitcher", pitcher_names, key="custom_pitcher"
    )

    # Look up ID by name
    selected_pitcher_id = pitcher_ids[selected_pitcher_name]

    # Query data
    if st.button("Analyze", key="custom_analyze"):
        data = safe_api_request(
            f"{API_BASE_URL}/matchup?team_id={team_id}&pitcher_id={selected_pitcher_id}"
        )

        # Display data
        if data.get("best_season_hitter"):
            display_hitter_data(
                f"🏆 Highest Season OPS Batter ({data.get('team_name', team_name)})",
                data.get("best_season_hitter"),
            )

        if data.get("best_recent_hitter"):
            display_hitter_data(
                f"📈 Highest OPS Batter Last 5 Games ({data.get('team_name', team_name)})",
                data.get("best_recent_hitter"),
            )

        if data.get("best_vs_pitcher_hitter"):
            display_hitter_data(
                f"🔥 Highest OPS Batter vs {selected_pitcher_name} ({data.get('team_name', team_name)})",
                data.get("best_vs_pitcher_hitter"),
            )

        if data.get("all_hitters_vs_pitcher"):
            display_hitter_data(
                f"📊 All Team Data vs {selected_pitcher_name} ({data.get('team_name', team_name)})",
                data.get("all_hitters_vs_pitcher"),
            )

        if not data.get("best_vs_pitcher_hitter") and not data.get(
            "all_hitters_vs_pitcher"
        ):
            st.write(f"⚠️ No matchup data against {selected_pitcher_name}")


def main():
    """Streamlit application main function"""
    # Set page configuration
    setup_page_config()

    # Display title
    st.title("⚾ MLB Matchup Data Analysis")

    # Create tabs
    tab1, tab2 = st.tabs(["📅 Today's Games", "🔍 Custom Matchup Analysis"])

    # Fill tab content
    with tab1:
        today_games_tab()

    with tab2:
        custom_matchup_tab()


if __name__ == "__main__":
    main()
