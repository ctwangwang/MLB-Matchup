import streamlit as st
import pandas as pd
import datetime


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

    # CRITICAL: First disable auto-refresh, THEN switch tab
    st.session_state.auto_refresh_enabled = False
    st.session_state.active_tab = "Batter vs. Pitcher Analysis"

    # Force rerun to apply changes immediately
    st.rerun()


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

                away_pitcher = score_data.get("probable_away_pitcher") or "TBD"
                home_pitcher = score_data.get("probable_home_pitcher") or "TBD"

                col_away, col_home = st.columns(2)

                with col_away:
                    st.markdown(f"**{score_data['away_team']}:** {away_pitcher}")
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
                            <span class="color-dot" style="background-color: green;"></span>
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

                        # Process values for color coding
                        era_val = (
                            f"{float(pitcher_stats[2]):.2f}" if pitcher_stats else "-"
                        )
                        whip_val = (
                            f"{float(pitcher_stats[3]):.2f}" if pitcher_stats else "-"
                        )

                        fip_minus_val = (
                            int(pitcher_saber[1])
                            if pitcher_saber and pitcher_saber[1]
                            else "-"
                        )
                        fip_minus_color = (
                            get_fip_minus_color(fip_minus_val)
                            if fip_minus_val != "-"
                            else "black"
                        )

                        war_val = (
                            float(pitcher_saber[2])
                            if pitcher_saber and pitcher_saber[2]
                            else "-"
                        )
                        war_display = f"{war_val:.1f}" if war_val != "-" else "-"
                        war_color = (
                            get_pitcher_war_color(war_val)
                            if war_val != "-"
                            else "black"
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
                                <th>ERA</th>
                                <th>WHIP</th>
                                <th>FIP-</th>
                                <th>WAR</th>
                            </tr>
                            <tr>
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

                        # Process values for color coding
                        avg_val = (
                            f"{float(season_stats[0]):.3f}" if season_stats else "-"
                        )
                        obp_val = (
                            f"{float(season_stats[1]):.3f}" if season_stats else "-"
                        )
                        slg_val = (
                            f"{float(season_stats[2]):.3f}" if season_stats else "-"
                        )
                        ops_val = (
                            f"{float(season_stats[3]):.3f}" if season_stats else "-"
                        )

                        wrc_plus_val = (
                            int(saber_stats[1])
                            if saber_stats and saber_stats[1]
                            else "-"
                        )
                        wrc_plus_color = (
                            get_wrc_plus_color(wrc_plus_val)
                            if wrc_plus_val != "-"
                            else "black"
                        )

                        war_val = (
                            float(saber_stats[2])
                            if saber_stats and saber_stats[2]
                            else "-"
                        )
                        war_display = f"{war_val:.1f}" if war_val != "-" else "-"
                        war_color = (
                            get_batter_war_color(war_val) if war_val != "-" else "black"
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
                                <th>AVG</th>
                                <th>OBP</th>
                                <th>SLG</th>
                                <th>OPS</th>
                                <th>wRC+</th>
                                <th>WAR</th>
                            </tr>
                            <tr>
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
                        df_matchup = pd.DataFrame(
                            [
                                {
                                    "AVG": f"{float(matchup_stats.get('avg', 0.000)):.3f}",
                                    "OBP": f"{float(matchup_stats.get('obp', 0.000)):.3f}",
                                    "SLG": f"{float(matchup_stats.get('slg', 0.000)):.3f}",
                                    "OPS": f"{float(matchup_stats.get('ops', 0.000)):.3f}",
                                }
                            ],
                            index=[batter_name],
                        )
                        st.table(df_matchup)
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
                            )
                            if pitcher_stats:
                                st.markdown(
                                    f"**{score_data['pitcher']} {score_data['pitcher_situation']['description']} (Season {pitcher_stats['season']})**"
                                )
                                df = pd.DataFrame(
                                    [
                                        {
                                            "AVG": str(
                                                round(float(pitcher_stats["avg"]), 4)
                                            )
                                            if pitcher_stats.get("avg")
                                            else "-",
                                            "OBP": str(
                                                round(float(pitcher_stats["obp"]), 4)
                                            )
                                            if pitcher_stats.get("obp")
                                            else "-",
                                            "SLG": str(
                                                round(float(pitcher_stats["slg"]), 4)
                                            )
                                            if pitcher_stats.get("slg")
                                            else "-",
                                            "OPS": str(
                                                round(float(pitcher_stats["ops"]), 4)
                                            )
                                            if pitcher_stats.get("ops")
                                            else "-",
                                        }
                                    ],
                                    index=[""],
                                )
                                st.table(df)
                            else:
                                st.info(
                                    f"No stats available for {score_data['pitcher']} against current batter type"
                                )

                        # Pitcher menOnBase stats
                        if score_data.get("men_on_base_situation"):
                            pitcher_men_stats = get_pitcher_situation_stats(
                                score_data["pitcher_id"],
                                score_data["men_on_base_situation"]["code"],
                            )
                            if pitcher_men_stats:
                                st.markdown(
                                    f"**{score_data['pitcher']} when {score_data['men_on_base_situation']['description']} (Season {pitcher_men_stats['season']})**"
                                )
                                # In the situation stats section, modify the DataFrame creation to:
                                df = pd.DataFrame(
                                    [
                                        {
                                            "AVG": str(
                                                round(
                                                    float(pitcher_men_stats["avg"]), 4
                                                )
                                            )
                                            if pitcher_men_stats.get("avg")
                                            else "-",
                                            "OBP": str(
                                                round(
                                                    float(pitcher_men_stats["obp"]), 4
                                                )
                                            )
                                            if pitcher_men_stats.get("obp")
                                            else "-",
                                            "SLG": str(
                                                round(
                                                    float(pitcher_men_stats["slg"]), 4
                                                )
                                            )
                                            if pitcher_men_stats.get("slg")
                                            else "-",
                                            "OPS": str(
                                                round(
                                                    float(pitcher_men_stats["ops"]), 4
                                                )
                                            )
                                            if pitcher_men_stats.get("ops")
                                            else "-",
                                        }
                                    ],
                                    index=[""],
                                )
                                st.table(df)
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
                            )
                            if batter_stats:
                                st.markdown(
                                    f"**{score_data['batter']} {score_data['batter_situation']['description']} (Season {batter_stats['season']})**"
                                )
                                # In the situation stats section, modify the DataFrame creation to:
                                df = pd.DataFrame(
                                    [
                                        {
                                            "AVG": str(
                                                round(float(batter_stats["avg"]), 4)
                                            )
                                            if batter_stats.get("avg")
                                            else "-",
                                            "OBP": str(
                                                round(float(batter_stats["obp"]), 4)
                                            )
                                            if batter_stats.get("obp")
                                            else "-",
                                            "SLG": str(
                                                round(float(batter_stats["slg"]), 4)
                                            )
                                            if batter_stats.get("slg")
                                            else "-",
                                            "OPS": str(
                                                round(float(batter_stats["ops"]), 4)
                                            )
                                            if batter_stats.get("ops")
                                            else "-",
                                        }
                                    ],
                                    index=[""],
                                )
                                st.table(df)
                            else:
                                st.info(
                                    f"No stats available for {score_data['batter']} against current pitcher type"
                                )

                        # Batter menOnBase stats
                        if score_data.get("men_on_base_situation"):
                            batter_men_stats = get_batter_situation_stats(
                                score_data["batter_id"],
                                score_data["men_on_base_situation"]["code"],
                            )
                            if batter_men_stats:
                                st.markdown(
                                    f"**{score_data['batter']} when {score_data['men_on_base_situation']['description']} (Season {batter_men_stats['season']})**"
                                )
                                # In the situation stats section, modify the DataFrame creation to:
                                df = pd.DataFrame(
                                    [
                                        {
                                            "AVG": str(
                                                round(float(batter_men_stats["avg"]), 4)
                                            )
                                            if batter_men_stats.get("avg")
                                            else "-",
                                            "OBP": str(
                                                round(float(batter_men_stats["obp"]), 4)
                                            )
                                            if batter_men_stats.get("obp")
                                            else "-",
                                            "SLG": str(
                                                round(float(batter_men_stats["slg"]), 4)
                                            )
                                            if batter_men_stats.get("slg")
                                            else "-",
                                            "OPS": str(
                                                round(float(batter_men_stats["ops"]), 4)
                                            )
                                            if batter_men_stats.get("ops")
                                            else "-",
                                        }
                                    ],
                                    index=[""],
                                )
                                st.table(df)
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
    st.markdown(f"### Analyzing {team_name} batters vs {pitcher_name}")

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
