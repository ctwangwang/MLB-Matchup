# utils/helpers.py
"""
Helper Functions Module: Provides various common utilities
"""

import time
import json


def round_stat(value, decimals=3):
    """
    Round statistical data

    Args:
        value (float/str): Value to format
        decimals (int): Number of decimal places

    Returns:
        float: Rounded number
    """
    try:
        return round(float(value), decimals)
    except ValueError:
        return 0.0


def retry_api_call(func, max_retries=3, backoff_factor=1.5):
    """
    API request retry decorator

    Args:
        func (callable): API request function to execute
        max_retries (int): Maximum number of retry attempts
        backoff_factor (float): Backoff factor (multiplier for delay time on each retry)

    Returns:
        any: Function return result
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

            # Calculate backoff time
            delay = backoff_factor**retries
            print(
                f"⚠️ API request failed, will retry in {delay:.2f} seconds ({retries}/{max_retries})..."
            )
            time.sleep(delay)

    # After all retries fail, raise the last captured exception
    print(f"❌ API request retry limit reached ({max_retries} times)")
    if last_exception:
        raise last_exception


def save_to_json(data, filename):
    """
    Save data to a JSON file

    Args:
        data (dict/list): Data to save
        filename (str): Filename
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Data saved to {filename}")


def load_from_json(filename):
    """
    Load data from a JSON file

    Args:
        filename (str): Filename

    Returns:
        dict/list: Loaded data
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Unable to load {filename}: {str(e)}")
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
