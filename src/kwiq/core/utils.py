import re
from datetime import datetime
from re import Pattern
from typing import AnyStr


def word_pattern(word: str) -> Pattern[AnyStr]:
    return re.compile(r'\b[\w-]*' + re.escape(word) + r'[\w-]*\b', re.IGNORECASE)


def current_date():
    return datetime.now().strftime('%Y_%m_%d')


def set_nested_value(data, key_path, value):
    keys = key_path.split('.')
    current_level = data

    # Traverse the nested dictionary to create any missing sub-levels
    for key in keys[:-1]:
        if key not in current_level:
            current_level[key] = {}
        current_level = current_level[key]

    # Set the value at the final level
    current_level[keys[-1]] = value
