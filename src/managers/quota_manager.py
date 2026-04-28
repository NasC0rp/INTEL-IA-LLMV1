import json
import os
from datetime import datetime, timedelta

class QuotaManager:
    def __init__(self, config):
        self.quota_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.quota')
        self.config = config

    def _get_tier_config(self):
        tier = self.config.get_tier_config()
        return {
            "max_messages": tier.get("max_messages", 30),
            "window_hours": tier.get("window_hours", 12)
        }

    def get_remaining(self, session_id):
        cfg = self._get_tier_config()
        data = self._load()
        if session_id not in data:
            data[session_id] = {"count": 0, "start": datetime.now().isoformat()}
            self._save(data)
            return cfg["max_messages"]
        entry = data[session_id]
        start = datetime.fromisoformat(entry["start"])
        if datetime.now() - start > timedelta(hours=cfg["window_hours"]):
            data[session_id] = {"count": 0, "start": datetime.now().isoformat()}
            self._save(data)
            return cfg["max_messages"]
        return max(0, cfg["max_messages"] - entry["count"])

    def use(self, session_id):
        data = self._load()
        if session_id not in data:
            data[session_id] = {"count": 1, "start": datetime.now().isoformat()}
        else:
            data[session_id]["count"] += 1
        self._save(data)

    def _load(self):
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save(self, data):
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        with open(self.quota_file, 'w') as f:
            json.dump(data, f)