import re
from datetime import datetime, timedelta


def is_iso_timestamp(value):
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return True
    except Exception:
        return False


def is_percent_like(value):
    s = str(value)
    return any(ch.isdigit() for ch in s)


def ensure_keys(obj, keys):
    missing = [k for k in keys if k not in obj]
    return missing


def is_number(value):
    try:
        float(value)
        return True
    except Exception:
        return False


def within_range(value, lo=None, hi=None):
    try:
        v = float(value)
    except Exception:
        return False
    if lo is not None and v < lo:
        return False
    if hi is not None and v > hi:
        return False
    return True


def recent_timestamp(value, max_age_seconds=86400):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return (datetime.now(dt.tzinfo) - dt) <= timedelta(seconds=max_age_seconds)
    except Exception:
        return False
