# MLB Score Tracker and Batter Analysis Tool

This integrated application combines real-time MLB game tracking with batter vs. pitcher analysis functionality. The application provides a unified interface to:

1. Track live MLB games with up-to-date scoring, inning information, and game situation visualizations
2. Analyze batters against specific pitchers to identify favorable matchups
3. Seamlessly move between live game tracking and detailed analysis

## Project Structure

```
MLB/
├── api/
│   ├── __init__.py
│   ├── app.py
│   └── mlb_api.py
├── config/
│   ├── __init__.py
│   └── team_config.py
├── database/
│   ├── __init__.py
│   ├── db_operations.py
│   └── db_setup.py
├── data_processing/
│   ├── __init__.py
│   └── player_data.py
├── ui/
│   ├── __init__.py
│   └── streamlit_app.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── integrated_mlb_app.py  <-- New integrated application
├── run.py                 <-- New unified launcher script
├── run_api.py
└── run_ui.py
```

## Key Features

### MLB Live Score Tracker
- Real-time score updates with auto-refresh every 30 seconds (configurable)
- Detailed box scores (inning-by-inning)
- Current game situation visualization (including baseball diamond)
- Current at-bat information
- Pitcher and batter tracking

### Batter Analysis Tool
- Analyze team batters against specific pitchers
- View season-best OPS batters
- See recent form (last 5 games) for batters
- Get historical matchup data for batters vs. specific pitchers
- One-click analysis buttons directly from the live game view

## Integration Points
1. **Direct links from live games to analysis**:
   - For upcoming games: Analyze probable pitcher matchups
   - For live games: Analyze current pitcher matchups
   - Seamless navigation between both views

2. **Shared data model**:
   - Unified MLB API access
   - Common team and player data

3. **Consistent UI**:
   - Tabbed interface for easy navigation
   - Matching styling and presentation

## How to Run

### Option 1: Integrated Launcher (Recommended)
The simplest way to run the application is to use the new integrated launcher:

```bash
python run.py
```

This will:
1. Start the API server for batter analysis in the background
2. Launch the Streamlit interface with both live scores and analysis functionality

### Option 2: Run Components Separately
You can still run the API server and UI separately:

```bash
# Terminal 1: Start the API server
python run_api.py

# Terminal 2: Start the integrated UI
streamlit run integrated_mlb_app.py
```

## Technical Notes

### MLB API Usage
The application connects to the MLB Stats API to fetch:
- Game schedules and live data
- Player statistics
- Historical matchup data

### Data Persistence
The application uses a local database to cache:
- Season statistics
- Recent player performance data
- Historical player vs. pitcher matchups

This reduces API calls and improves performance.

### Fallback Mechanisms
If the analysis API server is unavailable, the application will:
1. Attempt to perform direct calculations using MLB API data
2. Fall back to mock data if all else fails

## Future Enhancements
- Add support for visualization of player stats
- Implement historical game lookup and analysis
- Add predictive modeling for game outcomes
- Incorporate additional player metrics beyond OPS