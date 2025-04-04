# api/deepseek_analyzer.py
"""
DeepSeek API integration module: Use DeepSeek AI to analyze baseball matchups
"""

import os
import json
import requests
from typing import Dict, Any, Optional, Tuple

try:
    from config.api_keys import DEEPSEEK_API_KEY
except ImportError:
    # Fallback to environment variable if config file not found
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        print("⚠️ DeepSeek API key not found in config file or environment variables")

# You'll need to set this environment variable or configure it another way
# Only use environment variable if config import failed
if not DEEPSEEK_API_KEY:
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    print("⚠️ DeepSeek API key not found in config file or environment variables")

# DeepSeek API endpoint
DEEPSEEK_API_URL = (
    "https://api.deepseek.com/v1/chat/completions"  # Replace with actual endpoint
)


def get_deepseek_matchup_analysis(
    pitcher_data: Dict[str, Any],
    batter_data: Dict[str, Any],
    pitcher_name: str,
    batter_name: str,
) -> Optional[str]:
    """
    Use DeepSeek API to analyze matchup between pitcher and batter

    Args:
        pitcher_data: Dictionary containing pitcher's sabermetric data
        batter_data: Dictionary containing batter's sabermetric data
        pitcher_name: Name of the pitcher
        batter_name: Name of the batter

    Returns:
        str: DeepSeek's analysis of the matchup or None if request fails

    Original prompt:
    Provide a concise analysis (3-5 sentences) of how this matchup might play out based on these metrics.
    Consider strengths, weaknesses, and relevant statistical patterns.
    Focus on actionable insights that could impact the at-bat outcome.
    """
    if not DEEPSEEK_API_KEY:
        print(
            "⚠️ DeepSeek API key not configured. Set the DEEPSEEK_API_KEY environment variable."
        )
        return None

    # Format data for the prompt
    formatted_pitcher_data = format_pitcher_stats(pitcher_data, pitcher_name)
    formatted_batter_data = format_batter_stats(batter_data, batter_name)

    # Construct prompt for DeepSeek
    prompt = f"""
Based on the sabermetric data of the current pitcher and batter, please generate matchup insights.

PITCHER: {pitcher_name}
{formatted_pitcher_data}

BATTER: {batter_name}
{formatted_batter_data}

calculate win probability projections for this matchup accounting for all relevant factors and display in front. 
Present the final assessment with a clear numerical win probability percentage and key factors most likely to determine the outcome within 7 lines.
"""

    # Prepare request payload
    payload = {
        "model": "deepseek-chat",  # Update with appropriate model name
        "messages": [
            {
                "role": "system",
                "content": "You are a baseball analytics expert focusing on sabermetrics.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    try:
        # Make API request to DeepSeek
        response = requests.post(
            DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30
        )

        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            # Extract analysis from response
            analysis = (
                data.get("choices", [{}])[0].get("message", {}).get("content", "")
            )
            return analysis
        else:
            print(
                f"⚠️ DeepSeek API request failed: {response.status_code}, {response.text}"
            )
            return None

    except Exception as e:
        print(f"❌ Error making DeepSeek API request: {e}")
        return None


def format_pitcher_stats(pitcher_data: Dict[str, Any], pitcher_name: str) -> str:
    """Format pitcher stats for DeepSeek prompt"""
    # Extract relevant metrics
    try:
        era = pitcher_data.get("era", "-")
        whip = pitcher_data.get("whip", "-")
        fip = pitcher_data.get("fip", "-")
        fip_minus = pitcher_data.get("fip_minus", "-")
        war = pitcher_data.get("war", "-")
        k_per_9 = pitcher_data.get("k_per_9", "-")
        bb_per_9 = pitcher_data.get("bb_per_9", "-")
        h_per_9 = pitcher_data.get("h_per_9", "-")
        hr_per_9 = pitcher_data.get("hr_per_9", "-")
        xfip = pitcher_data.get("xfip", "-")
        ra9war = pitcher_data.get("ra9War", "-")
        rar = pitcher_data.get("rar", "-")
        exli = pitcher_data.get("exli", "-")
        era_minus = pitcher_data.get("era_minus", "-")

        # Format the data
        formatted_data = f"""
Pitcher Metrics:
- ERA: {era}
- WHIP: {whip}
- K/9: {k_per_9}
- BB/9: {bb_per_9}
- H/9: {h_per_9}
- HR/9: {hr_per_9}
- FIP: {fip}
- xFIP: {xfip}
- FIP-: {fip_minus}
- ERA-: {era_minus}
- WAR: {war}
- RA9WAR: {ra9war}
- RAR: {rar}
- EXLI: {exli}
"""
        return formatted_data

    except Exception as e:
        print(f"⚠️ Error formatting pitcher stats: {e}")
        return "Pitcher metrics unavailable"


def format_batter_stats(batter_data: Dict[str, Any], batter_name: str) -> str:
    """Format batter stats for DeepSeek prompt"""
    # Extract relevant metrics
    try:
        # Basic stats
        avg = batter_data.get("avg", "-")
        obp = batter_data.get("obp", "-")
        slg = batter_data.get("slg", "-")
        ops = batter_data.get("ops", "-")
        babip = batter_data.get("babip", "-")
        ab_per_hr = batter_data.get("ab_per_hr", "-")
        wrc_plus = batter_data.get("wrc_plus", "-")
        war = batter_data.get("war", "-")
        woba = batter_data.get("woba", "-")
        wraa = batter_data.get("wraa", "-")
        batting = batter_data.get("batting", "-")
        spd = batter_data.get("spd", "-")
        ubr = batter_data.get("ubr", "-")

        # Head-to-head stats against this pitcher
        vs_pitcher_avg = batter_data.get("vs_pitcher_avg", "-")
        vs_pitcher_obp = batter_data.get("vs_pitcher_obp", "-")
        vs_pitcher_slg = batter_data.get("vs_pitcher_slg", "-")
        vs_pitcher_ops = batter_data.get("vs_pitcher_ops", "-")

        # Format the data
        formatted_data = f"""
Batter Metrics:
- AVG: {avg}
- OBP: {obp}
- SLG: {slg}
- OPS: {ops}
- BABIP: {babip}
- AB/HR: {ab_per_hr}
- wOBA: {woba}
- wRC+: {wrc_plus}
- wRAA: {wraa}
- WAR: {war}
- Batting: {batting}
- Speed: {spd}
- UBR: {ubr}

Head-to-Head History:
- vs This Pitcher: {vs_pitcher_avg}/{vs_pitcher_obp}/{vs_pitcher_slg}/{vs_pitcher_ops} (AVG/OBP/SLG/OPS)
"""
        return formatted_data

    except Exception as e:
        print(f"⚠️ Error formatting batter stats: {e}")
        return "Batter metrics unavailable"


def get_matchup_insights(
    pitcher_id: int,
    batter_id: int,
    pitcher_name: str,
    batter_name: str,
    season: Optional[int] = None,
) -> str:
    """
    Get DeepSeek analysis of pitcher vs batter matchup with comprehensive data

    Args:
        pitcher_id: MLB ID of the pitcher
        batter_id: MLB ID of the batter
        pitcher_name: Name of the pitcher
        batter_name: Name of the batter
        season: Optional season year (defaults to previous year)

    Returns:
        str: Analysis of the matchup
    """
    from datetime import datetime
    from api.mlb_api import (
        get_pitcher_season_stats,
        get_pitcher_sabermetrics,
        get_batter_season_stats,
        get_batter_sabermetrics,
        get_vs_pitcher_stats,
        get_batter_situation_stats,  # Add this line
        get_pitcher_situation_stats,  # Add this line
    )

    # Use previous season if not specified
    if season is None:
        season = datetime.now().year - 1

    # Step 1: Gather pitcher data
    pitcher_data = {}

    # Get basic pitcher stats
    # Try to get all 8 values first
    try:
        (
            avg_against,
            ops_against,
            era,
            whip,
            k_per_9,
            bb_per_9,
            h_per_9,
            hr_per_9,
            wins,
            losses,
            holds,
            saves,
        ) = get_pitcher_season_stats(pitcher_id, season)
        pitcher_data.update(
            {
                "avg_against": avg_against if avg_against is not None else "-",
                "ops_against": ops_against if ops_against is not None else "-",
                "era": era if era is not None else "-",
                "whip": whip if whip is not None else "-",
                "k_per_9": k_per_9 if k_per_9 is not None else "-",
                "bb_per_9": bb_per_9 if bb_per_9 is not None else "-",
                "h_per_9": h_per_9 if h_per_9 is not None else "-",
                "hr_per_9": hr_per_9 if hr_per_9 is not None else "-",
            }
        )
    except Exception as e:
        print(f"⚠️ Error fetching pitcher season stats: {e}")
        pitcher_data.update(
            {
                "avg_against": avg_against if avg_against is not None else "-",
                "ops_against": ops_against if ops_against is not None else "-",
                "era": era if era is not None else "-",
                "whip": whip if whip is not None else "-",
                "k_per_9": "-",
                "bb_per_9": "-",
                "h_per_9": "-",
                "hr_per_9": "-",
            }
        )

    # Get advanced pitcher metrics
    try:
        # Get all 8 values
        fip, fip_minus, war, era_minus, xfip, ra9war, rar, exli = (
            get_pitcher_sabermetrics(pitcher_id, season)
        )
        pitcher_data.update(
            {
                "fip": fip if fip is not None else "-",
                "fip_minus": fip_minus if fip_minus is not None else "-",
                "war": war if war is not None else "-",
                "era_minus": era_minus if era_minus is not None else "-",
                "xfip": xfip if xfip is not None else "-",
                "ra9War": ra9war if ra9war is not None else "-",
                "rar": rar if rar is not None else "-",
                "exli": exli if exli is not None else "-",
            }
        )
    except Exception as e:
        print(f"⚠️ Error fetching pitcher sabermetrics: {e}")
        # Set default values
        pitcher_data.update(
            {
                "fip": "-",
                "fip_minus": "-",
                "war": "-",
                "era_minus": "-",
                "xfip": "-",
                "ra9War": "-",
                "rar": "-",
                "exli": "-",
            }
        )

    # Step 2: Gather batter data
    batter_data = {}

    # Get basic batter stats
    try:
        # Get all 8 values
        avg, obp, slg, ops, babip, ab_per_hr, hr, rbi = get_batter_season_stats(
            batter_id, season
        )
        batter_data.update(
            {
                "avg": avg if avg is not None else "-",
                "obp": obp if obp is not None else "-",
                "slg": slg if slg is not None else "-",
                "ops": ops if ops is not None else "-",
                "babip": babip if babip is not None else "-",
                "ab_per_hr": ab_per_hr if ab_per_hr is not None else "-",
                "hr": hr if hr is not None else "-",
                "rbi": rbi if rbi is not None else "-",
            }
        )
    except Exception as e:
        print(f"⚠️ Error fetching batter season stats: {e}")
        # Set default values for all 8 fields
        batter_data.update(
            {
                "avg": "-",
                "obp": "-",
                "slg": "-",
                "ops": "-",
                "babip": "-",
                "ab_per_hr": "-",
                "hr": "-",
                "rbi": "-",
            }
        )

    # Get advanced batter metrics
    try:
        # Get all 8 values
        wrc, wrc_plus, war, woba, wraa, batting, spd, ubr = get_batter_sabermetrics(
            batter_id, season
        )
        batter_data.update(
            {
                "wrc": wrc if wrc is not None else "-",
                "wrc_plus": wrc_plus if wrc_plus is not None else "-",
                "war": war if war is not None else "-",
                "woba": woba if woba is not None else "-",
                "wraa": wraa if wraa is not None else "-",
                "batting": batting if batting is not None else "-",
                "spd": spd if spd is not None else "-",
                "ubr": ubr if ubr is not None else "-",
            }
        )
    except Exception as e:
        print(f"⚠️ Error fetching batter sabermetrics: {e}")
        # Set default values
        batter_data.update(
            {
                "wrc": "-",
                "wrc_plus": "-",
                "war": "-",
                "woba": "-",
                "wraa": "-",
                "batting": "-",
                "spd": "-",
                "ubr": "-",
            }
        )

    # Step 3: Get head-to-head data
    vs_stats = get_vs_pitcher_stats(batter_id, pitcher_id)
    if vs_stats:
        batter_data.update(
            {
                "vs_pitcher_avg": vs_stats.get("avg", "-"),
                "vs_pitcher_obp": vs_stats.get("obp", "-"),
                "vs_pitcher_slg": vs_stats.get("slg", "-"),
                "vs_pitcher_ops": vs_stats.get("ops", "-"),
            }
        )

    # Step 4: Get DeepSeek analysis
    analysis = get_deepseek_matchup_analysis(
        pitcher_data, batter_data, pitcher_name, batter_name
    )

    # Return a default message if analysis fails
    if not analysis:
        return (
            f"Matchup analysis for {pitcher_name} vs {batter_name} could not be generated. "
            "Please check if DeepSeek API is properly configured."
        )

    return analysis
