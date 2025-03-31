# run_ui.py
import subprocess
import os

if __name__ == "__main__":
    print("🎮 啟動 Streamlit UI界面")
    # 設置環境變數，如果需要模擬數據
    env = os.environ.copy()
    # 檢測API服務器是否運行
    import requests

    try:
        requests.get("http://localhost:8000", timeout=1)
        print("✅ 檢測到API服務器運行中")
    except requests.exceptions.ConnectionError:
        print("⚠️ 未檢測到API服務器，將使用模擬數據")
        env["USE_MOCK_DATA"] = "1"

    # 運行Streamlit
    subprocess.run(["streamlit", "run", "ui/streamlit_app.py"], env=env)
