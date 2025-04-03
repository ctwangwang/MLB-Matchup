import streamlit as st
import datetime
import os
import sys
from typing import Optional
from streamlit_autorefresh import st_autorefresh

# Import our modules
from mlb_data import (
    get_today_date,
    safe_api_request,
    get_today_games,
    get_live_data,
    get_batter_analysis,
)

from mlb_visualizations import (
    create_baseball_diamond,
    display_hitter_data,
    create_hot_cold_zones,
    get_fip_minus_color,
    get_pitcher_war_color,
    get_wrc_plus_color,
    get_batter_war_color,
)

from ui_components import switch_to_analysis_tab, main_display, display_analysis_tab

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Try to import required modules from your existing project
try:
    from api.mlb_api import (
        get_player_info,
        get_batter_season_stats,
        get_pitcher_season_stats,
        get_player_recent_games,
        get_vs_pitcher_stats,
        get_team_roster,
        get_batter_situation_stats,
        get_pitcher_situation_stats,
        get_pitcher_sabermetrics,
        get_batter_sabermetrics,
    )
    from data_processing.player_data import get_batter_vs_pitcher_stats
    from config.team_config import MLB_TEAMS

    API_IMPORTS_SUCCESS = True
except ImportError as e:
    st.sidebar.warning(f"Could not import API modules: {e}")
    API_IMPORTS_SUCCESS = False
    # Create empty MLB_TEAMS if import failed
    MLB_TEAMS = {}

# Set page configuration
st.set_page_config(
    page_title="MLB Game Analysis & Tracker", page_icon="⚾", layout="wide"
)

# API base URL for your existing backend
# API_BASE_URL = "http://localhost:8000"
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# Initialize session state variables
if "selected_game_id" not in st.session_state:
    st.session_state.selected_game_id = None

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.datetime.now()

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Live Score Tracker"

if "analyze_pitcher_id" not in st.session_state:
    st.session_state.analyze_pitcher_id = None

if "analyze_team_id" not in st.session_state:
    st.session_state.analyze_team_id = None

if "analyze_pitcher_name" not in st.session_state:
    st.session_state.analyze_pitcher_name = None

if "analyze_team_name" not in st.session_state:
    st.session_state.analyze_team_name = None

if "pending_tab_switch" not in st.session_state:
    st.session_state.pending_tab_switch = False

if "previous_tab" not in st.session_state:
    st.session_state.previous_tab = "Live Score Tracker"

if "first_time_visit" not in st.session_state:
    st.session_state.first_time_visit = True
    # For first-time visitors, set previous_tab to Live Score Tracker
    st.session_state.previous_tab = "Live Score Tracker"
else:
    # Not first visit, so we'll track the tab changes normally
    st.session_state.first_time_visit = False

if "tab_redirect" not in st.session_state:
    st.session_state.tab_redirect = False

if "force_tab_switch" not in st.session_state:
    st.session_state.force_tab_switch = False

# Auto-refresh related state variables
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = False

if "auto_refresh_interval" not in st.session_state:
    st.session_state.auto_refresh_interval = 30  # 30 seconds default

if "last_auto_refresh" not in st.session_state:
    st.session_state.last_auto_refresh = datetime.datetime.now()


# Function to switch tabs via callback
def change_tab(tab_name):
    # Store current tab as previous before switching
    st.session_state.previous_tab = st.session_state.active_tab
    st.session_state.active_tab = tab_name


previous_tab = st.session_state.active_tab  # Save current tab before it changes

# Check URL for forced tab switch (add this near the beginning of live_tracker.py)
if st.query_params.get("active_tab") == "analysis":
    # Clear the parameter so it doesn't persist
    st.query_params["active_tab"] = ""
    # Set the active tab
    st.session_state.active_tab = "Batter vs. Pitcher Analysis"
    # Force refresh to ensure the tab switch takes effect
    # st.rerun()

# Determine the index for the radio button based on current active tab
tab_index = 0
if st.session_state.active_tab == "Batter vs. Pitcher Analysis":
    tab_index = 1
elif st.session_state.active_tab == "Custom Matchup Analysis":
    tab_index = 2


def handle_tab_change():
    # Store previous tab
    st.session_state.previous_tab = st.session_state.active_tab
    # Set new active tab
    st.session_state.active_tab = st.session_state.tab_selector

    # Disable auto-refresh when leaving Live Score Tracker tab
    if (
        st.session_state.previous_tab == "Live Score Tracker"
        and st.session_state.active_tab != "Live Score Tracker"
    ):
        st.session_state.auto_refresh_enabled = False


# Update the radio button to use the new handler
selected_tab = st.radio(
    "Select View:",
    ["Live Score Tracker", "Batter vs. Pitcher Analysis", "Custom Matchup Analysis"],
    horizontal=True,
    label_visibility="collapsed",
    index=tab_index,
    key="tab_selector",
    on_change=handle_tab_change,
)

# Update the active tab from user selection or from analysis button
if "tab_selector" in st.session_state:
    st.session_state.active_tab = st.session_state.tab_selector

# TAB 1: LIVE SCORE TRACKER
if st.session_state.active_tab == "Live Score Tracker":
    st.title("⚾ MLB Live Score Tracker")

    # Add the auto-refresh component
    if st.session_state.auto_refresh_enabled:
        # Convert seconds to milliseconds for the component
        refresh_interval_ms = st.session_state.auto_refresh_interval * 1000
        # Initialize the autorefresh component
        refresh_count = st_autorefresh(
            interval=refresh_interval_ms, key="autorefresher"
        )

        # Show refresh status
        st.info(
            f"🔄 Auto-refreshing every {st.session_state.auto_refresh_interval} seconds. Refresh count: {refresh_count}"
        )

    if previous_tab != st.session_state.active_tab:
        st.session_state.previous_tab = previous_tab
    # Track last refresh time
    current_time = datetime.datetime.now()
    time_diff = (current_time - st.session_state.last_refresh).total_seconds()

    # Check URL parameters first for game_id
    # query_params = st.experimental_get_query_params()
    game_id_from_url = st.query_params.get("game_id", "")

    # Check if we have a game ID from environment (for the launcher script)
    env_game_id = os.environ.get("GAME_ID", "")
    if env_game_id and not game_id_from_url:
        game_id_from_url = env_game_id

    # Sidebar date selector
    today = datetime.datetime.now()
    selected_date = st.sidebar.date_input("Select Date", today)
    selected_date_str = selected_date.strftime("%Y-%m-%d")

    # Get today's games
    today_games = get_today_games(selected_date_str)

    # Show games found in sidebar
    if today_games:
        st.sidebar.success(f"Found {len(today_games)} games for {selected_date_str}")
    else:
        st.sidebar.warning(f"No games found for {selected_date_str}")

    # Function to handle game selection
    def handle_game_selection():
        selected_game = st.session_state.select_game
        if selected_game and "ID:" in selected_game:
            new_game_id = selected_game.split("ID: ")[1].strip(")")

            # Only clear analysis if switching to a different game
            if st.session_state.selected_game_id != new_game_id:
                st.session_state.analyze_pitcher_id = None
                st.session_state.analyze_team_id = None
                st.session_state.analyze_pitcher_name = None
                st.session_state.analyze_team_name = None
                st.session_state.analysis_game_id = None

            st.query_params["game_id"] = new_game_id
            st.session_state.selected_game_id = new_game_id
            st.session_state.last_refresh = datetime.datetime.now()

    # Build game selection UI
    if today_games:
        game_options = []
        game_id_to_index = {}
        current_index = 0

        # Group games by status
        upcoming_games = [g for g in today_games if g["status"] == "Preview"]
        live_games = [g for g in today_games if g["status"] == "Live"]
        finished_games = [g for g in today_games if g["status"] == "Final"]

        # Build options list with headers
        if live_games:
            game_options.append("--- LIVE GAMES ---")
            current_index += 1
            for game in live_games:
                game_options.append(f"🔴 {game['matchup']} (ID: {game['id']})")
                game_id_to_index[str(game["id"])] = current_index
                current_index += 1

        if upcoming_games:
            game_options.append("--- UPCOMING GAMES ---")
            current_index += 1
            for game in upcoming_games:
                time_str = f" - {game['time']}" if game["time"] else ""
                game_options.append(
                    f"⏰ {game['matchup']}{time_str} (ID: {game['id']})"
                )
                game_id_to_index[str(game["id"])] = current_index
                current_index += 1

        if finished_games:
            game_options.append("--- COMPLETED GAMES ---")
            current_index += 1
            for game in finished_games:
                game_options.append(f"✓ {game['matchup']} (ID: {game['id']})")
                game_id_to_index[str(game["id"])] = current_index
                current_index += 1

        # Set default game ID based on priority: URL param > session state > live games > any game
        default_game_id = None

        # First priority: URL parameter
        if game_id_from_url:
            default_game_id = game_id_from_url
        # Second priority: Session state
        elif st.session_state.selected_game_id:
            default_game_id = st.session_state.selected_game_id
        # Third priority: First live game
        elif live_games:
            default_game_id = str(live_games[0]["id"])
        # Fourth priority: Any game
        elif upcoming_games or finished_games:
            all_games = upcoming_games + finished_games
            default_game_id = str(all_games[0]["id"])

        # Find the index to preselect in the dropdown
        default_index = (
            game_id_to_index.get(default_game_id, 0) if default_game_id else 0
        )
        if default_index >= len(game_options):
            default_index = 0

        # Create selectbox for game selection
        selected_game = st.sidebar.selectbox(
            "Select a Game",
            game_options,
            index=default_index,
            on_change=handle_game_selection,
            key="select_game",
        )

        # Extract game ID if a game was selected (not a header)
        selected_game_id = None
        if selected_game and "ID:" in selected_game:
            selected_game_id = selected_game.split("ID: ")[1].strip(")")

        # Use the game ID from the URL if available, otherwise use selected from dropdown
        game_id = game_id_from_url if game_id_from_url else selected_game_id

        # If we don't have a game ID yet, try to set a default
        if not game_id and default_game_id:
            game_id = default_game_id
            # Also update the URL
            st.query_params["game_id"] = game_id

    else:
        # No games found - allow manual entry
        st.sidebar.warning(f"No games found for {selected_date_str}")

        # Use URL parameter as default if available
        default_manual_id = (
            game_id_from_url if game_id_from_url else "779089"
        )  # Using a common game ID

        # Manual entry field
        manual_game_id = st.sidebar.text_input(
            "Enter Game ID manually:", value=default_manual_id
        )

        # Button to set the manually entered game ID
        if st.sidebar.button("Set Game ID"):
            st.query_params["game_id"] = manual_game_id
            st.session_state.selected_game_id = manual_game_id
            st.session_state.last_refresh = datetime.datetime.now()
            # No explicit rerun - the button click will cause Streamlit to rerun

        # Use the ID from URL if available, otherwise use manual entry
        game_id = game_id_from_url if game_id_from_url else manual_game_id

    # Display the current Game ID in the sidebar
    st.sidebar.info(f"Current Game ID: {game_id}")

    # Add custom CSS to make refresh button stand out
    st.sidebar.markdown(
        """
    <style>
    /* Target the specific button by its key */
    div[data-testid="stButton"] button {
        background-color: #FF5733;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
        font-size: 18px;
        width: 100%;
        border-radius: 5px;
        margin-bottom: 10px;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stButton"] button:hover {
        background-color: #E64A19;
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    # Add manual refresh button with a distinctive color and full width
    if st.sidebar.button("🔄 REFRESH DATA NOW", key="refresh_button"):
        st.session_state.last_refresh = datetime.datetime.now()
        st.rerun()

    # Add to the sidebar in the Live Score Tracker tab
    st.sidebar.markdown("### Auto-Refresh Settings")

    # Toggle button for auto-refresh
    if st.sidebar.button(
        "🔄 Enable Auto-Refresh"
        if not st.session_state.auto_refresh_enabled
        else "⏹️ Disable Auto-Refresh"
    ):
        st.session_state.auto_refresh_enabled = (
            not st.session_state.auto_refresh_enabled
        )
        st.session_state.last_auto_refresh = datetime.datetime.now()  # Reset the timer

    # Status indicator
    if st.session_state.auto_refresh_enabled:
        st.sidebar.success(
            f"Auto-refresh is enabled (every {st.session_state.auto_refresh_interval} seconds)"
        )
    else:
        st.sidebar.info("Auto-refresh is disabled")

    # Interval slider
    new_interval = st.sidebar.slider(
        "Refresh interval (seconds)",
        min_value=10,
        max_value=60,
        value=st.session_state.auto_refresh_interval,
        step=5,
    )

    # Update interval if changed
    if new_interval != st.session_state.auto_refresh_interval:
        st.session_state.auto_refresh_interval = new_interval
        st.session_state.last_auto_refresh = datetime.datetime.now()  # Reset the timer

    st.sidebar.markdown("---")

    # Only proceed if we have a game ID
    if game_id:
        # Save the selected game ID to session state
        st.session_state.selected_game_id = game_id

        # Get the live data
        with st.spinner("Fetching MLB data..."):
            score_data = get_live_data(game_id)

        # Store current pitcher and batter IDs in session state if in live game
        if score_data and score_data.get("abstract_game_state") == "Live":
            if score_data.get("pitcher_id"):
                st.session_state.current_pitcher_id = score_data["pitcher_id"]
                st.session_state.current_pitcher_name = score_data.get(
                    "pitcher", "Unknown Pitcher"
                )

            if score_data.get("batter_id"):
                st.session_state.current_batter_id = score_data["batter_id"]
                st.session_state.current_batter_name = score_data.get(
                    "batter", "Unknown Batter"
                )

        # Call the main display function to show the game information
        main_display(
            game_id,
            get_live_data,
            create_baseball_diamond,
            create_hot_cold_zones,
            get_fip_minus_color,
            get_pitcher_war_color,
            get_wrc_plus_color,
            get_batter_war_color,
            get_vs_pitcher_stats if API_IMPORTS_SUCCESS else None,
            API_IMPORTS_SUCCESS,
            get_batter_season_stats if API_IMPORTS_SUCCESS else None,
            get_pitcher_season_stats if API_IMPORTS_SUCCESS else None,
            get_batter_situation_stats if API_IMPORTS_SUCCESS else None,  # Add this
            get_pitcher_situation_stats if API_IMPORTS_SUCCESS else None,  # Add this
            get_pitcher_sabermetrics if API_IMPORTS_SUCCESS else None,
            get_batter_sabermetrics if API_IMPORTS_SUCCESS else None,
        )

        # Add DeepSeek analysis section for live games
        if (
            score_data
            and score_data.get("abstract_game_state") == "Live"
            and API_IMPORTS_SUCCESS
        ):
            from ui_components import add_deepseek_analysis_to_live_tracker

            add_deepseek_analysis_to_live_tracker()
        # Auto-refresh logic for the Live Score Tracker tab
        if (
            st.session_state.active_tab == "Live Score Tracker"
            and st.session_state.auto_refresh_enabled
        ):
            current_time = datetime.datetime.now()
            time_since_last_refresh = (
                current_time - st.session_state.last_auto_refresh
            ).total_seconds()

            if time_since_last_refresh >= st.session_state.auto_refresh_interval:
                st.session_state.last_refresh = current_time
                st.session_state.last_auto_refresh = current_time
                st.rerun()

# TAB 2: BATTER VS. PITCHER ANALYSIS
elif st.session_state.active_tab == "Batter vs. Pitcher Analysis":
    st.title("⚾ Batter vs. Pitcher Analysis")

    if (
        not st.session_state.previous_tab
        or st.session_state.previous_tab == "Batter vs. Pitcher Analysis"
    ):
        st.session_state.previous_tab = "Live Score Tracker"

    # Check if we have a current game and no analysis parameters
    if (
        st.session_state.selected_game_id
        and not st.session_state.analyze_pitcher_id
        and not st.session_state.analyze_team_id
    ):
        # Try to get current game data
        score_data = get_live_data(st.session_state.selected_game_id)

        if score_data and score_data.get("abstract_game_state") == "Live":
            # If game is live, show message to select a pitcher from live view
            st.warning(
                "Please select a pitcher to analyze from the Live Score Tracker view"
            )
            if st.button("Go to Live Score Tracker"):
                st.session_state.active_tab = "Live Score Tracker"
                st.rerun()
        else:
            # For non-live games, show message to use custom analysis
            st.warning("Please use Custom Matchup Analysis for non-live games")
            if st.button("Go to Custom Matchup Analysis"):
                st.session_state.active_tab = "Custom Matchup Analysis"
                st.rerun()
    elif (
        st.session_state.analyze_pitcher_id
        and st.session_state.analyze_team_id
        and st.session_state.analyze_pitcher_name
        and st.session_state.analyze_team_name
    ):
        # Existing analysis display logic
        pitcher_id = st.session_state.analyze_pitcher_id
        team_id = st.session_state.analyze_team_id
        pitcher_name = st.session_state.analyze_pitcher_name
        team_name = st.session_state.analyze_team_name

        display_analysis_tab(
            team_id,
            pitcher_id,
            team_name,
            pitcher_name,
            display_hitter_data,
            get_batter_analysis,
            API_IMPORTS_SUCCESS,
            API_BASE_URL,
            get_vs_pitcher_stats if API_IMPORTS_SUCCESS else None,
            get_batter_season_stats if API_IMPORTS_SUCCESS else None,
            get_batter_vs_pitcher_stats if API_IMPORTS_SUCCESS else None,
            MLB_TEAMS,
        )
    else:
        st.warning(
            "No pitcher selected for analysis. Please select a pitcher from the Live Score Tracker "
            "or use Custom Matchup Analysis."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Live Score Tracker"):
                st.session_state.active_tab = "Live Score Tracker"
                st.rerun()
        with col2:
            if st.button("Go to Custom Matchup Analysis"):
                st.session_state.active_tab = "Custom Matchup Analysis"
                st.rerun()


elif st.session_state.active_tab == "Custom Matchup Analysis":
    if previous_tab != st.session_state.active_tab:
        st.session_state.previous_tab = previous_tab
    # First thing - always ensure auto-refresh is disabled in this tab
    st.session_state.auto_refresh_enabled = False

    st.title("⚾ Custom Matchup Analysis")

    # Manual selection mode
    st.markdown("### Custom Matchup Analysis")

    # Select teams and pitchers
    col1, col2 = st.columns(2)

    with col1:
        # Select team to analyze
        if MLB_TEAMS:
            team_name = st.selectbox(
                "Select Team", list(MLB_TEAMS.keys()), key="custom_team"
            )
            team_id = MLB_TEAMS[team_name]
        else:
            st.warning("MLB team data not available. Please run the API server.")
            team_name = "New York Yankees"
            team_id = 147

    with col2:
        # Select opponent team
        if MLB_TEAMS:
            opponent_team_name = st.selectbox(
                "Select Opponent Pitcher Team",
                list(MLB_TEAMS.keys()),
                key="custom_opponent",
            )
            opponent_team_id = MLB_TEAMS[opponent_team_name]
        else:
            st.warning("MLB team data not available. Using demo data.")
            opponent_team_name = "Boston Red Sox"
            opponent_team_id = 111

    # Get opponent pitchers
    with st.spinner(f"Loading {opponent_team_name} pitchers..."):
        try:
            # First try to get from your API
            if API_IMPORTS_SUCCESS:
                pitcher_response = safe_api_request(
                    f"{API_BASE_URL}/team/{opponent_team_id}/pitchers"
                )
                pitchers = pitcher_response.get("pitchers", [])

                # If that fails, try direct MLB API call
                if not pitchers and API_IMPORTS_SUCCESS:
                    pitchers = get_team_roster(opponent_team_id)
            else:
                # Use mock data when API is not available
                pitchers = [
                    {"full_name": "Chris Sale", "pitcher_id": 519242},
                    {"full_name": "Gerrit Cole", "pitcher_id": 543037},
                    {"full_name": "Shohei Ohtani", "pitcher_id": 660271},
                ]

            if pitchers:
                # Extract pitcher names and IDs
                pitcher_names = [p.get("full_name", "") for p in pitchers]
                pitcher_ids = {
                    p.get("full_name", ""): p.get("pitcher_id", 0) for p in pitchers
                }

                # Select a pitcher
                selected_pitcher_name = st.selectbox(
                    "Select Pitcher", pitcher_names, key="custom_pitcher"
                )
                selected_pitcher_id = pitcher_ids.get(selected_pitcher_name, 0)

                # Analyze button
                if st.button("Analyze Matchup", key="custom_analyze"):
                    # Use the refactored analysis display function
                    display_analysis_tab(
                        team_id,
                        selected_pitcher_id,
                        team_name,
                        selected_pitcher_name,
                        display_hitter_data,
                        get_batter_analysis,
                        API_IMPORTS_SUCCESS,
                        API_BASE_URL,
                        get_vs_pitcher_stats if API_IMPORTS_SUCCESS else None,
                        get_batter_season_stats if API_IMPORTS_SUCCESS else None,
                        get_batter_vs_pitcher_stats if API_IMPORTS_SUCCESS else None,
                        MLB_TEAMS,
                    )
            else:
                st.warning(f"No pitchers found for {opponent_team_name}")
        except Exception as e:
            st.error(f"Error loading pitchers: {e}")
            st.info("Using standalone mode due to API connection issues.")


if __name__ == "__main__":
    # This will execute when run directly
    pass
