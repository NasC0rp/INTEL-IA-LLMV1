import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

class QuotaManager:
    def __init__(self, config: Any) -> None:
        self.quota_file: str = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache', '.quota')
        self.config: Any = config

    def _get_tier_config(self) -> Dict[str, int]:
        tier: Dict[str, Any] = self.config.get_tier_config()
        return {
            "max_messages": tier.get("max_messages", 30),
            "window_hours": tier.get("window_hours", 12)
        }

    def _quota_key(self, session_id: str) -> str:
        return f"tier:{self.config.get_tier()}"

    def get_remaining(self, session_id: str) -> int:
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        if key not in data:
            data[key] = {"count": 0, "start": datetime.now().isoformat()}
            self._save(data)
            return cfg["max_messages"]
        entry: Dict[str, Any] = data[key]
        start: datetime = datetime.fromisoformat(entry["start"])
        if datetime.now() - start > timedelta(hours=cfg["window_hours"]):
            data[key] = {"count": 0, "start": datetime.now().isoformat()}
            self._save(data)
            return cfg["max_messages"]
        return max(0, cfg["max_messages"] - entry["count"])

    def use(self, session_id: str) -> None:
        cfg: Dict[str, int] = self._get_tier_config()
        data: Dict[str, Any] = self._load()
        key: str = self._quota_key(session_id)
        now: datetime = datetime.now()
        if key not in data:
            data[key] = {"count": 1, "start": now.isoformat()}
        else:
            entry: Dict[str, Any] = data[key]
            start: datetime = datetime.fromisoformat(entry["start"])
            if now - start > timedelta(hours=cfg["window_hours"]):
                data[key] = {"count": 1, "start": now.isoformat()}
            else:
                data[key]["count"] += 1
        self._save(data)

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
        with open(self.quota_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
