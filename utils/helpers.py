# utils/helpers.py
from datetime import datetime

def now_iso():
    return datetime.utcnow().isoformat()

def pretty(dt):
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")
