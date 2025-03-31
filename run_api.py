# run_api.py
import uvicorn

if __name__ == "__main__":
    print("⚡ 啟動 FastAPI 伺服器 (端口: 8000)")
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)
