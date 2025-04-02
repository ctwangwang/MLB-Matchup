import streamlit as st
import pandas as pd
import datetime
import time
from utils.helpers import convert_stat_to_float, convert_stat_to_int


def switch_to_analysis_tab(pitcher_id, team_id, pitcher_name, team_name):
    """
    Function to switch to the analysis tab with proper data and disable auto-refresh

    This function needs to ensure we're analyzing the correct team's batters against the opposing pitcher.
    """
    # Store analysis parameters in session state
    st.session_state.analyze_pitcher_id = pitcher_id
    st.session_state.analyze_team_id = (
        team_id  # This is the team whose batters we want to analyze
    )
    st.session_state.analyze_pitcher_name = pitcher_name
    st.session_state.analyze_team_name = team_name

    st.session_state.active_tab = "Batter vs. Pitcher Analysis"

    st.session_state.pending_tab_switch = True  # Set a flag instead
    # Force rerun to apply changes immediately
    # st.rerun()


def main_display(
    game_id,
    get_live_data,
    create_baseball_diamond,
    create_hot_cold_zones,
    get_fip_minus_color,
    get_pitcher_war_color,
    get_wrc_plus_color,
    get_batter_war_color,
    get_vs_pitcher_stats,
    API_IMPORTS_SUCCESS,
    get_batter_season_stats,
    get_pitcher_season_stats,
    get_batter_situation_stats,
    get_pitcher_situation_stats,
    get_pitcher_sabermetrics,
    get_batter_sabermetrics,
):
    with st.spinner("Fetching MLB data..."):
        score_data = get_live_data(game_id)

    # Calculate previous season year (this year - 1)
    previous_season = datetime.datetime.now().year - 1

    if not score_data:
        st.warning(
            "Unable to fetch score data. Please check the Game ID and try again."
        )

        # Show common game IDs for reference
        st.info("""
        The game ID might be incorrect or the game data is not available yet.
        Try to select a different game or date.
        """)

        # Show a retry button
        if st.button("Retry"):
            # Just update the refresh timestamp
            # Let Streamlit handle the rerun naturally
            st.session_state.last_refresh = datetime.datetime.now()

        return

    # Create layout with columns
    col1, col2 = st.columns([3, 2])

    with col1:
        # Display team names and scores
        st.header("Score")

        # Create a fixed-height, stable score display
        st.markdown(
            """
        <style>
        .score-container {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .team-score {
            text-align: center;
            width: 48%;
        }
        .team-name {
            font-size: 1.5em;
            font-weight: bold;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .score-value {
            font-size: 4em;
            font-weight: bold;
            height: 100px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div class="score-container">
            <div class="team-score">
                <div class="team-name">{score_data["away_team"]}</div>
                <div class="score-value">{score_data["away_score"]}</div>
            </div>
            <div class="team-score">
                <div class="team-name">{score_data["home_team"]}</div>
                <div class="score-value">{score_data["home_score"]}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Display game status information
        status_color = (
            "green" if score_data["abstract_game_state"] == "Live" else "orange"
        )
        st.markdown(
            f"<p style='text-align: center; color: {status_color};'><b>Status:</b> {score_data['status']}</p>",
            unsafe_allow_html=True,
        )

        # Analyze button callback functions
        def analyze_away_pitcher():
            # For away pitcher (from away team), we want to analyze home team batters
            switch_to_analysis_tab(
                score_data["probable_away_pitcher_id"],
                score_data["home_team_id"],  # Home team's batters against away pitcher
                score_data["probable_away_pitcher"],
                score_data["home_team"],
            )

        def analyze_home_pitcher():
            # For home pitcher (from home team), we want to analyze away team batters
            switch_to_analysis_tab(
                score_data["probable_home_pitcher_id"],
                score_data["away_team_id"],  # Away team's batters against home pitcher
                score_data["probable_home_pitcher"],
                score_data["away_team"],
            )

        def analyze_current_pitcher():
            # Determine which team is batting against the pitcher
            if score_data.get("inning_half") == "top":
                # When it's top of the inning:
                # - Home team is pitching
                # - Away team is batting
                pitcher_team = score_data["home_team"]
                batter_team = score_data["away_team"]
                batter_team_id = score_data["away_team_id"]
            else:
                # When it's bottom of the inning:
                # - Away team is pitching
                # - Home team is batting
                pitcher_team = score_data["away_team"]
                batter_team = score_data["home_team"]
                batter_team_id = score_data["home_team_id"]

            switch_to_analysis_tab(
                score_data["pitcher_id"],
                batter_team_id,  # This is the batting team whose batters we want to analyze
                score_data["pitcher"],
                batter_team,
            )

        # Add analyze buttons for pitchers
        if score_data["abstract_game_state"] == "Preview":
            # Show scheduled start time
            if score_data["start_time"]:
                local_time = score_data["start_time"].astimezone()
                st.markdown(
                    f"<p style='text-align: center;'><b>Scheduled Start:</b> {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}</p>",
                    unsafe_allow_html=True,
                )

            # Display probable pitchers if available
            if score_data.get("probable_away_pitcher") or score_data.get(
                "probable_home_pitcher"
            ):
                st.subheader("Probable Pitchers")

                # Add color legend explaining what each color means
                st.markdown(
                    """
                    <style>
                    .color-legend {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 12px;
                        margin-bottom: 10px;
                        font-size: 0.85em;
                    }
                    .color-item {
                        display: flex;
                        align-items: center;
                    }
                    .color-dot {
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        margin-right: 5px;
                        display: inline-block;
                    }
                    </style>
                    <div class="color-legend">
                        <div class="color-item">
                            <span class="color-dot" style="background-color: red;"></span>
                            <span>MVP</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #EE82EE;"></span>
                            <span>All-Star</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #4169e1;"></span>
                            <span>Starter</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #00FF00;"></span>
                            <span>Role Player</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #F4A460;"></span>
                            <span>Replacement Level</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                away_pitcher = score_data.get("probable_away_pitcher") or "TBD"
                home_pitcher = score_data.get("probable_home_pitcher") or "TBD"

                col_away, col_home = st.columns(2)

                with col_away:
                    st.markdown(f"**{score_data['away_team']}:** {away_pitcher}")

                    # Display away pitcher stats with safe type conversion
                    if API_IMPORTS_SUCCESS and score_data.get(
                        "probable_away_pitcher_id"
                    ):
                        try:
                            pitcher_stats = get_pitcher_season_stats(
                                score_data["probable_away_pitcher_id"], previous_season
                            )

                            if pitcher_stats:
                                # Safely convert values to float
                                avg = convert_stat_to_float(pitcher_stats[0])
                                ops = convert_stat_to_float(pitcher_stats[1])
                                era = convert_stat_to_float(pitcher_stats[2])
                                whip = convert_stat_to_float(pitcher_stats[3])

                                st.markdown(f"**{previous_season} Season Stats:**")
                                stats_df = pd.DataFrame(
                                    {
                                        "Stat": ["ERA", "WHIP", "AVG", "OPS"],
                                        "Value": [
                                            f"{era:.2f}",
                                            f"{whip:.2f}",
                                            f"{avg:.3f}",
                                            f"{ops:.3f}",
                                        ],
                                    }
                                )
                                st.dataframe(
                                    stats_df, hide_index=True, use_container_width=True
                                )

                                # Advanced metrics with safe conversion
                                if get_pitcher_sabermetrics:
                                    try:
                                        sabermetrics = get_pitcher_sabermetrics(
                                            score_data["probable_away_pitcher_id"],
                                            previous_season,
                                        )

                                        if sabermetrics:
                                            fip_minus = convert_stat_to_int(
                                                sabermetrics[1]
                                            )
                                            pWAR = convert_stat_to_float(
                                                sabermetrics[2]
                                            )

                                            # Use HTML for layout instead of nested columns
                                            st.markdown(
                                                f"""
                                                <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                                                    <div style='text-align: center; width: 48%;'>
                                                        <p style='margin-bottom: 0;'>FIP-</p>
                                                        <div style='background-color: {get_fip_minus_color(fip_minus)}; 
                                                        padding: 5px; border-radius: 5px; color: white; font-weight: bold;'>
                                                        {fip_minus}</div>
                                                    </div>
                                                    <div style='text-align: center; width: 48%;'>
                                                        <p style='margin-bottom: 0;'>pWAR</p>
                                                        <div style='background-color: {get_pitcher_war_color(pWAR)}; 
                                                        padding: 5px; border-radius: 5px; color: white; font-weight: bold;'>
                                                        {pWAR:.1f}</div>
                                                    </div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )
                                    except Exception as e:
                                        st.warning(
                                            f"Could not load advanced metrics: {e}"
                                        )
                        except Exception as e:
                            st.warning(f"Could not load pitcher stats: {e}")

                    if score_data.get("probable_away_pitcher_id"):
                        if st.button(
                            f"Analyze {score_data['home_team']} batters vs {away_pitcher}",
                            key="away_pitcher_analysis",
                            on_click=analyze_away_pitcher,
                        ):
                            # The on_click handler does the work
                            pass
                with col_home:
                    st.markdown(f"**{score_data['home_team']}:** {home_pitcher}")

                    # Display home pitcher stats with safe type conversion
                    if API_IMPORTS_SUCCESS and score_data.get(
                        "probable_home_pitcher_id"
                    ):
                        try:
                            pitcher_stats = get_pitcher_season_stats(
                                score_data["probable_home_pitcher_id"], previous_season
                            )

                            if pitcher_stats:
                                # Safely convert values to float
                                avg = convert_stat_to_float(pitcher_stats[0])
                                ops = convert_stat_to_float(pitcher_stats[1])
                                era = convert_stat_to_float(pitcher_stats[2])
                                whip = convert_stat_to_float(pitcher_stats[3])

                                st.markdown(f"**{previous_season} Season Stats:**")
                                stats_df = pd.DataFrame(
                                    {
                                        "Stat": ["ERA", "WHIP", "AVG", "OPS"],
                                        "Value": [
                                            f"{era:.2f}",
                                            f"{whip:.2f}",
                                            f"{avg:.3f}",
                                            f"{ops:.3f}",
                                        ],
                                    }
                                )
                                st.dataframe(
                                    stats_df, hide_index=True, use_container_width=True
                                )

                                # Advanced metrics with safe conversion
                                if get_pitcher_sabermetrics:
                                    try:
                                        sabermetrics = get_pitcher_sabermetrics(
                                            score_data["probable_home_pitcher_id"],
                                            previous_season,
                                        )

                                        if sabermetrics:
                                            fip_minus = convert_stat_to_int(
                                                sabermetrics[1]
                                            )
                                            pWAR = convert_stat_to_float(
                                                sabermetrics[2]
                                            )

                                            # Use HTML for layout instead of nested columns
                                            st.markdown(
                                                f"""
                                                <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
                                                    <div style='text-align: center; width: 48%;'>
                                                        <p style='margin-bottom: 0;'>FIP-</p>
                                                        <div style='background-color: {get_fip_minus_color(fip_minus)}; 
                                                        padding: 5px; border-radius: 5px; color: white; font-weight: bold;'>
                                                        {fip_minus}</div>
                                                    </div>
                                                    <div style='text-align: center; width: 48%;'>
                                                        <p style='margin-bottom: 0;'>pWAR</p>
                                                        <div style='background-color: {get_pitcher_war_color(pWAR)}; 
                                                        padding: 5px; border-radius: 5px; color: white; font-weight: bold;'>
                                                        {pWAR:.1f}</div>
                                                    </div>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )
                                    except Exception as e:
                                        st.warning(
                                            f"Could not load advanced metrics: {e}"
                                        )
                        except Exception as e:
                            st.warning(f"Could not load pitcher stats: {e}")

                    if score_data.get("probable_home_pitcher_id"):
                        if st.button(
                            f"Analyze {score_data['away_team']} batters vs {home_pitcher}",
                            key="home_pitcher_analysis",
                            on_click=analyze_home_pitcher,
                        ):
                            # The on_click handler does the work
                            pass

        elif score_data["abstract_game_state"] == "Live":
            # Show inning information
            st.markdown(
                f"<p style='text-align: center;'><b>Inning:</b> {score_data['inning_state']} of {score_data['inning']}</p>",
                unsafe_allow_html=True,
            )

            # Box Score (inning-by-inning) with fixed height
            st.subheader("Box Score")

            # Set up DataFrame for box score
            inning_data = score_data["inning_scores"]

            # Format the DataFrame
            box_score = pd.DataFrame(
                {
                    "Team": [
                        score_data["away_team_abbrev"],
                        score_data["home_team_abbrev"],
                    ],
                }
            )

            # Add innings columns with proper type handling
            for i in range(1, 10):
                inning_col = f"{i}"
                inning_data = (
                    score_data["inning_scores"][i - 1]
                    if i <= len(score_data["inning_scores"])
                    else {}
                )

                away_val = inning_data.get("away", "-")
                home_val = inning_data.get("home", "-")

                # Ensure values are either integers or strings
                try:
                    away_val = int(away_val) if str(away_val).isdigit() else "-"
                    home_val = int(home_val) if str(home_val).isdigit() else "-"
                except (ValueError, TypeError):
                    away_val = "-"
                    home_val = "-"

                box_score[inning_col] = [away_val, home_val]

            # Add R (Runs) column with proper type handling
            box_score["R"] = [
                int(score_data["away_score"])
                if str(score_data["away_score"]).isdigit()
                else "-",
                int(score_data["home_score"])
                if str(score_data["home_score"]).isdigit()
                else "-",
            ]

            # Convert all numeric columns to object type to avoid Arrow serialization issues
            for col in box_score.columns[1:]:  # Skip Team column
                box_score[col] = box_score[col].astype(str).replace("nan", "-")

            # Display the box score with fixed height
            st.markdown(
                """
            <style>
            .fixed-height-table {
                height: 150px !important;
                overflow-y: hidden !important;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            # Display the box score
            st.dataframe(
                box_score, hide_index=True, use_container_width=True, height=130
            )
            # Display current play information in a fixed-height container
            current_play_info = (
                score_data["current_play"]
                if isinstance(score_data["current_play"], str)
                else "No play information available"
            )

            st.subheader("Current Play")

            st.markdown(
                f"""
            <div style="height: 60px; overflow-y: auto; margin-bottom: 20px; padding: 8px; background-color: rgba(70, 70, 70, 0.1); border-radius: 5px;">
                {current_play_info}
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Display pitcher and batter information in fixed containers
            pitcher_info = (
                score_data["pitcher"]
                if score_data["pitcher"] != "N/A"
                else "Not available"
            )
            batter_info = (
                score_data["batter"]
                if score_data["batter"] != "N/A"
                else "Not available"
            )

            st.markdown(
                f"""
            <style>
            .player-container {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
                height: 60px;
            }}
            .player-box {{
                width: 48%;
                padding: 10px;
                background-color: rgba(70, 70, 70, 0.1);
                border-radius: 5px;
                display: flex;
                align-items: center;
            }}
            .player-label {{
                font-weight: bold;
                margin-right: 5px;
            }}
            </style>
            
            <div class="player-container">
                <div class="player-box">
                    <span class="player-label">Pitcher:</span> {pitcher_info}
                </div>
                <div class="player-box">
                    <span class="player-label">Batter:</span> {batter_info}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            # In the main_display function in ui_components.py

            # Current Pitcher and Batter section
            if score_data.get("pitcher_id") and score_data.get("batter_id"):
                st.header("Current Players")

                # Add color legend explaining what each color means
                st.markdown(
                    """
                    <style>
                    .color-legend {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 12px;
                        margin-bottom: 10px;
                        font-size: 0.85em;
                    }
                    .color-item {
                        display: flex;
                        align-items: center;
                    }
                    .color-dot {
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        margin-right: 5px;
                        display: inline-block;
                    }
                    </style>
                    <div class="color-legend">
                        <div class="color-item">
                            <span class="color-dot" style="background-color: red;"></span>
                            <span>MVP</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #EE82EE;"></span>
                            <span>All-Star</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #4169e1;"></span>
                            <span>Starter</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #00FF00;"></span>
                            <span>Role Player</span>
                        </div>
                        <div class="color-item">
                            <span class="color-dot" style="background-color: #F4A460;"></span>
                            <span>Replacement Level</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Determine which team the pitcher and batter belong to
                if score_data.get("inning_half") == "top":
                    pitcher_team = score_data["home_team"]
                    batter_team = score_data["away_team"]
                else:
                    pitcher_team = score_data["away_team"]
                    batter_team = score_data["home_team"]

                # Pitcher info and stats
                st.subheader("Current Pitcher")
                st.markdown(f"{pitcher_team} : {score_data['pitcher']}")

                # Add pitcher season stats
                if (
                    API_IMPORTS_SUCCESS
                    and get_pitcher_season_stats
                    and get_pitcher_sabermetrics
                ):
                    pitcher_id = score_data["pitcher_id"]
                    pitcher_stats = get_pitcher_season_stats(
                        pitcher_id, previous_season
                    )
                    pitcher_saber = get_pitcher_sabermetrics(
                        pitcher_id, previous_season
                    )

                    if pitcher_stats or pitcher_saber:
                        st.markdown(
                            f"**{score_data['pitcher']}'s Season {previous_season} Stats:**"
                        )
                        wins_val = (
                            int(pitcher_stats[8])
                            if pitcher_stats and pitcher_stats[8] is not None
                            else "-"
                        )
                        losses_val = (
                            int(pitcher_stats[9])
                            if pitcher_stats and pitcher_stats[9] is not None
                            else "-"
                        )
                        holds_val = (
                            int(pitcher_stats[10])
                            if pitcher_stats and pitcher_stats[10] is not None
                            else "-"
                        )
                        saves_val = (
                            int(pitcher_stats[11])
                            if pitcher_stats and pitcher_stats[11] is not None
                            else "-"
                        )
                        # Process values for color coding
                        era_val = (
                            f"{float(pitcher_stats[2]):.2f}"
                            if pitcher_stats and pitcher_stats[2] is not None
                            else "-"
                        )
                        whip_val = (
                            f"{float(pitcher_stats[3]):.2f}"
                            if pitcher_stats and pitcher_stats[3] is not None
                            else "-"
                        )

                        fip_minus_val = (
                            int(pitcher_saber[1])
                            if pitcher_saber and pitcher_saber[1] is not None
                            else "-"
                        )
                        fip_minus_color = (
                            get_fip_minus_color(fip_minus_val)
                            if fip_minus_val != "-"
                            else "white"
                        )

                        war_val = (
                            float(pitcher_saber[2])
                            if pitcher_saber and pitcher_saber[2] is not None
                            else "-"
                        )
                        war_display = f"{war_val:.1f}" if war_val != "-" else "-"
                        war_color = (
                            get_pitcher_war_color(war_val)
                            if war_val != "-"
                            else "white"
                        )

                        # Use HTML to display colored values
                        st.markdown(
                            f"""
                        <style>
                        .stats-table {{
                            width: 100%;
                            text-align: center;
                            border-collapse: collapse;
                            margin-bottom: 15px;
                        }}
                        .stats-table th {{
                            padding: 8px;
                            background-color: #2c3e50;  /* Dark blue header */
                            color: white;
                            font-weight: bold;
                            border: 1px solid #555;
                        }}
                        .stats-table td {{
                            padding: 8px;
                            border: 1px solid #555;
                            background-color: #1e2933;  /* Slightly lighter than the main background */
                        }}
                        </style>
                        <table class="stats-table">
                            <tr>
                                <th>W</th>
                                <th>L</th>
                                <th>HLD</th>
                                <th>SV</th>
                                <th>ERA</th>
                                <th>WHIP</th>
                                <th>FIP-</th>
                                <th>WAR</th>
                            </tr>
                            <tr>
                                <td>{wins_val}</td>
                                <td>{losses_val}</td>
                                <td>{holds_val}</td>
                                <td>{saves_val}</td>
                                <td>{era_val}</td>
                                <td>{whip_val}</td>
                                <td style="color: {fip_minus_color}; font-weight: bold;">{fip_minus_val}</td>
                                <td style="color: {war_color}; font-weight: bold;">{war_display}</td>
                            </tr>
                        </table>
                        """,
                            unsafe_allow_html=True,
                        )

                # Batter info and stats
                st.subheader("Current Batter")
                st.markdown(f"{batter_team} : {score_data['batter']}")

                # Batter season stats
                if (
                    API_IMPORTS_SUCCESS
                    and get_batter_season_stats
                    and get_batter_sabermetrics
                ):
                    batter_id = score_data.get("batter_id")
                    batter_name = score_data["batter"]

                    # Get current season stats for the batter
                    season_stats = None
                    saber_stats = None
                    if batter_id:
                        season_stats = get_batter_season_stats(
                            batter_id, previous_season
                        )
                        saber_stats = get_batter_sabermetrics(
                            batter_id, previous_season
                        )

                    # Display season stats for the batter
                    if season_stats or saber_stats:
                        st.markdown(
                            f"**{batter_name}'s Season {previous_season} Stats:**"
                        )

                        hr_val = (
                            int(season_stats[6])
                            if season_stats and season_stats[6] is not None
                            else "-"
                        )
                        rbi_val = (
                            int(season_stats[7])
                            if season_stats and season_stats[7] is not None
                            else "-"
                        )
                        # Process values for color coding
                        avg_val = (
                            f"{float(season_stats[0]):.3f}"
                            if season_stats and season_stats[0] is not None
                            else "-"
                        )
                        obp_val = (
                            f"{float(season_stats[1]):.3f}"
                            if season_stats and season_stats[1] is not None
                            else "-"
                        )
                        slg_val = (
                            f"{float(season_stats[2]):.3f}"
                            if season_stats and season_stats[2] is not None
                            else "-"
                        )
                        ops_val = (
                            f"{float(season_stats[3]):.3f}"
                            if season_stats and season_stats[3] is not None
                            else "-"
                        )

                        wrc_plus_val = (
                            int(saber_stats[1])
                            if saber_stats and saber_stats[1] is not None
                            else "-"
                        )
                        wrc_plus_color = (
                            get_wrc_plus_color(wrc_plus_val)
                            if wrc_plus_val != "-"
                            else "white"
                        )

                        war_val = (
                            float(saber_stats[2])
                            if saber_stats and saber_stats[2] is not None
                            else "-"
                        )
                        war_display = f"{war_val:.1f}" if war_val != "-" else "-"
                        war_color = (
                            get_batter_war_color(war_val) if war_val != "-" else "white"
                        )

                        # Use HTML to display colored values
                        st.markdown(
                            f"""
                        <style>
                        .stats-table {{
                            width: 100%;
                            text-align: center;
                            border-collapse: collapse;
                            margin-bottom: 15px;
                        }}
                        .stats-table th {{
                            padding: 8px;
                            background-color: #2c3e50;  /* Dark blue header */
                            color: white;
                            font-weight: bold;
                            border: 1px solid #555;
                        }}
                        .stats-table td {{
                            padding: 8px;
                            border: 1px solid #555;
                            background-color: #1e2933;  /* Slightly lighter than the main background */
                        }}
                        </style>
                        <table class="stats-table">
                            <tr>
                                <th>HR</th>
                                <th>RBI</th>
                                <th>AVG</th>
                                <th>OBP</th>
                                <th>SLG</th>
                                <th>OPS</th>
                                <th>wRC+</th>
                                <th>WAR</th>
                            </tr>
                            <tr>
                                <td>{hr_val}</td>
                                <td>{rbi_val}</td>
                                <td>{avg_val}</td>
                                <td>{obp_val}</td>
                                <td>{slg_val}</td>
                                <td>{ops_val}</td>
                                <td style="color: {wrc_plus_color}; font-weight: bold;">{wrc_plus_val}</td>
                                <td style="color: {war_color}; font-weight: bold;">{war_display}</td>
                            </tr>
                        </table>
                        """,
                            unsafe_allow_html=True,
                        )

                # Matchup Stats section
                st.header("Matchup Stats")

                # Batter vs Pitcher matchup stats
                if API_IMPORTS_SUCCESS:
                    pitcher_id = score_data.get("pitcher_id")
                    batter_id = score_data.get("batter_id")

                    # Get matchup data
                    matchup_stats = get_vs_pitcher_stats(batter_id, pitcher_id)

                    if matchup_stats:
                        st.markdown(
                            f"**{score_data['batter']} vs {score_data['pitcher']} (Career)**"
                        )
                        st.markdown(
                            f"""
                        <style>
                        .stats-table {{
                            width: 100%;
                            text-align: center;
                            border-collapse: collapse;
                            margin-bottom: 15px;
                        }}
                        .stats-table th {{
                            padding: 8px;
                            background-color: #2c3e50;  /* Dark blue header */
                            color: white;
                            font-weight: bold;
                            border: 1px solid #555;
                        }}
                        .stats-table td {{
                            padding: 8px;
                            border: 1px solid #555;
                            background-color: #1e2933;  /* Slightly lighter than the main background */
                        }}
                        </style>
                        <table class="stats-table">
                            <tr>
                                <th>AVG</th>
                                <th>OBP</th>
                                <th>SLG</th>
                                <th>OPS</th>
                            </tr>
                            <tr>
                                <td>{matchup_stats["avg"]}</td>
                                <td>{matchup_stats["obp"]}</td>
                                <td>{matchup_stats["slg"]}</td>
                                <td>{matchup_stats["ops"]}</td>
                            </tr>
                        </table>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info(
                            f"No head-to-head matchup data available for {batter_name} vs {score_data['pitcher']}"
                        )

                # Analyze button
                if st.button(
                    f"Analyze {batter_team} batters vs {score_data['pitcher']}",
                    key="current_pitcher_analysis",
                    on_click=analyze_current_pitcher,
                ):
                    # The on_click handler does the work
                    pass

            # Situation Stats display
            if score_data.get("batter_situation") and score_data.get(
                "pitcher_situation"
            ):
                st.header("Situation Statistics")

                # Create columns - pitcher first, then batter
                col_pitch, col_bat = st.columns(2)

                with col_pitch:
                    if score_data.get("pitcher_id"):
                        # Pitcher vs Batter type stats
                        if score_data.get("pitcher_situation"):
                            pitcher_stats = get_pitcher_situation_stats(
                                score_data["pitcher_id"],
                                score_data["pitcher_situation"]["code"],
                                2024,
                            )
                            if pitcher_stats:
                                st.markdown(
                                    f"**{score_data['pitcher']} {score_data['pitcher_situation']['description']} (Season {pitcher_stats['season']})**"
                                )
                                # Extract pitcher situation stats with unique variable names
                                p_sit_avg = (
                                    f"{pitcher_stats['avg']:.3f}"
                                    if pitcher_stats.get("avg") is not None
                                    else "-"
                                )
                                p_sit_obp = (
                                    f"{pitcher_stats['obp']:.3f}"
                                    if pitcher_stats.get("obp") is not None
                                    else "-"
                                )
                                p_sit_slg = (
                                    f"{pitcher_stats['slg']:.3f}"
                                    if pitcher_stats.get("slg") is not None
                                    else "-"
                                )
                                p_sit_ops = (
                                    f"{pitcher_stats['ops']:.3f}"
                                    if pitcher_stats.get("ops") is not None
                                    else "-"
                                )

                                st.markdown(
                                    f"""
                                <style>
                                .stats-table {{
                                    width: 100%;
                                    text-align: center;
                                    border-collapse: collapse;
                                    margin-bottom: 15px;
                                }}
                                .stats-table th {{
                                    padding: 8px;
                                    background-color: #2c3e50;  /* Dark blue header */
                                    color: white;
                                    font-weight: bold;
                                    border: 1px solid #555;
                                }}
                                .stats-table td {{
                                    padding: 8px;
                                    border: 1px solid #555;
                                    background-color: #1e2933;  /* Slightly lighter than the main background */
                                }}
                                </style>
                                <table class="stats-table">
                                    <tr>
                                        <th>AVG</th>
                                        <th>OBP</th>
                                        <th>SLG</th>
                                        <th>OPS</th>
                                    </tr>
                                    <tr>
                                        <td>{p_sit_avg}</td>
                                        <td>{p_sit_obp}</td>
                                        <td>{p_sit_slg}</td>
                                        <td>{p_sit_ops}</td>
                                    </tr>
                                </table>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.info(
                                    f"No stats available for {score_data['pitcher']} against current batter type"
                                )

                        # Pitcher menOnBase stats
                        if score_data.get("men_on_base_situation"):
                            pitcher_men_stats = get_pitcher_situation_stats(
                                score_data["pitcher_id"],
                                score_data["men_on_base_situation"]["code"],
                                2024,
                            )
                            if pitcher_men_stats:
                                st.markdown(
                                    f"**{score_data['pitcher']} when {score_data['men_on_base_situation']['description']} (Season {pitcher_men_stats['season']})**"
                                )
                                # In the situation stats section, modify the DataFrame creation to:
                                p_men_avg = (
                                    f"{pitcher_men_stats['avg']:.3f}"
                                    if pitcher_men_stats.get("avg") is not None
                                    else "-"
                                )
                                p_men_obp = (
                                    f"{pitcher_men_stats['obp']:.3f}"
                                    if pitcher_men_stats.get("obp") is not None
                                    else "-"
                                )
                                p_men_slg = (
                                    f"{pitcher_men_stats['slg']:.3f}"
                                    if pitcher_men_stats.get("slg") is not None
                                    else "-"
                                )
                                p_men_ops = (
                                    f"{pitcher_men_stats['ops']:.3f}"
                                    if pitcher_men_stats.get("ops") is not None
                                    else "-"
                                )

                                st.markdown(
                                    f"""
                                <style>
                                .stats-table {{
                                    width: 100%;
                                    text-align: center;
                                    border-collapse: collapse;
                                    margin-bottom: 15px;
                                }}
                                .stats-table th {{
                                    padding: 8px;
                                    background-color: #2c3e50;  /* Dark blue header */
                                    color: white;
                                    font-weight: bold;
                                    border: 1px solid #555;
                                }}
                                .stats-table td {{
                                    padding: 8px;
                                    border: 1px solid #555;
                                    background-color: #1e2933;  /* Slightly lighter than the main background */
                                }}
                                </style>
                                <table class="stats-table">
                                    <tr>
                                        <th>AVG</th>
                                        <th>OBP</th>
                                        <th>SLG</th>
                                        <th>OPS</th>
                                    </tr>
                                    <tr>
                                        <td>{p_men_avg}</td>
                                        <td>{p_men_obp}</td>
                                        <td>{p_men_slg}</td>
                                        <td>{p_men_ops}</td>
                                    </tr>
                                </table>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.info(
                                    f"No stats available for {score_data['pitcher']} in current base situation"
                                )

                with col_bat:
                    if score_data.get("batter_id"):
                        # Batter vs Pitcher type stats
                        if score_data.get("batter_situation"):
                            batter_stats = get_batter_situation_stats(
                                score_data["batter_id"],
                                score_data["batter_situation"]["code"],
                                2024,
                            )
                            if batter_stats:
                                st.markdown(
                                    f"**{score_data['batter']} {score_data['batter_situation']['description']} (Season {batter_stats['season']})**"
                                )
                                # In the situation stats section, modify the DataFrame creation to:
                                b_sit_avg = (
                                    f"{batter_stats['avg']:.3f}"
                                    if batter_stats.get("avg") is not None
                                    else "-"
                                )
                                b_sit_obp = (
                                    f"{batter_stats['obp']:.3f}"
                                    if batter_stats.get("obp") is not None
                                    else "-"
                                )
                                b_sit_slg = (
                                    f"{batter_stats['slg']:.3f}"
                                    if batter_stats.get("slg") is not None
                                    else "-"
                                )
                                b_sit_ops = (
                                    f"{batter_stats['ops']:.3f}"
                                    if batter_stats.get("ops") is not None
                                    else "-"
                                )

                                st.markdown(
                                    f"""
                                <style>
                                .stats-table {{
                                    width: 100%;
                                    text-align: center;
                                    border-collapse: collapse;
                                    margin-bottom: 15px;
                                }}
                                .stats-table th {{
                                    padding: 8px;
                                    background-color: #2c3e50;  /* Dark blue header */
                                    color: white;
                                    font-weight: bold;
                                    border: 1px solid #555;
                                }}
                                .stats-table td {{
                                    padding: 8px;
                                    border: 1px solid #555;
                                    background-color: #1e2933;  /* Slightly lighter than the main background */
                                }}
                                </style>
                                <table class="stats-table">
                                    <tr>
                                        <th>AVG</th>
                                        <th>OBP</th>
                                        <th>SLG</th>
                                        <th>OPS</th>
                                    </tr>
                                    <tr>
                                        <td>{b_sit_avg}</td>
                                        <td>{b_sit_obp}</td>
                                        <td>{b_sit_slg}</td>
                                        <td>{b_sit_ops}</td>
                                    </tr>
                                </table>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.info(
                                    f"No stats available for {score_data['batter']} against current pitcher type"
                                )

                        # Batter menOnBase stats
                        if score_data.get("men_on_base_situation"):
                            batter_men_stats = get_batter_situation_stats(
                                score_data["batter_id"],
                                score_data["men_on_base_situation"]["code"],
                                2024,
                            )
                            if batter_men_stats:
                                st.markdown(
                                    f"**{score_data['batter']} when {score_data['men_on_base_situation']['description']} (Season {batter_men_stats['season']})**"
                                )
                                # In the situation stats section, modify the DataFrame creation to:
                                b_men_avg = (
                                    f"{batter_men_stats['avg']:.3f}"
                                    if batter_men_stats.get("avg") is not None
                                    else "-"
                                )
                                b_men_obp = (
                                    f"{batter_men_stats['obp']:.3f}"
                                    if batter_men_stats.get("obp") is not None
                                    else "-"
                                )
                                b_men_slg = (
                                    f"{batter_men_stats['slg']:.3f}"
                                    if batter_men_stats.get("slg") is not None
                                    else "-"
                                )
                                b_men_ops = (
                                    f"{batter_men_stats['ops']:.3f}"
                                    if batter_men_stats.get("ops") is not None
                                    else "-"
                                )

                                st.markdown(
                                    f"""
                                <style>
                                .stats-table {{
                                    width: 100%;
                                    text-align: center;
                                    border-collapse: collapse;
                                    margin-bottom: 15px;
                                }}
                                .stats-table th {{
                                    padding: 8px;
                                    background-color: #2c3e50;  /* Dark blue header */
                                    color: white;
                                    font-weight: bold;
                                    border: 1px solid #555;
                                }}
                                .stats-table td {{
                                    padding: 8px;
                                    border: 1px solid #555;
                                    background-color: #1e2933;  /* Slightly lighter than the main background */
                                }}
                                </style>
                                <table class="stats-table">
                                    <tr>
                                        <th>AVG</th>
                                        <th>OBP</th>
                                        <th>SLG</th>
                                        <th>OPS</th>
                                    </tr>
                                    <tr>
                                        <td>{b_men_avg}</td>
                                        <td>{b_men_obp}</td>
                                        <td>{b_men_slg}</td>
                                        <td>{b_men_ops}</td>
                                    </tr>
                                </table>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.info(
                                    f"No stats available for {score_data['batter']} in current base situation"
                                )
    with col2:
        # Game situation visualization with fixed heights
        if score_data["abstract_game_state"] == "Live":
            st.header("Game Situation")

            # Get count and outs information safely
            balls = min(
                int(score_data["balls"])
                if score_data["balls"] not in [None, "-"]
                else 0,
                3,
            )
            strikes = min(
                int(score_data["strikes"])
                if score_data["strikes"] not in [None, "-"]
                else 0,
                2,
            )
            outs = min(
                int(score_data["outs"]) if score_data["outs"] not in [None, "-"] else 0,
                2,
            )

            # Display count and outs with custom CSS for consistent height
            st.markdown(
                f"""
            <style>
            .metrics-container {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 20px;
            }}
            .metric-box {{
                width: 48%;
                padding: 15px 10px;
                background-color: rgba(70, 70, 70, 0.1);
                border-radius: 5px;
                text-align: center;
                min-height: 100px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .metric-label {{
                font-weight: bold;
                font-size: 1.2em;
                margin-bottom: 10px;
            }}
            .emoji-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                flex-grow: 1;
                justify-content: center;
            }}
            .emoji-row {{
                display: flex;
                gap: 10px;
            }}
            .emoji-light {{
                font-size: 1.8em;
            }}
            </style>

            <div class="metrics-container">
                <div class="metric-box">
                    <div class="metric-label">Count</div>
                    <div class="emoji-container">
                        <div class="emoji-row">
                            {"🟡" * strikes + "⚪" * (2 - strikes)}
                        </div>
                        <div class="emoji-row">
                            {"🟢" * balls + "⚪" * (3 - balls)}
                        </div>
                    </div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Outs</div>
                    <div class="emoji-container">
                        <div class="emoji-row">
                            {"🔴" * outs + "⚪" * (2 - outs)}
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Display baseball diamond with fixed height
            st.subheader("Baseball Diamond")
            baseball_fig = create_baseball_diamond(score_data["bases_occupied"])

            # Adjust the chart height and remove extra spacing
            st.plotly_chart(
                baseball_fig,
                use_container_width=True,
                height=300,  # Set height directly here
            )
            # Add this new section for hot/cold zones
            if score_data.get("batter_hot_cold_zones"):
                st.subheader("Batter Hot/Cold Zones")
                # Add stat type selector
                stat_options = ["OPS", "AVG", "Exit Velocity"]
                stat_mapping = {
                    "OPS": "onBasePlusSlugging",
                    "AVG": "battingAverage",
                    "Exit Velocity": "exitVelocity",
                }

                selected_stat = st.selectbox(
                    "Select Stat Type:",
                    options=stat_options,
                    index=0,
                    key="hot_zone_stat_type",
                )

                mapped_stat = stat_mapping[selected_stat]

                # Create and display the hot/cold zones visualization
                hot_zones_fig = create_hot_cold_zones(
                    score_data["batter_hot_cold_zones"],
                    stat_type=mapped_stat,
                    batter_handedness=score_data.get("batter_handedness"),
                )

                if hot_zones_fig:
                    st.plotly_chart(hot_zones_fig, use_container_width=True)
                else:
                    st.info("No hot/cold zone data available for this batter.")
        elif score_data.get("abstract_game_state") == "Preview":
            # For preview games, show venue and time information
            st.header("Game Preview")

            # Show venue info if available
            venue = score_data.get("venue", "")
            if venue:
                st.markdown(f"**Venue:** {venue}")

            # Calculate time until game starts if start_time is available
            if score_data.get("start_time"):
                now = datetime.datetime.now(datetime.timezone.utc)
                start_time = score_data["start_time"]
                time_diff = start_time - now

                # Only show if start time is in the future
                if time_diff.total_seconds() > 0:
                    # Format time until game
                    days = time_diff.days
                    hours, remainder = divmod(time_diff.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)

                    time_str = ""
                    if days > 0:
                        time_str += f"{days} days, "
                    if hours > 0 or days > 0:
                        time_str += f"{hours} hours, "

                    time_str += f"{minutes} minutes"

                    st.subheader("Time Until First Pitch")
                    st.info(time_str)


def display_analysis_tab(
    team_id,
    pitcher_id,
    team_name,
    pitcher_name,
    display_hitter_data,
    get_batter_analysis,
    API_IMPORTS_SUCCESS,
    API_BASE_URL,
    get_vs_pitcher_stats,
    get_batter_season_stats,
    get_batter_vs_pitcher_stats,
    MLB_TEAMS,
):
    """
    Display the batter vs pitcher analysis tab with consistent styling
    """
    import streamlit as st

    st.markdown(f"### Analyzing {team_name} batters vs {pitcher_name}")

    # Add consistent styling for all tables in this tab
    st.markdown(
        """
        <style>
        .stats-table {
            width: 100%;
            text-align: center;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        .stats-table th {
            padding: 8px;
            background-color: #2c3e50;  /* Dark blue header */
            color: white;
            font-weight: bold;
            border: 1px solid #555;
        }
        .stats-table td {
            padding: 8px;
            border: 1px solid #555;
            background-color: #1e2933;  /* Slightly lighter than the main background */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Perform the analysis
    with st.spinner(f"Analyzing {team_name} batters against {pitcher_name}..."):
        analysis_data = get_batter_analysis(
            team_id,
            pitcher_id,
            API_IMPORTS_SUCCESS,
            API_BASE_URL,
            get_vs_pitcher_stats,
            get_batter_season_stats,
            get_batter_vs_pitcher_stats,
        )

        # Display results
        if analysis_data:
            if analysis_data.get("best_season_hitter"):
                display_hitter_data(
                    f"🏆 Season Best OPS Batter ({team_name})",
                    analysis_data.get("best_season_hitter"),
                )

            if analysis_data.get("best_recent_hitter"):
                display_hitter_data(
                    f"📈 Last 5 Games Best OPS Batter ({team_name})",
                    analysis_data.get("best_recent_hitter"),
                )

            if analysis_data.get("best_vs_pitcher_hitter"):
                display_hitter_data(
                    f"🔥 Best OPS vs {pitcher_name} ({team_name})",
                    analysis_data.get("best_vs_pitcher_hitter"),
                )

            if analysis_data.get("all_hitters_vs_pitcher"):
                display_hitter_data(
                    f"📊 All Batters vs {pitcher_name} ({team_name})",
                    analysis_data.get("all_hitters_vs_pitcher"),
                )

            if not analysis_data.get(
                "best_vs_pitcher_hitter"
            ) and not analysis_data.get("all_hitters_vs_pitcher"):
                st.info(
                    f"⚠️ No historical matchup data found for {team_name} batters against {pitcher_name}"
                )
        else:
            st.error("Failed to retrieve analysis data")


def add_deepseek_analysis_to_live_tracker():
    """Add DeepSeek analysis component to the live tracker UI with consistent styling"""
    import streamlit as st
    import datetime

    # Add consistent styling
    st.markdown(
        """
        <style>
        .analysis-container {
            background-color: rgba(30, 41, 51, 0.9);
            border-left: 5px solid #ff4b4b;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Import here to avoid circular imports
    try:
        from api.deepseek_analyzer import get_matchup_insights

        DEEPSEEK_AVAILABLE = True
    except ImportError:
        DEEPSEEK_AVAILABLE = False

    # Create expandable section for DeepSeek analysis
    with st.expander("DeepSeek AI Matchup Analysis", expanded=True):
        if not DEEPSEEK_AVAILABLE:
            st.warning(
                "DeepSeek AI integration is not available. "
                "Make sure you have installed the DeepSeek API module."
            )
            return

        try:
            from config.api_keys import DEEPSEEK_API_KEY

            api_key = DEEPSEEK_API_KEY
        except ImportError:
            # Fallback to environment variable
            import os

            api_key = os.environ.get("DEEPSEEK_API_KEY")

        if not api_key:
            st.warning(
                "DeepSeek API key not configured. Please set the DEEPSEEK_API_KEY environment variable. "
                "You can get an API key from DeepSeek's website."
            )

            # Allow user to input API key in the UI
            temp_api_key = st.text_input(
                "Enter DeepSeek API Key (Temporary, will not be saved)", type="password"
            )

            if temp_api_key:
                os.environ["DEEPSEEK_API_KEY"] = temp_api_key
                st.success(
                    "API key set for this session! You can now analyze matchups."
                )

        # Check if current at-bat data is available
        current_pitcher_id = st.session_state.get("current_pitcher_id")
        current_batter_id = st.session_state.get("current_batter_id")
        current_pitcher_name = st.session_state.get(
            "current_pitcher_name", "Unknown Pitcher"
        )
        current_batter_name = st.session_state.get(
            "current_batter_name", "Unknown Batter"
        )

        if not (current_pitcher_id and current_batter_id):
            st.info("Waiting for active pitcher and batter data...")
            return

        # Create analysis button
        if st.button("Analyze Current Matchup with DeepSeek AI"):
            with st.spinner("Generating DeepSeek analysis..."):
                try:
                    # Call the DeepSeek analysis function
                    analysis = get_matchup_insights(
                        pitcher_id=current_pitcher_id,
                        batter_id=current_batter_id,
                        pitcher_name=current_pitcher_name,
                        batter_name=current_batter_name,
                    )

                    # Display the analysis
                    st.markdown("### Matchup Analysis")
                    st.markdown(
                        f"**{current_pitcher_name}** vs **{current_batter_name}**"
                    )

                    # Apply styling to the analysis output
                    st.markdown(
                        f"""
                        <div class="analysis-container">
                            {analysis}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Add timestamp
                    st.caption(
                        f"Generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )

                except Exception as e:
                    st.error(f"Error generating analysis: {str(e)}")


def add_deepseek_analysis_to_custom_matchup():
    """Add DeepSeek analysis component to custom matchup analysis UI with consistent styling"""
    import datetime

    # Add consistent styling
    st.markdown(
        """
        <style>
        .analysis-container {
            background-color: rgba(30, 41, 51, 0.9);
            border-left: 5px solid #ff4b4b;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Import here to avoid circular imports
    try:
        from api.deepseek_analyzer import get_matchup_insights

        DEEPSEEK_AVAILABLE = True
    except ImportError:
        DEEPSEEK_AVAILABLE = False

    st.markdown("### DeepSeek AI Advanced Matchup Analysis")

    if not DEEPSEEK_AVAILABLE:
        st.warning(
            "DeepSeek AI integration is not available. "
            "Make sure you have installed the DeepSeek API module."
        )
        return

    # Show API key configuration status
    try:
        from config.api_keys import DEEPSEEK_API_KEY

        api_key = DEEPSEEK_API_KEY
    except ImportError:
        # Fallback to environment variable
        import os

        api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not api_key:
        st.warning(
            "DeepSeek API key not configured. Please set the DEEPSEEK_API_KEY environment variable. "
            "You can get an API key from DeepSeek's website."
        )

        # Allow user to input API key in the UI
        temp_api_key = st.text_input(
            "Enter DeepSeek API Key (Temporary, will not be saved)", type="password"
        )

        if temp_api_key:
            os.environ["DEEPSEEK_API_KEY"] = temp_api_key
            st.success("API key set for this session! You can now analyze matchups.")

    # Get currently selected pitcher and team
    selected_pitcher_id = st.session_state.get("custom_pitcher_id")
    selected_team_id = st.session_state.get("custom_team_id")
    selected_pitcher_name = st.session_state.get(
        "custom_pitcher_name", "Unknown Pitcher"
    )

    if not (selected_pitcher_id and selected_team_id):
        st.info("Please select a team and pitcher first")
        return

    # Get team roster for batter selection
    try:
        from api.mlb_api import get_team_roster

        # Get current year
        current_year = datetime.datetime.now().year

        # Get team roster
        roster = get_team_roster(selected_team_id, current_year)

        # Extract position players
        position_players = [p for p in roster if p.get("position") != "P"]

        # Create dropdown for selecting batter
        if position_players:
            selected_batter = st.selectbox(
                "Select Batter for Analysis",
                options=[(p["full_name"], p["player_id"]) for p in position_players],
                format_func=lambda x: x[0],  # Show only the name in the dropdown
            )

            selected_batter_name, selected_batter_id = selected_batter

            # Create analysis button
            if st.button("Generate AI Matchup Analysis", type="primary"):
                with st.spinner("Generating AI analysis..."):
                    try:
                        # Add a small delay to make the spinner visible
                        time.sleep(1)

                        # Call the DeepSeek analysis function
                        analysis = get_matchup_insights(
                            pitcher_id=selected_pitcher_id,
                            batter_id=selected_batter_id,
                            pitcher_name=selected_pitcher_name,
                            batter_name=selected_batter_name,
                        )

                        # Display the analysis with consistent styling
                        st.markdown("### DeepSeek Analysis")
                        st.markdown(
                            f"**{selected_pitcher_name}** vs **{selected_batter_name}**"
                        )

                        # Apply styling to the analysis output
                        st.markdown(
                            f"""
                            <div class="analysis-container">
                                {analysis}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Add timestamp
                        st.caption(
                            f"Generated at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )

                    except Exception as e:
                        st.error(f"Error generating analysis: {str(e)}")
        else:
            st.warning(f"No position players found in the roster")

    except Exception as e:
        st.error(f"Error loading team roster: {str(e)}")


def update_live_tracker_with_deepseek(main_display_function, score_data):
    """
    Update the main display function to include DeepSeek analyses

    Args:
        main_display_function: Original main_display function
        score_data: The score data from get_live_data
    """
    # Store current pitcher and batter IDs in session state
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

    # Call original display function
    main_display_function()

    # Add DeepSeek analysis if we're in a live game
    if score_data.get("abstract_game_state") == "Live":
        add_deepseek_analysis_to_live_tracker()


def initialize_deepseek():
    """Initialize DeepSeek integration"""
    # Check if DeepSeek module is available
    try:
        import api.deepseek_analyzer

        st.success("DeepSeek AI integration initialized successfully!")
        return True
    except ImportError:
        st.warning(
            "DeepSeek AI integration module not found. "
            "Make sure you have added the deepseek_analyzer.py file to your api folder."
        )
        return False
