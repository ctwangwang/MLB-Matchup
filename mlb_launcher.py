#!/usr/bin/env python
"""
MLB Analysis System Comprehensive Launcher

A unified entry point for all MLB analysis system components:
- FastAPI server
- Data maintenance
- Streamlit UI applications
"""

import os
import sys
import time
import signal
import argparse
import subprocess
import datetime
import requests
import threading
from typing import Optional

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Global variable to track running processes
running_processes = []


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="MLB Analysis System Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start API server, update data, and launch live tracker
  python mlb_launcher.py --all
  
  # Start API server and main UI
  python mlb_launcher.py --api --ui
  
  # Start API server in background and launch live tracker
  python mlb_launcher.py --api-bg --live
  
  # Only update data without launching any UI
  python mlb_launcher.py --update-all
  
  # Launch live tracker with a specific game ID
  python mlb_launcher.py --live --game-id 778549
        """,
    )

    # Component selection
    app_group = parser.add_argument_group("Components")
    app_group.add_argument(
        "--all",
        action="store_true",
        help="Launch everything (API, update data, and live tracker)",
    )
    app_group.add_argument(
        "--api", action="store_true", help="Start the FastAPI server (blocking)"
    )
    app_group.add_argument(
        "--api-bg", action="store_true", help="Start the FastAPI server in background"
    )
    app_group.add_argument(
        "--ui", action="store_true", help="Launch the main Streamlit UI"
    )
    app_group.add_argument(
        "--live", action="store_true", help="Launch the live tracker app"
    )

    # Data maintenance options
    data_group = parser.add_argument_group("Data Maintenance")
    data_group.add_argument(
        "--update-season", action="store_true", help="Update 2024 season data"
    )
    data_group.add_argument(
        "--update-recent", action="store_true", help="Update recent 5 games data"
    )
    data_group.add_argument(
        "--update-all", action="store_true", help="Update all data (season and recent)"
    )

    # Live tracker options
    live_group = parser.add_argument_group("Live Tracker Options")
    live_group.add_argument(
        "--game-id", type=str, help="Specify a game ID for live tracker"
    )

    # Environment options
    env_group = parser.add_argument_group("Environment Options")
    env_group.add_argument(
        "--force-standalone",
        action="store_true",
        help="Force standalone mode even if API is available",
    )
    env_group.add_argument(
        "--port", type=int, default=8501, help="Port for Streamlit (default: 8501)"
    )
    env_group.add_argument(
        "--api-port", type=int, default=8000, help="Port for API server (default: 8000)"
    )

    return parser.parse_args()


def check_api_server(port=8000, timeout=1):
    """Check if the API server is running on the specified port"""
    try:
        url = f"http://localhost:{port}"
        response = requests.get(url, timeout=timeout)
        print(f"✅ API server detected at {url}")
        return True
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print(f"⚠️ API server not detected at {url}")
        return False


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

        # Import get_today_games function
        try:
            from mlb_data import get_today_games

            today_games = get_today_games(today)
        except ImportError:
            print("Could not import mlb_data module, using fallback game ID")
            return "778549"  # Default game ID as fallback

        if today_games:
            # First priority: Live games
            live_games = [g for g in today_games if g["status"] == "Live"]
            if live_games:
                game_id = str(live_games[0]["id"])
                print(
                    f"🔴 Found LIVE game: {live_games[0].get('matchup', '')} (ID: {game_id})"
                )
                return game_id

            # Second priority: Upcoming games
            upcoming_games = [g for g in today_games if g["status"] == "Preview"]
            if upcoming_games:
                game_id = str(upcoming_games[0]["id"])
                print(
                    f"⏰ Found upcoming game: {upcoming_games[0].get('matchup', '')} (ID: {game_id})"
                )
                return game_id

            # Third priority: Completed games
            finished_games = [g for g in today_games if g["status"] == "Final"]
            if finished_games:
                game_id = str(finished_games[0]["id"])
                print(
                    f"✓ Found completed game: {finished_games[0].get('matchup', '')} (ID: {game_id})"
                )
                return game_id

        # Fallback to default game ID if no games found
        print("⚠️ No games found, using default game ID")
        return "778549"  # Default game ID as fallback
    except Exception as e:
        print(f"⚠️ Error getting live game ID: {e}")
        return "778549"  # Default game ID in case of error


def start_api_server(port=8000, background=False):
    """Start the FastAPI server"""
    print(f"⚡ Starting FastAPI server on port {port}")

    api_cmd = [
        "uvicorn",
        "api.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--reload",
    ]

    if background:
        # Start API server as a subprocess
        process = subprocess.Popen(
            api_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        running_processes.append(process)

        # Wait for API server to start
        max_attempts = 5
        for i in range(max_attempts):
            time.sleep(1)  # Give server time to start
            if check_api_server(port, timeout=0.5):
                return True

        print(f"⚠️ API server didn't start after {max_attempts} attempts")
        return False
    else:
        # Start API server in foreground (blocking)
        subprocess.run(api_cmd)
        return True


def update_data(update_season=False, update_recent=False):
    """Update player data"""
    print("⚾ Running MLB Analysis System Data Maintenance Tool")

    try:
        # Ensure data directory exists
        os.makedirs("mlb_data", exist_ok=True)

        # Initialize database
        from database.db_setup import initialize_database

        initialize_database()
        print("✅ Database initialized")

        # Handle data updates
        if update_season:
            print("📊 Updating season data...")
            from data_processing.player_data import update_player_season_data

            update_player_season_data()
            print("✅ Season data updated")

        if update_recent:
            print("📊 Updating recent game data...")
            from data_processing.player_data import update_player_recent_data

            update_player_recent_data()
            print("✅ Recent game data updated")

        if not update_season and not update_recent:
            print("ℹ️ No data update operations specified")

        return True
    except Exception as e:
        print(f"❌ Error updating data: {e}")
        return False


def launch_live_tracker(game_id=None, port=8501, api_port=8000, force_standalone=False):
    """Launch the live tracker application"""
    # Set up environment variables
    env_vars = dict(os.environ)
    env_vars["PYTHONUNBUFFERED"] = "1"  # Ensure output is not buffered

    # Check if API server is running
    api_running = check_api_server(api_port) if not force_standalone else False

    # Set standalone mode if API is not running or forced
    if not api_running or force_standalone:
        env_vars["USE_STANDALONE_MODE"] = "1"
        print("ℹ️ Using standalone mode")

    # Get the game ID if not provided
    if not game_id:
        game_id = get_first_live_game_id()

    # Set game ID in environment
    env_vars["GAME_ID"] = game_id

    # Show timestamp for initialization
    print(
        f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting MLB Live Tracker with game ID: {game_id}"
    )

    # Launch Streamlit with the integrated app
    app_path = os.path.join(os.path.dirname(__file__), "live_tracker.py")
    print(f"🚀 Starting Streamlit Live Tracker from: {app_path}")

    # Run Streamlit
    process = subprocess.Popen(
        [
            "streamlit",
            "run",
            app_path,
            "--server.port",
            str(port),
            "--browser.serverAddress",
            "localhost",
            "--server.headless",
            "false",  # Allow browser to open automatically
        ],
        env=env_vars,
    )
    running_processes.append(process)

    # Wait for the process to finish
    process.wait()


def launch_ui(port=8502, api_port=8000):
    """Launch the main Streamlit UI interface"""
    print("🎮 Launching Streamlit UI interface")

    # Set up environment variables
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"  # Ensure output is not buffered

    # Check if API server is running
    api_running = check_api_server(api_port)
    if not api_running:
        env["USE_MOCK_DATA"] = "1"
        print("ℹ️ Using mock data (API server not detected)")

    # Run Streamlit
    app_path = os.path.join(os.path.dirname(__file__), "ui/streamlit_app.py")
    print(f"🚀 Starting Main UI from: {app_path}")

    process = subprocess.Popen(
        [
            "streamlit",
            "run",
            app_path,
            "--server.port",
            str(port),
            "--browser.serverAddress",
            "localhost",
            "--server.headless",
            "false",
        ],
        env=env,
    )
    running_processes.append(process)

    # Wait for the process to finish
    process.wait()


def cleanup():
    """Clean up all running processes when exiting"""
    print("\n🛑 Shutting down all processes...")
    for process in running_processes:
        try:
            process.terminate()
            process.wait(timeout=2)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass
    print("👋 Goodbye!")


def handle_signal(sig, frame):
    """Handle termination signals"""
    print("\n⚠️ Received termination signal")
    cleanup()
    sys.exit(0)


def main():
    """Main entry point"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Parse command line arguments
    args = parse_args()

    try:
        # Handle the --all option (start everything)
        if args.all:
            # Start API server in background
            if start_api_server(args.api_port, background=True):
                # Update data
                update_data(update_season=True, update_recent=True)
                # Launch live tracker
                launch_live_tracker(args.game_id, args.port, args.api_port)
            return

        # Handle --update-all option
        if args.update_all:
            args.update_season = True
            args.update_recent = True

        # Handle data maintenance operations
        if args.update_season or args.update_recent:
            success = update_data(args.update_season, args.update_recent)
            if not success:
                print("❌ Data update operations failed")

        # Handle API server
        if args.api:
            # Start API server in foreground (blocking)
            start_api_server(args.api_port, background=False)
            return
        elif args.api_bg:
            # Start API server in background
            start_api_server(args.api_port, background=True)

        # Launch applications
        if args.live:
            launch_live_tracker(
                args.game_id, args.port, args.api_port, args.force_standalone
            )
        elif args.ui:
            launch_ui(args.port, args.api_port)
        elif not any([args.update_season, args.update_recent, args.api_bg]):
            # If no specific action was requested, show help
            print("No specific action requested. Use --help to see available options.")

    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
