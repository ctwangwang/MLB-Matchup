#!/usr/bin/env python
"""
Simple launcher for the MLB integrated app
"""

import os
import sys
import subprocess
import datetime
import requests
import json

# Set the environment var to use standalone mode if needed
os.environ["USE_STANDALONE_MODE"] = "1"


def get_first_live_game_id():
    """
    Get the first live game ID from MLB API.
    If no live games are found, return the first upcoming game.
    If no upcoming games are found, return the first completed game.
    If no games are found at all, return a default game ID.
    """
    try:
        # Get today's date in YYYY-MM-DD format
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Use the same function as in live_tracker.py to get today's games
        from mlb_data import get_today_games

        today_games = get_today_games(today)

        if today_games:
            # First priority: Live games
            live_games = [g for g in today_games if g["status"] == "Live"]
            if live_games:
                return str(live_games[0]["id"])

            # Second priority: Upcoming games
            upcoming_games = [g for g in today_games if g["status"] == "Preview"]
            if upcoming_games:
                return str(upcoming_games[0]["id"])

            # Third priority: Completed games
            finished_games = [g for g in today_games if g["status"] == "Final"]
            if finished_games:
                return str(finished_games[0]["id"])

        # Fallback to default game ID if no games found
        return "778549"  # Default game ID as fallback
    except Exception as e:
        print(f"Error getting live game ID: {e}")
        return "778549"  # Default game ID in case of error


# Get the game ID of the first live game
game_id = get_first_live_game_id()

# Show timestamp for initialization
print(
    f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting MLB integrated app with game ID:",
    game_id,
)

# Launch Streamlit with the integrated app and specify game_id
app_path = os.path.join(os.path.dirname(__file__), "live_tracker.py")
print(f"Starting Streamlit app from: {app_path}")

# Set up environment variables for the app
env_vars = dict(os.environ)
env_vars["GAME_ID"] = game_id
env_vars["PYTHONUNBUFFERED"] = "1"  # Ensure output is not buffered

# Run Streamlit with the game_id parameter
subprocess.run(
    [
        "streamlit",
        "run",
        app_path,
        "--server.port",
        "8501",
        "--browser.serverAddress",
        "localhost",
        "--server.headless",
        "false",  # Allow browser to open automatically
    ],
    env=env_vars,
)
