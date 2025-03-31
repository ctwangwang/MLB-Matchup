import streamlit as st
import os
import sys
import datetime
from typing import Optional

# Force standalone mode for Streamlit Cloud
os.environ["USE_STANDALONE_MODE"] = "1"
os.environ["USE_MOCK_DATA"] = "1"

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import only what you need from your modules
from mlb_data import get_today_games, get_live_data, get_batter_analysis
from mlb_visualizations import (
    create_baseball_diamond,
    display_hitter_data,
    create_hot_cold_zones,
    get_fip_minus_color,
    get_pitcher_war_color,
    get_wrc_plus_color,
    get_batter_war_color,
)

# Import UI components but not the ones that depend on the API
from ui_components import main_display, display_analysis_tab

# Page configuration
st.set_page_config(
    page_title="MLB Game Analysis & Tracker", page_icon="⚾", layout="wide"
)

# App title and description
st.title("⚾ MLB Live Score Tracker")
st.markdown("Real-time score updates and analysis for MLB games")

# Add explanation about standalone mode
st.sidebar.info("Running in standalone mode with MLB direct API access")

# Initialize session states similar to live_tracker.py
if "selected_game_id" not in st.session_state:
    st.session_state.selected_game_id = None

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.datetime.now()

# Rest of your essential UI code from live_tracker.py
# Focus on the core features that work without your API server
