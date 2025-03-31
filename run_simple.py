#!/usr/bin/env python
"""
Simple launcher for the MLB integrated app
"""

import os
import sys
import subprocess
import datetime

# Set the environment var to use standalone mode if needed
os.environ["USE_STANDALONE_MODE"] = "1"

# Use a specific game ID that works as default - a more recent one for better testing
game_id = "778549"  # You can change this to another working game ID

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
