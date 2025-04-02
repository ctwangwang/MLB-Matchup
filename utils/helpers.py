# utils/helpers.py
"""
輔助函數模組：提供各種通用功能
"""

import time
import json


def round_stat(value, decimals=3):
    """
    四捨五入統計數據

    Args:
        value (float/str): 要格式化的值
        decimals (int): 小數點位數

    Returns:
        float: 四捨五入後的數字
    """
    try:
        return round(float(value), decimals)
    except ValueError:
        return 0.0


def retry_api_call(func, max_retries=3, backoff_factor=1.5):
    """
    API請求重試裝飾器

    Args:
        func (callable): 要執行的API請求函數
        max_retries (int): 最大重試次數
        backoff_factor (float): 退避因子 (每次重試延遲時間倍數)

    Returns:
        any: 函數返回結果
    """
    retries = 0
    last_exception = None

    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            last_exception = e
            retries += 1

            if retries >= max_retries:
                break

            # 計算退避時間
            delay = backoff_factor**retries
            print(
                f"⚠️ API 請求失敗，將在 {delay:.2f} 秒後重試 ({retries}/{max_retries})..."
            )
            time.sleep(delay)

    # 重試都失敗後，拋出最後捕獲的異常
    print(f"❌ API 請求重試達到上限 ({max_retries}次)")
    if last_exception:
        raise last_exception


def save_to_json(data, filename):
    """
    將數據保存為JSON文件

    Args:
        data (dict/list): 要保存的數據
        filename (str): 文件名
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存數據至 {filename}")


def load_from_json(filename):
    """
    從JSON文件加載數據

    Args:
        filename (str): 文件名

    Returns:
        dict/list: 加載的數據
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ 無法加載 {filename}: {str(e)}")
        return None


def convert_stat_to_float(value):
    """Safely convert a stat value to float"""
    if value is None:
        return 0.0

    try:
        if isinstance(value, str):
            # Handle any potential commas in string numbers
            value = value.replace(",", "")

        return float(value)
    except (ValueError, TypeError):
        return 0.0


def convert_stat_to_int(value):
    """Safely convert a stat value to integer"""
    if value is None:
        return 0

    try:
        if isinstance(value, str):
            # Handle any potential commas in string numbers
            value = value.replace(",", "")

        return int(float(value))
    except (ValueError, TypeError):
        return 0
