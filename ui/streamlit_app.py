# ui/streamlit_app.py
import os
import sys

# 設置項目根目錄路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import streamlit as st
import pandas as pd
import requests
import time
from config.team_config import MLB_TEAMS

# 檢查是否使用模擬數據
USE_MOCK_DATA = os.environ.get("USE_MOCK_DATA") == "1"

# API 基礎URL
API_BASE_URL = "http://localhost:8000"


# 模擬數據函數
def get_mock_team_pitchers():
    """返回模擬的球隊投手數據"""
    return {
        "pitchers": [
            {"pitcher_id": 123456, "full_name": "Clayton Kershaw"},
            {"pitcher_id": 234567, "full_name": "Walker Buehler"},
            {"pitcher_id": 345678, "full_name": "Julio Urías"},
        ]
    }


def get_mock_today_games():
    """返回模擬的今日比賽數據"""
    return {
        "games": [
            {
                "game_id": 1,
                "away_team": "New York Yankees",
                "away_team_id": 147,
                "home_team": "Boston Red Sox",
                "home_team_id": 111,
            },
            {
                "game_id": 2,
                "away_team": "Los Angeles Dodgers",
                "away_team_id": 119,
                "home_team": "San Francisco Giants",
                "home_team_id": 137,
            },
        ]
    }


def get_mock_game_pitchers():
    """返回模擬的比賽投手數據"""
    return {
        "away": [
            {"pitcher_id": 123456, "full_name": "Gerrit Cole"},
            {"pitcher_id": 234567, "full_name": "Luis Severino"},
        ],
        "home": [
            {"pitcher_id": 345678, "full_name": "Chris Sale"},
            {"pitcher_id": 456789, "full_name": "Nick Pivetta"},
        ],
    }


def get_mock_matchup_data():
    """返回模擬的對戰數據"""
    return {
        "team_name": "New York Yankees",
        "best_season_hitter": ("Aaron Judge", 0.310, 0.425, 0.600, 1.025),
        "best_recent_hitter": ("Juan Soto", 0.325, 0.480, 0.590, 1.070),
        "best_vs_pitcher_hitter": ("Giancarlo Stanton", 0.333, 0.400, 0.778, 1.178),
        "all_hitters_vs_pitcher": [
            ("Giancarlo Stanton", 0.333, 0.400, 0.778, 1.178),
            ("Aaron Judge", 0.300, 0.417, 0.700, 1.117),
            ("Anthony Rizzo", 0.278, 0.350, 0.500, 0.850),
        ],
    }


# 安全API請求函數
def safe_api_request(url, timeout=10, retries=2):
    """執行安全的API請求，處理連接問題"""
    global USE_MOCK_DATA  # 先聲明全局變量

    if USE_MOCK_DATA:
        # 使用模擬數據
        if "games/today" in url:
            return get_mock_today_games()
        elif "/game/" in url and "/pitchers" in url:
            return get_mock_game_pitchers()
        elif "/team/" in url and "/pitchers" in url:
            return get_mock_team_pitchers()
        elif "matchup" in url:
            return get_mock_matchup_data()
        return {}

    # 實際API請求
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            return response.json()
        except requests.exceptions.ConnectionError:
            if attempt < retries:
                # 重試前等待
                time.sleep(1)
                continue
            # 最後一次嘗試失敗，顯示錯誤
            st.error(f"⚠️ 無法連接到API伺服器 ({url})")
            st.info(
                "API服務器未運行。請在另一個終端中運行 'python run_api.py' 啟動API服務器。"
            )
            # 使用模擬數據
            USE_MOCK_DATA = True
            return safe_api_request(url)
        except Exception as e:
            st.error(f"⚠️ API請求錯誤: {str(e)}")
            return {}


def setup_page_config():
    """設置頁面配置和樣式"""
    st.set_page_config(page_title="MLB 對戰數據分析", page_icon="⚾", layout="wide")

    # 自定義CSS樣式
    st.markdown(
        """
        <style>
        h1 { font-size: 60px !important; }
        h2 { font-size: 45px !important; }
        .stTable { font-size: 22px !important; }
        label { font-size: 24px !important; font-weight: bold; } /* 放大 selectbox 標題字體 */
        div[data-baseweb="select"] > div { font-size: 20px !important; } /* 放大 selectbox 選項字體 */
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 在頁面頂部顯示模擬數據狀態
    if USE_MOCK_DATA:
        st.warning("⚠️ 使用模擬數據 - API服務器未連接")


def display_hitter_data(title, hitter_data):
    """
    顯示打者數據表格

    Args:
        title (str): 表格標題
        hitter_data (tuple/list): 打者數據
    """
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

        st.write(f"### {title}")
        st.table(df.set_index("打者"))  # 隱藏 index
    else:
        st.write(f"⚠️ {title} - 沒有可用的數據")


def today_games_tab():
    """今日比賽分析標籤頁"""
    st.header("📅 今日比賽")

    # 獲取當天比賽
    response_data = safe_api_request(f"{API_BASE_URL}/games/today")
    today_games = response_data.get("games", [])

    if not today_games:
        st.write("⚠️ 今日無比賽")
        return

    # 選擇比賽
    game_options = [f"{g['away_team']} @ {g['home_team']}" for g in today_games]
    selected_game = st.selectbox("選擇比賽", game_options)

    # 獲取選擇的比賽信息
    selected_index = game_options.index(selected_game)
    selected_game_info = today_games[selected_index]

    # 獲取比賽中的所有投手
    game_pitchers = safe_api_request(
        f"{API_BASE_URL}/game/{selected_game_info['game_id']}/pitchers"
    )

    # 建立兩欄分析區塊
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"⚔️ 客隊: {selected_game_info['away_team']}")

        # 客隊投手下拉選單
        away_pitcher_options = [p["full_name"] for p in game_pitchers.get("away", [])]
        away_pitcher_ids = {
            p["full_name"]: p["pitcher_id"] for p in game_pitchers.get("away", [])
        }

        if away_pitcher_options:
            selected_away_pitcher = st.selectbox(
                "選擇客隊投手", away_pitcher_options, key="away_pitcher_select"
            )
            selected_away_pitcher_id = away_pitcher_ids[selected_away_pitcher]
        else:
            st.write("⚠️ 無可用投手資料")
            selected_away_pitcher_id = None
            selected_away_pitcher = None

        # 分析按鈕 - 客隊投手對主隊打者
        if selected_away_pitcher_id and st.button(
            "分析主隊打者vs客隊投手", key="home_vs_away_analysis"
        ):
            # 分析主隊打者對客隊選擇的投手
            data = safe_api_request(
                f"{API_BASE_URL}/matchup?team_id={selected_game_info['home_team_id']}&pitcher_id={selected_away_pitcher_id}"
            )

            # 顯示數據
            if data.get("best_season_hitter"):
                display_hitter_data(
                    f"🏆 當季 OPS 最高打者 ({selected_game_info['home_team']})",
                    data.get("best_season_hitter"),
                )

            if data.get("best_recent_hitter"):
                display_hitter_data(
                    f"📈 最近 5 場 OPS 最高打者 ({selected_game_info['home_team']})",
                    data.get("best_recent_hitter"),
                )

            if data.get("best_vs_pitcher_hitter"):
                display_hitter_data(
                    f"🔥 對{selected_away_pitcher}的 OPS 最高打者 ({selected_game_info['home_team']})",
                    data.get("best_vs_pitcher_hitter"),
                )

            if data.get("all_hitters_vs_pitcher"):
                display_hitter_data(
                    f"📊 全隊對{selected_away_pitcher}的數據 ({selected_game_info['home_team']})",
                    data.get("all_hitters_vs_pitcher"),
                )

            if not data.get("best_vs_pitcher_hitter"):
                st.write(f"⚠️ 無對{selected_away_pitcher}的對戰數據")

    with col2:
        st.subheader(f"🏠 主隊: {selected_game_info['home_team']}")

        # 主隊投手下拉選單
        home_pitcher_options = [p["full_name"] for p in game_pitchers.get("home", [])]
        home_pitcher_ids = {
            p["full_name"]: p["pitcher_id"] for p in game_pitchers.get("home", [])
        }

        if home_pitcher_options:
            selected_home_pitcher = st.selectbox(
                "選擇主隊投手", home_pitcher_options, key="home_pitcher_select"
            )
            selected_home_pitcher_id = home_pitcher_ids[selected_home_pitcher]
        else:
            st.write("⚠️ 無可用投手資料")
            selected_home_pitcher_id = None
            selected_home_pitcher = None

        # 分析按鈕 - 主隊投手對客隊打者
        if selected_home_pitcher_id and st.button(
            "分析客隊打者vs主隊投手", key="away_vs_home_analysis"
        ):
            # 分析客隊打者對主隊選擇的投手
            data = safe_api_request(
                f"{API_BASE_URL}/matchup?team_id={selected_game_info['away_team_id']}&pitcher_id={selected_home_pitcher_id}"
            )

            # 顯示數據
            if data.get("best_season_hitter"):
                display_hitter_data(
                    f"🏆 當季 OPS 最高打者 ({selected_game_info['away_team']})",
                    data.get("best_season_hitter"),
                )

            if data.get("best_recent_hitter"):
                display_hitter_data(
                    f"📈 最近 5 場 OPS 最高打者 ({selected_game_info['away_team']})",
                    data.get("best_recent_hitter"),
                )

            if data.get("best_vs_pitcher_hitter"):
                display_hitter_data(
                    f"🔥 對{selected_home_pitcher}的 OPS 最高打者 ({selected_game_info['away_team']})",
                    data.get("best_vs_pitcher_hitter"),
                )

            if data.get("all_hitters_vs_pitcher"):
                display_hitter_data(
                    f"📊 全隊對{selected_home_pitcher}的數據 ({selected_game_info['away_team']})",
                    data.get("all_hitters_vs_pitcher"),
                )

            if not data.get("best_vs_pitcher_hitter"):
                st.write(f"⚠️ 無對{selected_home_pitcher}的對戰數據")


def custom_matchup_tab():
    """自訂對戰分析標籤頁"""
    st.header("🔍 自訂對戰分析")

    # 確保MLB_TEAMS不為空
    if not MLB_TEAMS:
        st.error("⚠️ 球隊數據未能成功載入。請檢查config/team_config.py")
        return

    # 選擇球隊
    team_name = st.selectbox("選擇你的球隊", list(MLB_TEAMS.keys()), key="custom_team")
    team_id = MLB_TEAMS[team_name]

    # 選擇對手球隊
    opponent_team_name = st.selectbox(
        "選擇對手球隊", list(MLB_TEAMS.keys()), key="custom_opponent"
    )
    opponent_team_id = MLB_TEAMS[opponent_team_name]

    # 取得對手投手清單
    response_data = safe_api_request(f"{API_BASE_URL}/team/{opponent_team_id}/pitchers")
    pitchers = response_data.get("pitchers", [])

    if not pitchers:
        st.write("⚠️ 該隊沒有可選投手")
        return

    # 提取投手名稱
    pitcher_names = [p["full_name"] for p in pitchers]

    # 建立名稱 -> ID 映射
    pitcher_ids = {p["full_name"]: p["pitcher_id"] for p in pitchers}

    # 選擇對手投手
    selected_pitcher_name = st.selectbox(
        "選擇對手投手", pitcher_names, key="custom_pitcher"
    )

    # 根據名稱查詢 ID
    selected_pitcher_id = pitcher_ids[selected_pitcher_name]

    # 查詢數據
    if st.button("分析", key="custom_analyze"):
        data = safe_api_request(
            f"{API_BASE_URL}/matchup?team_id={team_id}&pitcher_id={selected_pitcher_id}"
        )

        # 顯示數據
        if data.get("best_season_hitter"):
            display_hitter_data(
                f"🏆 當季 OPS 最高打者 ({data.get('team_name', team_name)})",
                data.get("best_season_hitter"),
            )

        if data.get("best_recent_hitter"):
            display_hitter_data(
                f"📈 最近 5 場 OPS 最高打者 ({data.get('team_name', team_name)})",
                data.get("best_recent_hitter"),
            )

        if data.get("best_vs_pitcher_hitter"):
            display_hitter_data(
                f"🔥 對{selected_pitcher_name}的 OPS 最高打者 ({data.get('team_name', team_name)})",
                data.get("best_vs_pitcher_hitter"),
            )

        if data.get("all_hitters_vs_pitcher"):
            display_hitter_data(
                f"📊 全隊對{selected_pitcher_name}的數據 ({data.get('team_name', team_name)})",
                data.get("all_hitters_vs_pitcher"),
            )

        if not data.get("best_vs_pitcher_hitter") and not data.get(
            "all_hitters_vs_pitcher"
        ):
            st.write(f"⚠️ 無對{selected_pitcher_name}的對戰數據")


def main():
    """Streamlit應用主函數"""
    # 設置頁面配置
    setup_page_config()

    # 顯示標題
    st.title("⚾ MLB 對戰數據分析")

    # 創建標籤頁
    tab1, tab2 = st.tabs(["📅 今日比賽", "🔍 自訂對戰分析"])

    # 填充標籤頁內容
    with tab1:
        today_games_tab()

    with tab2:
        custom_matchup_tab()


if __name__ == "__main__":
    main()
