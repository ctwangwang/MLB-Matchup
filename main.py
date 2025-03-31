# main.py
import os
import argparse
from database.db_setup import initialize_database
from data_processing.player_data import (
    update_player_season_data,
    update_player_recent_data,
)


def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="MLB 對戰數據分析系統")

    parser.add_argument("--update-season", action="store_true", help="更新2024賽季數據")

    parser.add_argument(
        "--update-recent", action="store_true", help="更新最近5場比賽數據"
    )

    return parser.parse_args()


def main():
    """主程序入口"""
    args = parse_args()

    print("⚾ MLB 對戰數據分析系統數據維護工具")

    # 確保數據目錄存在
    os.makedirs("mlb_data", exist_ok=True)

    # 初始化數據庫
    initialize_database()

    # 處理數據更新
    if args.update_season:
        update_player_season_data()

    if args.update_recent:
        update_player_recent_data()

    if not args.update_season and not args.update_recent:
        print(
            "沒有指定任何操作。使用 --update-season 或 --update-recent 參數來更新數據。"
        )
        print("示例: python main.py --update-season --update-recent")


if __name__ == "__main__":
    main()
