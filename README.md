# MLB Stats Analysis System

A comprehensive baseball analytics platform for analyzing MLB games, matchups, and player statistics in real-time.

![MLB Stats Analysis](https://img.shields.io/badge/MLB-Stats%20Analysis-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.98.0+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.24.0+-red)

## 📌 Overview

This system provides real-time statistics, visualizations, and AI-powered analysis for MLB games and player matchups. It includes:

- **Live Score Tracker**: Watch MLB games in real-time with detailed statistics and field visualizations
- **Batter vs. Pitcher Analysis**: Analyze historical matchups between batters and pitchers
- **DeepSeek AI Integration**: Get AI-powered insights for matchup analysis
- **Custom Matchup Analysis**: Create your own hypothetical matchups for analysis
- **Sabermetrics Support**: Advanced baseball statistics including wRC+, FIP-, WAR, and more

## 🏗️ System Architecture

The system consists of:

1. **FastAPI Backend**: Handles data fetching, processing, and serves the REST API
2. **Streamlit Frontend**: Provides an interactive user interface with visualizations
3. **MLB API Integration**: Fetches real-time and historical game data
4. **SQLite Database**: Stores player statistics for quick lookup
5. **DeepSeek AI Integration**: Provides AI-powered analysis of matchups

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- MLB API access
- DeepSeek API key (optional, for AI analysis)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mlb-stats-analysis.git
   cd mlb-stats-analysis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up API keys:
   ```bash
   cp config/api_keys_template.py config/api_keys.py
   # Edit config/api_keys.py to add your DeepSeek API key
   ```

4. Initialize the database:
   ```bash
   python -c "from database.db_setup import initialize_database; initialize_database()"
   ```

### Running the System

The system can be started using the comprehensive launcher script:

```bash
python mlb_launcher.py --all
```

This will:
1. Start the FastAPI server
2. Update player data
3. Launch the live tracker UI

#### Additional Launcher Options

```
# Start API server and main UI
python mlb_launcher.py --api --ui

# Start API server in background and launch live tracker
python mlb_launcher.py --api-bg --live

# Only update data without launching any UI
python mlb_launcher.py --update-all

# Launch live tracker with a specific game ID
python mlb_launcher.py --live --game-id 778549
```

### Running Components Individually

1. Start the API server:
   ```bash
   uvicorn api.app:app --reload
   ```

2. Start the Live Tracker:
   ```bash
   streamlit run live_tracker.py
   ```

3. Start the Main UI:
   ```bash
   streamlit run ui/streamlit_app.py
   ```

4. Update player data:
   ```bash
   python -c "from data_processing.player_data import update_player_season_data; update_player_season_data()"
   ```

## 📊 Features

### Live Score Tracker

- Real-time game updates
- Score and inning information
- Count and base runners visualization
- Baseball diamond visualization
- Player statistics
- Auto-refresh functionality

### Batter vs. Pitcher Analysis

- Head-to-head matchup statistics
- Team-wide analysis against a pitcher
- Historical performance data
- Best performing batters identification

### DeepSeek AI Analysis

- AI-powered matchup insights
- Win probability calculations
- Key factors affecting outcomes
- Statistical pattern analysis

### Sabermetrics Support

- Advanced statistics visualization with color coding
- Performance indicators including:
  - FIP (Fielding Independent Pitching)
  - wRC+ (Weighted Runs Created Plus)
  - WAR (Wins Above Replacement)
  - BABIP (Batting Average on Balls in Play)
  - And many more

## 🗄️ Data Storage

The system uses an SQLite database (`mlb_data/mlb.db`) to store:

- Player season statistics
- Recent game performance data
- Team information

## 📁 Project Structure

```
mlb-stats-analysis/
├── api/                     # FastAPI backend modules
│   ├── app.py               # Main API application
│   ├── deepseek_analyzer.py # DeepSeek AI integration
│   └── mlb_api.py           # MLB API client functions
├── config/                  # Configuration files
│   ├── api_keys_template.py # Template for API keys
│   ├── situation_mapping.py # Game situation mappings
│   └── team_config.py       # MLB team information
├── data_processing/         # Data processing modules
│   └── player_data.py       # Player data processing
├── database/                # Database operations
│   ├── db_operations.py     # SQL operations
│   └── db_setup.py          # Database initialization
├── mlb_data/                # Data storage
│   └── mlb.db               # SQLite database
├── ui/                      # UI components
│   └── streamlit_app.py     # Main Streamlit application
├── utils/                   # Utility functions
│   └── helpers.py           # Helper functions
├── app.py                   # Auto-refresh demo app
├── live_tracker.py          # Live game tracker
├── mlb_data.py              # MLB data handling
├── mlb_launcher.py          # Comprehensive launcher
├── mlb_visualizations.py    # Data visualization functions
├── requirements.txt         # Python dependencies
├── ui_components.py         # UI components for Streamlit
└── README.md                # This file
```

## 🔍 API Endpoints

The FastAPI backend provides these endpoints:

- `GET /` - API health check
- `GET /matchup?team_id={id}&pitcher_id={id}` - Batter vs. pitcher matchup analysis
- `GET /games/today` - Today's scheduled games
- `GET /game/{game_id}/pitchers` - Pitchers for a specific game
- `GET /team/{team_id}/pitchers` - Pitchers for a specific team

## 🛠️ Technologies Used

- **FastAPI**: Backend API server
- **Streamlit**: Interactive frontend
- **Plotly**: Interactive visualizations
- **SQLite**: Data storage
- **Pandas**: Data manipulation
- **DeepSeek API**: AI-powered analysis
- **MLB Stats API**: Real-time and historical data

## 🔁 Auto-Refresh Functionality

The live tracker features an auto-refresh capability that can be configured to update at intervals between 20-60 seconds. This ensures you get the latest game information without manual refreshing.

## 🌐 DeepSeek AI Integration

The system integrates with DeepSeek's AI API to provide advanced matchup insights:
- Win probability calculations
- Key statistical patterns
- Actionable insights for at-bat outcomes
- Pitcher vs. batter strength/weakness analysis

*Note: To use this feature, a DeepSeek API key is required in `config/api_keys.py`.*

## 📄 License

[MIT License](LICENSE)

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on the GitHub repository.