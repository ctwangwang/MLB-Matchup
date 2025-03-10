import requests
import sqlite3
import time
import os
import pandas as pd
from fastapi import FastAPI
import streamlit as st

# === 🏠 設定資料夾 & SQLite 資料庫 ===
DATA_DIR = "mlb_data"
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "mlb_2024.db")

# === ⚾ FastAPI 應用 ===
app = FastAPI()

# 30 支 MLB 球隊（球隊名稱: 球隊 ID）
MLB_TEAMS = {
    "New York Yankees": 147,
    "Los Angeles Dodgers": 119,
    "Boston Red Sox": 111,
    "Chicago Cubs": 112,
    "San Francisco Giants": 137,
    "St. Louis Cardinals": 138,
    "Houston Astros": 117,
    "Atlanta Braves": 144,
    "Toronto Blue Jays": 141,
    "Philadelphia Phillies": 143,
    "New York Mets": 121,
    "Texas Rangers": 140,
    "San Diego Padres": 135,
    "Washington Nationals": 120,
    "Tampa Bay Rays": 139,
    "Cleveland Guardians": 114,
    "Milwaukee Brewers": 158,
    "Chicago White Sox": 145,
    "Cincinnati Reds": 113,
    "Pittsburgh Pirates": 134,
    "Arizona Diamondbacks": 109,
    "Seattle Mariners": 136,
    "Minnesota Twins": 142,
    "Baltimore Orioles": 110,
    "Detroit Tigers": 116,
    "Colorado Rockies": 115,
    "Oakland Athletics": 133,
    "Kansas City Royals": 118,
    "Miami Marlins": 146,
    "Los Angeles Angels": 108,
}


# === 📌 創建 SQLite 連接 & 表格 ===
def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 更新 player_season_stats，添加 AVG（打擊率）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_season_stats (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT,
            team_id INTEGER,
            team_name TEXT,
            avg REAL,
            obp REAL,
            slg REAL,
            ops REAL
        )
    """)

    # 更新 player_recent_stats，添加 AVG, OBP, SLG
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_recent_stats (
            player_id INTEGER PRIMARY KEY,
            full_name TEXT,
            team_id INTEGER,
            avg REAL,
            obp REAL,
            slg REAL,
            avg_ops REAL
        )
    """)

    conn.commit()
    conn.close()


create_tables()


# === 📥 下載數據並存入 SQLite ===
def get_team_roster(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?season=2025"
    response = requests.get(url).json()
    players = response.get("roster", [])

    roster = []
    for player in players:
        roster.append(
            {
                "player_id": player["person"]["id"],
                "full_name": player["person"]["fullName"],
                "position": player["position"]["abbreviation"],
            }
        )

    return roster  # 回傳2025年的球員名單


def get_player_stats(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&season=2024&group=hitting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats:
        data = stats[0]["splits"][0]["stat"]
        return (
            data.get("avg", 0),  # 打擊率 AVG
            data.get("obp", 0),  # 上壘率 OBP
            data.get("slg", 0),  # 長打率 SLG
            data.get("ops", 0),  # OPS
        )

    return (0, 0, 0, 0)  # 沒有數據時，回傳 0


def get_recent_games(player_id):
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=gameLog&season=2024&group=hitting"
    response = requests.get(url).json()
    stats = response.get("stats", [])

    if stats:
        ops_list = []
        avg_list = []
        obp_list = []
        slg_list = []

        for game in stats[0]["splits"][-5:]:  # 取最近 5 場
            stat = game["stat"]
            ops_list.append(float(stat.get("ops", 0)))
            avg_list.append(float(stat.get("avg", 0)))
            obp_list.append(float(stat.get("obp", 0)))
            slg_list.append(float(stat.get("slg", 0)))

        avg_ops = sum(ops_list) / len(ops_list) if ops_list else 0
        avg_avg = sum(avg_list) / len(avg_list) if avg_list else 0
        avg_obp = sum(obp_list) / len(obp_list) if obp_list else 0
        avg_slg = sum(slg_list) / len(slg_list) if slg_list else 0

        return (player_id, avg_avg, avg_obp, avg_slg, avg_ops)

    return (player_id, 0, 0, 0, 0)  # 沒有數據時，回傳 0


def update_data():
    teams = requests.get("https://statsapi.mlb.com/api/v1/teams?sportId=1").json()[
        "teams"
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # **清除舊數據，但不刪除表**
    cursor.execute("DELETE FROM player_season_stats")
    cursor.execute("DELETE FROM player_recent_stats")
    conn.commit()

    for team in teams:
        team_id = team["id"]
        team_name = team["name"]
        print(f"📥 更新 2025 年球隊名單: {team_name}")

        # **確保 roster 來自 2025 年**
        players = get_team_roster(team_id)  # 這邊是 2025 年的球員

        for player in players:
            player_id = player["player_id"]
            full_name = player["full_name"]
            print(f"🔍 查詢 {full_name} ({player_id}) 的 2024 年數據")

            # **查詢 2024 年的數據**
            season_stats = get_player_stats(player_id)
            recent_stats = get_recent_games(player_id)

            # **存入 SQLite**
            cursor.execute(
                "INSERT OR REPLACE INTO player_season_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (player_id, full_name, team_id, team_name, *season_stats),
            )

            cursor.execute(
                "INSERT OR REPLACE INTO player_recent_stats VALUES (?, ?, ?, ?, ?, ?, ?)",
                (player_id, full_name, team_id, *recent_stats[1:]),
            )

            time.sleep(1)  # 避免 API 過載

    conn.commit()
    conn.close()
    print("✅ 2025 年陣容的 2024 年數據更新完成！")


# === 🏆 API：查詢最佳打者 ===
def query_db(query):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    return data


def get_team_pitchers(team_id):
    url = f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster?season=2025"
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

    return pitchers  # 回傳對方投手清單


# 四捨五入函數
def round_stat(value):
    try:
        return round(float(value), 3)
    except ValueError:
        return 0.000


def get_vs_pitcher_stats(player_id, pitcher_id):
    """
    Fetch the career matchup stats (vsPlayerTotal) for a given batter against a pitcher.
    """
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=vsPlayer&group=hitting&opposingPlayerId={pitcher_id}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"⚠️ API Request Failed: {response.status_code}, URL: {url}")
        return None

    data = response.json()

    # Ensure the stats key exists
    if "stats" not in data or not isinstance(data["stats"], list):
        print(f"⚠️ Invalid API response format: {data}")
        return None

    for stat_item in data["stats"]:
        # Only extract `vsPlayerTotal` for career matchup stats
        if stat_item["type"]["displayName"] == "vsPlayerTotal":
            splits = stat_item.get("splits", [])
            if splits:
                stat = splits[0]["stat"]
                return {
                    "avg": round_stat(stat.get("avg", "0.000")),
                    "obp": round_stat(stat.get("obp", "0.000")),
                    "slg": round_stat(stat.get("slg", "0.000")),
                    "ops": round_stat(stat.get("ops", "0.000")),
                }

    print(
        f"⚠️ No career stats found (vsPlayerTotal) for batter {player_id} vs pitcher {pitcher_id}"
    )
    return None


# 顯示結果的表格 (四捨五入到小數點後 3 位，標題加上球隊名稱)
def display_hitter_data(team_name, hitter_data):
    if hitter_data:
        if isinstance(hitter_data, tuple):
            hitter_data = [list(hitter_data)]
        elif isinstance(hitter_data, list) and isinstance(
            hitter_data[0], (str, float, int)
        ):
            hitter_data = [hitter_data]

        df = pd.DataFrame(
            hitter_data, columns=["打者", "AVG", "OBP", "SLG", "OPS"]
        ).round(3)

        # **✅ 標題加上球隊名稱**
        st.write(f"### ⚾ {team_name}")
        st.table(df.set_index("打者"))  # 隱藏 index
    else:
        st.write(f"⚠️ {team_name} 沒有可用的數據")


@app.get("/matchup")
def get_matchup(team_id: int, pitcher_id: int):
    try:
        # 獲取球隊名稱
        team_name = next(
            (name for name, id in MLB_TEAMS.items() if id == team_id), "Unknown Team"
        )

        # 查詢當季 OPS 最高的打者
        best_season = query_db(
            f"SELECT full_name, avg, obp, slg, ops FROM player_season_stats WHERE team_id={team_id} ORDER BY ops DESC LIMIT 1"
        )
        best_season = best_season[0] if best_season else None

        # 查詢最近 5 場 OPS 最高的打者
        best_recent = query_db(
            f"SELECT full_name, avg, obp, slg, avg_ops FROM player_recent_stats WHERE team_id={team_id} ORDER BY avg_ops DESC LIMIT 1"
        )
        best_recent = best_recent[0] if best_recent else None

        # 查詢該隊所有打者 ID
        best_vs_pitcher = None
        hitters = query_db(
            f"SELECT player_id, full_name FROM player_season_stats WHERE team_id={team_id}"
        )

        hitter_stats_list = []  # 保存所有對戰數據

        # 遍歷球員 vs 投手對戰數據
        for player_id, player_name in hitters:
            vs_stats = get_vs_pitcher_stats(player_id, pitcher_id)

            if vs_stats:
                avg, obp, slg, ops = (
                    vs_stats["avg"],
                    vs_stats["obp"],
                    vs_stats["slg"],
                    vs_stats["ops"],
                )
                hitter_stats_list.append((player_name, avg, obp, slg, ops))

                # 找到對該投手 OPS 最高的打者
                if best_vs_pitcher is None or ops > best_vs_pitcher[4]:
                    best_vs_pitcher = (player_name, avg, obp, slg, ops)

        # **按照 OPS 由高到低排序**
        hitter_stats_list = sorted(hitter_stats_list, key=lambda x: x[4], reverse=True)

        return {
            "team_name": team_name,  # ✅ **傳遞球隊名稱**
            "best_season_hitter": best_season if best_season else None,
            "best_recent_hitter": best_recent if best_recent else None,
            "best_vs_pitcher_hitter": best_vs_pitcher if best_vs_pitcher else None,
            "all_hitters_vs_pitcher": hitter_stats_list if hitter_stats_list else [],
        }

    except Exception as e:
        print(f"⚠️ 發生錯誤: {e}")
        return {"error": str(e)}


# === 🎮 Streamlit UI ===
def start_streamlit():
    st.title("⚾ MLB 對戰數據分析")

    # 選擇球隊
    team_name = st.selectbox("選擇你的球隊", list(MLB_TEAMS.keys()))
    team_id = MLB_TEAMS[team_name]

    # 選擇對手球隊
    opponent_team_name = st.selectbox("選擇對手球隊", list(MLB_TEAMS.keys()))
    opponent_team_id = MLB_TEAMS[opponent_team_name]

    # 取得對手投手清單
    pitchers = get_team_pitchers(opponent_team_id)
    if not pitchers:
        st.write("⚠️ 該隊沒有可選投手")
        return

    # 提取投手名稱
    pitcher_names = [p["full_name"] for p in pitchers]

    # 建立名稱 -> ID 映射
    pitcher_ids = {p["full_name"]: p["pitcher_id"] for p in pitchers}

    # 選擇對手投手
    selected_pitche_name = st.selectbox("選擇對手投手", pitcher_names)

    # 根據名稱查詢 ID
    selected_pitcher_id = pitcher_ids[selected_pitche_name]

    # 查詢數據
    # 當按下「分析」按鈕時
    if st.button("分析"):
        url = f"http://localhost:8000/matchup?team_id={team_id}&pitcher_id={selected_pitcher_id}"
        data = requests.get(url).json()

        # **顯示最佳打者數據**
        if data.get("best_season_hitter"):
            display_hitter_data(
                f"{data.get('team_name')} 2024 當季 OPS 最高打者",
                data.get("best_season_hitter"),
            )
        if data.get("best_recent_hitter"):
            display_hitter_data(
                f"{data.get('team_name')} 最近 5 場 OPS 最高打者",
                data.get("best_recent_hitter"),
            )
        if data.get("best_vs_pitcher_hitter"):
            display_hitter_data(
                f"{data.get('team_name')} 對該投手 OPS 最高打者",
                data.get("best_vs_pitcher_hitter"),
            )

        # **顯示所有對戰投手的球員數據**
        if data.get("all_hitters_vs_pitcher"):
            display_hitter_data(
                f"{data.get('team_name')} 打者對該投手的數據",
                data.get("all_hitters_vs_pitcher"),
            )


# === 🚀 運行 ===
if __name__ == "__main__":
    print("⚾ 更新數據中...")
    # update_data()
    print("⚡ 啟動 FastAPI：`uvicorn mlb_matchup:app --reload`")
    print("🎮 啟動 Streamlit：`streamlit run mlb_matchup.py`")
    print("⚡ 啟動 Streamlit UI...")
    start_streamlit()  # 🚀 這一行必須要有！
