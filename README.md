# MLB Game Analysis & Tracker

A comprehensive system for analyzing MLB games, tracking live games, and examining player matchups to gain insights into baseball statistics and performance.

![MLB Game Tracker](https://img.shields.io/badge/MLB-Game%20Tracker-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-brightgreen)
![Streamlit](https://img.shields.io/badge/Streamlit-1.24.0%2B-red)
![FastAPI](https://img.shields.io/badge/FastAPI-0.98.0%2B-blue)

## Features

- **Live Game Tracking**: Real-time updates of MLB games with detailed score and situation information
- **Baseball Diamond Visualization**: Interactive visualization of the current field situation
- **Batter vs. Pitcher Analysis**: Detailed statistical analysis of how batters perform against specific pitchers
- **Hot/Cold Zones**: Visual representation of batter's performance in different strike zones
- **Multi-language Support**: Available in English and Traditional Chinese
- **Advanced Statistics**: Includes sabermetrics like FIP-, wRC+, and WAR with color-coded indicators

## System Architecture

The system consists of three main components:

1. **FastAPI Backend**: Handles MLB data retrieval and processing
2. **Streamlit UI**: Provides interactive user interface for analysis
3. **Data Maintenance Tools**: Manages the retrieval and storage of MLB statistics

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mlb-analysis-tracker.git
   cd mlb-analysis-tracker
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Unified Launcher (Recommended)

The `mlb_launcher.py` script provides a unified command-line interface to all system components:

```bash
# Start everything (API server, update data, and launch live tracker)
python mlb_launcher.py --all

# Start API server and main UI
python mlb_launcher.py --api-bg --ui

# Start API server in background and launch live tracker
python mlb_launcher.py --api-bg --live

# Only update data without launching any UI
python mlb_launcher.py --update-all

# Launch live tracker with a specific game ID
python mlb_launcher.py --live --game-id 778549
```

For more options, run:
```bash
python mlb_launcher.py --help
```

### Individual Components

If you prefer to run components separately:

#### Start the API Server
```bash
python run_api.py
```

#### Update Player Data
```bash
python main.py --update-season --update-recent
```

#### Launch the Main UI
```bash
python run_ui.py
```

#### Launch the Live Tracker
```bash
python run_simple.py
```

## Application Views

The system offers three main views:

1. **Live Score Tracker**: Real-time game tracking with score updates and field visualizations
2. **Batter vs. Pitcher Analysis**: Analyze how a specific team's batters perform against a selected pitcher
3. **Custom Matchup Analysis**: Create custom matchups between any team and pitcher

## Technical Details

- **API Integration**: Uses MLB Stats API to retrieve real-time game data
- **Data Storage**: SQLite database for storing player statistics
- **Sabermetrics**: Advanced baseball statistics for deeper analysis
- **Auto-refresh**: Configurable auto-refresh feature for live game tracking
- **Standalone Mode**: Can operate with or without the backend API server

## Requirements

- Python 3.7+
- Streamlit 1.24.0+
- FastAPI 0.98.0+
- Additional dependencies listed in `requirements.txt`

## License

[MIT License](LICENSE)

## Acknowledgments

- MLB Stats API for providing the game data
- Streamlit and FastAPI for the excellent frameworks
- The sabermetrics community for advanced baseball statistics

## Contact

If you have any questions or feedback, please open an issue on GitHub.

---

Created with ⚾ by Kai Yuan (Chester) Wang
