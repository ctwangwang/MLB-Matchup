import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import numpy as np


def create_baseball_diamond(bases_occupied):
    """Create an enhanced baseball diamond visualization showing which bases are occupied."""

    # Ensure bases_occupied is a list
    if not isinstance(bases_occupied, list):
        bases_occupied = []

    fig = go.Figure()

    # Draw the infield grass (light green circle)
    theta = np.linspace(0, 2 * np.pi, 100)
    r = 1.8
    x_circle = r * np.cos(theta)
    y_circle = r * np.sin(theta)

    fig.add_trace(
        go.Scatter(
            x=x_circle,
            y=y_circle,
            fill="toself",
            fillcolor="rgba(65, 180, 75, 0.5)",
            line=dict(color="rgba(65, 180, 75, 0.5)"),
            showlegend=False,
        )
    )

    # Draw the baseball diamond with thicker lines
    fig.add_trace(
        go.Scatter(
            x=[0, 1, 0, -1, 0],
            y=[0, 1, 2, 1, 0],
            mode="lines",
            line=dict(color="white", width=3),
            showlegend=False,
        )
    )

    # Add the dirt infield (tan colored diamond)
    fig.add_trace(
        go.Scatter(
            x=[0, 1.1, 0, -1.1, 0],
            y=[-0.1, 1, 2.1, 1, -0.1],
            fill="toself",
            fillcolor="rgba(205, 170, 125, 0.7)",
            line=dict(color="rgba(205, 170, 125, 0.7)"),
            showlegend=False,
        )
    )

    # Redraw the base paths on top of the dirt
    fig.add_trace(
        go.Scatter(
            x=[0, 1, 0, -1, 0],
            y=[0, 1, 2, 1, 0],
            mode="lines",
            line=dict(color="white", width=3),
            showlegend=False,
        )
    )

    # Draw pitcher's mound
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[1],
            mode="markers",
            marker=dict(
                symbol="circle",
                size=12,
                color="rgba(205, 170, 125, 1)",
                line=dict(color="white", width=1),
            ),
            showlegend=False,
        )
    )

    # Draw home plate with better styling
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers",
            marker=dict(
                symbol="pentagon",
                size=18,
                color="white",
                line=dict(color="black", width=2),
            ),
            showlegend=False,
        )
    )

    # Draw bases with appropriate colors based on occupation
    base_positions = [(1, 1), (0, 2), (-1, 1)]  # (x, y) for 1st, 2nd, 3rd bases
    base_names = ["1st Base", "2nd Base", "3rd Base"]

    for i, (x, y) in enumerate(base_positions):
        base_num = i + 1
        # More vibrant red for occupied bases, and add shadow effect
        color = "rgba(255, 50, 50, 0.95)" if base_num in bases_occupied else "white"
        size = 18 if base_num in bases_occupied else 15
        # Add base shadow first
        fig.add_trace(
            go.Scatter(
                x=[x + 0.02],
                y=[y - 0.02],
                mode="markers",
                marker=dict(
                    symbol="square",
                    size=size,
                    color="rgba(0, 0, 0, 0.3)",
                ),
                showlegend=False,
            )
        )
        # Then the actual base
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers",
                marker=dict(
                    symbol="square",
                    size=size,
                    color=color,
                    line=dict(color="black", width=2),
                ),
                name=base_names[i],
                showlegend=False,
            )
        )

    # Update layout
    fig.update_layout(
        width=340,
        height=340,
        plot_bgcolor="rgba(30, 120, 30, 1)",  # Darker green for outfield
        xaxis=dict(
            range=[-2, 2],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True,
        ),
        yaxis=dict(
            range=[-0.5, 2.5],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Add outfield wall as an arc
    theta = np.linspace(-np.pi / 4, 5 * np.pi / 4, 100)
    r_wall = 2.8
    x_wall = r_wall * np.cos(theta)
    y_wall = r_wall * np.sin(theta) - 0.2

    fig.add_trace(
        go.Scatter(
            x=x_wall,
            y=y_wall,
            mode="lines",
            line=dict(color="rgba(60, 60, 60, 0.8)", width=5, dash="solid"),
            showlegend=False,
        )
    )

    return fig


def create_hot_cold_zones(
    batter_hot_cold_data, stat_type="onBasePlusSlugging", batter_handedness=None
):
    """
    Create a plotly visualization of a batter's hot/cold zones with a home plate below.

    Args:
        batter_hot_cold_data: The batterHotColdZoneStats data from the MLB API
        stat_type: Which stat to display ('onBasePlusSlugging', 'battingAverage', or 'exitVelocity')
        batter_handedness: 'L' for left-handed, 'R' for right-handed

    Returns:
        plotly Figure object
    """
    import plotly.graph_objects as go

    if not batter_hot_cold_data or "stats" not in batter_hot_cold_data:
        return None

    # Find the selected stat type in the data
    stat_data = None
    for split in batter_hot_cold_data["stats"][0]["splits"]:
        if split["stat"]["name"] == stat_type:
            stat_data = split["stat"]
            break

    if not stat_data:
        return None

    # Convert zone data to a dictionary for easy lookup
    zone_data = {z["zone"]: z for z in stat_data["zones"]}

    # Create a plot with custom dimensions
    fig = go.Figure()

    # Set background color
    fig.update_layout(
        plot_bgcolor="rgba(220, 220, 220, 1)",  # Light gray background
        paper_bgcolor="rgba(0, 0, 0, 0)",  # Transparent paper background
    )

    # Function to get a zone's color based on temperature
    def get_zone_color(zone_id):
        if zone_id in zone_data:
            temp = zone_data[zone_id].get("temp", "lukewarm")
            if temp == "hot":
                return "rgba(214, 41, 52, 0.6)"  # Red for hot
            elif temp == "cold":
                return "rgba(6, 90, 238, 0.6)"  # Blue for cold
            else:
                return "rgba(128, 128, 128, 0.6)"  # Grey for lukewarm
        return "rgba(128, 128, 128, 0.6)"  # Default to grey

    # Function to get a zone's value
    def get_zone_value(zone_id):
        if zone_id in zone_data:
            return zone_data[zone_id]["value"]
        return "-"

    # Define the grid - we'll use a 4-column grid to handle double-width zones
    grid_width = 4  # 4 columns to fit double-width cells
    grid_height = 5  # 5 rows

    # First, handle the inner 3x3 grid (zones 1-9)
    zone_mapping = [
        # Row 3 (bottom row of 3x3 grid): Zones 1, 2, 3
        {"row": 3, "col": 0, "zone": 1},
        {"row": 3, "col": 1, "zone": 2},
        {"row": 3, "col": 2, "zone": 3},
        # Row 2 (middle row of 3x3 grid): Zones 4, 5, 6
        {"row": 2, "col": 0, "zone": 4},
        {"row": 2, "col": 1, "zone": 5},
        {"row": 2, "col": 2, "zone": 6},
        # Row 1 (top row of 3x3 grid): Zones 7, 8, 9
        {"row": 1, "col": 0, "zone": 7},
        {"row": 1, "col": 1, "zone": 8},
        {"row": 1, "col": 2, "zone": 9},
    ]

    # Draw the inner 3x3 grid
    for zone in zone_mapping:
        row = zone["row"]
        col = zone["col"]
        zone_id = f"{zone['zone']:02d}"  # Format as "01", "02", etc.

        # Draw the zone
        fig.add_shape(
            type="rect",
            x0=col,
            y0=row + 0.5,
            x1=col + 1,
            y1=row + 1.5,
            line=dict(color="black", width=1),
            fillcolor=get_zone_color(zone_id),
            layer="below",
        )

        # Add zone number and value
        fig.add_annotation(
            x=col + 0.5,
            y=row + 1.2,  # Positioned in the upper part
            text=str(zone["zone"]),  # Display without leading zero
            showarrow=False,
            font=dict(size=14, color="black", family="Arial, sans-serif"),
        )

        fig.add_annotation(
            x=col + 0.5,
            y=row + 0.8,  # Positioned in the lower part
            text=get_zone_value(zone_id),
            showarrow=False,
            font=dict(size=12, color="black", family="Arial, sans-serif"),
        )

    # Now handle the outer zones (11, 12, 13, 14, 17, 18, 19, 20)
    outer_zones = [
        {"id": "13", "x0": -0.5, "y0": 1, "x1": 1.5, "y1": 1.5},  # Top left
        {"id": "14", "x0": 1.5, "y0": 1, "x1": 3.5, "y1": 1.5},  # Top right
        {
            "id": "11",
            "x0": -0.5,
            "y0": 4.5,
            "x1": 1.5,
            "y1": 5,
        },  # Bottom left, aligned with zone 13
        {"id": "12", "x0": 1.5, "y0": 4.5, "x1": 3.5, "y1": 5},  # Bottom right
        # Zone 17 is the upper half of the former zone 15
        {"id": "13", "x0": -0.5, "y0": 1.5, "x1": 0, "y1": 3},  # Upper left gap
        # Zone 18 is the lower half of the former zone 15
        {"id": "11", "x0": -0.5, "y0": 3, "x1": 0, "y1": 4.5},  # Lower left gap
        # Zone 19 is the upper half of the former zone 16
        {"id": "14", "x0": 3, "y0": 1.5, "x1": 3.5, "y1": 3},  # Upper right gap
        # Zone 20 is the lower half of the former zone 16
        {"id": "12", "x0": 3, "y0": 3, "x1": 3.5, "y1": 4.5},  # Lower right gap
    ]

    for zone in outer_zones:
        # Draw the zone
        fig.add_shape(
            type="rect",
            x0=zone["x0"],
            y0=zone["y0"],
            x1=zone["x1"],
            y1=zone["y1"],
            line=dict(color="black", width=1),
            fillcolor=get_zone_color(zone["id"]),
            layer="below",
        )

        # Add zone number and value
        center_x = (zone["x0"] + zone["x1"]) / 2
        center_y = (zone["y0"] + zone["y1"]) / 2

        fig.add_annotation(
            x=center_x,
            y=center_y + 0.15,  # Offset for number
            text=zone["id"],
            showarrow=False,
            font=dict(size=14, color="black", family="Arial, sans-serif"),
        )

        fig.add_annotation(
            x=center_x,
            y=center_y - 0.15,  # Offset for value
            text=get_zone_value(zone["id"]),
            showarrow=False,
            font=dict(size=12, color="black", family="Arial, sans-serif"),
        )

    # Stat type names for display
    stat_display_names = {
        "onBasePlusSlugging": "OPS",
        "battingAverage": "AVG",
        "exitVelocity": "Exit Velocity",
    }

    # Add home plate below the strike zone
    center_x = 1.5
    plate_width = 1.0
    plate_height = 1.0

    home_plate_points = [
        [center_x, 0],  # Top point
        [center_x + plate_width / 2, 0.4],  # Right corner
        [center_x + plate_width / 2, 0.8],  # Bottom right
        [center_x - plate_width / 2, 0.8],  # Bottom left
        [center_x - plate_width / 2, 0.4],  # Left corner
    ]

    fig.add_shape(
        type="path",
        path=f"M {home_plate_points[0][0]} {home_plate_points[0][1]} "
        f"L {home_plate_points[1][0]} {home_plate_points[1][1]} "
        f"L {home_plate_points[2][0]} {home_plate_points[2][1]} "
        f"L {home_plate_points[3][0]} {home_plate_points[3][1]} "
        f"L {home_plate_points[4][0]} {home_plate_points[4][1]} Z",
        fillcolor="#1a3a5a",
        line=dict(color="#1a3a5a"),
        layer="below",
    )

    # Add arrows to indicate batter handedness
    if batter_handedness:
        if batter_handedness.upper() == "R":
            # Add left arrow (for right-handed batter)
            fig.add_annotation(
                x=-1,
                y=3,
                xref="x",
                yref="y",
                text="➡️",
                showarrow=False,
                font=dict(size=20),
            )
        elif batter_handedness.upper() == "L":
            # Add right arrow (for left-handed batter)
            fig.add_annotation(
                x=4,
                y=3,
                xref="x",
                yref="y",
                text="⬅️",
                showarrow=False,
                font=dict(size=20),
            )

    # Update the axis range to account for the shifted zones and added home plate
    fig.update_layout(
        title=f"Batter Hot/Cold Zones - {stat_display_names.get(stat_type, stat_type)}",
        title_font=dict(size=16, family="Arial, sans-serif"),
        title_x=0.5,  # Center title
        width=500,
        height=650,  # Increased height to accommodate home plate
        xaxis=dict(
            range=[-0.7, 3.7],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True,
        ),
        yaxis=dict(
            range=[-0.2, 6.0],  # Extended y-range to include home plate
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1,
        ),
        margin=dict(l=20, r=20, t=50, b=40),  # Increased bottom margin
        showlegend=True,
        legend=dict(
            x=1.05,
            y=0.5,
            xanchor="left",
            orientation="v",
            bgcolor="rgba(40, 40, 40, 0.8)",
            bordercolor="rgba(255, 255, 255, 0.3)",
            borderwidth=1,
            font=dict(color="white"),
        ),
    )

    # Add a legend for the colors
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=15, color="rgba(214, 41, 52, 0.6)"),
            name="Hot",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                size=15,
                color="rgba(128, 128, 128, 0.6)",
                line=dict(color="black", width=1),
            ),
            name="Lukewarm",
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=15, color="rgba(6, 90, 238, 0.6)"),
            name="Cold",
            showlegend=True,
        )
    )

    # Replace the handedness legend items with these:
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=0),  # Invisible marker
            name="➡️ Right-Handed",  # Include emoji in name
            showlegend=True,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=0),  # Invisible marker
            name="⬅️ Left-Handed",  # Include emoji in name
            showlegend=True,
        )
    )
    # Add footnote about zone perspective - moved below the home plate
    fig.add_annotation(
        x=0.5,
        y=-0.12,  # Moved lower to account for home plate
        text="Zones are assigned from the catcher's perspective; zone 1 is 'high and away' to a left-handed batter.",
        showarrow=False,
        xref="paper",
        yref="paper",
        font=dict(size=10, family="Arial, sans-serif"),
        align="center",
    )

    return fig


def display_hitter_data(title, hitter_data):
    """
    Display hitter data in a table

    Args:
        title (str): Table title
        hitter_data (tuple/list): Hitter data
    """
    if hitter_data:
        if isinstance(hitter_data, tuple):
            hitter_data = [list(hitter_data)]
        elif isinstance(hitter_data, list) and isinstance(
            hitter_data[0], (str, float, int)
        ):
            hitter_data = [hitter_data]

        df = pd.DataFrame(
            hitter_data, columns=["Player", "AVG", "OBP", "SLG", "OPS"]
        ).round(3)

        st.subheader(title)
        st.table(df.set_index("Player"))  # Hide index
    else:
        st.write(f"⚠️ {title} - No data available")


def display_hitter_data(title, hitter_data):
    """
    Display hitter data in a table

    Args:
        title (str): Table title
        hitter_data (tuple/list): Hitter data
    """
    if hitter_data:
        if isinstance(hitter_data, tuple):
            hitter_data = [list(hitter_data)]
        elif isinstance(hitter_data, list) and isinstance(
            hitter_data[0], (str, float, int)
        ):
            hitter_data = [hitter_data]

        df = pd.DataFrame(
            hitter_data, columns=["Player", "AVG", "OBP", "SLG", "OPS"]
        ).round(3)

        st.subheader(title)
        st.table(df.set_index("Player"))  # Hide index
    else:
        st.write(f"⚠️ {title} - No data available")


def get_fip_minus_color(fip_minus):
    """
    Get color for FIP- value based on thresholds

    Args:
        fip_minus (float): FIP- value

    Returns:
        str: CSS color code
    """
    try:
        fip_minus = float(fip_minus)

        if fip_minus <= 80:
            return "red"
        elif 80 < fip_minus <= 90:
            return "#EE82EE"
        elif 90 < fip_minus <= 110:
            return "#4169e1"
        elif 110 < fip_minus <= 120:
            return "green"
        else:  # > 120
            return "#F4A460"
    except (ValueError, TypeError):
        return "black"  # Default color if not a valid number


def get_pitcher_war_color(war):
    """
    Get color for WAR value based on thresholds

    Args:
        war (float): WAR value

    Returns:
        str: CSS color code
    """
    try:
        war = float(war)

        if war >= 5:
            return "red"
        elif 3 <= war < 5:
            return "#EE82EE"
        elif 1 <= war < 3:
            return "#4169e1"
        elif 0 <= war < 1:
            return "green"
        else:  # < 0
            return "#F4A460"
    except (ValueError, TypeError):
        return "black"  # Default color if not a valid number


def get_wrc_plus_color(wrc_plus):
    """
    Get color for wRC+ value based on thresholds (using similar logic to FIP-)
    But since wRC+ is better when higher (opposite of FIP-), we'll invert the scale

    Args:
        wrc_plus (float): wRC+ value

    Returns:
        str: CSS color code
    """
    try:
        wrc_plus = float(wrc_plus)

        if wrc_plus >= 150:
            return "red"  # Excellent
        elif 130 <= wrc_plus < 150:
            return "#EE82EE"  # Great
        elif 110 <= wrc_plus < 130:
            return "#4169e1"  # Average
        elif 90 <= wrc_plus < 110:
            return "green"  # Below average
        else:  # < 90
            return "#F4A460"  # Poor
    except (ValueError, TypeError):
        return "black"  # Default color if not a valid number


def get_batter_war_color(war):
    """
    Get color for WAR value based on thresholds

    Args:
        war (float): WAR value

    Returns:
        str: CSS color code
    """
    try:
        war = float(war)

        if war >= 7:
            return "red"
        elif 4 <= war < 7:
            return "#EE82EE"
        elif 2 <= war < 4:
            return "#4169e1"
        elif 1 <= war < 2:
            return "green"
        else:  # < 1
            return "#F4A460"
    except (ValueError, TypeError):
        return "black"  # Default color if not a valid number
