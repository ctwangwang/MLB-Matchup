# api/mlb_api.py
"""
MLB API 請求模組：處理所有與 MLB API 的交互
"""

import requests
from datetime import datetime


def get_today_games():
    """
    獲取當天的賽事

    Returns:
        list: 當天賽事列表
    """

    # 獲取當天日期 (YYYY-MM-DD 格式)
    today_date = datetime.today().strftime("%Y-%m-%d")

    # 使用正確的 API URL
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today_date}"
    response = requests.get(url).json()

    # 檢查是否有賽事
    if "dates" not in response or not response["dates"]:
        return []  # 無賽事時返回空列表

    games = response["dates"][0].get("games", [])

    return [
        {
            "game_id": game["gamePk"],
            "away_team": game["teams"]["away"]["team"]["name"],
            "away_team_id": game["teams"]["away"]["team"]["id"],
            "home_team": game["teams"]["home"]["team"]["name"],
            "home_team_id": game["teams"]["home"]["team"]["id"],
        }
        for game in games
    ]


def get_player_info(player_id):
    """
    獲取球員基本資訊

    Args:
        player_id (int): 球員ID

    Returns:
        dict: 包含球員ID和全名的字典，若找不到則返回None
    """
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}"
    response = requests.get(url).json()

    try:
        player = response["people"][0]
        return {"player_id": player["id"], "full_name": player["fullName"]}
    except (KeyError, IndexError):
        return None


def get_team_roster(team_id, season=None):
    """
    獲取球隊名單

    Args:
        team_id (int): 球隊ID
        season (int, optional): 賽季年份，若不提供則使用當前年份

    Returns:
        list: 球隊名單列表
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?season={season}"
    response = requests.get(url).json()
    players = response.get("roster", [])

    return [
        {
            "player_id": player["person"]["id"],
            "full_name": player["person"]["fullName"],
            "position": player["position"]["abbreviation"],
        }
        for player in players
    ]


def get_team_pitchers(team_id, season=None):
    """
    獲取球隊投手列表

    Args:
        team_id (int): 球隊ID
        season (int, optional): 賽季年份，若不提供則使用當前年份

    Returns:
        list: 投手列表
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?season={season}"
    response = requests.get(url).json()

    pitchers = []
    for player in response.get("roster", []):
        if player["position"]["abbreviation"] in ["P"]:  # 只篩選投手
            pitchers.append(
                {
                    "pitcher_id": player["person"]["id"],
                    "full_name": player["person"]["fullName"],
                }
            )

    return pitchers


def get_game_pitchers(game_id):
    """
    獲取比賽中的所有投手

    Args:
        game_id (int): 比賽ID

    Returns:
        dict: 包含主客隊投手的字典
    """
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    response = requests.get(url).json()

    pitchers = {"away": [], "home": []}

    try:
        # 獲取客隊投手資訊
        away_pitchers_ids = response["teams"]["away"].get("pitchers", [])
        home_pitchers_ids = response["teams"]["home"].get("pitchers", [])

        # 獲取所有投手詳細資訊
        for pitcher_id in away_pitchers_ids:
            pitcher_info = get_player_info(pitcher_id)
            if pitcher_info:
                pitchers["away"].append(
                    {"pitcher_id": pitcher_id, "full_name": pitcher_info["full_name"]}
                )

        for pitcher_id in home_pitchers_ids:
            pitcher_info = get_player_info(pitcher_id)
            if pitcher_info:
                pitchers["home"].append(
                    {"pitcher_id": pitcher_id, "full_name": pitcher_info["full_name"]}
                )

        return pitchers
    except (KeyError, IndexError) as e:
        print(f"Error fetching pitchers: {e}")
        return {"away": [], "home": []}


def get_game_details(game_id):
    """
    獲取比賽詳細資訊

    Args:
        game_id (int): 比賽ID

    Returns:
        dict: 包含比賽詳情的字典
    """
    url = f"https://statsapi.mlb.com/api/v1/game/{game_id}/boxscore"
    response = requests.get(url).json()

    # 取得先發投手ID與名稱
    try:
        away_pitcher_id = response["teams"]["away"]["pitchers"][0]
        home_pitcher_id = response["teams"]["home"]["pitchers"][0]

        # 獲取投手完整資訊
        away_pitcher_info = get_player_info(away_pitcher_id)
        home_pitcher_info = get_player_info(home_pitcher_id)

        return {
            "away_pitcher_id": away_pitcher_id,
            "away_pitcher_name": away_pitcher_info["full_name"]
            if away_pitcher_info
            else "未知",
            "home_pitcher_id": home_pitcher_id,
            "home_pitcher_name": home_pitcher_info["full_name"]
            if home_pitcher_info
            else "未知",
        }
    except (KeyError, IndexError):
        # 若無法取得先發投手，返回空值
        return {
            "away_pitcher_id": None,
            "away_pitcher_name": "未公布",
            "home_pitcher_id": None,
            "home_pitcher_name": "未公布",
        }


def get_batter_season_stats(player_id, season=None):
    """
    獲取球員賽季打擊數據

    Args:
        player_id (int): 球員ID
        season (int, optional): 賽季年份，若不提供則使用當前年份

    Returns:
        tuple: (打擊率, 上壘率, 長打率, OPS, BABIP, AB/HR, 全壘打, 打點)
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&season={season}&group=hitting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("avg", None),  # 打擊率 AVG
            data.get("obp", None),  # 上壘率 OBP
            data.get("slg", None),  # 長打率 SLG
            data.get("ops", None),  # OPS
            data.get("babip", None),  # 打球落地安打率 BABIP
            data.get("atBatsPerHomeRun", None),  # 每全壘打打數 AB/HR
            data.get("homeRuns", None),  # 全壘打數 HR
            data.get("rbi", None),  # 打點 RBI
        )

    return (None, None, None, None, None, None, None, None)  # 沒有數據時返回None


def get_pitcher_season_stats(pitcher_id, season=None):
    """
    獲取投手賽季數據

    Args:
        pitcher_id (int): 投手ID
        season (int, optional): 賽季年份，若不提供則使用當前年份

    Returns:
        tuple: (打者面對打擊率, OPS, ERA, WHIP, K/9, BB/9, H/9, HR/9, 勝場, 敗場, 中繼成功, 救援成功)
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=season&season={season}&group=pitching"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("avg", None),  # 打者面對打擊率 AVG
            data.get("ops", None),  # 打者面對OPS
            data.get("era", None),  # 防禦率 ERA
            data.get("whip", None),  # 每局被上壘率 WHIP
            data.get("strikeoutsPer9Inn", None),  # 每九局三振數 K/9
            data.get("walksPer9Inn", None),  # 每九局保送數 BB/9
            data.get("hitsPer9Inn", None),  # 每九局被安打數 H/9
            data.get("homeRunsPer9", None),  # 每九局被全壘打數 HR/9
            data.get("wins", None),  # 勝場 W
            data.get("losses", None),  # 敗場 L
            data.get("holds", None),  # 中繼成功 HLD
            data.get("saves", None),  # 救援成功 SV
        )

    return (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )  # 沒有數據時返回None


def get_player_recent_games(player_id, season=None, games_count=5):
    """
    獲取球員最近幾場比賽的打擊數據並計算平均值

    Args:
        player_id (int): 球員ID
        season (int, optional): 賽季年份，若不提供則使用當前年份
        games_count (int): 要計算的比賽場數

    Returns:
        tuple: (球員ID, 平均打擊率, 平均上壘率, 平均長打率, 平均OPS)
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&season={season}&gameType=S,R&group=hitting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats:
        hits, at_bats, walks, hbp, sac_fly, total_bases = (
            0,
            0,
            0,
            0,
            0,
            0,
        )  # 初始化計算變數

        for game in stats[0]["splits"][-games_count:]:  # 取最近N場比賽
            stat = game["stat"]
            hits += int(stat.get("hits", 0))  # 安打數
            at_bats += int(stat.get("atBats", 0))  # 打數
            walks += int(stat.get("baseOnBalls", 0))  # 四壞球
            hbp += int(stat.get("hitByPitch", 0))  # 觸身球
            sac_fly += int(stat.get("sacFlies", 0))  # 高飛犧牲打
            total_bases += int(stat.get("totalBases", 0))  # 總壘打數

        # 手動計算 AVG, OBP, SLG
        avg = hits / at_bats if at_bats else 0  # 打擊率 AVG
        obp = (
            (hits + walks + hbp) / (at_bats + walks + hbp + sac_fly)
            if (at_bats + walks + hbp + sac_fly)
            else 0
        )  # 上壘率 OBP
        slg = total_bases / at_bats if at_bats else 0  # 長打率 SLG
        ops = obp + slg  # 手動計算 OPS

        return player_id, avg, obp, slg, ops

    return player_id, 0, 0, 0, 0  # 無數據時返回0


def get_vs_pitcher_stats(player_id, pitcher_id):
    """
    獲取打者對投手的歷史數據

    Args:
        player_id (int): 打者ID
        pitcher_id (int): 投手ID

    Returns:
        dict: 包含統計數據的字典，若無數據則返回None
    """
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=vsPlayer&group=hitting&opposingPlayerId={pitcher_id}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"⚠️ API Request Failed: {response.status_code}, URL: {url}")
        return None

    data = response.json()

    # 確保stats鍵存在
    if "stats" not in data or not isinstance(data["stats"], list):
        print(f"⚠️ Invalid API response format: {data}")
        return None

    for stat_item in data["stats"]:
        # 只提取career數據
        if stat_item["type"]["displayName"] == "vsPlayerTotal":
            splits = stat_item.get("splits", [])
            if splits:
                stat = splits[0]["stat"]
                return {
                    "avg": round(float(stat.get("avg", "0.000")), 3),
                    "obp": round(float(stat.get("obp", "0.000")), 3),
                    "slg": round(float(stat.get("slg", "0.000")), 3),
                    "ops": round(float(stat.get("ops", "0.000")), 3),
                }

    print(f"⚠️ No career stats found for batter {player_id} vs pitcher {pitcher_id}")
    return None


# Add these functions to mlb_api.py
def get_batter_situation_stats(batter_id, situation_code, season=None):
    """
    Get batter stats in specific situations (vs LHP/RHP)

    Args:
        batter_id (int): Batter MLB ID
        situation_code (str): Situation code (vr/vl)
        season (int, optional): Season year, defaults to previous season if None

    Returns:
        dict: Contains AVG, OBP, SLG, OPS or None if not available
    """
    if season is None:
        # Default to current season rather than previous
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats?stats=statSplits&season={season}&group=hitting&sitCodes={situation_code}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "stats" in data and data["stats"]:
            splits = data["stats"][0].get("splits", [])
            if splits:
                stats = splits[0]["stat"]
                return {
                    "avg": round(float(stats.get("avg", 0)), 3),
                    "obp": round(float(stats.get("obp", 0)), 3),
                    "slg": round(float(stats.get("slg", 0)), 3),
                    "ops": round(float(stats.get("ops", 0)), 3),
                    "situation": situation_code,
                    "season": season,
                }
    except Exception as e:
        print(f"Error getting batter situation stats: {e}")

    return None


def get_pitcher_situation_stats(pitcher_id, situation_code, season=None):
    """
    Get pitcher stats in specific situations (vs LHB/RHB or men on base)

    Args:
        pitcher_id (int): Pitcher MLB ID
        situation_code (str): Situation code (vr/vl/risp)
        season (int, optional): Season year, defaults to current season if None

    Returns:
        dict: Contains AVG, OBP, SLG, OPS allowed or None if not available
    """
    if season is None:
        # Default to current season rather than previous
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=statSplits&season={season}&group=pitching&sitCodes={situation_code}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "stats" in data and data["stats"]:
            splits = data["stats"][0].get("splits", [])
            if splits:
                stats = splits[0]["stat"]
                return {
                    "avg": round(float(stats.get("avg", 0)), 3),
                    "obp": round(float(stats.get("obp", 0)), 3),
                    "slg": round(float(stats.get("slg", 0)), 3),
                    "ops": round(float(stats.get("ops", 0)), 3),
                    "situation": situation_code,
                    "season": season,
                }
    except Exception as e:
        print(f"Error getting pitcher situation stats: {e}")

    return None


def get_pitcher_sabermetrics(pitcher_id, season=None):
    """
    獲取投手進階數據 (Sabermetrics)

    Args:
        pitcher_id (int): 投手ID
        season (int, optional): 賽季年份，若不提供則使用當前年份

    Returns:
        tuple: (FIP, FIP-, WAR, ERA-, xFIP, ra9WAR, RAR, EXLI)
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=sabermetrics&season={season}&group=pitching"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("fip", None),  # 獨立防禦率 FIP
            data.get("fipMinus", None),  # FIP- (FIP相對於聯盟平均)
            data.get("war", None),  # 貢獻勝場數 WAR
            data.get("eraMinus", None),  # ERA- (ERA相對於聯盟平均)
            data.get("xfip", None),  # 預期獨立防禦率 xFIP
            data.get("ra9War", None),  # RA9-based WAR
            data.get("rar", None),  # Runs Above Replacement
            data.get("exli", None),  # Exited Leverage Index
        )

    return (None, None, None, None, None, None, None, None)  # 沒有數據時返回0


def get_batter_sabermetrics(batter_id, season=None):
    """
    獲取打者進階數據 (Sabermetrics)

    Args:
        batter_id (int): 打者ID
        season (int, optional): 賽季年份，若不提供則使用當前年份

    Returns:
        tuple: (wRC, wRC+, WAR, wOBA, wRAA, Batting, Spd, UBR)
    """
    # 如果沒有提供賽季，使用當前年份
    if season is None:
        season = datetime.now().year

    url = f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats?stats=sabermetrics&season={season}&group=batting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats and stats[0].get("splits"):
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("wRc", None),  # 加權創造得分 wRC
            data.get("wRcPlus", None),  # wRC+ (相對於聯盟平均)
            data.get("war", None),  # 貢獻勝場數 WAR
            data.get("woba", None),  # 準確代表攻擊價值 wOBA
            data.get("wRaa", None),  # 真實得分貢獻 wRAA
            data.get("batting", None),  # WAR 中的打擊貢獻
            data.get("spd", None),  # 評估打者速度 Spd
            data.get("ubr", None),  # 非盜壘跑壘表現 UBR
        )

    return (None, None, None, None, None, None, None, None)  # 沒有數據時返回None
