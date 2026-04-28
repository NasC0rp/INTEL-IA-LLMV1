import time
from datetime import datetime

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_seconds(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m}m {s:.0f}s"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"